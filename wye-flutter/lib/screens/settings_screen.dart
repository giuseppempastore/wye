import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../config/mobile_upload_config.dart';
import '../theme/app_theme.dart';
import '../providers/app_providers.dart';
import '../widgets/dev_mobile_upload_widgets.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    final mobileUploadEnabled = context.watch<MobileUploadConfig>().enabled;
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
              // Profile Section
              Text(
                'Profilo',
                style: AppTypography.headline3,
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Consumer<UserPreferencesProvider>(
                        builder: (context, userPref, _) {
                          return Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'Account Premium',
                                    style: AppTypography.bodyLarge,
                                  ),
                                  Switch(
                                    value: userPref.isPremium,
                                    onChanged: (value) {
                                      userPref.setPremium(value);
                                    },
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              if (!userPref.isPremium)
                                ElevatedButton.icon(
                                  onPressed: () {
                                    userPref.setPremium(true);
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                        content: Text(
                                          'Modalità Premium attivata!',
                                        ),
                                        backgroundColor: AppColors.success,
                                        duration: Duration(seconds: 2),
                                      ),
                                    );
                                  },
                                  icon: const Icon(Icons.star),
                                  label: const Text('Attiva Premium'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppColors.accent,
                                  ),
                                )
                              else
                                Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: AppColors.accent.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(
                                      color: AppColors.accent,
                                    ),
                                  ),
                                  child: Row(
                                    children: [
                                      const Icon(
                                        Icons.verified,
                                        color: AppColors.accent,
                                        size: 20,
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        'Sei un utente Premium',
                                        style: AppTypography.label,
                                      ),
                                    ],
                                  ),
                                ),
                            ],
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Premium country + fact-check section
              Text(
                'Premium e sicurezza',
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
                            value: countryValue,
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
                            onChanged: userPref.isPremium
                                ? (value) {
                                    if (value != null) {
                                      userPref.setCountry(value);
                                    }
                                  }
                                : null,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            userPref.isPremium
                                ? 'Il paese selezionato sarà usato come riferimento nel flusso di scansione.'
                                : 'Questa sezione è disponibile solo per utenti premium.',
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
                                      AppColors.riskHigh.withOpacity(0.1),
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
                        value: userPref.language,
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

              if (mobileUploadEnabled) ...[
                Text(
                  'Upload mobile - sviluppo',
                  style: AppTypography.headline3,
                ),
                const SizedBox(height: 12),
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: DevMobileUploadTokenPanel(),
                  ),
                ),
                const SizedBox(height: 24),
              ],

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
