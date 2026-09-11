class LabelLanguageLexicon {
  final List<String> ingredientHeadings;
  final List<String> nutritionHeadings;
  final Map<String, List<String>> nutrientLabels;
  final Map<String, String> ingredientTranslations;
  final List<String> servingWords;

  const LabelLanguageLexicon({
    required this.ingredientHeadings,
    required this.nutritionHeadings,
    required this.nutrientLabels,
    required this.ingredientTranslations,
    required this.servingWords,
  });

  Iterable<String> get detectionSignals sync* {
    yield* ingredientHeadings;
    yield* nutritionHeadings;
    yield* ingredientTranslations.keys;
    yield* servingWords;
    for (final labels in nutrientLabels.values) {
      yield* labels;
    }
  }
}

/// Versioned deterministic optimizations. This is not a language allowlist:
/// unlisted Latin-language labels continue through structural parsing and the
/// optional text-only fallback.
const labelLexiconVersion = 'label_lexicon_v1';

const labelLanguageLexicons = <String, LabelLanguageLexicon>{
  'en': LabelLanguageLexicon(
    ingredientHeadings: ['ingredients', 'ingredient list'],
    nutritionHeadings: ['nutrition facts', 'nutrition information'],
    nutrientLabels: {
      'energy': ['energy'],
      'fat_g': ['fat', 'total fat'],
      'saturated_fat_g': ['saturated fat', 'saturates'],
      'carbohydrate_g': ['carbohydrate', 'carbohydrates'],
      'sugars_g': ['sugars', 'sugar'],
      'fibre_g': ['fibre', 'fiber'],
      'protein_g': ['protein'],
      'salt_g': ['salt'],
      'sodium_mg': ['sodium'],
    },
    ingredientTranslations: {
      'water': 'water',
      'sugar': 'sugar',
      'salt': 'salt',
      'wheat flour': 'wheat flour',
      'milk': 'milk',
      'oats': 'oats',
      'nuts': 'nuts',
    },
    servingWords: ['serving', 'portion'],
  ),
  'it': LabelLanguageLexicon(
    ingredientHeadings: ['ingredienti', 'lista ingredienti'],
    nutritionHeadings: [
      'valori nutrizionali',
      'dichiarazione nutrizionale',
      'informazioni nutrizionali',
    ],
    nutrientLabels: {
      'energy': ['energia'],
      'fat_g': ['grassi'],
      'saturated_fat_g': ['grassi saturi', 'di cui saturi'],
      'carbohydrate_g': ['carboidrati'],
      'sugars_g': ['zuccheri', 'di cui zuccheri'],
      'fibre_g': ['fibre', 'fibre alimentari'],
      'protein_g': ['proteine'],
      'salt_g': ['sale'],
      'sodium_mg': ['sodio'],
    },
    ingredientTranslations: {
      'acqua': 'water',
      'zucchero': 'sugar',
      'sale': 'salt',
      'farina di grano': 'wheat flour',
      'latte': 'milk',
      'avena': 'oats',
      'noci': 'nuts',
    },
    servingWords: ['porzione'],
  ),
  'fi': LabelLanguageLexicon(
    ingredientHeadings: ['ainesosat'],
    nutritionHeadings: ['ravintosisältö', 'ravintoarvo'],
    nutrientLabels: {
      'energy': ['energia'],
      'fat_g': ['rasvaa'],
      'saturated_fat_g': ['tyydyttyneitä', 'josta tyydyttyneitä'],
      'carbohydrate_g': ['hiilihydraattia'],
      'sugars_g': ['sokereita', 'josta sokereita'],
      'fibre_g': ['ravintokuitua'],
      'protein_g': ['proteiinia'],
      'salt_g': ['suolaa'],
      'sodium_mg': ['natriumia'],
    },
    ingredientTranslations: {
      'vesi': 'water',
      'sokeri': 'sugar',
      'suola': 'salt',
      'vehnäjauho': 'wheat flour',
      'maito': 'milk',
      'täysjyväkaura': 'whole grain oats',
      'pähkinä': 'nut',
    },
    servingWords: ['annos'],
  ),
  'es': LabelLanguageLexicon(
    ingredientHeadings: ['ingredientes'],
    nutritionHeadings: ['información nutricional', 'valores nutricionales'],
    nutrientLabels: {
      'energy': ['energía', 'valor energético'],
      'fat_g': ['grasas'],
      'saturated_fat_g': ['grasas saturadas', 'de las cuales saturadas'],
      'carbohydrate_g': ['hidratos de carbono', 'carbohidratos'],
      'sugars_g': ['azúcares', 'de los cuales azúcares'],
      'fibre_g': ['fibra'],
      'protein_g': ['proteínas'],
      'salt_g': ['sal'],
      'sodium_mg': ['sodio'],
    },
    ingredientTranslations: {
      'agua': 'water',
      'azúcar': 'sugar',
      'sal': 'salt',
      'harina de trigo': 'wheat flour',
      'leche': 'milk',
      'avena': 'oats',
      'nueces': 'nuts',
    },
    servingWords: ['porción'],
  ),
  'fr': LabelLanguageLexicon(
    ingredientHeadings: ['ingrédients', 'liste des ingrédients'],
    nutritionHeadings: [
      'informations nutritionnelles',
      'valeurs nutritionnelles'
    ],
    nutrientLabels: {
      'energy': ['énergie', 'valeur énergétique'],
      'fat_g': ['matières grasses'],
      'saturated_fat_g': ['acides gras saturés', 'dont acides gras saturés'],
      'carbohydrate_g': ['glucides'],
      'sugars_g': ['sucres', 'dont sucres'],
      'fibre_g': ['fibres alimentaires', 'fibres'],
      'protein_g': ['protéines'],
      'salt_g': ['sel'],
      'sodium_mg': ['sodium'],
    },
    ingredientTranslations: {
      'eau': 'water',
      'sucre': 'sugar',
      'sel': 'salt',
      'farine de blé': 'wheat flour',
      'lait': 'milk',
      'avoine': 'oats',
      'noix': 'nuts',
    },
    servingWords: ['portion'],
  ),
  'de': LabelLanguageLexicon(
    ingredientHeadings: ['zutaten', 'zutatenliste'],
    nutritionHeadings: ['nährwertangaben', 'nährwerte'],
    nutrientLabels: {
      'energy': ['energie', 'brennwert'],
      'fat_g': ['fett'],
      'saturated_fat_g': [
        'gesättigte fettsäuren',
        'davon gesättigte fettsäuren'
      ],
      'carbohydrate_g': ['kohlenhydrate'],
      'sugars_g': ['zucker', 'davon zucker'],
      'fibre_g': ['ballaststoffe'],
      'protein_g': ['eiweiß', 'protein'],
      'salt_g': ['salz'],
      'sodium_mg': ['natrium'],
    },
    ingredientTranslations: {
      'wasser': 'water',
      'zucker': 'sugar',
      'salz': 'salt',
      'weizenmehl': 'wheat flour',
      'milch': 'milk',
      'hafer': 'oats',
      'nüsse': 'nuts',
    },
    servingWords: ['portion'],
  ),
  'pt': LabelLanguageLexicon(
    ingredientHeadings: ['ingredientes'],
    nutritionHeadings: ['informação nutricional', 'declaração nutricional'],
    nutrientLabels: {
      'energy': ['energia', 'valor energético'],
      'fat_g': ['lípidos', 'gorduras'],
      'saturated_fat_g': ['ácidos gordos saturados', 'gorduras saturadas'],
      'carbohydrate_g': ['hidratos de carbono', 'carboidratos'],
      'sugars_g': ['açúcares'],
      'fibre_g': ['fibra'],
      'protein_g': ['proteínas'],
      'salt_g': ['sal'],
      'sodium_mg': ['sódio'],
    },
    ingredientTranslations: {
      'água': 'water',
      'açúcar': 'sugar',
      'sal': 'salt',
      'farinha de trigo': 'wheat flour',
      'leite': 'milk',
      'aveia': 'oats',
      'nozes': 'nuts',
    },
    servingWords: ['porção'],
  ),
  'sv': LabelLanguageLexicon(
    ingredientHeadings: ['ingredienser', 'ingrediensförteckning'],
    nutritionHeadings: ['näringsdeklaration', 'näringsvärde'],
    nutrientLabels: {
      'energy': ['energi'],
      'fat_g': ['fett'],
      'saturated_fat_g': ['mättat fett', 'varav mättat fett'],
      'carbohydrate_g': ['kolhydrat'],
      'sugars_g': ['sockerarter', 'varav sockerarter'],
      'fibre_g': ['fiber'],
      'protein_g': ['protein'],
      'salt_g': ['salt'],
      'sodium_mg': ['natrium'],
    },
    ingredientTranslations: {
      'vatten': 'water',
      'socker': 'sugar',
      'salt': 'salt',
      'vetemjöl': 'wheat flour',
      'mjölk': 'milk',
      'havre': 'oats',
      'nötter': 'nuts',
    },
    servingWords: ['portion'],
  ),
};
