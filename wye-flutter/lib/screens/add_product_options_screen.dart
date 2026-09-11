import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../services/ai_usage_quota_service.dart';
import '../theme/app_theme.dart';

class AddProductOptionsScreen extends StatelessWidget {
  const AddProductOptionsScreen({super.key});

  void _goBack(BuildContext context) {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/');
    }
  }

  @override
  Widget build(BuildContext context) {
    final quota = context.watch<AiUsageQuotaService>();
    return PopScope(
      canPop: Navigator.of(context).canPop(),
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) context.go('/');
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Aggiungi prodotto'),
          leading: BackButton(onPressed: () => _goBack(context)),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Come vuoi procedere?', style: AppTypography.headline3),
            const SizedBox(height: 8),
            const Text(
                'Scegli il percorso più adatto. Potrai tornare indietro senza perdere le bozze.'),
            const SizedBox(height: 20),
            _OptionCard(
              key: const ValueKey('add-option-analyze-label'),
              icon: Icons.auto_awesome_outlined,
              title: 'Analizza un’etichetta',
              description: quota.exhausted
                  ? 'Hai raggiunto il limite giornaliero. La registrazione resta disponibile.'
                  : '${quota.availabilityLabel}. Fotografa ingredienti e nutrizione.',
              onTap: () => context.push('/instant-label-analysis'),
            ),
            _OptionCard(
              key: const ValueKey('add-option-register-product'),
              icon: Icons.add_a_photo_outlined,
              title: 'Registra un nuovo prodotto',
              description:
                  'Scansiona il barcode e invia le foto come dati da validare.',
              onTap: () => context.push('/register-product'),
            ),
          ],
        ),
      ),
    );
  }
}

class _OptionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;
  final VoidCallback onTap;

  const _OptionCard({
    super.key,
    required this.icon,
    required this.title,
    required this.description,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(bottom: 12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                Icon(icon, color: AppColors.primary),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: AppTypography.bodyLarge),
                      const SizedBox(height: 5),
                      Text(description, style: AppTypography.bodySmall),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right),
              ],
            ),
          ),
        ),
      );
}
