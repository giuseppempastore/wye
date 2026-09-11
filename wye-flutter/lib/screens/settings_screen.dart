import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Impostazioni'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Preferenze locali',
                style: AppTypography.headline3,
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Consumer<UserPreferencesProvider>(
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
                            'Paese di residenza',
                            style: AppTypography.bodyLarge,
                          ),
                          const SizedBox(height: 8),
                          DropdownButtonFormField<String>(
                            initialValue: countryValue,
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
                              if (value != null) userPref.setCountry(value);
                            },
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Il paese selezionato sarà usato come riferimento nel flusso di scansione.',
                            style: AppTypography.bodySmall,
                          ),
                        ],
                      );
                    },
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Allergens Section
              Text(
                'Mie Allergie',
                style: AppTypography.headline3,
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Consumer<UserPreferencesProvider>(
                    builder: (context, userPref, _) {
                      final allergens = [
                        'Glutine',
                        'Latte',
                        'Uova',
                        'Arachidi',
                        'Noci',
                        'Soia',
                        'Sesamo',
                        'Pesce',
                      ];

                      if (userPref.userAllergies.isEmpty) {
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Nessuna allergia registrata',
                              style: AppTypography.bodyMedium,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Seleziona le tue allergie per ricevere notifiche personalizzate',
                              style: AppTypography.bodySmall,
                            ),
                          ],
                        );
                      }

                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              for (String allergen in userPref.userAllergies)
                                Chip(
                                  label: Text(allergen),
                                  onDeleted: () {
                                    userPref.removeAllergy(allergen);
                                  },
                                  deleteIcon: const Icon(Icons.close, size: 18),
                                  backgroundColor:
                                      AppColors.riskHigh.withValues(alpha: 0.1),
                                  labelStyle: TextStyle(
                                    color: AppColors.riskHigh,
                                  ),
                                ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: () => _showAllergySelector(
                              context,
                              allergens,
                              userPref,
                            ),
                            child: const Text('Aggiungi Allergia'),
                          ),
                        ],
                      );
                    },
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Language Section
              Text(
                'Lingua',
                style: AppTypography.headline3,
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Consumer<UserPreferencesProvider>(
                    builder: (context, userPref, _) {
                      return DropdownButtonFormField<String>(
                        initialValue: userPref.language,
                        decoration: InputDecoration(
                          prefixIcon: const Icon(Icons.language),
                        ),
                        items: [
                          const DropdownMenuItem(
                            value: 'it',
                            child: Text('Italiano'),
                          ),
                          const DropdownMenuItem(
                            value: 'en',
                            child: Text('English'),
                          ),
                          const DropdownMenuItem(
                            value: 'fr',
                            child: Text('Français'),
                          ),
                        ],
                        onChanged: (value) {
                          if (value != null) {
                            userPref.setLanguage(value);
                          }
                        },
                      );
                    },
                  ),
                ),
              ),
              const SizedBox(height: 24),

              Text('Beta test', style: AppTypography.headline3),
              const SizedBox(height: 12),
              Card(
                child: ListTile(
                  key: const ValueKey('open-beta-feedback'),
                  leading: const Icon(Icons.feedback_outlined),
                  title: const Text('Lascia feedback'),
                  subtitle: const Text(
                    'Segnala un problema o proponi un miglioramento.',
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/feedback'),
                ),
              ),
              const SizedBox(height: 24),

              // App Info Section
              Text(
                'Info App',
                style: AppTypography.headline3,
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Versione', style: AppTypography.bodyMedium),
                          Text('1.0.0', style: AppTypography.label),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Divider(color: AppColors.borderGrey),
                      const SizedBox(height: 12),
                      GestureDetector(
                        onTap: () {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Apri privacy policy'),
                            ),
                          );
                        },
                        child: Text(
                          'Privacy Policy',
                          style: AppTypography.bodyLarge.copyWith(
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      GestureDetector(
                        onTap: () {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Apri termini di servizio'),
                            ),
                          );
                        },
                        child: Text(
                          'Termini di Servizio',
                          style: AppTypography.bodyLarge.copyWith(
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 32),

              // Logout
              OutlinedButton.icon(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Logout non implementato (demo)'),
                    ),
                  );
                },
                icon: const Icon(Icons.logout),
                label: const Text('Esci'),
              ),
              const SizedBox(height: 24),
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
        currentIndex: 2,
        onTap: (index) {
          switch (index) {
            case 0:
              context.go('/');
              break;
            case 1:
              context.go('/history');
              break;
            case 2:
              // Già su impostazioni
              break;
          }
        },
      ),
    );
  }

  void _showAllergySelector(
    BuildContext context,
    List<String> allergens,
    UserPreferencesProvider userPref,
  ) {
    showModalBottomSheet(
      context: context,
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Seleziona Allergie',
                style: AppTypography.headline3,
              ),
              const SizedBox(height: 16),
              Expanded(
                child: ListView.builder(
                  itemCount: allergens.length,
                  itemBuilder: (context, index) {
                    final allergen = allergens[index];
                    final isSelected =
                        userPref.userAllergies.contains(allergen);

                    return ListTile(
                      title: Text(allergen),
                      trailing: Checkbox(
                        value: isSelected,
                        onChanged: (value) {
                          if (value == true) {
                            userPref.addAllergy(allergen);
                          } else {
                            userPref.removeAllergy(allergen);
                          }
                        },
                      ),
                      onTap: () {
                        if (isSelected) {
                          userPref.removeAllergy(allergen);
                        } else {
                          userPref.addAllergy(allergen);
                        }
                      },
                    );
                  },
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Fatto'),
              ),
            ],
          ),
        );
      },
    );
  }
}
