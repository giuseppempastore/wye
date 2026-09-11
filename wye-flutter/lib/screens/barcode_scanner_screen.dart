import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';
import '../services/product_barcode_validator.dart';
import '../services/device_camera_availability.dart';
import '../widgets/score_widgets.dart';

class BarcodeScannerScreen extends StatefulWidget {
  final Future<bool> Function()? cameraAvailabilityCheck;

  const BarcodeScannerScreen({
    super.key,
    this.cameraAvailabilityCheck,
  });

  @override
  State<BarcodeScannerScreen> createState() => _BarcodeScannerScreenState();
}

class _BarcodeScannerScreenState extends State<BarcodeScannerScreen> {
  final TextEditingController _barcodeController = TextEditingController();
  bool _isScanning = false;
  bool _checkingCamera = true;
  bool _cameraUnavailable = false;
  MobileScannerController? _scannerController;
  final ProductBarcodeValidator _barcodeValidator =
      const ProductBarcodeValidator();
  final BarcodeScanDebouncer _scanDebouncer = BarcodeScanDebouncer();

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    final available = await (widget.cameraAvailabilityCheck?.call() ??
        const DeviceCameraAvailability().hasUsableCamera());
    if (!mounted) return;
    setState(() {
      _checkingCamera = false;
      _cameraUnavailable = !available;
      if (available) _scannerController = MobileScannerController();
    });
  }

  void _goBack() {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/');
    }
  }

  @override
  void dispose() {
    _barcodeController.dispose();
    _scannerController?.dispose();
    super.dispose();
  }

  Future<void> _handleBarcodeScan(String barcode) async {
    final validation = _barcodeValidator.validate(barcode);
    debugPrint(validation.safeLog);
    if (!validation.isValid) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Codice non valido. Usa un EAN-8, UPC-A, EAN-13 o GTIN-14 con checksum corretto.',
            ),
            backgroundColor: AppColors.riskHigh,
          ),
        );
      }
      return;
    }
    final canonicalBarcode = validation.value!;

    final provider = context.read<BarcodeScannerProvider>();
    await provider.scanBarcode(canonicalBarcode);

    if (provider.currentProduct != null) {
      if (mounted) {
        context.go('/product/${provider.currentProduct!.barcode}');
      }
    } else if (provider.error != null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(provider.error!),
            backgroundColor: AppColors.riskHigh,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  bool _shouldProcessBarcode(String barcode) {
    final validation = _barcodeValidator.validate(barcode);
    debugPrint(validation.safeLog);
    return validation.isValid &&
        !_isScanning &&
        _scanDebouncer.shouldAccept(validation.value!, DateTime.now());
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: Navigator.of(context).canPop(),
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) context.go('/');
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Scansiona Barcode'),
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            tooltip: 'Indietro',
            onPressed: _goBack,
          ),
        ),
        body: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Camera placeholder (integrazione mobile_scanner)
                Container(
                  height: 300,
                  decoration: BoxDecoration(
                    color: AppColors.darkGrey,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: AppColors.primary,
                      width: 2,
                    ),
                  ),
                  child: _cameraUnavailable
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.no_photography_outlined,
                                    size: 48, color: AppColors.white),
                                const SizedBox(height: 16),
                                Text(
                                  'Fotocamera non disponibile. Nell’emulatore abilita una camera virtuale oppure prova su un telefono.',
                                  textAlign: TextAlign.center,
                                  style: AppTypography.bodyMedium.copyWith(
                                    color: AppColors.white,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                      : _scannerController != null
                          ? MobileScanner(
                              controller: _scannerController!,
                              onDetect: (capture) {
                                final List<Barcode> barcodes = capture.barcodes;
                                if (barcodes.isNotEmpty) {
                                  final String barcode =
                                      barcodes.first.rawValue ?? '';
                                  if (barcode.isNotEmpty &&
                                      _shouldProcessBarcode(barcode)) {
                                    final canonical = _barcodeValidator
                                        .validate(barcode)
                                        .value!;
                                    _barcodeController.text = canonical;
                                    setState(() => _isScanning = true);
                                    _handleBarcodeScan(canonical)
                                        .whenComplete(() {
                                      if (mounted) {
                                        setState(() => _isScanning = false);
                                      }
                                    });
                                  }
                                }
                              },
                              errorBuilder: (context, error) {
                                return Center(
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Icon(
                                        Icons.error_outline,
                                        size: 48,
                                        color: AppColors.riskHigh,
                                      ),
                                      const SizedBox(height: 16),
                                      Text(
                                        'Errore camera: ${error.toString()}',
                                        textAlign: TextAlign.center,
                                        style: AppTypography.bodySmall.copyWith(
                                          color: AppColors.white,
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            )
                          : Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  const Icon(
                                    Icons.camera_alt,
                                    size: 64,
                                    color: AppColors.white,
                                  ),
                                  const SizedBox(height: 16),
                                  Text(
                                    _checkingCamera
                                        ? 'Controllo fotocamera...'
                                        : 'Fotocamera non disponibile',
                                    textAlign: TextAlign.center,
                                    style: AppTypography.bodyMedium.copyWith(
                                      color: AppColors.white,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                ),
                const SizedBox(height: 24),

                // Manual barcode input
                Text(
                  'Oppure inserisci il codice manualmente',
                  style: AppTypography.label,
                ),
                const SizedBox(height: 12),

                Consumer<BarcodeScannerProvider>(
                  builder: (context, provider, _) {
                    return TextField(
                      controller: _barcodeController,
                      decoration: InputDecoration(
                        hintText: 'Es: 8718206...',
                        prefixIcon: const Icon(Icons.barcode_reader),
                        suffixIcon: _isScanning
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: Center(
                                  child: SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  ),
                                ),
                              )
                            : _barcodeController.text.isNotEmpty
                                ? IconButton(
                                    icon: const Icon(Icons.clear),
                                    onPressed: () {
                                      _barcodeController.clear();
                                    },
                                  )
                                : null,
                      ),
                      onChanged: (_) {
                        setState(() {});
                      },
                      onSubmitted: (barcode) async {
                        setState(() => _isScanning = true);
                        await _handleBarcodeScan(barcode);
                        if (mounted) setState(() => _isScanning = false);
                      },
                    );
                  },
                ),
                const SizedBox(height: 16),

                // Submit button
                Consumer<BarcodeScannerProvider>(
                  builder: (context, provider, _) {
                    return ElevatedButton.icon(
                      onPressed: _isScanning || _barcodeController.text.isEmpty
                          ? null
                          : () async {
                              setState(() => _isScanning = true);
                              await _handleBarcodeScan(
                                _barcodeController.text.trim(),
                              );
                              if (mounted) setState(() => _isScanning = false);
                            },
                      icon: const Icon(Icons.search),
                      label: const Text('Cerca Prodotto'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 24),

                Consumer<UserPreferencesProvider>(
                  builder: (context, userPref, _) {
                    final countries = {
                      'IT': 'Italia',
                      'DE': 'Germania',
                      'FR': 'Francia',
                      'ES': 'Spagna',
                      'UK': 'Regno Unito',
                      'US': 'Stati Uniti',
                    };
                    final countryValue =
                        countries.keys.contains(userPref.country)
                            ? userPref.country
                            : 'IT';
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Paese di riferimento per il fact checking',
                          style: AppTypography.label,
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          initialValue: countryValue,
                          isExpanded: true,
                          decoration: const InputDecoration(
                            prefixIcon: Icon(Icons.location_on_outlined),
                          ),
                          items: countries.entries
                              .map(
                                (entry) => DropdownMenuItem<String>(
                                  value: entry.key,
                                  child: Text(entry.value),
                                ),
                              )
                              .toList(),
                          onChanged: (value) {
                            if (value != null) {
                              userPref.setCountry(value);
                            }
                          },
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 32),

                // Tips
                Text(
                  'Suggerimenti',
                  style: AppTypography.headline3,
                ),
                const SizedBox(height: 12),

                InfoSection(
                  icon: Icons.info,
                  title: 'Dove trovare il barcode',
                  description:
                      'Di solito è sul retro o sul lato del prodotto. Leggi il codice sotto il barcode.',
                  iconColor: AppColors.info,
                ),
                const SizedBox(height: 12),

                InfoSection(
                  icon: Icons.lightbulb,
                  title: 'Illuminazione',
                  description:
                      'Assicurati una buona illuminazione per scansioni più veloci e accurate.',
                  iconColor: AppColors.warning,
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
      ),
    );
  }
}
