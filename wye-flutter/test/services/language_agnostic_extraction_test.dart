import 'package:flutter_test/flutter_test.dart';
import 'package:wye/models/text_normalization_models.dart';
import 'package:wye/services/language_detector.dart';
import 'package:wye/services/photo_field_mapper.dart';

void main() {
  const mapper = PhotoFieldMapper();

  group('canonical English ingredient golden cases', () {
    const cases = <String, ({String source, String english})>{
      'it': (
        source: 'Ingredienti: acqua, zucchero, sale',
        english: 'water, sugar, salt',
      ),
      'en': (
        source: 'Ingredients: water, sugar, salt',
        english: 'water, sugar, salt',
      ),
      'fi': (
        source: 'Ainesosat: vesi, sokeri, suola',
        english: 'water, sugar, salt',
      ),
      'es': (
        source: 'Ingredientes: agua, azúcar, sal',
        english: 'water, sugar, salt',
      ),
      'fr': (
        source: 'Ingrédients: eau, sucre, sel',
        english: 'water, sugar, salt',
      ),
      'de': (
        source: 'Zutaten: wasser, zucker, salz',
        english: 'water, sugar, salt',
      ),
      'pt': (
        source: 'Ingredientes: água, açúcar, sal',
        english: 'water, sugar, salt',
      ),
      'sv': (
        source: 'Ingredienser: vatten, socker, salt',
        english: 'water, sugar, salt',
      ),
    };

    for (final entry in cases.entries) {
      test('${entry.key} translates conservatively to English', () {
        final result = mapper.map(
          entry.value.source,
          ProductPhotoPurpose.ingredients,
        );

        expect(result.detectedLanguage, entry.key);
        expect(result.canonicalEnglish, entry.value.english);
        expect(result.rawText, entry.value.source);
        expect(result.sourceSegment, isNotEmpty);
        expect(result.normalizedCandidates, hasLength(3));
        expect(result.needsTextFallback, isFalse);
      });
    }
  });

  test('unknown language stays undetermined and requests text fallback', () {
    const raw = 'Compositio: aqua, saccharum, sal';
    final result = mapper.map(raw, ProductPhotoPurpose.ingredients);

    expect(result.detectedLanguage, 'und');
    expect(
        result.languageDetection.status, LanguageDetectionStatus.undetermined);
    expect(result.rawText, raw);
    expect(result.sourceSegment, 'aqua, saccharum, sal');
    expect(result.canonicalEnglish, isNull);
    expect(result.needsTextFallback, isTrue);
  });

  test('structure works without an ingredient heading', () {
    const raw = 'water, sugar 12%, SALT';
    final result = mapper.map(raw, ProductPhotoPurpose.ingredients);

    expect(result.sourceSegment, raw);
    expect(result.canonicalEnglish, 'water, sugar 12%, salt');
    expect(result.warnings, contains('ingredient_heading_unrecognized'));
    expect(result.normalizedCandidates[1].sourceText, 'sugar 12%');
    expect(result.normalizedCandidates[1].englishCandidate, 'sugar 12%');
    expect(result.normalizedCandidates[2].allergenEmphasis, isTrue);
  });

  test('OCR correction is explicit and never silently applied', () {
    final deterministic = mapper.map(
      'Ingredients: past4, water',
      ProductPhotoPurpose.ingredients,
    );
    expect(deterministic.rawText, contains('past4'));
    expect(deterministic.normalizedCandidates.first.sourceText, 'past4');
    expect(deterministic.normalizedCandidates.first.englishCandidate, isNull);

    final merged = deterministic.mergeTextFallback(
      const TextNormalizationResult(
        detectedLanguage: 'en',
        sourceSegment: 'past4, water',
        ingredientCandidates: [
          IngredientNormalizationCandidate(
            sourceText: 'past4',
            englishCandidate: 'pasta',
            normalizedCandidate: 'pasta',
            confidence: 0.7,
            needsReview: true,
            correctionReason: 'probable_ocr_substitution',
          ),
          IngredientNormalizationCandidate(
            sourceText: 'water',
            englishCandidate: 'water',
            normalizedCandidate: 'water',
            confidence: 0.99,
            needsReview: true,
          ),
        ],
      ),
    );
    expect(merged.rawText, contains('past4'));
    expect(merged.canonicalEnglish, 'pasta, water');
    expect(merged.normalizedCandidates.first.correctionReason,
        'probable_ocr_substitution');
    expect(merged.normalizedCandidates.first.needsReview, isTrue);
  });

  test('diacritics allergens and percentages remain in source evidence', () {
    const raw = 'Ainesosat: täysjyväkaura 64 %, PÄHKINÄ (4 %)';
    final result = mapper.map(raw, ProductPhotoPurpose.ingredients);

    expect(result.rawText, raw);
    expect(result.sourceSegment, 'täysjyväkaura 64 %, PÄHKINÄ (4 %)');
    expect(result.normalizedCandidates.first.sourceText, 'täysjyväkaura 64 %');
    expect(result.normalizedCandidates.last.sourceText, 'PÄHKINÄ (4 %)');
    expect(result.normalizedCandidates.last.allergenEmphasis, isTrue);
    expect(result.canonicalEnglish, 'whole grain oats 64 %, nut (4 %)');
  });

  group('canonical nutrition golden cases', () {
    const cases = <String, String>{
      'it':
          'Valori nutrizionali per 100 g\nEnergia 420 kJ / 100 kcal\nGrassi 1,5 g\nSale 0,4 g',
      'en':
          'Nutrition facts per 100 g\nEnergy 420 kJ / 100 kcal\nFat 1.5 g\nSalt 0.4 g',
      'fi':
          'Ravintosisältö 100 g\nEnergia 420 kJ / 100 kcal\nRasvaa 1,5 g\nSuolaa 0,4 g',
      'es':
          'Información nutricional 100 g\nEnergía 420 kJ / 100 kcal\nGrasas 1,5 g\nSal 0,4 g',
      'fr':
          'Informations nutritionnelles 100 g\nÉnergie 420 kJ / 100 kcal\nMatières grasses 1,5 g\nSel 0,4 g',
      'de':
          'Nährwertangaben 100 g\nEnergie 420 kJ / 100 kcal\nFett 1,5 g\nSalz 0,4 g',
      'pt':
          'Informação nutricional 100 g\nEnergia 420 kJ / 100 kcal\nLípidos 1,5 g\nSal 0,4 g',
      'sv':
          'Näringsdeklaration 100 g\nEnergi 420 kJ / 100 kcal\nFett 1,5 g\nSalt 0,4 g',
    };

    for (final entry in cases.entries) {
      test('${entry.key} maps canonical nutrient keys', () {
        final result = mapper.map(entry.value, ProductPhotoPurpose.nutrition);
        final byKey = {
          for (final item in result.nutrientObservations)
            item.canonicalKey: item,
        };

        expect(result.detectedLanguage, entry.key);
        expect(result.rawText, entry.value);
        expect(result.nutritionBasis, 'per_100_g');
        expect(byKey['energy_kj']?.normalizedValue, 420);
        expect(byKey['energy_kcal']?.normalizedValue, 100);
        expect(byKey['fat_g']?.normalizedValue, 1.5);
        expect(byKey['salt_g']?.normalizedValue, 0.4);
      });
    }
  });

  test('salt and sodium are separate canonical observations', () {
    final result = mapper.map(
      'Nutrition facts per 100 g\nSalt 0.8 g\nSodium 320 mg',
      ProductPhotoPurpose.nutrition,
    );
    final keys = result.nutrientObservations
        .map((observation) => observation.canonicalKey)
        .toSet();
    expect(keys, containsAll(<String>{'salt_g', 'sodium_mg'}));
    expect(result.nutrition['salt_g'], 0.8);
    expect(result.nutrition['sodium_mg'], 320);
  });

  test('dot and decimal comma normalize without changing source values', () {
    final result = mapper.map(
      'Nutrition facts per 100 g\nFat 1,5 g\nSugars 2.25 g',
      ProductPhotoPurpose.nutrition,
    );
    final fat = result.nutrientObservations
        .singleWhere((item) => item.canonicalKey == 'fat_g');
    final sugars = result.nutrientObservations
        .singleWhere((item) => item.canonicalKey == 'sugars_g');
    expect((fat.sourceValue, fat.normalizedValue), ('1,5', 1.5));
    expect((sugars.sourceValue, sugars.normalizedValue), ('2.25', 2.25));
  });

  test('uninstalled OCR script is explicit and produces no fields', () {
    final result = mapper.map(
      '配料：水，糖，盐',
      ProductPhotoPurpose.ingredients,
    );
    expect(result.languageDetection.script, OcrScript.chinese);
    expect(result.languageDetection.status,
        LanguageDetectionStatus.unsupportedScript);
    expect(result.detectedLanguage, 'und');
    expect(result.hasIngredients, isFalse);
    expect(result.warnings, contains('ocr_script_unsupported'));
  });

  test('ML Kit hint can carry an unlisted Latin language code', () {
    const detector = DeterministicLanguageDetector();
    final detected = detector.detect(
      'Ingrediënten: water, suiker, zout',
      recognizedLanguageCodes: const ['nl'],
    );
    expect(detected.code, 'nl');
    expect(detected.method, 'mlkit_recognized_languages');
    expect(detected.script, OcrScript.latin);
  });
}
