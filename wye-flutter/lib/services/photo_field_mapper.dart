enum ProductPhotoPurpose {
  identity,
  ingredients,
  nutrition,
}

class PhotoFieldMapping {
  final String? brandName;
  final String? productName;
  final String? category;
  final String? productType;
  final String? ingredientListText;
  final Map<String, double> nutrition;

  const PhotoFieldMapping({
    this.brandName,
    this.productName,
    this.category,
    this.productType,
    this.ingredientListText,
    this.nutrition = const {},
  });

  bool get hasIdentity =>
      brandName != null ||
      productName != null ||
      category != null ||
      productType != null;

  bool get hasIngredients => ingredientListText != null;

  bool get hasNutrition => nutrition.isNotEmpty;
}

/// Conservative OCR-to-form mapping.
///
/// A value is accepted only when its source is explicit for the requested
/// photo purpose. In particular, unlabelled marketing/title text is never
/// reused as an ingredient list.
class PhotoFieldMapper {
  static const _allowedProductTypes = {
    'snack',
    'beverage',
    'cosmetic',
    'bakery',
    'dairy',
    'cereal',
    'dessert',
    'sauce',
    'fruit',
    'other',
  };

  const PhotoFieldMapper();

  PhotoFieldMapping map(String rawText, ProductPhotoPurpose purpose) {
    final lines = rawText
        .split(RegExp(r'[\r\n]+'))
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .toList(growable: false);

    return switch (purpose) {
      ProductPhotoPurpose.identity => _mapIdentity(lines),
      ProductPhotoPurpose.ingredients => _mapIngredients(lines),
      ProductPhotoPurpose.nutrition => _mapNutrition(lines),
    };
  }

  PhotoFieldMapping _mapIdentity(List<String> lines) {
    String? labelledValue(List<String> labels) {
      for (final line in lines) {
        for (final label in labels) {
          final match = RegExp(
            '^${RegExp.escape(label)}\\s*[:\\-]\\s*(.+)\$',
            caseSensitive: false,
          ).firstMatch(line);
          final value = match?.group(1)?.trim();
          if (value != null && value.length >= 2 && value.length <= 100) {
            return value;
          }
        }
      }
      return null;
    }

    final category = labelledValue(const ['categoria', 'category']);
    final rawType = labelledValue(const [
      'tipo prodotto',
      'product type',
      'tipo',
      'type',
    ]);
    final normalizedType = rawType?.toLowerCase().replaceAll(' ', '_');

    return PhotoFieldMapping(
      brandName: labelledValue(const ['marca', 'brand']),
      productName:
          labelledValue(const ['nome prodotto', 'product name', 'prodotto']),
      category: category == null ? null : category.toLowerCase(),
      productType: normalizedType != null &&
              _allowedProductTypes.contains(normalizedType)
          ? normalizedType
          : null,
    );
  }

  PhotoFieldMapping _mapIngredients(List<String> lines) {
    final marker = RegExp(
      r'^(ingredienti|ingredients|lista ingredienti|ingredient list)\s*[:\-]?\s*(.*)$',
      caseSensitive: false,
    );
    final stop = RegExp(
      r'^(valori nutrizionali|dichiarazione nutrizionale|nutrition|nutrition facts|informazioni nutrizionali)\b',
      caseSensitive: false,
    );

    final collected = <String>[];
    var collecting = false;
    for (final line in lines) {
      final start = marker.firstMatch(line);
      if (start != null) {
        collecting = true;
        final sameLine = start.group(2)?.trim();
        if (sameLine != null && sameLine.isNotEmpty) {
          collected.add(sameLine);
        }
        continue;
      }
      if (collecting && stop.hasMatch(line)) {
        break;
      }
      if (collecting) {
        collected.add(line);
      }
    }

    final value = collected.join(' ').trim();
    if (value.length < 3) {
      return const PhotoFieldMapping();
    }
    return PhotoFieldMapping(ingredientListText: value);
  }

  PhotoFieldMapping _mapNutrition(List<String> lines) {
    final hasTableContext = lines.any(
      (line) => RegExp(
        r'(valori nutrizionali|dichiarazione nutrizionale|nutrition facts|per 100\s*(g|ml))',
        caseSensitive: false,
      ).hasMatch(line),
    );
    if (!hasTableContext) {
      return const PhotoFieldMapping();
    }

    final result = <String, double>{};
    void capture(String key, RegExp label, {String unit = 'g'}) {
      for (final line in lines) {
        if (!label.hasMatch(line)) continue;
        final match = RegExp(
          r'(-?\d+(?:[\.,]\d+)?)\s*(kcal|kj|mg|g)\b',
          caseSensitive: false,
        ).firstMatch(line);
        if (match == null) continue;
        final parsed = double.tryParse(match.group(1)!.replaceAll(',', '.'));
        final foundUnit = match.group(2)!.toLowerCase();
        if (parsed == null || parsed < 0) continue;
        if (key == 'energy_kcal' && foundUnit != 'kcal') continue;
        if (key != 'energy_kcal' && foundUnit != unit) continue;
        result[key] = parsed;
        return;
      }
    }

    capture(
        'energy_kcal', RegExp(r'\b(energia|energy)\b', caseSensitive: false),
        unit: 'kcal');
    capture(
        'protein_g', RegExp(r'\b(proteine|protein)\b', caseSensitive: false));
    capture(
        'carbs_g',
        RegExp(r'\b(carboidrati|carbohydrate|carbohydrates)\b',
            caseSensitive: false));
    capture('sugar_g', RegExp(r'\b(zuccheri|sugars?)\b', caseSensitive: false));
    capture('fat_g', RegExp(r'^(grassi|fat)\b', caseSensitive: false));
    capture(
      'saturated_fat_g',
      RegExp(r'\b(saturi|saturates|saturated fat)\b', caseSensitive: false),
    );
    capture('fiber_g',
        RegExp(r'\b(fibre|fiber|fibre alimentari)\b', caseSensitive: false));
    capture('sodium_mg', RegExp(r'\b(sodio|sodium)\b', caseSensitive: false),
        unit: 'mg');

    return PhotoFieldMapping(nutrition: result);
  }
}
