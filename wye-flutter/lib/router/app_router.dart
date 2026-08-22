import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../screens/home_screen.dart';
import '../screens/barcode_scanner_screen.dart';
import '../screens/product_detail_screen.dart';
import '../screens/manual_analysis_screen.dart';
import '../screens/history_screen.dart';
import '../screens/settings_screen.dart';

class AppRouter {
  static final GoRouter router = GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
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
        path: '/manual-analysis',
        name: 'manual_analysis',
        builder: (context, state) => const ManualAnalysisScreen(),
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
