import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'router/app_router.dart';
import 'theme/app_theme.dart';
import 'services/api_client.dart';
import 'services/database_service.dart';
import 'providers/app_providers.dart';

void main() async {
  // Inizializza database
  final db = DatabaseService();
  await db.init();

  runApp(WyeApp(databaseService: db));
}

class WyeApp extends StatefulWidget {
  final DatabaseService databaseService;

  const WyeApp({Key? key, required this.databaseService}) : super(key: key);

  @override
  State<WyeApp> createState() => _WyeAppState();
}

class _WyeAppState extends State<WyeApp> {
  @override
  void dispose() {
    widget.databaseService.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // API Client
        Provider<ApiClient>(create: (_) => ApiClient()),

        // Database Service
        Provider<DatabaseService>(create: (_) => widget.databaseService),

        // App State
        ChangeNotifierProvider(create: (_) => AppStateProvider()),

        // User Preferences
        ChangeNotifierProvider(create: (_) => UserPreferencesProvider()),

        // Barcode Scanner (dipende da ApiClient)
        ChangeNotifierProvider(
          create: (context) =>
              BarcodeScannerProvider(context.read<ApiClient>()),
        ),
      ],
      child: MaterialApp.router(
        title: 'WYE - Product Safety Score',
        theme: AppTheme.lightTheme,
        routerConfig: AppRouter.router,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
