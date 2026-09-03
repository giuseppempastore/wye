import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:wye/config/mobile_upload_config.dart';
import 'package:wye/models/capture_upload_error.dart';
import 'package:wye/models/capture_upload_models.dart';
import 'package:wye/services/capture_flow_logger.dart';
import 'package:wye/services/http_capture_upload_gateway.dart';

void main() {
  const tokenValue = 'temporary-mobile-token';
  final identity = ProductIdentity(productId: 7, barcode: '8001234567890');
  final metadata = ImageMetadata(
    mimeType: 'image/jpeg',
    byteSize: 4,
    sha256: List.filled(64, 'a').join(),
  );

  test('missing token fails closed before transport', () async {
    var requests = 0;
    final gateway = HttpCaptureUploadGateway(
      client: MockClient((request) async {
        requests += 1;
        return http.Response('{}', 500);
      }),
      config: MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('http://api.invalid:8000'),
      ),
      tokenProvider: InMemoryMobileUploadTokenProvider(),
    );
    addTearDown(gateway.close);

    await expectLater(
      gateway.initializeUpload(
        UploadInitializeRequest(
          productIdentity: identity,
          purpose: CaptureImagePurpose.ingredients,
          metadata: metadata,
        ),
      ),
      throwsA(
        isA<CaptureUploadException>()
            .having((error) => error.code, 'code', 'mobile_token_missing'),
      ),
    );
    expect(requests, 0);
  });

  test('facade routes use bearer token and binary PUT stays secret-free',
      () async {
    final requests = <http.Request>[];
    final logger = CollectingCaptureFlowLogger();
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        tokenValue,
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final client = MockClient((request) async {
      requests.add(request);
      if (request.method == 'PUT') {
        return http.Response('', 200);
      }
      if (request.url.path.endsWith('/finalize')) {
        return http.Response(
          jsonEncode({
            'upload_id': '00000000-0000-4000-8000-000000000001',
            'status': 'finalized',
            'storage_object_id': 301,
            'product_image_id': 401,
          }),
          200,
          headers: {'X-Request-ID': 'finalize-1'},
        );
      }
      return http.Response(
        jsonEncode({
          'upload_id': '00000000-0000-4000-8000-000000000001',
          'upload_url':
              'https://storage.invalid/object?signature=must-not-be-logged',
          'method': 'PUT',
          'headers': {'Content-Type': 'image/jpeg'},
          'expires_at': '2030-01-01T00:00:00Z',
        }),
        201,
        headers: {'X-Request-ID': 'initialize-1'},
      );
    });
    final gateway = HttpCaptureUploadGateway(
      client: client,
      config: MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('http://api.invalid:8000'),
      ),
      tokenProvider: tokenProvider,
      logger: logger,
    );
    addTearDown(gateway.close);

    final initialized = await gateway.initializeUpload(
      UploadInitializeRequest(
        productIdentity: identity,
        purpose: CaptureImagePurpose.ingredients,
        metadata: metadata,
      ),
    );
    await gateway.uploadBinary(
      capability: initialized,
      bytes: Uint8List.fromList([1, 2, 3, 4]),
    );
    final image = await gateway.finalizeUpload(
      UploadFinalizeRequest(
        productIdentity: identity,
        uploadId: '00000000-0000-4000-8000-000000000001',
      ),
    );

    expect(requests, hasLength(3));
    expect(
      requests[0].url.path,
      '/mobile/dev/v1/capture/products/7/images/uploads',
    );
    expect(requests[0].headers['authorization'], 'Bearer $tokenValue');
    expect(requests[0].headers, isNot(contains('x-wye-image-key')));
    expect(requests[0].body, isNot(contains('base64')));
    expect(requests[1].method, 'PUT');
    expect(requests[1].bodyBytes, [1, 2, 3, 4]);
    expect(requests[1].headers, isNot(contains('authorization')));
    expect(requests[1].headers, isNot(contains('x-wye-image-key')));
    expect(
      requests[2].url.path,
      '/mobile/dev/v1/capture/products/7/images/uploads/'
      '00000000-0000-4000-8000-000000000001/finalize',
    );
    expect(image.productImage.productImageId, 401);
    expect(image.productImage.storageObjectId, 301);
    expect(requests.map((request) => request.url.path),
        everyElement(isNot(contains('score'))));
    final logged = logger.events.join('\n');
    expect(logged, isNot(contains(tokenValue)));
    expect(logged, isNot(contains('signature=')));
    expect(logged, isNot(contains('storage.invalid')));
  });

  test('unsafe capability headers are rejected without exposing values',
      () async {
    const forbiddenSecret = 'must-not-leave-server';
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        tokenValue,
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final gateway = HttpCaptureUploadGateway(
      client: MockClient((request) async {
        return http.Response(
          jsonEncode({
            'upload_id': '00000000-0000-4000-8000-000000000001',
            'upload_url': 'https://storage.invalid/object?signature=secret',
            'method': 'PUT',
            'headers': {'X-WYE-Image-Key': forbiddenSecret},
            'expires_at': '2030-01-01T00:00:00Z',
          }),
          201,
        );
      }),
      config: MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('http://api.invalid:8000'),
      ),
      tokenProvider: tokenProvider,
    );
    addTearDown(gateway.close);

    Object? failure;
    try {
      await gateway.initializeUpload(
        UploadInitializeRequest(
          productIdentity: identity,
          purpose: CaptureImagePurpose.nutrition,
          metadata: metadata,
        ),
      );
    } on Object catch (error) {
      failure = error;
    }
    expect(failure, isA<CaptureUploadException>());
    expect(failure.toString(), isNot(contains(forbiddenSecret)));
    expect(failure.toString(), isNot(contains('signature=secret')));
  });

  test('expired binary capability fails before transport', () async {
    var requests = 0;
    final gateway = HttpCaptureUploadGateway(
      client: MockClient((request) async {
        requests += 1;
        return http.Response('', 200);
      }),
      config: MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('http://api.invalid:8000'),
      ),
      tokenProvider: InMemoryMobileUploadTokenProvider(),
    );
    addTearDown(gateway.close);

    await expectLater(
      gateway.uploadBinary(
        capability: UploadInitializeResponse(
          uploadId: '00000000-0000-4000-8000-000000000002',
          uploadUri: Uri.parse('https://storage.invalid/object?signature=old'),
          headers: {'Content-Type': 'image/jpeg'},
          expiresAt: DateTime.utc(2020),
        ),
        bytes: Uint8List.fromList([1]),
      ),
      throwsA(
        isA<CaptureUploadException>().having(
          (error) => error.code,
          'code',
          'upload_capability_expired',
        ),
      ),
    );
    expect(requests, 0);
  });

  test('facade error body and signed URL are not exposed', () async {
    const responseSecret = 'must-not-escape';
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        tokenValue,
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final gateway = HttpCaptureUploadGateway(
      client: MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': {
              'code': 'mobile_upload_failed',
              'message':
                  'https://storage.invalid/object?signature=$responseSecret',
            },
          }),
          503,
        );
      }),
      config: MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('http://api.invalid:8000'),
      ),
      tokenProvider: tokenProvider,
    );
    addTearDown(gateway.close);

    Object? failure;
    try {
      await gateway.initializeUpload(
        UploadInitializeRequest(
          productIdentity: identity,
          purpose: CaptureImagePurpose.ingredients,
          metadata: metadata,
        ),
      );
    } on Object catch (error) {
      failure = error;
    }

    expect(failure, isA<CaptureUploadException>());
    expect(failure.toString(), isNot(contains(responseSecret)));
    expect(failure.toString(), isNot(contains('storage.invalid')));
    expect(failure.toString(), isNot(contains(tokenValue)));
  });
}
