import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/score_evaluability_model.dart';
import 'package:wye/widgets/score_widgets.dart';

void main() {
  testWidgets('computable zero is displayed as an explicit component value',
      (tester) async {
    final scoreView = ProductScoreView(
      ingredientGoodnessPercent: ScoreEvaluation.computable(scoreValue: 0),
      nutritionGoodnessPercent: ScoreEvaluation.notComputable(),
      overallScore: OverallScoreState.deferred(),
    );

    await _pumpScoreCard(tester, scoreView);

    expect(
        find.byKey(const ValueKey('ingredient-score-value')), findsOneWidget);
    expect(find.text('0 su 100'), findsOneWidget);
    expect(find.text('Ingredienti'), findsOneWidget);
    expect(find.text('Nutrizione'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('nutrition-not-computable')),
      findsOneWidget,
    );
  });

  testWidgets('not computable has a neutral state and no component score',
      (tester) async {
    await _pumpScoreCard(tester, ProductScoreView.unavailable());

    expect(find.text('Non calcolabile'), findsNWidgets(2));
    expect(find.byKey(const ValueKey('ingredient-score-value')), findsNothing);
    expect(find.byKey(const ValueKey('nutrition-score-value')), findsNothing);
    expect(find.text('0 su 100'), findsNothing);
  });

  testWidgets('non applicable remains distinct and has no component score',
      (tester) async {
    final scoreView = ProductScoreView(
      ingredientGoodnessPercent: ScoreEvaluation.nonApplicable(),
      nutritionGoodnessPercent: ScoreEvaluation.notComputable(),
      overallScore: OverallScoreState(
        availability: OverallScoreAvailability.unavailable,
      ),
    );

    await _pumpScoreCard(tester, scoreView);

    expect(
      find.byKey(const ValueKey('ingredient-non-applicable')),
      findsOneWidget,
    );
    expect(find.text('Non applicabile'), findsOneWidget);
    expect(find.text('Non calcolabile'), findsOneWidget);
    expect(find.byKey(const ValueKey('ingredient-score-value')), findsNothing);
  });

  testWidgets('overall deferred and unavailable states render without a score',
      (tester) async {
    await _pumpScoreCard(tester, ProductScoreView.unavailable());

    expect(find.text('Valutazione complessiva'), findsOneWidget);
    expect(find.text('Differita per questa fase MVP'), findsOneWidget);
    expect(find.byKey(const ValueKey('overall-result-state')), findsOneWidget);
    expect(find.byType(LinearProgressIndicator), findsNothing);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    final unavailable = ProductScoreView(
      ingredientGoodnessPercent: ScoreEvaluation.notComputable(),
      nutritionGoodnessPercent: ScoreEvaluation.notComputable(),
      overallScore: OverallScoreState(
        availability: OverallScoreAvailability.unavailable,
      ),
    );

    await _pumpScoreCard(tester, unavailable);

    expect(
      find.text('Non disponibile per questa fase MVP'),
      findsOneWidget,
    );
  });

  testWidgets('components and supporting qualifiers render independently',
      (tester) async {
    final scoreView = ProductScoreView(
      ingredientGoodnessPercent: ScoreEvaluation.notComputable(
        assessmentCoveragePercent: 40,
        confidenceState: 'limited',
        missingInputs: [AssessmentDetail(code: 'ingredients_missing')],
        uncertainties: [AssessmentDetail(code: 'identity_uncertain')],
      ),
      nutritionGoodnessPercent: ScoreEvaluation.computable(scoreValue: 72),
      overallScore: OverallScoreState.deferred(),
    );

    await _pumpScoreCard(tester, scoreView);

    expect(find.text('Ingredienti'), findsOneWidget);
    expect(find.text('Non calcolabile'), findsOneWidget);
    expect(find.text('Nutrizione'), findsOneWidget);
    expect(find.text('72 su 100'), findsOneWidget);
    expect(find.text('Copertura: 40%'), findsOneWidget);
    expect(find.text('Confidenza: limited'), findsOneWidget);
    expect(find.text('Dati mancanti dichiarati: 1'), findsOneWidget);
    expect(find.text('Incertezze dichiarate: 1'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('ingredient-supporting-details')),
      findsOneWidget,
    );
  });

  testWidgets('score surface does not use safety score wording',
      (tester) async {
    await _pumpScoreCard(tester, ProductScoreView.unavailable());

    expect(find.textContaining('Safety Score'), findsNothing);
    expect(find.textContaining('salubrità'), findsNothing);
  });
}

Future<void> _pumpScoreCard(
  WidgetTester tester,
  ProductScoreView scoreView,
) {
  return tester.pumpWidget(
    MaterialApp(
      home: Scaffold(body: ScoreCard(scoreView: scoreView)),
    ),
  );
}
