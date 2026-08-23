import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';
import '../widgets/score_widgets.dart';

class BarcodeScannerScreen extends StatefulWidget {
  const BarcodeScannerScreen({Key? key}) : super(key: key);

  @override
  State<BarcodeScannerScreen> createState() => _BarcodeScannerScreenState();
}

class _BarcodeScannerScreenState extends State<BarcodeScannerScreen> {
  final TextEditingController _barcodeController = TextEditingController();
  bool _isScanning = false;
  MobileScannerController? _scannerController;
  String? _lastScannedBarcode;
  DateTime? _lastScanAt;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    _scannerController = MobileScannerController();
    setState(() {});
  }

  @override
  void dispose() {
    _barcodeController.dispose();
    _scannerController?.dispose();
    super.dispose();
  }

  Future<void> _handleBarcodeScan(String barcode) async {
    if (barcode.isEmpty) return;

    final provider = context.read<BarcodeScannerProvider>();
    await provider.scanBarcode(barcode);

    if (mounted) {
      context.read<UserPreferencesProvider>().resetPremiumFactCheckConsent();
    }

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
    // filtra codici troppo corti / rumorosi
    if (barcode.length < 8) return false;

    final now = DateTime.now();
    if (_lastScannedBarcode == barcode && _lastScanAt != null) {
      final delta = now.difference(_lastScanAt!);
      if (delta.inMilliseconds < 1800) {
        return false;
      }
    }

    _lastScannedBarcode = barcode;
    _lastScanAt = now;
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scansiona Barcode'),
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
                child: _scannerController != null
                    ? MobileScanner(
                        controller: _scannerController!,
                        onDetect: (capture) {
                          final List<Barcode> barcodes = capture.barcodes;
                          if (barcodes.isNotEmpty) {
                            final String barcode = barcodes.first.rawValue ?? '';
                            if (barcode.isNotEmpty && _shouldProcessBarcode(barcode)) {
                              _barcodeController.text = barcode;
                              _handleBarcodeScan(barcode);
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
                              'Inizializzazione camera...',
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
                      setState(() => _isScanning = false);
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
                            setState(() => _isScanning = false);
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
                  final countryValue = countries.keys.contains(userPref.country)
                      ? userPref.country
                      : 'IT';
                  final countryLabel = countries[countryValue] ?? countryValue;

                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Paese di riferimento per il fact checking',
                        style: AppTypography.label,
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        value: countryValue,
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
                      const SizedBox(height: 12),
                      CheckboxListTile(
                        value: userPref.isPremium
                            ? userPref.premiumFactCheckConsent
                            : false,
                        onChanged: userPref.isPremium
                            ? (value) async {
                                if (value == true) {
                                  userPref.setPremiumFactCheckConsent(true);
                                  if (mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(
                                          'Fact checking AI pronto per $countryLabel: esegui la scansione del prodotto per attivarlo.',
                                        ),
                                        backgroundColor: AppColors.accent,
                                      ),
                                    );
                                  }
                                  return;
                                }

                                userPref.setPremiumFactCheckConsent(false);
                              }
                            : null,
                        enabled: userPref.isPremium,
                        title: const Text('Fact checking AI premium'),
                        subtitle: Text(
                          userPref.isPremium
                              ? 'Verrà eseguito per il paese selezionato: $countryLabel.'
                              : 'Disponibile solo per utenti premium.',
                        ),
                        controlAffinity: ListTileControlAffinity.leading,
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
    );
  }
}
