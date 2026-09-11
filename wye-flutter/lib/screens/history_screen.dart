import 'dart:io';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';
import '../models/product_taxonomy.dart';
import '../widgets/product_image.dart';
import '../widgets/score_widgets.dart';
import '../services/database_service.dart';
import '../models/product_acquisition_draft.dart';
import '../services/api_client.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _refreshAcquisitions());
  }

  Future<void> _refreshAcquisitions() async {
    final database = context.read<DatabaseService>();
    final api = context.read<ApiClient>();
    var changed = false;
    for (final draft in database.getAcquisitionDrafts()) {
      if (draft.acquisitionId == null) continue;
      try {
        final remote = await api.getProductAcquisition(draft.acquisitionId!);
        final status = ProductAcquisitionStatusWire.parse(remote['status']);
        if (status != draft.status ||
            remote['recoverable_error_code'] != draft.recoverableErrorCode) {
          await database.saveAcquisitionDraft(draft.copyWith(
            status: status,
            recoverableErrorCode: remote['recoverable_error_code']?.toString(),
            clearRecoverableError: remote['recoverable_error_code'] == null,
          ));
          changed = true;
        }
      } on Object {
        // Offline history retains the last persisted safe state.
      }
    }
    if (changed && mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Storico'),
        elevation: 0,
      ),
      body: Consumer<BarcodeScannerProvider>(
        builder: (context, provider, _) {
          final acquisitions =
              context.read<DatabaseService>().getAcquisitionDrafts();
          if (provider.scanHistory.isEmpty && acquisitions.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.history,
                    size: 64,
                    color: AppColors.mediumGrey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Nessuna attività ancora',
                    style: AppTypography.headline3,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Scansioni, bozze e acquisizioni appariranno qui',
                    style: AppTypography.bodyMedium,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () => context.go('/scanner'),
                    icon: const Icon(Icons.qr_code_scanner),
                    label: const Text('Inizia a Scansionare'),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: acquisitions.length + provider.scanHistory.length,
            itemBuilder: (context, index) {
              if (index < acquisitions.length) {
                return _AcquisitionHistoryTile(draft: acquisitions[index]);
              }
              final scanIndex = index - acquisitions.length;
              final scan = provider.scanHistory[scanIndex];

              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(16),
                  leading: ProductImage(
                    imageUrl: scan.imageUrl,
                    width: 60,
                    height: 60,
                  ),
                  title: Text(
                    scan.productName,
                    style: AppTypography.bodyLarge,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 4),
                      Text(
                        productCategoryLabel(scan.category),
                        style: AppTypography.labelSmall,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Score: ${scoreAvailabilityLabel(scan.scoreView)}',
                        key: const ValueKey('history-score-state'),
                        style: AppTypography.bodySmall,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        scan.dataVerified
                            ? 'Dati etichetta verificati'
                            : 'Dati etichetta non verificati',
                        key: const ValueKey('history-validation-state'),
                        style: AppTypography.bodySmall,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _formatDate(scan.scannedAt),
                        style: AppTypography.bodySmall,
                      ),
                    ],
                  ),
                  trailing: Icon(
                    Icons.arrow_forward_ios,
                    size: 16,
                    color: AppColors.mediumGrey,
                  ),
                  onTap: () => context.go('/product/${scan.barcode}'),
                ),
              );
            },
          );
        },
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
        currentIndex: 1,
        onTap: (index) {
          switch (index) {
            case 0:
              context.go('/');
              break;
            case 1:
              // Già su storico
              break;
            case 2:
              context.go('/settings');
              break;
          }
        },
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final scanDate = DateTime(date.year, date.month, date.day);

    if (scanDate == today) {
      return 'Oggi alle ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } else if (scanDate == yesterday) {
      return 'Ieri alle ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } else {
      return '${date.day}/${date.month}/${date.year}';
    }
  }
}

class _AcquisitionHistoryTile extends StatelessWidget {
  final ProductAcquisitionDraft draft;

  const _AcquisitionHistoryTile({required this.draft});

  @override
  Widget build(BuildContext context) {
    final imagePath = draft.localImagePaths['product_front'];
    final imageFile = imagePath == null ? null : File(imagePath);
    return Card(
      key: ValueKey('acquisition-history-${draft.id}'),
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: SizedBox(
          width: 60,
          height: 60,
          child: imageFile != null && imageFile.existsSync()
              ? ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.file(imageFile, fit: BoxFit.cover),
                )
              : const Icon(Icons.inventory_2_outlined),
        ),
        title: Text(
          draft.productName.trim().isEmpty
              ? 'Registrazione prodotto'
              : draft.productName,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              draft.status.italianLabel,
              key: const ValueKey('acquisition-status'),
            ),
            const SizedBox(height: 4),
            const Text('Score: non ancora calcolato'),
            if (draft.recoverableErrorCode != null)
              const Text('Puoi riaprire la bozza e riprovare.'),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          if (draft.status == ProductAcquisitionStatus.draft ||
              draft.status == ProductAcquisitionStatus.failed) {
            context.go('/register-product');
          } else if (draft.barcode != null) {
            context.go('/product/${draft.barcode}');
          }
        },
      ),
    );
  }
}
