# WYE Mobile E2E — standalone self-test guide

> **Phase 9 authority:** this remains a partial technical reference for the canonical dev-only mobile path. Execute acceptance only under `WYE_PHASE_9_APP_ACCEPTANCE_PLAN.md`, record state in `WYE_PHASE_9_FEATURE_ACCEPTANCE_MATRIX.md`, and share evidence through `WYE_PHASE_9_TEST_FEEDBACK_GUIDE.md`; see also `WYE_PHASE_8_TO_9_TRANSITION.md`.

**Audience:** repository owner performing a local/dev real-phone test without Codex

**Scope:** dev-only mobile upload facade on a trusted home LAN

**Not authorized:** production, public release, scoring runtime, `/analyze`, `/analyze-image`, external extraction providers, or secrets embedded in Flutter

> **Critical route warning:** do not use the ordinary Add Product `Scatta foto` or `Carica foto` tiles during this test. Those controls currently call the legacy `/analyze-image` route. Use only the separate `Upload mobile locale` panel and its `Seleziona immagine` and `Avvia upload` buttons.

## A. What this test is

This is a local/dev integration test of the FastAPI mobile upload facade from a
real Android phone on a trusted LAN. It validates upload initialization, a
temporary direct binary PUT to local Moto/S3, finalization, and fake extraction.

It is not a production or release test. It does not authorize runtime scoring,
an overall score, `/analyze`, `/analyze-image`, or an external extraction
provider. Server, storage, database, and provider secrets remain server-side;
Flutter receives only a short-lived scoped mobile session and a temporary
upload capability.

## B. Prerequisites

- Windows workstation and Android phone are on the same trusted private LAN.
- The repository is at `C:\Projects\wye` on branch `ingredients_score`.
- The Python environment `backend\venv\e2e311` and Flutter dependencies are already installed.
- PostgreSQL is running with the approved local database configuration.
- Moto/local S3 and FastAPI can bind to the workstation LAN interface.
- Flutter is installed and the Android phone is connected and visible to `flutter devices`.
- No other service is using TCP ports 5000 or 8000.
- You have an existing positive numeric product ID suitable for local testing. Keep it distinct from the barcode.
- Windows Firewall remains enabled. If access is blocked, create/review a narrowly scoped Private/LocalSubnet rule; never disable the firewall globally.

In PowerShell:

```powershell
Set-Location C:\Projects\wye
git branch --show-current
git rev-parse HEAD
git status --short
```

Stop if the branch is wrong or the working tree is unexpectedly dirty.

Identify the workstation’s private LAN IPv4 address. Do not use `localhost` or `127.0.0.1` in phone-facing URLs:

```powershell
Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } | Select-Object InterfaceAlias,IPv4Address
$lanIp = '<LAN_IP>'
```

## C. Secret safety rules

- Never paste `X-WYE-Image-Key` into Flutter, a report, chat, or command output.
- Never commit `.env` or any environment dump.
- Never paste the mobile token into a report; transfer it only out of band and
  clear it promptly.
- Never paste a full presigned URL, its path/query, or query signature.
- Never paste an image, image bytes, base64, a sensitive raw path, raw OCR text,
  raw provider text, or an unredacted request/response/traceback.
- Never put database, storage, or provider credentials in Dart defines.

## D. Commands and checklist

### D.1 Start local storage and backend safely

Open a dedicated PowerShell window:

```powershell
Set-Location C:\Projects\wye\backend
.\venv\e2e311\Scripts\Activate.ps1
$lanIp = '<LAN_IP>'
python --version
python -c "import moto, uvicorn; print('local_dependencies_ready')"
```

Configure only local/dev values. Random values below are process-local test credentials; the commands do not print them:

```powershell
$env:WYE_RUNTIME_ENVIRONMENT = 'e2e'
$env:WYE_EXTRACTION_PROVIDER = 'fake'
Remove-Item Env:WYE_OPENAI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:WYE_OPENAI_EXTRACTION_MODEL -ErrorAction SilentlyContinue

$env:WYE_MOBILE_UPLOAD_FACADE_ENABLED = 'true'
$env:WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS = '300'
$env:WYE_STORAGE_PROVIDER = 's3'
$env:WYE_STORAGE_ENDPOINT = "http://${lanIp}:5000"
$env:WYE_STORAGE_BUCKET = 'wye-local-e2e'
$env:WYE_STORAGE_REGION = 'us-east-1'
$env:WYE_STORAGE_ACCESS_KEY = [guid]::NewGuid().ToString('N')
$env:WYE_STORAGE_SECRET_KEY = [guid]::NewGuid().ToString('N')
$env:WYE_STORAGE_FORCE_PATH_STYLE = 'true'
$env:WYE_IMAGE_API_KEY = [guid]::NewGuid().ToString('N')
```

Start Moto without access-log output that could expose query signatures:

```powershell
$motoCode = "logging=__import__('logging');threading=__import__('threading');logging.getLogger('werkzeug').disabled=True;Moto=__import__('moto.server',fromlist=['ThreadedMotoServer']).ThreadedMotoServer;s=Moto(ip_address='0.0.0.0',port=5000,verbose=False);s.start();threading.Event().wait()"
$motoProcess = Start-Process -FilePath '.\venv\e2e311\Scripts\pythonw.exe' -ArgumentList @('-c',$motoCode) -PassThru -WindowStyle Hidden
```

Create the local bucket:

```powershell
python -c "from app.storage import StorageSettings,get_storage_adapter; s=StorageSettings.from_env(); get_storage_adapter(s).client.create_bucket(Bucket=s.bucket); print('bucket_ready')"
```

Start FastAPI with access logging disabled and output outside the repository:

```powershell
$safeLogDir = Join-Path ([IO.Path]::GetTempPath()) ('wye-e2e-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $safeLogDir | Out-Null
$backendProcess = Start-Process -FilePath '.\venv\e2e311\Scripts\python.exe' -ArgumentList @('-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000','--log-level','info','--no-access-log') -RedirectStandardOutput (Join-Path $safeLogDir 'backend.stdout.log') -RedirectStandardError (Join-Path $safeLogDir 'backend.stderr.log') -PassThru -WindowStyle Hidden
```

Do not print or paste `$safeLogDir`; review its contents locally and sanitize before sharing anything.

### D.2 Validate LAN reachability

From the workstation:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/health'
Invoke-RestMethod "http://${lanIp}:8000/health"
```

From the phone browser, verify these host-level URLs:

- `http://<LAN_IP>:8000/health`
- `http://<LAN_IP>:5000/`

The storage root may return an XML response or non-success application status; the important result is network reachability. Never open, copy, or log a presigned object URL.

Stop if either host is unreachable. Check Wi-Fi client isolation, Private network classification, narrow firewall rules, and service bindings before continuing.

### D.3 Create and transfer the short-lived mobile session

Create the session from the same backend PowerShell process so the server-only image key never enters Flutter configuration:

```powershell
$sessionResponse = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/mobile/dev/v1/capture/sessions' -Headers @{'X-WYE-Image-Key'=$env:WYE_IMAGE_API_KEY} -ContentType 'application/json' -Body '{"scopes":["upload","extraction"]}'
$sessionResponse.access_token | Set-Clipboard
Write-Host 'Temporary mobile token copied; use it immediately and do not paste it into logs.'
```

Do not print `$sessionResponse`, the token, or request headers. The configured backend TTL is five minutes.

### D.4 Start Flutter on the phone

Open another PowerShell window:

```powershell
Set-Location C:\Projects\wye\wye-flutter
flutter devices
flutter run --no-pub -d <DEVICE_ID> --dart-define=WYE_MOBILE_UPLOAD_ENABLED=true --dart-define=API_BASE_URL=http://<LAN_IP>:8000
```

Do not add `X-WYE-Image-Key`, storage credentials, provider credentials, or the temporary mobile token as Dart defines.

## E. App steps on the phone

1. Open the app and verify the dev-only panels are visible.
2. Open Settings and find the dev-only mobile upload token panel.
3. Paste the temporary token into `Token mobile temporaneo`.
4. Set `Validita locale` to **5 minutes**, matching the backend TTL, then select `Imposta token`.
5. Immediately clear the workstation clipboard:

   ```powershell
   Set-Clipboard -Value ''
   ```

6. Open Add Product.
7. Do **not** select any ordinary `Scatta foto` or `Carica foto` tile.
8. Scroll to the separate `Upload mobile locale` panel.
9. Scan or enter the barcode, then enter/confirm the existing positive `Product ID`. They are not interchangeable.
10. Choose the image purpose: ingredients or nutrition.
11. Select `Seleziona immagine` inside this panel and complete the capture/select/crop step.
12. Select `Avvia upload` inside this panel.
13. Observe upload initialization, binary PUT, and automatic finalization.
14. Start extraction and note the extraction-run identifier/status.
15. If the run remains in progress, use the UI refresh/get action with a bounded retry count; do not invoke a scoring endpoint.
16. Confirm the fake extraction result is visible in its allowlisted form.
17. Expand `Log tecnici sanitizzati`, audit and copy only the minimum safe frontend events, then select `Svuota`.
18. Return to Settings and select `Rimuovi`; clear the clipboard again.

## F. Expected successful result and safe evidence

Expected success:

- initialization/finalization exposes `productImageId` and `storageObjectId` as separate identities (their numeric values need not differ);
- binary PUT succeeds through the temporary capability;
- finalize succeeds;
- extraction start/status uses an `extractionRunId`;
- the fake extraction result is visible in an allowlisted form;
- no `/analyze`, `/analyze-image`, or scoring endpoint is called;
- no numerical score or overall score is shown;
- logs contain event names, safe IDs, stage/status, latency, and retry count only.

Record the result in `WYE_PHASE_8_MOBILE_E2E_TEST_LOG_TEMPLATE.md`. Never record:

- `X-WYE-Image-Key` or the mobile token;
- full signed URLs, query strings, or signatures;
- storage/database/provider secret values;
- image bytes, base64, sensitive raw image paths;
- raw OCR/provider payloads;
- unredacted stack traces or HTTP bodies.

## G. Troubleshooting table

| Symptom | Safe check | Action |
| --- | --- | --- |
| Phone cannot reach FastAPI | Open `http://<LAN_IP>:8000/health` | Check LAN, binding, and Private/LocalSubnet firewall rule |
| Phone cannot reach storage | Open storage host root only | Check `WYE_STORAGE_ENDPOINT`, binding, LAN isolation, and firewall |
| Token rejected/expired | Compare local validity with five-minute backend TTL | Create one new short-lived session; never log it |
| Product ID is missing/invalid | Confirm an existing positive numeric `productId`, separately from barcode | Stop before initialize; do not substitute the barcode |
| UI reports `/analyze-image` or provider error | Verify which photo control was used | Stop; repeat only through `Upload mobile locale` |
| Upload initialize returns 4xx/5xx | Record safe status/category and backend `mobile_facade` event | Stop after one controlled attempt |
| Binary PUT fails | Record status class, latency, retry count; no URL | Check storage reachability and clock; do not expose the URL |
| Finalize returns HTTP 500 | Record safe IDs and status/category | Stop; do not invent IDs or retry indefinitely |
| Extraction fails | Confirm fake provider and record run ID/status | Stop if an external provider would be called |
| Flutter device is not detected | Run `flutter devices`; check USB debugging/authorization and cable or wireless pairing | Stop until the intended phone is listed |
| App opens but dev panels are hidden | Check the exact `WYE_MOBILE_UPLOAD_ENABLED=true` Dart define and restart the dev build | Do not fall back to ordinary photo controls |
| Any secret/signature appears | Do not copy the output | Stop, clear clipboard/log view, and rotate the affected temporary value |

## H. Specific HTTP 500 debug checklist

For an HTTP 500, first stop additional retries. Determine and record, without a
raw body or trace:

- the exact UI control and action used;
- the closest sanitized frontend event;
- the backend route name and HTTP status code;
- the sanitized backend exception/error category, if available;
- whether the failure was before PUT, during PUT, during finalize, or during extraction;
- `productId` and image purpose;
- `productImageId` and `storageObjectId`, only if created;
- the Moto/storage operation class and status only;
- whether any backend `mobile_facade` event exists.

Never include secrets, tokens, full URLs, query signatures, paths, images,
base64, bodies, raw OCR/provider data, or an unredacted traceback.

Use this working checklist locally:

```text
ui_entry_path: <DEV_MOBILE_PANEL|LEGACY_PHOTO_PATH>
exact_ui_step: <SAFE_DESCRIPTION>
stage: <initialize|binary_put|finalize|extraction_start|extraction_status|legacy_analyze_image>
backend_route_name: <ROUTE_NAME_OR_NOT_OBSERVED>
http_status: <number-or-not_available>
backend_traceback_category: <SAFE_CATEGORY_OR_NOT_AVAILABLE>
safe_error_category: <category-only>
productId: <non-sensitive-id-or-redacted>
barcode: <value-or-redacted>
image_purpose: <ingredients|nutrition>
productImageId: <id-or-not_created>
storageObjectId: <id-or-not_created>
extractionRunId: <id-or-not_created>
retry_count: <number>
elapsed_ms: <number-or-not_available>
frontend_events_present: <yes|no>
backend_mobile_facade_events_present: <yes|no>
moto_operation_status_class: <SAFE_CLASS_STATUS_OR_NOT_OBSERVED>
legacy_analyze_image_called: <no|yes-stop>
forbidden_content_audit: <pass|fail-stop>
expected: <short sanitized description>
actual: <short sanitized description>
```

## I. What to paste back into ChatGPT

Paste only this compact sanitized result, never the complete logs:

```text
FastAPI: <OK|FAIL>
Moto: <OK|FAIL>
Flutter run: <OK|FAIL>
temporary token created: <yes|no> (no token value)
upload initialize status: <status-or-not-reached>
binary PUT status: <status-class-or-not-reached>
finalize status: <status-or-not-reached>
extraction status: <status-or-not-reached>
frontend sanitized log excerpt: <minimal reviewed events-or-none>
backend sanitized error summary: <route/status/category-only-or-none>
forbidden-content audit: <PASS|FAIL-DO-NOT-PASTE>
final verdict: <PASS|FAIL|STOPPED>
```

If the forbidden-content audit fails, paste nothing from the affected capture.

## J. Shutdown and cleanup

Stop Flutter with `q` or `Ctrl+C`. In the backend PowerShell window:

```powershell
Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
Stop-Process -Id $motoProcess.Id -ErrorAction SilentlyContinue
Set-Clipboard -Value ''
Remove-Variable sessionResponse -ErrorAction SilentlyContinue

Remove-Item Env:WYE_RUNTIME_ENVIRONMENT -ErrorAction SilentlyContinue
Remove-Item Env:WYE_EXTRACTION_PROVIDER -ErrorAction SilentlyContinue
Remove-Item Env:WYE_MOBILE_UPLOAD_FACADE_ENABLED -ErrorAction SilentlyContinue
Remove-Item Env:WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS -ErrorAction SilentlyContinue
Remove-Item Env:WYE_STORAGE_PROVIDER -ErrorAction SilentlyContinue
Remove-Item Env:WYE_STORAGE_ENDPOINT -ErrorAction SilentlyContinue
Remove-Item Env:WYE_STORAGE_BUCKET -ErrorAction SilentlyContinue
Remove-Item Env:WYE_STORAGE_REGION -ErrorAction SilentlyContinue
Remove-Item Env:WYE_STORAGE_ACCESS_KEY -ErrorAction SilentlyContinue
Remove-Item Env:WYE_STORAGE_SECRET_KEY -ErrorAction SilentlyContinue
Remove-Item Env:WYE_STORAGE_FORCE_PATH_STYLE -ErrorAction SilentlyContinue
Remove-Item Env:WYE_IMAGE_API_KEY -ErrorAction SilentlyContinue
```

Do not delete temporary logs before reviewing whether they contain sensitive material. Do not share them verbatim. Finish with:

```powershell
Set-Location C:\Projects\wye
git status --short
```

The repository should remain unchanged except for documentation work explicitly authorized in a separate phase.
