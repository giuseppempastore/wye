import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';
import '../widgets/score_widgets.dart';

class ProductDetailScreen extends StatefulWidget {
  final String barcode;

  const ProductDetailScreen({
    Key? key,
    required this.barcode,
  }) : super(key: key);

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  late Future<void> _loadProductFuture;

  @override
  void initState() {
    super.initState();
    _loadProductFuture = _loadProduct();
  }

  Future<void> _loadProduct() async {
    final provider = context.read<BarcodeScannerProvider>();
    if (provider.currentProduct == null || provider.currentProduct!.barcode != widget.barcode) {
      await provider.scanBarcode(widget.barcode);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dettagli Prodotto'),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.home_rounded),
          tooltip: 'Torna alla home',
          onPressed: () => context.go('/'),
        ),
      ),
      body: FutureBuilder<void>(
        future: _loadProductFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          return Consumer<BarcodeScannerProvider>(
            builder: (context, provider, _) {
              if (provider.currentProduct == null) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.error_outline,
                        size: 64,
                        color: AppColors.riskHigh,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        provider.error ?? 'Prodotto non trovato',
                        style: AppTypography.bodyMedium,
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: () => context.go('/'),
                        child: const Text('Torna alla home'),
                      ),
                    ],
                  ),
                );
              }

              final product = provider.currentProduct!;

              return SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Product Info
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                product.brand,
                                style: AppTypography.labelSmall,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                product.productName,
                                style: AppTypography.headline3,
                              ),
                              const SizedBox(height: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.bgPrimary,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  product.category,
                                  style: AppTypography.labelSmall,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Score Card
                      ScoreCard(
                        score: product.finalScore,
                        ingredientScore: product.ingredientScore,
                        nutritionScore: product.nutritionScore,
                      ),
                      const SizedBox(height: 24),

                      // Ingredients Section
                      if (product.ingredients.isNotEmpty) ...[
                        Text(
                          'Ingredienti',
                          style: AppTypography.headline3,
                        ),
                        const SizedBox(height: 12),
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                for (int i = 0; i < product.ingredients.length; i++)
                                  Padding(
                                    padding: EdgeInsets.only(
                                      bottom: i < product.ingredients.length - 1
                                          ? 12
                                          : 0,
                                    ),
                                    child: Row(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          '${i + 1}.',
                                          style: AppTypography.bodyMedium,
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Text(
                                            product.ingredients[i],
                                            style: AppTypography.bodyMedium,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],

                      // Allergens Section
                      if (product.allergens.isNotEmpty) ...[
                        Text(
                          'Allergeni Rilevati',
                          style: AppTypography.headline3,
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            for (String allergen in product.allergens)
                              AllergenBadge(
                                allergen: allergen,
                                isUserSensitive: context
                                    .read<UserPreferencesProvider>()
                                    .userAllergies
                                    .contains(allergen),
                              ),
                          ],
                        ),
                        const SizedBox(height: 24),
                      ],

                      // Dangerous substances Section
                      if (product.dangerousSubstances.isNotEmpty) ...[
                        Text(
                          'Sostanze Pericolose / Ritiri',
                          style: AppTypography.headline3,
                        ),
                        const SizedBox(height: 12),
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                for (int i = 0; i < product.dangerousSubstances.length; i++)
                                  Padding(
                                    padding: EdgeInsets.only(
                                      bottom: i < product.dangerousSubstances.length - 1 ? 12 : 0,
                                    ),
                                    child: Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Icon(
                                          Icons.warning_amber_rounded,
                                          color: AppColors.riskHigh,
                                          size: 18,
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Text(
                                            product.dangerousSubstances[i],
                                            style: AppTypography.bodyMedium,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],

                      // Nutrition Facts Section
                      if (product.nutritionFacts != null) ...[
                        Text(
                          'Valori Nutrizionali',
                          style: AppTypography.headline3,
                        ),
                        const SizedBox(height: 12),
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              children: [
                                _NutritionRow(
                                  label: 'Energia',
                                  value:
                                      '${product.nutritionFacts!.energyKcal?.toStringAsFixed(0) ?? 'N/A'} kcal',
                                ),
                                _NutritionRow(
                                  label: 'Proteine',
                                  value:
                                      '${product.nutritionFacts!.protein?.toStringAsFixed(1) ?? 'N/A'} g',
                                ),
                                _NutritionRow(
                                  label: 'Carboidrati',
                                  value:
                                      '${product.nutritionFacts!.carbs?.toStringAsFixed(1) ?? 'N/A'} g',
                                ),
                                _NutritionRow(
                                  label: 'Zuccheri',
                                  value:
                                      '${product.nutritionFacts!.sugar?.toStringAsFixed(1) ?? 'N/A'} g',
                                ),
                                _NutritionRow(
                                  label: 'Grassi',
                                  value:
                                      '${product.nutritionFacts!.fat?.toStringAsFixed(1) ?? 'N/A'} g',
                                ),
                                _NutritionRow(
                                  label: 'Grassi Saturi',
                                  value:
                                      '${product.nutritionFacts!.saturatedFat?.toStringAsFixed(1) ?? 'N/A'} g',
                                ),
                                _NutritionRow(
                                  label: 'Sodio',
                                  value:
                                      '${product.nutritionFacts!.sodium?.toStringAsFixed(0) ?? 'N/A'} mg',
                                ),
                                _NutritionRow(
                                  label: 'Fibre',
                                  value:
                                      '${product.nutritionFacts!.fiber?.toStringAsFixed(1) ?? 'N/A'} g',
                                  isLast: true,
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],

                      const SizedBox(height: 24),

                      // Action Buttons
                      ElevatedButton.icon(
                        onPressed: () => context.go('/scanner'),
                        icon: const Icon(Icons.qr_code_scanner),
                        label: const Text('Scansiona un Altro Prodotto'),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: () => context.go('/history'),
                        icon: const Icon(Icons.history),
                        label: const Text('Visualizza Storico'),
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _NutritionRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isLast;

  const _NutritionRow({
    Key? key,
    required this.label,
    required this.value,
    this.isLast = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: AppTypography.bodyMedium),
            Text(value, style: AppTypography.bodyLarge),
          ],
        ),
        if (!isLast)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Divider(
              height: 1,
              color: AppColors.borderGrey,
            ),
          ),
      ],
    );
  }
}
