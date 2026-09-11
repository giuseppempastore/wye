import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/mobile_upload_config.dart';
import '../models/capture_upload_models.dart';

/// Internal Phase 9 transport capability. It is intentionally never exposed
/// as a user setting and remains memory-only.
class TechnicalSessionBootstrapper {
  final MobileUploadConfig config;
  final InMemoryMobileUploadTokenProvider credentialStore;
  final http.Client client;
  Future<bool>? _inFlight;

  TechnicalSessionBootstrapper({
    required this.config,
    required this.credentialStore,
    required this.client,
  });

  Future<bool> ensureReady() {
    if (!config.enabled) return Future.value(false);
    if (credentialStore.currentToken != null) return Future.value(true);
    return _inFlight ??= _bootstrap().whenComplete(() => _inFlight = null);
  }

  Future<bool> _bootstrap() async {
    try {
      final uri = config.apiBaseUri.replace(
        path: '/mobile/dev/v1/capture/anonymous-sessions',
        query: null,
        fragment: null,
      );
      final response = await client.post(uri).timeout(config.timeout);
      if (response.statusCode != 201) return false;
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final credential = payload['access_token'];
      final expiresAt =
          DateTime.tryParse(payload['expires_at']?.toString() ?? '');
      if (credential is! String || credential.isEmpty || expiresAt == null) {
        return false;
      }
      credentialStore.setToken(credential, expiresAt: expiresAt);
      return true;
    } on Object {
      return false;
    }
  }

  void close() => client.close();
}
