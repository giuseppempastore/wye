import 'dart:typed_data';

import '../models/capture_upload_models.dart';
import '../models/extraction_models.dart';

abstract class CaptureUploadGateway {
  Future<UploadInitializeResponse> initializeUpload(
    UploadInitializeRequest request,
  );

  Future<void> uploadBinary({
    required UploadInitializeResponse capability,
    required Uint8List bytes,
  });

  Future<UploadFinalizeResponse> finalizeUpload(UploadFinalizeRequest request);

  Future<ExtractionResultSummary> startExtraction({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
    required String idempotencyKey,
  });

  Future<List<ExtractionRunRef>> listExtractions({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
  });

  Future<ExtractionResultSummary> getExtraction({
    required ProductIdentity productIdentity,
    required ProductImageRef productImage,
    required int extractionRunId,
  });

  void close();
}
