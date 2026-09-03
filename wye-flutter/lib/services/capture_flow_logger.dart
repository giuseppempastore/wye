import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../models/capture_upload_models.dart';

class CaptureFlowEvent {
  final DateTime? timestamp;
  final String step;
  final String statusClass;
  final int? productId;
  final CaptureImagePurpose? purpose;
  final String? requestId;
  final int? productImageId;
  final int? storageObjectId;
  final int? extractionRunId;
  final int? itemCount;
  final int? httpStatusCode;
  final int? retryCount;
  final int? latencyMs;
  final String? errorCode;
  final String? errorCategory;

  const CaptureFlowEvent({
    this.timestamp,
    required this.step,
    required this.statusClass,
    this.productId,
    this.purpose,
    this.requestId,
    this.productImageId,
    this.storageObjectId,
    this.extractionRunId,
    this.itemCount,
    this.httpStatusCode,
    this.retryCount,
    this.latencyMs,
    this.errorCode,
    this.errorCategory,
  });

  CaptureFlowEvent sanitized({required DateTime fallbackTimestamp}) {
    return CaptureFlowEvent(
      timestamp: (timestamp ?? fallbackTimestamp).toUtc(),
      step: CaptureLogSanitizer.safeStep(step),
      statusClass: CaptureLogSanitizer.safeStatus(statusClass),
      productId: _positiveOrNull(productId),
      purpose: purpose,
      requestId: CaptureLogSanitizer.safeIdentifier(requestId),
      productImageId: _positiveOrNull(productImageId),
      storageObjectId: _positiveOrNull(storageObjectId),
      extractionRunId: _positiveOrNull(extractionRunId),
      itemCount: _nonNegativeOrNull(itemCount),
      httpStatusCode: _statusCodeOrNull(httpStatusCode),
      retryCount: _nonNegativeOrNull(retryCount),
      latencyMs: _nonNegativeOrNull(latencyMs),
      errorCode: CaptureLogSanitizer.safeCode(errorCode),
      errorCategory: CaptureLogSanitizer.safeCode(errorCategory),
    );
  }

  Map<String, Object?> toSafeFields() => {
        'timestamp': timestamp?.toUtc().toIso8601String(),
        'step': CaptureLogSanitizer.safeStep(step),
        'status_class': CaptureLogSanitizer.safeStatus(statusClass),
        'product_id': _positiveOrNull(productId),
        'image_purpose': purpose?.wireValue,
        'request_id': CaptureLogSanitizer.safeIdentifier(requestId),
        'product_image_id': _positiveOrNull(productImageId),
        'storage_object_id': _positiveOrNull(storageObjectId),
        'extraction_run_id': _positiveOrNull(extractionRunId),
        'item_count': _nonNegativeOrNull(itemCount),
        'http_status_code': _statusCodeOrNull(httpStatusCode),
        'retry_count': _nonNegativeOrNull(retryCount),
        'latency_ms': _nonNegativeOrNull(latencyMs),
        'error_code': CaptureLogSanitizer.safeCode(errorCode),
        'error_category': CaptureLogSanitizer.safeCode(errorCategory),
      };

  String toSafeLine() {
    final fields = Map<String, Object?>.from(toSafeFields())
      ..removeWhere((_, value) => value == null);
    return jsonEncode(fields);
  }

  @override
  String toString() => toSafeLine();
}

abstract class CaptureFlowLogger {
  void record(CaptureFlowEvent event);
}

class NoOpCaptureFlowLogger implements CaptureFlowLogger {
  const NoOpCaptureFlowLogger();

  @override
  void record(CaptureFlowEvent event) {}
}

class SanitizedInMemoryCaptureFlowLogger extends ChangeNotifier
    implements CaptureFlowLogger {
  final bool enabled;
  final int capacity;
  final DateTime Function() _clock;
  final List<CaptureFlowEvent> _events = [];

  SanitizedInMemoryCaptureFlowLogger({
    required this.enabled,
    this.capacity = 200,
    DateTime Function()? clock,
  }) : _clock = clock ?? DateTime.now {
    if (capacity <= 0 || capacity > 1000) {
      throw RangeError.range(capacity, 1, 1000, 'capacity');
    }
  }

  List<CaptureFlowEvent> get events => List.unmodifiable(_events);

  String get exportText =>
      _events.map((event) => event.toSafeLine()).join('\n');

  @override
  void record(CaptureFlowEvent event) {
    if (!enabled) {
      return;
    }
    _events.add(event.sanitized(fallbackTimestamp: _clock()));
    if (_events.length > capacity) {
      _events.removeRange(0, _events.length - capacity);
    }
    notifyListeners();
  }

  void clear() {
    if (_events.isEmpty) {
      return;
    }
    _events.clear();
    notifyListeners();
  }
}

class CollectingCaptureFlowLogger extends SanitizedInMemoryCaptureFlowLogger {
  CollectingCaptureFlowLogger()
      : super(enabled: true, capacity: 1000, clock: DateTime.now);
}

abstract final class CaptureLogSanitizer {
  static final _unsafeContent = RegExp(
    r'(bearer\s|x-wye-image-key|https?://|[?&][a-z0-9_-]+=|'
    r'^[a-zA-Z]:[\\/]|^/|[{}\[\]]|[\r\n])',
    caseSensitive: false,
  );
  static final _longEncodedValue = RegExp(r'^[A-Za-z0-9+/=_-]{80,}$');
  static final _safeIdentifier = RegExp(r'^[A-Za-z0-9._:-]{1,128}$');
  static final _safeCode = RegExp(r'^[a-z0-9_]{1,80}$');
  static final _safeStep = RegExp(r'^[a-z0-9_]{1,80}$');
  static final _safeStatus = RegExp(r'^(local|[1-5]xx|success|failure)$');

  static String safeStep(String value) =>
      _safeStep.hasMatch(value) ? value : 'redacted_step';

  static String safeStatus(String value) =>
      _safeStatus.hasMatch(value) ? value : 'failure';

  static String? safeCode(String? value) {
    if (value == null) {
      return null;
    }
    return _safeCode.hasMatch(value) ? value : 'redacted';
  }

  static String? safeIdentifier(String? value) {
    if (value == null || value.isEmpty) {
      return null;
    }
    if (_unsafeContent.hasMatch(value) ||
        _longEncodedValue.hasMatch(value) ||
        !_safeIdentifier.hasMatch(value)) {
      return '<redacted>';
    }
    return value;
  }
}

int? _positiveOrNull(int? value) {
  return value != null && value > 0 ? value : null;
}

int? _nonNegativeOrNull(int? value) {
  return value != null && value >= 0 ? value : null;
}

int? _statusCodeOrNull(int? value) {
  return value != null && value >= 100 && value <= 599 ? value : null;
}
