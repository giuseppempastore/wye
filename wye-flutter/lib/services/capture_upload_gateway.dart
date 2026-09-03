import 'dart:typed_data';

import '../models/capture_upload_models.dart';

abstract class CaptureUploadGateway {
  Future<UploadInitializeResponse> initializeUpload(
    UploadInitializeRequest request,
  );

  Future<void> uploadBinary({
    required UploadInitializeResponse capability,
    required Uint8List bytes,
  });

  Future<UploadFinalizeResponse> finalizeUpload(UploadFinalizeRequest request);

  void close();
}
