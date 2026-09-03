/// Mock API Client per testing offline
/// Utile quando il backend non è disponibile

import '../models/product_model.dart';
import '../models/score_evaluability_model.dart';
import 'api_client.dart';

class MockApiClient extends ApiClient {
  /// Mock database di prodotti per testing
  static final Map<String, Product> mockDatabase = {
    '8718206112001': Product(
      barcode: '8718206112001',
      productName: 'Nutella',
      brand: 'Ferrero',
      category: 'food',
      scoreView: _mockComponentScores(ingredient: 32, nutrition: 65),
      ingredients: [
        'Zucchero',
        'Olio di palma',
        'Nocciole',
        'Cacao in polvere',
        'Latte scremato in polvere',
        'Siero di latte',
        'Emulsionante (lecitina di soia)',
        'Vanillina'
      ],
      nutritionFacts: NutritionFacts(
        servingSize: 100,
        energyKcal: 530,
        protein: 6.3,
        carbs: 57.5,
        sugar: 56.3,
        fat: 30.9,
        saturatedFat: 10.7,
        sodium: 43,
        fiber: 0.7,
      ),
      allergens: ['Nocciole', 'Latte', 'Soia'],
    ),
    '5901234123457': Product(
      barcode: '5901234123457',
      productName: 'Biscotti al Cioccolato',
      brand: 'Brand Test 1',
      category: 'food',
      scoreView: _mockComponentScores(ingredient: 55, nutrition: 62),
      ingredients: [
        'Farina di frumento',
        'Zucchero',
        'Olio vegetale',
        'Chocolate chips (cacao)',
        'Uova',
        'Lievito chimico',
      ],
      nutritionFacts: NutritionFacts(
        servingSize: 100,
        energyKcal: 450,
        protein: 5.0,
        carbs: 62.0,
        sugar: 25.0,
        fat: 18.0,
        saturatedFat: 5.0,
        sodium: 150,
        fiber: 1.5,
      ),
      allergens: ['Glutine', 'Uova', 'Latte'],
    ),
    '4006381333931': Product(
      barcode: '4006381333931',
      productName: 'Snack Salato',
      brand: 'Brand Test 2',
      category: 'snack',
      scoreView: _mockComponentScores(ingredient: 45, nutrition: 55),
      ingredients: [
        'Patate',
        'Olio vegetale',
        'Sale',
        'Aromi',
        'Conservante E202',
      ],
      allergens: [],
    ),
  };

  /// Override: ritorna prodotto dal mock database con delay
  @override
  Future<Product> getProductByBarcode(String barcode) async {
    // Simula delay di rete
    await Future.delayed(const Duration(milliseconds: 500));

    if (mockDatabase.containsKey(barcode)) {
      return mockDatabase[barcode]!;
    } else {
      throw ProductNotFoundException(
        'Prodotto "$barcode" non trovato nel mock database',
      );
    }
  }

  /// Override: analizza ingredienti con mock logic
  @override
  Future<Product> analyzeIngredients({
    required String productName,
    required String ingredients,
    required String language,
    String? category,
  }) async {
    // Simula analisi
    await Future.delayed(const Duration(seconds: 1));

    final ingredientList = ingredients.split(',').map((i) => i.trim()).toList();

    return Product(
      barcode: 'mock_${DateTime.now().millisecondsSinceEpoch}',
      productName: productName,
      brand: 'Mock Brand',
      category: category ?? 'food',
      scoreView: ProductScoreView.unavailable(),
      ingredients: ingredientList,
      allergens: [],
    );
  }

  /// Override: health check sempre OK
  @override
  Future<bool> healthCheck() async {
    await Future.delayed(const Duration(milliseconds: 200));
    return true;
  }
}

ProductScoreView _mockComponentScores({
  required int ingredient,
  required int nutrition,
}) {
  return ProductScoreView(
    ingredientGoodnessPercent: ScoreEvaluation.computable(
      scoreValue: ingredient,
    ),
    nutritionGoodnessPercent: ScoreEvaluation.computable(
      scoreValue: nutrition,
    ),
    overallScore: OverallScoreState.deferred(),
  );
}
