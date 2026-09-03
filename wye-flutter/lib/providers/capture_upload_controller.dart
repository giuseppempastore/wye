import 'package:flutter/foundation.dart';

import '../config/mobile_upload_config.dart';
import '../models/capture_upload_error.dart';
import '../models/capture_upload_models.dart';
import '../models/extraction_models.dart';
import '../services/capture_upload_gateway.dart';
import '../services/capture_flow_logger.dart';
import '../services/image_metadata_service.dart';

enum DevMobileTokenState { missing, present, expired }

class CaptureUploadController extends ChangeNotifier {
  final MobileUploadConfig _config;
  final InMemoryMobileUploadTokenProvider _tokenProvider;
  final CaptureUploadGateway _gateway;
  final ImageMetadataService _metadataService;
  final CaptureFlowLogger _logger;

  UploadFlowState _state;
  ExtractionFlowState _extractionState = const ExtractionFlowState(
    step: ExtractionFlowStep.notStarted,
  );
  ImageCaptureDraft? _draft;
  bool _transitionActive = false;
  DateTime? _tokenExpiresAt;
  int _uploadRetryCount = 0;
  int _extractionRetryCount = 0;

  CaptureUploadController({
    required MobileUploadConfig config,
    required InMemoryMobileUploadTokenProvider tokenProvider,
    required CaptureUploadGateway gateway,
    required ImageMetadataService metadataService,
    CaptureFlowLogger logger = const NoOpCaptureFlowLogger(),
  })  : _config = config,
        _tokenProvider = tokenProvider,
        _gateway = gateway,
        _metadataService = metadataService,
        _logger = logger,
        _state = UploadFlowState(
          step: !config.enabled
              ? UploadFlowStep.disabled
              : tokenProvider.currentToken == null
                  ? UploadFlowStep.missingToken
                  : UploadFlowStep.idle,
        ) {
    _tokenExpiresAt = tokenProvider.currentToken?.expiresAt;
  }

  UploadFlowState get state => _state;

  ExtractionFlowState get extractionState => _extractionState;

  bool get isTransitionActive => _transitionActive;

  DateTime? get tokenExpiresAt => _tokenExpiresAt;

  DevMobileTokenState get tokenState {
    final expiry = _tokenExpiresAt;
    if (expiry != null && !expiry.isAfter(DateTime.now().toUtc())) {
      return DevMobileTokenState.expired;
    }
    return _tokenProvider.currentToken == null
        ? DevMobileTokenState.missing
        : DevMobileTokenState.present;
  }

  void setTemporaryToken(String token, {required DateTime expiresAt}) {
    if (!_config.enabled) {
      _setState(const UploadFlowState(step: UploadFlowStep.disabled));
      return;
    }
    _tokenExpiresAt = expiresAt.toUtc();
    _tokenProvider.setToken(token, expiresAt: _tokenExpiresAt!);
    _extractionState = const ExtractionFlowState(
      step: ExtractionFlowStep.notStarted,
    );
    _setState(
      UploadFlowState(
        step: _tokenProvider.currentToken == null
            ? UploadFlowStep.missingToken
            : UploadFlowStep.idle,
      ),
    );
    _record(
      'token_state_changed',
      statusClass: _tokenProvider.currentToken == null ? 'failure' : 'success',
      errorCode: _tokenProvider.currentToken == null ? 'token_expired' : null,
    );
  }

  void clearTemporaryToken() {
    _tokenExpiresAt = null;
    _tokenProvider.clear();
    _draft = null;
    _extractionState = const ExtractionFlowState(
      step: ExtractionFlowStep.notStarted,
    );
    _setState(
      UploadFlowState(
        step: _config.enabled
            ? UploadFlowStep.missingToken
            : UploadFlowStep.disabled,
      ),
    );
    _record('token_cleared', statusClass: 'success');
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
    _uploadRetryCount = 0;
    _extractionRetryCount = 0;
    _extractionState = const ExtractionFlowState(
      step: ExtractionFlowStep.notStarted,
    );
    _setState(
      UploadFlowState(
        step: UploadFlowStep.imageSelected,
        productIdentity: productIdentity,
        purpose: purpose,
      ),
    );
    _record(
      'image_selected',
      statusClass: 'success',
      productId: productIdentity.productId,
      purpose: purpose,
    );
  }

  Future<void> prepareMetadata() async {
    if (!_canStartLocalFlow() || _transitionActive) {
      return;
    }
    final draft = _draft;
    if (draft == null) {
      _fail(
        const CaptureUploadException(
          kind: CaptureUploadFailureKind.invalidInput,
          code: 'image_missing',
          safeMessage: 'An image must be selected before metadata is prepared',
          retryable: false,
          lastStableStep: UploadFlowStep.idle,
        ),
      );
      return;
    }

    _transitionActive = true;
    try {
      final metadata = await _metadataService.inspect(draft.bytes);
      if (metadata.byteSize != draft.bytes.length) {
        throw const CaptureUploadException(
          kind: CaptureUploadFailureKind.contract,
          code: 'image_metadata_size_mismatch',
          safeMessage: 'Image metadata does not match upload bytes',
          retryable: false,
          lastStableStep: UploadFlowStep.imageSelected,
        );
      }
      _setState(
        _state.copyWith(
          step: UploadFlowStep.metadataReady,
          metadata: metadata,
        ),
      );
      _record(
        'metadata_prepared',
        statusClass: 'success',
        productId: draft.productIdentity.productId,
        purpose: draft.purpose,
      );
    } on CaptureUploadException catch (error) {
      _fail(error);
    } on Object {
      _fail(
        const CaptureUploadException(
          kind: CaptureUploadFailureKind.contract,
          code: 'image_metadata_failed',
          safeMessage: 'Image metadata could not be prepared',
          retryable: false,
          lastStableStep: UploadFlowStep.imageSelected,
        ),
      );
    } finally {
      _transitionActive = false;
    }
  }

  Future<void> upload() async {
    if (!_canStartLocalFlow() ||
        _transitionActive ||
        _state.step == UploadFlowStep.failedTerminal) {
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
      _setExtractionState(
        ExtractionFlowState(
          step: extractionDeferred
              ? ExtractionFlowStep.deferred
              : ExtractionFlowStep.unavailable,
          errorCode:
              extractionDeferred ? null : 'extraction_purpose_unsupported',
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
    _uploadRetryCount += 1;
    _record(
      'upload_retry',
      statusClass: 'local',
      retryCount: _uploadRetryCount,
      productId: _state.productIdentity?.productId,
      purpose: _state.purpose,
    );
    _setState(_state.copyWith(step: UploadFlowStep.metadataReady));
    await upload();
  }

  Future<void> startExtraction() async {
    if (_transitionActive) {
      return;
    }
    final context = _validatedExtractionContext();
    if (context == null) {
      return;
    }
    _transitionActive = true;
    _setExtractionState(
      const ExtractionFlowState(step: ExtractionFlowStep.starting),
    );
    try {
      final result = await _gateway.startExtraction(
        productIdentity: context.productIdentity,
        productImage: context.productImage,
        idempotencyKey: 'mobile-extraction-'
            '${context.productIdentity.productId}-'
            '${context.productImage.productImageId}',
      );
      _applyExtractionResult(result);
    } on CaptureUploadException catch (error) {
      _failExtraction(error);
    } on Object {
      _failExtraction(
        const CaptureUploadException(
          kind: CaptureUploadFailureKind.transport,
          code: 'mobile_extraction_failed',
          safeMessage: 'Extraction request failed',
          retryable: true,
          lastStableStep: UploadFlowStep.extractionDeferred,
        ),
      );
    } finally {
      _transitionActive = false;
      notifyListeners();
    }
  }

  Future<void> refreshExtraction() async {
    if (_transitionActive) {
      return;
    }
    final context = _validatedExtractionContext();
    final runId = _extractionState.result?.run.extractionRunId;
    if (context == null) {
      return;
    }
    if (runId == null || runId <= 0) {
      _setExtractionState(
        const ExtractionFlowState(
          step: ExtractionFlowStep.failedTerminal,
          errorCode: 'extraction_run_id_missing',
        ),
      );
      return;
    }
    _transitionActive = true;
    _setExtractionState(
      ExtractionFlowState(
        step: ExtractionFlowStep.loading,
        result: _extractionState.result,
      ),
    );
    try {
      final result = await _gateway.getExtraction(
        productIdentity: context.productIdentity,
        productImage: context.productImage,
        extractionRunId: runId,
      );
      _applyExtractionResult(result);
    } on CaptureUploadException catch (error) {
      _failExtraction(error);
    } on Object {
      _failExtraction(
        const CaptureUploadException(
          kind: CaptureUploadFailureKind.transport,
          code: 'mobile_extraction_failed',
          safeMessage: 'Extraction request failed',
          retryable: true,
          lastStableStep: UploadFlowStep.extractionDeferred,
        ),
      );
    } finally {
      _transitionActive = false;
      notifyListeners();
    }
  }

  Future<void> retryExtraction() async {
    if (_extractionState.step != ExtractionFlowStep.failedRetryable) {
      return;
    }
    _extractionRetryCount += 1;
    _record(
      'extraction_retry',
      statusClass: 'local',
      retryCount: _extractionRetryCount,
      productId: _state.productIdentity?.productId,
      purpose: _state.purpose,
      productImageId: _state.productImage?.productImageId,
      storageObjectId: _state.productImage?.storageObjectId,
      extractionRunId: _extractionState.result?.run.extractionRunId,
    );
    if (_extractionState.result?.run.extractionRunId case final int runId
        when runId > 0) {
      await refreshExtraction();
    } else {
      await startExtraction();
    }
  }

  void reset() {
    _draft = null;
    _extractionState = const ExtractionFlowState(
      step: ExtractionFlowStep.notStarted,
    );
    _uploadRetryCount = 0;
    _extractionRetryCount = 0;
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

  _ExtractionContext? _validatedExtractionContext() {
    if (!_config.enabled) {
      _setExtractionState(
        const ExtractionFlowState(
          step: ExtractionFlowStep.unavailable,
          errorCode: 'mobile_upload_disabled',
        ),
      );
      _record(
        'extraction_unavailable',
        statusClass: 'failure',
        errorCode: 'mobile_upload_disabled',
      );
      return null;
    }
    if (_tokenProvider.currentToken == null) {
      _setExtractionState(
        const ExtractionFlowState(
          step: ExtractionFlowStep.failedTerminal,
          errorCode: 'mobile_token_missing',
        ),
      );
      _record(
        'extraction_failed',
        statusClass: 'failure',
        errorCode: 'mobile_token_missing',
      );
      return null;
    }
    final identity = _state.productIdentity;
    final image = _state.productImage;
    final purpose = _state.purpose;
    if (identity == null || image == null) {
      _setExtractionState(
        const ExtractionFlowState(
          step: ExtractionFlowStep.failedTerminal,
          errorCode: 'extraction_image_not_finalized',
        ),
      );
      _record(
        'extraction_failed',
        statusClass: 'failure',
        errorCode: 'extraction_image_not_finalized',
      );
      return null;
    }
    if (purpose != CaptureImagePurpose.ingredients &&
        purpose != CaptureImagePurpose.nutrition) {
      _setExtractionState(
        const ExtractionFlowState(
          step: ExtractionFlowStep.unavailable,
          errorCode: 'extraction_purpose_unsupported',
        ),
      );
      _record(
        'extraction_unavailable',
        statusClass: 'failure',
        productId: identity.productId,
        purpose: purpose,
        productImageId: image.productImageId,
        storageObjectId: image.storageObjectId,
        errorCode: 'extraction_purpose_unsupported',
      );
      return null;
    }
    if (_state.step != UploadFlowStep.extractionDeferred) {
      _setExtractionState(
        const ExtractionFlowState(
          step: ExtractionFlowStep.failedTerminal,
          errorCode: 'extraction_image_not_finalized',
        ),
      );
      _record(
        'extraction_failed',
        statusClass: 'failure',
        productId: identity.productId,
        purpose: purpose,
        productImageId: image.productImageId,
        storageObjectId: image.storageObjectId,
        errorCode: 'extraction_image_not_finalized',
      );
      return null;
    }
    return _ExtractionContext(identity, image);
  }

  void _applyExtractionResult(ExtractionResultSummary result) {
    final step = switch (result.run.status) {
      ExtractionStatus.pending ||
      ExtractionStatus.running =>
        ExtractionFlowStep.loading,
      ExtractionStatus.succeeded => ExtractionFlowStep.succeeded,
      ExtractionStatus.failed => ExtractionFlowStep.failedTerminal,
      ExtractionStatus.superseded => ExtractionFlowStep.unavailable,
    };
    _setExtractionState(
      ExtractionFlowState(
        step: step,
        result: result,
        errorCode: result.run.errorCode,
      ),
    );
    _record(
      'extraction_result',
      statusClass: result.run.status == ExtractionStatus.succeeded
          ? 'success'
          : result.run.status == ExtractionStatus.failed
              ? 'failure'
              : 'local',
      productId: _state.productIdentity?.productId,
      purpose: _state.purpose,
      productImageId: _state.productImage?.productImageId,
      storageObjectId: _state.productImage?.storageObjectId,
      extractionRunId: result.run.extractionRunId,
      itemCount: result.items.length,
      errorCode: result.run.errorCode,
    );
  }

  void _failExtraction(CaptureUploadException error) {
    _setExtractionState(
      ExtractionFlowState(
        step: error.retryable
            ? ExtractionFlowStep.failedRetryable
            : ExtractionFlowStep.failedTerminal,
        result: _extractionState.result,
        errorCode: error.code,
      ),
    );
    _recordFailure(
      error.retryable
          ? 'extraction_flow_failed_retryable'
          : 'extraction_flow_failed_terminal',
      error,
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
    _recordFailure(
      error.retryable
          ? 'upload_flow_failed_retryable'
          : 'upload_flow_failed_terminal',
      error,
    );
    if (error.kind == CaptureUploadFailureKind.disabled) {
      _setState(const UploadFlowState(step: UploadFlowStep.disabled));
      return;
    }
    if (error.kind == CaptureUploadFailureKind.missingToken) {
      _tokenExpiresAt = null;
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

  void _setExtractionState(ExtractionFlowState value) {
    _extractionState = value;
    notifyListeners();
  }

  void _recordFailure(String step, CaptureUploadException error) {
    _record(
      step,
      statusClass: error.statusCode == null
          ? 'failure'
          : '${error.statusCode! ~/ 100}xx',
      productId: _state.productIdentity?.productId,
      purpose: _state.purpose,
      productImageId: _state.productImage?.productImageId,
      storageObjectId: _state.productImage?.storageObjectId,
      extractionRunId: _extractionState.result?.run.extractionRunId,
      httpStatusCode: error.statusCode,
      retryCount: step.startsWith('extraction')
          ? _extractionRetryCount
          : _uploadRetryCount,
      errorCode: error.code,
      errorCategory: error.kind.name.toLowerCase(),
    );
  }

  void _record(
    String step, {
    required String statusClass,
    int? productId,
    CaptureImagePurpose? purpose,
    int? productImageId,
    int? storageObjectId,
    int? extractionRunId,
    int? itemCount,
    int? httpStatusCode,
    int? retryCount,
    String? errorCode,
    String? errorCategory,
  }) {
    _logger.record(
      CaptureFlowEvent(
        step: step,
        statusClass: statusClass,
        productId: productId,
        purpose: purpose,
        productImageId: productImageId,
        storageObjectId: storageObjectId,
        extractionRunId: extractionRunId,
        itemCount: itemCount,
        httpStatusCode: httpStatusCode,
        retryCount: retryCount,
        errorCode: errorCode,
        errorCategory: errorCategory,
      ),
    );
  }

  @override
  void dispose() {
    _tokenExpiresAt = null;
    _tokenProvider.clear();
    _draft = null;
    super.dispose();
  }
}

class _ExtractionContext {
  final ProductIdentity productIdentity;
  final ProductImageRef productImage;

  const _ExtractionContext(this.productIdentity, this.productImage);
}
