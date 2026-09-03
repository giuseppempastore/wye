import '../models/capture_upload_models.dart';

class CaptureFlowEvent {
  final String step;
  final String statusClass;
  final int? productId;
  final CaptureImagePurpose? purpose;
  final String? requestId;
  final int? productImageId;
  final int? storageObjectId;
  final int? latencyMs;

  const CaptureFlowEvent({
    required this.step,
    required this.statusClass,
    this.productId,
    this.purpose,
    this.requestId,
    this.productImageId,
    this.storageObjectId,
    this.latencyMs,
  });

  Map<String, Object?> toSafeFields() => {
        'step': step,
        'status_class': statusClass,
        'product_id': productId,
        'image_purpose': purpose?.wireValue,
        'request_id': _safeRequestId(requestId),
        'product_image_id': productImageId,
        'storage_object_id': storageObjectId,
        'latency_ms': latencyMs,
      };

  @override
  String toString() => 'CaptureFlowEvent(${toSafeFields()})';
}

abstract class CaptureFlowLogger {
  void record(CaptureFlowEvent event);
}

class NoOpCaptureFlowLogger implements CaptureFlowLogger {
  const NoOpCaptureFlowLogger();

  @override
  void record(CaptureFlowEvent event) {}
}

class CollectingCaptureFlowLogger implements CaptureFlowLogger {
  final List<CaptureFlowEvent> events = [];

  @override
  void record(CaptureFlowEvent event) {
    events.add(event);
  }
}

String? _safeRequestId(String? value) {
  if (value == null || value.isEmpty) {
    return null;
  }
  return RegExp(r'^[A-Za-z0-9._:-]{1,128}$').hasMatch(value)
      ? value
      : '<redacted>';
}
