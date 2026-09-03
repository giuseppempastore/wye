import 'capture_upload_models.dart';

enum CaptureUploadFailureKind {
  disabled,
  missingToken,
  invalidInput,
  transport,
  timeout,
  http,
  contract,
}

class CaptureUploadException implements Exception {
  final CaptureUploadFailureKind kind;
  final String code;
  final String safeMessage;
  final bool retryable;
  final UploadFlowStep lastStableStep;
  final int? statusCode;

  const CaptureUploadException({
    required this.kind,
    required this.code,
    required this.safeMessage,
    required this.retryable,
    required this.lastStableStep,
    this.statusCode,
  });

  @override
  String toString() =>
      'CaptureUploadException(code: $code, retryable: $retryable, '
      'statusCode: $statusCode, message: $safeMessage)';
}
