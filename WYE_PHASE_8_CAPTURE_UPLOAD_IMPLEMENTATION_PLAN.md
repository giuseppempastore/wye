# WYE — Phase 8.5 Capture / Upload Implementation Plan

## 1. Status, scope, and authority

    phase: Phase 8.5.2 — capture/upload implementation plan
    input_contract: WYE_PHASE_8_CAPTURE_UPLOAD_FLOW.md
    artifact_scope: planning and documentation only
    flutter_runtime_changes_authorized: NO
    backend_runtime_changes_authorized: NO
    live_endpoint_calls_authorized: NO
    scoring_runtime_authority: NONE
    release_authority: NONE
    overall_numerical_candidate: NONE / DEFERRED

This document translates the Phase 8.5.1 contract into a proposed, reviewable
implementation sequence. It does not implement or authorize product creation,
image upload, extraction, scoring, deployment, or release.

The Phase 7/8 constraints remain controlling. Capture and extraction produce
identifiers, storage metadata, and reviewable label data; they do not produce a
product assessment. No missing, failed, or deferred state may become zero, an
average, a placeholder, an imputation, or an overall score. Ingredient and
nutrition result states remain separate. No medical, clinical, therapeutic,
dietetic, personal-suitability, safety, healthiness, regulatory, certification,
or approval claim is authorized.

## 2. Selected mobile authorization boundary

### 2.1 Selected architecture

The selected boundary is:

```text
Flutter UI
  -> CaptureUploadController
  -> CaptureUploadGateway
  -> FastAPI mobile capture façade over configured LAN API_BASE_URL
  -> existing ImageUploadService / LabelExtractionService
  -> PostgreSQL and MinIO/S3

Flutter binary uploader
  -> one temporary presigned object-storage URL for raw binary PUT only
```

Rules:

1. Flutter uses FastAPI for all WYE control-plane operations: product
   resolution, product creation, upload initialization, finalization,
   extraction start, and extraction result retrieval.
2. The only non-FastAPI request is the raw binary PUT to the temporary
   presigned object-storage URL returned by FastAPI.
3. Flutter never contains or sends `X-WYE-Image-Key`. It also never contains
   storage, database, extraction-provider, or other server credentials.
4. The existing protected operational routes remain protected. The mobile
   façade calls the underlying services server-side; it must not relay the
   shared image key to or from the app.
5. Mobile façade access requires a separately reviewed, short-lived and scoped
   development session or equivalent safe local authorization mechanism. An
   unauthenticated LAN endpoint is not an acceptable substitute.
6. The upload URL and any mobile session token are temporary capabilities.
   They are memory-only, redacted from logs, and discarded at expiry or flow
   completion.
7. `API_BASE_URL` and the host embedded in the presigned MinIO/S3 URL must both
   be reachable from the physical phone. A `localhost`-only signed URL is a
   blocking configuration error.
8. Neither the façade nor the Flutter flow imports, calls, or maps scoring
   services or legacy `/analyze` and `/analyze-image` endpoints.

### 2.2 Blocking backend prerequisite

The current backend has no mobile-safe façade/session endpoint. Its image and
extraction routes require the shared `X-WYE-Image-Key`. Therefore live Flutter
integration is blocked until a separately authorized backend phase supplies:

- a versioned mobile capture façade;
- a reviewed short-lived, operation-scoped development authorization model;
- product ownership/submission scope sufficient for the requested product;
- stable response and error envelopes;
- a presigning endpoint that emits a device-reachable host;
- server-side correlation propagation without exposing secrets.

Until that prerequisite passes review, a Flutter runtime phase may implement
only pure DTOs, state transitions, fixtures, fake gateways, and widget behavior.
It must not call the existing protected routes directly and must not fall back
to base64 or legacy analysis endpoints.

## 3. Proposed implementation slices and gates

| Slice | Scope | Entry gate | Exit gate |
| --- | --- | --- | --- |
| A | Pure frontend models, metadata service, state reducer/controller, fixtures, and fake gateway | Plan reviewed and runtime work separately authorized | Unit tests pass; no HTTP and no scoring dependencies |
| B | Backend mobile façade/session prerequisite | Separate backend authorization and security review | Contract tests prove scope, expiry, redaction, and no image-key exposure |
| C | HTTP gateway and binary uploader behind a disabled feature flag | Slice B contract frozen; reachable development storage configured | Fake-transport tests pass; no live calls in CI |
| D | Add-product UI integration and safe history/result references | Slices A–C reviewed; UI scope authorized | Widget/state tests pass; legacy base64 paths are not used by the new flow |
| E | Physical-device validation | Phase 8.6 explicitly authorized | Redacted E2E record complete; rollback switch verified |

No slice may silently enable the next one. The feature flag defaults to off
until the physical-device environment and mobile authorization boundary are
both approved.

## 4. File-by-file frontend implementation plan

The paths below are proposed changes for a later authorized runtime phase.

### 4.1 Models and immutable contracts

| File | Planned change |
| --- | --- |
| `wye-flutter/lib/models/product_model.dart` | Preserve backend `id` as nullable `productId` for legacy compatibility; parse only integer `id`/approved transport field; carry it through serialization/history without treating barcode as an ID. Construct `ProductIdentity` only when a positive ID and matching non-empty barcode exist. Keep `scoreView` unchanged and continue ignoring legacy score placeholders. |
| `wye-flutter/lib/models/capture_upload_models.dart` (new) | Define the DTOs and enums in section 6 with validation, immutable collections, explicit wire parsing, and capability-safe `toString` behavior. No scoring fields. |
| `wye-flutter/lib/models/capture_upload_error.dart` (new) | Define structured local/transport/HTTP/application/storage failures, retryability, safe diagnostic code, last stable state, and related non-secret IDs. Never retain raw bodies, image bytes, signed URLs, or credentials. |

`Product.productId` remains nullable because existing cached/mock products have
no backend identity. `ProductIdentity.productId` is required and positive. An
upload method accepts `ProductIdentity`, never a bare barcode or nullable ID.

### 4.2 Metadata, transport, and logging services

| File | Planned change |
| --- | --- |
| `wye-flutter/pubspec.yaml` | Add an explicitly pinned direct SHA-256 dependency such as `crypto` only after dependency/lockfile policy and network authorization are approved. Do not add a MIME dependency unless magic-byte tests show it is needed. |
| `wye-flutter/lib/services/image_metadata_service.dart` (new) | Read the final post-crop file, identify JPEG/PNG/WebP by content signature, calculate byte size and lowercase SHA-256 over the exact bytes to upload, enforce local size policy, and return `ImageMetadata`. No base64 conversion. |
| `wye-flutter/lib/services/capture_upload_gateway.dart` (new) | Define the control-plane interface: resolve/create product identity, initialize upload, finalize upload, start/retrieve extraction. Method signatures accept typed DTOs and a correlation context. |
| `wye-flutter/lib/services/http_capture_upload_gateway.dart` (new) | Implement only the reviewed mobile façade contract using an injected `http.Client`, `API_BASE_URL`, safe session provider, timeout policy, and sanitized logger. It must not know `X-WYE-Image-Key` and must reject unexpected secret-bearing headers. |
| `wye-flutter/lib/services/presigned_binary_uploader.dart` (new) | PUT exact file bytes to the presigned URL with only returned allowlisted headers. Return status/latency, not the URL. Do not follow redirects to an unapproved host and do not log request URI/query or body. |
| `wye-flutter/lib/services/capture_flow_logger.dart` (new) | Emit structured redacted events described in section 9. Provide a test sink. Values classified as secret/capability/raw payload must be unrepresentable or redacted before reaching `logger`. |
| `wye-flutter/lib/services/api_client.dart` | Inject the HTTP transport instead of constructing it internally; add or adapt product resolve/create methods so raw `product.id` is preserved. Do not add the mobile image key. The new capture path must not call `analyzeIngredients`, `analyzeProductImage`, or score mappers. |
| `wye-flutter/lib/services/mock_api_client.dart` | Give mock products deterministic positive `productId` values where they represent server products; retain unavailable/deferred overall behavior. Do not calculate a score and do not simulate upload by calling legacy analysis. |
| `wye-flutter/lib/services/fake_capture_upload_gateway.dart` (new) | Provide deterministic in-memory identities, upload IDs, image/storage IDs, extraction states, delays, and injected failures. Never create a full signed URL in fixtures; use a reserved invalid host or an opaque fake capability. |

If dependency approval is unavailable, Slice A uses a metadata interface plus a
deterministic fake digest implementation in tests. It must not ship a weak or
invented checksum implementation.

### 4.3 State management and dependency injection

| File | Planned change |
| --- | --- |
| `wye-flutter/lib/providers/capture_upload_controller.dart` (new) | Implement a `ChangeNotifier` controller over an immutable `UploadFlowState`. Own cancellation, one active transition at a time, retry routing, capability disposal, and correlation ID. Delegate all I/O to injected interfaces. |
| `wye-flutter/lib/providers/app_providers.dart` | Keep existing barcode/product provider behavior isolated. Share a resolved `ProductIdentity` explicitly when entering capture; do not merge upload failures into score state or generic product-not-found state. |
| `wye-flutter/lib/main.dart` | Register metadata service, safe logger, gateway, binary uploader, and controller through Provider. Select fake versus HTTP gateway only from the disabled-by-default capture feature configuration. No secret configuration is read by Flutter. |
| `wye-flutter/lib/config/capture_feature_config.dart` (new) | Define compile-time non-secret enablement and allowed upload-host policy. Reject enabling live mode without an explicit API base URL and approved session provider. Never accept credentials. |

The controller exposes commands, not mutable fields: `resolveProduct`,
`selectImage`, `computeMetadata`, `initializeUpload`, `uploadBytes`, `finalize`,
`startExtraction`, `refreshExtraction`, `retry`, `cancel`, and `reset`.

### 4.4 Screens, widgets, navigation, and history

| File | Planned change |
| --- | --- |
| `wye-flutter/lib/screens/add_product_screen.dart` | Make this the only initial capture/upload surface. Image selection creates a purpose-specific local draft and no automatic network call. Remove the new flow's base64 construction and legacy `/analyze-image` use; omit legacy image URL fields from product creation. Resolve/create product first, then execute one image flow at a time. Backend extraction, not local OCR, supplies canonical ingredient/nutrition results. Local OCR may remain only as explicitly non-authoritative draft assistance if separately approved. |
| `wye-flutter/lib/screens/barcode_scanner_screen.dart` | Preserve resolved `productId` with the product; for not-found flow, pass a barcode draft to add-product without inventing an ID. Keep product detail route barcode-based unless a separately reviewed route migration is needed. |
| `wye-flutter/lib/screens/manual_analysis_screen.dart` | Do not connect this legacy `/analyze` surface to capture/upload. The first Phase 8.5 runtime slice leaves it unchanged and adds a regression assertion that the capture controller never invokes it. Retirement or redesign of manual scoring is a separate scope. |
| `wye-flutter/lib/screens/product_detail_screen.dart` | Accept safe finalized `ProductImageRef`/extraction summaries from product state when available. Never persist or render presigned URLs after expiry. Keep score components unchanged and overall deferred; extraction failure is not a product score state. |
| `wye-flutter/lib/screens/history_screen.dart` | Display only safe capture/extraction status when retained. New history records may store `productId`, `imageId`, purpose, and terminal extraction status, but not local paths, bytes, base64, capabilities, or secrets. Legacy records without `productId` re-resolve by barcode. |
| `wye-flutter/lib/models/product_model.dart` | Extend `ScanHistory` backward-compatibly with nullable safe identifiers/status only if history is included in the authorized runtime slice. No numerical score fields are reintroduced. |
| `wye-flutter/lib/widgets/capture_upload_widgets.dart` (new) | Add minimal, neutral progress/error/retry widgets keyed by state. Show technical upload/extraction state separately from assessment components; no risk colors, rankings, claims, or final marketing copy. |
| `wye-flutter/lib/router/app_router.dart` | Carry barcode draft or safe product identity through typed route state if needed. Never put signed URLs, local paths, session tokens, or checksums in a route URI. |

The first implementation remains single-image-at-a-time even though the form
can hold three images. A later queue may reuse the same controller sequentially;
parallel uploads are deferred until cancellation, ordering, and supersession
semantics are tested.

### 4.5 Fixtures, tests, and documentation

| File | Planned change |
| --- | --- |
| `wye-flutter/test/fixtures/capture_upload/product_responses.json` (new) | Found, not-found, created, and 409-reconciliation envelopes with safe synthetic IDs; include legacy score placeholders to prove they are ignored. |
| `wye-flutter/test/fixtures/capture_upload/upload_responses.json` (new) | Initialize/finalize success and stable error envelopes. Use invalid example hosts and redacted query placeholders only. |
| `wye-flutter/test/fixtures/capture_upload/extraction_responses.json` (new) | Pending/running/succeeded/failed/superseded runs for ingredients and nutrition, without assessment or score fields. |
| `wye-flutter/test/fixtures/capture_upload/images/` (new) | Tiny synthetic JPEG/PNG/WebP headers and mismatch samples; no real label, user, or product images. |
| Test files in section 8 | Characterize parsing, state transitions, retry, logging redaction, UI state, and absence of scoring calls. |
| `WYE_PHASE_8_CAPTURE_UPLOAD_FLOW.md` | Update only after implementation if reviewed endpoint semantics change. Preserve contract/history rather than rewriting it silently. |
| `WYE_PHASE_8_FRONTEND_PLAN.md` | Record completed implementation/review checkpoints only when authorized and verified. |
| `WYE_PHASE_8_MOBILE_E2E_LOG.md` (future) | Phase 8.6 redacted run template/results; never commit secrets or signed capabilities. |

## 5. Separately authorized backend prerequisite plan

These backend paths are proposals for a later backend task, not changes
authorized by this document.

| Proposed file | Planned responsibility |
| --- | --- |
| `backend/app/routes/mobile_capture.py` (new) | Versioned mobile façade for product identity, upload initialize/finalize, and extraction lifecycle. Require scoped mobile-session authorization and return stable typed envelopes. Never accept or return `X-WYE-Image-Key`. |
| `backend/app/services/mobile_capture_sessions.py` (new) | Issue/validate short-lived development sessions through a reviewed local pairing/operator mechanism; scope them to capture operations/product identity; record expiry and audit metadata. |
| `backend/app/security.py` or a new dedicated dependency | Add mobile-session verification without weakening `require_image_api_key` on existing operational routes. Reject disabled/unconfigured mode by default. |
| `backend/app/services/image_uploads.py` | Reuse existing initialize/finalize service behavior. Change only if the façade needs a safe typed response; preserve SHA-256, MIME, size, idempotency, and supersession checks. |
| `backend/app/services/label_extractions.py` | Reuse current service; do not invoke scoring. If async polling is selected, define enqueue/status semantics in a separate reviewed backend change. |
| `backend/app/storage/config.py` and `backend/.env.example` | Add only non-secret configuration needed to distinguish an internal storage endpoint from the device-reachable presigning endpoint, if required. Defaults must not expose a public service. |
| `backend/app/main.py` | Register the façade only behind explicit development configuration until production authentication exists. |
| `backend/tests/test_mobile_capture_api.py` (new) | Prove disabled-by-default behavior, session scope/expiry, no shared-key exposure, stable errors, correlation, and absence of scoring imports/calls. |

Proposed URL names remain provisional until the backend contract review. The
Flutter gateway depends on a versioned OpenAPI/fixture freeze, not guessed route
strings.

## 6. DTO and view-model plan

The following are contract sketches, not Dart implementation.

### 6.1 Identity and local draft

```text
ProductIdentity
  productId: positive integer
  barcode: non-empty string

CaptureImagePurpose
  productFront | ingredients | nutrition | other
  wire values: product_front | ingredients | nutrition | other

CaptureImageSource
  camera | gallery

ImageMetadata
  mimeType: image/jpeg | image/png | image/webp
  byteSize: positive integer
  sha256: 64 lowercase hexadecimal characters

ImageCaptureDraft
  draftId: local opaque identifier
  productIdentity: ProductIdentity?       # absent until resolution succeeds
  localPath: local-only path
  purpose: CaptureImagePurpose
  source: CaptureImageSource
  selectedAt: timestamp
  metadata: ImageMetadata?                # absent until computed
```

`localPath` is never serialized to an API request, route URI, analytics event,
or normal application log. The draft contains no score.

### 6.2 Upload DTOs

```text
UploadInitRequest
  productId: positive integer
  purpose: CaptureImagePurpose
  mimeType: allowed MIME
  byteSize: positive integer
  sha256: validated digest

UploadInitResponse
  uploadId: UUID string
  uploadCapability: opaque memory-only wrapper around URI/method/headers
  expiresAt: timestamp

UploadFinalizeRequest
  productId: positive integer
  uploadId: UUID string

UploadFinalizeResponse
  uploadId: UUID string
  status: finalized
  storageObjectId: positive integer
  productImageId: positive integer

ProductImageRef
  productId: positive integer
  imageId: productImageId
  storageObjectId: positive integer
  purpose: CaptureImagePurpose
  mimeType: allowed MIME
  byteSize: positive integer
  sha256: validated digest
```

`UploadFinalizeRequest` maps values to the path even if the HTTP request has no
JSON body. `uploadCapability` has no general JSON serialization, no revealing
`toString`, and an explicit `dispose`/expiry operation.

### 6.3 Extraction DTOs

```text
ExtractionRunStatus
  pending | running | succeeded | failed | superseded

ExtractionRunRef
  productId: positive integer
  imageId: positive integer
  extractionRunId: positive integer
  labelDocumentId: positive integer?
  status: ExtractionRunStatus
  errorCode: safe stable string?

ExtractionResult
  run: ExtractionRunRef
  documentType: ingredients | nutrition
  rawText: sensitive review data?
  items: immutable typed extraction items
```

The transport adapter validates that `documentType` agrees with image purpose.
Extraction DTOs contain no score, score band, risk label, or overall value.

### 6.4 Error and state DTOs

```text
CaptureUploadFailure
  category: local | transport | http | application | storage | cancelled
  code: stable safe code
  retryability: retryable | terminal | requires_product_resolution
  lastStableState: UploadFlowPhase
  httpStatus: integer?
  correlationId: opaque safe identifier
  productId: integer?
  uploadId: redacted/opaque identifier?
  imageId: integer?
  extractionRunId: integer?
  safeMessageKey: non-final UI requirement key

UploadFlowState
  phase: UploadFlowPhase
  correlationId: opaque safe identifier
  identity: ProductIdentity?
  draft: ImageCaptureDraft?
  init: safe upload metadata without printable capability?
  image: ProductImageRef?
  extraction: ExtractionRunRef?
  failure: CaptureUploadFailure?
```

State validation permits only fields appropriate to its phase. Failure fields
never contain exception dumps, raw response bodies, image data, local paths,
session tokens, or signed URLs.

## 7. Upload/capture state machine plan

### 7.1 States and permitted transitions

| State | Entry event | Successful next state | Failure behavior |
| --- | --- | --- | --- |
| `idle` | Open/reset flow | `productResolving` or `imageSelected` | Local validation only |
| `productResolving` | Resolve barcode | `productResolved` or `productCreated` | Retryable transport failure or terminal invalid barcode |
| `productResolved` | Existing product identity parsed | `imageSelected` / `imageMetadataComputed` | Cannot upload without positive ID |
| `productCreated` | Create response parsed or 409 reconciled | `imageSelected` / `imageMetadataComputed` | Ambiguous create returns to resolution, never blind re-create |
| `imageSelected` | Camera/gallery returns post-crop local file | `imageMetadataComputing` | Cancel returns to last product state |
| `imageMetadataComputing` | Read/sniff/hash exact file | `imageMetadataComputed` | Terminal unsupported/corrupt; retryable local-file unavailable after reselection |
| `imageMetadataComputed` | Valid purpose/MIME/size/hash | `uploadInitializing` | No network occurs automatically |
| `uploadInitializing` | User confirms upload | `binaryUploading` | Retry same metadata; new init after expiry/terminal attempt |
| `binaryUploading` | PUT capability consumed | `finalizing` | Unknown outcome retains upload ID; expired capability returns to initialize |
| `finalizing` | PUT reported success or outcome reconciliation | `imageAssociated` | Retry same upload ID; mismatch is terminal for attempt |
| `imageAssociated` | Finalize returns both IDs | `extractionDeferred` or `extractionStarting` | Image stays associated even if extraction later fails |
| `extractionDeferred` | Purpose not extractable or user defers | terminal successful capture | No synthetic result |
| `extractionStarting` | Ingredients/nutrition extraction requested | `extractionPolling` or direct `extractionSucceeded` | Same idempotency key for ambiguous retry |
| `extractionPolling` | Reviewed async/recovery policy | `extractionSucceeded` or `extractionFailed` | Bounded retry/backoff; stop on terminal state |
| `extractionSucceeded` | Valid terminal run/items | terminal successful result | Keep result separate from assessment |
| `extractionFailed` | Server terminal failure | retryable or terminal according to code | Never roll back finalized image automatically |
| `retryableFailure` | Recoverable failure classified | Resume explicit recorded state | Retry budget/backoff enforced |
| `terminalFailure` | Validation/security/integrity failure | Reset or explicit new attempt | No automatic fallback |
| `cancelled` | User cancels | Last safe local state or reset | Dispose capability/session references |

The controller serializes transitions and ignores stale async completions by
checking both `correlationId` and expected prior phase.

### 7.2 Retry and idempotency rules

- Product create timeout: resolve by barcode before any new POST.
- Product create 409: resolve and verify barcode; never assume returned identity.
- Upload initialize failure before response: retry request only under façade
  contract; each successful initialize produces a distinct upload ID.
- Expired presigned capability: dispose it and initialize a new upload.
- PUT timeout/unknown outcome: retain upload ID and attempt finalize/reconcile
  before creating a new upload.
- Finalize timeout: retry the same product/upload IDs; backend finalize is
  idempotent after success.
- MIME/size/signature/checksum failure: terminal for the attempt; reselect or
  recompute exact bytes and obtain a new upload ID.
- Extraction start timeout: reuse the same `Idempotency-Key` and correlation ID.
- Extraction polling: exponential or bounded stepped backoff with a maximum
  attempt/time budget defined in configuration; no infinite background loop.
- Retry never changes image purpose, digest, product ID, or request body under
  an existing upload/idempotency identity.

## 8. Test implementation plan

### 8.1 Pure model and metadata tests

- `test/models/product_identity_test.dart`: parse backend `id`; reject missing,
  non-integer, zero, negative, or barcode-mismatched upload identity; preserve
  legacy Product parsing without fabricating an ID.
- `test/models/capture_upload_models_test.dart`: round-trip safe DTOs, validate
  purpose/status enums, and reject invalid cross-field state.
- `test/services/image_metadata_service_test.dart`: use tiny synthetic fixtures
  to verify magic-byte MIME, exact byte count, SHA-256, unsupported data, and
  mismatch behavior. Assert no base64 output.
- Keep existing score model/product tests and add regression assertions that
  backend `ingredient_score`, `nutrition_score`, and `final_score` remain
  ignored by the typed frontend contract.

### 8.2 Transport and gateway tests

- `test/services/api_client_product_identity_test.dart`: injected fake HTTP
  transport for found/not-found/create/409/timeout/malformed responses; prove
  `product_id` survives without accepting score placeholders.
- `test/services/http_capture_upload_gateway_test.dart`: assert façade paths,
  typed payloads, timeouts, status/error mapping, correlation header, and that
  `X-WYE-Image-Key` is never present.
- `test/services/presigned_binary_uploader_test.dart`: exact bytes and allowed
  headers, host allowlist, expiration, success status, redirect rejection, and
  redacted diagnostics.
- `test/services/fake_capture_upload_gateway_test.dart`: deterministic IDs and
  every injected failure; no formula, score, or external network dependency.

All HTTP tests use injected fake clients/transports. No test contacts FastAPI,
MinIO, S3, an extraction provider, or the internet.

### 8.3 Controller/state tests

- `test/providers/capture_upload_controller_test.dart`: every legal transition,
  rejected illegal transition, stale completion, cancellation, retry target,
  retry budget, capability disposal, and single-active-operation behavior.
- Characterize 409 reconciliation, expired URL, unknown PUT result, idempotent
  finalize retry, extraction direct success, bounded polling, failed extraction,
  and restart/reset.
- Assert upload/extraction errors never change `ProductScoreView`, never create
  a zero, and leave overall deferred/unavailable without a number.

### 8.4 Widget and integration-boundary tests

- `test/screens/add_product_capture_flow_test.dart`: purpose selection, neutral
  state labels, disabled transitions without product ID, retry/cancel, one image
  at a time, and no automatic network on image selection.
- `test/widgets/capture_upload_widgets_test.dart`: idle/progress/deferred/error
  rendering without rankings, risk colors, safety claims, or scores.
- Update product detail/history widget tests only when those surfaces begin to
  consume `ProductImageRef` or extraction state.
- Add a regression test proving the capture flow never calls
  `analyzeIngredients`, `analyzeProductImage`, `/analyze`, `/analyze-image`, or
  any scoring method.
- Existing `score_widgets_test.dart` remains authoritative for zero versus
  unavailable and for an overall state without a numerical value.

### 8.5 Logging and secret-negative tests

- `test/services/capture_flow_logger_test.dart`: feed session tokens, full
  signed URLs, authorization headers, local paths, raw bytes, base64, and raw
  response bodies; assert none reaches the sink.
- Assert only endpoint templates, safe host aliases, status, latency, state,
  correlation ID, non-secret numeric IDs, size, purpose, and truncated digest
  can be emitted.
- Snapshot tests must use explicit redacted placeholders, never realistic
  secrets or reusable URLs.

## 9. Phase 8.6 mobile logging hooks

### 9.1 Correlation model

Generate one opaque `flowCorrelationId` when a capture draft begins. Generate a
child `requestId` for each network attempt. Send only the reviewed correlation
header to the FastAPI façade. FastAPI propagates it to structured application
logs and associates it with product/upload/image/extraction IDs. Object-storage
PUT cannot be assumed to echo custom headers; correlate it locally by request
ID, upload ID alias, timestamp, byte size, and status.

### 9.2 Event schema

```text
CaptureFlowLogEvent
  timestamp
  flowCorrelationId
  requestId?
  phase
  transition: from -> to
  endpointTemplate?
  method?
  statusCode?
  latencyMs?
  retryNumber?
  productId?
  uploadIdAlias?
  imageId?
  storageObjectId?
  extractionRunId?
  imagePurpose?
  mimeType?
  byteSize?
  sha256Prefix?
  safeErrorCode?
```

The logger receives an endpoint template such as
`/products/{product_id}/images/uploads`, never a rendered URI with sensitive
values or query parameters. `uploadIdAlias` is a per-run redacted alias unless
the reviewed log policy permits the actual UUID.

### 9.3 Required hook points

- product lookup/create start, response, 409 reconciliation, and parse result;
- image selected/cancelled and metadata compute start/result;
- upload initialize start/result/expiry;
- PUT start/status/latency/unknown outcome, without URL;
- finalize start/result/retry and returned safe IDs;
- extraction start/idempotent retry/status refresh/terminal result;
- controller transition, cancellation, retry budget, and terminal failure;
- backend façade entry/exit with matching correlation/request IDs;
- Phase 8.6 environment record: device/OS, command, API base host, database name,
  storage host/status, and non-secret configuration described in Phase 8.5.1.

### 9.4 Prohibited logging

The implementation must block or redact:

- `X-WYE-Image-Key`, mobile session tokens, pairing material, auth headers;
- full presigned upload/read URLs, signatures, query strings, returned headers;
- storage/database/provider credentials;
- raw image bytes, base64, local file paths, raw OCR/label text;
- unsanitized request/response bodies and provider responses;
- exception strings or stack context that include any prohibited value.

A logging redaction failure disables diagnostic payload logging and blocks
Phase 8.6 until the affected capability/secret is expired or rotated and the
captured logs are removed from the test artifact.

## 10. Rollback and safety criteria

### 10.1 Disable and rollback controls

- The capture/upload feature flag defaults to off and can disable UI entry plus
  live gateway construction without changing product lookup or score UX.
- Rollback never re-enables base64 submission, `/analyze-image`, `/analyze`, or
  placeholder scoring as a fallback.
- New models/services/controller remain isolated so their implementation commit
  can be reverted without reverting Phase 8.2–8.4 score/evaluability work.
- Capability/session references are disposed on disable, reset, logout/session
  expiry, app lifecycle termination when observable, and terminal failure.

### 10.2 Stop criteria

| Condition | Required safe behavior |
| --- | --- |
| Upload fails on a real device | Disable live feature, preserve only policy-approved local draft metadata, retain no capability, and collect redacted logs |
| Presigned MinIO/S3 URL is unreachable | Stop before retry storm; mark configuration failure; verify device-resolvable host and signing topology |
| `product_id` is missing, invalid, or ambiguous | Do not initialize upload; re-resolve by barcode or require explicit new-product completion |
| PUT outcome is unknown | Retain upload ID and reconcile/finalize; do not blindly duplicate upload |
| Finalize IDs are absent/inconsistent | Treat as terminal contract failure; do not invent image/storage IDs |
| Extraction state regresses or conflicts | Stop polling, preserve finalized image reference, record safe IDs/code, and show neutral extraction unavailable state |
| Backend returns legacy score placeholders | Ignore them through existing typed score adapter; assert no score-state mutation; flag contract telemetry |
| Mobile logs may expose a secret/capability | Stop logging and live test; remove/quarantine logs, expire/rotate affected material, fix redaction, and repeat review |
| Authorization façade is disabled or unavailable | Keep fake/local flow only; never send shared image key from Flutter |

Server-side image deletion is not currently a public mobile contract. Rollback
must not attempt destructive cleanup. Orphan/expired staging cleanup remains a
separately operated backend responsibility.

## 11. Implementation acceptance checklist

Before any live-device authorization, the review must verify:

1. No Flutter source, asset, define, fixture, log, or binary contains
   `X-WYE-Image-Key` or another server credential.
2. The mobile façade/session is enabled only under reviewed configuration and
   rejects absent, expired, or out-of-scope sessions.
3. The physical phone can reach both `API_BASE_URL` and the exact host used in
   a presigned URL.
4. Product identity is positive, stable, and distinct from barcode.
5. Final file bytes, MIME, size, and SHA-256 match the init request and PUT.
6. Finalize returns and preserves distinct storage-object and product-image IDs.
7. Extraction is requested only for ingredients/nutrition and uses stable
   idempotency/recovery semantics.
8. Errors, cancellation, and offline conditions never create an assessment or
   score and never convert missing data to zero.
9. Existing score tests remain green; overall remains unavailable/deferred.
10. All HTTP tests are fake/local; real phone traffic occurs only in an
    explicitly authorized Phase 8.6 session.
11. The rollback flag and redaction-failure stop path are exercised.
12. No generated, cache, build, secret, real image, or unredacted E2E artifact
    is staged.

## 12. Documentation/checkpoint updates

When each later slice is completed, update documentation narrowly:

- record the selected and implemented mobile façade/session contract;
- record actual DTO and route names if they differ from this proposal;
- update the Phase 8.5.1 contract through an explicit reviewed diff;
- create the Phase 8.6 log template only after redaction tests pass;
- keep runtime and release authority fields explicit;
- record that capture/extraction does not activate scoring runtime.

## 13. Checkpoint

    checkpoint: Phase 8.5.2 capture/upload implementation plan
    prior_verdict: READY_FOR_PHASE_8_5_2_CAPTURE_UPLOAD_IMPLEMENTATION_PLAN
    implementation_completed: DOCUMENTATION ONLY
    selected_control_plane: FASTAPI MOBILE FACADE
    selected_data_plane: TEMPORARY PRESIGNED BINARY PUT
    shared_mobile_secret: PROHIBITED
    current_live_integration_blocker: MOBILE-SAFE FACADE/SESSION NOT IMPLEMENTED
    endpoint_calls_performed: NONE
    scoring_runtime_connection: NONE
    overall_numerical_candidate: NONE / DEFERRED
    runtime_authority: NONE
    release_authority: NONE
    next_recommended_subphase: Phase 8.5.2.1 review and commit implementation plan

Expected planning verdict:

```text
READY_FOR_PHASE_8_5_2_1_REVIEW_AND_COMMIT
```
