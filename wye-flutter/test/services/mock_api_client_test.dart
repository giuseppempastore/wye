import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/score_evaluability_model.dart';
import 'package:wye/services/mock_api_client.dart';

void main() {
  test('static mock data has explicit components and no numeric overall', () {
    final product = MockApiClient.mockDatabase.values.first;

    expect(
      product.scoreView.ingredientGoodnessPercent.evaluabilityStatus,
      EvaluabilityStatus.computable,
    );
    expect(
      product.scoreView.nutritionGoodnessPercent.evaluabilityStatus,
      EvaluabilityStatus.computable,
    );
    expect(
      product.scoreView.overallScore.availability,
      OverallScoreAvailability.deferred,
    );
    expect(product.scoreView.overallScore.toJson(),
        isNot(contains('score_value')));
  });

  test('mock analysis does not calculate component or overall scores',
      () async {
    final client = MockApiClient();
    addTearDown(client.dispose);

    final product = await client.analyzeIngredients(
      productName: 'Fixture product',
      ingredients: 'fixture one, fixture two',
      language: 'it',
      category: 'food',
    );

    expect(product.scoreView.ingredientGoodnessPercent.scoreValue, isNull);
    expect(product.scoreView.nutritionGoodnessPercent.scoreValue, isNull);
    expect(
      product.scoreView.overallScore.availability,
      OverallScoreAvailability.deferred,
    );
  });
}
