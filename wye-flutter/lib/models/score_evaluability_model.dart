enum EvaluabilityStatus {
  computable,
  notComputable,
  nonApplicable;

  static EvaluabilityStatus fromWireValue(String value) {
    switch (value) {
      case 'computable':
        return EvaluabilityStatus.computable;
      case 'not_computable':
        return EvaluabilityStatus.notComputable;
      case 'non_applicable':
        return EvaluabilityStatus.nonApplicable;
      default:
        throw FormatException('Unsupported evaluability_status: $value');
    }
  }

  String get wireValue {
    switch (this) {
      case EvaluabilityStatus.computable:
        return 'computable';
      case EvaluabilityStatus.notComputable:
        return 'not_computable';
      case EvaluabilityStatus.nonApplicable:
        return 'non_applicable';
    }
  }
}

enum OverallScoreAvailability {
  unavailable,
  deferred;

  static OverallScoreAvailability fromWireValue(String value) {
    switch (value) {
      case 'unavailable':
        return OverallScoreAvailability.unavailable;
      case 'deferred':
        return OverallScoreAvailability.deferred;
      default:
        throw FormatException('Unsupported overall availability: $value');
    }
  }

  String get wireValue {
    switch (this) {
      case OverallScoreAvailability.unavailable:
        return 'unavailable';
      case OverallScoreAvailability.deferred:
        return 'deferred';
    }
  }
}

class AssessmentDetail {
  final String code;
  final Map<String, Object?> context;

  AssessmentDetail({
    required this.code,
    Map<String, Object?> context = const {},
  }) : context = Map.unmodifiable(context) {
    if (code.trim().isEmpty) {
      throw ArgumentError.value(code, 'code', 'Must not be empty');
    }
  }

  factory AssessmentDetail.fromJson(Map<String, dynamic> json) {
    final code = json['code'];
    if (code is! String) {
      throw const FormatException('Assessment detail code must be a string');
    }

    final rawContext = json['context'];
    if (rawContext != null && rawContext is! Map) {
      throw const FormatException(
          'Assessment detail context must be an object');
    }

    return AssessmentDetail(
      code: code,
      context: rawContext == null
          ? const {}
          : Map<String, Object?>.from(rawContext as Map),
    );
  }

  Map<String, Object?> toJson() => {
        'code': code,
        'context': context,
      };
}

class ScoreEvaluation {
  final EvaluabilityStatus evaluabilityStatus;
  final int? scoreValue;
  final int? assessmentCoveragePercent;
  final String? confidenceState;
  final List<AssessmentDetail> missingInputs;
  final List<AssessmentDetail> uncertainties;
  final List<AssessmentDetail> explanations;
  final List<AssessmentDetail> disclosures;

  ScoreEvaluation({
    required this.evaluabilityStatus,
    required this.scoreValue,
    this.assessmentCoveragePercent,
    this.confidenceState,
    List<AssessmentDetail> missingInputs = const [],
    List<AssessmentDetail> uncertainties = const [],
    List<AssessmentDetail> explanations = const [],
    List<AssessmentDetail> disclosures = const [],
  })  : missingInputs = List.unmodifiable(missingInputs),
        uncertainties = List.unmodifiable(uncertainties),
        explanations = List.unmodifiable(explanations),
        disclosures = List.unmodifiable(disclosures) {
    _validateScore(evaluabilityStatus, scoreValue);
    _validateCoverage(assessmentCoveragePercent);
    if (confidenceState != null && confidenceState!.trim().isEmpty) {
      throw ArgumentError.value(
        confidenceState,
        'confidenceState',
        'Must not be empty when supplied',
      );
    }
  }

  factory ScoreEvaluation.computable({
    required int scoreValue,
    int? assessmentCoveragePercent,
    String? confidenceState,
    List<AssessmentDetail> missingInputs = const [],
    List<AssessmentDetail> uncertainties = const [],
    List<AssessmentDetail> explanations = const [],
    List<AssessmentDetail> disclosures = const [],
  }) {
    return ScoreEvaluation(
      evaluabilityStatus: EvaluabilityStatus.computable,
      scoreValue: scoreValue,
      assessmentCoveragePercent: assessmentCoveragePercent,
      confidenceState: confidenceState,
      missingInputs: missingInputs,
      uncertainties: uncertainties,
      explanations: explanations,
      disclosures: disclosures,
    );
  }

  factory ScoreEvaluation.notComputable({
    int? assessmentCoveragePercent,
    String? confidenceState,
    List<AssessmentDetail> missingInputs = const [],
    List<AssessmentDetail> uncertainties = const [],
    List<AssessmentDetail> explanations = const [],
    List<AssessmentDetail> disclosures = const [],
  }) {
    return ScoreEvaluation(
      evaluabilityStatus: EvaluabilityStatus.notComputable,
      scoreValue: null,
      assessmentCoveragePercent: assessmentCoveragePercent,
      confidenceState: confidenceState,
      missingInputs: missingInputs,
      uncertainties: uncertainties,
      explanations: explanations,
      disclosures: disclosures,
    );
  }

  factory ScoreEvaluation.nonApplicable({
    int? assessmentCoveragePercent,
    String? confidenceState,
    List<AssessmentDetail> explanations = const [],
    List<AssessmentDetail> disclosures = const [],
  }) {
    return ScoreEvaluation(
      evaluabilityStatus: EvaluabilityStatus.nonApplicable,
      scoreValue: null,
      assessmentCoveragePercent: assessmentCoveragePercent,
      confidenceState: confidenceState,
      explanations: explanations,
      disclosures: disclosures,
    );
  }

  factory ScoreEvaluation.fromJson(Map<String, dynamic> json) {
    final rawStatus = json['evaluability_status'];
    if (rawStatus is! String) {
      throw const FormatException('evaluability_status must be a string');
    }

    final rawScore = json['score_value'];
    if (rawScore != null && rawScore is! int) {
      throw const FormatException('score_value must be an integer or absent');
    }

    final rawCoverage = json['assessment_coverage_percent'];
    if (rawCoverage != null && rawCoverage is! int) {
      throw const FormatException(
        'assessment_coverage_percent must be an integer or absent',
      );
    }

    final rawConfidence = json['confidence_state'];
    if (rawConfidence != null && rawConfidence is! String) {
      throw const FormatException(
          'confidence_state must be a string or absent');
    }

    return ScoreEvaluation(
      evaluabilityStatus: EvaluabilityStatus.fromWireValue(rawStatus),
      scoreValue: rawScore as int?,
      assessmentCoveragePercent: rawCoverage as int?,
      confidenceState: rawConfidence as String?,
      missingInputs: _detailsFromJson(json['missing_inputs'], 'missing_inputs'),
      uncertainties: _detailsFromJson(json['uncertainties'], 'uncertainties'),
      explanations: _detailsFromJson(json['explanations'], 'explanations'),
      disclosures: _detailsFromJson(json['disclosures'], 'disclosures'),
    );
  }

  Map<String, Object?> toJson() => {
        'evaluability_status': evaluabilityStatus.wireValue,
        'score_value': scoreValue,
        'assessment_coverage_percent': assessmentCoveragePercent,
        'confidence_state': confidenceState,
        'missing_inputs': missingInputs.map((item) => item.toJson()).toList(),
        'uncertainties': uncertainties.map((item) => item.toJson()).toList(),
        'explanations': explanations.map((item) => item.toJson()).toList(),
        'disclosures': disclosures.map((item) => item.toJson()).toList(),
      };

  static void _validateScore(
    EvaluabilityStatus status,
    int? scoreValue,
  ) {
    if (status == EvaluabilityStatus.computable) {
      if (scoreValue == null) {
        throw ArgumentError(
          'A computable evaluation requires a numeric score',
        );
      }
      if (scoreValue < 0 || scoreValue > 100) {
        throw RangeError.range(scoreValue, 0, 100, 'scoreValue');
      }
      return;
    }

    if (scoreValue != null) {
      throw ArgumentError(
        '${status.wireValue} evaluations cannot carry a numeric score',
      );
    }
  }

  static void _validateCoverage(int? coveragePercent) {
    if (coveragePercent != null &&
        (coveragePercent < 0 || coveragePercent > 100)) {
      throw RangeError.range(
        coveragePercent,
        0,
        100,
        'assessmentCoveragePercent',
      );
    }
  }
}

class OverallScoreState {
  final OverallScoreAvailability availability;
  final List<AssessmentDetail> explanations;
  final List<AssessmentDetail> disclosures;

  OverallScoreState({
    required this.availability,
    List<AssessmentDetail> explanations = const [],
    List<AssessmentDetail> disclosures = const [],
  })  : explanations = List.unmodifiable(explanations),
        disclosures = List.unmodifiable(disclosures);

  factory OverallScoreState.deferred({
    List<AssessmentDetail> explanations = const [],
    List<AssessmentDetail> disclosures = const [],
  }) {
    return OverallScoreState(
      availability: OverallScoreAvailability.deferred,
      explanations: explanations,
      disclosures: disclosures,
    );
  }

  factory OverallScoreState.fromJson(Map<String, dynamic> json) {
    for (final prohibitedField in const [
      'score_value',
      'overall_goodness_percent',
    ]) {
      if (json[prohibitedField] != null) {
        throw FormatException(
          '$prohibitedField is not allowed while overall score is unavailable',
        );
      }
    }

    final rawAvailability = json['availability'];
    if (rawAvailability is! String) {
      throw const FormatException('overall availability must be a string');
    }

    return OverallScoreState(
      availability: OverallScoreAvailability.fromWireValue(rawAvailability),
      explanations: _detailsFromJson(json['explanations'], 'explanations'),
      disclosures: _detailsFromJson(json['disclosures'], 'disclosures'),
    );
  }

  Map<String, Object?> toJson() => {
        'availability': availability.wireValue,
        'explanations': explanations.map((item) => item.toJson()).toList(),
        'disclosures': disclosures.map((item) => item.toJson()).toList(),
      };
}

class ProductScoreView {
  final ScoreEvaluation ingredientGoodnessPercent;
  final ScoreEvaluation nutritionGoodnessPercent;
  final OverallScoreState overallScore;

  ProductScoreView({
    required this.ingredientGoodnessPercent,
    required this.nutritionGoodnessPercent,
    required this.overallScore,
  });

  factory ProductScoreView.unavailable() {
    return ProductScoreView(
      ingredientGoodnessPercent: ScoreEvaluation.notComputable(),
      nutritionGoodnessPercent: ScoreEvaluation.notComputable(),
      overallScore: OverallScoreState.deferred(),
    );
  }

  factory ProductScoreView.fromJson(Map<String, dynamic> json) {
    return ProductScoreView(
      ingredientGoodnessPercent: ScoreEvaluation.fromJson(
        _objectFromJson(
          json['ingredient_goodness_percent'],
          'ingredient_goodness_percent',
        ),
      ),
      nutritionGoodnessPercent: ScoreEvaluation.fromJson(
        _objectFromJson(
          json['nutrition_goodness_percent'],
          'nutrition_goodness_percent',
        ),
      ),
      overallScore: OverallScoreState.fromJson(
        _objectFromJson(json['overall_score'], 'overall_score'),
      ),
    );
  }

  Map<String, Object?> toJson() => {
        'ingredient_goodness_percent': ingredientGoodnessPercent.toJson(),
        'nutrition_goodness_percent': nutritionGoodnessPercent.toJson(),
        'overall_score': overallScore.toJson(),
      };
}

List<AssessmentDetail> _detailsFromJson(Object? value, String fieldName) {
  if (value == null) {
    return const [];
  }
  if (value is! List) {
    throw FormatException('$fieldName must be a list');
  }

  return List.unmodifiable(
    value.map((item) {
      if (item is! Map) {
        throw FormatException('$fieldName items must be objects');
      }
      return AssessmentDetail.fromJson(Map<String, dynamic>.from(item));
    }),
  );
}

Map<String, dynamic> _objectFromJson(Object? value, String fieldName) {
  if (value is! Map) {
    throw FormatException('$fieldName must be an object');
  }
  return Map<String, dynamic>.from(value);
}
