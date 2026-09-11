import '../models/text_normalization_models.dart';
import 'label_language_lexicon.dart';
import 'language_detector.dart';

enum ProductPhotoPurpose {
  productFront,
  ingredients,
  nutrition,
  other,
  unknown,
}

class PhotoFieldMapping {
  static const parserVersion = 'photo_field_mapper_v3';

  final String rawText;
  final LanguageDetectionResult languageDetection;
  final String? sourceSegment;
  final String? canonicalEnglish;
  final List<IngredientNormalizationCandidate> normalizedCandidates;
  final List<NutritionNormalizationCandidate> nutrientObservations;
  final Map<String, double> nutrition;
  final String? nutritionBasis;
  final List<String> warnings;
  final bool textFallbackUsed;
  final Map<String, String?> textFallbackProvenance;

  const PhotoFieldMapping({
    this.rawText = '',
    this.languageDetection = const LanguageDetectionResult(
      code: 'und',
      status: LanguageDetectionStatus.undetermined,
      method: 'not_run',
      version: DeterministicLanguageDetector.version,
      script: OcrScript.undetermined,
    ),
    this.sourceSegment,
    this.canonicalEnglish,
    this.normalizedCandidates = const [],
    this.nutrientObservations = const [],
    this.nutrition = const {},
    this.nutritionBasis,
    this.warnings = const [],
    this.textFallbackUsed = false,
    this.textFallbackProvenance = const {},
  });

  String get detectedLanguage => languageDetection.code;
  String? get ingredientListText => canonicalEnglish ?? sourceSegment;
  bool get hasIngredients => ingredientListText?.trim().isNotEmpty == true;
  bool get hasNutrition => nutrition.isNotEmpty;
  String? get brandName => null;
  String? get productName => null;
  String? get category => null;
  String? get productType => null;
  bool get hasIdentity => false;

  bool get needsReview =>
      warnings.isNotEmpty ||
      normalizedCandidates.any((candidate) => candidate.needsReview) ||
      nutrientObservations.any((candidate) => candidate.needsReview);

  bool get needsTextFallback {
    if (!languageDetection.scriptSupported || rawText.trim().isEmpty) {
      return false;
    }
    if (languageDetection.status == LanguageDetectionStatus.undetermined) {
      return true;
    }
    if (sourceSegment == null || sourceSegment!.trim().isEmpty) return true;
    if (normalizedCandidates.isNotEmpty) {
      return normalizedCandidates.any(
        (candidate) =>
            candidate.englishCandidate == null ||
            candidate.normalizedCandidate == null,
      );
    }
    return nutrientObservations.isEmpty;
  }

  TextNormalizationRequestPayload toTextNormalizationRequest(
    ProductPhotoPurpose purpose,
  ) {
    return TextNormalizationRequestPayload(
      sourceLanguage: detectedLanguage,
      documentType: purpose == ProductPhotoPurpose.nutrition
          ? 'nutrition'
          : 'ingredients',
      rawText: sourceSegment?.trim().isNotEmpty == true
          ? sourceSegment!
          : rawText.trim(),
      parserVersion: parserVersion,
    );
  }

  PhotoFieldMapping mergeTextFallback(TextNormalizationResult result) {
    final candidates = result.ingredientCandidates.isNotEmpty
        ? result.ingredientCandidates
        : normalizedCandidates;
    final observations = result.nutritionCandidates.isNotEmpty
        ? result.nutritionCandidates
        : nutrientObservations;
    final translated = candidates.isNotEmpty &&
            candidates.every(
              (candidate) =>
                  candidate.englishCandidate?.trim().isNotEmpty == true,
            )
        ? candidates
            .map((candidate) => candidate.englishCandidate!.trim())
            .join(', ')
        : canonicalEnglish;
    final mergedLanguage =
        detectedLanguage == 'und' && result.detectedLanguage != 'und'
            ? LanguageDetectionResult(
                code: result.detectedLanguage,
                status: LanguageDetectionStatus.detected,
                method: 'backend_text_fallback',
                version: DeterministicLanguageDetector.version,
                script: languageDetection.script,
              )
            : languageDetection;
    return PhotoFieldMapping(
      rawText: rawText,
      languageDetection: mergedLanguage,
      sourceSegment: sourceSegment ?? result.sourceSegment,
      canonicalEnglish: translated,
      normalizedCandidates: candidates,
      nutrientObservations: observations,
      nutrition: _legacyNutritionMap(observations, fallback: nutrition),
      nutritionBasis: result.nutritionBasis ?? nutritionBasis,
      warnings: {
        ...warnings.where(
          (warning) =>
              warning != 'translation_required' &&
              warning != 'language_undetermined',
        ),
        ...result.warnings,
      }.toList(growable: false),
      textFallbackUsed: true,
      textFallbackProvenance: result.provenance,
    );
  }

  Map<String, dynamic> toPersistencePayload(ProductPhotoPurpose purpose) => {
        'document_type': switch (purpose) {
          ProductPhotoPurpose.ingredients => 'ingredients',
          ProductPhotoPurpose.nutrition => 'nutrition',
          _ => 'other',
        },
        'raw_text': rawText,
        'source_language': detectedLanguage,
        'language_confidence': languageDetection.confidence,
        'language_method': languageDetection.method,
        'language_version': languageDetection.version,
        'ocr_script': languageDetection.script.name,
        'parser_version': parserVersion,
        'source_segment': sourceSegment,
        'canonical_english': canonicalEnglish,
        'normalized_candidates': normalizedCandidates
            .map((candidate) => candidate.toJson())
            .toList(growable: false),
        'nutrient_observations': nutrientObservations
            .map((candidate) => candidate.toJson())
            .toList(growable: false),
        'nutrition': nutrition,
        'nutrition_basis': nutritionBasis,
        'text_fallback_used': textFallbackUsed,
        'normalization_provenance': textFallbackProvenance,
        'warnings': warnings,
      };

  static Map<String, double> _legacyNutritionMap(
    List<NutritionNormalizationCandidate> observations, {
    Map<String, double> fallback = const {},
  }) {
    final values = Map<String, double>.from(fallback);
    const legacyKeys = {
      'energy_kcal': 'energy_kcal',
      'fat_g': 'fat_g',
      'saturated_fat_g': 'saturated_fat_g',
      'carbohydrate_g': 'carbs_g',
      'sugars_g': 'sugar_g',
      'fibre_g': 'fiber_g',
      'protein_g': 'protein_g',
      'salt_g': 'salt_g',
      'sodium_mg': 'sodium_mg',
    };
    for (final observation in observations) {
      final key = legacyKeys[observation.canonicalKey];
      if (key != null) values[key] = observation.normalizedValue;
    }
    return values;
  }
}

class PhotoFieldMapper {
  final LanguageDetector languageDetector;

  const PhotoFieldMapper({
    this.languageDetector = const DeterministicLanguageDetector(),
  });

  bool shouldExtractText(ProductPhotoPurpose purpose) =>
      purpose == ProductPhotoPurpose.ingredients ||
      purpose == ProductPhotoPurpose.nutrition;

  PhotoFieldMapping map(
    String rawText,
    ProductPhotoPurpose purpose, {
    Iterable<String> recognizedLanguageCodes = const [],
  }) {
    final lines = rawText
        .split(RegExp(r'[\r\n]+'))
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .toList(growable: false);
    final language = languageDetector.detect(
      rawText,
      recognizedLanguageCodes: recognizedLanguageCodes,
    );
    if (!language.scriptSupported) {
      return PhotoFieldMapping(
        rawText: rawText,
        languageDetection: language,
        warnings: const ['ocr_script_unsupported'],
      );
    }

    return switch (purpose) {
      ProductPhotoPurpose.productFront ||
      ProductPhotoPurpose.other ||
      ProductPhotoPurpose.unknown =>
        PhotoFieldMapping(
          rawText: rawText,
          languageDetection: language,
          warnings: [
            if (language.status == LanguageDetectionStatus.undetermined)
              'language_undetermined',
          ],
        ),
      ProductPhotoPurpose.ingredients =>
        _mapIngredients(rawText, lines, language),
      ProductPhotoPurpose.nutrition => _mapNutrition(rawText, lines, language),
    };
  }

  PhotoFieldMapping _mapIngredients(
    String rawText,
    List<String> lines,
    LanguageDetectionResult language,
  ) {
    final extraction = _extractIngredientSegment(lines);
    final segment = extraction.segment;
    if (segment == null || segment.length < 3) {
      return PhotoFieldMapping(
        rawText: rawText,
        languageDetection: language,
        warnings: [
          'ingredient_segment_missing',
          if (language.status == LanguageDetectionStatus.undetermined)
            'language_undetermined',
        ],
      );
    }
    final candidates = _splitIngredients(segment)
        .map((item) => _translateIngredient(item, language.code))
        .toList(growable: false);
    final translated = candidates.isNotEmpty &&
            candidates.every((candidate) => candidate.englishCandidate != null)
        ? candidates.map((candidate) => candidate.englishCandidate!).join(', ')
        : null;
    return PhotoFieldMapping(
      rawText: rawText,
      languageDetection: language,
      sourceSegment: segment,
      canonicalEnglish: translated,
      normalizedCandidates: candidates,
      warnings: [
        if (!extraction.knownHeading) 'ingredient_heading_unrecognized',
        if (language.status == LanguageDetectionStatus.undetermined)
          'language_undetermined',
        if (translated == null) 'translation_required',
      ],
    );
  }

  _SegmentExtraction _extractIngredientSegment(List<String> lines) {
    final headings = labelLanguageLexicons.values
        .expand((lexicon) => lexicon.ingredientHeadings)
        .toList(growable: false);
    final nutritionHeadings = labelLanguageLexicons.values
        .expand((lexicon) => lexicon.nutritionHeadings)
        .toList(growable: false);
    final marker = RegExp(
      '^(${headings.map(RegExp.escape).join('|')})\\s*[:\\-]?\\s*(.*)\$',
      caseSensitive: false,
      unicode: true,
    );
    final stop = RegExp(
      '^(${nutritionHeadings.map(RegExp.escape).join('|')})(?:\\s|\$)',
      caseSensitive: false,
      unicode: true,
    );
    final collected = <String>[];
    var collecting = false;
    for (final line in lines) {
      final start = marker.firstMatch(line);
      if (start != null) {
        collecting = true;
        final sameLine = start.group(2)?.trim();
        if (sameLine?.isNotEmpty == true) collected.add(sameLine!);
        continue;
      }
      if (collecting && stop.hasMatch(line)) break;
      if (collecting && !_isIngredientNoise(line)) collected.add(line);
    }
    if (collected.isNotEmpty) {
      return _SegmentExtraction(_cleanSegment(collected.join(' ')), true);
    }

    String? best;
    var bestScore = 0;
    for (final line in lines) {
      if (_isIngredientNoise(line)) continue;
      final colon = line.indexOf(':');
      final candidate = colon >= 0 ? line.substring(colon + 1).trim() : line;
      final separators = RegExp(r'[,;]').allMatches(candidate).length;
      final pieces = _splitIngredients(candidate);
      if (separators == 0 || pieces.length < 2) continue;
      final score = candidate.length + separators * 30;
      if (score > bestScore) {
        best = candidate;
        bestScore = score;
      }
    }
    return _SegmentExtraction(best == null ? null : _cleanSegment(best), false);
  }

  bool _isIngredientNoise(String line) {
    final lower = line.toLowerCase();
    final nutritionHeadings = labelLanguageLexicons.values
        .expand((lexicon) => lexicon.nutritionHeadings);
    if (nutritionHeadings.any(lower.startsWith)) return true;
    return RegExp(
      r'\b(www\.|net weight|peso netto|conservare|store in|made in|via\s+|serving|porzione|adresse|dirección|valmistaja|osoite)\b',
      caseSensitive: false,
      unicode: true,
    ).hasMatch(line);
  }

  List<String> _splitIngredients(String segment) {
    final result = <String>[];
    final buffer = StringBuffer();
    var depth = 0;
    for (final rune in segment.runes) {
      final char = String.fromCharCode(rune);
      if (char == '(' || char == '[') depth += 1;
      if (char == ')' || char == ']') depth = depth > 0 ? depth - 1 : 0;
      if ((char == ',' || char == ';') && depth == 0) {
        final value = buffer.toString().trim();
        if (value.isNotEmpty) result.add(value);
        buffer.clear();
      } else {
        buffer.write(char);
      }
    }
    final value = buffer.toString().trim();
    if (value.isNotEmpty) result.add(value);
    return result;
  }

  IngredientNormalizationCandidate _translateIngredient(
    String source,
    String language,
  ) {
    final quantity = RegExp(
      r'\s*(\(\s*\d+(?:[\.,]\d+)?\s*%\s*\)|\d+(?:[\.,]\d+)?\s*%)\s*$',
      unicode: true,
    ).firstMatch(source);
    final base = quantity == null
        ? source.trim()
        : source.substring(0, quantity.start).trim();
    final normalizedSource = base.toLowerCase().replaceAll(RegExp(r'\s+'), ' ');
    final lexicon = labelLanguageLexicons[language];
    // Even English OCR is not accepted as canonical merely because it uses
    // Latin characters: only versioned deterministic entries are passed
    // through without a reviewable fallback candidate.
    final translated = lexicon?.ingredientTranslations[normalizedSource];
    final englishWithQuantity = translated == null
        ? null
        : quantity == null
            ? translated
            : '$translated ${quantity.group(1)}';
    final letters = source.replaceAll(RegExp(r'[^A-Za-zÀ-ž]'), '');
    final allergenEmphasis =
        letters.length > 1 && source == source.toUpperCase();
    return IngredientNormalizationCandidate(
      sourceText: source,
      englishCandidate: englishWithQuantity,
      normalizedCandidate: translated,
      confidence: translated == null ? null : (language == 'en' ? 0.99 : 0.95),
      needsReview: translated == null,
      allergenEmphasis: allergenEmphasis,
    );
  }

  PhotoFieldMapping _mapNutrition(
    String rawText,
    List<String> lines,
    LanguageDetectionResult language,
  ) {
    final rows = <String>[];
    for (var index = 0; index < lines.length; index++) {
      final current = lines[index];
      rows.add(current);
      if (!RegExp(r'\d').hasMatch(current) && index + 1 < lines.length) {
        final next = lines[index + 1];
        if (RegExp(r'\d').hasMatch(next)) rows.add('$current $next');
      }
    }
    final observations = <NutritionNormalizationCandidate>[];
    final saturatedLabels = labelLanguageLexicons.values
        .expand(
          (lexicon) => lexicon.nutrientLabels['saturated_fat_g'] ?? const [],
        )
        .toList(growable: false);

    for (final canonicalKey in const [
      'energy',
      'saturated_fat_g',
      'fat_g',
      'carbohydrate_g',
      'sugars_g',
      'fibre_g',
      'protein_g',
      'salt_g',
      'sodium_mg',
    ]) {
      final labels = labelLanguageLexicons.values
          .expand(
            (lexicon) => lexicon.nutrientLabels[canonicalKey] ?? const [],
          )
          .toSet()
          .toList()
        ..sort((a, b) => b.length.compareTo(a.length));
      for (final row in rows) {
        String? matchedLabel;
        for (final label in labels) {
          if (_containsLabel(row, label)) {
            matchedLabel = label;
            break;
          }
        }
        if (matchedLabel == null) continue;
        if (canonicalKey == 'fat_g' &&
            saturatedLabels.any((label) => _containsLabel(row, label))) {
          continue;
        }
        final matches = RegExp(
          r'(-?\d+(?:[\.,]\d+)?)\s*(kcal|kj|mg|g)\b',
          caseSensitive: false,
        ).allMatches(row);
        for (final match in matches) {
          final sourceUnit = match.group(2)!;
          final unit = sourceUnit.toLowerCase();
          final value = double.tryParse(match.group(1)!.replaceAll(',', '.'));
          if (value == null || value < 0) continue;
          final key = canonicalKey == 'energy'
              ? (unit == 'kj' ? 'energy_kj' : 'energy_kcal')
              : canonicalKey;
          final maximum = key == 'energy_kj'
              ? 4000
              : key == 'energy_kcal'
                  ? 900
                  : key == 'sodium_mg'
                      ? 100000
                      : 100;
          final allowed = canonicalKey == 'energy'
              ? {'kj', 'kcal'}
              : key == 'sodium_mg'
                  ? {'mg'}
                  : {'g'};
          if (!allowed.contains(unit) || value > maximum) continue;
          if (observations.any((item) => item.canonicalKey == key)) continue;
          final lowerRow = row.toLowerCase();
          final labelStart = lowerRow.indexOf(matchedLabel.toLowerCase());
          final originalLabel = labelStart < 0
              ? matchedLabel
              : row.substring(labelStart, labelStart + matchedLabel.length);
          observations.add(
            NutritionNormalizationCandidate(
              canonicalKey: key,
              sourceLabel: originalLabel,
              sourceValue: match.group(1)!,
              sourceUnit: sourceUnit,
              normalizedValue: value,
              normalizedUnit: unit,
              confidence: 0.98,
              needsReview: false,
            ),
          );
        }
      }
    }

    final context = lines.join(' ').toLowerCase();
    String? basis;
    if (RegExp(r'100\s*g\b').hasMatch(context)) {
      basis = 'per_100_g';
    } else if (RegExp(r'100\s*ml\b').hasMatch(context)) {
      basis = 'per_100_ml';
    } else {
      final servingWords = labelLanguageLexicons.values
          .expand((lexicon) => lexicon.servingWords);
      if (servingWords.any((word) => _containsLabel(context, word))) {
        basis = 'per_serving';
      }
    }
    final hasKnownHeading = labelLanguageLexicons.values
        .expand((lexicon) => lexicon.nutritionHeadings)
        .any((heading) => context.contains(heading));
    final hasTableContext =
        hasKnownHeading || basis != null || observations.length >= 2;
    if (!hasTableContext) {
      return PhotoFieldMapping(
        rawText: rawText,
        languageDetection: language,
        sourceSegment: lines.join('\n'),
        warnings: [
          'nutrition_table_context_missing',
          if (language.status == LanguageDetectionStatus.undetermined)
            'language_undetermined',
        ],
      );
    }
    return PhotoFieldMapping(
      rawText: rawText,
      languageDetection: language,
      sourceSegment: lines.join('\n'),
      nutrientObservations: observations,
      nutrition: PhotoFieldMapping._legacyNutritionMap(observations),
      nutritionBasis: basis,
      warnings: [
        if (basis == null) 'nutrition_basis_missing',
        if (observations.isEmpty) 'nutrition_rows_missing',
        if (language.status == LanguageDetectionStatus.undetermined)
          'language_undetermined',
      ],
    );
  }

  bool _containsLabel(String text, String label) {
    final escaped = RegExp.escape(label.toLowerCase());
    return RegExp('(^|[^a-zà-ž])$escaped([^a-zà-ž]|\$)')
        .hasMatch(text.toLowerCase());
  }

  String _cleanSegment(String value) =>
      value.replaceAll(RegExp(r'\s+'), ' ').trim();
}

class _SegmentExtraction {
  final String? segment;
  final bool knownHeading;

  const _SegmentExtraction(this.segment, this.knownHeading);
}
