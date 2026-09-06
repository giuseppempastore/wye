import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'config/mobile_upload_config.dart';
import 'models/capture_upload_models.dart';
import 'router/app_router.dart';
import 'theme/app_theme.dart';
import 'services/api_client.dart';
import 'services/capture_flow_logger.dart';
import 'services/capture_upload_gateway.dart';
import 'services/http_capture_upload_gateway.dart';
import 'services/image_metadata_service.dart';
import 'services/logging_capture_upload_gateway.dart';
import 'services/database_service.dart';
import 'services/photo_capture_recovery_service.dart';
import 'providers/app_providers.dart';
import 'providers/capture_upload_controller.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await PhotoCaptureRecoveryService.shared.initialize();
  final initialLocation = PhotoCaptureRecoveryService.shared.hasRecoveredPhoto
      ? '/add-product'
      : '/';
  // Inizializza database
  final db = DatabaseService();
  await db.init();

  runApp(
    WyeApp(databaseService: db, initialLocation: initialLocation),
  );
}

class WyeApp extends StatefulWidget {
  final DatabaseService databaseService;
  final String initialLocation;

  const WyeApp({
    Key? key,
    required this.databaseService,
    this.initialLocation = '/',
  }) : super(key: key);

  @override
  State<WyeApp> createState() => _WyeAppState();
}

class _WyeAppState extends State<WyeApp> {
  late final MobileUploadConfig _mobileUploadConfig;
  late final SanitizedInMemoryCaptureFlowLogger _captureFlowLogger;
  final InMemoryMobileUploadTokenProvider _mobileTokenProvider =
      InMemoryMobileUploadTokenProvider();
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    _mobileUploadConfig = MobileUploadConfig.fromEnvironment(
      apiBaseUrl: ApiConfig.baseUrl,
    );
    _captureFlowLogger = SanitizedInMemoryCaptureFlowLogger(
      enabled: _mobileUploadConfig.enabled,
      capacity: 200,
    );
    _router = AppRouter.createRouter(initialLocation: widget.initialLocation);
  }

  @override
  void dispose() {
    _mobileTokenProvider.clear();
    _captureFlowLogger.dispose();
    _router.dispose();
    widget.databaseService.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // API Client
        Provider<ApiClient>(
          create: (_) => ApiClient(
            mobileTokenProvider: _mobileTokenProvider,
          ),
        ),

        Provider<MobileUploadConfig>.value(value: _mobileUploadConfig),
        Provider<InMemoryMobileUploadTokenProvider>.value(
          value: _mobileTokenProvider,
        ),
        ChangeNotifierProvider<SanitizedInMemoryCaptureFlowLogger>.value(
          value: _captureFlowLogger,
        ),
        Provider<CaptureUploadGateway>(
          create: (_) => LoggingCaptureUploadGateway(
            delegate: HttpCaptureUploadGateway(
              client: http.Client(),
              config: _mobileUploadConfig,
              tokenProvider: _mobileTokenProvider,
              logger: _captureFlowLogger,
            ),
            logger: _captureFlowLogger,
          ),
          dispose: (_, gateway) => gateway.close(),
        ),
        Provider<ImageMetadataService>.value(
          value: const Sha256ImageMetadataService(),
        ),

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

        ChangeNotifierProvider(
          create: (context) => CaptureUploadController(
            config: _mobileUploadConfig,
            tokenProvider: _mobileTokenProvider,
            gateway: context.read<CaptureUploadGateway>(),
            metadataService: context.read<ImageMetadataService>(),
            logger: _captureFlowLogger,
          ),
        ),
      ],
      child: MaterialApp.router(
        title: 'WYE',
        theme: AppTheme.lightTheme,
        routerConfig: _router,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
