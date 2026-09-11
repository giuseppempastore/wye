class IngredientNormalizationCandidate {
  final String sourceText;
  final String? englishCandidate;
  final String? normalizedCandidate;
  final double? confidence;
  final bool needsReview;
  final String? correctionReason;
  final bool allergenEmphasis;

  const IngredientNormalizationCandidate({
    required this.sourceText,
    this.englishCandidate,
    this.normalizedCandidate,
    this.confidence,
    this.needsReview = true,
    this.correctionReason,
    this.allergenEmphasis = false,
  });

  factory IngredientNormalizationCandidate.fromJson(
    Map<String, dynamic> json,
  ) {
    return IngredientNormalizationCandidate(
      sourceText: json['source_text']?.toString() ?? '',
      englishCandidate: json['english_candidate']?.toString(),
      normalizedCandidate: json['normalized_candidate']?.toString(),
      confidence: (json['confidence'] as num?)?.toDouble(),
      needsReview: json['needs_review'] != false,
      correctionReason: json['correction_reason']?.toString(),
      allergenEmphasis: json['allergen_emphasis'] == true,
    );
  }

  Map<String, dynamic> toJson() => {
        'source_text': sourceText,
        'english_candidate': englishCandidate,
        'normalized_candidate': normalizedCandidate,
        'confidence': confidence,
        'needs_review': needsReview,
        'correction_reason': correctionReason,
        'allergen_emphasis': allergenEmphasis,
      };
}

class NutritionNormalizationCandidate {
  final String canonicalKey;
  final String sourceLabel;
  final String sourceValue;
  final String sourceUnit;
  final double normalizedValue;
  final String normalizedUnit;
  final double? confidence;
  final bool needsReview;

  const NutritionNormalizationCandidate({
    required this.canonicalKey,
    required this.sourceLabel,
    required this.sourceValue,
    required this.sourceUnit,
    required this.normalizedValue,
    required this.normalizedUnit,
    this.confidence,
    this.needsReview = true,
  });

  factory NutritionNormalizationCandidate.fromJson(
    Map<String, dynamic> json,
  ) {
    return NutritionNormalizationCandidate(
      canonicalKey: json['canonical_key']?.toString() ?? '',
      sourceLabel: json['source_label']?.toString() ?? '',
      sourceValue: json['source_value']?.toString() ?? '',
      sourceUnit: json['source_unit']?.toString() ?? '',
      normalizedValue: (json['normalized_value'] as num?)?.toDouble() ?? 0,
      normalizedUnit: json['normalized_unit']?.toString() ?? '',
      confidence: (json['confidence'] as num?)?.toDouble(),
      needsReview: json['needs_review'] != false,
    );
  }

  Map<String, dynamic> toJson() => {
        'canonical_key': canonicalKey,
        'source_label': sourceLabel,
        'source_value': sourceValue,
        'source_unit': sourceUnit,
        'normalized_value': normalizedValue,
        'normalized_unit': normalizedUnit,
        'confidence': confidence,
        'needs_review': needsReview,
      };
}

class TextNormalizationRequestPayload {
  final String sourceLanguage;
  final String documentType;
  final String rawText;
  final String targetLanguage;
  final String schemaVersion;
  final String parserVersion;

  const TextNormalizationRequestPayload({
    required this.sourceLanguage,
    required this.documentType,
    required this.rawText,
    this.targetLanguage = 'en',
    this.schemaVersion = '2',
    required this.parserVersion,
  });

  Map<String, Object> toJson() => {
        'source_language': sourceLanguage,
        'document_type': documentType,
        'raw_text': rawText,
        'target_language': targetLanguage,
        'schema_version': schemaVersion,
        'parser_version': parserVersion,
      };
}

class TextNormalizationResult {
  final String detectedLanguage;
  final String sourceSegment;
  final List<IngredientNormalizationCandidate> ingredientCandidates;
  final List<NutritionNormalizationCandidate> nutritionCandidates;
  final String? nutritionBasis;
  final List<String> warnings;
  final Map<String, String?> provenance;
  final bool cacheHit;

  const TextNormalizationResult({
    required this.detectedLanguage,
    required this.sourceSegment,
    this.ingredientCandidates = const [],
    this.nutritionCandidates = const [],
    this.nutritionBasis,
    this.warnings = const [],
    this.provenance = const {},
    this.cacheHit = false,
  });

  factory TextNormalizationResult.fromJson(Map<String, dynamic> json) {
    return TextNormalizationResult(
      detectedLanguage: json['detected_language']?.toString() ?? 'und',
      sourceSegment: json['source_segment']?.toString() ?? '',
      ingredientCandidates: (json['canonical_english_items'] as List? ?? [])
          .map(
            (item) => IngredientNormalizationCandidate.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(growable: false),
      nutritionCandidates: (json['nutrition_items'] as List? ?? [])
          .map(
            (item) => NutritionNormalizationCandidate.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(growable: false),
      nutritionBasis: json['nutrition_basis']?.toString(),
      warnings: (json['warnings'] as List? ?? [])
          .map((value) => value.toString())
          .toList(growable: false),
      provenance: (json['provenance'] as Map? ?? const {})
          .map((key, value) => MapEntry(key.toString(), value?.toString())),
      cacheHit: json['cache_hit'] == true,
    );
  }
}
