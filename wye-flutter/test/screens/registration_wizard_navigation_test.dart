import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:wye/config/mobile_upload_config.dart';
import 'package:wye/screens/add_product_screen.dart';

void main() {
  Future<void> pumpWizard(WidgetTester tester) async {
    await tester.pumpWidget(
      Provider<MobileUploadConfig>.value(
        value: MobileUploadConfig(
          enabled: false,
          apiBaseUri: Uri.parse('http://127.0.0.1:8000'),
        ),
        child: const MaterialApp(home: AddProductScreen()),
      ),
    );
    await tester.pump();
  }

  testWidgets('public barcode field is scanner-only and disabled',
      (tester) async {
    await pumpWizard(tester);
    final barcode =
        tester.widget<TextFormField>(find.byType(TextFormField).first);
    expect(barcode.enabled, isFalse);
    final editable =
        tester.widget<EditableText>(find.byType(EditableText).first);
    expect(editable.readOnly, isTrue);
    expect(find.text('Scansiona barcode'), findsOneWidget);
  });

  testWidgets('Android back moves to the previous wizard step', (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.byKey(const ValueKey('wizard-step-3')));
    await tester.pump();
    expect(find.text('Passaggio 4 di 4'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pump();
    expect(find.text('Passaggio 3 di 4'), findsOneWidget);
  });

  testWidgets('delete draft requires explicit confirmation', (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.byKey(const ValueKey('draft-actions-menu')));
    await tester.pumpAndSettle();
    expect(find.text('Salva bozza'), findsOneWidget);
    expect(find.text('Elimina bozza'), findsOneWidget);
    await tester.tap(find.text('Elimina bozza'));
    await tester.pumpAndSettle();
    expect(find.text('Eliminare la bozza?'), findsOneWidget);
    expect(find.text('Mantieni bozza'), findsOneWidget);
  });

  testWidgets('nutrition UI has unambiguous salt and sodium units',
      (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.byKey(const ValueKey('wizard-step-2')));
    await tester.pumpAndSettle();
    expect(find.text('Sale (g)'), findsOneWidget);
    expect(find.text('Sodio (mg)'), findsOneWidget);
    expect(find.text('Sale (mg)'), findsNothing);
    expect(find.text('Energia kJ'), findsOneWidget);
    expect(find.text('Energia kcal'), findsOneWidget);
    expect(find.byKey(const ValueKey('nutrition-basis')), findsOneWidget);
  });

  testWidgets('ingredients can be added, edited and removed as items',
      (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.byKey(const ValueKey('wizard-step-1')));
    await tester.pumpAndSettle();

    final addButton = find.byKey(const ValueKey('ingredient-add'));
    await tester.ensureVisible(addButton);
    await tester.tap(addButton);
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, 'Farina integrale');
    await tester.tap(find.text('Salva'));
    await tester.pumpAndSettle();

    expect(find.text('Farina integrale'), findsWidgets);
    expect(find.text('Corretto dall’utente · Da validare'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('ingredient-item-0')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, 'Avena integrale');
    await tester.tap(find.text('Salva'));
    await tester.pumpAndSettle();
    expect(find.text('Avena integrale'), findsWidgets);

    final chip = tester.widget<InputChip>(
      find.byKey(const ValueKey('ingredient-item-0')),
    );
    chip.onDeleted!();
    await tester.pump();
    expect(find.text('Avena integrale'), findsNothing);
  });

  testWidgets('nutrition rejects negative and implausible values',
      (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.byKey(const ValueKey('wizard-step-2')));
    await tester.pumpAndSettle();

    final energyKj = find.widgetWithText(TextFormField, 'Energia kJ');
    await tester.enterText(energyKj, '-1');
    await tester.pump();
    expect(find.text('Non può essere negativo'), findsOneWidget);

    await tester.enterText(energyKj, '5000');
    await tester.pump();
    expect(find.text('Valore non plausibile'), findsOneWidget);
  });

  testWidgets('each wizard step shows only its own content', (tester) async {
    await pumpWizard(tester);
    expect(find.text('Prodotto'), findsOneWidget);
    expect(find.text('1. Barcode prodotto'), findsOneWidget);
    expect(find.text('Valori nutrizionali'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('wizard-step-1')));
    await tester.pumpAndSettle();
    expect(find.text('Passaggio 2 di 4'), findsOneWidget);
    expect(find.text('Ingredienti'), findsWidgets);
    expect(find.text('1. Barcode prodotto'), findsNothing);
    expect(find.text('Valori nutrizionali'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('wizard-step-2')));
    await tester.pumpAndSettle();
    expect(find.text('Passaggio 3 di 4'), findsOneWidget);
    expect(find.text('Valori nutrizionali'), findsWidgets);
    expect(find.text('Ingredienti'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('wizard-step-3')));
    await tester.pumpAndSettle();
    expect(find.text('Passaggio 4 di 4'), findsOneWidget);
    expect(find.text('Riepilogo'), findsOneWidget);
    expect(find.byKey(const ValueKey('registration-summary')), findsOneWidget);
    expect(find.text('Invia per la verifica'), findsOneWidget);
  });

  testWidgets('wizard exposes one primary action and compact draft menu',
      (tester) async {
    await pumpWizard(tester);
    expect(find.text('Continua'), findsOneWidget);
    expect(find.text('Indietro'), findsNothing);
    expect(find.text('Avanti'), findsNothing);
    expect(find.text('Salva e continua dopo'), findsNothing);
    expect(find.text('Salva come dati da validare'), findsNothing);
    expect(find.byKey(const ValueKey('draft-actions-menu')), findsOneWidget);
  });
}
