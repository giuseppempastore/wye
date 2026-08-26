import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:logger/logger.dart';
import 'package:flutter/foundation.dart';
import '../models/product_model.dart';
class ApiConfig {
  // Override opzionale:
  // flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
  static const String _apiBaseUrlOverride =
      String.fromEnvironment('API_BASE_URL', defaultValue: '');

  static String get baseUrl {
    if (_apiBaseUrlOverride.isNotEmpty) {
      return _apiBaseUrlOverride;
    }

    // Web app in browser: il backend locale del PC è localhost/127.0.0.1
    if (kIsWeb) {
      return 'http://127.0.0.1:8000';
    }

    // Android emulator
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8000';
    }

    // iOS simulator / desktop locale
    return 'http://127.0.0.1:8000';
  }

  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
}

class ApiClient {
  final Logger _logger = Logger();
  late http.Client _client;

  ApiClient() {
    _client = http.Client();
  }

  /// Fetch prodotto da barcode
  Future<Product> getProductByBarcode(String barcode) async {
    try {
      _logger.i('📦 Fetching product for barcode: $barcode');

      final response = await _client
          .get(
            Uri.parse('${ApiConfig.baseUrl}/product/$barcode'),
          )
          .timeout(ApiConfig.connectionTimeout, onTimeout: () {
        throw TimeoutException(
            'Backend non risponde. Verifica la connessione.');
      });

      _logger.d('Response status: ${response.statusCode}');
      _logger.d('Response body: ${response.body}');

      if (response.statusCode == 200) {
        try {
          final jsonData = jsonDecode(response.body) as Map<String, dynamic>;

          // Caso backend: prodotto non trovato nel DB
          if (jsonData['error'] == 'not_found') {
            throw ProductNotFoundException(
              'Prodotto non trovato nel database. Prova a inserirlo manualmente nella sezione Premium.',
            );
          }

          // Caso backend DB: { product, score, ingredients }
          if (jsonData.containsKey('product')) {
            final product = _mapDbProductResponse(jsonData, barcode);
            _logger.i('✅ Product found: ${product.productName}');
            return product;
          }

          // Caso API già nel formato app
          final product = Product.fromJson(jsonData);
          _logger.i('✅ Product found: ${product.productName}');
          return product;
        } on ProductNotFoundException {
          rethrow;
        } catch (e) {
          _logger.e('❌ JSON parse error: $e');
          throw ApiException('Errore nel parsing della risposta del server');
        }
      } else if (response.statusCode == 404) {
        _logger.w('⚠️ Product not found: $barcode');
        throw ProductNotFoundException(
            'Prodotto non trovato nel database. Prova a inserirlo manualmente nella sezione Premium.');
      } else if (response.statusCode >= 500) {
        _logger.e('❌ Server error: ${response.statusCode}');
        throw ApiException('Errore del server. Riprova tra poco.');
      } else {
        _logger.e('❌ Error: ${response.statusCode} - ${response.body}');
        throw ApiException(
            'Errore nel recupero del prodotto (${response.statusCode})');
      }
    } on ProductNotFoundException {
      rethrow;
    } on SocketException {
      _logger.e('❌ Network error - impossible to reach backend');
      throw NetworkException(
        'Impossibile raggiungere il server. Verifica che:\n'
        '1. Il backend Python è in esecuzione\n'
        '2. L\'indirizzo IP/URL è corretto\n'
        '3. Sei sulla stessa rete',
      );
    } on TimeoutException catch (e) {
      _logger.e('❌ Timeout: $e');
      throw NetworkException(e.message ?? 'Timeout della richiesta');
    } catch (e) {
      _logger.e('❌ Unexpected exception: $e');
      rethrow;
    }
  }

  Future<Product> createProduct({
    required String barcode,
    required String brandName,
    required String productName,
    required String category,
    required String productType,
    required String ingredients,
    Map<String, dynamic>? nutritionFacts,
    String source = 'photo_submission',
    String? imageUrl,
    String? ingredientImageUrl,
    String? nutritionImageUrl,
  }) async {
    try {
      final payload = {
        'barcode': barcode.trim(),
        'brand_name': brandName.trim(),
        'product_name': productName.trim(),
        'category': category.trim(),
        'product_type': productType.trim(),
        'ingredients': ingredients,
        'nutrition': nutritionFacts ?? {},
        'source': source,
        if (imageUrl != null && imageUrl.trim().isNotEmpty) 'image_url': imageUrl.trim(),
        if (ingredientImageUrl != null && ingredientImageUrl.trim().isNotEmpty) 'ingredient_image_url': ingredientImageUrl.trim(),
        if (nutritionImageUrl != null && nutritionImageUrl.trim().isNotEmpty) 'nutrition_image_url': nutritionImageUrl.trim(),
      };

      final response = await _client
          .post(
            Uri.parse('${ApiConfig.baseUrl}/products'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(ApiConfig.connectionTimeout, onTimeout: () {
            throw TimeoutException('Creazione prodotto timeout - riprova');
          });

      if (response.statusCode == 200 || response.statusCode == 201) {
        final jsonData = jsonDecode(response.body) as Map<String, dynamic>;
        final productData = jsonData['product'] as Map<String, dynamic>? ?? {};

        if (productData.isEmpty) {
          throw ApiException('Risposta del server vuota durante la creazione prodotto');
        }

        final product = Product.fromJson(productData);
        _logger.i('✅ Product created: ${product.productName}');
        return product;
      }

      throw ApiException(
          'Errore nella creazione prodotto (${response.statusCode}): ${response.body}');
    } on SocketException {
      _logger.e('❌ Network error while creating product');
      throw NetworkException(
          'Impossibile raggiungere il server. Verifica che il backend sia attivo.');
    } on TimeoutException catch (e) {
      _logger.e('❌ Timeout while creating product: $e');
      throw NetworkException(e.message ?? 'Timeout della creazione prodotto');
    } catch (e) {
      _logger.e('❌ Exception creating product: $e');
      rethrow;
    }
  }

  /// Analizza ingredienti manuali (premium feature)
  Future<Product> analyzeIngredients({
    required String productName,
    required String ingredients,
    required String language,
    String? category,
  }) async {
    try {
      _logger.i('🔬 Analyzing ingredients for: $productName');

      final payload = {
        'product_name': productName,
        'ingredients': ingredients,
        'language': language,
        if (category != null) 'category': category,
      };

      _logger.d('Payload: $payload');

      final response = await _client
          .post(
            Uri.parse('${ApiConfig.baseUrl}/analyze'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(ApiConfig.connectionTimeout, onTimeout: () {
        throw TimeoutException('Analisi timeout - riprova');
      });

      _logger.d('Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        try {
          final jsonData = jsonDecode(response.body) as Map<String, dynamic>;

          // Caso backend scoring.py: ritorna score/verdict/warnings
          if (jsonData.containsKey('score') &&
              !jsonData.containsKey('final_score')) {
            final product = _mapAnalyzeResponseToProduct(jsonData);
            _logger.i('✅ Analysis complete: ${product.finalScore}');
            return product;
          }

          // Caso API già nel formato app
          final product = Product.fromJson(jsonData);
          _logger.i('✅ Analysis complete: ${product.finalScore}');
          return product;
        } catch (e) {
          _logger.e('❌ JSON parse error: $e');
          throw ApiException('Errore nel parsing della risposta');
        }
      } else if (response.statusCode == 400) {
        _logger.e('❌ Bad request: ${response.body}');
        throw ApiException('Dati non validi. Controlla gli ingredienti inseriti.');
      } else {
        throw ApiException(
            'Errore nell\'analisi (${response.statusCode}): ${response.body}');
      }
    } on SocketException {
      _logger.e('❌ Network error');
      throw NetworkException(
          'Errore di connessione. Controlla la rete e riprova.');
    } catch (e) {
      _logger.e('❌ Exception: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> normalizePhotoText({
    required String rawText,
  }) async {
    try {
      final response = await _client
          .post(
            Uri.parse('${ApiConfig.baseUrl}/normalize-photo'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'raw_text': rawText}),
          )
          .timeout(ApiConfig.connectionTimeout, onTimeout: () {
            throw TimeoutException('Normalizzazione OCR timeout - riprova');
          });

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body) as Map<String, dynamic>;
        return {
          'ingredients': jsonData['ingredients'] ?? const [],
          'nutrition': jsonData['nutrition'] ?? const {},
          'product_name': jsonData['product_name'] ?? jsonData['name'] ?? '',
          'brand_name': jsonData['brand_name'] ?? jsonData['brand'] ?? '',
          'category': jsonData['category'] ?? 'food',
          'product_type': jsonData['product_type'] ?? jsonData['type'] ?? 'snack',
        };
      }

      throw ApiException(
          'Errore nella normalizzazione foto (${response.statusCode}): ${response.body}');
    } on SocketException {
      throw NetworkException(
          'Impossibile raggiungere il server. Verifica che il backend sia attivo.');
    } on TimeoutException catch (e) {
      throw NetworkException(e.message ?? 'Timeout della normalizzazione foto');
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> analyzeProductImage({
    required String imageUrl,
    String? rawText,
  }) async {
    try {
      _logger.i('📤 POST ${ApiConfig.baseUrl}/analyze-image');
      _logger.d('Payload: imageUrl length=${imageUrl.length}, rawText length=${rawText?.length ?? 0}');
      final response = await _client
          .post(
            Uri.parse('${ApiConfig.baseUrl}/analyze-image'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'image_url': imageUrl,
              if (rawText != null && rawText.trim().isNotEmpty) 'raw_text': rawText,
            }),
          )
          .timeout(ApiConfig.connectionTimeout, onTimeout: () {
            throw TimeoutException('Analisi immagine timeout - riprova');
          });

      _logger.i('Response status: ${response.statusCode}');
      _logger.d('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body) as Map<String, dynamic>;
        return {
          'ingredients': jsonData['ingredients'] ?? const [],
          'nutrition': jsonData['nutrition'] ?? const {},
          'product_name': jsonData['product_name'] ?? jsonData['name'] ?? '',
          'brand_name': jsonData['brand_name'] ?? jsonData['brand'] ?? '',
          'category': jsonData['category'] ?? 'food',
          'product_type': jsonData['product_type'] ?? jsonData['type'] ?? 'snack',
        };
      }

      throw ApiException(
          'Errore nell\'analisi immagine (${response.statusCode}): ${response.body}');
    } on SocketException {
      throw NetworkException(
          'Impossibile raggiungere il server. Verifica che il backend sia attivo.');
    } on TimeoutException catch (e) {
      throw NetworkException(e.message ?? 'Timeout dell\'analisi immagine');
    } catch (e) {
      rethrow;
    }
  }

  /// Health check del backend
  Future<bool> healthCheck() async {
    try {
      _logger.i('🏥 Checking backend health...');

      final response = await _client
          .get(Uri.parse('${ApiConfig.baseUrl}/health'))
          .timeout(const Duration(seconds: 5));

      final isHealthy = response.statusCode == 200;
      _logger.i(isHealthy ? '✅ Backend online' : '⚠️ Backend unhealthy');
      return isHealthy;
    } catch (e) {
      _logger.w('⚠️ Health check failed: $e');
      return false;
    }
  }

  void dispose() {
    _client.close();
    _logger.i('🔌 ApiClient disposed');
  }
}

Product _mapDbProductResponse(Map<String, dynamic> jsonData, String fallbackBarcode) {
  final productData = (jsonData['product'] as Map<String, dynamic>? ?? {});
  final scoreData = (jsonData['score'] as Map<String, dynamic>? ?? {});
  final ingredientsData = (jsonData['ingredients'] as List<dynamic>? ?? []);

  final ingredients = ingredientsData
      .map((e) => (e as Map<String, dynamic>)['canonical_name']?.toString() ??
          e['raw_name']?.toString() ??
          '')
      .where((e) => e.isNotEmpty)
      .toList();

  final allergens = ingredientsData
      .where((e) => (e as Map<String, dynamic>)['allergen_flag'] == true)
      .map((e) => (e as Map<String, dynamic>)['canonical_name']?.toString() ?? 'allergen')
      .toSet()
      .toList();

  final dangerousSubstances = ingredientsData
      .where((e) => (e as Map<String, dynamic>)['risky_flag'] == true ||
          (e['risk_level'] != null && ['high','critical'].contains(e['risk_level'].toString().toLowerCase())))
      .map((e) => (e as Map<String, dynamic>)['canonical_name']?.toString() ?? e['raw_name']?.toString() ?? 'sostanza pericolosa')
      .toSet()
      .toList();

  final ingredientScore =
      (scoreData['ingredient_score'] as num?)?.toDouble() ?? 0.0;
  final nutritionScore = (scoreData['nutrition_score'] as num?)?.toDouble();
  final finalScore = (scoreData['final_score'] as num?)?.toDouble() ?? ingredientScore;

  return Product(
    barcode: productData['barcode']?.toString() ?? fallbackBarcode,
    productName: productData['product_name']?.toString() ?? 'Prodotto',
    brand: productData['brand_name']?.toString() ?? 'N/A',
    category: productData['category']?.toString() ?? 'food',
    ingredientScore: ingredientScore,
    nutritionScore: nutritionScore,
    finalScore: finalScore,
    riskLevel: scoreData['score_band']?.toString() ?? _riskLevelFromScore(finalScore),
    ingredients: ingredients,
    allergens: allergens,
    dangerousSubstances: dangerousSubstances,
    imageUrl: productData['image_url']?.toString(),
  );
}

Product _mapAnalyzeResponseToProduct(Map<String, dynamic> jsonData) {
  final score = (jsonData['score'] as num?)?.toDouble() ?? 0.0;
  final ingredientItems = (jsonData['ingredients'] as List<dynamic>? ?? []);

  final ingredients = ingredientItems
      .map((e) => (e as Map<String, dynamic>)['raw']?.toString() ?? '')
      .where((e) => e.isNotEmpty)
      .toList();

  return Product(
    barcode: 'manual_${DateTime.now().millisecondsSinceEpoch}',
    productName: jsonData['product_name']?.toString() ?? 'Analisi manuale',
    brand: 'Manual Entry',
    category: 'food',
    ingredientScore: score,
    nutritionScore: null,
    finalScore: score,
    riskLevel: jsonData['score_label']?.toString() ?? _riskLevelFromScore(score),
    ingredients: ingredients,
    allergens: const [],
  );
}

String _riskLevelFromScore(double score) {
  if (score < 25) return 'critical';
  if (score < 40) return 'high';
  if (score < 60) return 'moderate';
  if (score < 80) return 'low';
  return 'excellent';
}

// Custom Exceptions
class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => message;
}

class NetworkException implements Exception {
  final String message;
  NetworkException(this.message);

  @override
  String toString() => message;
}

class ProductNotFoundException implements Exception {
  final String message;
  ProductNotFoundException(this.message);

  @override
  String toString() => message;
}

class TimeoutException implements Exception {
  final String? message;
  TimeoutException(this.message);

  @override
  String toString() => message ?? 'Request timeout';
}
