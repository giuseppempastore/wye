import 'dart:convert';
import 'dart:io';

import 'package:hive_flutter/hive_flutter.dart';
import '../models/product_model.dart';
import '../models/product_acquisition_draft.dart';
import 'package:logger/logger.dart';

class DatabaseService {
  static const String productsBoxName = 'products';
  static const String historyBoxName = 'scan_history';
  static const String acquisitionDraftsBoxName = 'product_acquisition_drafts';
  static const String activeAcquisitionDraftKey = 'active_draft_id';

  late Box<String> _productsBox;
  late Box<String> _historyBox;
  late Box<String> _acquisitionDraftsBox;
  final Logger _logger = Logger();
  final String? hivePath;

  DatabaseService({this.hivePath});

  /// Inizializza il database
  Future<void> init() async {
    try {
      _logger.i('🗄️ Initializing Hive database...');

      if (hivePath == null) {
        await Hive.initFlutter();
      } else {
        Hive.init(hivePath!);
      }

      _productsBox = await Hive.openBox<String>(productsBoxName);
      _historyBox = await Hive.openBox<String>(historyBoxName);
      _acquisitionDraftsBox =
          await Hive.openBox<String>(acquisitionDraftsBoxName);

      _logger.i('✅ Database initialized');
    } catch (e) {
      _logger.e('❌ Database init error: $e');
      rethrow;
    }
  }

  /// Salva un prodotto nella cache
  Future<void> saveProduct(Product product) async {
    try {
      _logger.i('Saving product locally');

      final json = _productToJson(product);
      await _productsBox.put(product.barcode, json);

      _logger.d('Product cached');
    } catch (e) {
      _logger.e('❌ Save product error: $e');
    }
  }

  /// Recupera un prodotto dalla cache
  Product? getProduct(String barcode) {
    try {
      _logger.d('Getting product from cache');

      final json = _productsBox.get(barcode);
      if (json == null) {
        _logger.d('Product not in cache');
        return null;
      }

      final product = _jsonToProduct(json);
      _logger.d('Product found in cache');
      return product;
    } catch (e) {
      _logger.e('❌ Get product error: $e');
      return null;
    }
  }

  /// Salva storico scansione
  Future<void> addToHistory(ScanHistory scan) async {
    try {
      _logger.i('Adding product to local history');

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

      final history =
          _historyBox.values.map((json) => _jsonToHistory(json)).toList();

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
      _logger.i('Removing product from history');

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
      'acquisition_drafts': _acquisitionDraftsBox.values
          .where((value) => value.startsWith('{'))
          .length,
      'last_updated': DateTime.now().toIso8601String(),
    };
  }

  /// Conversione Product → JSON string
  String _productToJson(Product product) {
    return jsonEncode(product.toJson());
  }

  /// Conversione JSON string → Product
  Product _jsonToProduct(String jsonString) {
    return Product.fromJson(jsonDecode(jsonString) as Map<String, dynamic>);
  }

  /// Conversione ScanHistory → JSON string
  String _historyToJson(ScanHistory scan) {
    return jsonEncode(scan.toJson());
  }

  /// Conversione JSON string → ScanHistory
  ScanHistory _jsonToHistory(String jsonString) {
    return ScanHistory.fromJson(
      jsonDecode(jsonString) as Map<String, dynamic>,
    );
  }

  Future<void> saveAcquisitionDraft(ProductAcquisitionDraft draft) async {
    await _acquisitionDraftsBox.put(draft.id, jsonEncode(draft.toJson()));
    await _acquisitionDraftsBox.put(activeAcquisitionDraftKey, draft.id);
  }

  ProductAcquisitionDraft? getActiveAcquisitionDraft() {
    final id = _acquisitionDraftsBox.get(activeAcquisitionDraftKey);
    if (id == null || id.isEmpty) return null;
    final encoded = _acquisitionDraftsBox.get(id);
    if (encoded == null) return null;
    try {
      return ProductAcquisitionDraft.fromJson(
        jsonDecode(encoded) as Map<String, dynamic>,
      );
    } on Object catch (error) {
      _logger.w('Invalid acquisition draft ignored: ${error.runtimeType}');
      return null;
    }
  }

  List<ProductAcquisitionDraft> getAcquisitionDrafts() {
    final drafts = <ProductAcquisitionDraft>[];
    for (final entry in _acquisitionDraftsBox.toMap().entries) {
      if (entry.key == activeAcquisitionDraftKey) continue;
      try {
        drafts.add(ProductAcquisitionDraft.fromJson(
          jsonDecode(entry.value) as Map<String, dynamic>,
        ));
      } on Object {
        // A corrupt local entry must not hide the remaining history.
      }
    }
    drafts.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    return drafts;
  }

  Future<String> retainDraftImage({
    required String draftId,
    required String documentType,
    required String sourcePath,
  }) async {
    final source = File(sourcePath);
    if (!await source.exists()) {
      throw const FileSystemException('Photo missing');
    }
    final boxPath = _acquisitionDraftsBox.path;
    if (boxPath == null) {
      throw const FileSystemException('Hive path unavailable');
    }
    final directory = Directory(
        '${File(boxPath).parent.path}${Platform.pathSeparator}wye_drafts${Platform.pathSeparator}$draftId');
    await directory.create(recursive: true);
    final extension =
        source.path.toLowerCase().endsWith('.png') ? 'png' : 'jpg';
    final destination = File(
        '${directory.path}${Platform.pathSeparator}$documentType.$extension');
    if (await destination.exists()) {
      await destination.delete();
    }
    await source.copy(destination.path);
    return destination.path;
  }

  Future<void> deleteAcquisitionDraft(String draftId) async {
    final encoded = _acquisitionDraftsBox.get(draftId);
    if (encoded != null) {
      try {
        final draft = ProductAcquisitionDraft.fromJson(
          jsonDecode(encoded) as Map<String, dynamic>,
        );
        for (final path in draft.localImagePaths.values) {
          final file = File(path);
          if (await file.exists()) await file.delete();
        }
        if (draft.localImagePaths.isNotEmpty) {
          final parent = File(draft.localImagePaths.values.first).parent;
          if (await parent.exists()) await parent.delete(recursive: true);
        }
      } on Object catch (error) {
        _logger.w('Draft media cleanup incomplete: ${error.runtimeType}');
      }
    }
    await _acquisitionDraftsBox.delete(draftId);
    if (_acquisitionDraftsBox.get(activeAcquisitionDraftKey) == draftId) {
      await _acquisitionDraftsBox.delete(activeAcquisitionDraftKey);
    }
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
