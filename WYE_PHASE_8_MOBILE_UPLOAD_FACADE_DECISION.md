# WYE — Phase 8.5.3 Mobile Upload Facade Decision RFC

## 1. Status and authority

    phase: Phase 8.5.3 — Mobile Upload Facade Decision RFC
    status: APPROVED — OPTION A / DEV-LOCAL MVP ONLY
    decision: OPTION A APPROVED
    approval_date: 2026-09-03
    approval_scope: LOCAL/DEV MVP INTEGRATION AND REAL-DEVICE TEST PREPARATION ONLY
    approved_option: OPTION A — DEV-ONLY FASTAPI MOBILE FACADE
    production_deployment_authority: NONE
    flutter_runtime_authority: NONE
    backend_runtime_authority: NONE
    endpoint_call_authority: NONE
    scoring_runtime_authority: NONE
    release_authority: NONE
    overall_numerical_candidate: NONE / DEFERRED

This RFC compares safe boundaries for exercising the WYE capture, binary
upload, finalization, and optional label-extraction flow from a real Flutter
phone. On 2026-09-03, the product/technical owner explicitly approved Option A
for local/dev MVP integration and real-device test preparation only.

The approval selects the development architecture. It does not itself modify
or authorize files for a runtime implementation task; that work still requires
a separately scoped authorization and review.

This document does not authorize Flutter or backend changes, live endpoint
calls, deployment, production authentication, scoring, or release. Capture and
extraction remain data-ingestion operations, not a product assessment. They
must not produce, infer, or activate a numerical overall score.

## 2. Context and inspected baseline

The decision is grounded in the current repository behavior:

- Flutter selects `API_BASE_URL` from `--dart-define` when provided. Its
  defaults target `10.0.2.2` for an Android emulator and loopback for other
  local targets. A physical phone therefore needs an explicit device-reachable
  FastAPI address.
- The current Flutter `ApiClient` has no `X-WYE-Image-Key` handling. It still
  contains legacy analysis and base64-capable product paths, which the Phase
  8.5 flow must not use as fallbacks.
- Product-image initialize, finalize, list, and access routes are protected by
  `require_image_api_key`. Label-extraction routes use the same dependency.
- `require_image_api_key` compares `X-WYE-Image-Key` with the server-side
  `WYE_IMAGE_API_KEY`. This is a shared operational credential, not a mobile
  user/session credential.
- Upload initialization returns a temporary presigned PUT URL plus required
  headers and expiry. Finalization validates MIME, byte size, content
  signature, and SHA-256 before returning distinct `storage_object_id` and
  `product_image_id` values.
- Extraction is supported for ingredients and nutrition images and requires an
  idempotency key. It is protected by the shared image key and remains separate
  from scoring.
- The storage adapter signs URLs using the configured storage endpoint. The
  current example MinIO endpoint is `http://localhost:9000`, which a physical
  phone cannot resolve as the development computer.
- The Phase 8.5.1 flow and Phase 8.5.2 implementation plan already require
  FastAPI control-plane operations, a temporary presigned binary PUT as the
  only direct storage request, redacted diagnostics, and no scoring runtime.

These facts leave a security and product decision: how a real phone receives
narrow temporary authority without receiving a reusable server credential.

## 3. Decision problem

Select the development boundary that permits a real phone to:

1. resolve or create a product identity;
2. initialize an upload for that product;
3. PUT the exact image bytes to a temporary presigned URL;
4. finalize and retain the product-image association;
5. start and retrieve ingredients/nutrition extraction when applicable;
6. capture safe Phase 8.6 diagnostics;

while ensuring the phone never contains a shared server, database, storage, or
provider secret.

The immediate decision is for MVP development and real-device validation. It
is not a decision about production identity, account lifecycle, authorization,
or release readiness.

## 4. Non-negotiable constraints

Every acceptable option must preserve all of the following:

1. `X-WYE-Image-Key`, `WYE_IMAGE_API_KEY`, database credentials, storage
   credentials, extraction-provider keys, and other server secrets remain
   server-side.
2. A shared server key must not be compiled into Flutter source, assets,
   fixtures, native resources, application storage, CI variables exposed to
   the build, or `--dart-define`.
3. Flutter uses FastAPI for the WYE control plane. Direct Flutter access is
   limited to the exact binary PUT authorized by a temporary presigned URL.
4. Presigned URLs and mobile session material are temporary capabilities. They
   are memory-only where practical, least-privilege, expiry-bound, and never
   logged in full.
5. The feature is disabled by default and fails closed when authorization,
   storage, signing, or network configuration is absent or invalid.
6. A physical device must reach both `API_BASE_URL` and the exact host embedded
   in the presigned URL. Loopback-only addresses are invalid for LAN testing.
7. Product `product_id` remains distinct from barcode. Product-image ID remains
   distinct from storage-object ID.
8. No option may fall back to base64 image payloads, `/analyze`,
   `/analyze-image`, placeholder scores, or a client-side score calculation.
9. Capture/upload/extraction errors and missing results never become zero or
   another score value. The numerical overall score remains unavailable and
   deferred.
10. No medical, clinical, therapeutic, personalized dietary, dose, frequency,
    portion, safety, healthiness, regulatory, certification, approval, or
    individual-suitability claim is authorized.
11. Runtime, release, and production use require later explicit authorization.

## 5. Evaluation criteria

The options are compared on:

- protection of reusable secrets;
- least privilege, expiry, and revocation;
- ability to validate a real phone, camera, and network path;
- reuse of existing upload/finalize/extraction services;
- implementation and review size for MVP development;
- operational clarity and diagnosability;
- migration path toward production authentication;
- ability to disable or roll back without reviving legacy flows.

## 6. Options

### 6.1 Option A — Dev-only FastAPI mobile facade

**Decision: approved for local/dev MVP real-device testing preparation only.**

Proposed topology:

```text
operator-approved development session
  -> Flutter phone
  -> FastAPI mobile facade at device-reachable API_BASE_URL
  -> existing server-side product/upload/finalize/extraction services
  -> PostgreSQL and MinIO/S3

Flutter phone
  -> one raw binary PUT to a short-lived presigned storage URL
```

Boundary rules:

- FastAPI retains `X-WYE-Image-Key` and every server credential server-side.
  Prefer calling the existing service layer directly; the facade must not
  expose the key or require Flutter to replay it.
- The facade is registered only when an explicit development feature flag is
  enabled. Disabled or incomplete configuration returns a closed/unavailable
  state.
- An operator-mediated bootstrap issues a short-lived, scoped mobile session
  capability. The bootstrap mechanism, transport protection, TTL, operation
  scopes, resource binding, replay controls, and revocation behavior require a
  separate security review before implementation.
- The recommended session is limited to the capture flow and development
  environment. It is not a general login and grants no administrative,
  review-approval, scoring, database, or storage-listing authority.
- FastAPI issues only narrow upload/extraction capabilities. Upload init binds
  product ID, purpose, MIME, size, checksum, expiry, and one staging object.
  Extraction authority binds the finalized product/image identity and allowed
  document type.
- The presigned URL authorizes only the required PUT. Flutter sends the exact
  bytes and allowlisted signed headers, then returns to FastAPI for finalize and
  extraction control-plane calls.
- Session and presigned capabilities are held in memory, cleared on expiry,
  cancellation, terminal error, feature disable, and app lifecycle teardown
  where observable.
- Plaintext LAN transport is not acceptable for a reusable bearer capability.
  Approval must select protected local transport, such as reviewed development
  HTTPS or an authenticated encrypted tunnel. Any exception would require an
  explicit threat decision and must not become a production precedent.

Strengths:

- validates the real camera, phone filesystem, Flutter state, LAN path,
  presigned PUT, FastAPI, storage, finalization, and extraction lifecycle;
- reuses existing backend service invariants without placing their shared key
  in the mobile trust boundary;
- smaller and more reversible than a complete production identity system;
- gives Phase 8.6 one correlation boundary and a clear disable switch;
- can later be retired or placed behind production authentication.

Costs and risks:

- requires a new, carefully reviewed development authorization/bootstrap
  mechanism;
- requires device-reachable FastAPI and presigning/storage hosts, firewall and
  certificate/tunnel configuration;
- a bearer capability can be stolen if transport or logging is unsafe;
- dev-only routes can accidentally survive into release builds or deployed
  environments unless fail-closed gates are tested;
- the facade contract may be mistaken for the future production API unless its
  status and scope are explicit.

Required mitigations:

- disabled-by-default backend and Flutter flags with environment allowlisting;
- short TTL, narrow operations, resource binding, bounded request use where
  practical, explicit expiry, and server-side revocation;
- no token or signed-URL persistence and negative logging tests;
- protected transport and a device-reachable signing topology;
- startup/runtime assertions preventing dev facade enablement in production
  configuration;
- audit events with safe aliases and correlation IDs, never capability values;
- a separate implementation review and a separate Phase 8.6 execution
  authorization.

Fit: the safest practical route for MVP real-phone development, but not a
production authentication design and not release authorization.

### 6.2 Option B — Local desktop/harness-only upload test

The phone does not receive upload authority. A trusted local desktop script or
test harness exercises initialize, PUT, finalize, and extraction while Flutter
continues to use fakes and local widget/state tests.

Strengths:

- keeps all server credentials and capabilities on the development computer;
- reuses current protected operational routes without a new mobile facade;
- provides a low-risk fallback for validating storage integrity, idempotency,
  finalization, and extraction when LAN or MinIO reachability blocks;
- is quick to disable and leaves the mobile application unchanged.

Limitations:

- does not validate camera/gallery behavior, phone file access, mobile network
  policy, LAN routing, device DNS, certificates, lifecycle cancellation, or the
  actual Flutter-to-FastAPI boundary;
- cannot complete the real-phone objective of Phase 8.6;
- delays rather than solves mobile authorization.

Fit: approved fallback or diagnostic step if Option A infrastructure is
blocked. It is not an equivalent substitute for mobile E2E evidence.

### 6.3 Option C — Full authenticated user/session model

Introduce production-grade user identity, login/session lifecycle, product and
submission ownership, authorization policy, revocation, account recovery,
auditing, abuse controls, and deployment-grade transport. The capture routes
would be protected by this general model.

Strengths:

- strongest long-term boundary and clearest path to multi-user production;
- supports durable ownership, policy enforcement, revocation, abuse controls,
  and broader API consistency;
- avoids creating a development-only authorization concept that later needs
  retirement.

Costs and risks:

- substantially expands product, privacy, security, database, backend, mobile,
  testing, and operational scope;
- requires decisions not yet authorized for the WYE MVP;
- can delay capture-flow validation while solving unrelated account concerns;
- creates release expectations that Phase 8 does not authorize.

Fit: preferred long-term production direction, but too large for immediate
Phase 8.5 MVP work unless explicitly authorized as a separate program.

### 6.4 Option D — Embed `X-WYE-Image-Key` in Flutter/mobile app

Place the shared key in Dart, a native resource, asset, local configuration,
CI-supplied build value, or `--dart-define`, then call the current protected
routes directly.

This option is **rejected**.

Reasons:

- a mobile binary and its runtime traffic/configuration cannot protect a
  reusable shared server secret from extraction;
- compromise grants the operational authority of the shared key rather than a
  narrow, expiring capture capability;
- rotation invalidates all builds and does not repair already distributed
  copies;
- `--dart-define` changes delivery mechanics, not the mobile trust boundary;
- it violates the controlling Phase 8.5 security constraint and is forbidden
  even for real-phone development testing.

No implementation task may revive Option D as a temporary workaround.

## 7. Comparison summary

| Criterion | A: Dev facade | B: Desktop harness | C: Full auth | D: Embedded key |
| --- | --- | --- | --- | --- |
| Reusable server secret stays off phone | Yes | Yes | Yes | No |
| Real-phone capture/network validation | Yes | No | Yes | Yes, unsafely |
| Short-lived/scoped mobile authority | Yes, required | Not applicable | Yes | No |
| Immediate MVP scope | Moderate | Small | Very large | Superficially small |
| Production-ready | No | No | Potentially, after full review | No |
| Rollback/disable clarity | Strong if gated | Strong | Requires full design | Unacceptable |
| Decision treatment | Approved, dev/local only | Fallback | Future work | Rejected |

## 8. Approved decision

**Option A, a dev-only FastAPI mobile facade, is approved** as the development
path for local/dev MVP integration and real-device test preparation. Use Option
B as the fallback when protected LAN, certificate/tunnel, firewall, or
device-reachable MinIO configuration prevents real-phone execution. Option C
remains explicitly separate future work. Option D remains prohibited.

Approval record:

- approval date: 2026-09-03;
- approval authority: explicit product/technical-owner instruction;
- scope: local/dev MVP integration and real-device testing preparation only;
- selected boundary: FastAPI control plane plus temporary presigned binary PUT;
- server secrets: server-side only; never embedded in Flutter;
- default state: disabled;
- production deployment and public release: not authorized;
- scoring runtime and numerical overall score: not authorized;
- Option B retained as fallback, Option C deferred, and Option D rejected.

The later implementation task must still freeze the bootstrap and
protected-transport mechanism, session TTL/scopes/resource binding/revocation,
allowed environments/hosts/devices, feature flags, and facade retirement owner.
Those implementation details may not weaken the approved constraints.

## 9. Consequences of approving Option A

Positive consequences:

- Phase 8 can test the full phone-to-storage-to-extraction path without a
  shared server secret in Flutter;
- the existing upload integrity and extraction service behavior can remain the
  canonical backend implementation;
- frontend code can depend on typed, narrow control-plane interfaces and fakes;
- failures can be correlated across device, facade, storage, and extraction.

Tradeoffs:

- the project must operate a development authorization lifecycle and protected
  transport before the first live test;
- separate internal and device-reachable storage endpoints may be required so
  generated signatures contain a host the phone can resolve;
- configuration, firewall, certificate/tunnel, expiry, clock, and app-lifecycle
  failures become part of the test matrix;
- the dev facade must be visibly non-production and eventually removed,
  replaced, or placed behind Option C.

Non-consequences:

- approval would not approve production authentication or release;
- it would not approve scoring, an overall number, medical/safety claims, or
  transformation of extracted label data into an assessment;
- it would not permit Flutter to call the existing key-protected routes with
  `X-WYE-Image-Key`.

## 10. Implementation prerequisites

No code work may start until the decision is approved and the implementation
task explicitly authorizes its files. That task must first define:

1. a versioned facade contract for product resolution/creation, upload init and
   finalize, extraction start, and result retrieval;
2. an operator-mediated, short-lived mobile-session bootstrap with protected
   transport, narrow scopes, expiry, revocation, replay policy, and safe failure
   envelopes;
3. direct server-side reuse of upload/extraction services without forwarding
   or exposing the shared image key;
4. disabled-by-default flags on backend and Flutter plus production-environment
   rejection;
5. a device-reachable `API_BASE_URL`, firewall rule, protected transport, and
   exact MinIO/S3 presigning host topology;
6. capability-safe DTOs that cannot print or serialize bearer tokens and full
   signed URLs through generic diagnostics;
7. product, upload, product-image, storage-object, and extraction identifiers
   with the distinctions defined in Phase 8.5.1;
8. upload size, MIME, SHA-256, expiry, redirect, idempotency, cancellation, and
   unknown-outcome policies;
9. a redacted correlation/logging contract and test sink;
10. a documented owner, disable procedure, expiry/revocation procedure, and
    dev-facade retirement gate;
11. proof that no scoring module, endpoint, mapper, formula, or numerical
    overall output is imported or activated.

## 11. Test implications

### 11.1 Before any real-phone call

- Backend contract tests: facade disabled by default; production configuration
  rejection; bootstrap/session expiry, scope, resource binding, revocation,
  replay, malformed capability, and stable error mapping.
- Backend isolation tests: existing image/extraction services are reused; the
  shared image key never appears in a response; no scoring import or call.
- Flutter unit tests: capability-safe parsing, expiry, state transitions,
  cancellation, retry, host allowlist, and no persistence.
- Transport tests with injected fakes: exact request bodies/headers, binary PUT
  only, redirect rejection, timeouts, and absence of `X-WYE-Image-Key`.
- Negative secret tests: source/assets/fixtures/log sinks contain no key,
  session value, authorization header, full signed URL, raw image/base64, raw
  payload, or local image path.
- Configuration tests: invalid/missing API base, HTTP where protected transport
  is required, loopback storage host, production mode, or disabled facade all
  fail closed.

### 11.2 Phase 8.6 real-phone validation

Only after separate authorization, validate:

- operator bootstrap and expiry from the intended device/environment;
- physical camera/gallery bytes and exact SHA-256 through finalize;
- device reachability of FastAPI and the presigned storage host;
- success, cancellation, expiry, offline, unknown PUT, idempotent finalize, and
  extraction recovery paths;
- immediate disable/revocation and fallback to Option B;
- unchanged score state and absent/deferred numerical overall result.

No CI or ordinary unit test may contact the live facade, MinIO/S3, an extraction
provider, or the internet.

## 12. Mobile E2E logging implications

Phase 8.6 needs a single flow correlation ID plus per-request IDs across Flutter
and FastAPI. Safe records may contain timestamps, transition names, endpoint
templates, status, latency, retry number, image purpose, MIME, byte size,
non-secret database IDs, safe capability aliases, truncated checksum, and
stable error codes.

The following must never be recorded:

- `X-WYE-Image-Key`, mobile session/bootstrap values, auth headers, storage,
  database, or provider credentials;
- full presigned upload/read URLs, signatures, query strings, signed headers,
  cookies, or redirect locations containing capabilities;
- raw image bytes, base64, local image paths, raw OCR/label text, unsanitized
  request/response bodies, provider payloads, or exception strings containing
  any prohibited value.

Logs must use endpoint templates and safe host aliases rather than rendered
capability-bearing URIs. A redaction test failure blocks live Phase 8.6 work;
affected capabilities must expire or be revoked, and unsafe artifacts must not
be staged or committed.

## 13. Rollback and disable criteria

The approved implementation must provide one fail-closed switch that disables
mobile session issuance, facade route use, and Flutter live-flow entry without
changing established product lookup or score/evaluability behavior.

Disable the live path and use Option B/fakes when any of these occurs:

- authorization is absent, expired, over-scoped, replayable outside policy, or
  cannot be revoked;
- the facade is enabled in an unapproved environment;
- protected transport is unavailable or certificate/tunnel identity cannot be
  verified;
- `API_BASE_URL` or the presigned host is unreachable from the device;
- a signed URL contains loopback or an unexpected/non-allowlisted host;
- Flutter source, binary, storage, telemetry, crash data, or logs may contain a
  shared secret or reusable capability;
- upload/finalize identifiers or integrity checks are inconsistent;
- PUT outcome cannot be reconciled without blind duplication;
- extraction crosses product/image scope or invokes scoring behavior;
- logs contain a full signed URL, raw payload, base64 image, or local path;
- the disable/revocation control fails during the Phase 8.6 rehearsal.

Rollback must never restore legacy base64 upload, `/analyze-image`, `/analyze`,
placeholder scoring, or an embedded shared key. It must not attempt destructive
server cleanup from the phone.

## 14. Decision record and rejected alternatives

Current record:

- Option A: **approved for local/dev MVP real-device testing preparation only**;
- Option B: **accepted fallback**, not sufficient for real-phone validation;
- Option C: **deferred future architecture**, separate authorization required;
- Option D: **rejected and prohibited**, including delivery through
  `--dart-define`.

This RFC moved from DRAFT through the explicit product/technical approval dated
2026-09-03. The approved scope and constraints are recorded here. Any expansion
to production, public release, scoring, or a different authorization boundary
requires a new explicit decision. A successful desktop harness or availability
of a shared key does not expand this approval.

## 15. Checkpoint

    checkpoint: Phase 8.5.3.1 mobile upload facade decision approval
    artifact_status: APPROVED — OPTION A / DEV-LOCAL MVP ONLY
    decision_status: OPTION A APPROVED
    approval_date: 2026-09-03
    approval_scope: LOCAL/DEV MVP INTEGRATION AND REAL-DEVICE TEST PREPARATION ONLY
    approved_option: OPTION A — DEV-ONLY FASTAPI MOBILE FACADE
    fallback_option: OPTION B — LOCAL DESKTOP/HARNESS ONLY
    future_option: OPTION C — FULL AUTHENTICATED USER/SESSION MODEL
    rejected_option: OPTION D — EMBED X-WYE-IMAGE-KEY IN MOBILE
    runtime_changes_completed: NONE
    endpoint_calls_performed: NONE
    scoring_runtime_connection: NONE
    overall_numerical_candidate: NONE / DEFERRED
    runtime_authority: NONE
    release_authority: NONE
    next_recommended_subphase: Phase 8.5.4 mobile-safe facade implementation

Expected approval verdict:

```text
READY_FOR_PHASE_8_5_4_MOBILE_FACADE_IMPLEMENTATION
```
