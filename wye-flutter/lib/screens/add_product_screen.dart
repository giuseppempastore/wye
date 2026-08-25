import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_cropper/image_cropper.dart';
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
  final _categoryController = TextEditingController();
  final _productTypeController = TextEditingController();
  final List<String> _productTypeOptions = const [
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
  ];
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
  XFile? _productImage;
  XFile? _nutritionImage;
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

  Future<void> _pickImage(
    void Function(XFile?) setter,
    ImageSource source, {
    bool isProductPhoto = false,
  }) async {
    final pickedFile = await _picker.pickImage(source: source, imageQuality: 85);
    if (pickedFile == null) return;

    XFile finalFile = pickedFile;
    try {
      final croppedFile = await _cropImage(pickedFile);
      if (croppedFile != null) {
        finalFile = croppedFile;
      }
    } catch (error) {
      debugPrint('Crop not available: $error');
    }

    setter(finalFile);
    setState(() {});

    await _extractTextFromPhoto(finalFile, isProductPhoto: isProductPhoto);
  }

  Future<XFile?> _cropImage(XFile file) async {
    try {
      final croppedFile = await ImageCropper().cropImage(
        sourcePath: file.path,
        uiSettings: [
          AndroidUiSettings(
            toolbarTitle: 'Ritaglia immagine',
            toolbarColor: Colors.black,
            toolbarWidgetColor: Colors.white,
            initAspectRatio: CropAspectRatioPreset.original,
            lockAspectRatio: false,
            hideBottomControls: false,
          ),
          IOSUiSettings(
            title: 'Ritaglia immagine',
            minimumAspectRatio: 1.0,
          ),
        ],
      );

      if (croppedFile == null) {
        return null;
      }

      return XFile(croppedFile.path);
    } on Exception catch (error) {
      debugPrint('Image cropper failed: $error');
      return null;
    }
  }

  Future<ImageSource?> _chooseImageSource() async {
    return await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Scatta foto'),
              onTap: () => Navigator.of(context).pop(ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Scegli dalla galleria'),
              onTap: () => Navigator.of(context).pop(ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
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

  Future<void> _extractTextFromPhoto(
    XFile file, {
    required bool isProductPhoto,
  }) async {
    setState(() => _isProcessingImage = true);

    try {
      final bytes = await file.readAsBytes();
      final imageUrl = 'data:image/jpeg;base64,${base64Encode(bytes)}';
      debugPrint('Sending image to backend (${bytes.length} bytes) for OCR');

      final image = InputImage.fromFilePath(file.path);
      final recognizer = TextRecognizer();
      final recognizedText = await recognizer.processImage(image);
      final rawText = recognizedText.text.trim();
      await recognizer.close();

      final barcodeValue = _extractBarcodeValue(rawText);
      if (isProductPhoto && barcodeValue != null && _isValidBarcode(barcodeValue)) {
        _barcodeController.text = barcodeValue;
      }

      final normalized = await ApiClient().analyzeProductImage(
        imageUrl: imageUrl,
        rawText: rawText,
      );
      debugPrint('Backend returned normalized: $normalized');

      final productName = (normalized['product_name'] as String?)?.trim();
      final brandName = (normalized['brand_name'] as String?)?.trim();
      final category = (normalized['category'] as String?)?.trim().toLowerCase();
      final productType = (normalized['product_type'] as String?)?.trim().toLowerCase();
      final nutrition = normalized['nutrition'] as Map<String, dynamic>? ?? const {};
      final ingredients = (normalized['ingredients'] as List?)?.whereType<String>().toList() ?? const <String>[];

      if (isProductPhoto && category != null && category.isNotEmpty && category != 'food' && category != 'foods') {
        throw Exception('Il prodotto non risulta essere un food. Il processo è stato interrotto.');
      }

      if (isProductPhoto) {
        if (productName != null && productName.isNotEmpty) {
          _productNameController.text = productName;
        }
        if (brandName != null && brandName.isNotEmpty) {
          _brandController.text = brandName;
        }
        if (category != null && category.isNotEmpty) {
          _categoryController.text = category;
        }
        if (productType != null && productType.isNotEmpty) {
          _productTypeController.text = productType;
        }
      }

      if (!isProductPhoto && ingredients.isNotEmpty) {
        _ingredientsController.text = ingredients.join(', ');
      }

      if (isProductPhoto && ingredients.isNotEmpty && _ingredientsController.text.trim().isEmpty) {
        _ingredientsController.text = ingredients.join(', ');
      }

      if (isProductPhoto) {
        void setterIfPresent(String key, TextEditingController controller) {
          final value = nutrition[key];
          if (value == null) return;
          controller.text = value.toString();
        }

        setterIfPresent('energy_kcal', _energyController);
        setterIfPresent('protein_g', _proteinController);
        setterIfPresent('carbs_g', _carbsController);
        setterIfPresent('sugar_g', _sugarController);
        setterIfPresent('fat_g', _fatController);
        setterIfPresent('saturated_fat_g', _saturatedFatController);
        setterIfPresent('sodium_mg', _sodiumController);
        setterIfPresent('fiber_g', _fiberController);
      }

      if (mounted) {
        final hasData = barcodeValue != null || ingredients.isNotEmpty || productName != null || brandName != null || nutrition.isNotEmpty;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              hasData
                  ? (isProductPhoto
                      ? 'Foto prodotto analizzata: brand, nome, categoria e tipo precompilati.'
                      : 'Foto ingredienti analizzata: ingredienti aggiornati.')
                  : 'Nessun dato rilevato dalla foto. Riprova con una foto più chiara.',
            ),
            backgroundColor: AppColors.primary,
          ),
        );
      }
    } catch (error, stackTrace) {
      debugPrint('Photo analysis failed: $error');
      debugPrint('Photo analysis stack trace: $stackTrace');

      if (mounted) {
        final errText = error?.toString() ?? '';
        final isFoodValidationError = errText.contains('non risulta essere un food');
        final isNetworkError = errText.toLowerCase().contains('network') ||
            errText.toLowerCase().contains('socket') ||
            errText.toLowerCase().contains('timeout') ||
            errText.toLowerCase().contains('connection');

        final userMessage = isFoodValidationError
            ? 'Il prodotto non è classificato come food. Il salvataggio è stato interrotto.'
            : isNetworkError
                ? 'Impossibile raggiungere il backend: verifica che il server sia avviato e che il reverse port adb sia attivo.'
                : 'Non è stato possibile leggere la foto. Riprova con una foto più chiara. Errore: ${errText.split("\n").first}';

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(userMessage),
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

  bool _isValidBarcode(String value) {
    final digits = value.replaceAll(RegExp(r'\D'), '');
    if (digits.length != 13) {
      return false;
    }

    int total = 0;
    for (int i = 0; i < 12; i++) {
      final digit = int.parse(digits[i]);
      total += digit * (i % 2 == 0 ? 1 : 3);
    }

    final expectedCheckDigit = (10 - (total % 10)) % 10;
    return expectedCheckDigit == int.parse(digits[12]);
  }

  String? _extractBarcodeValue(String rawText) {
    final matches = RegExp(r'\b\d{8,14}\b').allMatches(rawText);
    final candidates = <String>[];

    for (final match in matches) {
      final value = match.group(0);
      if (value == null) continue;

      final numeric = value.trim();
      if (!RegExp(r'^\d+$').hasMatch(numeric)) continue;
      if (numeric.length != 13) continue;

      if (_isValidBarcode(numeric)) {
        candidates.add(numeric);
      }
    }

    if (candidates.isEmpty) {
      return null;
    }

    return candidates.first;
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
    final categoryValue = _categoryController.text.trim().toLowerCase();
    if (categoryValue.isNotEmpty && categoryValue != 'food' && categoryValue != 'foods') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Il prodotto non è classificato come food. Il salvataggio è stato interrotto.'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }

    final requiredNutritionFields = [
      _energyController,
      _proteinController,
      _carbsController,
      _fatController,
    ];

    for (final field in requiredNutritionFields) {
      final validatorMessage = _validateNumericField(field.text, required: true);
      if (validatorMessage != null) {
        field.text = '';
      }
    }

    final formValid = _formKey.currentState?.validate() ?? false;
    if (!formValid) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Compila tutti i campi obbligatori.'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final provider = context.read<BarcodeScannerProvider>();
      String? imageUrl;
      if (_productImage != null) {
        final bytes = await _productImage!.readAsBytes();
        final base64 = base64Encode(bytes);
        imageUrl = 'data:image/jpeg;base64,$base64';
      }

      String? ingredientImageUrl;
      if (_ingredientsImage != null) {
        final bytes = await _ingredientsImage!.readAsBytes();
        final base64 = base64Encode(bytes);
        ingredientImageUrl = 'data:image/jpeg;base64,$base64';
      }

      String? nutritionImageUrl;
      if (_nutritionImage != null) {
        final bytes = await _nutritionImage!.readAsBytes();
        final base64 = base64Encode(bytes);
        nutritionImageUrl = 'data:image/jpeg;base64,$base64';
      }

      await provider.addProductFromSubmission(
        barcode: _barcodeController.text.trim(),
        brandName: _brandController.text.trim(),
        productName: _productNameController.text.trim(),
        category: _categoryController.text.trim(),
        productType: _productTypeController.text.trim(),
        ingredients: _ingredientsController.text.trim(),
        nutritionFacts: _buildNutrition(),
        imageUrl: imageUrl,
        ingredientImageUrl: ingredientImageUrl,
        nutritionImageUrl: nutritionImageUrl,
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
            autovalidateMode: AutovalidateMode.onUserInteraction,
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

                _ImagePickerTile(
                  label: _productImage == null ? 'Scatta/Carica foto prodotto' : 'Foto prodotto pronta',
                  file: _productImage,
                  onTap: () async {
                    final source = await _chooseImageSource();
                    if (source == null) return;
                    await _pickImage((file) => _productImage = file, source, isProductPhoto: true);
                  },
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
                  onChanged: (_) => setState(() {}),
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
                  onChanged: (_) => setState(() {}),
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
                  validator: (value) => (value == null || value.trim().isEmpty) ? 'Inserisci la categoria' : null,
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 16),

                Text('Tipo prodotto', style: AppTypography.label),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _productTypeController.text.trim().isNotEmpty ? _productTypeController.text.trim() : null,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.inventory_2),
                  ),
                  items: _productTypeOptions
                      .map(
                        (type) => DropdownMenuItem<String>(
                          value: type,
                          child: Text(type),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value != null) {
                      _productTypeController.text = value;
                    }
                  },
                  validator: (value) => (value == null || value.trim().isEmpty) ? 'Inserisci il tipo prodotto' : null,
                ),
                const SizedBox(height: 16),

                Text('Barcode', style: AppTypography.label),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _barcodeController,
                  readOnly: true,
                  decoration: const InputDecoration(
                    hintText: 'Barcode rilevato automaticamente dalla foto',
                    prefixIcon: Icon(Icons.qr_code),
                  ),
                  validator: (value) => (value == null || value.trim().isEmpty) ? 'Inserisci il barcode' : null,
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: _openBarcodeScanner,
                  icon: const Icon(Icons.qr_code_scanner),
                  label: const Text('Leggi barcode con scanner'),
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
                  onTap: () async {
                    final source = await _chooseImageSource();
                    if (source == null) return;
                    await _pickImage((file) => _ingredientsImage = file, source, isProductPhoto: false);
                  },
                ),
                const SizedBox(height: 24),

                Text('Valori nutrizionali', style: AppTypography.headline3),
                const SizedBox(height: 8),
                _ImagePickerTile(
                  label: _nutritionImage == null ? 'Scatta/Carica foto valori nutrizionali' : 'Foto valori nutrizionali pronta',
                  file: _nutritionImage,
                  onTap: () async {
                    final source = await _chooseImageSource();
                    if (source == null) return;
                    await _pickImage((file) => _nutritionImage = file, source);
                  },
                ),
                const SizedBox(height: 12),
                Text(
                  'Inserisci manualmente i valori numerici richiesti per 100 g di prodotto. Sodio e fibre sono opzionali.',
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
