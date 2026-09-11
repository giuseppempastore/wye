import 'dart:io';
import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';

import '../config/mobile_upload_config.dart';
import '../models/capture_upload_models.dart';
import '../models/product_taxonomy.dart';
import '../models/product_acquisition_draft.dart';
import '../providers/app_providers.dart';
import '../providers/capture_upload_controller.dart';
import '../services/database_service.dart';
import '../services/device_camera_availability.dart';
import '../services/api_client.dart';
import '../services/language_detector.dart';
import '../services/photo_field_mapper.dart';
import '../services/photo_processing_policy.dart';
import '../services/photo_capture_recovery_service.dart';
import '../services/product_barcode_validator.dart';
import '../services/technical_session_bootstrapper.dart';
import '../theme/app_theme.dart';

class AddProductScreen extends StatefulWidget {
  final DatabaseService? databaseService;

  const AddProductScreen({super.key, this.databaseService});

  @override
  State<AddProductScreen> createState() => _AddProductScreenState();
}

class _AddProductScreenState extends State<AddProductScreen>
    with WidgetsBindingObserver {
  final _formKey = GlobalKey<FormState>();
  final _barcodeController = TextEditingController();
  final _brandController = TextEditingController();
  final _productNameController = TextEditingController();
  final _categoryController = TextEditingController();
  final _productTypeController = TextEditingController();
  final _ingredientsController = TextEditingController();
  final _energyKjController = TextEditingController();
  final _energyController = TextEditingController();
  final _proteinController = TextEditingController();
  final _carbsController = TextEditingController();
  final _sugarController = TextEditingController();
  final _fatController = TextEditingController();
  final _saturatedFatController = TextEditingController();
  final _sodiumController = TextEditingController();
  final _fiberController = TextEditingController();
  final _saltController = TextEditingController();

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
  bool _ingredientsUserEdited = false;
  bool _nutritionUserEdited = false;
  int? _savedProductId;
  String? _savedProductBarcode;
  Map<String, dynamic>? _ingredientExtractionPayload;
  Map<String, dynamic>? _nutritionExtractionPayload;
  String? _nutritionBasis;
  String? _barcodeLookupMessage;
  String? _ingredientRawOcr;
  String? _nutritionRawOcr;
  String? _ingredientLanguage;
  String? _nutritionLanguage;
  late ProductAcquisitionDraft _draft;
  Timer? _draftSaveDebounce;
  bool _draftReady = false;
  bool _existingProduct = false;
  int _currentStep = 0;
  final Map<String, int> _uploadedImageIds = {};
  final Map<String, String> _uploadedChecksums = {};
  final ScrollController _scrollController = ScrollController();

  final ImagePicker _picker = ImagePicker();
  final PhotoFieldMapper _photoFieldMapper = const PhotoFieldMapper();
  final ProductBarcodeValidator _barcodeValidator =
      const ProductBarcodeValidator();
  final PhotoCaptureRecoveryService _photoRecovery =
      PhotoCaptureRecoveryService.shared;
  DatabaseService? _databaseService;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _databaseService = widget.databaseService;
    final entropy = Random.secure().nextInt(1 << 32).toRadixString(16);
    _draft = ProductAcquisitionDraft(
      id: 'draft_${DateTime.now().toUtc().microsecondsSinceEpoch}_$entropy',
      updatedAt: DateTime.now().toUtc(),
    );
    for (final controller in _allControllers) {
      controller.addListener(_scheduleDraftSave);
    }
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await _restoreDraft();
      await _recoverPhoto();
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _draftSaveDebounce?.cancel();
    if (_draftReady) {
      // Hive writes are initiated before the widget disappears; no technical
      // credential is part of the serialized state.
      unawaited(_saveDraft());
    }
    _barcodeController.dispose();
    _brandController.dispose();
    _productNameController.dispose();
    _categoryController.dispose();
    _productTypeController.dispose();
    _ingredientsController.dispose();
    _energyKjController.dispose();
    _energyController.dispose();
    _proteinController.dispose();
    _carbsController.dispose();
    _sugarController.dispose();
    _fatController.dispose();
    _saturatedFatController.dispose();
    _sodiumController.dispose();
    _fiberController.dispose();
    _saltController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_draftReady &&
        (state == AppLifecycleState.inactive ||
            state == AppLifecycleState.paused ||
            state == AppLifecycleState.detached ||
            state == AppLifecycleState.hidden)) {
      unawaited(_saveDraft());
    }
  }

  List<TextEditingController> get _allControllers => [
        _barcodeController,
        _brandController,
        _productNameController,
        _categoryController,
        _productTypeController,
        _ingredientsController,
        _energyKjController,
        _energyController,
        _proteinController,
        _carbsController,
        _sugarController,
        _fatController,
        _saturatedFatController,
        _sodiumController,
        _fiberController,
        _saltController,
      ];

  Future<void> _restoreDraft() async {
    if (_databaseService == null) {
      try {
        _databaseService = context.read<DatabaseService>();
      } on ProviderNotFoundException {
        // Lightweight widget tests may intentionally omit local persistence.
      }
    }
    final stored = _databaseService?.getActiveAcquisitionDraft();
    if (stored != null && stored.status == ProductAcquisitionStatus.draft) {
      _draft = stored;
      _currentStep = stored.currentStep.clamp(0, 3);
      _barcodeController.text = stored.barcode ?? '';
      _brandController.text = stored.brand;
      _productNameController.text = stored.productName;
      _categoryController.text = stored.categoryId;
      _productTypeController.text = stored.productTypeId;
      _ingredientsController.text = stored.ingredients;
      _ingredientsUserEdited = stored.ingredientsUserEdited;
      _nutritionUserEdited = stored.nutritionUserEdited;
      final fields = <String, TextEditingController>{
        'energy_kj': _energyKjController,
        'energy_kcal': _energyController,
        'protein_g': _proteinController,
        'carbs_g': _carbsController,
        'sugar_g': _sugarController,
        'fat_g': _fatController,
        'saturated_fat_g': _saturatedFatController,
        'sodium_mg': _sodiumController,
        'fiber_g': _fiberController,
        'salt_g': _saltController,
      };
      for (final entry in fields.entries) {
        final value = stored.nutrition[entry.key];
        if (value != null) entry.value.text = value.toString();
      }
      _nutritionBasis = stored.nutritionBasis;
      _productImage = _restoredFile(stored.localImagePaths['product_front']);
      _ingredientsImage = _restoredFile(stored.localImagePaths['ingredients']);
      _nutritionImage = _restoredFile(stored.localImagePaths['nutrition']);
      _ingredientExtractionPayload = stored.labelExtractions['ingredients'];
      _nutritionExtractionPayload = stored.labelExtractions['nutrition'];
      _ingredientRawOcr = _ingredientExtractionPayload?['raw_text']?.toString();
      _nutritionRawOcr = _nutritionExtractionPayload?['raw_text']?.toString();
      _ingredientLanguage =
          _ingredientExtractionPayload?['source_language']?.toString();
      _nutritionLanguage =
          _nutritionExtractionPayload?['source_language']?.toString();
      _savedProductId = stored.productId;
      _uploadedImageIds.addAll(stored.uploadedImageIds);
      _uploadedChecksums.addAll(stored.uploadedImageChecksums);
      _barcodeLookupMessage = stored.barcodeLookupCompleted
          ? 'Barcode acquisito dallo scanner e bozza ripristinata.'
          : null;
    }
    if (!mounted) return;
    setState(() => _draftReady = true);
    await _saveDraft();
  }

  XFile? _restoredFile(String? path) {
    if (path == null || !File(path).existsSync()) return null;
    return XFile(path);
  }

  void _scheduleDraftSave() {
    if (!_draftReady) return;
    _draftSaveDebounce?.cancel();
    _draftSaveDebounce = Timer(
      const Duration(milliseconds: 250),
      () => unawaited(_saveDraft()),
    );
  }

  Future<void> _saveDraft({
    ProductAcquisitionStatus? status,
    String? acquisitionId,
    String? errorCode,
  }) async {
    if (!_draftReady) return;
    final imagePaths = <String, String>{
      if (_productImage != null) 'product_front': _productImage!.path,
      if (_ingredientsImage != null) 'ingredients': _ingredientsImage!.path,
      if (_nutritionImage != null) 'nutrition': _nutritionImage!.path,
    };
    _draft = _draft.copyWith(
      currentStep: _currentStep,
      status: status,
      barcode: _barcodeController.text.trim().isEmpty
          ? null
          : _barcodeController.text.trim(),
      barcodeLookupCompleted: _barcodeController.text.trim().isNotEmpty,
      productId: _savedProductId,
      brand: _brandController.text,
      productName: _productNameController.text,
      categoryId: _categoryController.text,
      productTypeId: _productTypeController.text,
      ingredients: _ingredientsController.text,
      ingredientsUserEdited: _ingredientsUserEdited,
      nutrition: _buildNutrition().map(
        (key, value) => MapEntry(key, (value as num).toDouble()),
      ),
      nutritionUserEdited: _nutritionUserEdited,
      nutritionBasis: _nutritionBasis,
      localImagePaths: imagePaths,
      uploadedImageIds: _uploadedImageIds,
      uploadedImageChecksums: _uploadedChecksums,
      labelExtractions: {
        if (_ingredientExtractionPayload != null)
          'ingredients': _ingredientExtractionPayload!,
        if (_nutritionExtractionPayload != null)
          'nutrition': _nutritionExtractionPayload!,
      },
      recoverableErrorCode: errorCode,
      clearRecoverableError: errorCode == null,
      acquisitionId: acquisitionId,
    );
    await _databaseService?.saveAcquisitionDraft(_draft);
  }

  String _documentType(ProductPhotoPurpose purpose) => switch (purpose) {
        ProductPhotoPurpose.productFront => 'product_front',
        ProductPhotoPurpose.ingredients => 'ingredients',
        ProductPhotoPurpose.nutrition => 'nutrition',
        _ => 'other',
      };

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
        // OCR photos retain more detail; the product photo is resized by the
        // cropper only after the user confirms the crop.
        imageQuality: purpose == ProductPhotoPurpose.productFront
            ? 100
            : PhotoProcessingPolicy.documentJpegQuality,
        maxWidth: purpose == ProductPhotoPurpose.productFront
            ? null
            : PhotoProcessingPolicy.documentMaxDimension.toDouble(),
        maxHeight: purpose == ProductPhotoPurpose.productFront
            ? null
            : PhotoProcessingPolicy.documentMaxDimension.toDouble(),
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
    XFile finalFile = pickedFile;
    if (PhotoProcessingPolicy.requiresManualCrop(purpose)) {
      if (mounted) {
        setState(() => _imageFlowStatus = 'Ritaglia la foto prodotto...');
      }
      final croppedFile = await _cropImage(pickedFile);
      if (croppedFile == null) {
        if (mounted) {
          setState(() => _photoReviewMessage =
              'Ritaglio annullato: la foto precedente non è stata modificata.');
        }
        return;
      }
      finalFile = croppedFile;
    } else {
      if (mounted) {
        setState(() => _imageFlowStatus = 'Controllo qualità foto...');
      }
      final assessment =
          await const OnDevicePhotoQualityService().assess(finalFile.path);
      if (!assessment.ok) {
        final keep = await _confirmLowQualityPhoto(assessment.userMessage);
        if (!keep) return;
      }
    }
    try {
      final retainedPath = await _databaseService?.retainDraftImage(
        draftId: _draft.id,
        documentType: _documentType(purpose),
        sourcePath: finalFile.path,
      );
      if (retainedPath != null) finalFile = XFile(retainedPath);
    } on Object catch (error) {
      debugPrint('Draft photo retention failed: ${error.runtimeType}');
    }
    setter(finalFile);
    await _saveDraft();
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

  Future<bool> _confirmLowQualityPhoto(String issue) async {
    if (!mounted) return false;
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Meglio rifare la foto'),
            content: Text(
              'Il controllo sul dispositivo rileva: $issue. Una nuova foto '
              'ben illuminata evita letture sbagliate. Nessuna analisi AI è stata usata.',
            ),
            actions: [
              FilledButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Rifai foto'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Usa comunque · Da verificare'),
              ),
            ],
          ),
        ) ??
        false;
  }

  Future<XFile?> _cropImage(XFile file) async {
    try {
      final croppedFile = await ImageCropper().cropImage(
        sourcePath: file.path,
        maxWidth: PhotoProcessingPolicy.productMaxDimension,
        maxHeight: PhotoProcessingPolicy.productMaxDimension,
        compressQuality: PhotoProcessingPolicy.productJpegQuality,
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
    if (_barcodeController.text.isNotEmpty && _draft.hasUserData) {
      final replace = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Scansionare un altro barcode?'),
          content: const Text(
            'La nuova scansione cambierà l’identità della bozza. Foto e dati '
            'resteranno salvati, ma dovrai ricontrollarli.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Mantieni attuale'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Scansiona di nuovo'),
            ),
          ],
        ),
      );
      if (replace != true) return;
      _existingProduct = false;
      _savedProductId = null;
    }
    if (!mounted) return;
    final hasCamera = await const DeviceCameraAvailability().hasUsableCamera();
    if (!mounted) return;
    if (!hasCamera) {
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Fotocamera non disponibile'),
          content: const Text(
            'Questo emulatore non ha una camera virtuale configurata. '
            'Abilitala nelle impostazioni dell’AVD oppure usa un telefono.',
          ),
          actions: [
            FilledButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Ho capito'),
            ),
          ],
        ),
      );
      return;
    }
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
      await _lookupBarcode();
      await _saveDraft();
    }
  }

  Future<void> _lookupBarcode() async {
    final validation = _barcodeValidator.validate(_barcodeController.text);
    debugPrint(validation.safeLog);
    if (!validation.isValid) {
      if (mounted) {
        setState(() => _barcodeLookupMessage =
            'Barcode non valido: controlla lunghezza e cifra di controllo.');
      }
      return;
    }
    final provider = context.read<BarcodeScannerProvider>();
    await provider.scanBarcode(validation.value!);
    if (!mounted) return;
    final product = provider.currentProduct;
    if (product == null) {
      provider.clearError();
      setState(() {
        _existingProduct = false;
        _barcodeController.text = validation.value!;
        _barcodeLookupMessage =
            'Nuovo barcode: completa foto e dati per creare il prodotto da validare.';
      });
      return;
    }
    setState(() {
      _existingProduct = true;
      _barcodeController.text = validation.value!;
      _brandController.text = product.brand;
      _productNameController.text = product.productName;
      _categoryController.text = productCategoryOptions.any(
        (option) => option.id == product.category,
      )
          ? product.category
          : 'other';
      _productTypeController.text = productTypeOptions.any(
        (option) => option.id == product.productType,
      )
          ? product.productType!
          : 'other';
      _barcodeLookupMessage = product.dataVerified
          ? 'Prodotto esistente verificato: i dati non verranno sovrascritti.'
          : 'Prodotto esistente recuperato: la nuova acquisizione sarà collegata allo stesso Product ID.';
    });
    final openExisting = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Prodotto già presente'),
        content: const Text(
          'Questo barcode appartiene a un prodotto esistente. Puoi aprire il '
          'dettaglio; la registrazione duplicata resta bloccata.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Resta qui'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Apri prodotto'),
          ),
        ],
      ),
    );
    if (openExisting == true && mounted) {
      context.go('/product/${validation.value}');
    }
  }

  Future<void> _mapTextFromPhoto(
    XFile file, {
    required ProductPhotoPurpose purpose,
  }) async {
    _resetExtractedFields(purpose);
    final image = InputImage.fromFilePath(file.path);
    final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
    try {
      final recognizedText = await recognizer.processImage(image);
      final rawText = recognizedText.text;
      final recognizedLanguages = recognizedText.blocks
          .expand((block) => block.recognizedLanguages)
          .where((code) => code.trim().isNotEmpty)
          .toSet();
      final mapping = _photoFieldMapper.map(
        rawText,
        purpose,
        recognizedLanguageCodes: recognizedLanguages,
      );
      if (purpose == ProductPhotoPurpose.ingredients) {
        _ingredientRawOcr = mapping.rawText;
        _ingredientLanguage = mapping.detectedLanguage;
        _ingredientExtractionPayload = mapping.rawText.isEmpty
            ? null
            : mapping.toPersistencePayload(ProductPhotoPurpose.ingredients);
        if (mapping.ingredientListText case final value?) {
          _ingredientsController.text = value;
          _ingredientsUserEdited = false;
          _ingredientsNeedConfirmation = true;
          _ingredientsConfirmed = false;
        }
      } else if (purpose == ProductPhotoPurpose.nutrition) {
        _nutritionRawOcr = mapping.rawText;
        _nutritionLanguage = mapping.detectedLanguage;
        _nutritionExtractionPayload = mapping.rawText.isEmpty
            ? null
            : mapping.toPersistencePayload(ProductPhotoPurpose.nutrition);
        _nutritionBasis = mapping.nutritionBasis;
        final controllers = <String, TextEditingController>{
          'energy_kj': _energyKjController,
          'energy_kcal': _energyController,
          'protein_g': _proteinController,
          'carbs_g': _carbsController,
          'sugar_g': _sugarController,
          'fat_g': _fatController,
          'saturated_fat_g': _saturatedFatController,
          'sodium_mg': _sodiumController,
          'fiber_g': _fiberController,
          'salt_g': _saltController,
        };
        for (final entry in controllers.entries) {
          final value = mapping.nutrition[entry.key];
          if (value != null) {
            entry.value.text = value.toString();
            _nutritionNeedsConfirmation = true;
            _nutritionConfirmed = false;
          }
        }
        _nutritionUserEdited = false;
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
      final languageLabel =
          languageDisplayNameItalian(mapping.detectedLanguage);
      final basisLabel = switch (mapping.nutritionBasis) {
        'per_100_g' => ' Base: per 100 g.',
        'per_100_ml' => ' Base: per 100 ml.',
        'per_serving' => ' Base: per porzione.',
        _ => '',
      };
      final scriptUnsupported = mapping.languageDetection.status ==
          LanguageDetectionStatus.unsupportedScript;
      final message = scriptUnsupported
          ? 'Sistema di scrittura non supportato in questa versione. I campi restano vuoti.'
          : hasData
              ? '$successMessage Lingua: $languageLabel.$basisLabel'
              : '$emptyMessage Lingua: $languageLabel.';
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

  void _resetExtractedFields(ProductPhotoPurpose purpose) {
    if (purpose == ProductPhotoPurpose.ingredients) {
      _ingredientsController.clear();
      _ingredientsNeedConfirmation = false;
      _ingredientsConfirmed = false;
      _ingredientExtractionPayload = null;
      _ingredientRawOcr = null;
      _ingredientLanguage = null;
      return;
    }
    if (purpose != ProductPhotoPurpose.nutrition) return;
    for (final controller in [
      _energyKjController,
      _energyController,
      _proteinController,
      _carbsController,
      _sugarController,
      _fatController,
      _saturatedFatController,
      _sodiumController,
      _fiberController,
      _saltController,
    ]) {
      controller.clear();
    }
    _nutritionNeedsConfirmation = false;
    _nutritionConfirmed = false;
    _nutritionExtractionPayload = null;
    _nutritionBasis = null;
    _nutritionRawOcr = null;
    _nutritionLanguage = null;
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

    addIfPresent('energy_kj', _energyKjController);
    addIfPresent('energy_kcal', _energyController);
    addIfPresent('protein_g', _proteinController);
    addIfPresent('carbs_g', _carbsController);
    addIfPresent('sugar_g', _sugarController);
    addIfPresent('fat_g', _fatController);
    addIfPresent('saturated_fat_g', _saturatedFatController);
    addIfPresent('sodium_mg', _sodiumController);
    addIfPresent('fiber_g', _fiberController);
    addIfPresent('salt_g', _saltController);

    return nutrition;
  }

  List<String> get _ingredientItems => _ingredientsController.text
      .split(RegExp(r'[,;\n]+'))
      .map((value) => value.trim())
      .where((value) => value.isNotEmpty)
      .toList(growable: false);

  void _replaceIngredientItems(List<String> items) {
    setState(() {
      _ingredientsController.text = items.join(', ');
      _ingredientsUserEdited = true;
      _ingredientsConfirmed = false;
    });
    _scheduleDraftSave();
  }

  Future<String?> _editIngredientDialog({String initialValue = ''}) async {
    final controller = TextEditingController(text: initialValue);
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(initialValue.isEmpty
            ? 'Aggiungi ingrediente'
            : 'Modifica ingrediente'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLength: 160,
          decoration: const InputDecoration(labelText: 'Ingrediente'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annulla'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('Salva'),
          ),
        ],
      ),
    );
    // The dialog route may still be completing its exit animation when the
    // future resolves. Dispose on the following frame to avoid rebuilding a
    // TextField with an already-disposed controller.
    WidgetsBinding.instance.addPostFrameCallback((_) => controller.dispose());
    return result;
  }

  Future<void> _addIngredient() async {
    final value = await _editIngredientDialog();
    if (value == null || value.isEmpty) return;
    _replaceIngredientItems([..._ingredientItems, value]);
  }

  Future<void> _editIngredient(int index) async {
    final items = [..._ingredientItems];
    if (index < 0 || index >= items.length) return;
    final value = await _editIngredientDialog(initialValue: items[index]);
    if (value == null || value.isEmpty) return;
    items[index] = value;
    _replaceIngredientItems(items);
  }

  void _removeIngredient(int index) {
    final items = [..._ingredientItems];
    if (index < 0 || index >= items.length) return;
    items.removeAt(index);
    _replaceIngredientItems(items);
  }

  void _markNutritionEdited(String _) {
    setState(() {
      _nutritionUserEdited = true;
      _nutritionConfirmed = false;
    });
  }

  Future<void> _moveToStep(int step) async {
    setState(() => _currentStep = step.clamp(0, 3));
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          0,
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOut,
        );
      }
    });
    await _saveDraft();
  }

  Future<void> _handleBack() async {
    if (_currentStep > 0) {
      await _moveToStep(_currentStep - 1);
      return;
    }
    await _saveDraft();
    if (!mounted) return;
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/add-product');
    }
  }

  Future<void> _saveAndExit() async {
    await _saveDraft();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Bozza salvata. Potrai riprenderla dopo.')),
    );
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/add-product');
    }
  }

  Future<void> _deleteDraft() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Eliminare la bozza?'),
        content: const Text(
          'Saranno rimossi soltanto questa bozza e i suoi file locali. '
          'L’operazione non può essere annullata.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Mantieni bozza'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Elimina bozza'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await _databaseService?.deleteAcquisitionDraft(_draft.id);
    if (!mounted) return;
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/add-product');
    }
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
    final identityComplete = _brandController.text.trim().isNotEmpty &&
        _productNameController.text.trim().isNotEmpty &&
        _categoryController.text.trim().isNotEmpty &&
        _productTypeController.text.trim().isNotEmpty;
    if (!identityComplete) {
      await _moveToStep(0);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Completa i dati principali del prodotto.'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }
    if (_existingProduct && _draft.productId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
              'Questo prodotto esiste già: apri il dettaglio invece di duplicarlo.'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }
    if (_productImage == null ||
        _ingredientsImage == null ||
        _nutritionImage == null) {
      final missingStep = _productImage == null
          ? 0
          : _ingredientsImage == null
              ? 1
              : 2;
      await _moveToStep(missingStep);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Servono tutte e tre le foto: prodotto, ingredienti e valori nutrizionali.',
          ),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }
    if ((_ingredientsNeedConfirmation && !_ingredientsConfirmed) ||
        (_nutritionNeedsConfirmation && !_nutritionConfirmed)) {
      await _moveToStep(
        _ingredientsNeedConfirmation && !_ingredientsConfirmed ? 1 : 2,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content:
              Text('Conferma o correggi i dati OCR segnati Da verificare.'),
          backgroundColor: AppColors.riskHigh,
        ),
      );
      return;
    }
    final nutritionFields = [
      _energyKjController,
      _energyController,
      _proteinController,
      _carbsController,
      _sugarController,
      _fatController,
      _saturatedFatController,
      _sodiumController,
      _saltController,
      _fiberController,
    ];

    for (final field in nutritionFields) {
      final validatorMessage = _validateNumericField(field.text);
      if (validatorMessage != null) {
        await _moveToStep(2);
        if (!mounted) return;
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
      final apiClient = context.read<ApiClient>();
      final hasImages = _productImage != null ||
          _ingredientsImage != null ||
          _nutritionImage != null;
      final uploadEnabled = context.read<MobileUploadConfig>().enabled;
      final canUploadImages = uploadEnabled &&
          await context.read<TechnicalSessionBootstrapper>().ensureReady();
      if (hasImages && !canUploadImages) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'Connessione sicura non disponibile. Riprova tra qualche secondo.',
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
        nutritionBasis: _nutritionBasis,
        labelExtractions: [
          if (_ingredientExtractionPayload != null)
            _ingredientExtractionPayload!,
          if (_nutritionExtractionPayload != null) _nutritionExtractionPayload!,
        ],
      );

      String? photoUploadError;
      if (provider.error == null && hasImages) {
        final product = provider.currentProduct;
        if (product?.productId == null) {
          photoUploadError = 'product_id_missing';
        } else if (product!.dataVerified) {
          photoUploadError = 'verified_product_requires_admin_review';
        } else {
          final savedProduct = product;
          final photos = <(XFile, CaptureImagePurpose)>[
            if (_productImage != null)
              (_productImage!, CaptureImagePurpose.productFront),
            if (_ingredientsImage != null)
              (_ingredientsImage!, CaptureImagePurpose.ingredients),
            if (_nutritionImage != null)
              (_nutritionImage!, CaptureImagePurpose.nutrition),
          ];
          for (final photo in photos) {
            final documentType = switch (photo.$2) {
              CaptureImagePurpose.productFront => 'product_front',
              CaptureImagePurpose.ingredients => 'ingredients',
              CaptureImagePurpose.nutrition => 'nutrition',
              _ => 'other',
            };
            if (_uploadedImageIds.containsKey(documentType) &&
                _uploadedChecksums.containsKey(documentType)) {
              continue;
            }
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
            final imageId =
                captureController.state.productImage?.productImageId;
            final checksum = captureController.state.metadata?.sha256;
            if (imageId == null || checksum == null) {
              photoUploadError = 'photo_upload_reference_missing';
              break;
            }
            _uploadedImageIds[documentType] = imageId;
            _uploadedChecksums[documentType] = checksum;
            await _saveDraft();
          }
          if (photoUploadError == null) {
            final extractionByType = {
              'ingredients': _ingredientExtractionPayload,
              'nutrition': _nutritionExtractionPayload,
            };
            final acquisition = await apiClient.submitPublicProductAcquisition(
              productId: savedProduct.productId!,
              barcode: savedProduct.barcode,
              draftId: _draft.id,
              documents: ['product_front', 'ingredients', 'nutrition']
                  .map((documentType) => {
                        'document_type': documentType,
                        'product_image_id': _uploadedImageIds[documentType],
                        'checksum_sha256': _uploadedChecksums[documentType],
                        if (extractionByType[documentType] != null)
                          'raw_ocr':
                              extractionByType[documentType]!['raw_text'],
                        if (extractionByType[documentType] != null)
                          'source_language': extractionByType[documentType]![
                                  'source_language'] ??
                              extractionByType[documentType]![
                                  'detected_language'] ??
                              'und',
                        'structured_extraction':
                            extractionByType[documentType] ??
                                const <String, dynamic>{},
                      })
                  .toList(),
            );
            await _saveDraft(
              status: ProductAcquisitionStatusWire.parse(acquisition['status']),
              acquisitionId: acquisition['acquisition_id']?.toString(),
            );
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
          if (photoUploadError == null) {
            await _saveDraft(status: ProductAcquisitionStatus.queued);
          } else {
            await _saveDraft(errorCode: photoUploadError);
          }
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
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) unawaited(_handleBack());
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Registra nuovo prodotto'),
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            tooltip: 'Indietro',
            onPressed: _handleBack,
          ),
          actions: [
            PopupMenuButton<String>(
              key: const ValueKey('draft-actions-menu'),
              tooltip: 'Azioni bozza',
              onSelected: (action) {
                if (action == 'save') {
                  unawaited(_saveAndExit());
                } else if (action == 'delete') {
                  unawaited(_deleteDraft());
                }
              },
              itemBuilder: (context) => const [
                PopupMenuItem(
                  value: 'save',
                  child: ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(Icons.save_outlined),
                    title: Text('Salva bozza'),
                  ),
                ),
                PopupMenuItem(
                  value: 'delete',
                  child: ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(Icons.delete_outline),
                    title: Text('Elimina bozza'),
                  ),
                ),
              ],
            ),
          ],
        ),
        body: Stack(
          children: [
            SafeArea(
              child: SingleChildScrollView(
                controller: _scrollController,
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _formKey,
                  autovalidateMode: AutovalidateMode.onUserInteraction,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Passaggio ${_currentStep + 1} di 4',
                        key: const ValueKey('registration-wizard-step'),
                        style: AppTypography.label,
                      ),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(value: (_currentStep + 1) / 4),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        children: List.generate(
                          4,
                          (index) => ChoiceChip(
                            key: ValueKey('wizard-step-$index'),
                            label: Text('${index + 1}'),
                            selected: _currentStep == index,
                            showCheckmark: false,
                            onSelected: (_) => _moveToStep(index),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        switch (_currentStep) {
                          0 => 'Prodotto',
                          1 => 'Ingredienti',
                          2 => 'Valori nutrizionali',
                          _ => 'Riepilogo',
                        },
                        key: const ValueKey('registration-wizard-title'),
                        style: AppTypography.headline2,
                      ),
                      const SizedBox(height: 24),
                      if (_currentStep == 0) ...[
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                                color:
                                    AppColors.primary.withValues(alpha: 0.3)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.camera_alt_outlined,
                                  color: AppColors.primary),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'Scansiona il barcode e aggiungi la foto frontale e i dati principali del prodotto.',
                                  style: AppTypography.bodyMedium,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 24),
                        Text('1. Barcode prodotto',
                            style: AppTypography.headline3),
                        const SizedBox(height: 8),
                        TextFormField(
                          controller: _barcodeController,
                          readOnly: true,
                          enabled: false,
                          decoration: const InputDecoration(
                            hintText: 'Barcode obbligatorio: usa lo scanner',
                            prefixIcon: Icon(Icons.qr_code),
                          ),
                          validator: (value) =>
                              _barcodeValidator.validate(value ?? '').isValid
                                  ? null
                                  : 'Barcode non valido',
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: _openBarcodeScanner,
                                icon: const Icon(Icons.qr_code_scanner),
                                label: Text(_barcodeController.text.isEmpty
                                    ? 'Scansiona barcode'
                                    : 'Scansiona di nuovo'),
                              ),
                            ),
                          ],
                        ),
                        if (_barcodeLookupMessage != null) ...[
                          const SizedBox(height: 8),
                          Text(
                            _barcodeLookupMessage!,
                            key: const ValueKey('barcode-lookup-state'),
                            style: AppTypography.bodySmall,
                          ),
                        ],
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
                        DropdownButtonFormField<String>(
                          initialValue:
                              _categoryController.text.trim().isNotEmpty
                                  ? _categoryController.text.trim()
                                  : null,
                          decoration: const InputDecoration(
                            hintText: 'Seleziona una categoria',
                            prefixIcon: Icon(Icons.category),
                          ),
                          items: productCategoryOptions
                              .map(
                                (option) => DropdownMenuItem<String>(
                                  value: option.id,
                                  child: Text(option.label),
                                ),
                              )
                              .toList(),
                          onChanged: (value) {
                            if (value != null) {
                              setState(() => _categoryController.text = value);
                            }
                          },
                          validator: (value) =>
                              (value == null || value.trim().isEmpty)
                                  ? 'Seleziona la categoria'
                                  : null,
                        ),
                        const SizedBox(height: 16),
                        Text('Tipo prodotto', style: AppTypography.label),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          initialValue:
                              _productTypeController.text.trim().isNotEmpty
                                  ? _productTypeController.text.trim()
                                  : null,
                          decoration: const InputDecoration(
                            prefixIcon: Icon(Icons.inventory_2),
                          ),
                          items: productTypeOptions
                              .map(
                                (option) => DropdownMenuItem<String>(
                                  value: option.id,
                                  child: Text(option.label),
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
                                  ? 'Seleziona il tipo prodotto'
                                  : null,
                        ),
                        const SizedBox(height: 24),
                      ],
                      if (_currentStep == 1) ...[
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: AppColors.primary.withValues(alpha: 0.3),
                            ),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.document_scanner_outlined,
                                color: AppColors.primary,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'Fotografa soltanto la lista ingredienti. Se il testo non è chiaro, il campo resta vuoto.',
                                  style: AppTypography.bodyMedium,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 24),
                        const Align(
                          alignment: Alignment.centerLeft,
                          child: Chip(
                            key: ValueKey('product-validation-pending'),
                            avatar: Icon(Icons.fact_check_outlined, size: 18),
                            label: Text('Dati etichetta non verificati'),
                          ),
                        ),
                        const SizedBox(height: 8),
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
                            setState(() {
                              _ingredientsUserEdited = true;
                              _ingredientsConfirmed = false;
                            });
                          },
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            Chip(
                              key: const ValueKey('ingredients-provenance'),
                              avatar: Icon(
                                _ingredientsUserEdited
                                    ? Icons.edit_outlined
                                    : Icons.document_scanner_outlined,
                                size: 18,
                              ),
                              label: Text(_ingredientsUserEdited
                                  ? 'Corretto dall’utente · Da validare'
                                  : _ingredientRawOcr != null
                                      ? 'Estratto dalla foto · Da verificare'
                                      : 'Inserimento manuale · Da validare'),
                            ),
                            const Spacer(),
                            TextButton.icon(
                              key: const ValueKey('ingredient-add'),
                              onPressed: _addIngredient,
                              icon: const Icon(Icons.add),
                              label: const Text('Aggiungi'),
                            ),
                          ],
                        ),
                        if (_ingredientItems.isNotEmpty)
                          Wrap(
                            key: const ValueKey('ingredient-items'),
                            spacing: 8,
                            runSpacing: 6,
                            children: [
                              for (var index = 0;
                                  index < _ingredientItems.length;
                                  index++)
                                InputChip(
                                  key: ValueKey('ingredient-item-$index'),
                                  label: Text(_ingredientItems[index]),
                                  onPressed: () => _editIngredient(index),
                                  onDeleted: () => _removeIngredient(index),
                                  deleteButtonTooltipMessage:
                                      'Elimina ingrediente',
                                ),
                            ],
                          ),
                        if (_ingredientRawOcr case final rawText?)
                          _OcrOriginalTextPanel(
                            key: const ValueKey('ingredients-original-ocr'),
                            languageCode: _ingredientLanguage ?? 'und',
                            rawText: rawText,
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
                      ],
                      if (_currentStep == 2) ...[
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: AppColors.primary.withValues(alpha: 0.3),
                            ),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.table_chart_outlined,
                                color: AppColors.primary,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'Fotografa la tabella nutrizionale. I valori poco sicuri restano vuoti e possono essere corretti.',
                                  style: AppTypography.bodyMedium,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 24),
                        Text('Valori nutrizionali',
                            style: AppTypography.headline3),
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
                          'I valori leggibili vengono precompilati dalla foto. Correggi soltanto quelli segnalati; i campi non rilevati restano vuoti.',
                          style: AppTypography.bodySmall,
                        ),
                        if (_nutritionRawOcr case final rawText?)
                          _OcrOriginalTextPanel(
                            key: const ValueKey('nutrition-original-ocr'),
                            languageCode: _nutritionLanguage ?? 'und',
                            rawText: rawText,
                          ),
                        if (_nutritionNeedsConfirmation)
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Chip(label: Text('Da verificare')),
                              CheckboxListTile(
                                key: const ValueKey(
                                    'nutrition-review-confirmation'),
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
                        DropdownButtonFormField<String>(
                          key: const ValueKey('nutrition-basis'),
                          initialValue: _nutritionBasis,
                          decoration: const InputDecoration(
                            labelText: 'Valori riferiti a',
                            border: OutlineInputBorder(),
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'per_100_g',
                              child: Text('100 g'),
                            ),
                            DropdownMenuItem(
                              value: 'per_100_ml',
                              child: Text('100 ml'),
                            ),
                            DropdownMenuItem(
                              value: 'per_serving',
                              child: Text('Una porzione'),
                            ),
                          ],
                          onChanged: (value) => setState(() {
                            _nutritionBasis = value;
                            _nutritionUserEdited = true;
                            _nutritionConfirmed = false;
                          }),
                        ),
                        const SizedBox(height: 10),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Chip(
                            key: const ValueKey('nutrition-provenance'),
                            avatar: Icon(
                              _nutritionUserEdited
                                  ? Icons.edit_outlined
                                  : Icons.document_scanner_outlined,
                              size: 18,
                            ),
                            label: Text(_nutritionUserEdited
                                ? 'Corretto dall’utente · Da validare'
                                : _nutritionRawOcr != null
                                    ? 'Estratto dalla foto · Da verificare'
                                    : 'Inserimento manuale · Da validare'),
                          ),
                        ),
                        const SizedBox(height: 10),
                        GridView.count(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          crossAxisCount: 2,
                          crossAxisSpacing: 12,
                          mainAxisSpacing: 12,
                          childAspectRatio: 2.4,
                          children: [
                            _NumberField(
                              controller: _energyKjController,
                              label: 'Energia kJ',
                              maximum: 4000,
                              onChanged: _markNutritionEdited,
                            ),
                            _NumberField(
                              controller: _energyController,
                              label: 'Energia kcal',
                              maximum: 900,
                              onChanged: _markNutritionEdited,
                            ),
                            _NumberField(
                              controller: _proteinController,
                              label: 'Proteine g',
                              onChanged: _markNutritionEdited,
                            ),
                            _NumberField(
                              controller: _carbsController,
                              label: 'Carboidrati g',
                              onChanged: _markNutritionEdited,
                            ),
                            _NumberField(
                                controller: _sugarController,
                                label: 'Zuccheri g',
                                onChanged: _markNutritionEdited),
                            _NumberField(
                              controller: _fatController,
                              label: 'Grassi g',
                              onChanged: _markNutritionEdited,
                            ),
                            _NumberField(
                                controller: _saturatedFatController,
                                label: 'Grassi saturi g',
                                onChanged: _markNutritionEdited),
                            _NumberField(
                                controller: _sodiumController,
                                label: 'Sodio (mg)',
                                maximum: 100000,
                                onChanged: _markNutritionEdited),
                            _NumberField(
                                controller: _saltController,
                                label: 'Sale (g)',
                                onChanged: _markNutritionEdited),
                            _NumberField(
                                controller: _fiberController,
                                label: 'Fibre g',
                                onChanged: _markNutritionEdited),
                          ],
                        ),
                        const SizedBox(height: 24),
                      ],
                      if (_photoReviewMessage != null) ...[
                        Semantics(
                          liveRegion: true,
                          child: Container(
                            key: const ValueKey('photo-review-status'),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.08),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: AppColors.primary.withValues(alpha: 0.3),
                              ),
                            ),
                            child: Text(
                              _photoReviewMessage!,
                              style: AppTypography.bodySmall,
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],
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
                      if (_currentStep == 3) ...[
                        Card(
                          key: const ValueKey('registration-summary'),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Controlla prima dell’invio',
                                  style: AppTypography.headline3,
                                ),
                                const SizedBox(height: 12),
                                _WizardSummaryRow(
                                  label: 'Prodotto',
                                  value:
                                      _productNameController.text.trim().isEmpty
                                          ? 'Da completare'
                                          : _productNameController.text.trim(),
                                ),
                                _WizardSummaryRow(
                                  label: 'Foto prodotto',
                                  value: _productImage == null
                                      ? 'Mancante'
                                      : 'Pronta',
                                ),
                                _WizardSummaryRow(
                                  label: 'Ingredienti',
                                  value: _ingredientsImage == null
                                      ? 'Foto mancante'
                                      : 'Foto pronta',
                                ),
                                _WizardSummaryRow(
                                  label: 'Nutrizione',
                                  value: _nutritionImage == null
                                      ? 'Foto mancante'
                                      : 'Foto pronta',
                                ),
                                const Divider(height: 24),
                                const Text(
                                  'Il prodotto verrà salvato come “Da validare”. Nessuno score viene inventato.',
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          key: const ValueKey('submit-acquisition'),
                          onPressed: _isSubmitting || _isProcessingImage
                              ? null
                              : _submit,
                          icon: _isSubmitting
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child:
                                      CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.save_alt),
                          label: Text(_isSubmitting
                              ? 'Invio...'
                              : 'Invia per la verifica'),
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
                                  const Text('Dati etichetta non verificati'),
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
                                      label:
                                          const Text('Apri dettaglio prodotto'),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                        ],
                      ],
                      if (_currentStep < 3)
                        FilledButton.icon(
                          key: const ValueKey('wizard-next'),
                          onPressed: () => _moveToStep(_currentStep + 1),
                          icon: const Icon(Icons.arrow_forward),
                          label: const Text('Continua'),
                          style: FilledButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                        ),
                      const SizedBox(height: 24),
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
            BottomNavigationBarItem(
                icon: Icon(Icons.history), label: 'Storico'),
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
      ),
    );
  }
}

class _WizardSummaryRow extends StatelessWidget {
  final String label;
  final String value;

  const _WizardSummaryRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(label, style: AppTypography.label),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(value, textAlign: TextAlign.end),
          ),
        ],
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

class _OcrOriginalTextPanel extends StatelessWidget {
  final String languageCode;
  final String rawText;

  const _OcrOriginalTextPanel({
    super.key,
    required this.languageCode,
    required this.rawText,
  });

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: const Text('Consulta testo originale etichetta'),
      subtitle: Text(
        languageCode == 'und'
            ? 'Lingua non determinata'
            : 'Lingua rilevata: ${languageDisplayNameItalian(languageCode)}',
      ),
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: SelectableText(rawText),
        ),
      ],
    );
  }
}

class _NumberField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final double maximum;
  final ValueChanged<String>? onChanged;

  const _NumberField({
    required this.controller,
    required this.label,
    this.maximum = 100,
    this.onChanged,
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
      onChanged: onChanged,
      validator: (value) {
        final text = value?.trim() ?? '';
        if (text.isEmpty) return null;
        final parsed = double.tryParse(text.replaceAll(',', '.'));
        if (parsed == null) return 'Numero non valido';
        if (parsed < 0) return 'Non può essere negativo';
        if (parsed > maximum) return 'Valore non plausibile';
        return null;
      },
    );
  }
}
