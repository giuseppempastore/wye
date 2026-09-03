import 'dart:typed_data';

class MobileUploadToken {
  final String _value;
  final DateTime expiresAt;

  MobileUploadToken(String value, {required this.expiresAt})
      : _value = value.trim() {
    if (_value.isEmpty) {
      throw ArgumentError.value(value, 'value', 'Must not be empty');
    }
  }

  bool get isExpired => !expiresAt.isAfter(DateTime.now().toUtc());

  String get authorizationHeader => 'Bearer $_value';

  @override
  String toString() =>
      'MobileUploadToken(value: <redacted>, expiresAt: $expiresAt)';
}

abstract class MobileUploadTokenProvider {
  MobileUploadToken? get currentToken;
}

class InMemoryMobileUploadTokenProvider implements MobileUploadTokenProvider {
  MobileUploadToken? _token;

  @override
  MobileUploadToken? get currentToken {
    final token = _token;
    if (token == null) {
      return null;
    }
    if (token.isExpired) {
      _token = null;
      return null;
    }
    return token;
  }

  void setToken(String value, {required DateTime expiresAt}) {
    _token = MobileUploadToken(value, expiresAt: expiresAt.toUtc());
  }

  void clear() {
    _token = null;
  }

  @override
  String toString() => 'InMemoryMobileUploadTokenProvider(hasUsableToken: '
      '${currentToken != null})';
}

class ProductIdentity {
  final int productId;
  final String barcode;

  ProductIdentity({required this.productId, required String barcode})
      : barcode = barcode.trim() {
    if (productId <= 0) {
      throw RangeError.value(productId, 'productId', 'Must be positive');
    }
    if (this.barcode.isEmpty) {
      throw ArgumentError.value(barcode, 'barcode', 'Must not be empty');
    }
  }

  @override
  String toString() =>
      'ProductIdentity(productId: $productId, barcode: $barcode)';
}

enum CaptureImagePurpose {
  productFront,
  ingredients,
  nutrition,
  other;

  String get wireValue {
    switch (this) {
      case CaptureImagePurpose.productFront:
        return 'product_front';
      case CaptureImagePurpose.ingredients:
        return 'ingredients';
      case CaptureImagePurpose.nutrition:
        return 'nutrition';
      case CaptureImagePurpose.other:
        return 'other';
    }
  }
}

class ImageCaptureDraft {
  final ProductIdentity productIdentity;
  final CaptureImagePurpose purpose;
  final Uint8List bytes;

  ImageCaptureDraft({
    required this.productIdentity,
    required this.purpose,
    required Uint8List bytes,
  }) : bytes = Uint8List.fromList(bytes) {
    if (bytes.isEmpty) {
      throw ArgumentError.value(bytes, 'bytes', 'Must not be empty');
    }
  }

  @override
  String toString() =>
      'ImageCaptureDraft(productId: ${productIdentity.productId}, '
      'purpose: ${purpose.wireValue}, byteSize: ${bytes.length})';
}

class ImageMetadata {
  static const supportedMimeTypes = {
    'image/jpeg',
    'image/png',
    'image/webp',
  };

  final String mimeType;
  final int byteSize;
  final String sha256;

  ImageMetadata({
    required this.mimeType,
    required this.byteSize,
    required String sha256,
  }) : sha256 = sha256.toLowerCase() {
    if (!supportedMimeTypes.contains(mimeType)) {
      throw ArgumentError.value(mimeType, 'mimeType', 'Unsupported MIME type');
    }
    if (byteSize <= 0) {
      throw RangeError.value(byteSize, 'byteSize', 'Must be positive');
    }
    if (!RegExp(r'^[0-9a-fA-F]{64}$').hasMatch(sha256)) {
      throw ArgumentError.value(sha256, 'sha256', 'Must be a SHA-256 digest');
    }
  }

  Map<String, Object> toJson() => {
        'mime_type': mimeType,
        'byte_size': byteSize,
        'sha256': sha256,
      };
}

class UploadInitializeRequest {
  final ProductIdentity productIdentity;
  final CaptureImagePurpose purpose;
  final ImageMetadata metadata;

  const UploadInitializeRequest({
    required this.productIdentity,
    required this.purpose,
    required this.metadata,
  });

  Map<String, Object> toJson() => {
        'image_type': purpose.wireValue,
        ...metadata.toJson(),
      };
}

class UploadInitializeResponse {
  final String uploadId;
  final Uri uploadUri;
  final Map<String, String> headers;
  final DateTime expiresAt;

  UploadInitializeResponse({
    required String uploadId,
    required this.uploadUri,
    required Map<String, String> headers,
    required this.expiresAt,
  })  : uploadId = uploadId.trim(),
        headers = Map.unmodifiable(headers) {
    _validateUploadId(this.uploadId);
    if (!uploadUri.hasScheme || uploadUri.host.isEmpty) {
      throw ArgumentError.value(uploadUri, 'uploadUri', 'Must be absolute');
    }
    if (uploadUri.userInfo.isNotEmpty) {
      throw ArgumentError.value(
        uploadUri,
        'uploadUri',
        'User information is not allowed',
      );
    }
    if (uploadUri.scheme != 'http' && uploadUri.scheme != 'https') {
      throw ArgumentError.value(uploadUri, 'uploadUri', 'Unsupported scheme');
    }
    if (uploadUri.hasFragment) {
      throw ArgumentError.value(
        uploadUri,
        'uploadUri',
        'Fragments are not allowed',
      );
    }
  }

  factory UploadInitializeResponse.fromJson(Map<String, dynamic> json) {
    final rawHeaders = json['headers'];
    if (rawHeaders is! Map) {
      throw const FormatException('headers must be an object');
    }
    if (_requiredString(json, 'method') != 'PUT') {
      throw const FormatException('method must be PUT');
    }
    if (rawHeaders.keys.any((key) => key is! String) ||
        rawHeaders.values.any((value) => value is! String)) {
      throw const FormatException('header names and values must be strings');
    }
    return UploadInitializeResponse(
      uploadId: _requiredString(json, 'upload_id'),
      uploadUri: Uri.parse(_requiredString(json, 'upload_url')),
      headers: Map<String, String>.from(rawHeaders),
      expiresAt: DateTime.parse(_requiredString(json, 'expires_at')),
    );
  }

  @override
  String toString() =>
      'UploadInitializeResponse(uploadId: $uploadId, uploadUri: <redacted>, '
      'headerCount: ${headers.length}, expiresAt: $expiresAt)';
}

class UploadFinalizeRequest {
  final ProductIdentity productIdentity;
  final String uploadId;

  UploadFinalizeRequest({
    required this.productIdentity,
    required String uploadId,
  }) : uploadId = uploadId.trim() {
    _validateUploadId(this.uploadId);
  }
}

class ProductImageRef {
  final int productImageId;
  final int storageObjectId;
  final String uploadId;

  ProductImageRef({
    required this.productImageId,
    required this.storageObjectId,
    required String uploadId,
  }) : uploadId = uploadId.trim() {
    if (productImageId <= 0 || storageObjectId <= 0) {
      throw ArgumentError('Image and storage identifiers must be positive');
    }
    _validateUploadId(this.uploadId);
  }

  factory ProductImageRef.fromJson(Map<String, dynamic> json) {
    return ProductImageRef(
      productImageId: _requiredPositiveInt(json, 'product_image_id'),
      storageObjectId: _requiredPositiveInt(json, 'storage_object_id'),
      uploadId: _requiredString(json, 'upload_id'),
    );
  }
}

class UploadFinalizeResponse {
  final ProductImageRef productImage;

  const UploadFinalizeResponse({required this.productImage});

  factory UploadFinalizeResponse.fromJson(Map<String, dynamic> json) {
    if (_requiredString(json, 'status') != 'finalized') {
      throw const FormatException('status must be finalized');
    }
    return UploadFinalizeResponse(
      productImage: ProductImageRef.fromJson(json),
    );
  }
}

enum ExtractionRunStatus { pending, running, succeeded, failed, superseded }

class ExtractionRunRef {
  final int runId;
  final int? labelDocumentId;
  final ExtractionRunStatus status;
  final String? errorCode;

  const ExtractionRunRef({
    required this.runId,
    required this.status,
    this.labelDocumentId,
    this.errorCode,
  });

  factory ExtractionRunRef.fromJson(Map<String, dynamic> json) {
    final rawStatus = _requiredString(json, 'run_status');
    final status = ExtractionRunStatus.values.where(
      (candidate) => candidate.name == rawStatus,
    );
    if (status.isEmpty) {
      throw FormatException('Unsupported extraction run status: $rawStatus');
    }
    final labelDocumentId = json['label_document_id'];
    if (labelDocumentId != null &&
        (labelDocumentId is! int || labelDocumentId <= 0)) {
      throw const FormatException(
        'label_document_id must be a positive integer or absent',
      );
    }
    return ExtractionRunRef(
      runId: _requiredPositiveInt(json, 'id'),
      labelDocumentId: labelDocumentId as int?,
      status: status.single,
      errorCode: json['error_code'] as String?,
    );
  }
}

enum UploadFlowStep {
  disabled,
  missingToken,
  idle,
  productResolving,
  productRequired,
  imageSelected,
  metadataReady,
  uploadInitializing,
  binaryUploading,
  finalizing,
  uploadedAssociated,
  extractionStarting,
  extractionDeferred,
  failedRetryable,
  failedTerminal,
}

class UploadFlowState {
  final UploadFlowStep step;
  final ProductIdentity? productIdentity;
  final CaptureImagePurpose? purpose;
  final ImageMetadata? metadata;
  final ProductImageRef? productImage;
  final String? errorCode;

  const UploadFlowState({
    required this.step,
    this.productIdentity,
    this.purpose,
    this.metadata,
    this.productImage,
    this.errorCode,
  });

  UploadFlowState copyWith({
    required UploadFlowStep step,
    ProductIdentity? productIdentity,
    CaptureImagePurpose? purpose,
    ImageMetadata? metadata,
    ProductImageRef? productImage,
    String? errorCode,
  }) {
    return UploadFlowState(
      step: step,
      productIdentity: productIdentity ?? this.productIdentity,
      purpose: purpose ?? this.purpose,
      metadata: metadata ?? this.metadata,
      productImage: productImage ?? this.productImage,
      errorCode: errorCode,
    );
  }
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is! String || value.trim().isEmpty) {
    throw FormatException('$key must be a non-empty string');
  }
  return value;
}

int _requiredPositiveInt(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value is! int || value <= 0) {
    throw FormatException('$key must be a positive integer');
  }
  return value;
}

void _validateUploadId(String value) {
  if (!RegExp(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
  ).hasMatch(value)) {
    throw ArgumentError.value(value, 'uploadId', 'Must be a UUID');
  }
}
