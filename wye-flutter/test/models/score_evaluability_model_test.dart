import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/score_evaluability_model.dart';

void main() {
  late Map<String, dynamic> fixtures;

  setUpAll(() {
    final fixtureFile = File(
      'test/fixtures/score_evaluability/assessment_cases.json',
    );
    fixtures =
        jsonDecode(fixtureFile.readAsStringSync()) as Map<String, dynamic>;
  });

  group('ScoreEvaluation', () {
    test('accepts zero as a valid computable score', () {
      final evaluation = ScoreEvaluation.fromJson(
        _fixture(fixtures, 'computable_zero'),
      );

      expect(evaluation.evaluabilityStatus, EvaluabilityStatus.computable);
      expect(evaluation.scoreValue, 0);
    });

    test('accepts 100 as a valid computable score', () {
      final evaluation = ScoreEvaluation.fromJson(
        _fixture(fixtures, 'computable_hundred'),
      );

      expect(evaluation.evaluabilityStatus, EvaluabilityStatus.computable);
      expect(evaluation.scoreValue, 100);
    });

    test('rejects computable scores outside 0 through 100', () {
      expect(
        () => ScoreEvaluation(
          evaluabilityStatus: EvaluabilityStatus.computable,
          scoreValue: -1,
        ),
        throwsRangeError,
      );
      expect(
        () => ScoreEvaluation(
          evaluabilityStatus: EvaluabilityStatus.computable,
          scoreValue: 101,
        ),
        throwsRangeError,
      );
    });

    test('represents not_computable without a numeric score', () {
      final evaluation = ScoreEvaluation.fromJson(
        _fixture(fixtures, 'not_computable'),
      );

      expect(
        evaluation.evaluabilityStatus,
        EvaluabilityStatus.notComputable,
      );
      expect(evaluation.scoreValue, isNull);
      expect(evaluation.missingInputs, isNotEmpty);
    });

    test('represents non_applicable without a numeric score', () {
      final evaluation = ScoreEvaluation.fromJson(
        _fixture(fixtures, 'non_applicable'),
      );

      expect(
        evaluation.evaluabilityStatus,
        EvaluabilityStatus.nonApplicable,
      );
      expect(evaluation.scoreValue, isNull);
    });

    test('does not convert a missing score to zero', () {
      final unavailable = ScoreEvaluation.fromJson(
        _fixture(fixtures, 'not_computable'),
      );

      expect(unavailable.scoreValue, isNull);
      expect(
        () => ScoreEvaluation.fromJson({
          'evaluability_status': 'computable',
        }),
        throwsArgumentError,
      );
    });

    test('rejects numeric scores for non-computable states', () {
      for (final status in const [
        EvaluabilityStatus.notComputable,
        EvaluabilityStatus.nonApplicable,
      ]) {
        expect(
          () => ScoreEvaluation(
            evaluabilityStatus: status,
            scoreValue: 0,
          ),
          throwsArgumentError,
        );
      }
    });

    test('keeps qualifiers separate and does not alter the score', () {
      final evaluation = ScoreEvaluation.fromJson(
        _fixture(fixtures, 'computable_zero'),
      );

      expect(evaluation.scoreValue, 0);
      expect(evaluation.assessmentCoveragePercent, 42);
      expect(evaluation.confidenceState, 'fixture_low');
      expect(evaluation.missingInputs.single.code,
          'fixture_optional_input_missing');
      expect(
          evaluation.uncertainties.single.code, 'fixture_identity_uncertainty');
      expect(evaluation.explanations.single.code, 'fixture_computed_endpoint');
      expect(evaluation.disclosures.single.code, 'fixture_informational_only');
    });
  });

  group('ProductScoreView', () {
    test('keeps ingredient and nutrition goodness independent', () {
      final product = ProductScoreView.fromJson(
        _fixture(fixtures, 'product_independent_components'),
      );

      expect(product.ingredientGoodnessPercent.scoreValue, 0);
      expect(product.nutritionGoodnessPercent.scoreValue, 100);
      expect(
        product.ingredientGoodnessPercent.scoreValue,
        isNot(product.nutritionGoodnessPercent.scoreValue),
      );
    });

    test('represents overall score as deferred without a numeric field', () {
      final product = ProductScoreView.fromJson(
        _fixture(fixtures, 'product_independent_components'),
      );

      expect(
        product.overallScore.availability,
        OverallScoreAvailability.deferred,
      );
      expect(product.overallScore.toJson(), isNot(contains('score_value')));
      expect(
        product.overallScore.toJson(),
        isNot(contains('overall_goodness_percent')),
      );
    });

    test('rejects an overall state carrying a numeric value', () {
      expect(
        () => OverallScoreState.fromJson({
          'availability': 'deferred',
          'overall_goodness_percent': 50,
        }),
        throwsFormatException,
      );
    });
  });
}

Map<String, dynamic> _fixture(
  Map<String, dynamic> fixtures,
  String name,
) {
  return Map<String, dynamic>.from(fixtures[name] as Map);
}
