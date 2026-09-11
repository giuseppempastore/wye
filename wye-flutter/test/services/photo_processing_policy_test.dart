import 'package:flutter_test/flutter_test.dart';
import 'package:wye/services/photo_field_mapper.dart';
import 'package:wye/services/photo_processing_policy.dart';

void main() {
  test('manual crop is exclusive to the product photo', () {
    expect(
      PhotoProcessingPolicy.requiresManualCrop(
        ProductPhotoPurpose.productFront,
      ),
      isTrue,
    );
    expect(
      PhotoProcessingPolicy.requiresManualCrop(
        ProductPhotoPurpose.ingredients,
      ),
      isFalse,
    );
    expect(
      PhotoProcessingPolicy.requiresManualCrop(
        ProductPhotoPurpose.nutrition,
      ),
      isFalse,
    );
  });

  test('capture limits stay conservative and explicit', () {
    expect(PhotoProcessingPolicy.productMaxDimension, 2048);
    expect(PhotoProcessingPolicy.productJpegQuality, 88);
    expect(PhotoProcessingPolicy.documentMaxDimension, 3072);
    expect(PhotoProcessingPolicy.documentJpegQuality, 94);
  });
}
