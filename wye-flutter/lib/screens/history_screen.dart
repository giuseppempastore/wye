import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../models/product_model.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';
import '../widgets/score_widgets.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Storico Scansioni'),
        elevation: 0,
      ),
      body: Consumer<BarcodeScannerProvider>(
        builder: (context, provider, _) {
          if (provider.scanHistory.isEmpty) {
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
                    'Nessuno scansionamento ancora',
                    style: AppTypography.headline3,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'I tuoi scansionamenti appariranno qui',
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
            itemCount: provider.scanHistory.length,
            itemBuilder: (context, index) {
              final scan = provider.scanHistory[index];
              final color = getScoreColor(scan.finalScore);

              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(16),
                  leading: _buildHistoryImage(scan, color),
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
                        scan.category,
                        style: AppTypography.labelSmall,
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

  Widget _buildHistoryImage(ScanHistory scan, Color color) {
    if (scan.imageUrl != null && scan.imageUrl!.startsWith('data:image')) {
      final bytes = const Base64Codec().decode(scan.imageUrl!.split(',').last);
      return ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: Image.memory(
          bytes,
          width: 60,
          height: 60,
          fit: BoxFit.cover,
        ),
      );
    }

    return Container(
      width: 60,
      height: 60,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color, width: 2),
      ),
      child: Center(
        child: Text(
          '${scan.finalScore.toStringAsFixed(0)}',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
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
