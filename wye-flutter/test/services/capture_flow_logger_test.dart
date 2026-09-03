import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/capture_upload_models.dart';
import 'package:wye/services/capture_flow_logger.dart';

void main() {
  final fixedTime = DateTime.utc(2026, 9, 3, 12, 30);

  test('disabled logger remains empty', () {
    final logger = SanitizedInMemoryCaptureFlowLogger(enabled: false);
    addTearDown(logger.dispose);

    logger.record(
      const CaptureFlowEvent(step: 'image_selected', statusClass: 'success'),
    );

    expect(logger.events, isEmpty);
    expect(logger.exportText, isEmpty);
  });

  test('enabled logger captures only allowlisted structured fields', () {
    final logger = SanitizedInMemoryCaptureFlowLogger(
      enabled: true,
      clock: () => fixedTime,
    );
    addTearDown(logger.dispose);

    logger.record(
      const CaptureFlowEvent(
        step: 'upload_initialize',
        statusClass: '2xx',
        productId: 7,
        purpose: CaptureImagePurpose.ingredients,
        requestId: 'safe-request-42',
        productImageId: 11,
        storageObjectId: 12,
        extractionRunId: 13,
        itemCount: 2,
        httpStatusCode: 201,
        retryCount: 0,
        latencyMs: 25,
      ),
    );

    expect(logger.events, hasLength(1));
    expect(logger.events.single.timestamp, fixedTime);
    expect(logger.exportText, contains('"request_id":"safe-request-42"'));
    expect(logger.exportText, contains('"http_status_code":201'));
    expect(logger.exportText, isNot(contains('score')));
    expect(logger.exportText, isNot(contains('overall')));
  });

  test('buffer is bounded and can be cleared', () {
    final logger = SanitizedInMemoryCaptureFlowLogger(
      enabled: true,
      capacity: 2,
      clock: () => fixedTime,
    );
    addTearDown(logger.dispose);

    for (final step in [
      'image_selected',
      'metadata_prepared',
      'token_cleared'
    ]) {
      logger.record(CaptureFlowEvent(step: step, statusClass: 'local'));
    }

    expect(logger.events.map((event) => event.step), [
      'metadata_prepared',
      'token_cleared',
    ]);
    logger.clear();
    expect(logger.events, isEmpty);
    expect(logger.exportText, isEmpty);
  });

  test('request identifiers with sensitive shapes are redacted', () {
    final logger = SanitizedInMemoryCaptureFlowLogger(
      enabled: true,
      clock: () => fixedTime,
    );
    addTearDown(logger.dispose);
    final unsafeValues = [
      'Bearer temporary-sensitive-token',
      'X-WYE-Image-Key: server-secret',
      'https://storage.invalid/object?X-Amz-Signature=secret-signature',
      'C:\\private\\camera\\label.jpg',
      '/private/camera/label.jpg',
      '{"raw_payload":"provider secret"}',
      'aGVsbG8=' * 20,
    ];

    for (final value in unsafeValues) {
      logger.record(
        CaptureFlowEvent(
          step: 'upload_initialize',
          statusClass: 'failure',
          requestId: value,
        ),
      );
    }

    final export = logger.exportText;
    expect(export, contains('<redacted>'));
    for (final value in unsafeValues) {
      expect(export, isNot(contains(value)));
    }
    expect(export, isNot(contains('temporary-sensitive-token')));
    expect(export, isNot(contains('secret-signature')));
    expect(export, isNot(contains('provider secret')));
  });

  test('a new logger starts empty and does not restore prior events', () {
    final first = SanitizedInMemoryCaptureFlowLogger(
      enabled: true,
      clock: () => fixedTime,
    );
    first.record(
      const CaptureFlowEvent(step: 'image_selected', statusClass: 'success'),
    );
    expect(first.events, isNotEmpty);
    first.dispose();

    final second = SanitizedInMemoryCaptureFlowLogger(enabled: true);
    addTearDown(second.dispose);
    expect(second.events, isEmpty);
  });
}
