import 'package:flutter_test/flutter_test.dart';
import 'package:wye/services/product_barcode_validator.dart';

void main() {
  const validator = ProductBarcodeValidator();

  group('canonical product barcode validation', () {
    final validCases = <String, ProductBarcodeKind>{
      '96385074': ProductBarcodeKind.ean8,
      '036000291452': ProductBarcodeKind.upcA,
      '4006381333931': ProductBarcodeKind.ean13,
      '10012345678902': ProductBarcodeKind.gtin14,
      ' 4006381333931 ': ProductBarcodeKind.ean13,
    };
    for (final entry in validCases.entries) {
      test('accepts ${entry.value.name}', () {
        final result = validator.validate(entry.key);
        expect(result.isValid, isTrue);
        expect(result.kind, entry.value);
        expect(result.value, entry.key.trim());
      });
    }

    final invalidCases = <String, String>{
      '': 'empty',
      '1234567': 'invalid_length',
      '123456789': 'invalid_length',
      '4006381333932': 'invalid_checksum',
      '036000291453': 'invalid_checksum',
      'ABC4006381333931': 'non_numeric',
      'https://example.test/4006381333931': 'non_numeric',
      '4006 381333931': 'non_numeric',
      '４００６３８１３３３９３１': 'non_numeric',
    };
    for (final entry in invalidCases.entries) {
      test('rejects ${entry.value}', () {
        final result = validator.validate(entry.key);
        expect(result.isValid, isFalse);
        expect(result.reason, entry.value);
        expect(result.value, isNull);
      });
    }
  });

  test('duplicate scan is accepted only after debounce window', () {
    final gate = BarcodeScanDebouncer();
    final now = DateTime.utc(2026, 9, 6);
    expect(gate.shouldAccept('4006381333931', now), isTrue);
    expect(
      gate.shouldAccept(
        '4006381333931',
        now.add(const Duration(milliseconds: 200)),
      ),
      isFalse,
    );
    expect(
      gate.shouldAccept(
        '4006381333931',
        now.add(const Duration(milliseconds: 1800)),
      ),
      isTrue,
    );
  });

  test('safe log never contains the barcode value', () {
    final result = validator.validate('4006381333931');
    expect(result.safeLog, isNot(contains('4006381333931')));
    expect(result.safeLog, contains('length=13'));
  });
}
