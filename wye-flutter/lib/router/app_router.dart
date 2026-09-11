import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../screens/home_v2_screen.dart';
import '../screens/barcode_scanner_screen.dart';
import '../screens/product_detail_screen.dart';
import '../screens/add_product_screen.dart';
import '../screens/history_screen.dart';
import '../screens/settings_screen.dart';
import '../screens/instant_label_analysis_screen.dart';
import '../screens/add_product_options_screen.dart';
import '../screens/beta_feedback_screen.dart';

class AppRouter {
  static GoRouter createRouter({String initialLocation = '/'}) => GoRouter(
        initialLocation: initialLocation,
        routes: [
          GoRoute(
            path: '/',
            name: 'home',
            builder: (context, state) => const AcquisitionHomeScreen(),
          ),
          GoRoute(
            path: '/scanner',
            name: 'scanner',
            builder: (context, state) => const BarcodeScannerScreen(),
          ),
          GoRoute(
            path: '/product/:barcode',
            name: 'product_detail',
            builder: (context, state) {
              final barcode = state.pathParameters['barcode']!;
              return ProductDetailScreen(barcode: barcode);
            },
          ),
          GoRoute(
            path: '/add-product',
            name: 'add_product',
            builder: (context, state) => const AddProductOptionsScreen(),
          ),
          GoRoute(
            path: '/register-product',
            name: 'register_product',
            builder: (context, state) => const AddProductScreen(),
          ),
          GoRoute(
            path: '/history',
            name: 'history',
            builder: (context, state) => const HistoryScreen(),
          ),
          GoRoute(
            path: '/settings',
            name: 'settings',
            builder: (context, state) => const SettingsScreen(),
          ),
          GoRoute(
            path: '/instant-label-analysis',
            name: 'instant_label_analysis',
            builder: (context, state) => const InstantLabelAnalysisScreen(),
          ),
          GoRoute(
            path: '/feedback',
            name: 'beta_feedback',
            builder: (context, state) => const BetaFeedbackScreen(),
          ),
        ],
        errorBuilder: (context, state) => Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('404 - Pagina non trovata'),
                ElevatedButton(
                  onPressed: () => context.go('/'),
                  child: const Text('Torna alla home'),
                ),
              ],
            ),
          ),
        ),
      );
}
