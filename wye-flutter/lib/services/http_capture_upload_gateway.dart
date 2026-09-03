import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../config/mobile_upload_config.dart';
import '../models/capture_upload_error.dart';
import '../models/capture_upload_models.dart';
import '../models/extraction_models.dart';
import 'capture_flow_logger.dart';
import 'capture_upload_gateway.dart';

class HttpCaptureUploadGateway implements CaptureUploadGateway {
  static const _facadePrefix = '/mobile/dev/v1/capture';
  static const _forbiddenCapabilityHeaders = {
    'authorization',
    'cookie',
    'proxy-authorization',
    'set-cookie',
    'x-wye-image-key',
  };
  static const _allowedCapabilityHeaders = {
    'content-type',
    'content-md5',
    'x-amz-checksum-sha256',
    'x-amz-content-sha256',
  };

  final http.Client _client;
  final MobileUploadConfig _config;
  final MobileUploadTokenProvider _tokenProvider;
  final CaptureFlowLogger _logger;

  HttpCaptureUploadGateway({
    required http.Client client,
    required MobileUploadConfig config,
    required MobileUploadTokenProvider tokenProvider,
    CaptureFlowLogger logger = const NoOpCaptureFlowLogger(),
  })  : _client = client,
        _config = config,
        _tokenProvider = tokenProvider,
        _logger = logger;

  @override
  Future<UploadInitializeResponse> initializeUpload(
    UploadInitializeRequest request,
  ) async {
    final started = DateTime.now();
    final response = await _sendControlPlane(
      uri: _facadeUri(
        '/products/${request.productIdentity.productId}/images/uploads',
      ),
      body: request.toJson(),
      stableStep: UploadFlowStep.metadataReady,
    );
    final parsed = _decodeObject(response, UploadFlowStep.metadataReady);
    try {
      final result = UploadInitializeResponse.fromJson(parsed);
      _validateCapabilityHeaders(result.headers);
      _logger.record(
        CaptureFlowEvent(
          step: 'upload_initialize',
          statusClass: '${response.statusCode ~/ 100}xx',
          productId: request.productIdentity.productId,
          purpose: request.purpose,
          requestId: response.headers['x-request-id'],
          httpStatusCode: response.statusCode,
          latencyMs: DateTime.now().difference(started).inMilliseconds,
        ),
      );
      return result;
    } on CaptureUploadException {
      rethrow;
    } on Object {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.contract,
        code: 'mobile_upload_contract_invalid',
        safeMessage: 'Upload initialization response is invalid',
        retryable: false,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    }
  }

  @override
  Future<void> uploadBinary({
    required UploadInitializeResponse capability,
    required Uint8List bytes,
  }) async {
    if (bytes.isEmpty) {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.invalidInput,
        code: 'empty_image',
        safeMessage: 'Image bytes are empty',
        retryable: false,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    }
    if (!capability.expiresAt.isAfter(DateTime.now().toUtc())) {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.invalidInput,
        code: 'upload_capability_expired',
        safeMessage: 'Upload capability has expired',
        retryable: true,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    }
    _validateCapabilityHeaders(capability.headers);
    final started = DateTime.now();
    final request = http.Request('PUT', capability.uploadUri)
      ..followRedirects = false
      ..headers.addAll(capability.headers)
      ..bodyBytes = bytes;
    try {
      final streamed = await _client.send(request).timeout(_config.timeout);
      await streamed.stream.drain<void>().timeout(_config.timeout);
      if (streamed.statusCode < 200 || streamed.statusCode >= 300) {
        throw CaptureUploadException(
          kind: CaptureUploadFailureKind.http,
          code: 'binary_upload_failed',
          safeMessage: 'Binary upload failed',
          retryable: streamed.statusCode >= 500,
          lastStableStep: UploadFlowStep.metadataReady,
          statusCode: streamed.statusCode,
        );
      }
      _logger.record(
        CaptureFlowEvent(
          step: 'binary_upload',
          statusClass: '${streamed.statusCode ~/ 100}xx',
          httpStatusCode: streamed.statusCode,
          latencyMs: DateTime.now().difference(started).inMilliseconds,
        ),
      );
    } on CaptureUploadException {
      rethrow;
    } on TimeoutException {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.timeout,
        code: 'binary_upload_timeout',
        safeMessage: 'Binary upload timed out',
        retryable: true,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    } on SocketException {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.transport,
        code: 'binary_upload_transport_error',
        safeMessage: 'Binary upload transport failed',
        retryable: true,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    } on http.ClientException {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.transport,
        code: 'binary_upload_transport_error',
        safeMessage: 'Binary upload transport failed',
        retryable: true,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    }
  }

  @override
  Future<UploadFinalizeResponse> finalizeUpload(
    UploadFinalizeRequest request,
  ) async {
    final started = DateTime.now();
    final response = await _sendControlPlane(
      uri: _facadeUri(
        '/products/${request.productIdentity.productId}/images/uploads/'
        '${Uri.encodeComponent(request.uploadId)}/finalize',
      ),
      stableStep: UploadFlowStep.metadataReady,
    );
    try {
      final result = UploadFinalizeResponse.fromJson(
        _decodeObject(response, UploadFlowStep.metadataReady),
      );
      _logger.record(
        CaptureFlowEvent(
          step: 'upload_finalize',
          statusClass: '${response.statusCode ~/ 100}xx',
          productId: request.productIdentity.productId,
          requestId: response.headers['x-request-id'],
          httpStatusCode: response.statusCode,
          productImageId: result.productImage.productImageId,
          storageObjectId: result.productImage.storageObjectId,
          latencyMs: DateTime.now().difference(started).inMilliseconds,
        ),
      );
      return result;
    } on CaptureUploadException {
      rethrow;
    } on Object {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.contract,
        code: 'mobile_finalize_contract_invalid',
        safeMessage: 'Upload finalization response is invalid',
        retryable: false,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    }
  }

  @override
  Future<ExtractionResultSummary> startExtraction({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
    required String idempotencyKey,
  }) async {
    final key = idempotencyKey.trim();
    if (key.isEmpty || key.length > 255) {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.invalidInput,
        code: 'extraction_idempotency_key_invalid',
        safeMessage: 'Extraction idempotency key is invalid',
        retryable: false,
        lastStableStep: UploadFlowStep.extractionDeferred,
      );
    }
    final started = DateTime.now();
    final response = await _sendControlPlane(
      uri: _extractionUri(productIdentity, productImage),
      stableStep: UploadFlowStep.extractionDeferred,
      body: const {},
      headers: {'Idempotency-Key': key},
    );
    final result = _decodeExtractionResult(response);
    _recordExtractionEvent(
      step: 'extraction_start',
      response: response,
      started: started,
      productIdentity: productIdentity,
      productImage: productImage,
      extractionRunId: result.run.extractionRunId,
    );
    return result;
  }

  @override
  Future<List<ExtractionRunRef>> listExtractions({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
  }) async {
    final started = DateTime.now();
    final response = await _sendControlPlane(
      method: 'GET',
      uri: _extractionUri(productIdentity, productImage),
      stableStep: UploadFlowStep.extractionDeferred,
    );
    try {
      final decoded =
          _decodeObject(response, UploadFlowStep.extractionDeferred);
      final rawRuns = decoded['extractions'];
      if (rawRuns is! List) {
        throw const FormatException('extractions must be a list');
      }
      final runs = rawRuns
          .map(
            (run) => ExtractionRunRef.fromJson(
              Map<String, dynamic>.from(run as Map),
            ),
          )
          .toList(growable: false);
      _recordExtractionEvent(
        step: 'extraction_list',
        response: response,
        started: started,
        productIdentity: productIdentity,
        productImage: productImage,
      );
      return runs;
    } on CaptureUploadException {
      rethrow;
    } on Object {
      throw _extractionContractError();
    }
  }

  @override
  Future<ExtractionResultSummary> getExtraction({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
    required int extractionRunId,
  }) async {
    if (extractionRunId <= 0) {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.invalidInput,
        code: 'extraction_run_id_invalid',
        safeMessage: 'Extraction run identifier is invalid',
        retryable: false,
        lastStableStep: UploadFlowStep.extractionDeferred,
      );
    }
    final started = DateTime.now();
    final response = await _sendControlPlane(
      method: 'GET',
      uri: _extractionUri(productIdentity, productImage).replace(
        path: '${_extractionUri(productIdentity, productImage).path}/'
            '$extractionRunId',
      ),
      stableStep: UploadFlowStep.extractionDeferred,
    );
    final result = _decodeExtractionResult(response);
    if (result.run.extractionRunId != extractionRunId) {
      throw _extractionContractError();
    }
    _recordExtractionEvent(
      step: 'extraction_get',
      response: response,
      started: started,
      productIdentity: productIdentity,
      productImage: productImage,
      extractionRunId: extractionRunId,
    );
    return result;
  }

  Future<http.Response> _sendControlPlane({
    String method = 'POST',
    required Uri uri,
    required UploadFlowStep stableStep,
    Map<String, Object>? body,
    Map<String, String> headers = const {},
  }) async {
    if (!_config.enabled) {
      throw CaptureUploadException(
        kind: CaptureUploadFailureKind.disabled,
        code: 'mobile_upload_disabled',
        safeMessage: 'Mobile upload is disabled',
        retryable: false,
        lastStableStep: stableStep,
      );
    }
    final token = _tokenProvider.currentToken;
    if (token == null) {
      throw CaptureUploadException(
        kind: CaptureUploadFailureKind.missingToken,
        code: 'mobile_token_missing',
        safeMessage: 'Mobile upload token is missing',
        retryable: false,
        lastStableStep: stableStep,
      );
    }
    try {
      final request = http.Request(method, uri)
        ..followRedirects = false
        ..headers.addAll({
          'Authorization': token.authorizationHeader,
          ...headers,
        });
      if (body != null) {
        request.headers['Content-Type'] = 'application/json';
        request.body = jsonEncode(body);
      }
      final streamed = await _client.send(request).timeout(_config.timeout);
      final response =
          await http.Response.fromStream(streamed).timeout(_config.timeout);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw CaptureUploadException(
          kind: CaptureUploadFailureKind.http,
          code: _safeErrorCode(response.body) ?? 'mobile_facade_http_error',
          safeMessage: 'Mobile facade request failed',
          retryable: response.statusCode >= 500,
          lastStableStep: stableStep,
          statusCode: response.statusCode,
        );
      }
      return response;
    } on CaptureUploadException {
      rethrow;
    } on TimeoutException {
      throw CaptureUploadException(
        kind: CaptureUploadFailureKind.timeout,
        code: 'mobile_facade_timeout',
        safeMessage: 'Mobile facade request timed out',
        retryable: true,
        lastStableStep: stableStep,
      );
    } on SocketException {
      throw CaptureUploadException(
        kind: CaptureUploadFailureKind.transport,
        code: 'mobile_facade_transport_error',
        safeMessage: 'Mobile facade transport failed',
        retryable: true,
        lastStableStep: stableStep,
      );
    } on http.ClientException {
      throw CaptureUploadException(
        kind: CaptureUploadFailureKind.transport,
        code: 'mobile_facade_transport_error',
        safeMessage: 'Mobile facade transport failed',
        retryable: true,
        lastStableStep: stableStep,
      );
    }
  }

  ExtractionResultSummary _decodeExtractionResult(http.Response response) {
    try {
      return ExtractionResultSummary.fromJson(
        _decodeObject(response, UploadFlowStep.extractionDeferred),
      );
    } on CaptureUploadException {
      rethrow;
    } on Object {
      throw _extractionContractError();
    }
  }

  CaptureUploadException _extractionContractError() {
    return const CaptureUploadException(
      kind: CaptureUploadFailureKind.contract,
      code: 'mobile_extraction_contract_invalid',
      safeMessage: 'Extraction response is invalid',
      retryable: false,
      lastStableStep: UploadFlowStep.extractionDeferred,
    );
  }

  Uri _extractionUri(
    ProductIdentity productIdentity,
    ProductImageRef productImage,
  ) {
    return _facadeUri(
      '/products/${productIdentity.productId}/images/'
      '${productImage.productImageId}/extractions',
    );
  }

  void _recordExtractionEvent({
    required String step,
    required http.Response response,
    required DateTime started,
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
    int? extractionRunId,
  }) {
    _logger.record(
      CaptureFlowEvent(
        step: step,
        statusClass: '${response.statusCode ~/ 100}xx',
        productId: productIdentity.productId,
        productImageId: productImage.productImageId,
        storageObjectId: productImage.storageObjectId,
        extractionRunId: extractionRunId,
        requestId: response.headers['x-request-id'],
        httpStatusCode: response.statusCode,
        latencyMs: DateTime.now().difference(started).inMilliseconds,
      ),
    );
  }

  Map<String, dynamic> _decodeObject(
    http.Response response,
    UploadFlowStep stableStep,
  ) {
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is! Map) {
        throw const FormatException('Expected object');
      }
      return Map<String, dynamic>.from(decoded);
    } on Object {
      throw CaptureUploadException(
        kind: CaptureUploadFailureKind.contract,
        code: 'mobile_facade_contract_invalid',
        safeMessage: 'Mobile facade response is invalid',
        retryable: false,
        lastStableStep: stableStep,
      );
    }
  }

  void _validateCapabilityHeaders(Map<String, String> headers) {
    final normalizedNames = headers.keys.map((name) => name.toLowerCase());
    if (normalizedNames.any(_forbiddenCapabilityHeaders.contains) ||
        normalizedNames
            .any((name) => !_allowedCapabilityHeaders.contains(name))) {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.contract,
        code: 'unsafe_upload_headers',
        safeMessage: 'Upload capability contains forbidden headers',
        retryable: false,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    }
  }

  Uri _facadeUri(String suffix) {
    final basePath = _config.apiBaseUri.path.endsWith('/')
        ? _config.apiBaseUri.path.substring(
            0,
            _config.apiBaseUri.path.length - 1,
          )
        : _config.apiBaseUri.path;
    return _config.apiBaseUri.replace(path: '$basePath$_facadePrefix$suffix');
  }

  String? _safeErrorCode(String body) {
    try {
      final decoded = jsonDecode(body);
      final detail = decoded is Map ? decoded['detail'] : null;
      final code = detail is Map ? detail['code'] : null;
      return code is String && RegExp(r'^[a-z0-9_]{1,80}$').hasMatch(code)
          ? code
          : null;
    } on Object {
      return null;
    }
  }

  @override
  void close() {
    _client.close();
  }
}
