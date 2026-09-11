import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:wye/config/mobile_upload_config.dart';
import 'package:wye/router/app_router.dart';
import 'package:wye/services/ai_usage_quota_service.dart';
import 'package:wye/services/anonymous_installation_service.dart';

void main() {
  testWidgets('Home, Add product and Analyze label preserve back hierarchy',
      (tester) async {
    final router = AppRouter.createRouter();
    addTearDown(router.dispose);
    final quota = AiUsageQuotaService(
      installation: AnonymousInstallationService(),
    );
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: quota),
          Provider.value(
            value: MobileUploadConfig(
              enabled: false,
              apiBaseUri: Uri.parse('http://127.0.0.1:8000'),
            ),
          ),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('home-add-product')));
    await tester.pumpAndSettle();
    expect(find.text('Come vuoi procedere?'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('add-option-analyze-label')));
    await tester.pumpAndSettle();
    expect(find.text('Analizza un’etichetta'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Come vuoi procedere?'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('home-add-product')), findsOneWidget);
  });

  testWidgets('registration back at first step returns to Add product',
      (tester) async {
    final router = AppRouter.createRouter(initialLocation: '/add-product');
    addTearDown(router.dispose);
    final quota = AiUsageQuotaService(
      installation: AnonymousInstallationService(),
    );
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: quota),
          Provider.value(
            value: MobileUploadConfig(
              enabled: false,
              apiBaseUri: Uri.parse('http://127.0.0.1:8000'),
            ),
          ),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('add-option-register-product')));
    await tester.pumpAndSettle();
    expect(find.text('Registra nuovo prodotto'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Come vuoi procedere?'), findsOneWidget);
  });
}
