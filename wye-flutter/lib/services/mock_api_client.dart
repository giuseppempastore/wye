/// Mock API Client per testing offline
/// Utile quando il backend non è disponibile

import '../models/product_model.dart';
import 'api_client.dart';

class MockApiClient extends ApiClient {
  /// Mock database di prodotti per testing
  static final Map<String, Product> mockDatabase = {
    '8718206112001': Product(
      barcode: '8718206112001',
      productName: 'Nutella',
      brand: 'Ferrero',
      category: 'food',
      ingredientScore: 32,
      nutritionScore: 65,
      finalScore: 42,
      riskLevel: 'moderate',
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
      ingredientScore: 55,
      nutritionScore: 62,
      finalScore: 58,
      riskLevel: 'moderate',
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
      ingredientScore: 45,
      nutritionScore: 55,
      finalScore: 50,
      riskLevel: 'moderate',
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

    final ingredientList = ingredients
        .split(',')
        .map((i) => i.trim())
        .toList();

    // Mock scoring logic
    final hasRiskyIngredients = ingredientList
        .any((i) => i.toLowerCase().contains('conservante') ||
            i.toLowerCase().contains('artificiale'));

    final ingredientScore = hasRiskyIngredients ? 35 : 65;
    final nutritionScore = category == 'food' ? 60 : 0;
    final finalScore = ((ingredientScore * 0.6) + (nutritionScore * 0.4)).toInt().toDouble();

    return Product(
      barcode: 'mock_${DateTime.now().millisecondsSinceEpoch}',
      productName: productName,
      brand: 'Mock Brand',
      category: category ?? 'food',
      ingredientScore: ingredientScore.toDouble(),
      nutritionScore: category == 'food' ? nutritionScore.toDouble() : null,
      finalScore: finalScore,
      riskLevel: finalScore < 40
          ? 'high'
          : finalScore < 60
              ? 'moderate'
              : 'low',
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
