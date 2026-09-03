# WYE Phase 8.6 Mobile E2E Sanitized Log Template

Status: EMPTY TEMPLATE - DO NOT ADD SECRETS OR RAW PAYLOADS

Use only after explicit authorization for the real-device run. Keep complete
logs outside the repository. Paste only reviewed summaries or minimal sanitized
event lines here.

## 1. Authorization and outcome

    authorization_reference: <REFERENCE_OR_NOT_YET_AUTHORIZED>
    test_date: <YYYY-MM-DD>
    test_window_timezone: <TIMEZONE>
    operator_alias: <NON_SECRET_ALIAS>
    outcome: <PASS|FAIL|STOPPED|NOT_RUN>
    stop_reason: <SAFE_CODE_OR_NONE>

## 2. Versions and commits

    device_model: <MODEL>
    os_version: <VERSION>
    flutter_version: <VERSION>
    dart_version: <VERSION>
    app_commit: <COMMIT_SHA>
    backend_commit: <COMMIT_SHA>
    branch: ingredients_score
    working_tree_before: <CLEAN|NOT_CLEAN>
    working_tree_after: <CLEAN|NOT_CLEAN>

## 3. Sanitized environment

    api_base_url: http://<LAN_HOST>:8000
    storage_endpoint_host_only: <STORAGE_HOST>:<PORT>
    database_name_non_sensitive: <DATABASE_NAME>
    phone_pc_same_trusted_network: <PASS|FAIL|NOT_CHECKED>
    phone_fastapi_health_reachable: <PASS|FAIL|NOT_CHECKED>
    phone_storage_host_reachable: <PASS|FAIL|NOT_CHECKED>
    temporary_firewall_allowance: <NONE|SAFE_RULE_ALIAS>
    backend_facade_enabled_for_window: <YES|NO>
    backend_session_ttl_seconds: <30_TO_900>
    flutter_mobile_upload_enabled: <YES|NO>

Record environment names only, never values:

    backend_env_names_confirmed:
      - WYE_MOBILE_UPLOAD_FACADE_ENABLED
      - WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS
      - WYE_IMAGE_API_KEY
      - PGHOST
      - PGPORT
      - PGUSER
      - PGPASSWORD
      - PGDATABASE
      - WYE_STORAGE_PROVIDER
      - WYE_STORAGE_ENDPOINT
      - WYE_STORAGE_BUCKET
      - WYE_STORAGE_REGION
      - WYE_STORAGE_ACCESS_KEY
      - WYE_STORAGE_SECRET_KEY
      - WYE_EXTRACTION_PROVIDER
      - WYE_OPENAI_API_KEY
      - WYE_OPENAI_EXTRACTION_MODEL

## 4. Command summaries

Keep placeholders; do not paste expanded commands, environment dumps, headers,
token responses, full URLs, or verbose HTTP output.

    backend_start_summary: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
    flutter_device_selector: <DEVICE_ID_OR_ALIAS>
    flutter_run_summary: flutter run -d <DEVICE_ID> --dart-define=WYE_MOBILE_UPLOAD_ENABLED=true --dart-define=API_BASE_URL=http://<LAN_HOST>:8000
    flutter_log_summary: <NOT_CAPTURED|NON_VERBOSE_DEVICE_LOG_CAPTURED>
    session_creation_summary: operator-only local POST; scopes upload+extraction; token not printed

## 5. Prerequisites

| Check | Result | Sanitized note |
| --- | --- | --- |
| Existing backend virtualenv | `<PASS|FAIL>` | `<NOTE>` |
| PostgreSQL available | `<PASS|FAIL>` | `<NOTE>` |
| MinIO/S3 available to backend | `<PASS|FAIL>` | `<NOTE>` |
| FastAPI reachable from PC LAN address | `<PASS|FAIL>` | `<NOTE>` |
| FastAPI reachable from phone | `<PASS|FAIL>` | `<NOTE>` |
| Storage host reachable from phone | `<PASS|FAIL>` | `<NOTE>` |
| Phone visible to Flutter | `<PASS|FAIL>` | `<NOTE>` |
| Temporary token TTL/scopes verified | `<PASS|FAIL>` | `<TTL_AND_SCOPES_ONLY>` |
| Backend/body/header debug logging disabled | `<PASS|FAIL>` | `<NOTE>` |
| Frontend structured logger limitation accepted | `<PASS|FAIL>` | `Current app wiring is NoOp` |

## 6. Test identity and safe IDs

    barcode: <BARCODE>
    product_id: <POSITIVE_INT>
    image_purpose: <ingredients|nutrition>
    product_image_id: <POSITIVE_INT_OR_NOT_CREATED>
    storage_object_id: <POSITIVE_INT_OR_NOT_CREATED>
    extraction_run_id: <POSITIVE_INT_OR_NOT_CREATED>
    extracted_item_count: <NON_NEGATIVE_INT_OR_NOT_AVAILABLE>
    retry_count_upload: <NON_NEGATIVE_INT>
    retry_count_extraction: <NON_NEGATIVE_INT>

Do not record the upload ID/capability, image path, image content, extracted
text, or provider response.

## 7. Ordered UI observations

| Sequence | UI state observed | Expected | Actual | Result |
| --- | --- | --- | --- | --- |
| 1 | Dev panels visible | Yes | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |
| 2 | Token present/expiry state | Present, value hidden | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |
| 3 | Metadata ready | Image ready | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |
| 4 | Upload initialize/PUT/finalize | Ordered progress | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |
| 5 | Image associated | Extraction deferred | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |
| 6 | Extraction start/loading | Neutral state | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |
| 7 | Extraction terminal state | Completed or safe failure | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |
| 8 | Token cleared | Missing; actions blocked | `<SAFE_SUMMARY>` | `<PASS|FAIL>` |

## 8. Sanitized HTTP/backend event summary

Do not paste bodies, headers, full paths containing capability material, or
stack traces. Numeric resource IDs and request IDs matching the safe format are
allowed.

| Time | Event | Status/code | productId | productImageId | storageObjectId | extractionRunId | Retry | Safe note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<TIME>` | `session_create` | `<201/created>` | `-` | `-` | `-` | `-` | `0` | `<NOTE>` |
| `<TIME>` | `upload_initialize` | `<STATUS>` | `<ID>` | `-` | `-` | `-` | `<N>` | `<NOTE>` |
| `<TIME>` | `binary_put` | `<2xx_OR_ERROR_CLASS>` | `<ID>` | `-` | `-` | `-` | `<N>` | Host omitted |
| `<TIME>` | `upload_finalize` | `<STATUS>` | `<ID>` | `<ID>` | `<ID>` | `-` | `<N>` | `<NOTE>` |
| `<TIME>` | `extraction_create` | `<STATUS>` | `<ID>` | `<ID>` | `<ID>` | `<ID>` | `<N>` | `<NOTE>` |
| `<TIME>` | `extraction_get` | `<STATUS>` | `<ID>` | `<ID>` | `<ID>` | `<ID>` | `<N>` | `<NOTE>` |

## 9. Sanitized frontend evidence

Current application wiring emits no structured `CaptureFlowEvent` sink.
Record only non-verbose process observations and UI-state summaries.

    flutter_process_log_class: <LIFECYCLE_ONLY|SAFE_ERROR_CODE|NONE>
    ui_state_sequence: <COMMA_SEPARATED_STATE_NAMES>
    structured_capture_events_available: NO
    raw_log_excerpt: <OMIT_BY_DEFAULT>

If an excerpt is essential, include at most the minimal reviewed line and
replace every address/path/query/body/text value with a descriptive redaction.

## 10. Expected versus actual

    expected_result: upload finalized; extraction completed/read or explicit safe failure; no scoring
    actual_result: <SANITIZED_SUMMARY>
    mismatch: <NONE_OR_SANITIZED_DESCRIPTION>
    triage_branch_used: <RUNBOOK_SECTION_OR_NONE>
    next_action: <SAFE_FOLLOW_UP>

## 11. Error record

    safe_error_code: <CODE_OR_NONE>
    http_status_or_class: <STATUS_OR_NONE>
    failed_step: <STEP_OR_NONE>
    retryable: <YES|NO|UNKNOWN>
    retries_performed: <N>
    sanitized_description: <NO_RAW_BODY_OR_STACK_TRACE>

## 12. Prohibited-content audit

Every item must be PASS before sharing this template.

| Prohibited content | Result |
| --- | --- |
| `X-WYE-Image-Key` value absent | `<PASS|FAIL>` |
| Mobile token/Authorization value absent | `<PASS|FAIL>` |
| Full signed URL/path/query/signature absent | `<PASS|FAIL>` |
| Storage/database/provider credentials absent | `<PASS|FAIL>` |
| Image path, bytes, base64 absent | `<PASS|FAIL>` |
| Raw request/response/OCR/provider payload absent | `<PASS|FAIL>` |
| Secret-bearing stack trace absent | `<PASS|FAIL>` |
| Scoring endpoint/runtime absent | `<PASS|FAIL>` |
| Numerical overall score absent | `<PASS|FAIL>` |
| Unreviewed screenshots absent | `<PASS|FAIL>` |

## 13. Optional screenshots

    screenshots_included: <NO|COUNT>
    each_reviewed_for_secrets_urls_paths_notifications_personal_data: <PASS|FAIL|N/A>
    screenshot_purpose: <SAFE_DESCRIPTION_OR_N/A>

Do not embed screenshots in this template unless a later task explicitly
authorizes a reviewed sanitized artifact.

## 14. Shutdown confirmation

    flutter_token_cleared: <YES|NO>
    clipboard_cleared: <YES|NO>
    backend_stopped: <YES|NO>
    backend_facade_returned_default_off: <YES|NO>
    temporary_firewall_allowance_removed_or_disabled: <YES|NO|N/A>
    logs_reviewed_before_sharing: <YES|NO>
    repository_contains_no_e2e_artifacts: <YES|NO>

## 15. Paste-back package

Paste back:

1. this completed sanitized template;
2. the placeholder-preserving command summaries;
3. safe backend event/status lines only;
4. ordered UI states, safe IDs, retry counts, expected versus actual, and error
   codes;
5. confirmation that all prohibited-content checks passed.

Never paste complete logs, environment dumps, secrets, tokens, signed URLs,
headers, payloads, images, base64, extracted text, provider content, or
unreviewed screenshots.
