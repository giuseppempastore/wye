import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:wye/screens/add_product_options_screen.dart';
import 'package:wye/services/ai_usage_quota_service.dart';
import 'package:wye/services/anonymous_installation_service.dart';

void main() {
  testWidgets('both add-product paths are enabled for Base', (tester) async {
    final quota = AiUsageQuotaService(
      installation: AnonymousInstallationService(),
    );
    await tester.pumpWidget(
      ChangeNotifierProvider.value(
        value: quota,
        child: const MaterialApp(home: AddProductOptionsScreen()),
      ),
    );
    expect(find.text('Analizza un’etichetta'), findsOneWidget);
    expect(find.text('Registra un nuovo prodotto'), findsOneWidget);
    expect(
        find.textContaining('Analisi AI disponibili oggi: 3'), findsOneWidget);
    expect(find.byIcon(Icons.lock_outline), findsNothing);
    expect(find.byType(BackButton), findsOneWidget);

    for (var index = 0; index < 3; index++) {
      quota.simulateBillableCallForTest();
    }
    await tester.pump();
    expect(find.text('Registra un nuovo prodotto'), findsOneWidget);
    final cards = tester.widgetList<InkWell>(find.byType(InkWell));
    expect(cards.every((card) => card.onTap != null), isTrue);
  });
}
