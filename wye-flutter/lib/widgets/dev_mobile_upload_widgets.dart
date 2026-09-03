import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../models/capture_upload_models.dart';
import '../models/extraction_models.dart';
import '../providers/capture_upload_controller.dart';
import '../theme/app_theme.dart';

typedef DevImageBytesPicker = Future<Uint8List?> Function();

class DevMobileUploadTokenPanel extends StatefulWidget {
  const DevMobileUploadTokenPanel({super.key});

  @override
  State<DevMobileUploadTokenPanel> createState() =>
      _DevMobileUploadTokenPanelState();
}

class _DevMobileUploadTokenPanelState extends State<DevMobileUploadTokenPanel> {
  final _tokenController = TextEditingController();
  final _validityController = TextEditingController(text: '15');

  @override
  void dispose() {
    _tokenController.dispose();
    _validityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CaptureUploadController>(
      builder: (context, controller, _) {
        final tokenState = controller.tokenState;
        return Column(
          key: const Key('dev-mobile-token-panel'),
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Solo sviluppo locale. Il token resta in memoria e viene '
              'rimosso alla chiusura dell\'app.',
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('dev-mobile-token-field'),
              controller: _tokenController,
              obscureText: true,
              enableSuggestions: false,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'Token mobile temporaneo',
                prefixIcon: Icon(Icons.key),
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('dev-mobile-token-validity-field'),
              controller: _validityController,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              decoration: const InputDecoration(
                labelText: 'Validita locale (1-60 minuti)',
                prefixIcon: Icon(Icons.timer_outlined),
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    key: const Key('dev-mobile-token-save'),
                    onPressed: _canSave ? () => _save(controller) : null,
                    icon: const Icon(Icons.lock_clock_outlined),
                    label: const Text('Imposta token'),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  key: const Key('dev-mobile-token-clear'),
                  onPressed: tokenState == DevMobileTokenState.missing
                      ? null
                      : () {
                          _tokenController.clear();
                          controller.clearTemporaryToken();
                          setState(() {});
                        },
                  child: const Text('Rimuovi'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _tokenStatus(controller),
              key: const Key('dev-mobile-token-status'),
              style: AppTypography.bodySmall,
            ),
          ],
        );
      },
    );
  }

  bool get _canSave {
    final minutes = int.tryParse(_validityController.text.trim());
    return _tokenController.text.trim().isNotEmpty &&
        minutes != null &&
        minutes > 0 &&
        minutes <= 60;
  }

  void _save(CaptureUploadController controller) {
    final minutes = int.parse(_validityController.text.trim());
    controller.setTemporaryToken(
      _tokenController.text.trim(),
      expiresAt: DateTime.now().toUtc().add(Duration(minutes: minutes)),
    );
    _tokenController.clear();
    setState(() {});
  }

  String _tokenStatus(CaptureUploadController controller) {
    switch (controller.tokenState) {
      case DevMobileTokenState.missing:
        return 'Token mancante';
      case DevMobileTokenState.expired:
        return 'Token scaduto';
      case DevMobileTokenState.present:
        final expiry = controller.tokenExpiresAt;
        return expiry == null
            ? 'Token presente'
            : 'Token presente fino a ${expiry.toLocal().toIso8601String()}';
    }
  }
}

class DevMobileCaptureUploadPanel extends StatefulWidget {
  final DevImageBytesPicker? pickImageBytes;

  const DevMobileCaptureUploadPanel({
    super.key,
    this.pickImageBytes,
  });

  @override
  State<DevMobileCaptureUploadPanel> createState() =>
      _DevMobileCaptureUploadPanelState();
}

class _DevMobileCaptureUploadPanelState
    extends State<DevMobileCaptureUploadPanel> {
  final _productIdController = TextEditingController();
  final _barcodeController = TextEditingController();
  final _picker = ImagePicker();
  CaptureImagePurpose _purpose = CaptureImagePurpose.ingredients;
  bool _picking = false;

  @override
  void dispose() {
    _productIdController.dispose();
    _barcodeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CaptureUploadController>(
      builder: (context, controller, _) {
        final busy = _picking || controller.isTransitionActive;
        return Card(
          key: const Key('dev-mobile-capture-panel'),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text('Upload mobile locale', style: AppTypography.headline3),
                const SizedBox(height: 8),
                const Text(
                  'Percorso tecnico locale separato dallo scoring.',
                ),
                const SizedBox(height: 12),
                TextField(
                  key: const Key('dev-mobile-product-id-field'),
                  controller: _productIdController,
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  decoration: const InputDecoration(
                    labelText: 'Product ID',
                    prefixIcon: Icon(Icons.tag),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                TextField(
                  key: const Key('dev-mobile-barcode-field'),
                  controller: _barcodeController,
                  decoration: const InputDecoration(
                    labelText: 'Barcode',
                    prefixIcon: Icon(Icons.qr_code),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<CaptureImagePurpose>(
                  key: const Key('dev-mobile-purpose-field'),
                  initialValue: _purpose,
                  decoration: const InputDecoration(
                    labelText: 'Tipo immagine',
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: CaptureImagePurpose.ingredients,
                      child: Text('Ingredienti'),
                    ),
                    DropdownMenuItem(
                      value: CaptureImagePurpose.nutrition,
                      child: Text('Valori nutrizionali'),
                    ),
                    DropdownMenuItem(
                      value: CaptureImagePurpose.productFront,
                      child: Text('Fronte prodotto'),
                    ),
                  ],
                  onChanged: busy
                      ? null
                      : (value) {
                          if (value != null) {
                            setState(() => _purpose = value);
                          }
                        },
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  key: const Key('dev-mobile-pick-image'),
                  onPressed: _canSelectImage(controller) && !busy
                      ? () => _selectImage(controller)
                      : null,
                  icon: const Icon(Icons.add_a_photo_outlined),
                  label: const Text('Seleziona immagine'),
                ),
                const SizedBox(height: 8),
                ElevatedButton.icon(
                  key: const Key('dev-mobile-upload'),
                  onPressed: _canUpload(controller) && !busy
                      ? () => controller.upload()
                      : null,
                  icon: const Icon(Icons.cloud_upload_outlined),
                  label: const Text('Avvia upload'),
                ),
                if (controller.state.step ==
                    UploadFlowStep.failedRetryable) ...[
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    key: const Key('dev-mobile-upload-retry'),
                    onPressed: busy ? null : controller.retry,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Riprova'),
                  ),
                ],
                const SizedBox(height: 12),
                Text(
                  _statusText(controller),
                  key: const Key('dev-mobile-upload-status'),
                  style: AppTypography.bodySmall,
                ),
                if (_showExtractionControls(controller)) ...[
                  const SizedBox(height: 12),
                  const Divider(),
                  const SizedBox(height: 8),
                  Text(
                    'Estrazione etichetta',
                    style: AppTypography.bodyMedium,
                  ),
                  const SizedBox(height: 8),
                  if (controller.extractionState.step ==
                      ExtractionFlowStep.deferred)
                    OutlinedButton.icon(
                      key: const Key('dev-mobile-extraction-start'),
                      onPressed: busy ? null : controller.startExtraction,
                      icon: const Icon(Icons.text_snippet_outlined),
                      label: const Text('Avvia estrazione'),
                    ),
                  if (controller.extractionState.step ==
                      ExtractionFlowStep.loading)
                    OutlinedButton.icon(
                      key: const Key('dev-mobile-extraction-refresh'),
                      onPressed: busy ? null : controller.refreshExtraction,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Aggiorna stato'),
                    ),
                  if (controller.extractionState.step ==
                      ExtractionFlowStep.failedRetryable)
                    OutlinedButton.icon(
                      key: const Key('dev-mobile-extraction-retry'),
                      onPressed: busy ? null : controller.retryExtraction,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Riprova estrazione'),
                    ),
                  const SizedBox(height: 8),
                  Text(
                    _extractionStatusText(controller),
                    key: const Key('dev-mobile-extraction-status'),
                    style: AppTypography.bodySmall,
                  ),
                  if (controller.extractionState.step ==
                      ExtractionFlowStep.succeeded)
                    ..._extractionItems(controller.extractionState),
                ],
                if (busy) ...[
                  const SizedBox(height: 12),
                  const LinearProgressIndicator(),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  int? get _productId {
    final parsed = int.tryParse(_productIdController.text.trim());
    return parsed != null && parsed > 0 ? parsed : null;
  }

  bool _canSelectImage(CaptureUploadController controller) =>
      controller.tokenState == DevMobileTokenState.present &&
      _productId != null &&
      _barcodeController.text.trim().isNotEmpty;

  bool _canUpload(CaptureUploadController controller) =>
      _canSelectImage(controller) &&
      controller.state.step == UploadFlowStep.metadataReady &&
      _matchesPreparedIdentity(controller);

  Future<void> _selectImage(CaptureUploadController controller) async {
    if (!_canSelectImage(controller)) {
      setState(() {});
      return;
    }
    setState(() => _picking = true);
    try {
      final bytes = await (widget.pickImageBytes ?? _pickImageBytes)();
      if (bytes == null || !mounted) {
        return;
      }
      controller.selectImage(
        productIdentity: ProductIdentity(
          productId: _productId!,
          barcode: _barcodeController.text.trim(),
        ),
        purpose: _purpose,
        bytes: bytes,
      );
      await controller.prepareMetadata();
    } finally {
      if (mounted) {
        setState(() => _picking = false);
      }
    }
  }

  Future<Uint8List?> _pickImageBytes() async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt_outlined),
              title: const Text('Scatta foto'),
              onTap: () => Navigator.of(context).pop(ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Scegli dalla galleria'),
              onTap: () => Navigator.of(context).pop(ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (source == null) {
      return null;
    }

    final picked = await _picker.pickImage(source: source, imageQuality: 85);
    if (picked == null) {
      return null;
    }

    XFile finalFile = picked;
    try {
      final cropped = await ImageCropper().cropImage(
        sourcePath: picked.path,
        uiSettings: [
          AndroidUiSettings(
            toolbarTitle: 'Ritaglia immagine',
            toolbarColor: Colors.black,
            toolbarWidgetColor: Colors.white,
            initAspectRatio: CropAspectRatioPreset.original,
            lockAspectRatio: false,
          ),
          IOSUiSettings(title: 'Ritaglia immagine'),
        ],
      );
      if (cropped != null) {
        finalFile = XFile(cropped.path);
      }
    } on Exception {
      // Cropping is optional; the selected bytes remain local and unlogged.
    }
    return finalFile.readAsBytes();
  }

  String _statusText(CaptureUploadController controller) {
    if (controller.tokenState == DevMobileTokenState.expired) {
      return 'Token scaduto';
    }
    if (controller.tokenState == DevMobileTokenState.missing) {
      return 'Token mancante';
    }
    if (_productId == null) {
      return 'Product ID richiesto';
    }
    if (_barcodeController.text.trim().isEmpty) {
      return 'Barcode richiesto';
    }
    if (controller.state.step == UploadFlowStep.metadataReady &&
        !_matchesPreparedIdentity(controller)) {
      return 'Dati modificati; seleziona nuovamente l\'immagine';
    }
    switch (controller.state.step) {
      case UploadFlowStep.disabled:
        return 'Funzione disabilitata';
      case UploadFlowStep.missingToken:
        return 'Token mancante';
      case UploadFlowStep.idle:
      case UploadFlowStep.productResolving:
      case UploadFlowStep.productRequired:
        return 'Immagine richiesta';
      case UploadFlowStep.imageSelected:
        return 'Preparazione metadati';
      case UploadFlowStep.metadataReady:
        return 'Immagine pronta per upload';
      case UploadFlowStep.uploadInitializing:
        return 'Inizializzazione upload';
      case UploadFlowStep.binaryUploading:
        return 'Invio immagine';
      case UploadFlowStep.finalizing:
        return 'Finalizzazione upload';
      case UploadFlowStep.uploadedAssociated:
        return 'Upload completato e immagine associata';
      case UploadFlowStep.extractionStarting:
        return 'Estrazione non disponibile in questa fase';
      case UploadFlowStep.extractionDeferred:
        return 'Upload associato; estrazione non avviata';
      case UploadFlowStep.failedRetryable:
        return 'Upload non completato; riprova disponibile';
      case UploadFlowStep.failedTerminal:
        return 'Upload bloccato (${controller.state.errorCode ?? 'errore'})';
    }
  }

  bool _matchesPreparedIdentity(CaptureUploadController controller) {
    final identity = controller.state.productIdentity;
    return identity?.productId == _productId &&
        identity?.barcode == _barcodeController.text.trim() &&
        controller.state.purpose == _purpose;
  }

  bool _showExtractionControls(CaptureUploadController controller) {
    return controller.state.productImage != null;
  }

  String _extractionStatusText(CaptureUploadController controller) {
    switch (controller.extractionState.step) {
      case ExtractionFlowStep.notStarted:
      case ExtractionFlowStep.deferred:
        return 'Estrazione non avviata';
      case ExtractionFlowStep.starting:
        return 'Avvio estrazione';
      case ExtractionFlowStep.loading:
        return 'Estrazione in elaborazione';
      case ExtractionFlowStep.succeeded:
        final count = controller.extractionState.result?.items.length ?? 0;
        return 'Estrazione completata: $count elementi disponibili';
      case ExtractionFlowStep.failedRetryable:
        return 'Estrazione non completata; riprova disponibile';
      case ExtractionFlowStep.failedTerminal:
        return 'Estrazione bloccata '
            '(${controller.extractionState.errorCode ?? 'errore'})';
      case ExtractionFlowStep.unavailable:
        return 'Estrazione non disponibile per questa immagine';
    }
  }

  List<Widget> _extractionItems(ExtractionFlowState state) {
    final items = state.result?.items ?? const <ExtractionItem>[];
    return [
      for (final item in items)
        ListTile(
          dense: true,
          contentPadding: EdgeInsets.zero,
          key: Key('dev-mobile-extraction-item-${item.extractionItemId}'),
          title: Text(item.normalizedText ?? item.rawText),
          subtitle: Text(
            '${_itemTypeLabel(item.type)} · ${item.status.name}',
          ),
        ),
    ];
  }

  String _itemTypeLabel(ExtractionItemType type) {
    return switch (type) {
      ExtractionItemType.ingredient => 'Ingrediente',
      ExtractionItemType.ingredientList => 'Lista ingredienti',
      ExtractionItemType.nutrition => 'Dato nutrizionale',
      ExtractionItemType.allergen => 'Voce allergeni',
      ExtractionItemType.quantity => 'Quantita',
      ExtractionItemType.unit => 'Unita',
      ExtractionItemType.other => 'Altro',
    };
  }
}
