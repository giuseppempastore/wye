import 'package:flutter/material.dart';
import '../models/product_model.dart';
import '../services/api_client.dart';
import '../services/product_barcode_validator.dart';

// State per il barcode scanning
class BarcodeScannerProvider extends ChangeNotifier {
  final ApiClient _apiClient;
  final ProductBarcodeValidator _barcodeValidator =
      const ProductBarcodeValidator();

  Product? _currentProduct;
  bool _isLoading = false;
  String? _error;
  List<ScanHistory> _scanHistory = [];

  BarcodeScannerProvider(this._apiClient);

  // Getters
  Product? get currentProduct => _currentProduct;
  bool get isLoading => _isLoading;
  String? get error => _error;
  List<ScanHistory> get scanHistory => _scanHistory;

  /// Scansiona un barcode
  Future<void> scanBarcode(String barcode) async {
    final validation = _barcodeValidator.validate(barcode);
    debugPrint(validation.safeLog);
    if (!validation.isValid) {
      _error = 'Barcode non valido';
      _currentProduct = null;
      notifyListeners();
      return;
    }
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentProduct = await _apiClient.getProductByBarcode(validation.value!);
      _addToHistory(_currentProduct!);
      _error = null;
    } on ProductNotFoundException catch (e) {
      _error = e.message;
      _currentProduct = null;
    } on NetworkException catch (e) {
      _error = e.message;
      _currentProduct = null;
    } catch (_) {
      _error = 'Errore imprevisto durante la ricerca';
      _currentProduct = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Analizza ingredienti manuali
  Future<void> analyzeIngredients({
    required String productName,
    required String ingredients,
    String language = 'it',
    String? category,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentProduct = await _apiClient.analyzeIngredients(
        productName: productName,
        ingredients: ingredients,
        language: language,
        category: category,
      );
      _addToHistory(_currentProduct!);
      _error = null;
    } catch (e) {
      _error = 'Errore nell\'analisi: $e';
      _currentProduct = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> addProductFromSubmission({
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
    final validation = _barcodeValidator.validate(barcode);
    debugPrint(validation.safeLog);
    if (!validation.isValid) {
      _error = 'Barcode non valido';
      _currentProduct = null;
      notifyListeners();
      return;
    }
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentProduct = await _apiClient.createProduct(
        barcode: validation.value!,
        brandName: brandName,
        productName: productName,
        category: category,
        productType: productType,
        ingredients: ingredients,
        nutritionFacts: nutritionFacts ?? const {},
        source: source,
        imageUrl: imageUrl,
        ingredientImageUrl: ingredientImageUrl,
        nutritionImageUrl: nutritionImageUrl,
      );
      _addToHistory(_currentProduct!);
      _error = null;
    } on ProductNotFoundException catch (e) {
      _error = e.message;
      _currentProduct = null;
    } on NetworkException catch (e) {
      _error = e.message;
      _currentProduct = null;
    } catch (_) {
      _error = 'Errore durante l\'inserimento del prodotto';
      _currentProduct = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Aggiunge un prodotto allo storico
  void _addToHistory(Product product) {
    _scanHistory.removeWhere((item) => item.barcode == product.barcode);
    _scanHistory.insert(0, ScanHistory.fromProduct(product));
    if (_scanHistory.length > 50) {
      _scanHistory.removeLast(); // Limita a 50 ultimi
    }
    notifyListeners();
  }

  /// Pulisci errore
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Reset stato
  void reset() {
    _currentProduct = null;
    _isLoading = false;
    _error = null;
    notifyListeners();
  }

  @override
  void dispose() {
    super.dispose();
  }
}

// State per le preferenze e i dati utente
class UserPreferencesProvider extends ChangeNotifier {
  bool _isPremium = false;
  List<String> _userAllergies = [];
  String _language = 'it';
  String _country = 'IT';
  bool _premiumFactCheckConsent = false;

  // Getters
  bool get isPremium => _isPremium;
  List<String> get userAllergies => _userAllergies;
  String get language => _language;
  String get country => _country;
  bool get premiumFactCheckConsent => _premiumFactCheckConsent;

  void setUserAllergies(List<String> allergies) {
    _userAllergies = allergies;
    notifyListeners();
  }

  void setPremium(bool value) {
    _isPremium = value;
    if (!_isPremium) {
      _premiumFactCheckConsent = false;
    }
    notifyListeners();
  }

  void setLanguage(String lang) {
    _language = lang;
    notifyListeners();
  }

  void setCountry(String countryCode) {
    _country = countryCode;
    notifyListeners();
  }

  void setPremiumFactCheckConsent(bool value) {
    _premiumFactCheckConsent = value;
    notifyListeners();
  }

  void resetPremiumFactCheckConsent() {
    _premiumFactCheckConsent = false;
    notifyListeners();
  }

  void addAllergy(String allergen) {
    if (!_userAllergies.contains(allergen)) {
      _userAllergies.add(allergen);
      notifyListeners();
    }
  }

  void removeAllergy(String allergen) {
    _userAllergies.remove(allergen);
    notifyListeners();
  }
}

// State per app globali
class AppStateProvider extends ChangeNotifier {
  bool _isConnected = false;
  bool _isInitializing = true;

  bool get isConnected => _isConnected;
  bool get isInitializing => _isInitializing;

  Future<void> initApp() async {
    _isInitializing = true;
    notifyListeners();

    // Simula caricamento iniziale
    await Future.delayed(const Duration(seconds: 1));

    _isInitializing = false;
    notifyListeners();
  }

  void setConnected(bool value) {
    _isConnected = value;
    notifyListeners();
  }
}
