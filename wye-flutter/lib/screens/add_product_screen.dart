import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';

import '../providers/app_providers.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';

class AddProductScreen extends StatefulWidget {
  const AddProductScreen({Key? key}) : super(key: key);

  @override
  State<AddProductScreen> createState() => _AddProductScreenState();
}

class _AddProductScreenState extends State<AddProductScreen> {
  final _formKey = GlobalKey<FormState>();
  final _barcodeController = TextEditingController();
  final _brandController = TextEditingController();
  final _productNameController = TextEditingController();
  final _categoryController = TextEditingController(text: 'food');
  final _productTypeController = TextEditingController(text: 'snack');
  final _ingredientsController = TextEditingController();
  final _energyController = TextEditingController();
  final _proteinController = TextEditingController();
  final _carbsController = TextEditingController();
  final _sugarController = TextEditingController();
  final _fatController = TextEditingController();
  final _saturatedFatController = TextEditingController();
  final _sodiumController = TextEditingController();
  final _fiberController = TextEditingController();

  XFile? _ingredientsImage;
  bool _isSubmitting = false;
  bool _isProcessingImage = false;

  final ImagePicker _picker = ImagePicker();

  @override
  void dispose() {
    _barcodeController.dispose();
    _brandController.dispose();
    _productNameController.dispose();
    _categoryController.dispose();
    _productTypeController.dispose();
    _ingredientsController.dispose();
    _energyController.dispose();
    _proteinController.dispose();
    _carbsController.dispose();
    _sugarController.dispose();
    _fatController.dispose();
    _saturatedFatController.dispose();
    _sodiumController.dispose();
    _fiberController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(void Function(XFile?) setter, ImageSource source) async {
    final file = await _picker.pickImage(source: source, imageQuality: 85);
    if (file == null) return;

    setter(file);
    setState(() {});

    if (source == ImageSource.camera) {
      await _extractTextFromPhoto(file);
    }
  }

  Future<void> _openBarcodeScanner() async {
    final barcode = await showDialog<String>(
      context: context,
      builder: (context) {
        final scannerController = MobileScannerController();

        return Dialog(
          insetPadding: const EdgeInsets.all(16),
          child: SizedBox(
            height: 460,
            width: 360,
            child: Stack(
              children: [
                MobileScanner(
                  controller: scannerController,
                  onDetect: (capture) {
                    final detected = capture.barcodes.first.rawValue?.trim();
                    if (detected != null && detected.isNotEmpty) {
                      scannerController.dispose();
                      Navigator.of(context).pop(detected);
                    }
                  },
                ),
                Positioned(
                  top: 12,
                  right: 12,
                  child: IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close, color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );

    if (barcode != null && barcode.isNotEmpty) {
      _barcodeController.text = barcode;
      _barcodeController.selection = TextSelection.fromPosition(
        TextPosition(offset: barcode.length),
      );
      setState(() {});
    }
  }

  Future<void> _extractTextFromPhoto(XFile file) async {
    setState(() => _isProcessingImage = true);

    try {
      final image = InputImage.fromFilePath(file.path);
      final recognizer = TextRecognizer();
      final recognizedText = await recognizer.processImage(image);
      final rawText = recognizedText.text.trim();
      await recognizer.close();

      if (rawText.isEmpty) {
        throw Exception('Nessun testo rilevato nella foto');
      }

      final barcodeValue = _extractBarcodeValue(rawText);
      if (barcodeValue != null) {
        _barcodeController.text = barcodeValue;
      }

      final normalized = await ApiClient().normalizePhotoText(rawText: rawText);
      final ingredients = (normalized['ingredients'] as List?)?.whereType<String>().toList() ?? const <String>[];

      if (ingredients.isNotEmpty) {
        _ingredientsController.text = ingredients.join(', ');
      }

      if (mounted) {
        final hasData = barcodeValue != null || ingredients.isNotEmpty;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              hasData
                  ? 'Testo della foto analizzato con AI e ingredienti precompilati.'
                  : 'Nessun dato rilevato dalla foto. Riprova con una foto più chiara.',
            ),
            backgroundColor: AppColors.primary,
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Non è stato possibile leggere la foto. Riprova con una foto più chiara.'),
            backgroundColor: AppColors.riskHigh,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isProcessingImage = false);
      }
    }
  }

  String? _extractBarcodeValue(String rawText) {
    final digitsOnly = rawText.replaceAll(RegExp(r'[^0-9]'), '');
    final matches = RegExp(r'\d{8,20}').allMatches(digitsOnly);
    for (final match in matches) {
      final value = match.group(0);
      if (value != null && value.length >= 8) {
        return value;
      }
    }
    return null;
  }

  String? _validateNumericField(String? value, {bool required = false}) {
    final text = value?.trim() ?? '';
    if (text.isEmpty) {
      if (required) {
        return 'Campo obbligatorio';
      }
      return null;
    }

    final numericPattern = RegExp(r'^\d+(?:[.,]\d+)?$');
    if (!numericPattern.hasMatch(text)) {
      return 'Inserisci solo valori numerici';
    }

    return null;
  }

  Map<String, dynamic> _buildNutrition() {
    final nutrition = <String, dynamic>{};

    void addIfPresent(String key, TextEditingController controller) {
      final value = controller.text.trim();
      if (value.isNotEmpty) {
        final normalized = value.replaceAll(',', '.');
        final parsed = double.tryParse(normalized);
        if (parsed != null) {
          nutrition[key] = parsed;
        }
      }
    }

    addIfPresent('energy_kcal', _energyController);
    addIfPresent('protein_g', _proteinController);
    addIfPresent('carbs_g', _carbsController);
    addIfPresent('sugar_g', _sugarController);
    addIfPresent('fat_g', _fatController);
    addIfPresent('saturated_fat_g', _saturatedFatController);
    addIfPresent('sodium_mg', _sodiumController);
    addIfPresent('fiber_g', _fiberController);

    return nutrition;
  }

  Future<void> _submit() async {
    final requiredNutritionFields = [
      _energyController,
      _proteinController,
      _carbsController,
      _fatController,
    ];

    for (final field in requiredNutritionFields) {
      final validatorMessage = _validateNumericField(field.text, required: true);
      if (validatorMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(validatorMessage),
            backgroundColor: AppColors.riskHigh,
          ),
        );
        return;
      }
    }

    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSubmitting = true);

    try {
      final provider = context.read<BarcodeScannerProvider>();
      await provider.addProductFromSubmission(
        barcode: _barcodeController.text.trim(),
        brandName: _brandController.text.trim(),
        productName: _productNameController.text.trim(),
        category: _categoryController.text.trim(),
        productType: _productTypeController.text.trim(),
        ingredients: _ingredientsController.text.trim(),
        nutritionFacts: _buildNutrition(),
      );

      if (mounted) {
        final message = provider.error == null
            ? 'Prodotto salvato correttamente nel database.'
            : provider.error ?? 'Errore durante il salvataggio';

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(message),
            backgroundColor: provider.error == null ? AppColors.success : AppColors.riskHigh,
          ),
        );

        if (provider.error == null) {
          context.go('/');
        }
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Aggiungi Prodotto'),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.home_rounded),
          tooltip: 'Torna alla home',
          onPressed: () => context.go('/'),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.primary.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.camera_alt_outlined, color: AppColors.primary),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Barcode e ingredienti possono essere precompilati dalle foto. I valori nutrizionali vanno inseriti manualmente e le calorie, proteine, carboidrati e grassi sono obbligatori.',
                          style: AppTypography.bodyMedium,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                Text('Barcode', style: AppTypography.label),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _barcodeController,
                  decoration: InputDecoration(
                    hintText: 'Es: 9876543210987',
                    prefixIcon: const Icon(Icons.qr_code),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.camera_alt),
                      onPressed: _openBarcodeScanner,
                    ),
                  ),
                  validator: (value) => (value == null || value.trim().isEmpty) ? 'Inserisci il barcode' : null,
                ),
                const SizedBox(height: 16),

                Text('Brand', style: AppTypography.label),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _brandController,
                  decoration: const InputDecoration(
                    hintText: 'Es: Bio Natura',
                    prefixIcon: Icon(Icons.business),
                  ),
                  validator: (value) => (value == null || value.trim().isEmpty) ? 'Inserisci il brand' : null,
                ),
                const SizedBox(height: 16),

                Text('Nome prodotto', style: AppTypography.label),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _productNameController,
                  decoration: const InputDecoration(
                    hintText: 'Es: Granola al cacao',
                    prefixIcon: Icon(Icons.shopping_bag),
                  ),
                  validator: (value) => (value == null || value.trim().isEmpty) ? 'Inserisci il nome del prodotto' : null,
                ),
                const SizedBox(height: 16),

                Text('Categoria', style: AppTypography.label),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _categoryController,
                  decoration: const InputDecoration(
                    hintText: 'food',
                    prefixIcon: Icon(Icons.category),
                  ),
                ),
                const SizedBox(height: 16),

                Text('Tipo prodotto', style: AppTypography.label),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _productTypeController,
                  decoration: const InputDecoration(
                    hintText: 'snack',
                    prefixIcon: Icon(Icons.inventory_2),
                  ),
                ),
                const SizedBox(height: 24),

                Text('Ingredienti', style: AppTypography.label),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _ingredientsController,
                  maxLines: 5,
                  decoration: const InputDecoration(
                    hintText: 'Gli ingredienti vengono precompilati da foto e possono essere corretti manualmente.',
                    prefixIcon: Icon(Icons.list_alt),
                  ),
                ),
                const SizedBox(height: 8),
                _ImagePickerTile(
                  label: _ingredientsImage == null ? 'Scatta/Carica foto ingredienti' : 'Foto ingredienti pronta',
                  file: _ingredientsImage,
                  onTap: () => _pickImage((file) => _ingredientsImage = file, ImageSource.camera),
                ),
                const SizedBox(height: 24),

                Text('Valori nutrizionali', style: AppTypography.headline3),
                const SizedBox(height: 8),
                Text(
                  'Inserisci manualmente i valori numerici richiesti. Sodio e fibre sono opzionali.',
                  style: AppTypography.bodySmall,
                ),
                const SizedBox(height: 16),
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 2.4,
                  children: [
                    _NumberField(
                      controller: _energyController,
                      label: 'Energia kcal',
                    ),
                    _NumberField(
                      controller: _proteinController,
                      label: 'Proteine g',
                    ),
                    _NumberField(
                      controller: _carbsController,
                      label: 'Carboidrati g',
                    ),
                    _NumberField(controller: _sugarController, label: 'Zuccheri g'),
                    _NumberField(
                      controller: _fatController,
                      label: 'Grassi g',
                    ),
                    _NumberField(controller: _saturatedFatController, label: 'Grassi saturi g'),
                    _NumberField(controller: _sodiumController, label: 'Sodio mg'),
                    _NumberField(controller: _fiberController, label: 'Fibre g'),
                  ],
                ),
                const SizedBox(height: 24),

                if (_isProcessingImage)
                  const Padding(
                    padding: EdgeInsets.only(bottom: 12),
                    child: Center(
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                  ),

                ElevatedButton.icon(
                  onPressed: _isSubmitting ? null : _submit,
                  icon: _isSubmitting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.save_alt),
                  label: Text(_isSubmitting ? 'Salvataggio...' : 'Salva prodotto nel database'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () => context.go('/'),
                  icon: const Icon(Icons.home),
                  label: const Text('Torna alla home'),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'Storico'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Impostazioni'),
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

class _ImagePickerTile extends StatelessWidget {
  final String label;
  final XFile? file;
  final VoidCallback onTap;

  const _ImagePickerTile({
    required this.label,
    this.file,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.lightGrey,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.borderGrey),
        ),
        child: Row(
          children: [
            Icon(file == null ? Icons.add_a_photo_outlined : Icons.check_circle, color: AppColors.primary),
            const SizedBox(width: 12),
            Expanded(child: Text(label, style: AppTypography.bodyMedium)),
          ],
        ),
      ),
    );
  }
}

class _NumberField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final String? Function(String?)? validator;

  const _NumberField({
    required this.controller,
    required this.label,
    this.validator,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
      ),
      validator: validator,
    );
  }
}
