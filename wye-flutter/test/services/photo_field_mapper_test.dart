import 'package:flutter_test/flutter_test.dart';
import 'package:wye/services/photo_field_mapper.dart';

void main() {
  const mapper = PhotoFieldMapper();

  test('identity photo maps only explicitly labelled identity fields', () {
    final result = mapper.map(
      'Brand: Bio Natura\nProduct name: Granola Cacao\n'
      'Category: food\nProduct type: cereal\n'
      'Ingredients: wheat, sugar',
      ProductPhotoPurpose.identity,
    );

    expect(result.brandName, 'Bio Natura');
    expect(result.productName, 'Granola Cacao');
    expect(result.category, 'food');
    expect(result.productType, 'cereal');
    expect(result.ingredientListText, isNull);
    expect(result.nutrition, isEmpty);
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
    expect(result.ingredientListText, isNull);
  });

  test('nutrition without table context is left empty', () {
    final result = mapper.map(
      'Snack proteico 12 g\nEnergia per vivere meglio',
      ProductPhotoPurpose.nutrition,
    );

    expect(result.nutrition, isEmpty);
  });
}
