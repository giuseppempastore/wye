import 'photo_field_mapper.dart';

/// Central capture rules for Phase 9 photo flows.
class PhotoProcessingPolicy {
  static const int productMaxDimension = 2048;
  static const int productJpegQuality = 88;
  static const int documentMaxDimension = 3072;
  static const int documentJpegQuality = 94;

  const PhotoProcessingPolicy._();

  static bool requiresManualCrop(ProductPhotoPurpose purpose) =>
      purpose == ProductPhotoPurpose.productFront;
}
