# WYE Phase 8 — Mobile E2E HTTP 500 postmortem

**Status:** SANITIZED POSTMORTEM — NO RUNTIME FIX APPLIED

**Date:** 2026-09-04

**Repository state reviewed:** branch `ingredients_score`, commit `c225e27f51278c7580726e574508380021e10ce8`

## 1. Scope and safety boundaries

This document records the sanitized analysis of the HTTP 500 observed during the first real-device photo attempt. It does not authorize or perform another device run, upload, endpoint call, provider call, runtime scoring, production deployment, or release.

No secret, token, full presigned URL, query signature, image, base64 value, raw OCR/provider payload, sensitive path, or unredacted request/response body is reproduced here.

## 2. Reported symptom

The user-visible symptom was described as a photo upload failure returning HTTP 500. The phrase “photo upload” was ambiguous because the Add Product screen exposes both legacy photo actions and the separate dev-only mobile upload panel.

## 3. Evidence reviewed

The review used only the locally retained, temporary logs from the failed attempt and the committed frontend/backend source paths. No service was started and no request was replayed.

Sanitized evidence summary:

| Evidence | Result |
| --- | --- |
| HTTP 500 / `Internal Server Error` | Present in Flutter output |
| Flutter call to `/analyze-image` | Present |
| Flutter call to `/mobile/dev/v1/capture/.../uploads` | Not present |
| Mobile-facade structured backend event | Not present |
| Binary PUT/finalize failure event | Not present |
| Backend route frame | `app.main.analyze_image` |
| Backend service frame | `analyze_image_with_ai` |
| Terminal exception category | `openai.BadRequestError` |
| Forbidden-content indicators in retained logs | None detected by the sanitized pattern audit |

The evidence set did not contain a capture request/session identifier, `productId`, image purpose, `productImageId`, `storageObjectId`, initialize/PUT/finalize status sequence, Moto operation status, or structured frontend capture-flow export.

## 4. Failure localization

The observed 500 is localized to the legacy image-analysis path:

1. A standard Add Product photo action selected/cropped an image.
2. The legacy frontend path called `ApiClient.analyzeProductImage`.
3. That client sent `POST /analyze-image`.
4. The backend entered `app.main.analyze_image` and then `analyze_image_with_ai`.
5. The provider client raised `openai.BadRequestError`.

The failure therefore occurred before the dev mobile upload initialization route. There is no evidence that the new mobile initialize → temporary binary PUT → finalize → extraction path was entered.

## 5. What this result does and does not establish

Established:

- the failed attempt used the legacy `/analyze-image` path;
- the response surfaced as HTTP 500;
- the backend provider call ended with a bad-request exception category;
- the attempt did not produce evidence about Moto, the presigned binary PUT, finalization, or the extraction-run flow of the mobile facade.

Not established:

- the exact provider rejection reason, because unsafe raw provider/request material is intentionally omitted;
- a defect in Moto, storage reachability, mobile session handling, upload initialization, binary PUT, finalize, or extraction;
- successful or failed operation of the dev mobile facade;
- any scoring behavior.

The most likely immediate cause of the route mismatch is selection of a normal photo tile instead of the separate `Upload mobile locale` panel. This is an inference from the route evidence and the current widget wiring, not a claim about the user’s intent.

## 6. Correct path for the next authorized diagnostic run

The next run must use only the dev mobile upload UI:

1. configure the short-lived token in Settings;
2. open Add Product and scroll to `Upload mobile locale`;
3. enter the existing positive `productId` separately from the barcode;
4. select the image purpose;
5. use `Seleziona immagine` inside that panel;
6. use `Avvia upload` inside that panel;
7. observe initialize, binary PUT, finalize, and extraction events.

The ordinary `Scatta foto` and `Carica foto` tiles must not be used for this test: they currently invoke the legacy `/analyze-image` behavior.

## 7. Required sanitized evidence for a future 500

Record only:

- UI entry path: `DEV_MOBILE_PANEL` or `LEGACY_PHOTO_PATH`;
- safe request/session correlation identifier;
- operation and stage: initialize, binary upload, finalize, extraction start, extraction refresh;
- HTTP status code or status class;
- safe error category;
- elapsed time and retry count;
- `productId`, barcode, image purpose, `productImageId`, `storageObjectId`, and `extractionRunId` when available and non-sensitive;
- sanitized frontend capture-flow events;
- sanitized backend `mobile_facade` events;
- storage operation name and status class only.

Never record the mobile token, `X-WYE-Image-Key`, storage/database/provider secrets, a full signed URL, query parameters or signatures, raw paths, image bytes, base64, raw OCR/provider payloads, or unredacted stack traces.

## 8. Stop conditions

Stop without retrying if:

- the selected UI path is the legacy photo flow;
- the mobile token or any server secret appears in output;
- a full signed URL or signature appears in output;
- the phone cannot reach both FastAPI and the storage host over the trusted LAN;
- the dev-only feature is not explicitly enabled or the environment is not local/dev;
- an external extraction/scoring provider would be called;
- the repository becomes dirty unexpectedly;
- production/release behavior would be required.

## 9. Conclusion

The first device attempt is not a valid pass/fail result for the Phase 8 mobile upload facade. It tested the legacy `/analyze-image` route and failed in the external-provider analysis call. The mobile upload implementation remains unverified on a real device.

**Postmortem verdict:** `FAILURE_LOCALIZED_TO_LEGACY_ANALYZE_IMAGE_PATH`

**Next controlled step:** review/commit these documentation artifacts, then authorize a targeted real-device retry using the dev mobile panel and sanitized evidence checklist.
