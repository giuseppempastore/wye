import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/product_model.dart';
import 'package:wye/models/score_evaluability_model.dart';

void main() {
  test('positive product id remains distinct from barcode', () {
    final product = Product.fromJson({..._productJson(), 'id': 73});

    expect(product.productId, 73);
    expect(product.barcode, 'fixture-product');
    expect(product.toJson()['id'], 73);
  });

  group('Product score parsing', () {
    test('missing component scores remain not_computable instead of zero', () {
      final product = Product.fromJson(_productJson());

      expect(
        product.scoreView.ingredientGoodnessPercent.evaluabilityStatus,
        EvaluabilityStatus.notComputable,
      );
      expect(product.scoreView.ingredientGoodnessPercent.scoreValue, isNull);
      expect(
        product.scoreView.nutritionGoodnessPercent.evaluabilityStatus,
        EvaluabilityStatus.notComputable,
      );
      expect(product.scoreView.nutritionGoodnessPercent.scoreValue, isNull);
    });

    test('an explicit typed computable zero remains zero', () {
      final product = Product.fromJson({
        ..._productJson(),
        'ingredient_goodness_percent': {
          'evaluability_status': 'computable',
          'score_value': 0,
        },
        'nutrition_goodness_percent': {
          'evaluability_status': 'not_computable',
        },
        'overall_score': {
          'availability': 'deferred',
        },
      });

      expect(
        product.scoreView.ingredientGoodnessPercent.evaluabilityStatus,
        EvaluabilityStatus.computable,
      );
      expect(product.scoreView.ingredientGoodnessPercent.scoreValue, 0);
      expect(product.scoreView.nutritionGoodnessPercent.scoreValue, isNull);
    });

    test('legacy numeric fields are not promoted to the typed score contract',
        () {
      final product = Product.fromJson({
        ..._productJson(),
        'ingredient_score': 0,
        'nutrition_score': 80,
        'final_score': 40,
      });

      expect(product.scoreView.ingredientGoodnessPercent.scoreValue, isNull);
      expect(product.scoreView.nutritionGoodnessPercent.scoreValue, isNull);
      expect(
        product.scoreView.overallScore.availability,
        OverallScoreAvailability.deferred,
      );
    });

    test('serialization emits typed score state without legacy score fields',
        () {
      final serialized = Product.fromJson(_productJson()).toJson();

      expect(serialized, contains('score_view'));
      expect(serialized, isNot(contains('ingredient_score')));
      expect(serialized, isNot(contains('nutrition_score')));
      expect(serialized, isNot(contains('final_score')));
    });
  });

  test('scan history preserves deferred overall without a numeric value', () {
    final scan = ScanHistory.fromProduct(Product.fromJson(_productJson()));
    final serialized = scan.toJson();
    final restored = ScanHistory.fromJson(serialized);

    expect(serialized, isNot(contains('final_score')));
    expect(
      restored.scoreView.overallScore.availability,
      OverallScoreAvailability.deferred,
    );
    expect(restored.scoreView.ingredientGoodnessPercent.scoreValue, isNull);
  });
}

Map<String, dynamic> _productJson() => {
      'barcode': 'fixture-product',
      'product_name': 'Fixture product',
      'brand': 'Fixture brand',
      'category': 'food',
      'ingredients': <String>[],
      'allergens': <String>[],
    };
