import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:wye/screens/home_v2_screen.dart';

void main() {
  Future<void> pumpHome(WidgetTester tester) => tester.pumpWidget(
        const MaterialApp(home: AcquisitionHomeScreen()),
      );

  testWidgets('legacy manual analysis is absent', (tester) async {
    await pumpHome(tester);
    expect(find.text('Analizza Manualmente'), findsNothing);
    expect(find.text('Analizza manualmente'), findsNothing);
  });

  testWidgets('home contains only the two main actions', (tester) async {
    await pumpHome(tester);
    expect(find.byKey(const ValueKey('home-scan-product')), findsOneWidget);
    expect(find.byKey(const ValueKey('home-add-product')), findsOneWidget);
    expect(find.text('Scansiona prodotto'), findsOneWidget);
    expect(find.text('Aggiungi prodotto'), findsOneWidget);
  });

  testWidgets('duplicate recent scans section is absent', (tester) async {
    await pumpHome(tester);
    expect(find.text('Ultimi scansionamenti'), findsNothing);
  });

  testWidgets('history is absent as a home CTA but remains in navigation',
      (tester) async {
    await pumpHome(tester);
    expect(find.byKey(const ValueKey('home-history')), findsNothing);
    expect(find.text('Storico'), findsOneWidget);
    expect(find.byIcon(Icons.history), findsOneWidget);
  });

  testWidgets('technical and premium actions are absent', (tester) async {
    await pumpHome(tester);
    expect(find.text('Registra nuovo prodotto'), findsNothing);
    expect(find.textContaining('Premium'), findsNothing);
    expect(find.text('Upload mobile locale'), findsNothing);
    expect(find.textContaining('Token'), findsNothing);
  });
}
