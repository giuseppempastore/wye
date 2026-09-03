import 'dart:typed_data';

import '../models/capture_upload_error.dart';
import '../models/capture_upload_models.dart';
import 'capture_upload_gateway.dart';

class FakeCaptureUploadGateway implements CaptureUploadGateway {
  final List<String> calls = [];
  CaptureUploadException? failure;
  UploadInitializeRequest? initializeRequest;
  Uint8List? uploadedBytes;

  @override
  Future<UploadInitializeResponse> initializeUpload(
    UploadInitializeRequest request,
  ) async {
    calls.add('initialize');
    initializeRequest = request;
    if (failure case final error?) {
      throw error;
    }
    return UploadInitializeResponse(
      uploadId: '00000000-0000-4000-8000-000000000001',
      uploadUri: Uri.parse('https://upload.invalid/<redacted>'),
      headers: {'Content-Type': request.metadata.mimeType},
      expiresAt: DateTime.utc(2030),
    );
  }

  @override
  Future<void> uploadBinary({
    required UploadInitializeResponse capability,
    required Uint8List bytes,
  }) async {
    calls.add('put');
    if (failure case final error?) {
      throw error;
    }
    uploadedBytes = Uint8List.fromList(bytes);
  }

  @override
  Future<UploadFinalizeResponse> finalizeUpload(
    UploadFinalizeRequest request,
  ) async {
    calls.add('finalize');
    if (failure case final error?) {
      throw error;
    }
    return UploadFinalizeResponse(
      productImage: ProductImageRef(
        productImageId: 401,
        storageObjectId: 301,
        uploadId: request.uploadId,
      ),
    );
  }

  @override
  void close() {}
}
