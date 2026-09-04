# WYE Phase 8.6 Mobile E2E Test Runbook

Status: LOCAL ENVIRONMENT READY - REAL-DEVICE EXECUTION REQUIRES EXPLICIT AUTHORIZATION

Preparation date: 2026-09-03

## 1. Scope and non-authorizations

This runbook prepares one local-development test of the dev-only Flutter
capture, binary upload, finalize, and label-extraction flow on a real phone. It
does not authorize executing that test.

The future run is limited to a local operator-controlled Windows machine, one
physical phone on the same trusted LAN, the default-off FastAPI mobile facade,
and a temporary scoped mobile session. It does not authorize:

- production deployment or public release;
- scoring runtime, scoring endpoints, formulas, or a numerical overall score;
- `/analyze`, `/analyze-image`, or another legacy analysis fallback;
- medical, safety, certification, healthiness, or personal-suitability claims;
- placing `X-WYE-Image-Key`, storage/database/provider credentials, or another
  server secret in Flutter;
- retaining a mobile token, upload capability, image, or raw provider response
  in the test record.

Extraction is informational label-data extraction only. The feature remains
disabled by default on both backend and Flutter.

## 2. Sanitized notation

All commands below are templates for a later explicitly authorized run. Values
inside angle brackets are placeholders and must never be copied into the
committed report as real credentials or capabilities.

| Placeholder | Meaning | May be recorded? |
| --- | --- | --- |
| `<LAN_IP>` | PC address reachable only on the trusted LAN | Only as `<LAN_HOST>` in the shared report |
| `<DEVICE_ID>` | Flutter device selector | Yes, if non-sensitive |
| `<BACKEND_VENV>` | Existing backend virtualenv directory | Yes |
| `<SAFE_LOG_DIR>` | Local restricted directory for sanitized logs | Path itself should not be shared |
| `<PRODUCT_ID>` | Existing positive database product ID | Yes |
| `<BARCODE>` | Product barcode | Yes, if the test product is non-sensitive |
| `<STORAGE_HOST>` | Host and port only, without path/query | Yes in redacted form |

Never create placeholders for a real token, secret, signature, full presigned
URL, image path, image bytes, base64, or provider payload in the report.

## 3. Grounded implementation contract

### 3.1 Control and data planes

| Operation | Contract | Authorization |
| --- | --- | --- |
| Health | `GET /health` | None; reachability only |
| Create mobile session | `POST /mobile/dev/v1/capture/sessions` | Operator-only server secret; never Flutter |
| Initialize upload | `POST /mobile/dev/v1/capture/products/{product_id}/images/uploads` | Bearer session with `upload` scope |
| Upload exact bytes | Temporary presigned binary `PUT` | Presigned capability headers only; no Bearer or server secret |
| Finalize upload | `POST /mobile/dev/v1/capture/products/{product_id}/images/uploads/{upload_id}/finalize` | Bearer session with `upload` scope |
| Start extraction | `POST /mobile/dev/v1/capture/products/{product_id}/images/{image_id}/extractions` | Bearer session with `extraction` scope |
| List extraction runs | `GET` on the extraction collection above | Bearer session with `extraction` scope |
| Read extraction run | `GET` on the collection plus `/{run_id}` | Bearer session with `extraction` scope |

FastAPI is the control plane. The only direct Flutter-to-storage operation is
the temporary binary PUT. Flutter must never send `X-WYE-Image-Key`.

### 3.2 Feature and lifetime constraints

- Backend flag: `WYE_MOBILE_UPLOAD_FACADE_ENABLED`; default `false`.
- Backend session TTL: `WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS`; allowed
  range 30-900 seconds, default 300.
- Flutter define: `WYE_MOBILE_UPLOAD_ENABLED`; default `false`.
- Flutter API define: `API_BASE_URL`; for a phone it must use a LAN-reachable
  host, not `localhost`, `127.0.0.1`, or the Android-emulator-only host.
- Sessions are process-local. Backend restart invalidates them. Use one Uvicorn
  worker and do not use `--reload` for the test.
- The storage endpoint used to sign the PUT must resolve and be reachable from
  the phone. A localhost MinIO endpoint is not sufficient.

### 3.3 Logging reality

The backend emits sanitized `mobile_facade` events with request/session IDs,
product/image/storage/run IDs, status, and latency. Phase 8.6.2 locally wires a
sanitized Flutter event sink when `WYE_MOBILE_UPLOAD_ENABLED=true`. It retains
only the latest 200 allowlisted events in process memory and exposes explicit
copy and clear actions in the dev upload panel. It performs no file, database,
preferences, backend, or analytics persistence. When the feature flag is
false, recording remains a no-op.

The safe frontend fields are: UTC timestamp, step, status class, safe
request/correlation ID, numeric product/image/storage/extraction-run IDs, image
purpose, item count, HTTP status code, retry count, latency, and sanitized
error code/category. Token values, authorization headers, `X-WYE-Image-Key`,
full or signed URLs, query signatures, upload/image bytes, base64, local image
paths, request/response bodies, and raw OCR/provider text are outside the event
model and must remain absent from copied output.

## 4. Prerequisites checklist

Mark every item PASS, FAIL, or NOT CHECKED in the separate log template. Any
FAIL blocks the run.

### 4.1 Windows and repository

- [ ] Windows machine is on a trusted/private LAN.
- [ ] Repository, branch, and application/backend commits are recorded.
- [ ] Working tree is clean before starting the future run.
- [ ] The Python 3.11 backend virtualenv at `backend/venv/e2e311` is activated;
  no dependency install is performed as part of the E2E run.
- [ ] A restricted local log directory exists outside tracked source paths.
- [ ] Shell transcription and HTTP debugging that could echo headers/bodies are
  disabled.

### 4.2 Backend dependencies

- [ ] PostgreSQL is running and reachable using `PGHOST`, `PGPORT`, `PGUSER`,
  `PGPASSWORD`, and `PGDATABASE`; values are not printed.
- [ ] The non-sensitive database name is recorded, normally `wye` unless the
  operator selected a dedicated local database.
- [ ] Moto/local S3 is running and reachable from the backend.
- [ ] `WYE_STORAGE_PROVIDER`, `WYE_STORAGE_ENDPOINT`,
  `WYE_STORAGE_BUCKET`, `WYE_STORAGE_REGION`,
  `WYE_STORAGE_FORCE_PATH_STYLE`, upload TTL, and size limits are present.
- [ ] Storage access/secret keys are present server-side but never printed.
- [ ] Extraction provider configuration is present server-side but provider
  credentials, prompts, and raw responses are never printed or copied.

Phase 8.6.3a.2 establishes the following local-only baseline:

- Moto 5.1.11 is available from `backend/venv/e2e311` without Docker or an
  external download;
- use `WYE_STORAGE_PROVIDER=s3` and
  `WYE_STORAGE_FORCE_PATH_STYLE=true` for Moto;
- bind Moto to `0.0.0.0`, but set `WYE_STORAGE_ENDPOINT` to
  `http://<LAN_IP>:5000` so generated presigned URLs contain a host reachable
  by the phone rather than `localhost`;
- set `WYE_RUNTIME_ENVIRONMENT=e2e` and
  `WYE_EXTRACTION_PROVIDER=fake` together for the explicitly authorized local
  fake runtime;
- the fake provider is rejected when the runtime environment is absent,
  `staging`, or `production`; the default environment is `production`;
- do not configure or call an external extraction provider for this E2E run.

### 4.3 LAN and phone

- [ ] Phone and PC use the same trusted network, without guest/client isolation.
- [ ] FastAPI binds to `0.0.0.0` and TCP port 8000 is allowed only on the
  private network for the test window.
- [ ] `GET /health` succeeds from the PC through loopback and the LAN address.
- [ ] The phone can open the LAN health URL before Flutter is launched.
- [ ] The host embedded by the storage signer is reachable from the phone.
- [ ] Any temporary firewall allowance has a recorded rollback step.

### 4.4 Flutter/device tooling

- [ ] Android USB debugging or Wi-Fi debugging is enabled only as needed.
- [ ] `flutter devices` lists the intended phone.
- [ ] The phone authorizes the current development machine.
- [ ] Flutter and Dart versions are recorded without verbose diagnostic dumps.
- [ ] No server secret is present in a Dart define, source file, asset, shell
  argument, application storage, or device log.

## 5. Backend startup plan

Do not execute the real-device flow without separate authorization. In that
later authorized run, use dedicated PowerShell processes whose
transcript/history will not capture secret values.

Start Moto in its own process before FastAPI:

```powershell
Set-Location C:\Projects\wye\backend
& .\venv\e2e311\Scripts\moto_server.exe -H 0.0.0.0 -p 5000
```

In the trusted backend process, configure these non-secret choices:

```powershell
$env:WYE_RUNTIME_ENVIRONMENT = 'e2e'
$env:WYE_EXTRACTION_PROVIDER = 'fake'
$env:WYE_STORAGE_PROVIDER = 's3'
$env:WYE_STORAGE_ENDPOINT = 'http://<LAN_IP>:5000'
$env:WYE_STORAGE_BUCKET = 'wye-local-e2e'
$env:WYE_STORAGE_REGION = 'us-east-1'
$env:WYE_STORAGE_FORCE_PATH_STYLE = 'true'
```

Set non-production Moto access/secret values only in the trusted process and
never echo or record them. Create the bucket without printing configuration:

```powershell
& .\venv\e2e311\Scripts\python.exe -c "from app.storage import StorageSettings,get_storage_adapter; s=StorageSettings.from_env(); get_storage_adapter(s).client.create_bucket(Bucket=s.bucket); print('bucket_ready')"
```

Then start FastAPI:

```powershell
Set-Location C:\Projects\wye\backend
& .\venv\e2e311\Scripts\Activate.ps1

$env:WYE_MOBILE_UPLOAD_FACADE_ENABLED = 'true'
$env:WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS = '300'

# Confirm required environment-variable names are configured in the trusted
# process. Do not echo, list, serialize, or screenshot their values.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info `
  2>&1 | Tee-Object -FilePath '<SAFE_LOG_DIR>\backend-mobile-e2e.log'
```

Rules:

- run a single process/worker and omit `--reload`;
- do not enable request/response body or header dumps;
- do not use `Get-ChildItem Env:`, `set`, or another command that prints the
  entire environment;
- keep the backend log local until the redaction inspection passes;
- never record the value of `WYE_IMAGE_API_KEY`, storage/database credentials,
  or the extraction-provider key.

In separate terminals, later reachability checks may use:

```powershell
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/health'
Invoke-RestMethod -Method Get -Uri 'http://<LAN_IP>:8000/health'
```

The phone browser may open the second health URL. Record only success/failure
and the redacted host `<LAN_HOST>:8000`, not screenshots containing unrelated
device information.

For local MinIO, ensure the configured `WYE_STORAGE_ENDPOINT` uses a host the
phone can reach and that MinIO is bound accordingly. Record only
`<STORAGE_HOST>:<PORT>`. Do not copy a presigned path or query string into any
log, command summary, screenshot, or report.

The same rule applies to Moto: the endpoint used by `S3StorageAdapter` is also
the host embedded in generated presigned URLs. A successful PC loopback smoke
does not prove phone reachability; validate `<LAN_IP>:5000` from the phone
before any upload attempt.

## 6. Mobile token preparation

The operator creates one short-lived session locally using server-side
authorization. Flutter never calls the session-creation route and never learns
the operator secret.

The later operator-only PowerShell template is:

```powershell
$sessionResponse = Invoke-RestMethod `
  -Method Post `
  -Uri 'http://127.0.0.1:8000/mobile/dev/v1/capture/sessions' `
  -Headers @{ 'X-WYE-Image-Key' = $env:WYE_IMAGE_API_KEY } `
  -ContentType 'application/json' `
  -Body '{"scopes":["upload","extraction"]}'

$sessionExpiresAt = $sessionResponse.expires_at
$sessionResponse.access_token | Set-Clipboard
Write-Host "Temporary mobile session expiry: $sessionExpiresAt"
```

Safety procedure:

1. Confirm returned scopes are exactly `upload` and `extraction` without
   printing the full response object.
2. Record only TTL and expiry time.
3. Paste the token once into the obscured Flutter dev UI field.
4. Immediately clear the clipboard: `Set-Clipboard -Value ''`.
5. Remove the in-memory shell object after the paste:
   `Remove-Variable sessionResponse -ErrorAction SilentlyContinue`.
6. Never redirect the session response to disk, terminal output, a transcript,
   chat, issue, screenshot, or report.
7. Clear the token from Flutter after the test. Confirm expiration is handled
   as `Token scaduto` or `Token mancante` and blocks further calls.

If the backend restarts, create a new session; never reuse or extend the old
token. If the token appears anywhere unintended, stop under Section 11.

## 7. Flutter run and log plan

Do not execute these commands during Phase 8.6.2.

```powershell
Set-Location C:\Projects\wye\wye-flutter
flutter devices

flutter run -d <DEVICE_ID> `
  --dart-define=WYE_MOBILE_UPLOAD_ENABLED=true `
  --dart-define=API_BASE_URL=http://<LAN_IP>:8000
```

Do not add any secret or token Dart define. Do not use verbose HTTP inspection.
If a separate Flutter process log is required:

```powershell
flutter logs -d <DEVICE_ID> 2>&1 |
  Tee-Object -FilePath '<SAFE_LOG_DIR>\flutter-mobile-e2e.log'
```

The log above is a process/device log and remains distinct from the structured
capture-flow panel. Expand **Log tecnici sanitizzati** in the dev upload panel
to inspect the bounded in-memory events. Copy only after completing the
forbidden-content audit, paste only the minimal relevant lines into the log
template, and then use **Svuota**. Before sharing any process log, scan it and
remove the complete artifact if prohibited content is found; do not preserve a
partially redacted secret-bearing original in the repository.

## 8. Manual test scenario and expected observations

Use one non-sensitive packaged-food test product already represented by a
positive `productId`. Prefer an ingredients image for the first run; nutrition
is an allowed alternative. Do not use `product_front` for extraction.

> **Route selection guard:** use only the separate dev-only `Upload mobile
> locale` panel, including its `Seleziona immagine` and `Avvia upload` actions.
> Do not use the ordinary Add Product `Scatta foto` or `Carica foto` tiles:
> those controls invoke the legacy `/analyze-image` path and do not test the
> mobile initialize/binary PUT/finalize facade.

| Step | Operator action | Expected UI | Expected backend event/status | Frontend evidence | Safe IDs |
| --- | --- | --- | --- | --- | --- |
| 1 | Open the app built with the two approved defines | Dev token and mobile upload panels visible | None | Panel visibility recorded | None |
| 2 | Paste temporary token and set matching local validity | `Token presente` with expiry; token field cleared | Prior operator call: `session_create`, `created`, HTTP 201 | UI state only | Do not record token |
| 3 | Enter/scan barcode and enter existing positive product ID | Image selection becomes available | Product lookup may be separate from facade; do not invoke legacy analysis | Record resolved/matched state | Barcode, productId |
| 4 | Select `ingredients` or `nutrition`; capture/select image | `Preparazione metadati`, then `Immagine pronta per upload` | None | UI state; no image/path in logs | Purpose only |
| 5 | Start upload | Initialize, binary send, finalize progress states | `upload_initialize`/`created` HTTP 201; storage PUT 2xx; `upload_finalize`/`finalized` HTTP 2xx | Sanitized started/succeeded/failed event lines | productId, productImageId, storageObjectId |
| 6 | Confirm association | `Upload associato; estrazione non avviata` | Finalize event contains distinct image/storage IDs | UI state | productImageId != storageObjectId is not required, but identities must remain separate |
| 7 | Start extraction | `Avvio estrazione`, then completed or loading | `extraction_create`/`completed` HTTP 201 | Sanitized extraction event/status; no extracted text | extractionRunId |
| 8 | If loading, select refresh with bounded manual retries | `Estrazione in elaborazione`, then completed/failure | `extraction_get`/`completed` HTTP 200 per refresh | Record retry count and state sequence | extractionRunId unchanged |
| 9 | Inspect result summary | Completed state and allowlisted item count/text; no score | No scoring event or endpoint | Record state and item count, not raw text | run ID only |
| 10 | Clear token | `Token mancante`; further actions blocked | No new facade call | UI state | None |

For every network step, record only the HTTP status/status class, safe backend
event, latency if already present, and safe numeric IDs. Do not record request
or response bodies. A pending/running extraction is not a failure; refresh
manually with a small recorded retry count and no automatic retry storm.

### 8.1 Expected negative observations

- No Flutter request contains `X-WYE-Image-Key`.
- Binary PUT contains neither Bearer authorization nor a server secret.
- No call reaches `/analyze`, `/analyze-image`, or a scoring route.
- No numerical overall score appears or changes.
- No token, full signed URL, query signature, image path/bytes/base64, raw
  provider response, or secret-bearing stack trace appears in logs or shared
  evidence. The UI may show allowlisted normalized item text, never the raw
  OCR/provider fallback, and that text is not copied into the test report.
- `product_front` shows extraction unavailable and provides no start action.

## 9. Log capture and sanitation procedure

Use `WYE_PHASE_8_MOBILE_E2E_TEST_LOG_TEMPLATE.md` for the shareable record.

1. Capture backend and Flutter process logs only into `<SAFE_LOG_DIR>`, outside
   the repository. Structured frontend events remain in app memory only.
2. Stop the run before inspecting or copying logs.
3. Search locally for authorization headers, token fragments, secret variable
   values, URL query markers/signature names, image paths, base64 markers, raw
   bodies, and extracted/provider text.
4. If any prohibited value may be present, follow the secret-exposure stop path
   in Section 11. Do not share or commit that log.
5. Copy only reviewed, minimal event lines into the template. Prefer summaries
   over complete logs.
6. After copying the reviewed structured frontend lines, clear the in-memory
   panel and clear the clipboard after transferring the sanitized evidence.
7. Screenshots are optional and must exclude/blur token fields, notifications,
   addresses, full URLs, local paths, product/provider text not needed for the
   assertion, and other personal data.
8. Re-run `git status --short` before any later review; logs and screenshots
   must remain untracked and outside the repository unless a separately
   reviewed sanitized artifact is explicitly authorized.

## 10. Failure triage guide

Follow the first matching branch and do not bypass a failed prerequisite.

### 10.1 Connectivity

1. **Phone cannot reach FastAPI health**
   - Confirm both devices are on the same trusted LAN.
   - Confirm Uvicorn binds `0.0.0.0`, not loopback only.
   - Confirm the Flutter URL uses the PC LAN address.
   - Check private-network firewall allowance and client isolation.
   - Do not proceed to token or upload calls.

2. **FastAPI reachable, presigned storage PUT unreachable**
   - Stop retries.
   - Verify the storage endpoint host emitted by the signer is phone-reachable.
   - Check MinIO/S3 bind address, port, DNS, TLS trust, and firewall.
   - Never paste the full presigned URL into logs or chat; report host and error
     class only.

### 10.2 Authorization and identity

3. **Token missing, expired, invalid, or wrong scope**
   - Confirm facade is enabled and TTL is within 30-900 seconds.
   - Confirm the operator requested both scopes.
   - If backend restarted, create a fresh token out of band.
   - Never place the operator key in Flutter or extend a token client-side.

4. **Product ID missing or invalid**
   - Stop before initialize.
   - Resolve/create the product through an already authorized product workflow,
     or select an existing test product.
   - Do not substitute the barcode for `productId`.

### 10.3 Upload and extraction

5. **Upload initialize fails**
   - Correlate sanitized backend event, HTTP class, productId, purpose, and safe
     error code.
   - Check facade flag, upload scope, storage configuration, MIME/size/digest.

6. **Binary PUT fails or outcome is unknown**
   - Do not retry rapidly and do not log the capability URL.
   - Check capability expiry, storage host reachability, allowed headers, MIME,
     and exact byte size.
   - Preserve only the UI state and safe attempt count; do not expose upload
     capability material.

7. **Finalize fails**
   - Record safe HTTP/error class and productId only.
   - Do not invent `productImageId` or `storageObjectId` and do not start
     extraction.

8. **Extraction start fails**
   - Confirm finalized image, supported purpose, extraction scope, and stable
     idempotent retry path.
   - Record only safe error code and IDs; never provider response text.

9. **Extraction polling/result fails**
   - Confirm product/image/run IDs remain distinct and unchanged.
   - Stop on terminal or inconsistent state; use only bounded manual refresh.
   - Do not fall back to legacy analysis or scoring.

### 10.4 Evidence quality and exposure

10. **Logs are insufficient**
    - Preserve the safe manual state/status summary.
    - Do not enable verbose body/header logging.
    - Use the existing bounded structured panel; if it remains insufficient,
      stop and request a separately reviewed instrumentation change.

11. **Possible secret exposure**
    - Stop app, logging, and test traffic immediately.
    - Restrict/quarantine the local artifact; do not paste or commit it.
    - Expire the mobile session by waiting for TTL or restarting the single
      local backend process.
    - Rotate any possibly exposed server/storage/provider credential through
      the responsible operator process.
    - Remove the unsafe local capture according to the operator's approved
      secure-deletion procedure; this runbook does not authorize deletion.
    - Review and fix redaction before requesting another run.

## 11. Mandatory stop conditions

Stop immediately if any of the following occurs:

- a server secret, mobile token, authorization header, full signed URL, or
  query signature appears in logs, UI, clipboard history, screenshot, or report;
- image bytes, base64, a sensitive raw image path, raw request/response body,
  raw OCR/provider payload, or secret-bearing stack trace is captured;
- `/analyze`, `/analyze-image`, a scoring endpoint, or scoring runtime is called;
- a numerical overall score appears or extraction mutates score state;
- production/release configuration, a public interface, or a non-local
  environment is touched;
- an unexpected backend/database mutation occurs outside the intended
  capture/upload/finalize/extraction records;
- product, image, storage, or extraction-run identifiers are missing,
  fabricated, conflated, or inconsistent;
- repeated requests form an unbounded retry/polling loop;
- logs cannot support a safe diagnosis without enabling prohibited logging.

After a stop, do not resume in the same session unless the cause is understood,
affected temporary material has expired/been handled, and renewed authorization
is explicit.

## 12. Post-test report format

After a later authorized run, paste back only the completed sanitized template
and a short command summary in this exact order:

1. authorization reference and test window;
2. app/backend commit IDs and clean-tree confirmation;
3. sanitized environment summary using host aliases only;
4. commands executed with placeholders retained and secrets omitted;
5. prerequisite PASS/FAIL results;
6. ordered UI states;
7. HTTP status classes plus minimal safe backend and frontend event summaries;
8. productId, purpose, productImageId, storageObjectId, extractionRunId, and
   retry count;
9. expected versus actual outcome;
10. sanitized errors and triage performed;
11. stop conditions checked;
12. confirmation that token/clipboard were cleared and flags/firewall were
    returned to their default/off state.

Do not paste full log files. Do not paste tokens, headers, environment values,
URLs with paths or queries, raw bodies, images/base64, extracted label text,
provider content, or unreviewed screenshots.

## 13. Post-run shutdown checklist

- [ ] Clear token in Flutter.
- [ ] Clear the in-memory structured frontend log panel.
- [ ] Clear clipboard and remove the in-memory PowerShell session object.
- [ ] Stop Flutter log capture.
- [ ] Stop the single local FastAPI process.
- [ ] Stop the local Moto process.
- [ ] Restore `WYE_MOBILE_UPLOAD_FACADE_ENABLED` to absent/false for later
  processes.
- [ ] End the Flutter build/run; normal builds remain default-off.
- [ ] Remove/disable the temporary private-network firewall allowance using the
  operator's approved process.
- [ ] Inspect and sanitize evidence before sharing.
- [ ] Confirm repository working tree contains no logs, screenshots, images,
  tokens, environment files, or generated artifacts.
- [ ] Do not run cleanup, prune, or destructive database/storage operations as
  part of this runbook.

## 14. Historical Phase 8.6.2 checkpoint

    checkpoint: Phase 8.6.2 sanitized frontend log capture hooks
    implementation_status: IMPLEMENTED LOCALLY - REVIEW AND COMMIT PENDING
    runbook_status: UPDATED LOCALLY
    real_device_test_executed: NO
    endpoint_calls_performed: NONE
    backend_services_started: NONE
    backend_feature_flag_default: FALSE
    flutter_feature_flag_default: FALSE
    mobile_token_transport: OUT-OF-BAND; IN-MEMORY ONLY
    required_mobile_scopes: UPLOAD, EXTRACTION
    frontend_structured_logger: DEV-ONLY; IN-MEMORY; SANITIZED; LATEST 200 EVENTS
    frontend_log_export: DEV PANEL COPY AND CLEAR; NO PERSISTENCE
    server_secrets_in_flutter: PROHIBITED
    raw_payload_logging: PROHIBITED
    scoring_runtime_authority: NONE
    production_runtime_authority: NONE
    release_authority: NONE
    next_recommended_subphase: Phase 8.6.2.1 review and commit log hooks

Historical implementation verdict:

```text
READY_FOR_PHASE_8_6_2_1_REVIEW_AND_COMMIT_LOG_HOOKS
```

## 15. Phase 8.6.3a.2 local-environment checkpoint

    checkpoint: Phase 8.6.3a.2 storage and fake extraction localization
    backend_python: 3.11.5
    backend_virtualenv: backend/venv/e2e311
    storage_runtime: MOTO 5.1.11 - LOCAL ONLY
    storage_provider_value: s3
    storage_path_style: TRUE
    presigned_put_smoke: PASSED ON PC LOOPBACK
    phone_storage_reachability: NOT YET VALIDATED
    extraction_runtime_environment: WYE_RUNTIME_ENVIRONMENT=e2e
    extraction_provider: WYE_EXTRACTION_PROVIDER=fake
    fake_non_local_behavior: FAIL CLOSED
    external_provider_calls: NONE
    backend_health_smoke: PASSED ON PC LOOPBACK
    real_device_test_executed: NO
    scoring_runtime_authority: NONE
    production_runtime_authority: NONE
    release_authority: NONE
    next_recommended_subphase: Phase 8.6.3a.3 environment review and commit

Expected environment-localization verdict:

```text
READY_FOR_PHASE_8_6_3A_3_ENV_REVIEW_AND_COMMIT
```

## 16. Phase 8.6.4 sanitized HTTP 500 postmortem

The first real-device photo attempt returned HTTP 500 but is not a valid
mobile-facade result. Sanitized local evidence shows a frontend call to the
legacy `/analyze-image` route and backend frames in `analyze_image` and
`analyze_image_with_ai`, ending in the safe exception category
`openai.BadRequestError`. There was no mobile initialize route, backend
`mobile_facade` event, binary PUT event, finalize event, or extraction-run
event in the retained evidence.

This localizes the observed failure to the legacy image-analysis path before
mobile upload initialization. It does not establish a Moto, storage,
presigning, finalize, extraction, or scoring defect. Raw provider/request data
is intentionally excluded, so the exact provider rejection detail is not
asserted.

The full sanitized finding is recorded in
`WYE_PHASE_8_MOBILE_E2E_500_POSTMORTEM.md`. The standalone operator procedure
is `WYE_MOBILE_E2E_SELF_TEST_GUIDE.md`. A future authorized run must record
`ui_entry_path`, the failing stage, safe status/category, safe IDs, retry count,
and whether backend `mobile_facade` events exist. It must stop if the legacy
photo path is selected or prohibited content appears.

    checkpoint: Phase 8.6.4 mobile E2E 500 postmortem and self-test guide
    first_device_attempt: APP LAUNCHED; PHOTO ACTION FAILED ON LEGACY ANALYZE-IMAGE PATH
    mobile_facade_result: NOT TESTED BY THE FAILED ATTEMPT
    runtime_fix_applied: NO
    repeated_device_run: NO
    endpoint_calls_performed_by_postmortem: NONE
    external_provider_calls_performed_by_postmortem: NONE
    scoring_runtime_authority: NONE
    production_runtime_authority: NONE
    release_authority: NONE
    next_recommended_subphase: Phase 8.6.4.1 review, commit, and targeted 500 debug authorization

Postmortem documentation verdict:

```text
READY_FOR_PHASE_8_6_4_1_REVIEW_COMMIT_AND_500_DEBUG
```
