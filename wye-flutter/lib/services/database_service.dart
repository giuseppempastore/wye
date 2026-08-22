import 'package:hive_flutter/hive_flutter.dart';
import '../models/product_model.dart';
import 'package:logger/logger.dart';

class DatabaseService {
  static const String productsBoxName = 'products';
  static const String historyBoxName = 'scan_history';
  
  late Box<String> _productsBox;
  late Box<String> _historyBox;
  final Logger _logger = Logger();

  /// Inizializza il database
  Future<void> init() async {
    try {
      _logger.i('🗄️ Initializing Hive database...');
      
      await Hive.initFlutter();
      
      _productsBox = await Hive.openBox<String>(productsBoxName);
      _historyBox = await Hive.openBox<String>(historyBoxName);
      
      _logger.i('✅ Database initialized');
    } catch (e) {
      _logger.e('❌ Database init error: $e');
      rethrow;
    }
  }

  /// Salva un prodotto nella cache
  Future<void> saveProduct(Product product) async {
    try {
      _logger.i('💾 Saving product: ${product.barcode}');
      
      final json = _productToJson(product);
      await _productsBox.put(product.barcode, json);
      
      _logger.d('✅ Product cached: ${product.barcode}');
    } catch (e) {
      _logger.e('❌ Save product error: $e');
    }
  }

  /// Recupera un prodotto dalla cache
  Product? getProduct(String barcode) {
    try {
      _logger.d('🔍 Getting product from cache: $barcode');
      
      final json = _productsBox.get(barcode);
      if (json == null) {
        _logger.d('⚠️ Product not in cache: $barcode');
        return null;
      }
      
      final product = _jsonToProduct(json);
      _logger.d('✅ Product from cache: $barcode');
      return product;
    } catch (e) {
      _logger.e('❌ Get product error: $e');
      return null;
    }
  }

  /// Salva storico scansione
  Future<void> addToHistory(ScanHistory scan) async {
    try {
      _logger.i('📝 Adding to history: ${scan.barcode}');
      
      final key = '${scan.barcode}_${scan.scannedAt.millisecondsSinceEpoch}';
      final json = _historyToJson(scan);
      await _historyBox.put(key, json);
      
      _logger.d('✅ History added');
    } catch (e) {
      _logger.e('❌ Add to history error: $e');
    }
  }

  /// Recupera storico completo
  List<ScanHistory> getHistory() {
    try {
      _logger.d('📖 Getting scan history');
      
      final history = _historyBox.values
          .map((json) => _jsonToHistory(json))
          .toList();
      
      // Ordina per data più recente
      history.sort((a, b) => b.scannedAt.compareTo(a.scannedAt));
      
      _logger.d('✅ History loaded: ${history.length} items');
      return history;
    } catch (e) {
      _logger.e('❌ Get history error: $e');
      return [];
    }
  }

  /// Pulisci un elemento dallo storico
  Future<void> removeFromHistory(String barcode) async {
    try {
      _logger.i('🗑️ Removing from history: $barcode');
      
      final keysToRemove = _historyBox.keys
          .where((key) => key.toString().startsWith(barcode))
          .toList();
      
      await _historyBox.deleteAll(keysToRemove);
      
      _logger.d('✅ Removed ${keysToRemove.length} items');
    } catch (e) {
      _logger.e('❌ Remove from history error: $e');
    }
  }

  /// Pulisci tutta la cache
  Future<void> clearAll() async {
    try {
      _logger.w('🧹 Clearing all cache');
      
      await _productsBox.clear();
      await _historyBox.clear();
      
      _logger.i('✅ Cache cleared');
    } catch (e) {
      _logger.e('❌ Clear cache error: $e');
    }
  }

  /// Ottieni statistiche cache
  Map<String, dynamic> getCacheStats() {
    return {
      'products_cached': _productsBox.length,
      'history_items': _historyBox.length,
      'last_updated': DateTime.now().toIso8601String(),
    };
  }

  /// Conversione Product → JSON string
  String _productToJson(Product product) {
    return product.toJson().toString();
  }

  /// Conversione JSON string → Product
  Product _jsonToProduct(String jsonString) {
    // Parse il toString della Map
    final mapString = jsonString;
    // In production, userai json.decode() qui
    // Per ora, ripassa il prodotto originale
    throw UnimplementedError(
      'Implementare serializzazione: usa json.decode(jsonString)',
    );
  }

  /// Conversione ScanHistory → JSON string
  String _historyToJson(ScanHistory scan) {
    return scan.toJson().toString();
  }

  /// Conversione JSON string → ScanHistory
  ScanHistory _jsonToHistory(String jsonString) {
    throw UnimplementedError(
      'Implementare serializzazione: usa json.decode(jsonString)',
    );
  }

  /// Chiudi database
  Future<void> close() async {
    try {
      _logger.i('🔌 Closing database...');
      await Hive.close();
      _logger.i('✅ Database closed');
    } catch (e) {
      _logger.e('❌ Close database error: $e');
    }
  }
}
