enum ProductAcquisitionStatus {
  draft,
  queued,
  processing,
  extracted,
  needsReview,
  adminValidated,
  rejected,
  correctionRequired,
  failed,
}

extension ProductAcquisitionStatusWire on ProductAcquisitionStatus {
  String get wireValue => switch (this) {
        ProductAcquisitionStatus.needsReview => 'needs_review',
        ProductAcquisitionStatus.adminValidated => 'admin_validated',
        ProductAcquisitionStatus.correctionRequired => 'correction_required',
        _ => name,
      };

  String get italianLabel => switch (this) {
        ProductAcquisitionStatus.draft => 'Bozza',
        ProductAcquisitionStatus.queued => 'In coda',
        ProductAcquisitionStatus.processing => 'In elaborazione',
        ProductAcquisitionStatus.extracted => 'Estrazione completata',
        ProductAcquisitionStatus.needsReview => 'Dati etichetta non verificati',
        ProductAcquisitionStatus.adminValidated => 'Prodotto verificato',
        ProductAcquisitionStatus.rejected => 'Richiesta rifiutata',
        ProductAcquisitionStatus.correctionRequired => 'Correzione richiesta',
        ProductAcquisitionStatus.failed => 'Elaborazione fallita',
      };

  static ProductAcquisitionStatus parse(Object? value) {
    final wire = value?.toString();
    return ProductAcquisitionStatus.values.firstWhere(
      (status) => status.wireValue == wire,
      orElse: () => ProductAcquisitionStatus.draft,
    );
  }
}

/// Persisted, non-secret state for the public product-registration wizard.
///
/// Image bytes are never duplicated in Hive: only app-owned local paths and
/// completed backend image identifiers are retained. Mobile tokens, presigned
/// URLs and provider payloads are deliberately outside this model.
class ProductAcquisitionDraft {
  static const int schemaVersion = 1;

  final String id;
  final int currentStep;
  final ProductAcquisitionStatus status;
  final String? barcode;
  final bool barcodeLookupCompleted;
  final int? productId;
  final String brand;
  final String productName;
  final String categoryId;
  final String productTypeId;
  final String ingredients;
  final bool ingredientsUserEdited;
  final Map<String, double> nutrition;
  final bool nutritionUserEdited;
  final String? nutritionBasis;
  final Map<String, String> localImagePaths;
  final Map<String, int> uploadedImageIds;
  final Map<String, String> uploadedImageChecksums;
  final Map<String, Map<String, dynamic>> labelExtractions;
  final String? recoverableErrorCode;
  final String? acquisitionId;
  final DateTime updatedAt;

  const ProductAcquisitionDraft({
    required this.id,
    this.currentStep = 0,
    this.status = ProductAcquisitionStatus.draft,
    this.barcode,
    this.barcodeLookupCompleted = false,
    this.productId,
    this.brand = '',
    this.productName = '',
    this.categoryId = '',
    this.productTypeId = '',
    this.ingredients = '',
    this.ingredientsUserEdited = false,
    this.nutrition = const {},
    this.nutritionUserEdited = false,
    this.nutritionBasis,
    this.localImagePaths = const {},
    this.uploadedImageIds = const {},
    this.uploadedImageChecksums = const {},
    this.labelExtractions = const {},
    this.recoverableErrorCode,
    this.acquisitionId,
    required this.updatedAt,
  });

  bool get hasUserData =>
      barcode != null ||
      brand.trim().isNotEmpty ||
      productName.trim().isNotEmpty ||
      categoryId.isNotEmpty ||
      productTypeId.isNotEmpty ||
      ingredients.trim().isNotEmpty ||
      nutrition.isNotEmpty ||
      localImagePaths.isNotEmpty ||
      labelExtractions.isNotEmpty;

  ProductAcquisitionDraft copyWith({
    int? currentStep,
    ProductAcquisitionStatus? status,
    String? barcode,
    bool clearBarcode = false,
    bool? barcodeLookupCompleted,
    int? productId,
    String? brand,
    String? productName,
    String? categoryId,
    String? productTypeId,
    String? ingredients,
    bool? ingredientsUserEdited,
    Map<String, double>? nutrition,
    bool? nutritionUserEdited,
    String? nutritionBasis,
    Map<String, String>? localImagePaths,
    Map<String, int>? uploadedImageIds,
    Map<String, String>? uploadedImageChecksums,
    Map<String, Map<String, dynamic>>? labelExtractions,
    String? recoverableErrorCode,
    bool clearRecoverableError = false,
    String? acquisitionId,
    DateTime? updatedAt,
  }) {
    return ProductAcquisitionDraft(
      id: id,
      currentStep: currentStep ?? this.currentStep,
      status: status ?? this.status,
      barcode: clearBarcode ? null : barcode ?? this.barcode,
      barcodeLookupCompleted:
          barcodeLookupCompleted ?? this.barcodeLookupCompleted,
      productId: productId ?? this.productId,
      brand: brand ?? this.brand,
      productName: productName ?? this.productName,
      categoryId: categoryId ?? this.categoryId,
      productTypeId: productTypeId ?? this.productTypeId,
      ingredients: ingredients ?? this.ingredients,
      ingredientsUserEdited:
          ingredientsUserEdited ?? this.ingredientsUserEdited,
      nutrition: nutrition ?? this.nutrition,
      nutritionUserEdited: nutritionUserEdited ?? this.nutritionUserEdited,
      nutritionBasis: nutritionBasis ?? this.nutritionBasis,
      localImagePaths: localImagePaths ?? this.localImagePaths,
      uploadedImageIds: uploadedImageIds ?? this.uploadedImageIds,
      uploadedImageChecksums:
          uploadedImageChecksums ?? this.uploadedImageChecksums,
      labelExtractions: labelExtractions ?? this.labelExtractions,
      recoverableErrorCode: clearRecoverableError
          ? null
          : recoverableErrorCode ?? this.recoverableErrorCode,
      acquisitionId: acquisitionId ?? this.acquisitionId,
      updatedAt: updatedAt ?? DateTime.now().toUtc(),
    );
  }

  Map<String, dynamic> toJson() => {
        'schema_version': schemaVersion,
        'id': id,
        'current_step': currentStep,
        'status': status.wireValue,
        'barcode': barcode,
        'barcode_lookup_completed': barcodeLookupCompleted,
        'product_id': productId,
        'brand': brand,
        'product_name': productName,
        'category_id': categoryId,
        'product_type_id': productTypeId,
        'ingredients': ingredients,
        'ingredients_user_edited': ingredientsUserEdited,
        'nutrition': nutrition,
        'nutrition_user_edited': nutritionUserEdited,
        'nutrition_basis': nutritionBasis,
        'local_image_paths': localImagePaths,
        'uploaded_image_ids': uploadedImageIds,
        'uploaded_image_checksums': uploadedImageChecksums,
        'label_extractions': labelExtractions,
        'recoverable_error_code': recoverableErrorCode,
        'acquisition_id': acquisitionId,
        'updated_at': updatedAt.toIso8601String(),
      };

  factory ProductAcquisitionDraft.fromJson(Map<String, dynamic> json) {
    if (json['schema_version'] != schemaVersion) {
      throw const FormatException('Unsupported acquisition draft version');
    }
    final id = json['id']?.toString().trim() ?? '';
    if (id.isEmpty) throw const FormatException('Draft ID is required');
    return ProductAcquisitionDraft(
      id: id,
      currentStep: (json['current_step'] as num?)?.toInt() ?? 0,
      status: ProductAcquisitionStatusWire.parse(json['status']),
      barcode: json['barcode']?.toString(),
      barcodeLookupCompleted: json['barcode_lookup_completed'] == true,
      productId: (json['product_id'] as num?)?.toInt(),
      brand: json['brand']?.toString() ?? '',
      productName: json['product_name']?.toString() ?? '',
      categoryId: json['category_id']?.toString() ?? '',
      productTypeId: json['product_type_id']?.toString() ?? '',
      ingredients: json['ingredients']?.toString() ?? '',
      ingredientsUserEdited: json['ingredients_user_edited'] == true,
      nutrition: (json['nutrition'] as Map? ?? const {}).map(
        (key, value) => MapEntry(key.toString(), (value as num).toDouble()),
      ),
      nutritionUserEdited: json['nutrition_user_edited'] == true,
      nutritionBasis: json['nutrition_basis']?.toString(),
      localImagePaths: (json['local_image_paths'] as Map? ?? const {}).map(
        (key, value) => MapEntry(key.toString(), value.toString()),
      ),
      uploadedImageIds: (json['uploaded_image_ids'] as Map? ?? const {}).map(
        (key, value) => MapEntry(key.toString(), (value as num).toInt()),
      ),
      uploadedImageChecksums:
          (json['uploaded_image_checksums'] as Map? ?? const {}).map(
        (key, value) => MapEntry(key.toString(), value.toString()),
      ),
      labelExtractions: (json['label_extractions'] as Map? ?? const {}).map(
        (key, value) => MapEntry(
          key.toString(),
          Map<String, dynamic>.from(value as Map),
        ),
      ),
      recoverableErrorCode: json['recoverable_error_code']?.toString(),
      acquisitionId: json['acquisition_id']?.toString(),
      updatedAt:
          DateTime.tryParse(json['updated_at']?.toString() ?? '')?.toUtc() ??
              DateTime.fromMillisecondsSinceEpoch(0, isUtc: true),
    );
  }
}
