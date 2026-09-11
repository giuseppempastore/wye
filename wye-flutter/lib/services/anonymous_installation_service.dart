import 'dart:math';

import 'package:shared_preferences/shared_preferences.dart';

class AnonymousInstallationService {
  static const _storageKey = 'wye_anonymous_installation_v1';
  String? _installationId;

  String? get currentId => _installationId;

  Future<String> ensureId() async {
    if (_installationId case final id?) return id;
    final preferences = await SharedPreferences.getInstance();
    final stored = preferences.getString(_storageKey);
    if (stored != null && RegExp(r'^[a-f0-9]{32}$').hasMatch(stored)) {
      return _installationId = stored;
    }
    final random = Random.secure();
    final generated = List.generate(
      32,
      (_) => random.nextInt(16).toRadixString(16),
    ).join();
    await preferences.setString(_storageKey, generated);
    return _installationId = generated;
  }
}
