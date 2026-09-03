# WYE — Phase 8.5 Capture / Upload Contract and Flow

## 1. Document status and authority

    phase: Phase 8.5.1 — capture/upload contract and flow specification
    artifact_scope: documentation and contract specification only
    frontend_runtime_authority: NONE
    backend_runtime_authority: NONE
    scoring_runtime_authority: NONE
    release_authority: NONE
    overall_numerical_candidate: NONE / DEFERRED

This document specifies a conservative MVP sequence for product identity,
mobile image capture, direct object-storage upload, upload finalization,
product-image association, and optional label extraction. It does not authorize
implementation, live endpoint use, scoring, deployment, or release.

The Phase 7/8 boundary remains controlling. WYE provides broad, approximate,
informational food guidance only. It is not a doctor and makes no medical,
clinical, therapeutic, personalized dietary, dose, frequency, portion, safety,
healthiness, regulatory-compliance, certification, approval, or
individual-suitability claim. Image or label extraction is data capture, not a
product assessment. No overall numerical score is available or approved.

## 2. Inspected baseline

### 2.1 Current Flutter flow

- `BarcodeScannerScreen` uses `mobile_scanner`, accepts manual barcode input,
  calls `BarcodeScannerProvider.scanBarcode`, and navigates to
  `/product/:barcode` after `GET /product/{barcode}` succeeds.
- `AddProductScreen` supports camera/gallery selection and optional cropping for
  product-front, ingredients, and nutrition images. It also runs on-device ML
  Kit text recognition.
- The current photo path encodes bytes as `data:image/jpeg;base64,...`, calls
  legacy `POST /analyze-image`, and later includes up to three base64 data URLs
  in `POST /products`. This is not the canonical Phase 8.5 upload path.
- Manual ingredient analysis calls legacy `POST /analyze`. It is not part of
  this capture/upload contract and must not be invoked by its implementation.
- `ApiConfig` defaults to `10.0.2.2:8000` on Android and `127.0.0.1:8000` on
  other non-web targets unless `API_BASE_URL` is supplied with `--dart-define`.
  The Android default targets an emulator, not a physical phone.
- `Product` and `ScanHistory` retain `barcode` but have no `product_id`. Product
  detail and history navigation are barcode-based. History may retain a base64
  image data URL.
- `POST /products` and `GET /product/{barcode}` return a backend product row
  containing `id`, but the current Flutter parsing/mapping discards it.

### 2.2 Current backend flow

- `POST /products` creates a product and returns
  `{message, product}`. The raw `product` row includes the stable database `id`.
  An existing barcode currently produces `409`, so the caller must re-resolve
  it rather than assuming creation is idempotent.
- `GET /product/{barcode}` returns `{product, score, ingredients}` when found.
  A missing barcode currently returns HTTP 200 with
  `{error: "not_found", barcode}` rather than a 404 response.
- `POST /products/{product_id}/images/uploads` initializes an upload from
  `image_type`, `mime_type`, `byte_size`, and lowercase hexadecimal `sha256`.
  It returns `upload_id`, a temporary `upload_url`, method `PUT`, required
  storage headers, and `expires_at`.
- The client sends the raw binary file to `upload_url`. This object-storage
  request is distinct from the WYE API request and uses exactly the returned
  method and headers.
- `POST /products/{product_id}/images/uploads/{upload_id}/finalize` verifies
  object existence, size, MIME, file signature, and SHA-256. It then creates or
  reuses a content-addressed `storage_objects` row, associates a
  `product_images` row, supersedes the prior current image of the same type,
  and returns `storage_object_id` plus `product_image_id`.
- Finalization is idempotent for an already finalized `upload_id`. Identical
  content can reuse the content-addressed storage object and product image.
- `GET /products/{product_id}/images` lists product-image metadata. The access
  endpoint `GET /products/{product_id}/images/{image_id}/access` returns a
  temporary read URL.
- Image types are `product_front`, `ingredients`, `nutrition`, and `other`.
  Accepted MIME types are JPEG, PNG, and WebP. The configured default maximum
  is 15 MiB, subject to the server environment.
- Label extraction is supported only for `ingredients` and `nutrition` images.
  `POST /products/{product_id}/images/{image_id}/extractions` requires an
  `Idempotency-Key`; list and single-run GET endpoints expose persisted runs.
- Extraction currently executes synchronously inside the POST request. The
  persisted states are `pending`, `running`, `succeeded`, `failed`, and
  `superseded`, but the current POST normally returns only after a terminal
  result or error. The GET endpoints support recovery and future asynchronous
  execution; they do not yet define a mobile polling policy.
- Product-image and extraction routes are protected by the temporary shared
  `X-WYE-Image-Key`. No product ownership or authenticated consumer-session
  model exists yet.

## 3. Canonical identifiers

| Identifier | Meaning | Source and rule |
| --- | --- | --- |
| `barcode` | External packaged-product lookup key | Scanned or manually entered string; never substitute it for a database ID |
| `product_id` | Stable backend product primary key | Read from the backend `product.id`; required in all image/extraction paths |
| `upload_id` | One staged upload attempt | UUID returned by upload initialization; used for finalize/retry only |
| `storage_object_id` | Internal content-addressed object record | Returned after finalize; not a product or image identity |
| `image_id` / `product_image_id` | Product-image association and version | Returned by finalize; use as `{image_id}` for access and extraction routes |
| `label_document_id` | Image-derived ingredients/nutrition document | Created server-side for an extractable image and exposed through the extraction run record |
| `extraction_run_id` | One persisted extraction attempt | Read from `extraction.id`; use for run status/result retrieval |
| extraction item `id` | One detected ingredient, allergen, list, or nutrition item | Child of exactly one extraction run; not a score or assessment result |

The frontend must carry the identifiers as distinct typed fields. It must not
derive `product_id`, `image_id`, or `extraction_run_id` from the barcode,
timestamps, list positions, filenames, or each other.

## 4. Canonical MVP capture/upload sequence

### 4.1 Product resolution

1. Accept a barcode from the scanner or manual barcode field. Normalize only
   according to an explicitly agreed product contract; preserve the submitted
   value for diagnostics.
2. Resolve the barcode with `GET /product/{barcode}`.
3. If found, parse and retain both `product.id` as `product_id` and the barcode.
4. If not found, keep the image locally as a draft while collecting the fields
   currently required by `POST /products`. Create the product without base64
   image fields and read `product.id` from the response.
5. If creation returns `409`, repeat barcode lookup and use the returned
   product only if its barcode matches the draft. Do not invent an ID.
6. Do not start upload initialization until a stable `product_id` exists.

The present backend does not support a barcode-free product identity. A future
manual flow without a barcode requires a separate identity contract and is
outside this specification.

### 4.2 Image preparation and classification

1. Capture or select one image and retain its local URI only for the lifetime
   and retry policy of the draft.
2. Assign one explicit purpose:
   `product_front`, `ingredients`, `nutrition`, or `other`. Do not infer
   `nutrition` from the current `isProductPhoto` boolean.
3. Read the final post-crop binary bytes and determine their real MIME type.
   Do not label every picked file as JPEG.
4. Calculate the exact byte length and lowercase SHA-256 of those same bytes.
5. Reject unsupported formats or files above the server-advertised/configured
   size before initialization when possible. Client validation is advisory;
   server verification remains authoritative.

### 4.3 Upload and finalization

1. Through an approved mobile-safe authorization boundary, request:

   ```http
   POST /products/{product_id}/images/uploads
   Content-Type: application/json

   {
     "image_type": "ingredients",
     "mime_type": "image/jpeg",
     "byte_size": 123456,
     "sha256": "<64 lowercase hex characters>"
   }
   ```

2. Retain `upload_id` and `expires_at` in transient flow state. Do not persist
   or log the presigned URL or its query string.
3. Send the unchanged raw bytes to `upload_url` using the returned method and
   every returned header, including the exact `Content-Type`. Do not send JSON,
   base64, cookies, or `X-WYE-Image-Key` to object storage unless a future
   contract explicitly returns such a header.
4. Treat only the object-storage success status as bytes uploaded. It does not
   mean the image is associated with the product.
5. Finalize with:

   ```http
   POST /products/{product_id}/images/uploads/{upload_id}/finalize
   ```

6. Treat the upload as complete only when the response has
   `status = finalized`, `storage_object_id`, and `product_image_id`.
   Store `product_image_id` as `image_id`; keep `storage_object_id` distinct.
7. A successful finalize is the product-image association step. No separate
   association call exists in the current backend.

### 4.4 Optional extraction and result presentation

1. Do not start extraction for `product_front` or `other` images.
2. For an `ingredients` or `nutrition` `image_id`, generate a stable
   per-attempt `Idempotency-Key` and call:

   ```http
   POST /products/{product_id}/images/{image_id}/extractions
   Idempotency-Key: <stable retry key>

   {}
   ```

3. On success, retain `extraction.id` as `extraction_run_id`, its
   `label_document_id`, `run_status`, and returned `items` separately.
4. On a timeout or recoverable transport failure, retry the same request with
   the same idempotency key. If a `run_id` is returned in an error, retrieve it
   directly. Otherwise list runs for the image and reconcile by the stored
   idempotency key only after the response contract exposes enough information.
5. The implementation plan must choose between the current synchronous POST
   behavior and a future asynchronous `202 + polling` contract. If polling is
   authorized, use bounded backoff and stop at `succeeded`, `failed`, or
   `superseded`; do not poll indefinitely.
6. Present extracted label data as a reviewable capture result. Keep raw text,
   document type, detected items, source image, and extraction state separate.
   Do not call a scoring endpoint and do not derive a score.
7. Until an independently authorized assessment exists, score components stay
   `not_computable` or `non_applicable` as supplied by their typed contract;
   overall remains unavailable/deferred without a number.

### 4.5 Frontend flow state

The implementation should make state explicit rather than inferring it from a
nullable URL or score:

```text
draft
  -> product_resolved(product_id, barcode)
  -> image_prepared(local_uri, image_type, mime_type, byte_size, sha256)
  -> upload_initialized(upload_id, expires_at)
  -> bytes_uploaded(upload_id)
  -> upload_finalized(storage_object_id, image_id)
  -> extraction_not_requested
     | extraction_pending(extraction_run_id)
     | extraction_running(extraction_run_id)
     | extraction_succeeded(extraction_run_id, label_document_id, items)
     | extraction_failed(extraction_run_id?, error_code)
```

Technical upload/extraction errors must not be represented as zero scores,
low scores, or unfavorable product judgments.

## 5. Current endpoint contract summary

| Step | Current endpoint | Current response / relevant behavior |
| --- | --- | --- |
| Resolve product | `GET /product/{barcode}` | Product row includes `id`; missing product is a 200 error envelope |
| Create product | `POST /products` | Returns `{message, product}`; existing barcode is 409; legacy base64 fields exist but are excluded from this flow |
| Initialize upload | `POST /products/{product_id}/images/uploads` | 201 with `upload_id`, `upload_url`, `method`, `headers`, `expires_at` |
| Upload bytes | Returned object-storage URL | Raw binary PUT with exact returned headers |
| Finalize | `POST /products/{product_id}/images/uploads/{upload_id}/finalize` | `status`, `storage_object_id`, `product_image_id`; idempotent after success |
| List images | `GET /products/{product_id}/images` | Image metadata, current/superseded state, checksum, and storage provider |
| Temporary image access | `GET /products/{product_id}/images/{image_id}/access` | Presigned read URL and expiry |
| Create extraction | `POST /products/{product_id}/images/{image_id}/extractions` | 201 after current synchronous execution; requires `Idempotency-Key` |
| List extraction runs | `GET /products/{product_id}/images/{image_id}/extractions` | Persisted extraction rows |
| Get extraction result | `GET /products/{product_id}/images/{image_id}/extractions/{run_id}` | `{extraction, items}` |

Upload and extraction application errors use an HTTP status plus a structured
`detail` containing a stable `code` and `message`; extraction errors may also
contain `run_id`. The implementation must map transport status, application
code, and local state separately.

## 6. Security and mobile constraints

### 6.1 Secret boundary

`X-WYE-Image-Key` is a temporary shared server credential. A Flutter binary,
asset, source file, `--dart-define`, local preferences, device log, or CI build
cannot keep it secret. The app must not embed, request, persist, or log it.

Likewise, object-storage access key, secret key, extraction-provider key, and
database credentials remain server-side only. The presigned URL is a temporary
bearer capability: the app may use it for the one upload, but must redact the
complete URL and query parameters from logs and must not retain it after the
flow completes or expires.

Safe MVP options requiring a later explicit decision are:

1. **Preferred development boundary:** a local trusted proxy/broker holds
   `WYE_IMAGE_API_KEY` server-side, restricts access to the development session,
   and forwards only the narrow initialize/finalize/extraction operations.
2. **Server-side dev session:** a development-only bootstrap creates a short
   lived, scoped session token; environment secrets remain in the backend.
3. **Temporary local harness:** verify storage and extraction from a local
   backend/CLI without putting the shared key on the phone; mobile stops after
   local capture until a safe boundary exists.
4. **Future product solution:** authenticated users/sessions, product ownership
   or submission grants, per-operation authorization, expiry, and audit.

No direct mobile integration with the protected routes is authorized until one
option is selected and threat-reviewed.

### 6.2 Physical-device connectivity

- A real phone needs an explicit reachable `API_BASE_URL`; Android emulator
  address `10.0.2.2` is not valid for a physical device.
- A development run may use a LAN address or an approved `adb reverse` setup.
  The backend and object-storage hosts embedded in presigned URLs must both be
  reachable from the phone. A URL signed for `localhost:9000` commonly fails on
  a phone unless the exact host/port path is deliberately forwarded.
- The Android manifest currently permits cleartext traffic. That is a local
  development condition, not release approval. iOS has no inspected transport
  exception; prefer HTTPS or make any development-only exception an explicit
  later decision.
- Hash and upload the post-crop bytes actually sent. Large files should be
  hashed/streamed without unnecessary base64 copies where platform APIs allow.
- Camera/gallery cancellation, permission denial, process interruption, and
  loss of the temporary local file require explicit non-destructive states.

## 7. Retry, offline, and failure semantics

- Before product resolution: keep a local draft; do not fabricate server IDs.
- Product lookup failure: distinguish not found from offline, timeout, parsing,
  and server failure. Do not create a duplicate after an ambiguous response.
- Upload URL expired before/during PUT: initialize a new upload attempt with the
  same prepared image metadata; do not reuse the expired URL.
- PUT outcome unknown: check/finalize the same `upload_id` first. Reinitialize
  only after a stable terminal response or expiry policy says it is safe.
- Finalize timeout: retry the same `upload_id`; current finalization is
  idempotent after success.
- Checksum/MIME/size/signature mismatch: terminal for that attempt; re-read or
  re-encode the image and create a new attempt rather than changing metadata to
  bypass validation.
- Extraction timeout/transport ambiguity: reuse the same idempotency key and
  reconcile the persisted run. A 409 idempotency conflict is not retryable with
  changed inputs under the same key.
- Offline mode may retain a draft, local URI, type, size, and digest according
  to an explicit privacy/lifetime policy. It must not retain secrets or
  presigned URLs and must not show a synthetic extraction or score result.
- Cancellation stops future steps but does not delete a finalized server image.
  Server-side delete/retention is not defined by the current public routes.

## 8. Phase 8.6 — Mobile E2E test and log capture

Phase 8.6 must use a real phone only after the Phase 8.5 implementation plan,
safe authorization boundary, and local environment are approved. Each run must
create a redacted session record with the following fields.

### 8.1 Environment record

- timestamp, tester, commit SHA, clean/dirty state, and test scenario ID;
- device manufacturer/model and physical device identifier redacted as needed;
- Android/iOS version, Flutter/Dart version, and debug/profile mode;
- exact `flutter run` command and device selector;
- effective `API_BASE_URL` and connectivity method (LAN, emulator, adb reverse,
  or other), without credentials;
- exact backend start command, for example the locally selected
  `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` invocation;
- backend configuration names and non-secret values relevant to upload:
  provider, endpoint host, bucket alias, TTLs, size limit, path-style setting,
  extraction provider/model/timeout, and whether required secrets are present;
- database host/port and database name (`PGDATABASE`, default `wye`) without
  username/password;
- PostgreSQL migration level;
- MinIO/object-storage process, bucket, health/reachability, and endpoint as
  seen by both backend and phone.

### 8.2 Test input and identifier record

- barcode and whether scanned or manually entered;
- whether the product was retrieved, created, or resolved after 409;
- `product_id`, `upload_id`, `storage_object_id`, `image_id`,
  `label_document_id`, and `extraction_run_id` when available;
- photo purpose (`product_front`, `ingredients`, `nutrition`, or `other`),
  source (camera/gallery), real MIME type, byte size, and a truncated checksum;
- idempotency key represented by a redacted correlation alias rather than any
  reusable credential;
- expected behavior and actual behavior for each state transition.

### 8.3 Logs and request timeline

- timestamped frontend application logs and the complete `flutter run` console;
- `adb logcat` filtered to the app/process on Android, or Xcode/device console
  logs on iOS;
- FastAPI/uvicorn logs and any local authorization broker logs;
- object-storage/MinIO status and relevant request/error logs;
- ordered request summaries: endpoint template, method, status code, latency,
  request field names, declared byte size, response field names, stable error
  code, and retry number;
- object-storage PUT status and latency without the signed URL;
- exception type and full stack trace from frontend/backend when present;
- screenshots or screen recordings only after checking that they contain no
  secrets or unnecessary label/user data.

Never log `X-WYE-Image-Key`, storage credentials, provider keys, database
passwords, authorization headers, full presigned URLs/query strings, raw image
bytes, base64 images, or unsanitized provider responses. Redact sensitive label
content and device identifiers when they are not required for diagnosis.

### 8.4 Minimum device scenarios

1. Retrieve an existing barcode and upload each supported image purpose.
2. Create a new product, recover from the current 409 race path, and retain the
   returned `product_id`.
3. Capture from camera and select from gallery; include crop and cancellation.
4. Exercise a successful binary PUT and finalize, then retry finalize.
5. Exercise expired upload, offline before initialize, interrupted/unknown PUT,
   and network loss before finalize.
6. Extract ingredients and nutrition separately; verify product-front
   extraction is rejected without changing score state.
7. Exercise extraction timeout/idempotent retry and persisted-result recovery.
8. Verify product detail/history show capture/extraction state without invoking
   scoring runtime or displaying a numerical overall score.

## 9. Contract gaps and implementation blockers

| Gap / blocker | Current evidence | Required decision before implementation |
| --- | --- | --- |
| Flutter loses `product_id` | Backend product rows contain `id`; `Product` discards it | Add a typed identity/transport model or capture-session DTO without conflating barcode and ID |
| Product-create response | Raw response is sufficient for `product.id`, but the current client returns only `Product` | Preserve response metadata and specify behavior for 200, 409, ambiguous timeout, and lookup reconciliation |
| Unknown barcode capture order | Backend requires a product before upload and create currently requires barcode, brand, name, ingredients, and nutrition | Decide the minimum draft/create contract or defer upload until all required fields are collected |
| Barcode-free manual product | No stable backend identity contract exists | Keep out of MVP or define a separate server-generated identity flow |
| Mobile authorization | Protected routes require a shared `X-WYE-Image-Key` | Select and implement a server-side broker/session boundary; never embed the key |
| Presigned URL reachability | Default MinIO endpoint is `localhost:9000`; physical phones need a reachable signed host | Define LAN/HTTPS/forwarding topology and test the exact signed URL from device |
| Image-purpose model | UI uses separate fields plus a boolean that conflates nutrition with product photos | Introduce an explicit image-purpose enum mapped to backend values |
| MIME/checksum preparation | Current code always constructs a JPEG data URL and makes base64 copies | Specify real MIME detection, final-byte hashing, size validation, and streaming policy |
| Legacy base64 fields/endpoints | `/analyze-image` and image URL fields remain in frontend/backend | Canonical adapter must omit them; retirement is a separate authorized change |
| Finalize metadata | Finalize returns IDs but not the full image row, verified metadata, or read URL | Decide whether IDs are sufficient or extend/version response; use list/access only if authorized |
| Extraction execution model | POST is synchronous, while persisted states and GET routes resemble an async lifecycle | Choose synchronous timeout/recovery semantics or define `202` and bounded polling |
| Extraction reconciliation | List response does not provide a documented client correlation contract beyond stored row fields | Define exposed idempotency/fingerprint fields and deterministic recovery behavior |
| Error envelope consistency | Product-not-found is HTTP 200; other routes use HTTP errors with differing detail shapes | Define typed/versioned status and error DTOs before UI integration |
| Offline persistence/privacy | No capture-session store or retention policy exists | Define draft lifetime, local-file cleanup, retry ownership, and redaction |
| History/navigation identity | History and route use barcode and optional base64 only | Decide how `product_id`, `image_id`, and extraction state are retained without persisting signed URLs |
| Legacy product scores | `POST /products` still inserts placeholder numerical score rows | Frontend must ignore them; backend removal requires separate authorization |
| Extraction provider/config | Current configured provider can require external network access | Define an offline/fake dev path and explicit opt-in for any later real-provider test |

These blockers do not authorize backend or Flutter changes. Phase 8.5.2 must
turn the selected decisions into a file-level implementation plan, mocks,
contract tests, migration/backward-compatibility boundaries, and rollback
criteria before runtime work begins.

## 10. Checkpoint

    checkpoint: Phase 8.5.1 capture/upload contract and flow specification
    prior_verdict: READY_FOR_PHASE_8_5_CAPTURE_UPLOAD_FLOW
    implementation_completed: DOCUMENTATION ONLY
    endpoint_calls_performed: NONE
    runtime_authority: NONE
    release_authority: NONE
    mobile_secret_embedding: PROHIBITED
    scoring_runtime_connection: NONE
    overall_numerical_candidate: NONE / DEFERRED
    next_recommended_subphase: Phase 8.5.2 capture/upload implementation plan

Expected planning verdict:

```text
READY_FOR_PHASE_8_5_2_CAPTURE_UPLOAD_IMPLEMENTATION_PLAN
```
