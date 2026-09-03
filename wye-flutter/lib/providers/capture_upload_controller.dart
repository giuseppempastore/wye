import 'package:flutter/foundation.dart';

import '../config/mobile_upload_config.dart';
import '../models/capture_upload_error.dart';
import '../models/capture_upload_models.dart';
import '../services/capture_upload_gateway.dart';

class CaptureUploadController extends ChangeNotifier {
  final MobileUploadConfig _config;
  final InMemoryMobileUploadTokenProvider _tokenProvider;
  final CaptureUploadGateway _gateway;

  UploadFlowState _state;
  ImageCaptureDraft? _draft;
  bool _transitionActive = false;

  CaptureUploadController({
    required MobileUploadConfig config,
    required InMemoryMobileUploadTokenProvider tokenProvider,
    required CaptureUploadGateway gateway,
  })  : _config = config,
        _tokenProvider = tokenProvider,
        _gateway = gateway,
        _state = UploadFlowState(
          step: !config.enabled
              ? UploadFlowStep.disabled
              : tokenProvider.currentToken == null
                  ? UploadFlowStep.missingToken
                  : UploadFlowStep.idle,
        );

  UploadFlowState get state => _state;

  bool get isTransitionActive => _transitionActive;

  void setTemporaryToken(String token, {required DateTime expiresAt}) {
    if (!_config.enabled) {
      _setState(const UploadFlowState(step: UploadFlowStep.disabled));
      return;
    }
    _tokenProvider.setToken(token, expiresAt: expiresAt);
    _setState(
      UploadFlowState(
        step: _tokenProvider.currentToken == null
            ? UploadFlowStep.missingToken
            : UploadFlowStep.idle,
      ),
    );
  }

  void clearTemporaryToken() {
    _tokenProvider.clear();
    _draft = null;
    _setState(
      UploadFlowState(
        step: _config.enabled
            ? UploadFlowStep.missingToken
            : UploadFlowStep.disabled,
      ),
    );
  }

  void markProductResolving() {
    if (_canStartLocalFlow()) {
      _setState(const UploadFlowState(step: UploadFlowStep.productResolving));
    }
  }

  void markProductRequired() {
    if (_canStartLocalFlow()) {
      _setState(const UploadFlowState(step: UploadFlowStep.productRequired));
    }
  }

  void selectImage({
    required ProductIdentity productIdentity,
    required CaptureImagePurpose purpose,
    required Uint8List bytes,
  }) {
    if (!_canStartLocalFlow()) {
      return;
    }
    _draft = ImageCaptureDraft(
      productIdentity: productIdentity,
      purpose: purpose,
      bytes: bytes,
    );
    _setState(
      UploadFlowState(
        step: UploadFlowStep.imageSelected,
        productIdentity: productIdentity,
        purpose: purpose,
      ),
    );
  }

  void setMetadata(ImageMetadata metadata) {
    final draft = _draft;
    if (draft == null) {
      throw StateError('An image must be selected before metadata is set');
    }
    if (metadata.byteSize != draft.bytes.length) {
      throw ArgumentError.value(
        metadata.byteSize,
        'metadata.byteSize',
        'Must match the exact upload bytes',
      );
    }
    _setState(
      _state.copyWith(
        step: UploadFlowStep.metadataReady,
        metadata: metadata,
      ),
    );
  }

  Future<void> upload() async {
    if (!_canStartLocalFlow() || _transitionActive) {
      return;
    }
    final draft = _draft;
    final metadata = _state.metadata;
    if (draft == null || metadata == null) {
      _fail(
        const CaptureUploadException(
          kind: CaptureUploadFailureKind.invalidInput,
          code: 'image_metadata_missing',
          safeMessage: 'Image metadata is required',
          retryable: false,
          lastStableStep: UploadFlowStep.imageSelected,
        ),
      );
      return;
    }

    _transitionActive = true;
    try {
      _setState(
        _state.copyWith(step: UploadFlowStep.uploadInitializing),
      );
      final initialized = await _gateway.initializeUpload(
        UploadInitializeRequest(
          productIdentity: draft.productIdentity,
          purpose: draft.purpose,
          metadata: metadata,
        ),
      );

      _setState(_state.copyWith(step: UploadFlowStep.binaryUploading));
      await _gateway.uploadBinary(
        capability: initialized,
        bytes: draft.bytes,
      );

      _setState(_state.copyWith(step: UploadFlowStep.finalizing));
      final imageRef = await _gateway.finalizeUpload(
        UploadFinalizeRequest(
          productIdentity: draft.productIdentity,
          uploadId: initialized.uploadId,
        ),
      );

      final extractionDeferred =
          draft.purpose == CaptureImagePurpose.ingredients ||
              draft.purpose == CaptureImagePurpose.nutrition;
      _setState(
        _state.copyWith(
          step: extractionDeferred
              ? UploadFlowStep.extractionDeferred
              : UploadFlowStep.uploadedAssociated,
          productImage: imageRef.productImage,
        ),
      );
    } on CaptureUploadException catch (error) {
      _fail(error);
    } on Object {
      _fail(
        const CaptureUploadException(
          kind: CaptureUploadFailureKind.transport,
          code: 'capture_upload_failed',
          safeMessage: 'Capture upload failed',
          retryable: true,
          lastStableStep: UploadFlowStep.metadataReady,
        ),
      );
    } finally {
      _transitionActive = false;
    }
  }

  Future<void> retry() async {
    if (_state.step != UploadFlowStep.failedRetryable) {
      return;
    }
    _setState(_state.copyWith(step: UploadFlowStep.metadataReady));
    await upload();
  }

  void reset() {
    _draft = null;
    _setState(
      UploadFlowState(
        step: !_config.enabled
            ? UploadFlowStep.disabled
            : _tokenProvider.currentToken == null
                ? UploadFlowStep.missingToken
                : UploadFlowStep.idle,
      ),
    );
  }

  bool _canStartLocalFlow() {
    if (!_config.enabled) {
      _setState(const UploadFlowState(step: UploadFlowStep.disabled));
      return false;
    }
    if (_tokenProvider.currentToken == null) {
      _setState(const UploadFlowState(step: UploadFlowStep.missingToken));
      return false;
    }
    return true;
  }

  void _fail(CaptureUploadException error) {
    if (error.kind == CaptureUploadFailureKind.disabled) {
      _setState(const UploadFlowState(step: UploadFlowStep.disabled));
      return;
    }
    if (error.kind == CaptureUploadFailureKind.missingToken) {
      _tokenProvider.clear();
      _setState(
        UploadFlowState(
          step: UploadFlowStep.missingToken,
          productIdentity: _state.productIdentity,
          purpose: _state.purpose,
          metadata: _state.metadata,
          errorCode: error.code,
        ),
      );
      return;
    }
    _setState(
      _state.copyWith(
        step: error.retryable
            ? UploadFlowStep.failedRetryable
            : UploadFlowStep.failedTerminal,
        errorCode: error.code,
      ),
    );
  }

  void _setState(UploadFlowState value) {
    _state = value;
    notifyListeners();
  }

  @override
  void dispose() {
    _tokenProvider.clear();
    _draft = null;
    super.dispose();
  }
}
