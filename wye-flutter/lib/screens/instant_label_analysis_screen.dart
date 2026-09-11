import 'package:flutter/material.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../services/ai_usage_quota_service.dart';
import '../services/capture_upload_gateway.dart';
import '../services/device_camera_availability.dart';
import '../services/photo_field_mapper.dart';
import '../services/technical_session_bootstrapper.dart';
import '../theme/app_theme.dart';

class InstantLabelAnalysisScreen extends StatefulWidget {
  const InstantLabelAnalysisScreen({super.key});

  @override
  State<InstantLabelAnalysisScreen> createState() =>
      _InstantLabelAnalysisScreenState();
}

class _InstantLabelAnalysisScreenState
    extends State<InstantLabelAnalysisScreen> {
  final _picker = ImagePicker();
  final _mapper = const PhotoFieldMapper();
  bool _working = false;
  String? _ingredientsResult;
  String? _nutritionResult;
  String? _notice;

  void _goBack() {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/add-product');
    }
  }

  Future<ImageSource?> _chooseSource() => showModalBottomSheet<ImageSource>(
        context: context,
        builder: (context) => SafeArea(
          child: Wrap(children: [
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: const Text('Scatta foto'),
              onTap: () => Navigator.pop(context, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Carica dalla galleria'),
              onTap: () => Navigator.pop(context, ImageSource.gallery),
            ),
          ]),
        ),
      );

  Future<void> _analyze(ProductPhotoPurpose purpose) async {
    final quota = context.read<AiUsageQuotaService>();
    final sessionBootstrapper = context.read<TechnicalSessionBootstrapper>();
    final captureGateway = context.read<CaptureUploadGateway>();
    final source = await _chooseSource();
    if (source == null) return;
    final file = await _picker.pickImage(source: source, imageQuality: 92);
    if (file == null || !mounted) return;
    final assessment =
        await const OnDevicePhotoQualityService().assess(file.path);
    if (!assessment.ok && mounted) {
      setState(() {
        _notice = 'Meglio rifare la foto: ${assessment.userMessage}. '
            'Nessuna analisi AI è stata usata.';
      });
      return;
    }
    setState(() {
      _working = true;
      _notice = null;
    });
    final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
    try {
      final recognized = await recognizer.processImage(
        InputImage.fromFilePath(file.path),
      );
      var mapping = _mapper.map(recognized.text, purpose);
      if (mapping.needsTextFallback && !quota.exhausted) {
        final ready = await sessionBootstrapper.ensureReady();
        if (ready && mounted) {
          try {
            final result = await captureGateway.normalizeText(
              mapping.toTextNormalizationRequest(purpose),
            );
            mapping = mapping.mergeTextFallback(result);
            await quota.refresh();
          } on Object {
            _notice =
                'Analisi avanzata non disponibile: controlla i dati letti.';
          }
        }
      } else if (mapping.needsTextFallback && quota.exhausted) {
        _notice =
            'Hai raggiunto il limite giornaliero. È stata usata solo la lettura locale.';
      }
      if (!mounted) return;
      setState(() {
        if (purpose == ProductPhotoPurpose.ingredients) {
          _ingredientsResult =
              mapping.ingredientListText?.trim().isNotEmpty == true
                  ? mapping.ingredientListText
                  : 'Ingredienti non riconosciuti · da verificare';
        } else {
          _nutritionResult = mapping.hasNutrition
              ? mapping.nutrition.entries
                  .map((entry) => '${entry.key}: ${entry.value}')
                  .join('\n')
              : 'Valori nutrizionali non riconosciuti · da verificare';
        }
      });
    } on Object {
      if (mounted) {
        setState(() => _notice = 'Foto non leggibile. Riprova con più luce.');
      }
    } finally {
      await recognizer.close();
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final quota = context.watch<AiUsageQuotaService>();
    return PopScope(
      canPop: Navigator.of(context).canPop(),
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) context.go('/add-product');
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Analizza un’etichetta'),
          leading: BackButton(onPressed: _goBack),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              color: AppColors.primary.withValues(alpha: .08),
              child: ListTile(
                leading: const Icon(Icons.auto_awesome_outlined),
                title: Text(quota.availabilityLabel),
                subtitle: Text(quota.exhausted
                    ? 'Hai raggiunto il limite giornaliero. Puoi comunque registrare un nuovo prodotto da validare.'
                    : 'OCR e analisi locale non consumano disponibilità.'),
              ),
            ),
            const SizedBox(height: 16),
            _PhotoAction(
              key: const ValueKey('analyze-ingredients-photo'),
              title: 'Foto ingredienti',
              result: _ingredientsResult,
              enabled: !_working,
              onPressed: () => _analyze(ProductPhotoPurpose.ingredients),
            ),
            const SizedBox(height: 12),
            _PhotoAction(
              key: const ValueKey('analyze-nutrition-photo'),
              title: 'Foto valori nutrizionali',
              result: _nutritionResult,
              enabled: !_working,
              onPressed: () => _analyze(ProductPhotoPurpose.nutrition),
            ),
            if (_working) ...[
              const SizedBox(height: 20),
              const Center(child: CircularProgressIndicator()),
            ],
            if (_notice != null) ...[
              const SizedBox(height: 16),
              Text(_notice!),
            ],
            const SizedBox(height: 20),
            const Card(
              child: ListTile(
                leading: Icon(Icons.fact_check_outlined),
                title: Text('Dati non verificati'),
                subtitle: Text(
                    'Score non ancora calcolato. Nessun valore numerico viene simulato.'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PhotoAction extends StatelessWidget {
  final String title;
  final String? result;
  final bool enabled;
  final VoidCallback onPressed;

  const _PhotoAction({
    super.key,
    required this.title,
    required this.result,
    required this.enabled,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              FilledButton.tonalIcon(
                onPressed: enabled ? onPressed : null,
                icon: const Icon(Icons.add_a_photo_outlined),
                label: Text(title),
              ),
              if (result != null) ...[
                const SizedBox(height: 12),
                Text(result!),
              ],
            ],
          ),
        ),
      );
}
