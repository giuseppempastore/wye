import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:wye/config/mobile_upload_config.dart';
import 'package:wye/models/capture_upload_error.dart';
import 'package:wye/models/capture_upload_models.dart';
import 'package:wye/models/extraction_models.dart';
import 'package:wye/providers/app_providers.dart';
import 'package:wye/providers/capture_upload_controller.dart';
import 'package:wye/screens/add_product_screen.dart';
import 'package:wye/screens/settings_screen.dart';
import 'package:wye/services/fake_capture_upload_gateway.dart';
import 'package:wye/services/image_metadata_service.dart';
import 'package:wye/widgets/dev_mobile_upload_widgets.dart';

void main() {
  testWidgets('dev token UI is hidden when the feature flag is false',
      (tester) async {
    final harness = _Harness(enabled: false);
    addTearDown(harness.dispose);

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          Provider<MobileUploadConfig>.value(value: harness.config),
          ChangeNotifierProvider<UserPreferencesProvider>(
            create: (_) => UserPreferencesProvider(),
          ),
          ChangeNotifierProvider<CaptureUploadController>.value(
            value: harness.controller,
          ),
        ],
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );

    expect(find.byKey(const Key('dev-mobile-token-panel')), findsNothing);
    expect(find.text('Upload mobile - sviluppo'), findsNothing);

    await tester.pumpWidget(
      Provider<MobileUploadConfig>.value(
        value: harness.config,
        child: const MaterialApp(home: AddProductScreen()),
      ),
    );
    expect(find.byKey(const Key('dev-mobile-capture-panel')), findsNothing);
  });

  testWidgets('dev token and capture surfaces are visible when enabled',
      (tester) async {
    final harness = _Harness();
    addTearDown(harness.dispose);

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          Provider<MobileUploadConfig>.value(value: harness.config),
          ChangeNotifierProvider<UserPreferencesProvider>(
            create: (_) => UserPreferencesProvider(),
          ),
          ChangeNotifierProvider<CaptureUploadController>.value(
            value: harness.controller,
          ),
        ],
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    expect(find.byKey(const Key('dev-mobile-token-panel')), findsOneWidget);

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          Provider<MobileUploadConfig>.value(value: harness.config),
          ChangeNotifierProvider<CaptureUploadController>.value(
            value: harness.controller,
          ),
        ],
        child: const MaterialApp(home: AddProductScreen()),
      ),
    );
    expect(find.byKey(const Key('dev-mobile-capture-panel')), findsOneWidget);
  });

  testWidgets('token can be entered, is redacted, and can be cleared',
      (tester) async {
    final harness = _Harness();
    addTearDown(harness.dispose);
    await _pumpPanels(tester, harness);
    const secret = 'temporary-sensitive-token';

    expect(
      tester
          .widget<TextField>(
            find.byKey(const Key('dev-mobile-token-field')),
          )
          .obscureText,
      isTrue,
    );

    await tester.enterText(
      find.byKey(const Key('dev-mobile-token-field')),
      secret,
    );
    await tester.pump();
    await tester.ensureVisible(find.byKey(const Key('dev-mobile-token-save')));
    await tester.tap(find.byKey(const Key('dev-mobile-token-save')));
    await tester.pump();

    expect(harness.controller.tokenState, DevMobileTokenState.present);
    expect(find.textContaining('Token presente'), findsOneWidget);
    expect(find.textContaining(secret), findsNothing);

    await tester.tap(find.byKey(const Key('dev-mobile-token-clear')));
    await tester.pump();

    expect(harness.controller.tokenState, DevMobileTokenState.missing);
    expect(find.text('Token mancante'), findsWidgets);
  });

  testWidgets('expired token is explicit and blocks capture', (tester) async {
    final harness = _Harness();
    addTearDown(harness.dispose);
    harness.controller.setTemporaryToken(
      'expired-sensitive-token',
      expiresAt: DateTime.now().toUtc().subtract(const Duration(seconds: 1)),
    );

    await _pumpPanels(tester, harness);
    await tester.enterText(
      find.byKey(const Key('dev-mobile-product-id-field')),
      '7',
    );
    await tester.enterText(
      find.byKey(const Key('dev-mobile-barcode-field')),
      '8001234567890',
    );
    await tester.pump();

    expect(find.text('Token scaduto'), findsWidgets);
    expect(
      tester
          .widget<OutlinedButton>(
            find.byKey(const Key('dev-mobile-pick-image')),
          )
          .onPressed,
      isNull,
    );
    expect(find.textContaining('expired-sensitive-token'), findsNothing);
  });

  test('temporary token is not available in a new in-memory session', () {
    final first = _Harness();
    first.controller.setTemporaryToken(
      'temporary-sensitive-token',
      expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
    );
    expect(first.controller.tokenState, DevMobileTokenState.present);
    first.dispose();

    final second = _Harness();
    expect(second.controller.tokenState, DevMobileTokenState.missing);
    second.dispose();
  });

  testWidgets('capture actions require token and product ID', (tester) async {
    final harness = _Harness();
    addTearDown(harness.dispose);
    await _pumpPanels(tester, harness);

    expect(_pickButton(tester).onPressed, isNull);
    expect(_uploadButton(tester).onPressed, isNull);
    expect(find.text('Token mancante'), findsWidgets);

    harness.setUsableToken();
    await tester.pump();
    await tester.enterText(
      find.byKey(const Key('dev-mobile-barcode-field')),
      '8001234567890',
    );
    await tester.pump();

    expect(_pickButton(tester).onPressed, isNull);
    expect(find.text('Product ID richiesto'), findsOneWidget);

    await tester.enterText(
      find.byKey(const Key('dev-mobile-product-id-field')),
      '7',
    );
    await tester.pump();

    expect(_pickButton(tester).onPressed, isNotNull);
    expect(_uploadButton(tester).onPressed, isNull);
  });

  testWidgets('purpose selection and fake upload reach associated state',
      (tester) async {
    final harness = _Harness();
    addTearDown(harness.dispose);
    harness.setUsableToken();
    const secret = 'temporary-sensitive-token';
    await _pumpPanels(
      tester,
      harness,
      pickImageBytes: () async =>
          Uint8List.fromList([0xff, 0xd8, 0xff, 1, 2, 3]),
    );
    await tester.enterText(
      find.byKey(const Key('dev-mobile-product-id-field')),
      '7',
    );
    await tester.enterText(
      find.byKey(const Key('dev-mobile-barcode-field')),
      '8001234567890',
    );
    await tester.pump();
    await tester.ensureVisible(
      find.byKey(const Key('dev-mobile-purpose-field')),
    );
    await tester.tap(find.byKey(const Key('dev-mobile-purpose-field')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Fronte prodotto').last);
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('dev-mobile-pick-image')));
    await tester.tap(find.byKey(const Key('dev-mobile-pick-image')));
    await tester.pumpAndSettle();
    expect(harness.controller.state.step, UploadFlowStep.metadataReady);

    await tester.ensureVisible(find.byKey(const Key('dev-mobile-upload')));
    await tester.tap(find.byKey(const Key('dev-mobile-upload')));
    await tester.pumpAndSettle();

    expect(harness.controller.state.step, UploadFlowStep.uploadedAssociated);
    expect(harness.gateway.calls, ['initialize', 'put', 'finalize']);
    expect(
      harness.gateway.initializeRequest!.purpose,
      CaptureImagePurpose.productFront,
    );
    expect(
      harness.gateway.initializeRequest!.metadata.sha256,
      const Sha256DigestService().hash(harness.gateway.uploadedBytes!),
    );
    expect(find.text('Upload completato e immagine associata'), findsOneWidget);
    expect(
      find.text('Estrazione non disponibile per questa immagine'),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('dev-mobile-extraction-start')),
      findsNothing,
    );

    final visibleText = tester
        .widgetList<Text>(find.byType(Text))
        .map((widget) => widget.data ?? '')
        .join('\n');
    expect(visibleText, isNot(contains(secret)));
    expect(visibleText, isNot(contains('signature=')));
    expect(visibleText, isNot(contains('upload.invalid')));
    expect(visibleText, isNot(contains('base64')));
    expect(harness.gateway.calls, everyElement(isNot(contains('analyze'))));
    expect(harness.gateway.calls, everyElement(isNot(contains('score'))));
  });

  testWidgets('ingredients upload can start extraction and show safe items',
      (tester) async {
    final harness = _Harness();
    addTearDown(harness.dispose);
    harness.setUsableToken();
    harness.gateway.extractionResult = ExtractionResultSummary(
      run: const ExtractionRunRef(
        extractionRunId: 501,
        status: ExtractionStatus.succeeded,
      ),
      items: const [
        ExtractionItem(
          extractionItemId: 601,
          type: ExtractionItemType.ingredient,
          rawText: 'sale',
          normalizedText: 'sale',
          status: ExtractionItemStatus.detected,
        ),
      ],
    );
    await _pumpPanels(
      tester,
      harness,
      pickImageBytes: () async =>
          Uint8List.fromList([0xff, 0xd8, 0xff, 4, 5, 6]),
    );
    await tester.enterText(
      find.byKey(const Key('dev-mobile-product-id-field')),
      '8',
    );
    await tester.enterText(
      find.byKey(const Key('dev-mobile-barcode-field')),
      '8001234567890',
    );
    await tester.pump();

    await tester.ensureVisible(find.byKey(const Key('dev-mobile-pick-image')));
    await tester.tap(find.byKey(const Key('dev-mobile-pick-image')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('dev-mobile-upload')));
    await tester.tap(find.byKey(const Key('dev-mobile-upload')));
    await tester.pumpAndSettle();

    expect(harness.controller.state.step, UploadFlowStep.extractionDeferred);
    expect(
      find.text('Upload associato; estrazione non avviata'),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('dev-mobile-extraction-start')),
      findsOneWidget,
    );

    await tester.ensureVisible(
      find.byKey(const Key('dev-mobile-extraction-start')),
    );
    await tester.tap(find.byKey(const Key('dev-mobile-extraction-start')));
    await tester.pumpAndSettle();

    expect(
        harness.controller.extractionState.step, ExtractionFlowStep.succeeded);
    expect(find.text('Estrazione completata: 1 elementi disponibili'),
        findsOneWidget);
    expect(find.text('sale'), findsOneWidget);
    expect(harness.gateway.calls.last, 'extraction-start');
    final visibleText = tester
        .widgetList<Text>(find.byType(Text))
        .map((widget) => widget.data ?? '')
        .join('\n');
    expect(visibleText, isNot(contains('temporary-sensitive-token')));
    expect(visibleText, isNot(contains('signature=')));
    expect(visibleText, isNot(contains('base64')));
    expect(visibleText, isNot(contains('score')));
  });

  testWidgets('metadata failure blocks upload before the gateway',
      (tester) async {
    final harness = _Harness(
      metadataService: const _FailingMetadataService(),
    );
    addTearDown(harness.dispose);
    harness.setUsableToken();
    await _pumpPanels(
      tester,
      harness,
      pickImageBytes: () async => Uint8List.fromList([1, 2, 3]),
    );
    await tester.enterText(
      find.byKey(const Key('dev-mobile-product-id-field')),
      '9',
    );
    await tester.enterText(
      find.byKey(const Key('dev-mobile-barcode-field')),
      '8001234567890',
    );
    await tester.pump();

    await tester.ensureVisible(find.byKey(const Key('dev-mobile-pick-image')));
    await tester.tap(find.byKey(const Key('dev-mobile-pick-image')));
    await tester.pumpAndSettle();

    expect(harness.controller.state.step, UploadFlowStep.failedTerminal);
    expect(harness.gateway.calls, isEmpty);
    expect(_uploadButton(tester).onPressed, isNull);
    expect(find.textContaining('Upload bloccato'), findsOneWidget);
  });
}

Future<void> _pumpPanels(
  WidgetTester tester,
  _Harness harness, {
  DevImageBytesPicker? pickImageBytes,
}) async {
  await tester.pumpWidget(
    ChangeNotifierProvider<CaptureUploadController>.value(
      value: harness.controller,
      child: MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: Column(
              children: [
                const DevMobileUploadTokenPanel(),
                DevMobileCaptureUploadPanel(
                  pickImageBytes: pickImageBytes,
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

OutlinedButton _pickButton(WidgetTester tester) =>
    tester.widget<OutlinedButton>(
      find.byKey(const Key('dev-mobile-pick-image')),
    );

ElevatedButton _uploadButton(WidgetTester tester) =>
    tester.widget<ElevatedButton>(
      find.byKey(const Key('dev-mobile-upload')),
    );

class _Harness {
  final bool enabled;
  final ImageMetadataService metadataService;
  late final MobileUploadConfig config;
  late final InMemoryMobileUploadTokenProvider tokenProvider;
  late final FakeCaptureUploadGateway gateway;
  late final CaptureUploadController controller;

  _Harness({
    this.enabled = true,
    this.metadataService = const Sha256ImageMetadataService(),
  }) {
    config = MobileUploadConfig(
      enabled: enabled,
      apiBaseUri: Uri.parse('http://api.invalid:8000'),
    );
    tokenProvider = InMemoryMobileUploadTokenProvider();
    gateway = FakeCaptureUploadGateway();
    controller = CaptureUploadController(
      config: config,
      tokenProvider: tokenProvider,
      gateway: gateway,
      metadataService: metadataService,
    );
  }

  void setUsableToken() {
    controller.setTemporaryToken(
      'temporary-sensitive-token',
      expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 5)),
    );
  }

  void dispose() {
    controller.dispose();
    gateway.close();
  }
}

class _FailingMetadataService implements ImageMetadataService {
  const _FailingMetadataService();

  @override
  Future<ImageMetadata> inspect(Uint8List bytes) async {
    throw const CaptureUploadException(
      kind: CaptureUploadFailureKind.invalidInput,
      code: 'unsupported_image_format',
      safeMessage: 'Image format is not supported',
      retryable: false,
      lastStableStep: UploadFlowStep.imageSelected,
    );
  }
}
