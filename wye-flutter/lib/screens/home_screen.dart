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
        title: Text(
          'WYE',
          style: AppTypography.headline2.copyWith(
            color: AppColors.primary,
            letterSpacing: 1.5,
          ),
        ),
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
                  height: 180,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.15),
                        blurRadius: 12,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Stack(
                      children: [
                        Positioned.fill(
                          child: Image.asset(
                            'img/What_you_eatin_theme_upd_1.jpg',
                            fit: BoxFit.cover,
                          ),
                        ),
                        Positioned.fill(
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.bottomCenter,
                                end: Alignment.topCenter,
                                colors: [
                                  Colors.black.withOpacity(0.6),
                                  Colors.transparent,
                                ],
                              ),
                            ),
                          ),
                        ),
                        Positioned.fill(
                          child: Container(),
                        ),
                      ],
                    ),
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
                const SizedBox(height: 12),

                // Button: Add product from photo / extracted data
                OutlinedButton.icon(
                  onPressed: () => context.go('/add-product'),
                  icon: const Icon(Icons.add_photo_alternate_rounded),
                  label: const Text('Aggiungi Prodotto da Foto'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
                const SizedBox(height: 32),

                // Info Cards
                Theme(
                  data: Theme.of(context).copyWith(
                    dividerColor: Colors.transparent,
                  ),
                  child: ExpansionTile(
                    initiallyExpanded: false,
                    title: Text(
                      'Come funziona',
                      style: AppTypography.headline3,
                    ),
                    tilePadding: EdgeInsets.zero,
                    childrenPadding: const EdgeInsets.only(top: 8),
                    children: [
                      InfoSection(
                        icon: Icons.explore,
                        title: 'Valutazione trasparente',
                        description:
                            'Scopri la salubrità di ogni prodotto basato su ingredienti e nutrizione.',
                        iconColor: AppColors.primary,
                      ),
                      const SizedBox(height: 12),
                      InfoSection(
                        icon: Icons.warning,
                        title: 'Allergeni e rischi',
                        description:
                            'Identifichiamo ingredienti critici e allergeni potenziali.',
                        iconColor: AppColors.riskHigh,
                      ),
                      const SizedBox(height: 12),
                      InfoSection(
                        icon: Icons.trending_up,
                        title: 'Scoring dettagliato',
                        description:
                            'Vedi come ingredienti e nutrizione influenzano il punteggio finale.',
                        iconColor: AppColors.secondary,
                      ),
                    ],
                  ),
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
