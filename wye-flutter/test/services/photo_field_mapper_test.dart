import 'package:flutter_test/flutter_test.dart';
import 'package:wye/services/photo_field_mapper.dart';

void main() {
  const mapper = PhotoFieldMapper();

  test('product front is representative and maps no fields', () {
    final result = mapper.map(
      'Brand: Bio Natura\nProduct name: Granola Cacao\n'
      'Category: food\nProduct type: cereal\n'
      'Ingredients: wheat, sugar',
      ProductPhotoPurpose.productFront,
    );

    expect(result.brandName, isNull);
    expect(result.productName, isNull);
    expect(result.category, isNull);
    expect(result.productType, isNull);
    expect(result.sourceSegment, isNull);
    expect(result.canonicalEnglish, isNull);
    expect(result.nutrition, isEmpty);
    expect(mapper.shouldExtractText(ProductPhotoPurpose.productFront), isFalse);
  });

  test('product front never populates ingredients', () {
    final result = mapper.map(
      'Ingredienti: acqua, sale',
      ProductPhotoPurpose.productFront,
    );
    expect(result.hasIngredients, isFalse);
  });

  test('product front never populates nutrition', () {
    final result = mapper.map(
      'Valori nutrizionali\nEnergia 100 kcal',
      ProductPhotoPurpose.productFront,
    );
    expect(result.hasNutrition, isFalse);
  });

  test('unlabelled product title never becomes ingredients', () {
    final result = mapper.map(
      'Bio Natura\nGranola Cacao Croccante\nCon avena integrale',
      ProductPhotoPurpose.ingredients,
    );

    expect(result.ingredientListText, isNull);
    expect(result.hasIngredients, isFalse);
  });

  test('ingredient mapping starts only at ingredient-list marker', () {
    final result = mapper.map(
      'Granola Cacao\nIngredienti: avena, zucchero, cacao\n'
      'Valori nutrizionali\nEnergia 420 kcal',
      ProductPhotoPurpose.ingredients,
    );

    expect(result.ingredientListText, 'avena, zucchero, cacao');
    expect(result.ingredientListText, isNot(contains('Granola Cacao')));
    expect(result.ingredientListText, isNot(contains('420')));
    expect(result.hasIdentity, isFalse);
    expect(result.nutrition, isEmpty);
  });

  test('nutrition photo maps labelled table values only', () {
    final result = mapper.map(
      'Valori nutrizionali per 100 g\nEnergia 420 kcal\n'
      'Proteine 12 g\nCarboidrati 55 g\nZuccheri 10 g\n'
      'Grassi 18 g\nSodio 80 mg',
      ProductPhotoPurpose.nutrition,
    );

    expect(result.nutrition['energy_kcal'], 420);
    expect(result.nutrition['protein_g'], 12);
    expect(result.nutrition['carbs_g'], 55);
    expect(result.nutrition['sugar_g'], 10);
    expect(result.nutrition['fat_g'], 18);
    expect(result.nutrition['sodium_mg'], 80);
    expect(result.sourceSegment, contains('Valori nutrizionali'));
    expect(result.canonicalEnglish, isNull);
    expect(result.hasIdentity, isFalse);
  });

  test('nutrition without table context is left empty', () {
    final result = mapper.map(
      'Snack proteico 12 g\nEnergia per vivere meglio',
      ProductPhotoPurpose.nutrition,
    );

    expect(result.nutrition, isEmpty);
  });

  test('unknown purpose prepopulates no canonical field', () {
    final result = mapper.map(
      'Brand: Example\nIngredienti: acqua\nEnergia 10 kcal',
      ProductPhotoPurpose.unknown,
    );
    expect(result.hasIdentity, isFalse);
    expect(result.hasIngredients, isFalse);
    expect(result.hasNutrition, isFalse);
    expect(mapper.shouldExtractText(ProductPhotoPurpose.unknown), isFalse);
  });

  test('obvious non-ingredient lines are filtered', () {
    final result = mapper.map(
      'Ingredienti:\nacqua, sale\nPeso netto 200 g\nVia Roma 1\n'
      'Valori nutrizionali',
      ProductPhotoPurpose.ingredients,
    );
    expect(result.ingredientListText, 'water, salt');
    expect(result.sourceSegment, 'acqua, sale');
  });

  test('Finnish Ainesosat is isolated and characters are preserved', () {
    final result = mapper.map(
      'Tuotteen nimi\nAinesosat: täysjyväkaura, sokeri, pähkinä (4 %)\n'
      'Ravintosisältö 100 g\nEnergia 1700 kJ / 405 kcal',
      ProductPhotoPurpose.ingredients,
    );

    expect(result.detectedLanguage, 'fi');
    expect(
      result.ingredientListText,
      'whole grain oats, sugar, nut (4 %)',
    );
    expect(result.sourceSegment, 'täysjyväkaura, sokeri, pähkinä (4 %)');
    expect(result.rawText, contains('pähkinä'));
    expect(result.warnings, isEmpty);
  });

  test('Finnish nutrition supports decimal comma, split rows, and salt', () {
    final result = mapper.map(
      'Ravintosisältö / 100 g\nEnergia\n1700 kJ / 405 kcal\n'
      'Rasvaa 12,5 g\njosta tyydyttyneitä 2,5 g\n'
      'Hiilihydraattia 61,2 g\njosta sokereita 8,4 g\n'
      'Ravintokuitua 7,0 g\nProteiinia 10,1 g\nSuolaa 0,8 g',
      ProductPhotoPurpose.nutrition,
    );

    expect(result.detectedLanguage, 'fi');
    expect(result.nutritionBasis, 'per_100_g');
    expect(result.nutrition['energy_kcal'], 405);
    expect(result.nutrition['fat_g'], 12.5);
    expect(result.nutrition['saturated_fat_g'], 2.5);
    expect(result.nutrition['carbs_g'], 61.2);
    expect(result.nutrition['sugar_g'], 8.4);
    expect(result.nutrition['fiber_g'], 7);
    expect(result.nutrition['protein_g'], 10.1);
    expect(result.nutrition['salt_g'], 0.8);
  });

  test('OCR typo is preserved and never silently corrected', () {
    final result = mapper.map(
      'Ainesosat: past4, vesi',
      ProductPhotoPurpose.ingredients,
    );

    expect(result.ingredientListText, 'past4, vesi');
    expect(result.rawText, contains('past4'));
    expect(result.ingredientListText, isNot(contains('pasta')));
  });
}
