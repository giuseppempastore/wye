import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';
import '../widgets/score_widgets.dart';

class ManualAnalysisScreen extends StatefulWidget {
  const ManualAnalysisScreen({Key? key}) : super(key: key);

  @override
  State<ManualAnalysisScreen> createState() => _ManualAnalysisScreenState();
}

class _ManualAnalysisScreenState extends State<ManualAnalysisScreen> {
  final TextEditingController _productNameController = TextEditingController();
  final TextEditingController _ingredientsController = TextEditingController();
  String _selectedLanguage = 'it';
  String _selectedCategory = 'food';
  bool _isAnalyzing = false;

  @override
  void dispose() {
    _productNameController.dispose();
    _ingredientsController.dispose();
    super.dispose();
  }

  Future<void> _analyze() async {
    if (_productNameController.text.isEmpty ||
        _ingredientsController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Per favore, compila tutti i campi'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }

    setState(() => _isAnalyzing = true);

    final provider = context.read<BarcodeScannerProvider>();
    await provider.analyzeIngredients(
      productName: _productNameController.text,
      ingredients: _ingredientsController.text,
      language: _selectedLanguage,
      category: _selectedCategory,
    );

    setState(() => _isAnalyzing = false);

    if (provider.currentProduct != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Analisi completata!'),
          backgroundColor: AppColors.success,
          duration: Duration(seconds: 1),
        ),
      );
      // Scroll to results
      Future.delayed(const Duration(milliseconds: 500), () {
        if (mounted) {
          _scrollToResults();
        }
      });
    } else if (provider.error != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.error!),
          backgroundColor: AppColors.riskHigh,
        ),
      );
    }
  }

  void _scrollToResults() {
    // Implementare scroll automatico ai risultati
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analisi Manuale'),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.home_rounded),
          tooltip: 'Torna alla home',
          onPressed: () => context.go('/'),
        ),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Premium Feature Notice
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.accent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: AppColors.accent.withOpacity(0.5),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.star,
                      color: AppColors.accent,
                      size: 24,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Funzionalità Premium',
                            style: AppTypography.label,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Analizza prodotti non presenti nel catalogo',
                            style: AppTypography.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Product Name
              Text(
                'Nome Prodotto',
                style: AppTypography.label,
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _productNameController,
                decoration: InputDecoration(
                  hintText: 'Es: Biscotti al Cioccolato',
                  prefixIcon: const Icon(Icons.shopping_bag),
                ),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 24),

              // Category
              Text(
                'Categoria',
                style: AppTypography.label,
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _selectedCategory,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.category),
                ),
                items: [
                  const DropdownMenuItem(value: 'food', child: Text('Alimento')),
                  const DropdownMenuItem(
                    value: 'beverage',
                    child: Text('Bevanda'),
                  ),
                  const DropdownMenuItem(
                    value: 'cosmetic',
                    child: Text('Cosmetico'),
                  ),
                  const DropdownMenuItem(
                    value: 'supplement',
                    child: Text('Integratore'),
                  ),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _selectedCategory = value);
                  }
                },
              ),
              const SizedBox(height: 24),

              // Ingredients
              Text(
                'Lista Ingredienti',
                style: AppTypography.label,
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _ingredientsController,
                decoration: InputDecoration(
                  hintText:
                      'Es: acqua, zucchero, farina, burro, cacao, lievito...',
                  prefixIcon: const Icon(Icons.list),
                ),
                maxLines: 6,
                textAlignVertical: TextAlignVertical.top,
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 16),
              Text(
                'Puoi copiare la lista direttamente dal packaging',
                style: AppTypography.bodySmall,
              ),
              const SizedBox(height: 24),

              // Language
              Text(
                'Lingua Ingredienti',
                style: AppTypography.label,
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _selectedLanguage,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.language),
                ),
                items: [
                  const DropdownMenuItem(value: 'it', child: Text('Italiano')),
                  const DropdownMenuItem(value: 'en', child: Text('Inglese')),
                  const DropdownMenuItem(value: 'fr', child: Text('Francese')),
                  const DropdownMenuItem(value: 'es', child: Text('Spagnolo')),
                  const DropdownMenuItem(value: 'de', child: Text('Tedesco')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _selectedLanguage = value);
                  }
                },
              ),
              const SizedBox(height: 32),

              // Analyze Button
              Consumer<BarcodeScannerProvider>(
                builder: (context, provider, _) {
                  return ElevatedButton.icon(
                    onPressed: _isAnalyzing
                        ? null
                        : _productNameController.text.isNotEmpty &&
                                _ingredientsController.text.isNotEmpty
                            ? _analyze
                            : null,
                    icon: _isAnalyzing
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.analytics),
                    label: Text(
                      _isAnalyzing ? 'Analizzando...' : 'Analizza',
                    ),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  );
                },
              ),
              const SizedBox(height: 32),

              // Results Section
              Consumer<BarcodeScannerProvider>(
                builder: (context, provider, _) {
                  if (provider.currentProduct == null) {
                    return const SizedBox.shrink();
                  }

                  final product = provider.currentProduct!;

                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Divider(color: AppColors.borderGrey),
                      const SizedBox(height: 24),
                      Text(
                        'Risultati Analisi',
                        style: AppTypography.headline3,
                      ),
                      const SizedBox(height: 16),
                      ScoreCard(
                        score: product.finalScore,
                        ingredientScore: product.ingredientScore,
                        nutritionScore: product.nutritionScore,
                      ),
                      const SizedBox(height: 24),

                      // Allergens
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
                              AllergenBadge(allergen: allergen),
                          ],
                        ),
                        const SizedBox(height: 24),
                      ],

                      ElevatedButton.icon(
                        onPressed: () {
                          _productNameController.clear();
                          _ingredientsController.clear();
                          provider.reset();
                          setState(() {});
                        },
                        icon: const Icon(Icons.refresh),
                        label: const Text('Analizza un Altro'),
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: 'Storico',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'Impostazioni',
          ),
        ],
        currentIndex: 0,
        onTap: (index) {
          switch (index) {
            case 0:
              context.go('/');
              break;
            case 1:
              context.go('/history');
              break;
            case 2:
              context.go('/settings');
              break;
          }
        },
      ),
    );
  }
}
