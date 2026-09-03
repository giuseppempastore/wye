import 'dart:typed_data';

import 'package:crypto/crypto.dart' as crypto;

import '../models/capture_upload_error.dart';
import '../models/capture_upload_models.dart';

abstract class ImageMetadataService {
  Future<ImageMetadata> inspect(Uint8List bytes);
}

class Sha256DigestService {
  const Sha256DigestService();

  String hash(Uint8List bytes) => crypto.sha256.convert(bytes).toString();
}

class Sha256ImageMetadataService implements ImageMetadataService {
  final Sha256DigestService _digestService;

  const Sha256ImageMetadataService({
    Sha256DigestService digestService = const Sha256DigestService(),
  }) : _digestService = digestService;

  @override
  Future<ImageMetadata> inspect(Uint8List bytes) async {
    if (bytes.isEmpty) {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.invalidInput,
        code: 'empty_image_bytes',
        safeMessage: 'Image bytes must not be empty',
        retryable: false,
        lastStableStep: UploadFlowStep.imageSelected,
      );
    }

    final mimeType = _detectMimeType(bytes);
    if (mimeType == null) {
      throw const CaptureUploadException(
        kind: CaptureUploadFailureKind.invalidInput,
        code: 'unsupported_image_format',
        safeMessage: 'Image format is not supported',
        retryable: false,
        lastStableStep: UploadFlowStep.imageSelected,
      );
    }

    return ImageMetadata(
      mimeType: mimeType,
      byteSize: bytes.length,
      sha256: _digestService.hash(bytes),
    );
  }

  String? _detectMimeType(Uint8List bytes) {
    if (_startsWith(bytes, const [0xff, 0xd8, 0xff])) {
      return 'image/jpeg';
    }
    if (_startsWith(
      bytes,
      const [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a],
    )) {
      return 'image/png';
    }
    if (bytes.length >= 12 &&
        _matchesAt(bytes, 0, const [0x52, 0x49, 0x46, 0x46]) &&
        _matchesAt(bytes, 8, const [0x57, 0x45, 0x42, 0x50])) {
      return 'image/webp';
    }
    return null;
  }

  bool _startsWith(Uint8List bytes, List<int> signature) =>
      _matchesAt(bytes, 0, signature);

  bool _matchesAt(Uint8List bytes, int offset, List<int> signature) {
    if (bytes.length < offset + signature.length) {
      return false;
    }
    for (var index = 0; index < signature.length; index++) {
      if (bytes[offset + index] != signature[index]) {
        return false;
      }
    }
    return true;
  }
}
