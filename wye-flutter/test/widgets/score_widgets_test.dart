import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/score_evaluability_model.dart';
import 'package:wye/widgets/score_widgets.dart';

void main() {
  testWidgets('deferred overall does not require or render a number',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ScoreCard(scoreView: ProductScoreView.unavailable()),
        ),
      ),
    );

    expect(find.text('/100'), findsNothing);
    expect(find.byIcon(Icons.info_outline), findsOneWidget);
  });

  testWidgets('explicit computable component zero remains visible',
      (tester) async {
    final scoreView = ProductScoreView(
      ingredientGoodnessPercent: ScoreEvaluation.computable(scoreValue: 0),
      nutritionGoodnessPercent: ScoreEvaluation.notComputable(),
      overallScore: OverallScoreState.deferred(),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ScoreCard(scoreView: scoreView)),
      ),
    );

    expect(find.text('0'), findsOneWidget);
    expect(find.text('Ingredienti'), findsOneWidget);
    expect(find.text('Nutrizione'), findsNothing);
    expect(find.text('/100'), findsNothing);
  });
}
