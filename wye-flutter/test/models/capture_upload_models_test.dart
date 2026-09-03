import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:wye/config/mobile_upload_config.dart';
import 'package:wye/models/capture_upload_models.dart';

void main() {
  test('mobile upload feature is disabled by default', () {
    expect(MobileUploadConfig.enabledByBuild, isFalse);
  });

  test('API base URL rejects credentials and unsupported schemes', () {
    expect(
      () => MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('ftp://api.invalid'),
      ),
      throwsArgumentError,
    );
    expect(
      () => MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('https://secret@api.invalid'),
      ),
      throwsArgumentError,
    );
  });

  test('temporary token and image draft representations are redacted', () {
    const secret = 'temporary-mobile-secret';
    final expiry = DateTime.now().toUtc().add(const Duration(minutes: 5));
    final token = MobileUploadToken(secret, expiresAt: expiry);
    final provider = InMemoryMobileUploadTokenProvider()
      ..setToken(secret, expiresAt: expiry);
    final draft = ImageCaptureDraft(
      productIdentity: ProductIdentity(productId: 42, barcode: '8001234567890'),
      purpose: CaptureImagePurpose.ingredients,
      bytes: Uint8List.fromList([1, 2, 3]),
    );

    expect(token.toString(), isNot(contains(secret)));
    expect(provider.toString(), isNot(contains(secret)));
    expect(draft.toString(), isNot(contains('[1, 2, 3]')));
  });

  test('expired temporary token fails closed in memory', () {
    final provider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'expired-secret',
        expiresAt: DateTime.now().toUtc().subtract(const Duration(seconds: 1)),
      );

    expect(provider.currentToken, isNull);
    expect(provider.toString(), isNot(contains('expired-secret')));
  });

  test('product, image and storage identifiers remain distinct', () {
    final identity = ProductIdentity(productId: 42, barcode: '42-barcode');
    final image = ProductImageRef.fromJson({
      'upload_id': '00000000-0000-4000-8000-000000000001',
      'product_image_id': 401,
      'storage_object_id': 301,
    });

    expect(identity.productId, 42);
    expect(identity.barcode, '42-barcode');
    expect(image.productImageId, 401);
    expect(image.storageObjectId, 301);
    expect(image.productImageId, isNot(image.storageObjectId));
  });

  test('metadata requires supported MIME, exact size and SHA-256', () {
    final metadata = ImageMetadata(
      mimeType: 'image/jpeg',
      byteSize: 3,
      sha256: List.filled(64, 'A').join(),
    );

    expect(metadata.sha256, List.filled(64, 'a').join());
    expect(
      () => ImageMetadata(
        mimeType: 'image/gif',
        byteSize: 3,
        sha256: List.filled(64, 'a').join(),
      ),
      throwsArgumentError,
    );
  });

  test('upload capability accepts only binary PUT', () {
    expect(
      () => UploadInitializeResponse.fromJson({
        'upload_id': '00000000-0000-4000-8000-000000000001',
        'upload_url': 'https://storage.invalid/object?signature=secret',
        'method': 'POST',
        'headers': <String, String>{},
        'expires_at': '2030-01-01T00:00:00Z',
      }),
      throwsFormatException,
    );
  });

  test('upload and finalize contracts reject coerced or unexpected values', () {
    expect(
      () => UploadInitializeResponse.fromJson({
        'upload_id': '00000000-0000-4000-8000-000000000001',
        'upload_url': 'https://storage.invalid/object?signature=secret',
        'method': 'PUT',
        'headers': {'Content-Type': 7},
        'expires_at': '2030-01-01T00:00:00Z',
      }),
      throwsFormatException,
    );
    expect(
      () => UploadFinalizeResponse.fromJson({
        'upload_id': '00000000-0000-4000-8000-000000000001',
        'status': 'pending',
        'product_image_id': 401,
        'storage_object_id': 301,
      }),
      throwsFormatException,
    );
  });

  test('initialize request has no base64 or score fields', () {
    final request = UploadInitializeRequest(
      productIdentity: ProductIdentity(productId: 42, barcode: 'barcode-42'),
      purpose: CaptureImagePurpose.nutrition,
      metadata: ImageMetadata(
        mimeType: 'image/png',
        byteSize: 3,
        sha256: List.filled(64, 'd').join(),
      ),
    ).toJson();

    expect(request, isNot(contains('base64')));
    expect(request.keys, everyElement(isNot(contains('score'))));
    expect(request.keys, everyElement(isNot(contains('overall'))));
  });
}
