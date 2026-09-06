import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:logger/logger.dart';
import 'package:flutter/foundation.dart';
import '../models/capture_upload_models.dart';
import '../models/product_model.dart';
import '../models/score_evaluability_model.dart';

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
  final MobileUploadTokenProvider? _mobileTokenProvider;
  late http.Client _client;

  ApiClient({MobileUploadTokenProvider? mobileTokenProvider})
      : _mobileTokenProvider = mobileTokenProvider {
    _client = http.Client();
  }

  /// Fetch prodotto da barcode
  Future<Product> getProductByBarcode(String barcode) async {
    try {
      _logger.i('Fetching product by barcode');

      final response = await _client
          .get(
        Uri.parse('${ApiConfig.baseUrl}/product/$barcode'),
      )
          .timeout(ApiConfig.connectionTimeout, onTimeout: () {
        throw TimeoutException(
            'Backend non risponde. Verifica la connessione.');
      });

      _logger.d('Response status: ${response.statusCode}');

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
            final imageUrl = await _resolveCanonicalImageUrl(jsonData);
            final product = _mapDbProductResponse(
              jsonData,
              barcode,
              imageUrlOverride: imageUrl,
            );
            _logger.i('Product found');
            return product;
          }

          // Caso API già nel formato app
          final product = Product.fromJson(jsonData);
          _logger.i('Product found');
          return product;
        } on ProductNotFoundException {
          rethrow;
        } catch (e) {
          _logger.e('Product response parsing failed');
          throw ApiException('Errore nel parsing della risposta del server');
        }
      } else if (response.statusCode == 404) {
        _logger.w('Product not found');
        throw ProductNotFoundException(
            'Prodotto non trovato nel database. Prova a inserirlo manualmente nella sezione Premium.');
      } else if (response.statusCode >= 500) {
        _logger.e('❌ Server error: ${response.statusCode}');
        throw ApiException('Errore del server. Riprova tra poco.');
      } else {
        _logger.e('Product lookup failed with status ${response.statusCode}');
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
      _logger.e('Product lookup timed out');
      throw NetworkException(e.message ?? 'Timeout della richiesta');
    } catch (e) {
      _logger.e('Product lookup failed');
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
        if (imageUrl != null && imageUrl.trim().isNotEmpty)
          'image_url': imageUrl.trim(),
        if (ingredientImageUrl != null && ingredientImageUrl.trim().isNotEmpty)
          'ingredient_image_url': ingredientImageUrl.trim(),
        if (nutritionImageUrl != null && nutritionImageUrl.trim().isNotEmpty)
          'nutrition_image_url': nutritionImageUrl.trim(),
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
          throw ApiException(
              'Risposta del server vuota durante la creazione prodotto');
        }

        final product = await getProductByBarcode(barcode.trim());
        _logger.i('Product created');
        return product;
      }

      throw ApiException(
          'Errore nella creazione prodotto (${response.statusCode})');
    } on SocketException {
      _logger.e('❌ Network error while creating product');
      throw NetworkException(
          'Impossibile raggiungere il server. Verifica che il backend sia attivo.');
    } on TimeoutException catch (e) {
      _logger.e('Product creation timed out');
      throw NetworkException(e.message ?? 'Timeout della creazione prodotto');
    } catch (e) {
      _logger.e('Product creation failed');
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
      _logger.i('Analyzing manually entered ingredients');

      final payload = {
        'product_name': productName,
        'ingredients': ingredients,
        'language': language,
        if (category != null) 'category': category,
      };


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
              jsonData['ingredients'] is List) {
            final product = _mapAnalyzeResponseToProduct(jsonData);
            _logger.i('✅ Legacy analysis response mapped without score');
            return product;
          }

          // Caso API già nel formato app
          final product = Product.fromJson(jsonData);
          _logger.i('✅ Analysis response parsed');
          return product;
        } catch (e) {
          _logger.e('Analysis response parsing failed');
          throw ApiException('Errore nel parsing della risposta');
        }
      } else if (response.statusCode == 400) {
        _logger.e('Analysis request rejected');
        throw ApiException(
            'Dati non validi. Controlla gli ingredienti inseriti.');
      } else {
        throw ApiException('Errore nell\'analisi (${response.statusCode})');
      }
    } on SocketException {
      _logger.e('❌ Network error');
      throw NetworkException(
          'Errore di connessione. Controlla la rete e riprova.');
    } catch (e) {
      _logger.e('Analysis request failed');
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
          'product_type':
              jsonData['product_type'] ?? jsonData['type'] ?? 'snack',
        };
      }

      throw ApiException(
          'Errore nella normalizzazione foto (${response.statusCode})');
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
      _logger.d(
          'Payload: imageUrl length=${imageUrl.length}, rawText length=${rawText?.length ?? 0}');
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

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body) as Map<String, dynamic>;
        return {
          'ingredients': jsonData['ingredients'] ?? const [],
          'nutrition': jsonData['nutrition'] ?? const {},
          'product_name': jsonData['product_name'] ?? jsonData['name'] ?? '',
          'brand_name': jsonData['brand_name'] ?? jsonData['brand'] ?? '',
          'category': jsonData['category'] ?? 'food',
          'product_type':
              jsonData['product_type'] ?? jsonData['type'] ?? 'snack',
        };
      }

      throw ApiException(
          'Errore nell\'analisi immagine (${response.statusCode})');
    } on SocketException {
      throw NetworkException(
          'Impossibile raggiungere il server. Verifica che il backend sia attivo.');
    } on TimeoutException catch (e) {
      throw NetworkException(e.message ?? 'Timeout dell\'analisi immagine');
    } catch (e) {
      rethrow;
    }
  }

  Future<String?> _resolveCanonicalImageUrl(
    Map<String, dynamic> response,
  ) async {
    final product = response['product'];
    final fallback = product is Map ? product['image_url']?.toString() : null;
    final imageRef = response['product_image'];
    final token = _mobileTokenProvider?.currentToken;
    if (product is! Map || imageRef is! Map || token == null) {
      return _absoluteOrEmbeddedImageUrl(fallback);
    }

    final productId = product['id'];
    final imageId = imageRef['id'];
    if (productId is! int ||
        productId <= 0 ||
        imageId is! int ||
        imageId <= 0) {
      return _absoluteOrEmbeddedImageUrl(fallback);
    }

    try {
      final response = await _client.get(
        Uri.parse(
          '${ApiConfig.baseUrl}/mobile/dev/v1/capture/products/'
          '$productId/images/$imageId/access',
        ),
        headers: {'Authorization': token.authorizationHeader},
      ).timeout(ApiConfig.connectionTimeout);
      if (response.statusCode != 200) {
        return _absoluteOrEmbeddedImageUrl(fallback);
      }
      final body = jsonDecode(response.body);
      final rawUrl = body is Map ? body['url']?.toString() : null;
      final url = rawUrl == null ? null : Uri.tryParse(rawUrl);
      if (url == null ||
          !url.hasScheme ||
          (url.scheme != 'http' && url.scheme != 'https')) {
        return _absoluteOrEmbeddedImageUrl(fallback);
      }
      return url.toString();
    } catch (_) {
      return _absoluteOrEmbeddedImageUrl(fallback);
    }
  }

  String? _absoluteOrEmbeddedImageUrl(String? value) {
    final trimmed = value?.trim();
    if (trimmed == null || trimmed.isEmpty) return null;
    if (trimmed.startsWith('data:image')) return trimmed;
    final uri = Uri.tryParse(trimmed);
    if (uri != null && uri.hasScheme) return trimmed;
    if (trimmed.startsWith('/')) return '${ApiConfig.baseUrl}$trimmed';
    return null;
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
      _logger.w('Health check failed');
      return false;
    }
  }

  void dispose() {
    _client.close();
    _logger.i('🔌 ApiClient disposed');
  }
}

Product _mapDbProductResponse(
  Map<String, dynamic> jsonData,
  String fallbackBarcode, {
  String? imageUrlOverride,
}) {
  final productData = (jsonData['product'] as Map<String, dynamic>? ?? {});
  final ingredientsData = (jsonData['ingredients'] as List<dynamic>? ?? []);

  final ingredients = ingredientsData
      .map((e) =>
          (e as Map<String, dynamic>)['canonical_name']?.toString() ??
          e['raw_name']?.toString() ??
          '')
      .where((e) => e.isNotEmpty)
      .toList();

  final allergens = ingredientsData
      .where((e) => (e as Map<String, dynamic>)['allergen_flag'] == true)
      .map((e) =>
          (e as Map<String, dynamic>)['canonical_name']?.toString() ??
          'allergen')
      .toSet()
      .toList();

  final dangerousSubstances = ingredientsData
      .where((e) =>
          (e as Map<String, dynamic>)['risky_flag'] == true ||
          (e['risk_level'] != null &&
              ['high', 'critical']
                  .contains(e['risk_level'].toString().toLowerCase())))
      .map((e) =>
          (e as Map<String, dynamic>)['canonical_name']?.toString() ??
          e['raw_name']?.toString() ??
          'sostanza pericolosa')
      .toSet()
      .toList();

  final scoreData = jsonData['score_view'];
  final nutritionData = jsonData['nutrition_facts'];

  return Product(
    productId: productData['id'] is int && productData['id'] > 0
        ? productData['id'] as int
        : null,
    barcode: productData['barcode']?.toString() ?? fallbackBarcode,
    productName: productData['product_name']?.toString() ?? 'Prodotto',
    brand: productData['brand_name']?.toString() ?? 'N/A',
    category: productData['category']?.toString() ?? 'food',
    scoreView: scoreData is Map
        ? ProductScoreView.fromJson(Map<String, dynamic>.from(scoreData))
        : ProductScoreView.unavailable(),
    ingredients: ingredients,
    allergens: allergens,
    dangerousSubstances: dangerousSubstances,
    nutritionFacts: nutritionData is Map
        ? NutritionFacts.fromJson({
            'serving_size': nutritionData['serving_size'],
            'energy_kcal': nutritionData['energy_kcal'],
            'protein': nutritionData['protein_g'],
            'carbs': nutritionData['carbs_g'],
            'sugar': nutritionData['sugar_g'],
            'fat': nutritionData['fat_g'],
            'saturated_fat': nutritionData['saturated_fat_g'],
            'sodium': nutritionData['sodium_mg'],
            'fiber': nutritionData['fiber_g'],
          })
        : null,
    imageUrl: imageUrlOverride ?? productData['image_url']?.toString(),
  );
}

Product _mapAnalyzeResponseToProduct(Map<String, dynamic> jsonData) {
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
    scoreView: ProductScoreView.unavailable(),
    ingredients: ingredients,
    allergens: const [],
  );
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
