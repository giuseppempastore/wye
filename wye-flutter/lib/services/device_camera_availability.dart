import 'dart:io';

import 'package:flutter/services.dart';

/// Prevents CameraX from starting when an Android emulator exposes zero
/// camera IDs. Some CameraX/plugin combinations terminate the whole process in
/// that state instead of returning a recoverable Flutter error.
class DeviceCameraAvailability {
  static const MethodChannel _channel =
      MethodChannel('wye/device_capabilities');

  const DeviceCameraAvailability();

  Future<bool> hasUsableCamera() async {
    if (!Platform.isAndroid) return true;
    try {
      return await _channel.invokeMethod<bool>('hasCamera') ?? false;
    } on PlatformException {
      return false;
    } on MissingPluginException {
      return false;
    }
  }
}

class PhotoQualityAssessment {
  final bool ok;
  final List<String> issues;

  const PhotoQualityAssessment({required this.ok, this.issues = const []});

  String get userMessage {
    final labels = <String>[
      if (issues.contains('low_resolution')) 'risoluzione troppo bassa',
      if (issues.contains('too_dark')) 'foto troppo scura',
      if (issues.contains('possibly_blurred')) 'foto probabilmente sfocata',
      if (issues.contains('unreadable')) 'file immagine non leggibile',
    ];
    return labels.isEmpty ? 'qualità non sufficiente' : labels.join(', ');
  }
}

class OnDevicePhotoQualityService {
  static const MethodChannel _channel =
      MethodChannel('wye/device_capabilities');

  const OnDevicePhotoQualityService();

  Future<PhotoQualityAssessment> assess(String path) async {
    if (!Platform.isAndroid) return const PhotoQualityAssessment(ok: true);
    try {
      final value = await _channel.invokeMapMethod<String, dynamic>(
        'assessPhoto',
        {'path': path},
      );
      return PhotoQualityAssessment(
        ok: value?['ok'] == true,
        issues: (value?['issues'] as List? ?? const [])
            .map((item) => item.toString())
            .toList(growable: false),
      );
    } on PlatformException {
      return const PhotoQualityAssessment(ok: false, issues: ['unreadable']);
    } on MissingPluginException {
      return const PhotoQualityAssessment(ok: false, issues: ['unreadable']);
    }
  }
}
