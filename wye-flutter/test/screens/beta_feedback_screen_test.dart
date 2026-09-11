import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:wye/providers/app_providers.dart';
import 'package:wye/router/app_router.dart';
import 'package:wye/services/api_client.dart';

class _RecordingApiClient extends ApiClient {
  int submissions = 0;

  @override
  Future<String> submitBetaFeedback({
    required String feedbackType,
    required String severity,
    required String message,
    String? expectedBehavior,
    String? actualBehavior,
    bool includeTechnicalContext = false,
  }) async {
    submissions++;
    return 'feedback-test-id';
  }
}

Future<({GoRouter router, _RecordingApiClient api})> _pumpApp(
  WidgetTester tester, {
  String initialLocation = '/settings',
}) async {
  final router = AppRouter.createRouter(initialLocation: initialLocation);
  final api = _RecordingApiClient();
  addTearDown(router.dispose);
  addTearDown(api.dispose);
  await tester.pumpWidget(
    MultiProvider(
      providers: [
        Provider<ApiClient>.value(value: api),
        ChangeNotifierProvider(create: (_) => UserPreferencesProvider()),
      ],
      child: MaterialApp.router(routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
  return (router: router, api: api);
}

Future<void> _openFromSettings(WidgetTester tester) async {
  final feedbackTile = find.byKey(const ValueKey('open-beta-feedback'));
  await tester.scrollUntilVisible(
    feedbackTile,
    300,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.tap(feedbackTile);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows a back arrow and returns once to Settings',
      (tester) async {
    final harness = await _pumpApp(tester);
    await _openFromSettings(tester);

    expect(find.byKey(const ValueKey('feedback-back-button')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('feedback-back-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('open-beta-feedback')), findsOneWidget);
    expect(harness.router.canPop(), isFalse);
    expect(find.text('Uscire senza inviare?'), findsNothing);
  });

  testWidgets('Android back matches the arrow and does not close the app',
      (tester) async {
    final harness = await _pumpApp(tester);
    await _openFromSettings(tester);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('open-beta-feedback')), findsOneWidget);
    expect(harness.router.canPop(), isFalse);
  });

  testWidgets('direct feedback route falls back to Home', (tester) async {
    await _pumpApp(tester, initialLocation: '/feedback');

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('home-scan-product')), findsOneWidget);
    expect(find.byKey(const ValueKey('home-add-product')), findsOneWidget);
  });

  testWidgets('edited form asks before leaving and keeps text on cancel',
      (tester) async {
    await _pumpApp(tester);
    await _openFromSettings(tester);
    await tester.enterText(
      find.byKey(const ValueKey('feedback-message')),
      'Il pulsante non risponde',
    );
    await tester.pump();

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Uscire senza inviare?'), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('continue-feedback-editing')),
    );
    await tester.pumpAndSettle();
    expect(find.text('Il pulsante non risponde'), findsOneWidget);
    expect(find.text('Lascia feedback'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('discard-feedback')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('open-beta-feedback')), findsOneWidget);
  });

  testWidgets('successful submit clears the form and is not repeated on back',
      (tester) async {
    final harness = await _pumpApp(tester);
    await _openFromSettings(tester);
    await tester.enterText(
      find.byKey(const ValueKey('feedback-message')),
      'Flusso completato correttamente',
    );
    await tester.drag(find.byType(ListView), const Offset(0, -900));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('submit-feedback')));
    await tester.pumpAndSettle();
    expect(harness.api.submissions, 1);
    expect(find.text('Feedback inviato. Grazie!'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('open-beta-feedback')), findsOneWidget);
    expect(find.text('Uscire senza inviare?'), findsNothing);
    expect(harness.api.submissions, 1);
  });

  testWidgets('empty message is rejected without calling the backend',
      (tester) async {
    final harness = await _pumpApp(tester, initialLocation: '/feedback');
    await tester.drag(find.byType(ListView), const Offset(0, -900));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('submit-feedback')));
    await tester.pump();
    expect(find.text('Scrivi almeno 5 caratteri.'), findsOneWidget);
    expect(harness.api.submissions, 0);
  });
}
