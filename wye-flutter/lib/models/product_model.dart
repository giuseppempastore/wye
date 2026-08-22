class Product {
  final String barcode;
  final String productName;
  final String brand;
  final String category;
  final double ingredientScore;
  final double? nutritionScore;
  final double finalScore;
  final double? riskIndex; // 0-100 numeric danger index
  final String riskLevel;
  final List<String> ingredients;
  final NutritionFacts? nutritionFacts;
  final List<String> allergens;
  final String? imageUrl;
  final DateTime? fetchedAt;

  Product({
    required this.barcode,
    required this.productName,
    required this.brand,
    required this.category,
    required this.ingredientScore,
    this.nutritionScore,
    this.riskIndex,
    required this.finalScore,
    required this.riskLevel,
    required this.ingredients,
    this.nutritionFacts,
    required this.allergens,
    this.imageUrl,
    this.fetchedAt,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      barcode: json['barcode'] as String,
      productName: json['product_name'] as String,
      brand: json['brand'] as String,
      category: json['category'] as String,
      ingredientScore: (json['ingredient_score'] as num).toDouble(),
      nutritionScore: json['nutrition_score'] != null
          ? (json['nutrition_score'] as num).toDouble()
          : null,
      finalScore: (json['final_score'] as num).toDouble(),
      riskLevel: json['risk_level'] as String,
      ingredients: List<String>.from(json['ingredients'] as List? ?? []),
      nutritionFacts: json['nutrition_facts'] != null
          ? NutritionFacts.fromJson(json['nutrition_facts'])
          : null,
      allergens: List<String>.from(json['allergens'] as List? ?? []),
      imageUrl: json['image_url'] as String?,
      riskIndex: json['risk_index'] != null
          ? (json['risk_index'] as num).toDouble()
          : null,
      fetchedAt: DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'barcode': barcode,
      'product_name': productName,
      'brand': brand,
      'category': category,
      'ingredient_score': ingredientScore,
      'risk_index': riskIndex,
      'nutrition_score': nutritionScore,
      'final_score': finalScore,
      'risk_level': riskLevel,
      'ingredients': ingredients,
      'nutrition_facts': nutritionFacts?.toJson(),
      'allergens': allergens,
      'image_url': imageUrl,
      'fetched_at': fetchedAt?.toIso8601String(),
    };
  }

  @override
  String toString() => 'Product(barcode: $barcode, productName: $productName)';
}

class NutritionFacts {
  final double? servingSize;
  final double? energyKcal;
  final double? protein;
  final double? carbs;
  final double? sugar;
  final double? fat;
  final double? saturatedFat;
  final double? sodium;
  final double? fiber;

  NutritionFacts({
    this.servingSize,
    this.energyKcal,
    this.protein,
    this.carbs,
    this.sugar,
    this.fat,
    this.saturatedFat,
    this.sodium,
    this.fiber,
  });

  factory NutritionFacts.fromJson(Map<String, dynamic> json) {
    return NutritionFacts(
      servingSize: json['serving_size'] as double?,
      energyKcal: json['energy_kcal'] as double?,
      protein: json['protein'] as double?,
      carbs: json['carbs'] as double?,
      sugar: json['sugar'] as double?,
      fat: json['fat'] as double?,
      saturatedFat: json['saturated_fat'] as double?,
      sodium: json['sodium'] as double?,
      fiber: json['fiber'] as double?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'serving_size': servingSize,
      'energy_kcal': energyKcal,
      'protein': protein,
      'carbs': carbs,
      'sugar': sugar,
      'fat': fat,
      'saturated_fat': saturatedFat,
      'sodium': sodium,
      'fiber': fiber,
    };
  }
}

class ScanHistory {
  final String barcode;
  final String productName;
  final double finalScore;
  final DateTime scannedAt;
  final String category;

  ScanHistory({
    required this.barcode,
    required this.productName,
    required this.finalScore,
    required this.scannedAt,
    required this.category,
  });

  factory ScanHistory.fromProduct(Product product) {
    return ScanHistory(
      barcode: product.barcode,
      productName: product.productName,
      finalScore: product.finalScore,
      scannedAt: DateTime.now(),
      category: product.category,
    );
  }

  factory ScanHistory.fromJson(Map<String, dynamic> json) {
    return ScanHistory(
      barcode: json['barcode'] as String,
      productName: json['product_name'] as String,
      finalScore: (json['final_score'] as num).toDouble(),
      scannedAt: DateTime.parse(json['scanned_at'] as String),
      category: json['category'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'barcode': barcode,
      'product_name': productName,
      'final_score': finalScore,
      'scanned_at': scannedAt.toIso8601String(),
      'category': category,
    };
  }
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
      trackedProductBarcodes: List<String>.from(json['tracked_product_barcodes'] as List? ?? []),
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
      riskIndex: json['risk_index'] != null ? (json['risk_index'] as num).toDouble() : null,
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
      itemBreakdown: Map<String, int>.from(json['item_breakdown'] as Map? ?? {}),
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
