class MobileUploadConfig {
  static const bool enabledByBuild = bool.fromEnvironment(
    'WYE_MOBILE_UPLOAD_ENABLED',
    defaultValue: false,
  );

  final bool enabled;
  final Uri apiBaseUri;
  final Duration timeout;

  MobileUploadConfig({
    required this.enabled,
    required this.apiBaseUri,
    this.timeout = const Duration(seconds: 30),
  }) {
    if (!apiBaseUri.hasScheme || apiBaseUri.host.isEmpty) {
      throw ArgumentError.value(apiBaseUri, 'apiBaseUri', 'Must be absolute');
    }
    if (apiBaseUri.scheme != 'http' && apiBaseUri.scheme != 'https') {
      throw ArgumentError.value(apiBaseUri, 'apiBaseUri', 'Unsupported scheme');
    }
    if (apiBaseUri.userInfo.isNotEmpty ||
        apiBaseUri.hasQuery ||
        apiBaseUri.hasFragment) {
      throw ArgumentError.value(
        apiBaseUri,
        'apiBaseUri',
        'Credentials, query and fragment are not allowed',
      );
    }
  }

  factory MobileUploadConfig.fromEnvironment({required String apiBaseUrl}) {
    return MobileUploadConfig(
      enabled: enabledByBuild,
      apiBaseUri: Uri.parse(apiBaseUrl),
    );
  }
}
