import 'label_language_lexicon.dart';

enum OcrScript {
  latin,
  chinese,
  devanagari,
  japanese,
  korean,
  undetermined,
}

enum LanguageDetectionStatus { detected, undetermined, unsupportedScript }

class LanguageDetectionResult {
  final String code;
  final double? confidence;
  final LanguageDetectionStatus status;
  final String method;
  final String version;
  final OcrScript script;

  const LanguageDetectionResult({
    required this.code,
    this.confidence,
    required this.status,
    required this.method,
    required this.version,
    required this.script,
  });

  bool get scriptSupported => OcrRuntimeCapabilities.isInstalled(script);
}

abstract class LanguageDetector {
  LanguageDetectionResult detect(
    String rawText, {
    Iterable<String> recognizedLanguageCodes = const [],
  });
}

class OcrRuntimeCapabilities {
  static const installedScripts = <OcrScript>{OcrScript.latin};

  static bool isInstalled(OcrScript script) =>
      installedScripts.contains(script) || script == OcrScript.undetermined;

  static OcrScript classify(String text) {
    var hasLatin = false;
    var hasHan = false;
    var hasJapaneseKana = false;
    var hasDevanagari = false;
    var hasKorean = false;
    for (final rune in text.runes) {
      hasJapaneseKana |= rune >= 0x3040 && rune <= 0x30ff;
      hasKorean |= rune >= 0xac00 && rune <= 0xd7af;
      hasDevanagari |= rune >= 0x0900 && rune <= 0x097f;
      hasHan |= rune >= 0x4e00 && rune <= 0x9fff;
      hasLatin |= (rune >= 0x0041 && rune <= 0x024f) ||
          (rune >= 0x1e00 && rune <= 0x1eff);
    }
    if (hasJapaneseKana) return OcrScript.japanese;
    if (hasKorean) return OcrScript.korean;
    if (hasDevanagari) return OcrScript.devanagari;
    if (hasHan) return OcrScript.chinese;
    if (hasLatin) return OcrScript.latin;
    return OcrScript.undetermined;
  }
}

class DeterministicLanguageDetector implements LanguageDetector {
  static const version = 'language_detector_v1';

  const DeterministicLanguageDetector();

  @override
  LanguageDetectionResult detect(
    String rawText, {
    Iterable<String> recognizedLanguageCodes = const [],
  }) {
    final script = OcrRuntimeCapabilities.classify(rawText);
    if (!OcrRuntimeCapabilities.isInstalled(script)) {
      return LanguageDetectionResult(
        code: 'und',
        status: LanguageDetectionStatus.unsupportedScript,
        method: 'unicode_script_guard',
        version: version,
        script: script,
      );
    }

    final hints = recognizedLanguageCodes
        .map(_normalizeLanguageCode)
        .where((code) => code != null && code != 'und')
        .cast<String>()
        .toList(growable: false);
    if (hints.isNotEmpty) {
      final counts = <String, int>{};
      for (final code in hints) {
        counts[code] = (counts[code] ?? 0) + 1;
      }
      final ordered = counts.entries.toList()
        ..sort((a, b) => b.value.compareTo(a.value));
      if (ordered.length == 1 || ordered[0].value > ordered[1].value) {
        return LanguageDetectionResult(
          code: ordered.first.key,
          status: LanguageDetectionStatus.detected,
          method: 'mlkit_recognized_languages',
          version: version,
          script: script,
        );
      }
    }

    final folded = rawText.toLowerCase();
    final scores = <String, int>{};
    for (final entry in labelLanguageLexicons.entries) {
      var score = 0;
      for (final signal in entry.value.detectionSignals.toSet()) {
        if (_containsTerm(folded, signal.toLowerCase())) score += 1;
      }
      if (score > 0) scores[entry.key] = score;
    }
    final ordered = scores.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    if (ordered.isNotEmpty &&
        (ordered.length == 1 || ordered[0].value > ordered[1].value)) {
      final confidence = (ordered.first.value / 4).clamp(0.25, 1.0);
      return LanguageDetectionResult(
        code: ordered.first.key,
        confidence: confidence,
        status: LanguageDetectionStatus.detected,
        method: 'versioned_label_lexicon',
        version: version,
        script: script,
      );
    }

    return LanguageDetectionResult(
      code: 'und',
      status: LanguageDetectionStatus.undetermined,
      method: 'no_confident_language_signal',
      version: version,
      script: script,
    );
  }

  static bool _containsTerm(String text, String term) {
    final escaped = RegExp.escape(term);
    return RegExp('(^|[^a-zà-ž])$escaped([^a-zà-ž]|\$)').hasMatch(text);
  }

  static String? _normalizeLanguageCode(String raw) {
    final value = raw.trim().replaceAll('_', '-');
    if (!RegExp(r'^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$').hasMatch(value)) {
      return null;
    }
    final parts = value.split('-');
    return [parts.first.toLowerCase(), ...parts.skip(1)].join('-');
  }
}

String languageDisplayNameItalian(String code) {
  return const {
        'it': 'italiano',
        'en': 'inglese',
        'fi': 'finlandese',
        'es': 'spagnolo',
        'fr': 'francese',
        'de': 'tedesco',
        'pt': 'portoghese',
        'sv': 'svedese',
        'und': 'non determinata',
      }[code] ??
      code;
}
