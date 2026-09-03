enum ExtractionStatus { pending, running, succeeded, failed, superseded }

enum ExtractionItemType {
  ingredient,
  ingredientList,
  nutrition,
  allergen,
  quantity,
  unit,
  other,
}

enum ExtractionItemStatus { detected, validated, rejected }

class ExtractionRunRef {
  final int extractionRunId;
  final int? labelDocumentId;
  final ExtractionStatus status;
  final String? errorCode;
  final DateTime? createdAt;
  final DateTime? startedAt;
  final DateTime? completedAt;

  const ExtractionRunRef({
    required this.extractionRunId,
    required this.status,
    this.labelDocumentId,
    this.errorCode,
    this.createdAt,
    this.startedAt,
    this.completedAt,
  });

  factory ExtractionRunRef.fromJson(Map<String, dynamic> json) {
    final labelDocumentId = json['label_document_id'];
    if (labelDocumentId != null &&
        (labelDocumentId is! int || labelDocumentId <= 0)) {
      throw const FormatException(
        'label_document_id must be a positive integer or absent',
      );
    }
    return ExtractionRunRef(
      extractionRunId: _requiredPositiveInt(json, 'id'),
      labelDocumentId: labelDocumentId as int?,
      status: _parseEnum(
        ExtractionStatus.values,
        _requiredString(json, 'run_status'),
        (value) => value.name,
        'run_status',
      ),
      errorCode: _optionalSafeCode(json, 'error_code'),
      createdAt: _optionalDateTime(json, 'created_at'),
      startedAt: _optionalDateTime(json, 'started_at'),
      completedAt: _optionalDateTime(json, 'completed_at'),
    );
  }
}

class ExtractionItem {
  final int extractionItemId;
  final ExtractionItemType type;
  final String rawText;
  final String? normalizedText;
  final String? detectedLanguage;
  final String? unit;
  final int? positionInDocument;
  final double? confidence;
  final ExtractionItemStatus status;

  const ExtractionItem({
    required this.extractionItemId,
    required this.type,
    required this.rawText,
    required this.status,
    this.normalizedText,
    this.detectedLanguage,
    this.unit,
    this.positionInDocument,
    this.confidence,
  });

  factory ExtractionItem.fromJson(Map<String, dynamic> json) {
    final position = json['position_in_document'];
    if (position != null && position is! int) {
      throw const FormatException('position_in_document must be an integer');
    }
    final rawConfidence = json['extraction_confidence'];
    final confidence = rawConfidence is num ? rawConfidence.toDouble() : null;
    if (rawConfidence != null &&
        (confidence == null || confidence < 0 || confidence > 1)) {
      throw const FormatException(
        'extraction_confidence must be between 0 and 1',
      );
    }
    return ExtractionItem(
      extractionItemId: _requiredPositiveInt(json, 'id'),
      type: _parseEnum(
        ExtractionItemType.values,
        _requiredString(json, 'item_type'),
        (value) => value == ExtractionItemType.ingredientList
            ? 'ingredient_list'
            : value.name,
        'item_type',
      ),
      rawText: _requiredString(json, 'raw_text'),
      normalizedText: _optionalString(json, 'normalized_text'),
      detectedLanguage: _optionalString(json, 'detected_language'),
      unit: _optionalString(json, 'unit'),
      positionInDocument: position as int?,
      confidence: confidence,
      status: _parseEnum(
        ExtractionItemStatus.values,
        _requiredString(json, 'extraction_status'),
        (value) => value.name,
        'extraction_status',
      ),
    );
  }
}

class ExtractionResultSummary {
  final ExtractionRunRef run;
  final List<ExtractionItem> items;

  ExtractionResultSummary({
    required this.run,
    required List<ExtractionItem> items,
  }) : items = List.unmodifiable(items);

  factory ExtractionResultSummary.fromJson(Map<String, dynamic> json) {
    final run = json['extraction'];
    final items = json['items'];
    if (run is! Map || items is! List) {
      throw const FormatException('Extraction response shape is invalid');
    }
    return ExtractionResultSummary(
      run: ExtractionRunRef.fromJson(Map<String, dynamic>.from(run)),
      items: items
          .map(
            (item) => ExtractionItem.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
    );
  }
}

enum ExtractionFlowStep {
  notStarted,
  deferred,
  starting,
  loading,
  succeeded,
  failedRetryable,
  failedTerminal,
  unavailable,
}

class ExtractionFlowState {
  final ExtractionFlowStep step;
  final ExtractionResultSummary? result;
  final String? errorCode;

  const ExtractionFlowState({
    required this.step,
    this.result,
    this.errorCode,
  });
}

T _parseEnum<T>(
  Iterable<T> values,
  String wireValue,
  String Function(T value) toWireValue,
  String field,
) {
  final matches = values.where((value) => toWireValue(value) == wireValue);
  if (matches.length != 1) {
    throw FormatException('Unsupported $field');
  }
  return matches.single;
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is! String || value.trim().isEmpty) {
    throw FormatException('$key must be a non-empty string');
  }
  return value.trim();
}

String? _optionalString(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null) {
    return null;
  }
  if (value is! String || value.trim().isEmpty) {
    throw FormatException('$key must be a non-empty string or absent');
  }
  return value.trim();
}

String? _optionalSafeCode(Map<String, dynamic> json, String key) {
  final value = _optionalString(json, key);
  if (value != null && !RegExp(r'^[a-z0-9_]{1,80}$').hasMatch(value)) {
    throw FormatException('$key must be a safe error code or absent');
  }
  return value;
}

int _requiredPositiveInt(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is! int || value <= 0) {
    throw FormatException('$key must be a positive integer');
  }
  return value;
}

DateTime? _optionalDateTime(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null) {
    return null;
  }
  if (value is! String) {
    throw FormatException('$key must be an ISO-8601 string or absent');
  }
  return DateTime.parse(value).toUtc();
}
