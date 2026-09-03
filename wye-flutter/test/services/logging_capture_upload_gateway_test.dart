import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/capture_upload_error.dart';
import 'package:wye/models/capture_upload_models.dart';
import 'package:wye/models/extraction_models.dart';
import 'package:wye/services/capture_flow_logger.dart';
import 'package:wye/services/fake_capture_upload_gateway.dart';
import 'package:wye/services/logging_capture_upload_gateway.dart';

void main() {
  late FakeCaptureUploadGateway delegate;
  late SanitizedInMemoryCaptureFlowLogger logger;
  late LoggingCaptureUploadGateway gateway;
  late ProductIdentity identity;
  late ImageMetadata metadata;

  setUp(() {
    delegate = FakeCaptureUploadGateway();
    logger = SanitizedInMemoryCaptureFlowLogger(enabled: true);
    gateway = LoggingCaptureUploadGateway(delegate: delegate, logger: logger);
    identity = ProductIdentity(productId: 7, barcode: '8001234567890');
    metadata = ImageMetadata(
      mimeType: 'image/jpeg',
      byteSize: 4,
      sha256: 'a' * 64,
    );
  });

  tearDown(() {
    gateway.close();
    logger.dispose();
  });

  test('upload and extraction operations emit sanitized lifecycle events',
      () async {
    const rawProviderText = 'raw-provider-private-text';
    delegate.extractionResult = ExtractionResultSummary(
      run: const ExtractionRunRef(
        extractionRunId: 501,
        status: ExtractionStatus.succeeded,
      ),
      items: const [
        ExtractionItem(
          extractionItemId: 601,
          type: ExtractionItemType.ingredient,
          rawText: rawProviderText,
          status: ExtractionItemStatus.detected,
        ),
      ],
    );

    final initialized = await gateway.initializeUpload(
      UploadInitializeRequest(
        productIdentity: identity,
        purpose: CaptureImagePurpose.ingredients,
        metadata: metadata,
      ),
    );
    await gateway.uploadBinary(
      capability: initialized,
      bytes: Uint8List.fromList([0xff, 0xd8, 0xff, 0xd9]),
    );
    final finalized = await gateway.finalizeUpload(
      UploadFinalizeRequest(
        productIdentity: identity,
        uploadId: initialized.uploadId,
      ),
    );
    await gateway.startExtraction(
      productIdentity: identity,
      productImage: finalized.productImage,
      idempotencyKey: 'mobile-extraction-safe-id',
    );
    await gateway.listExtractions(
      productIdentity: identity,
      productImage: finalized.productImage,
    );
    await gateway.getExtraction(
      productIdentity: identity,
      productImage: finalized.productImage,
      extractionRunId: 501,
    );

    final steps = logger.events.map((event) => event.step).toList();
    expect(
        steps,
        containsAll(<String>[
          'upload_initialize_started',
          'upload_initialize_succeeded',
          'binary_put_started',
          'binary_put_succeeded',
          'upload_finalize_started',
          'upload_finalize_succeeded',
          'extraction_start_started',
          'extraction_start_succeeded',
          'extraction_list_started',
          'extraction_list_succeeded',
          'extraction_get_started',
          'extraction_get_succeeded',
        ]));
    expect(
      logger.events
          .singleWhere((event) => event.step == 'extraction_list_succeeded')
          .itemCount,
      1,
    );

    final export = logger.exportText;
    expect(export, isNot(contains(rawProviderText)));
    expect(export, isNot(contains('upload.invalid')));
    expect(export, isNot(contains('mobile-extraction-safe-id')));
    expect(export, isNot(contains('8001234567890')));
    expect(export, isNot(contains('base64')));
    expect(export, isNot(contains('score')));
    expect(export, isNot(contains('overall')));
  });

  test('typed gateway failure logs only safe code and category', () async {
    delegate.failure = const CaptureUploadException(
      kind: CaptureUploadFailureKind.http,
      code: 'mobile_facade_unavailable',
      safeMessage: 'A safe message that is intentionally not logged',
      retryable: true,
      lastStableStep: UploadFlowStep.metadataReady,
      statusCode: 503,
    );

    await expectLater(
      gateway.initializeUpload(
        UploadInitializeRequest(
          productIdentity: identity,
          purpose: CaptureImagePurpose.ingredients,
          metadata: metadata,
        ),
      ),
      throwsA(isA<CaptureUploadException>()),
    );

    final failure = logger.events.last;
    expect(failure.step, 'upload_initialize_failed');
    expect(failure.httpStatusCode, 503);
    expect(failure.errorCode, 'mobile_facade_unavailable');
    expect(failure.errorCategory, 'http');
    expect(logger.exportText, isNot(contains('intentionally not logged')));
  });
}
