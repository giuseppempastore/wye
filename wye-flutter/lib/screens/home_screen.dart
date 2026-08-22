import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';
import '../widgets/score_widgets.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WYE'),
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        AppColors.primary.withOpacity(0.1),
                        AppColors.secondary.withOpacity(0.05),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: AppColors.primary.withOpacity(0.2),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Benvenuto su WYE',
                        style: AppTypography.headline2,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Scopri la salubrità dei prodotti che consumi.',
                        style: AppTypography.bodyMedium,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),

                // Main Actions
                Text(
                  'Inizia',
                  style: AppTypography.headline3,
                ),
                const SizedBox(height: 16),

                // Button: Scan Barcode
                ElevatedButton.icon(
                  onPressed: () => context.go('/scanner'),
                  icon: const Icon(Icons.qr_code_scanner),
                  label: const Text('Scansiona Barcode'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 12),

                // Button: Manual Analysis (Premium)
                OutlinedButton.icon(
                  onPressed: () => context.go('/manual-analysis'),
                  icon: const Icon(Icons.edit_note),
                  label: const Text('Analizza Manualmente'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
                const SizedBox(height: 32),

                // Info Cards
                Text(
                  'Come funziona',
                  style: AppTypography.headline3,
                ),
                const SizedBox(height: 16),

                // Info Card 1
                InfoSection(
                  icon: Icons.explore,
                  title: 'Valutazione trasparente',
                  description:
                      'Scopri la salubrità di ogni prodotto basato su ingredienti e nutrizione.',
                  iconColor: AppColors.primary,
                ),
                const SizedBox(height: 12),

                // Info Card 2
                InfoSection(
                  icon: Icons.warning,
                  title: 'Allergeni e rischi',
                  description:
                      'Identifichiamo ingredienti critici e allergeni potenziali.',
                  iconColor: AppColors.riskHigh,
                ),
                const SizedBox(height: 12),

                // Info Card 3
                InfoSection(
                  icon: Icons.trending_up,
                  title: 'Scoring dettagliato',
                  description:
                      'Vedi come ingredienti e nutrizione influenzano il punteggio finale.',
                  iconColor: AppColors.secondary,
                ),
                const SizedBox(height: 32),

                // Recent Scans (placeholder)
                Text(
                  'Ultimi scansionamenti',
                  style: AppTypography.headline3,
                ),
                const SizedBox(height: 16),

                // Empty state
                Container(
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: AppColors.lightGrey,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.borderGrey),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.history,
                        size: 48,
                        color: AppColors.mediumGrey,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Nessuno scansionamento ancora',
                        style: AppTypography.bodyMedium,
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => context.go('/scanner'),
                        child: const Text('Inizia il primo scan'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
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
