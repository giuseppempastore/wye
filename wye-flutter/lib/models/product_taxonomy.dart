class ProductTaxonomyOption {
  final String id;
  final String label;

  const ProductTaxonomyOption(this.id, this.label);
}

const productTypeOptions = <ProductTaxonomyOption>[
  ProductTaxonomyOption('food', 'Alimento'),
  ProductTaxonomyOption('beverage', 'Bevanda'),
  ProductTaxonomyOption('supplement', 'Integratore alimentare'),
  ProductTaxonomyOption('ingredient', 'Ingrediente o materia prima'),
  ProductTaxonomyOption('other', 'Altro'),
];

const productCategoryOptions = <ProductTaxonomyOption>[
  ProductTaxonomyOption('beverages', 'Bevande'),
  ProductTaxonomyOption('sweets_snacks', 'Dolci e snack'),
  ProductTaxonomyOption('cereals_bakery', 'Cereali e prodotti da forno'),
  ProductTaxonomyOption('pasta_rice_grains', 'Pasta, riso e altri cereali'),
  ProductTaxonomyOption('dairy', 'Latte e derivati'),
  ProductTaxonomyOption('meat_cold_cuts', 'Carne e salumi'),
  ProductTaxonomyOption('fish_seafood', 'Pesce e prodotti ittici'),
  ProductTaxonomyOption('fruit_vegetables', 'Frutta e verdura'),
  ProductTaxonomyOption('legumes', 'Legumi'),
  ProductTaxonomyOption('sauces_condiments', 'Condimenti e salse'),
  ProductTaxonomyOption('oils_fats', 'Oli e grassi'),
  ProductTaxonomyOption('sugars_sweeteners', 'Zuccheri e dolcificanti'),
  ProductTaxonomyOption('ready_meals', 'Piatti pronti'),
  ProductTaxonomyOption(
    'plant_based_alternatives',
    'Prodotti vegetali alternativi',
  ),
  ProductTaxonomyOption('supplements', 'Integratori'),
  ProductTaxonomyOption('baby_food', 'Alimenti per bambini'),
  ProductTaxonomyOption('other', 'Altro'),
];

String productCategoryLabel(String id) {
  if (id == 'food' || id == 'foods') return 'Alimenti (dato legacy)';
  for (final option in productCategoryOptions) {
    if (option.id == id) return option.label;
  }
  return id;
}

String productTypeLabel(String? id) {
  for (final option in productTypeOptions) {
    if (option.id == id) return option.label;
  }
  return id ?? '';
}
