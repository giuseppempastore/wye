import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/product_acquisition_draft.dart';

void main() {
  ProductAcquisitionDraft sample() => ProductAcquisitionDraft(
        id: 'draft_12345678',
        currentStep: 2,
        barcode: '4006381333931',
        barcodeLookupCompleted: true,
        productId: 42,
        brand: 'Brand',
        productName: 'Product',
        categoryId: 'other',
        productTypeId: 'food',
        ingredients: 'water, salt',
        ingredientsUserEdited: true,
        nutrition: const {
          'energy_kj': 840,
          'energy_kcal': 200,
          'salt_g': .8,
          'sodium_mg': 320,
        },
        nutritionUserEdited: true,
        nutritionBasis: 'per_100_g',
        localImagePaths: const {
          'product_front': '/safe/front.jpg',
          'ingredients': '/safe/ingredients.jpg',
        },
        uploadedImageIds: const {'product_front': 9},
        uploadedImageChecksums: {'product_front': 'a' * 64},
        labelExtractions: const {
          'ingredients': {'raw_text': 'Ingredients: water, salt'}
        },
        recoverableErrorCode: 'network_unavailable',
        updatedAt: DateTime.utc(2026, 9, 6),
      );

  test('round trip restores barcode, photos, OCR and current step', () {
    final restored = ProductAcquisitionDraft.fromJson(sample().toJson());
    expect(restored.barcode, '4006381333931');
    expect(restored.currentStep, 2);
    expect(restored.localImagePaths['ingredients'], '/safe/ingredients.jpg');
    expect(restored.labelExtractions['ingredients']?['raw_text'], isNotEmpty);
  });

  test('salt grams and sodium milligrams remain separate', () {
    final restored = ProductAcquisitionDraft.fromJson(sample().toJson());
    expect(restored.nutrition['salt_g'], .8);
    expect(restored.nutrition['sodium_mg'], 320);
  });

  test('kJ, kcal and user correction provenance survive restore', () {
    final restored = ProductAcquisitionDraft.fromJson(sample().toJson());
    expect(restored.nutrition['energy_kj'], 840);
    expect(restored.nutrition['energy_kcal'], 200);
    expect(restored.ingredientsUserEdited, isTrue);
    expect(restored.nutritionUserEdited, isTrue);
    expect(restored.labelExtractions['ingredients']?['raw_text'],
        'Ingredients: water, salt');
  });

  test('serialization never contains token or presigned URL fields', () {
    final encoded = sample().toJson().toString().toLowerCase();
    expect(encoded, isNot(contains('access_token')));
    expect(encoded, isNot(contains('authorization')));
    expect(encoded, isNot(contains('presigned')));
  });

  test('uploaded image identifiers and checksums survive restore', () {
    final restored = ProductAcquisitionDraft.fromJson(sample().toJson());
    expect(restored.uploadedImageIds['product_front'], 9);
    expect(restored.uploadedImageChecksums['product_front'], 'a' * 64);
  });

  test('recoverable upload error does not remove draft content', () {
    final failed = sample().copyWith(
      status: ProductAcquisitionStatus.failed,
      recoverableErrorCode: 'upload_failed',
    );
    expect(failed.hasUserData, isTrue);
    expect(failed.localImagePaths, isNotEmpty);
    expect(failed.recoverableErrorCode, 'upload_failed');
  });

  test('copying a draft preserves stable identity', () {
    expect(sample().copyWith(currentStep: 3).id, sample().id);
  });

  test('all acquisition statuses have distinct wire values', () {
    final values = ProductAcquisitionStatus.values
        .map((status) => status.wireValue)
        .toSet();
    expect(values.length, ProductAcquisitionStatus.values.length);
  });

  test('all acquisition statuses have user-facing labels', () {
    for (final status in ProductAcquisitionStatus.values) {
      expect(status.italianLabel.trim(), isNotEmpty);
    }
  });

  test('unknown persisted state is safely restored as draft', () {
    final json = sample().toJson()..['status'] = 'future_state';
    expect(
      ProductAcquisitionDraft.fromJson(json).status,
      ProductAcquisitionStatus.draft,
    );
  });

  test('unsupported schema version is rejected', () {
    final json = sample().toJson()..['schema_version'] = 999;
    expect(
      () => ProductAcquisitionDraft.fromJson(json),
      throwsFormatException,
    );
  });
}
