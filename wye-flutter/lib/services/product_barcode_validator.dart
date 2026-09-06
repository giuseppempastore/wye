enum ProductBarcodeKind { ean8, upcA, ean13, gtin14 }

class ProductBarcodeValidation {
  final bool isValid;
  final String? value;
  final ProductBarcodeKind? kind;
  final int length;
  final String reason;

  const ProductBarcodeValidation._({
    required this.isValid,
    required this.value,
    required this.kind,
    required this.length,
    required this.reason,
  });

  String get safeLog =>
      'barcode_validation kind=${kind?.name ?? 'unknown'} length=$length '
      'result=${isValid ? 'valid' : 'invalid'} reason=$reason';
}

class ProductBarcodeValidator {
  const ProductBarcodeValidator();

  ProductBarcodeValidation validate(String rawValue) {
    final value = rawValue.trim();
    if (value.isEmpty) {
      return const ProductBarcodeValidation._(
        isValid: false,
        value: null,
        kind: null,
        length: 0,
        reason: 'empty',
      );
    }
    if (!RegExp(r'^\d+$').hasMatch(value)) {
      return ProductBarcodeValidation._(
        isValid: false,
        value: null,
        kind: null,
        length: value.length,
        reason: 'non_numeric',
      );
    }
    final kind = switch (value.length) {
      8 => ProductBarcodeKind.ean8,
      12 => ProductBarcodeKind.upcA,
      13 => ProductBarcodeKind.ean13,
      14 => ProductBarcodeKind.gtin14,
      _ => null,
    };
    if (kind == null) {
      return ProductBarcodeValidation._(
        isValid: false,
        value: null,
        kind: null,
        length: value.length,
        reason: 'invalid_length',
      );
    }

    var sum = 0;
    for (var index = value.length - 2, position = 1;
        index >= 0;
        index--, position++) {
      final digit = int.parse(value[index]);
      sum += digit * (position.isOdd ? 3 : 1);
    }
    final expected = (10 - (sum % 10)) % 10;
    if (expected != int.parse(value[value.length - 1])) {
      return ProductBarcodeValidation._(
        isValid: false,
        value: null,
        kind: kind,
        length: value.length,
        reason: 'invalid_checksum',
      );
    }
    return ProductBarcodeValidation._(
      isValid: true,
      value: value,
      kind: kind,
      length: value.length,
      reason: 'ok',
    );
  }
}

class BarcodeScanDebouncer {
  final Duration duplicateWindow;
  String? _lastValue;
  DateTime? _lastAcceptedAt;

  BarcodeScanDebouncer({
    this.duplicateWindow = const Duration(milliseconds: 1800),
  });

  bool shouldAccept(String canonicalValue, DateTime now) {
    if (_lastValue == canonicalValue &&
        _lastAcceptedAt != null &&
        now.difference(_lastAcceptedAt!) < duplicateWindow) {
      return false;
    }
    _lastValue = canonicalValue;
    _lastAcceptedAt = now;
    return true;
  }
}
