import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';

class AcquisitionHomeScreen extends StatelessWidget {
  const AcquisitionHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'WYE',
          style: AppTypography.headline2.copyWith(
            color: AppColors.primary,
            letterSpacing: 1.5,
          ),
        ),
      ),
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.all(16),
              sliver: SliverFillRemaining(
                hasScrollBody: false,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Image.asset(
                        'img/What_you_eatin_theme_upd_1.jpg',
                        height: 144,
                        fit: BoxFit.cover,
                      ),
                    ),
                    const Spacer(),
                    Text('Cosa vuoi fare?', style: AppTypography.headline3),
                    const SizedBox(height: 14),
                    _HomeAction(
                      key: const ValueKey('home-scan-product'),
                      icon: Icons.qr_code_scanner,
                      title: 'Scansiona prodotto',
                      description:
                          'Leggi il barcode e apri dati e valutazione disponibili.',
                      onTap: () => context.push('/scanner'),
                    ),
                    _HomeAction(
                      key: const ValueKey('home-add-product'),
                      icon: Icons.add_a_photo_outlined,
                      title: 'Aggiungi prodotto',
                      description:
                          'Analizza un’etichetta o registra un nuovo prodotto.',
                      onTap: () => context.push('/add-product'),
                    ),
                    const Spacer(),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 0,
        onTap: (index) {
          if (index == 1) context.go('/history');
          if (index == 2) context.go('/settings');
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'Storico'),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'Impostazioni',
          ),
        ],
      ),
    );
  }
}

class _HomeAction extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;
  final VoidCallback? onTap;

  const _HomeAction({
    super.key,
    required this.icon,
    required this.title,
    required this.description,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      color: Colors.white,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 96),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
            child: Row(
              children: [
                Icon(icon, color: AppColors.primary, size: 30),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: AppTypography.bodyLarge.copyWith(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(description, style: AppTypography.bodySmall),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
