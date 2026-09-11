import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/product_taxonomy.dart';

void main() {
  test('product type picklist exposes only stable IDs', () {
    expect(
      productTypeOptions.map((option) => option.id).toSet(),
      {'food', 'beverage', 'supplement', 'ingredient', 'other'},
    );
  });

  test('category picklist uses stable IDs and localized labels', () {
    expect(productCategoryOptions, hasLength(17));
    expect(
      productCategoryOptions.any(
        (option) =>
            option.id == 'sweets_snacks' && option.label == 'Dolci e snack',
      ),
      isTrue,
    );
    expect(
      productCategoryOptions.map((option) => option.id).toSet(),
      hasLength(productCategoryOptions.length),
    );
    expect(productCategoryLabel('sweets_snacks'), 'Dolci e snack');
    expect(productTypeLabel('beverage'), 'Bevanda');
  });
}
