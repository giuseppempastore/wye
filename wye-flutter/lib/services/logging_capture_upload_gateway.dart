import 'dart:typed_data';

import '../models/capture_upload_error.dart';
import '../models/capture_upload_models.dart';
import '../models/extraction_models.dart';
import 'capture_flow_logger.dart';
import 'capture_upload_gateway.dart';

class LoggingCaptureUploadGateway implements CaptureUploadGateway {
  final CaptureUploadGateway _delegate;
  final CaptureFlowLogger _logger;

  LoggingCaptureUploadGateway({
    required CaptureUploadGateway delegate,
    required CaptureFlowLogger logger,
  })  : _delegate = delegate,
        _logger = logger;

  @override
  Future<UploadInitializeResponse> initializeUpload(
    UploadInitializeRequest request,
  ) async {
    _started(
      'upload_initialize_started',
      productId: request.productIdentity.productId,
      purpose: request.purpose,
    );
    try {
      final result = await _delegate.initializeUpload(request);
      _succeeded(
        'upload_initialize_succeeded',
        productId: request.productIdentity.productId,
        purpose: request.purpose,
      );
      return result;
    } on CaptureUploadException catch (error) {
      _failed(
        'upload_initialize_failed',
        error,
        productId: request.productIdentity.productId,
        purpose: request.purpose,
      );
      rethrow;
    } on Object {
      _unexpected('upload_initialize_failed');
      rethrow;
    }
  }

  @override
  Future<void> uploadBinary({
    required UploadInitializeResponse capability,
    required Uint8List bytes,
  }) async {
    _started('binary_put_started');
    try {
      await _delegate.uploadBinary(capability: capability, bytes: bytes);
      _succeeded('binary_put_succeeded');
    } on CaptureUploadException catch (error) {
      _failed('binary_put_failed', error);
      rethrow;
    } on Object {
      _unexpected('binary_put_failed');
      rethrow;
    }
  }

  @override
  Future<UploadFinalizeResponse> finalizeUpload(
    UploadFinalizeRequest request,
  ) async {
    _started(
      'upload_finalize_started',
      productId: request.productIdentity.productId,
    );
    try {
      final result = await _delegate.finalizeUpload(request);
      _succeeded(
        'upload_finalize_succeeded',
        productId: request.productIdentity.productId,
        productImageId: result.productImage.productImageId,
        storageObjectId: result.productImage.storageObjectId,
      );
      return result;
    } on CaptureUploadException catch (error) {
      _failed(
        'upload_finalize_failed',
        error,
        productId: request.productIdentity.productId,
      );
      rethrow;
    } on Object {
      _unexpected('upload_finalize_failed');
      rethrow;
    }
  }

  @override
  Future<ExtractionResultSummary> startExtraction({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
    required String idempotencyKey,
  }) async {
    _started(
      'extraction_start_started',
      productId: productIdentity.productId,
      productImageId: productImage.productImageId,
      storageObjectId: productImage.storageObjectId,
    );
    try {
      final result = await _delegate.startExtraction(
        productIdentity: productIdentity,
        productImage: productImage,
        idempotencyKey: idempotencyKey,
      );
      _succeeded(
        'extraction_start_succeeded',
        productId: productIdentity.productId,
        productImageId: productImage.productImageId,
        storageObjectId: productImage.storageObjectId,
        extractionRunId: result.run.extractionRunId,
      );
      return result;
    } on CaptureUploadException catch (error) {
      _failed(
        'extraction_start_failed',
        error,
        productId: productIdentity.productId,
        productImageId: productImage.productImageId,
        storageObjectId: productImage.storageObjectId,
      );
      rethrow;
    } on Object {
      _unexpected('extraction_start_failed');
      rethrow;
    }
  }

  @override
  Future<List<ExtractionRunRef>> listExtractions({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
  }) async {
    _started(
      'extraction_list_started',
      productId: productIdentity.productId,
      productImageId: productImage.productImageId,
      storageObjectId: productImage.storageObjectId,
    );
    try {
      final result = await _delegate.listExtractions(
        productIdentity: productIdentity,
        productImage: productImage,
      );
      _succeeded(
        'extraction_list_succeeded',
        productId: productIdentity.productId,
        productImageId: productImage.productImageId,
        storageObjectId: productImage.storageObjectId,
        itemCount: result.length,
      );
      return result;
    } on CaptureUploadException catch (error) {
      _failed(
        'extraction_list_failed',
        error,
        productId: productIdentity.productId,
        productImageId: productImage.productImageId,
        storageObjectId: productImage.storageObjectId,
      );
      rethrow;
    } on Object {
      _unexpected('extraction_list_failed');
      rethrow;
    }
  }

  @override
  Future<ExtractionResultSummary> getExtraction({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
    required int extractionRunId,
  }) async {
    _started(
      'extraction_get_started',
      productId: productIdentity.productId,
      productImageId: productImage.productImageId,
      storageObjectId: productImage.storageObjectId,
      extractionRunId: extractionRunId,
    );
    try {
      final result = await _delegate.getExtraction(
        productIdentity: productIdentity,
        productImage: productImage,
        extractionRunId: extractionRunId,
      );
      _succeeded(
        'extraction_get_succeeded',
        productId: productIdentity.productId,
        productImageId: productImage.productImageId,
        storageObjectId: productImage.storageObjectId,
        extractionRunId: extractionRunId,
      );
      return result;
    } on CaptureUploadException catch (error) {
      _failed(
        'extraction_get_failed',
        error,
        productId: productIdentity.productId,
        productImageId: productImage.productImageId,
        storageObjectId: productImage.storageObjectId,
        extractionRunId: extractionRunId,
      );
      rethrow;
    } on Object {
      _unexpected('extraction_get_failed');
      rethrow;
    }
  }

  void _started(
    String step, {
    int? productId,
    CaptureImagePurpose? purpose,
    int? productImageId,
    int? storageObjectId,
    int? extractionRunId,
  }) {
    _logger.record(
      CaptureFlowEvent(
        step: step,
        statusClass: 'local',
        productId: productId,
        purpose: purpose,
        productImageId: productImageId,
        storageObjectId: storageObjectId,
        extractionRunId: extractionRunId,
      ),
    );
  }

  void _succeeded(
    String step, {
    int? productId,
    CaptureImagePurpose? purpose,
    int? productImageId,
    int? storageObjectId,
    int? extractionRunId,
    int? itemCount,
  }) {
    _logger.record(
      CaptureFlowEvent(
        step: step,
        statusClass: 'success',
        productId: productId,
        purpose: purpose,
        productImageId: productImageId,
        storageObjectId: storageObjectId,
        extractionRunId: extractionRunId,
        itemCount: itemCount,
      ),
    );
  }

  void _failed(
    String step,
    CaptureUploadException error, {
    int? productId,
    CaptureImagePurpose? purpose,
    int? productImageId,
    int? storageObjectId,
    int? extractionRunId,
  }) {
    _logger.record(
      CaptureFlowEvent(
        step: step,
        statusClass: error.statusCode == null
            ? 'failure'
            : '${error.statusCode! ~/ 100}xx',
        productId: productId,
        purpose: purpose,
        productImageId: productImageId,
        storageObjectId: storageObjectId,
        extractionRunId: extractionRunId,
        httpStatusCode: error.statusCode,
        errorCode: error.code,
        errorCategory: error.kind.name.toLowerCase(),
      ),
    );
  }

  void _unexpected(String step) {
    _logger.record(
      CaptureFlowEvent(
        step: step,
        statusClass: 'failure',
        errorCode: 'unexpected_failure',
        errorCategory: 'unexpected',
      ),
    );
  }

  @override
  void close() {
    _delegate.close();
  }
}
