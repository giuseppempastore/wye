import 'dart:io';

import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'photo_field_mapper.dart';

typedef LostImageRetriever = Future<LostDataResponse> Function();

class RecoveredProductPhoto {
  final XFile file;
  final ProductPhotoPurpose purpose;

  const RecoveredProductPhoto({required this.file, required this.purpose});
}

/// Recovers Android camera results when the OS destroys MainActivity while the
/// external camera intent is open. Only purpose and a temporary cache path are
/// persisted; neither value is logged or exported as test evidence.
class PhotoCaptureRecoveryService {
  static final PhotoCaptureRecoveryService shared =
      PhotoCaptureRecoveryService();

  static const _purposeKey = 'phase9_pending_photo_purpose';
  static const _capturedPathKey = 'phase9_pending_photo_cache_path';

  final LostImageRetriever _retrieveLostData;
  RecoveredProductPhoto? _recovered;
  String? _safeRecoveryCode;

  PhotoCaptureRecoveryService({LostImageRetriever? retrieveLostData})
      : _retrieveLostData = retrieveLostData ?? ImagePicker().retrieveLostData;

  String? get safeRecoveryCode => _safeRecoveryCode;
  bool get hasRecoveredPhoto => _recovered != null;

  Future<void> initialize() async {
    try {
      final preferences = await SharedPreferences.getInstance();
      final purpose = _decodePurpose(preferences.getString(_purposeKey));
      final response = await _retrieveLostData();
      XFile? file = response.files?.firstOrNull ?? response.file;
      final cachedPath = preferences.getString(_capturedPathKey);
      if (file == null &&
          cachedPath != null &&
          cachedPath.isNotEmpty &&
          await File(cachedPath).exists()) {
        file = XFile(cachedPath);
      }
      if (purpose != null && file != null) {
        _recovered = RecoveredProductPhoto(file: file, purpose: purpose);
        _safeRecoveryCode = 'photo_capture_recovered';
        return;
      }
      if (!response.isEmpty || purpose != null) {
        _safeRecoveryCode = response.exception == null
            ? 'photo_capture_recovery_empty'
            : 'photo_capture_recovery_failed';
      }
      await clearPending();
    } on Object {
      _safeRecoveryCode = 'photo_capture_recovery_failed';
    }
  }

  Future<void> begin(ProductPhotoPurpose purpose) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(_purposeKey, purpose.name);
    await preferences.remove(_capturedPathKey);
  }

  Future<void> markCaptured(XFile file) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(_capturedPathKey, file.path);
  }

  RecoveredProductPhoto? takeRecovered() {
    final value = _recovered;
    _recovered = null;
    return value;
  }

  Future<void> clearPending() async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.remove(_purposeKey);
    await preferences.remove(_capturedPathKey);
  }

  static ProductPhotoPurpose? _decodePurpose(String? value) {
    for (final purpose in ProductPhotoPurpose.values) {
      if (purpose.name == value) return purpose;
    }
    return null;
  }
}
