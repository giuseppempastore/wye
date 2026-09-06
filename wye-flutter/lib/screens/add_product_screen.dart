import 'dart:io';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';

import '../config/mobile_upload_config.dart';
import '../models/capture_upload_models.dart';
import '../providers/app_providers.dart';
import '../providers/capture_upload_controller.dart';
import '../services/photo_field_mapper.dart';
import '../services/photo_capture_recovery_service.dart';
import '../services/product_barcode_validator.dart';
import '../theme/app_theme.dart';
import '../widgets/dev_mobile_upload_widgets.dart';

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
  String _imageFlowStatus = '';
  String? _photoReviewMessage;
  bool _ingredientsNeedConfirmation = false;
  bool _ingredientsConfirmed = false;
  bool _nutritionNeedsConfirmation = false;
  bool _nutritionConfirmed = false;
  int? _savedProductId;
  String? _savedProductBarcode;

  final ImagePicker _picker = ImagePicker();
  final PhotoFieldMapper _photoFieldMapper = const PhotoFieldMapper();
  final ProductBarcodeValidator _barcodeValidator =
      const ProductBarcodeValidator();
  final PhotoCaptureRecoveryService _photoRecovery =
      PhotoCaptureRecoveryService.shared;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _recoverPhoto());
  }

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
    required ProductPhotoPurpose purpose,
  }) async {
    try {
      await _photoRecovery.begin(purpose);
      setState(() {
        _isProcessingImage = true;
        _imageFlowStatus = source == ImageSource.camera
            ? 'Apertura fotocamera...'
            : 'Apertura galleria...';
        _photoReviewMessage = null;
      });
      // Paint the transition surface before Android opens a native activity.
      // When camera returns, the user sees this state instead of the form.
      await WidgetsBinding.instance.endOfFrame;

      final pickedFile = await _picker.pickImage(
        source: source,
        imageQuality: 82,
        maxWidth: 2048,
        maxHeight: 2048,
        requestFullMetadata: false,
      );
      if (pickedFile == null) return;
      await _photoRecovery.markCaptured(pickedFile);
      await _processPhoto(pickedFile, setter: setter, purpose: purpose);
    } catch (error) {
      debugPrint('Photo flow failed: ${error.runtimeType}');
    } finally {
      await _photoRecovery.clearPending();
      if (mounted) {
        setState(() {
          _isProcessingImage = false;
          _imageFlowStatus = '';
        });
      }
    }
  }

  Future<void> _recoverPhoto() async {
    final recovered = _photoRecovery.takeRecovered();
    if (recovered == null || !mounted) return;
    setState(() {
      _isProcessingImage = true;
      _imageFlowStatus = 'Foto recuperata. Apertura editor immagine...';
      _photoReviewMessage = null;
    });
    try {
      await _processPhoto(
        recovered.file,
        setter: (file) => _setPhotoForPurpose(recovered.purpose, file),
        purpose: recovered.purpose,
      );
      if (mounted) {
        setState(() {
          _photoReviewMessage =
              'Foto recuperata dopo il riavvio Android. Controlla il risultato prima di salvare.';
        });
      }
    } on Object catch (error) {
      debugPrint('Recovered photo flow failed: ${error.runtimeType}');
    } finally {
      await _photoRecovery.clearPending();
      if (mounted) {
        setState(() {
          _isProcessingImage = false;
          _imageFlowStatus = '';
        });
      }
    }
  }

  void _setPhotoForPurpose(ProductPhotoPurpose purpose, XFile? file) {
    switch (purpose) {
      case ProductPhotoPurpose.productFront:
        _productImage = file;
      case ProductPhotoPurpose.ingredients:
        _ingredientsImage = file;
      case ProductPhotoPurpose.nutrition:
        _nutritionImage = file;
      case ProductPhotoPurpose.other:
      case ProductPhotoPurpose.unknown:
        return;
    }
  }

  Future<void> _processPhoto(
    XFile pickedFile, {
    required void Function(XFile?) setter,
    required ProductPhotoPurpose purpose,
  }) async {
    if (mounted) {
      setState(() => _imageFlowStatus = 'Apertura editor immagine...');
    }
    final croppedFile = await _cropImage(pickedFile);
    final finalFile = croppedFile == null ? pickedFile : croppedFile;
    setter(finalFile);
    if (!_photoFieldMapper.shouldExtractText(purpose)) {
      if (mounted) {
        setState(() {
          _photoReviewMessage =
              'Foto frontale pronta. È solo rappresentativa: non compila i campi e non avvia AI.';
        });
      }
      return;
    }
    if (mounted) {
      setState(() => _imageFlowStatus = 'Lettura del testo visibile...');
    }
    await _mapTextFromPhoto(finalFile, purpose: purpose);
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
      debugPrint('Image cropper failed: ${error.runtimeType}');
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
                    final detected = capture.barcodes.first.rawValue;
                    final validation =
                        _barcodeValidator.validate(detected ?? '');
                    debugPrint(validation.safeLog);
                    if (validation.isValid) {
                      scannerController.dispose();
                      Navigator.of(context).pop(validation.value);
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

  Future<void> _mapTextFromPhoto(
    XFile file, {
    required ProductPhotoPurpose purpose,
  }) async {
    final image = InputImage.fromFilePath(file.path);
    final recognizer = TextRecognizer();
    try {
      final recognizedText = await recognizer.processImage(image);
      final rawText = recognizedText.text.trim();

      final mapping = _photoFieldMapper.map(rawText, purpose);
      if (purpose == ProductPhotoPurpose.ingredients) {
        if (mapping.ingredientListText case final value?) {
          _ingredientsController.text = value;
          _ingredientsNeedConfirmation = true;
          _ingredientsConfirmed = false;
        }
      } else if (purpose == ProductPhotoPurpose.nutrition) {
        final controllers = <String, TextEditingController>{
          'energy_kcal': _energyController,
          'protein_g': _proteinController,
          'carbs_g': _carbsController,
          'sugar_g': _sugarController,
          'fat_g': _fatController,
          'saturated_fat_g': _saturatedFatController,
          'sodium_mg': _sodiumController,
          'fiber_g': _fiberController,
        };
        for (final entry in controllers.entries) {
          final value = mapping.nutrition[entry.key];
          if (value != null) {
            entry.value.text = value.toString();
            _nutritionNeedsConfirmation = true;
            _nutritionConfirmed = false;
          }
        }
      }

      final hasData = switch (purpose) {
        ProductPhotoPurpose.productFront ||
        ProductPhotoPurpose.other ||
        ProductPhotoPurpose.unknown =>
          false,
        ProductPhotoPurpose.ingredients => mapping.hasIngredients,
        ProductPhotoPurpose.nutrition => mapping.hasNutrition,
      };
      final successMessage = switch (purpose) {
        ProductPhotoPurpose.productFront ||
        ProductPhotoPurpose.other ||
        ProductPhotoPurpose.unknown =>
          'Nessun campo compilato.',
        ProductPhotoPurpose.ingredients =>
          'Lista ingredienti rilevata. Controlla il testo prima di salvare.',
        ProductPhotoPurpose.nutrition =>
          'Valori nutrizionali rilevati. Controllali prima di salvare.',
      };
      final emptyMessage = switch (purpose) {
        ProductPhotoPurpose.productFront ||
        ProductPhotoPurpose.other ||
        ProductPhotoPurpose.unknown =>
          'Classifica manualmente la foto; nessun campo e stato modificato.',
        ProductPhotoPurpose.ingredients =>
          'Ingredienti da verificare: il campo resta vuoto.',
        ProductPhotoPurpose.nutrition =>
          'Valori nutrizionali da verificare: i campi restano vuoti.',
      };
      final message = hasData ? successMessage : emptyMessage;
      if (mounted) {
        setState(() => _photoReviewMessage = message);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(message), backgroundColor: AppColors.primary),
        );
      }
    } catch (error) {
      debugPrint('Local OCR mapping failed: ${error.runtimeType}');
      if (mounted) {
        const message =
            'Testo non leggibile con sufficiente sicurezza: nessun campo e stato modificato.';
        setState(() => _photoReviewMessage = message);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(message),
            backgroundColor: AppColors.riskHigh,
          ),
        );
      }
    } finally {
      await recognizer.close();
    }
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
    final barcodeValidation =
        _barcodeValidator.validate(_barcodeController.text);
    debugPrint(barcodeValidation.safeLog);
    if (!barcodeValidation.isValid) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Barcode non valido: usa EAN-8, UPC-A, EAN-13 o GTIN-14 con checksum corretto.',
          ),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }
    _barcodeController.text = barcodeValidation.value!;
    if ((_ingredientsNeedConfirmation && !_ingredientsConfirmed) ||
        (_nutritionNeedsConfirmation && !_nutritionConfirmed)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content:
              Text('Conferma o correggi i dati OCR segnati Da verificare.'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }
    final categoryValue = _categoryController.text.trim().toLowerCase();
    if (categoryValue.isNotEmpty &&
        categoryValue != 'food' &&
        categoryValue != 'foods') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
              'Il prodotto non è classificato come food. Il salvataggio è stato interrotto.'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }

    final nutritionFields = [
      _energyController,
      _proteinController,
      _carbsController,
      _fatController,
    ];

    for (final field in nutritionFields) {
      final validatorMessage = _validateNumericField(field.text);
      if (validatorMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Correggi i valori nutrizionali non numerici oppure lasciali vuoti.',
            ),
            backgroundColor: AppColors.riskHigh,
          ),
        );
        return;
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
      final captureController = context.read<CaptureUploadController>();
      final hasImages = _productImage != null ||
          _ingredientsImage != null ||
          _nutritionImage != null;
      final canUploadImages = context.read<MobileUploadConfig>().enabled &&
          captureController.tokenState == DevMobileTokenState.present;
      if (hasImages && !canUploadImages) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'Per salvare le foto imposta prima il token mobile temporaneo nelle Impostazioni.',
              ),
              backgroundColor: AppColors.riskHigh,
            ),
          );
        }
        return;
      }

      await provider.addProductFromSubmission(
        barcode: _barcodeController.text.trim(),
        brandName: _brandController.text.trim(),
        productName: _productNameController.text.trim(),
        category: _categoryController.text.trim(),
        productType: _productTypeController.text.trim(),
        ingredients: _ingredientsController.text.trim(),
        nutritionFacts: _buildNutrition(),
      );

      String? photoUploadError;
      if (provider.error == null && hasImages) {
        final product = provider.currentProduct;
        if (product?.productId == null) {
          photoUploadError = 'product_id_missing';
        } else {
          final savedProduct = product!;
          final photos = <(XFile, CaptureImagePurpose)>[
            if (_productImage != null)
              (_productImage!, CaptureImagePurpose.productFront),
            if (_ingredientsImage != null)
              (_ingredientsImage!, CaptureImagePurpose.ingredients),
            if (_nutritionImage != null)
              (_nutritionImage!, CaptureImagePurpose.nutrition),
          ];
          for (final photo in photos) {
            captureController.reset();
            captureController.selectImage(
              productIdentity: ProductIdentity(
                productId: savedProduct.productId!,
                barcode: savedProduct.barcode,
              ),
              purpose: photo.$2,
              bytes: await photo.$1.readAsBytes(),
            );
            await captureController.prepareMetadata();
            await captureController.upload();
            final completed = captureController.state.step ==
                    UploadFlowStep.uploadedAssociated ||
                captureController.state.step ==
                    UploadFlowStep.extractionDeferred;
            if (!completed) {
              photoUploadError = captureController.state.errorCode ??
                  'photo_upload_incomplete';
              break;
            }
          }
          if (photoUploadError == null) {
            await provider.scanBarcode(savedProduct.barcode);
          }
        }
      }

      if (mounted) {
        final message = provider.error == null && photoUploadError == null
            ? 'Prodotto e foto salvati correttamente.'
            : provider.error == null
                ? 'Prodotto salvato; foto da riprovare ($photoUploadError).'
                : provider.error ?? 'Errore durante il salvataggio';

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(message),
            backgroundColor:
                provider.error == null ? AppColors.success : AppColors.riskHigh,
          ),
        );

        if (provider.error == null) {
          setState(() {
            _savedProductId = provider.currentProduct?.productId;
            _savedProductBarcode = provider.currentProduct?.barcode;
          });
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
    final mobileUploadEnabled = context.watch<MobileUploadConfig>().enabled;
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
      body: Stack(
        children: [
          SafeArea(
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
                        border: Border.all(
                            color: AppColors.primary.withOpacity(0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.camera_alt_outlined,
                              color: AppColors.primary),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'Ogni foto compila solo la propria sezione. Se il testo non e abbastanza chiaro, i campi restano vuoti e vanno verificati.',
                              style: AppTypography.bodyMedium,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                    _ImagePickerTile(
                      label: _productImage == null
                          ? 'Scatta/Carica foto prodotto'
                          : 'Foto prodotto pronta',
                      file: _productImage,
                      onTap: () async {
                        final source = await _chooseImageSource();
                        if (source == null) return;
                        await _pickImage(
                          (file) => _productImage = file,
                          source,
                          purpose: ProductPhotoPurpose.productFront,
                        );
                      },
                    ),
                    if (_photoReviewMessage != null) ...[
                      const SizedBox(height: 12),
                      Semantics(
                        liveRegion: true,
                        child: Container(
                          key: const ValueKey('photo-review-status'),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withOpacity(0.08),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: AppColors.primary.withOpacity(0.3),
                            ),
                          ),
                          child: Text(
                            _photoReviewMessage!,
                            style: AppTypography.bodySmall,
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
                    Text('Brand', style: AppTypography.label),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _brandController,
                      decoration: const InputDecoration(
                        hintText: 'Es: Bio Natura',
                        prefixIcon: Icon(Icons.business),
                      ),
                      validator: (value) =>
                          (value == null || value.trim().isEmpty)
                              ? 'Inserisci il brand'
                              : null,
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
                      validator: (value) =>
                          (value == null || value.trim().isEmpty)
                              ? 'Inserisci il nome del prodotto'
                              : null,
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
                      validator: (value) =>
                          (value == null || value.trim().isEmpty)
                              ? 'Inserisci la categoria'
                              : null,
                      onChanged: (_) => setState(() {}),
                    ),
                    const SizedBox(height: 16),
                    Text('Tipo prodotto', style: AppTypography.label),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      value: _productTypeController.text.trim().isNotEmpty
                          ? _productTypeController.text.trim()
                          : null,
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
                      validator: (value) =>
                          (value == null || value.trim().isEmpty)
                              ? 'Inserisci il tipo prodotto'
                              : null,
                    ),
                    const SizedBox(height: 16),
                    Text('Barcode', style: AppTypography.label),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _barcodeController,
                      readOnly: true,
                      decoration: const InputDecoration(
                        hintText: 'Leggi il barcode con lo scanner',
                        prefixIcon: Icon(Icons.qr_code),
                      ),
                      validator: (value) =>
                          _barcodeValidator.validate(value ?? '').isValid
                              ? null
                              : 'Barcode non valido',
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
                        hintText:
                            'Gli ingredienti vengono precompilati da foto e possono essere corretti manualmente.',
                        prefixIcon: Icon(Icons.list_alt),
                      ),
                      onChanged: (_) {
                        if (_ingredientsNeedConfirmation) {
                          setState(() => _ingredientsConfirmed = false);
                        }
                      },
                    ),
                    if (_ingredientsNeedConfirmation)
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Chip(label: Text('Da verificare')),
                          CheckboxListTile(
                            key: const ValueKey(
                                'ingredients-review-confirmation'),
                            contentPadding: EdgeInsets.zero,
                            value: _ingredientsConfirmed,
                            title: const Text(
                                'Ho corretto o rimosso i dati OCR errati'),
                            subtitle: const Text(
                              'La conferma utente non equivale a verifica scientifica.',
                            ),
                            onChanged: (value) => setState(
                              () => _ingredientsConfirmed = value ?? false,
                            ),
                          ),
                        ],
                      ),
                    const SizedBox(height: 8),
                    _ImagePickerTile(
                      label: _ingredientsImage == null
                          ? 'Scatta/Carica foto ingredienti'
                          : 'Foto ingredienti pronta',
                      file: _ingredientsImage,
                      onTap: () async {
                        final source = await _chooseImageSource();
                        if (source == null) return;
                        await _pickImage(
                          (file) => _ingredientsImage = file,
                          source,
                          purpose: ProductPhotoPurpose.ingredients,
                        );
                      },
                    ),
                    const SizedBox(height: 24),
                    Text('Valori nutrizionali', style: AppTypography.headline3),
                    const SizedBox(height: 8),
                    _ImagePickerTile(
                      label: _nutritionImage == null
                          ? 'Scatta/Carica foto valori nutrizionali'
                          : 'Foto valori nutrizionali pronta',
                      file: _nutritionImage,
                      onTap: () async {
                        final source = await _chooseImageSource();
                        if (source == null) return;
                        await _pickImage(
                          (file) => _nutritionImage = file,
                          source,
                          purpose: ProductPhotoPurpose.nutrition,
                        );
                      },
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Inserisci manualmente i valori numerici richiesti per 100 g di prodotto. Sodio e fibre sono opzionali.',
                      style: AppTypography.bodySmall,
                    ),
                    if (_nutritionNeedsConfirmation)
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Chip(label: Text('Da verificare')),
                          CheckboxListTile(
                            key:
                                const ValueKey('nutrition-review-confirmation'),
                            contentPadding: EdgeInsets.zero,
                            value: _nutritionConfirmed,
                            title: const Text(
                                'Ho controllato valori e unità dei dati OCR'),
                            subtitle: const Text(
                              'I dati restano non verificati scientificamente.',
                            ),
                            onChanged: (value) => setState(
                              () => _nutritionConfirmed = value ?? false,
                            ),
                          ),
                        ],
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
                        _NumberField(
                            controller: _sugarController, label: 'Zuccheri g'),
                        _NumberField(
                          controller: _fatController,
                          label: 'Grassi g',
                        ),
                        _NumberField(
                            controller: _saturatedFatController,
                            label: 'Grassi saturi g'),
                        _NumberField(
                            controller: _sodiumController, label: 'Sodio mg'),
                        _NumberField(
                            controller: _fiberController, label: 'Fibre g'),
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
                    if (mobileUploadEnabled) ...[
                      const DevMobileCaptureUploadPanel(),
                      const SizedBox(height: 24),
                    ],
                    ElevatedButton.icon(
                      onPressed:
                          _isSubmitting || _isProcessingImage ? null : _submit,
                      icon: _isSubmitting
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.save_alt),
                      label: Text(_isSubmitting
                          ? 'Salvataggio...'
                          : 'Salva prodotto nel database'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                    if (_savedProductId != null) ...[
                      const SizedBox(height: 16),
                      Card(
                        key: const ValueKey('product-save-result'),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Prodotto salvato',
                                  style: AppTypography.headline3),
                              const SizedBox(height: 8),
                              Text('Product ID: $_savedProductId'),
                              const SizedBox(height: 4),
                              const Text('Score: non ancora calcolato'),
                              const SizedBox(height: 4),
                              const Text('Origine: inserimento da foto'),
                              if (_savedProductBarcode != null) ...[
                                const SizedBox(height: 12),
                                OutlinedButton.icon(
                                  key: const ValueKey('open-saved-product'),
                                  onPressed: () => context.go(
                                    '/product/$_savedProductBarcode',
                                  ),
                                  icon: const Icon(Icons.open_in_new),
                                  label: const Text('Apri dettaglio prodotto'),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ],
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
          if (_isProcessingImage)
            Positioned.fill(
              child: AbsorbPointer(
                child: ColoredBox(
                  color: Colors.black54,
                  child: Center(
                    child: Card(
                      key: const ValueKey('photo-flow-overlay'),
                      margin: const EdgeInsets.all(32),
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const CircularProgressIndicator(),
                            const SizedBox(height: 16),
                            Text(
                              _imageFlowStatus,
                              textAlign: TextAlign.center,
                              style: AppTypography.bodyLarge,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Non tornare indietro: il prossimo passaggio si apre automaticamente.',
                              textAlign: TextAlign.center,
                              style: AppTypography.bodySmall,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'Storico'),
          BottomNavigationBarItem(
              icon: Icon(Icons.settings), label: 'Impostazioni'),
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
            if (file == null)
              const Icon(Icons.add_a_photo_outlined, color: AppColors.primary)
            else
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.file(
                  File(file!.path),
                  key: const ValueKey('captured-image-preview'),
                  width: 64,
                  height: 64,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const SizedBox(
                    width: 64,
                    height: 64,
                    child: Icon(Icons.check_circle, color: AppColors.primary),
                  ),
                ),
              ),
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

  const _NumberField({
    required this.controller,
    required this.label,
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
    );
  }
}
