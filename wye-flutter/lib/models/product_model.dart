import 'score_evaluability_model.dart';

class Product {
  final int? productId;
  final String barcode;
  final String productName;
  final String brand;
  final String category;
  final String? productType;
  final String validationStatus;
  final bool dataVerified;
  final ProductScoreView scoreView;
  final double? riskIndex; // 0-100 numeric danger index
  final List<String> ingredients;
  final List<String> allergens;
  final List<String> dangerousSubstances;
  final NutritionFacts? nutritionFacts;
  final String? imageUrl;
  final DateTime? fetchedAt;

  Product({
    this.productId,
    required this.barcode,
    required this.productName,
    required this.brand,
    required this.category,
    this.productType,
    this.validationStatus = 'needs_review',
    this.dataVerified = false,
    required this.scoreView,
    this.riskIndex,
    required this.ingredients,
    required this.allergens,
    this.dangerousSubstances = const [],
    this.nutritionFacts,
    this.imageUrl,
    this.fetchedAt,
  }) {
    if (productId != null && productId! <= 0) {
      throw RangeError.value(productId!, 'productId', 'Must be positive');
    }
  }

  factory Product.fromJson(Map<String, dynamic> json) {
    final barcodeValue = (json['barcode'] ?? '').toString();
    final productNameValue =
        (json['product_name'] ?? json['name'] ?? 'Unnamed product').toString();
    final brandValue =
        (json['brand'] ?? json['brand_name'] ?? 'Unknown Brand').toString();
    final categoryValue = (json['category'] ?? 'food').toString();

    return Product(
      productId: _positiveProductId(json['id'] ?? json['product_id']),
      barcode: barcodeValue,
      productName: productNameValue,
      brand: brandValue,
      category: categoryValue,
      productType: json['product_type']?.toString(),
      validationStatus: json['status']?.toString() ?? 'needs_review',
      dataVerified: json['verified'] == true,
      scoreView: _scoreViewFromJson(json),
      ingredients: json['ingredients'] is List
          ? List<String>.from(
              (json['ingredients'] as List).map((e) => e.toString()))
          : const [],
      allergens: List<String>.from(json['allergens'] as List? ?? []),
      dangerousSubstances: List<String>.from(
          json['dangerous_substances'] as List? ??
              json['hazardous_substances'] as List? ??
              []),
      nutritionFacts: json['nutrition_facts'] != null
          ? NutritionFacts.fromJson(json['nutrition_facts'])
          : null,
      imageUrl: json['image_url'] as String?,
      riskIndex: json['risk_index'] != null
          ? (json['risk_index'] as num).toDouble()
          : null,
      fetchedAt: DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': productId,
      'barcode': barcode,
      'product_name': productName,
      'brand': brand,
      'category': category,
      'product_type': productType,
      'status': validationStatus,
      'verified': dataVerified,
      'score_view': scoreView.toJson(),
      'risk_index': riskIndex,
      'ingredients': ingredients,
      'nutrition_facts': nutritionFacts?.toJson(),
      'allergens': allergens,
      'dangerous_substances': dangerousSubstances,
      'image_url': imageUrl,
      'fetched_at': fetchedAt?.toIso8601String(),
    };
  }

  @override
  String toString() => 'Product(productId: $productId, barcode: <redacted>, '
      'productName: $productName)';
}

int? _positiveProductId(Object? value) {
  return value is int && value > 0 ? value : null;
}

class NutritionFacts {
  final double? servingSize;
  final double? energyKcal;
  final double? energyKj;
  final double? protein;
  final double? carbs;
  final double? sugar;
  final double? fat;
  final double? saturatedFat;
  final double? sodiumMg;
  final double? saltG;
  final double? fiber;

  NutritionFacts({
    this.servingSize,
    this.energyKcal,
    this.energyKj,
    this.protein,
    this.carbs,
    this.sugar,
    this.fat,
    this.saturatedFat,
    this.sodiumMg,
    this.saltG,
    this.fiber,
  });

  factory NutritionFacts.fromJson(Map<String, dynamic> json) {
    return NutritionFacts(
      servingSize: _toDouble(json['serving_size']),
      energyKcal: _toDouble(json['energy_kcal']),
      energyKj: _toDouble(json['energy_kj']),
      protein: _toDouble(json['protein']),
      carbs: _toDouble(json['carbs']),
      sugar: _toDouble(json['sugar']),
      fat: _toDouble(json['fat']),
      saturatedFat: _toDouble(json['saturated_fat']),
      sodiumMg: _toDouble(json['sodium_mg'] ?? json['sodium']),
      saltG: _toDouble(json['salt_g'] ?? json['salt']),
      fiber: _toDouble(json['fiber']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'serving_size': servingSize,
      'energy_kcal': energyKcal,
      'energy_kj': energyKj,
      'protein': protein,
      'carbs': carbs,
      'sugar': sugar,
      'fat': fat,
      'saturated_fat': saturatedFat,
      'sodium_mg': sodiumMg,
      'salt_g': saltG,
      'fiber': fiber,
    };
  }
}

double? _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '');
}

class ScanHistory {
  final String barcode;
  final String productName;
  final ProductScoreView scoreView;
  final DateTime scannedAt;
  final String category;
  final String? imageUrl;
  final String validationStatus;
  final bool dataVerified;

  ScanHistory({
    required this.barcode,
    required this.productName,
    required this.scoreView,
    required this.scannedAt,
    required this.category,
    this.imageUrl,
    this.validationStatus = 'needs_review',
    this.dataVerified = false,
  });

  factory ScanHistory.fromProduct(Product product) {
    return ScanHistory(
      barcode: product.barcode,
      productName: product.productName,
      scoreView: product.scoreView,
      scannedAt: DateTime.now(),
      category: product.category,
      imageUrl: product.imageUrl,
      validationStatus: product.validationStatus,
      dataVerified: product.dataVerified,
    );
  }

  factory ScanHistory.fromJson(Map<String, dynamic> json) {
    return ScanHistory(
      barcode: json['barcode'] as String,
      productName: json['product_name'] as String,
      scoreView: _scoreViewFromJson(json),
      scannedAt: DateTime.parse(json['scanned_at'] as String),
      category: json['category'] as String,
      imageUrl: json['image_url'] as String?,
      validationStatus: json['validation_status']?.toString() ?? 'needs_review',
      dataVerified: json['data_verified'] == true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'barcode': barcode,
      'product_name': productName,
      'score_view': scoreView.toJson(),
      'scanned_at': scannedAt.toIso8601String(),
      'category': category,
      'image_url': imageUrl,
      'validation_status': validationStatus,
      'data_verified': dataVerified,
    };
  }
}

ProductScoreView _scoreViewFromJson(Map<String, dynamic> json) {
  final nestedScoreView = json['score_view'];
  if (nestedScoreView is Map) {
    return ProductScoreView.fromJson(
      Map<String, dynamic>.from(nestedScoreView),
    );
  }

  final hasTypedTopLevelScore = json['ingredient_goodness_percent'] is Map &&
      json['nutrition_goodness_percent'] is Map &&
      json['overall_score'] is Map;
  if (hasTypedTopLevelScore) {
    return ProductScoreView.fromJson(json);
  }

  return ProductScoreView.unavailable();
}

// --- Consumption program models for Premium users ---

class ConsumptionProgram {
  final String id;
  final String name;
  final DateTime startDate;
  final DateTime? endDate;
  final String period; // 'daily' | 'weekly' | 'monthly'
  final List<String> trackedProductBarcodes; // list of barcodes or product ids

  ConsumptionProgram({
    required this.id,
    required this.name,
    required this.startDate,
    this.endDate,
    required this.period,
    required this.trackedProductBarcodes,
  });

  factory ConsumptionProgram.fromJson(Map<String, dynamic> json) {
    return ConsumptionProgram(
      id: json['id'] as String,
      name: json['name'] as String,
      startDate: DateTime.parse(json['start_date'] as String),
      endDate: json['end_date'] != null
          ? DateTime.parse(json['end_date'] as String)
          : null,
      period: json['period'] as String,
      trackedProductBarcodes:
          List<String>.from(json['tracked_product_barcodes'] as List? ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'start_date': startDate.toIso8601String(),
      'end_date': endDate?.toIso8601String(),
      'period': period,
      'tracked_product_barcodes': trackedProductBarcodes,
    };
  }
}

class ConsumptionEntry {
  final String id;
  final String programId;
  final String productBarcode;
  final String productName;
  final DateTime consumedAt;
  final double quantity; // e.g., number of servings
  final double? riskIndex; // numeric danger index captured at consumption

  ConsumptionEntry({
    required this.id,
    required this.programId,
    required this.productBarcode,
    required this.productName,
    required this.consumedAt,
    required this.quantity,
    this.riskIndex,
  });

  factory ConsumptionEntry.fromJson(Map<String, dynamic> json) {
    return ConsumptionEntry(
      id: json['id'] as String,
      programId: json['program_id'] as String,
      productBarcode: json['product_barcode'] as String,
      productName: json['product_name'] as String,
      consumedAt: DateTime.parse(json['consumed_at'] as String),
      quantity: (json['quantity'] as num).toDouble(),
      riskIndex: json['risk_index'] != null
          ? (json['risk_index'] as num).toDouble()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'program_id': programId,
      'product_barcode': productBarcode,
      'product_name': productName,
      'consumed_at': consumedAt.toIso8601String(),
      'quantity': quantity,
      'risk_index': riskIndex,
    };
  }
}

class ConsumptionSummary {
  final String programId;
  final DateTime periodStart;
  final String periodType; // 'daily'|'weekly'|'monthly'
  final int itemCount;
  final double aggregatedRiskScore; // sum or weighted sum of risk indices
  final Map<String, int> itemBreakdown; // barcode -> count

  ConsumptionSummary({
    required this.programId,
    required this.periodStart,
    required this.periodType,
    required this.itemCount,
    required this.aggregatedRiskScore,
    required this.itemBreakdown,
  });

  factory ConsumptionSummary.fromJson(Map<String, dynamic> json) {
    return ConsumptionSummary(
      programId: json['program_id'] as String,
      periodStart: DateTime.parse(json['period_start'] as String),
      periodType: json['period_type'] as String,
      itemCount: json['item_count'] as int,
      aggregatedRiskScore: (json['aggregated_risk_score'] as num).toDouble(),
      itemBreakdown:
          Map<String, int>.from(json['item_breakdown'] as Map? ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'program_id': programId,
      'period_start': periodStart.toIso8601String(),
      'period_type': periodType,
      'item_count': itemCount,
      'aggregated_risk_score': aggregatedRiskScore,
      'item_breakdown': itemBreakdown,
    };
  }
}
