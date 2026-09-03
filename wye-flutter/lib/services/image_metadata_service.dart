import 'dart:typed_data';

import '../models/capture_upload_error.dart';
import '../models/capture_upload_models.dart';

abstract class ImageMetadataService {
  Future<ImageMetadata> inspect(Uint8List bytes);
}

class Sha256MetadataUnavailableService implements ImageMetadataService {
  const Sha256MetadataUnavailableService();

  @override
  Future<ImageMetadata> inspect(Uint8List bytes) async {
    throw const CaptureUploadException(
      kind: CaptureUploadFailureKind.contract,
      code: 'sha256_dependency_unavailable',
      safeMessage: 'Image hashing is not available in this build',
      retryable: false,
      lastStableStep: UploadFlowStep.imageSelected,
    );
  }
}
