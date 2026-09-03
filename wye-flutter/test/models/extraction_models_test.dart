import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/extraction_models.dart';

void main() {
  test('extraction response maps only the explicit frontend allowlist', () {
    final result = ExtractionResultSummary.fromJson({
      'extraction': {
        'id': 501,
        'label_document_id': 701,
        'run_status': 'succeeded',
        'created_at': '2026-09-03T10:00:00Z',
        'raw_response': {'provider': 'must-not-be-represented'},
        'score': 99,
        'overall_score': 99,
      },
      'items': [
        {
          'id': 601,
          'item_type': 'ingredient',
          'raw_text': 'sale',
          'normalized_text': 'sale',
          'detected_language': 'it',
          'extraction_confidence': 0.8,
          'extraction_status': 'detected',
          'structured_value': {'provider': 'must-not-be-represented'},
          'internal_field': 'must-not-be-represented',
          'goodness_percent': 100,
        },
      ],
    });

    expect(result.run.extractionRunId, 501);
    expect(result.run.labelDocumentId, 701);
    expect(result.run.status, ExtractionStatus.succeeded);
    expect(result.items.single.extractionItemId, 601);
    expect(result.items.single.type, ExtractionItemType.ingredient);
    expect(result.items.single.normalizedText, 'sale');
    expect(result.items.single.confidence, 0.8);
  });

  test('missing or invalid extraction identifiers fail closed', () {
    expect(
      () => ExtractionRunRef.fromJson({
        'id': 0,
        'run_status': 'succeeded',
      }),
      throwsFormatException,
    );
    expect(
      () => ExtractionRunRef.fromJson({'run_status': 'succeeded'}),
      throwsFormatException,
    );
    expect(
      () => ExtractionRunRef.fromJson({
        'id': 1,
        'run_status': 'unknown',
      }),
      throwsFormatException,
    );
  });

  test('invalid extraction item fields are rejected without coercion', () {
    expect(
      () => ExtractionItem.fromJson({
        'id': 1,
        'item_type': 'ingredient',
        'raw_text': 'sale',
        'extraction_confidence': 2,
        'extraction_status': 'detected',
      }),
      throwsFormatException,
    );
    expect(
      () => ExtractionItem.fromJson({
        'id': '1',
        'item_type': 'ingredient',
        'raw_text': 'sale',
        'extraction_status': 'detected',
      }),
      throwsFormatException,
    );
  });
}
