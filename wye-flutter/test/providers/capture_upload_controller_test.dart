import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:wye/config/mobile_upload_config.dart';
import 'package:wye/models/capture_upload_error.dart';
import 'package:wye/models/capture_upload_models.dart';
import 'package:wye/providers/capture_upload_controller.dart';
import 'package:wye/services/fake_capture_upload_gateway.dart';
import 'package:wye/services/image_metadata_service.dart';

void main() {
  MobileUploadConfig enabledConfig() => MobileUploadConfig(
        enabled: true,
        apiBaseUri: Uri.parse('http://api.invalid:8000'),
      );

  test('controller is disabled or missing-token fail closed', () {
    final disabled = CaptureUploadController(
      config: MobileUploadConfig(
        enabled: false,
        apiBaseUri: Uri.parse('http://api.invalid:8000'),
      ),
      tokenProvider: InMemoryMobileUploadTokenProvider(),
      gateway: FakeCaptureUploadGateway(),
      metadataService: _FakeImageMetadataService(),
    );
    final missingToken = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: InMemoryMobileUploadTokenProvider(),
      gateway: FakeCaptureUploadGateway(),
      metadataService: _FakeImageMetadataService(),
    );
    addTearDown(disabled.dispose);
    addTearDown(missingToken.dispose);

    expect(disabled.state.step, UploadFlowStep.disabled);
    expect(missingToken.state.step, UploadFlowStep.missingToken);
  });

  test('setting an already expired token remains missing-token', () {
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: InMemoryMobileUploadTokenProvider(),
      gateway: FakeCaptureUploadGateway(),
      metadataService: _FakeImageMetadataService(),
    );
    addTearDown(controller.dispose);

    controller.setTemporaryToken(
      'expired-token',
      expiresAt: DateTime.now().toUtc().subtract(const Duration(seconds: 1)),
    );

    expect(controller.state.step, UploadFlowStep.missingToken);
  });

  test('fake metadata adapter supplies deterministic test-only digest',
      () async {
    final service = _FakeImageMetadataService();
    final metadata = await service.inspect(Uint8List.fromList([1, 2, 3]));

    expect(metadata.byteSize, 3);
    expect(metadata.sha256, List.filled(64, 'c').join());
  });

  test('happy path transitions through binary PUT and keeps IDs distinct',
      () async {
    final gateway = FakeCaptureUploadGateway();
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'temporary-token',
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: const Sha256ImageMetadataService(),
    );
    addTearDown(controller.dispose);
    final transitions = <UploadFlowStep>[];
    controller.addListener(() => transitions.add(controller.state.step));
    final identity = ProductIdentity(productId: 7, barcode: '7000000000001');
    final bytes = Uint8List.fromList([0xff, 0xd8, 0xff, 1, 2, 3, 4]);

    controller.selectImage(
      productIdentity: identity,
      purpose: CaptureImagePurpose.ingredients,
      bytes: bytes,
    );
    await controller.prepareMetadata();
    await controller.upload();

    expect(
      transitions,
      containsAllInOrder([
        UploadFlowStep.imageSelected,
        UploadFlowStep.metadataReady,
        UploadFlowStep.uploadInitializing,
        UploadFlowStep.binaryUploading,
        UploadFlowStep.finalizing,
        UploadFlowStep.extractionDeferred,
      ]),
    );
    expect(gateway.calls, ['initialize', 'put', 'finalize']);
    expect(gateway.uploadedBytes, bytes);
    expect(gateway.initializeRequest!.metadata.byteSize, bytes.length);
    expect(gateway.initializeRequest!.metadata.mimeType, 'image/jpeg');
    expect(
      gateway.initializeRequest!.metadata.sha256,
      const Sha256DigestService().hash(gateway.uploadedBytes!),
    );
    expect(gateway.initializeRequest!.productIdentity.productId, 7);
    expect(gateway.initializeRequest!.productIdentity.barcode, '7000000000001');
    expect(controller.state.productImage!.productImageId, 401);
    expect(controller.state.productImage!.storageObjectId, 301);
  });

  test('retryable failure is explicit and retry follows the same safe path',
      () async {
    final gateway = FakeCaptureUploadGateway()
      ..failure = const CaptureUploadException(
        kind: CaptureUploadFailureKind.transport,
        code: 'binary_upload_transport_error',
        safeMessage: 'Binary upload transport failed',
        retryable: true,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'temporary-token',
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: _FakeImageMetadataService(),
    );
    addTearDown(controller.dispose);
    final bytes = Uint8List.fromList([1]);
    controller.selectImage(
      productIdentity: ProductIdentity(productId: 7, barcode: 'barcode-7'),
      purpose: CaptureImagePurpose.productFront,
      bytes: bytes,
    );
    await controller.prepareMetadata();

    await controller.upload();
    expect(controller.state.step, UploadFlowStep.failedRetryable);
    expect(controller.state.errorCode, 'binary_upload_transport_error');

    gateway.failure = null;
    await controller.retry();
    expect(controller.state.step, UploadFlowStep.uploadedAssociated);
  });

  test('terminal failure is explicit and cannot be retried', () async {
    final gateway = FakeCaptureUploadGateway()
      ..failure = const CaptureUploadException(
        kind: CaptureUploadFailureKind.contract,
        code: 'unsafe_upload_headers',
        safeMessage: 'Upload capability contains forbidden headers',
        retryable: false,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'temporary-token',
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: _FakeImageMetadataService(),
    );
    addTearDown(controller.dispose);
    controller.selectImage(
      productIdentity: ProductIdentity(productId: 9, barcode: 'barcode-9'),
      purpose: CaptureImagePurpose.productFront,
      bytes: Uint8List.fromList([1]),
    );
    await controller.prepareMetadata();

    await controller.upload();
    expect(controller.state.step, UploadFlowStep.failedTerminal);
    expect(controller.state.errorCode, 'unsafe_upload_headers');
    final callCount = gateway.calls.length;
    await controller.retry();
    expect(gateway.calls, hasLength(callCount));
  });

  test('expired or rejected capability returns to missing-token state',
      () async {
    final gateway = FakeCaptureUploadGateway()
      ..failure = const CaptureUploadException(
        kind: CaptureUploadFailureKind.missingToken,
        code: 'mobile_token_missing',
        safeMessage: 'Mobile upload token is missing',
        retryable: false,
        lastStableStep: UploadFlowStep.metadataReady,
      );
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'temporary-token',
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: _FakeImageMetadataService(),
    );
    addTearDown(controller.dispose);
    controller.selectImage(
      productIdentity: ProductIdentity(productId: 10, barcode: 'barcode-10'),
      purpose: CaptureImagePurpose.nutrition,
      bytes: Uint8List.fromList([1]),
    );
    await controller.prepareMetadata();

    await controller.upload();

    expect(controller.state.step, UploadFlowStep.missingToken);
    expect(controller.state.errorCode, 'mobile_token_missing');
  });

  test('metadata mismatch fails closed before any gateway call', () async {
    final gateway = FakeCaptureUploadGateway();
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'temporary-token',
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: _MismatchedImageMetadataService(),
    );
    addTearDown(controller.dispose);
    controller.selectImage(
      productIdentity: ProductIdentity(productId: 11, barcode: 'barcode-11'),
      purpose: CaptureImagePurpose.productFront,
      bytes: Uint8List.fromList([1, 2, 3]),
    );

    await controller.prepareMetadata();
    await controller.upload();

    expect(controller.state.step, UploadFlowStep.failedTerminal);
    expect(controller.state.errorCode, 'image_metadata_size_mismatch');
    expect(gateway.calls, isEmpty);
  });

  test('malformed metadata hash fails closed before any gateway call',
      () async {
    final gateway = FakeCaptureUploadGateway();
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'temporary-token',
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: _MalformedHashImageMetadataService(),
    );
    addTearDown(controller.dispose);
    controller.selectImage(
      productIdentity: ProductIdentity(productId: 13, barcode: 'barcode-13'),
      purpose: CaptureImagePurpose.productFront,
      bytes: Uint8List.fromList([1, 2, 3]),
    );

    await controller.prepareMetadata();
    await controller.upload();

    expect(controller.state.step, UploadFlowStep.failedTerminal);
    expect(controller.state.errorCode, 'image_metadata_failed');
    expect(gateway.calls, isEmpty);
  });

  test('upload without prepared metadata fails closed', () async {
    final gateway = FakeCaptureUploadGateway();
    final tokenProvider = InMemoryMobileUploadTokenProvider()
      ..setToken(
        'temporary-token',
        expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
      );
    final controller = CaptureUploadController(
      config: enabledConfig(),
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: _FakeImageMetadataService(),
    );
    addTearDown(controller.dispose);
    controller.selectImage(
      productIdentity: ProductIdentity(productId: 12, barcode: 'barcode-12'),
      purpose: CaptureImagePurpose.productFront,
      bytes: Uint8List.fromList([1]),
    );

    await controller.upload();

    expect(controller.state.step, UploadFlowStep.failedTerminal);
    expect(controller.state.errorCode, 'image_metadata_missing');
    expect(gateway.calls, isEmpty);
  });
}

class _FakeImageMetadataService implements ImageMetadataService {
  @override
  Future<ImageMetadata> inspect(Uint8List bytes) async {
    return ImageMetadata(
      mimeType: 'image/jpeg',
      byteSize: bytes.length,
      sha256: List.filled(64, 'c').join(),
    );
  }
}

class _MismatchedImageMetadataService implements ImageMetadataService {
  @override
  Future<ImageMetadata> inspect(Uint8List bytes) async {
    return ImageMetadata(
      mimeType: 'image/jpeg',
      byteSize: bytes.length + 1,
      sha256: List.filled(64, 'd').join(),
    );
  }
}

class _MalformedHashImageMetadataService implements ImageMetadataService {
  @override
  Future<ImageMetadata> inspect(Uint8List bytes) async {
    return ImageMetadata(
      mimeType: 'image/jpeg',
      byteSize: bytes.length,
      sha256: List.filled(63, 'e').join(),
    );
  }
}
