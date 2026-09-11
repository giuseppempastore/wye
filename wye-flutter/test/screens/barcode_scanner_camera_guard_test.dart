import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';
import 'package:wye/providers/app_providers.dart';
import 'package:wye/screens/barcode_scanner_screen.dart';
import 'package:wye/services/api_client.dart';

void main() {
  testWidgets('zero-camera device shows guidance without mounting CameraX',
      (tester) async {
    final api = ApiClient();
    addTearDown(api.dispose);
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => BarcodeScannerProvider(api)),
          ChangeNotifierProvider(create: (_) => UserPreferencesProvider()),
        ],
        child: MaterialApp(
          home: BarcodeScannerScreen(
            cameraAvailabilityCheck: () async => false,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(MobileScanner), findsNothing);
    expect(find.textContaining('Fotocamera non disponibile'), findsWidgets);
    expect(find.textContaining('camera virtuale'), findsOneWidget);
  });
}
