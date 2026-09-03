# WYE — Phase 8 Frontend / UX / Integration Plan

## 1. Document status

    phase: Phase 8 — Frontend / UX / integration
    completed_prior_subphase: Phase 8.0.1 — read-only frontend inventory
    current_subphase: Phase 8.1 — frontend baseline preservation and contract gap specification
    document_scope: planning and contract specification only
    runtime_authority: NONE
    release_authority: NONE
    implementation_authority: NONE
    external_validation: FUTURE OPTIONAL NOT PRESENT

This document preserves the existing Flutter baseline and records the contract
gaps that must be resolved before a future frontend implementation is
authorized. It does not authorize Dart, Flutter, backend, API, database,
scoring-runtime, release, or production changes.

The Phase 7 constraints remain controlling: WYE provides broad, approximate,
informational guidance about packaged foods; it is not a doctor; it makes no
medical, clinical, therapeutic, personalized dietary, dose, frequency, portion,
safety, healthiness, regulatory-compliance, certification, approval, or
individual-suitability claim. Internal Informational Assurance is not external
validation or certification.

## 2. Phase 8 status

| Item | Status |
| --- | --- |
| Phase 8.0.1 frontend inventory | COMPLETED — `READY_FOR_PHASE_8_FRONTEND_PLAN` |
| Phase 8.1 baseline preservation and contract-gap specification | COMPLETED BY THIS DOCUMENT |
| Runtime or release | NOT AUTHORIZED |
| Product-scoring candidates | INTERNAL / GOVERNED; NOT PRODUCTION-APPROVED |
| Numerical overall product score | DEFERRED; NO CANDIDATE APPROVED |

The completed inventory found a committed Flutter application at
`wye-flutter/`. The application is a useful preservation baseline, but its
current score DTOs, widgets, mock behavior, legacy backend assumptions, and
some terminology do not yet satisfy the Phase 7 contract.

## 3. Frontend baseline preservation

### 3.1 Preserved application baseline

The existing application path is `wye-flutter/`. Its current navigation uses
GoRouter and declares the following routes:

| Route | Existing screen / purpose |
| --- | --- |
| `/` | Home |
| `/scanner` | Barcode scanner |
| `/product/:barcode` | Product detail |
| `/manual-analysis` | Manual ingredient analysis |
| `/add-product` | Product capture / manual product submission |
| `/history` | Scan history |
| `/settings` | Settings |

Existing screen, widget, theme, router, provider, model, and service files are
committed user work and must be preserved until a separately authorized
implementation subphase changes them deliberately. The baseline architecture
is Provider/ChangeNotifier with local widget state, GoRouter navigation, an
`ApiClient`, Hive initialization/local-storage service, product DTOs, reusable
score widgets, camera/barcode/OCR dependencies, and one Flutter test.

The baseline has the following layers:

| Layer | Existing location | Preservation note |
| --- | --- | --- |
| App bootstrap and dependency injection | `lib/main.dart` | Manual application code |
| Navigation | `lib/router/app_router.dart` | Manual route baseline |
| Screens | `lib/screens/` | Manual UX baseline |
| State | `lib/providers/app_providers.dart` | Manual application-state baseline |
| API and local storage | `lib/services/` | Manual integration baseline |
| DTOs | `lib/models/product_model.dart` | Manual legacy contract baseline |
| Scores/widgets/theme | `lib/widgets/`, `lib/theme/` | Manual UI baseline requiring future review |
| Test | `test/widget_test.dart` | Existing minimal characterization baseline |
| Assets | `img/` | Existing application assets |

### 3.2 Generated or local material

The following must not drive product, UI, or API design decisions:

- `.dart_tool/`, `build/`, `.idea/`, Android `.gradle/`, local properties and
  generated plugin/build artifacts;
- local `web/` files currently ignored by the Flutter `.gitignore`;
- ignored `pubspec.lock` and other machine-specific IDE/cache files.

These files are not an instruction to delete, clean, regenerate, or reformat
anything. A later versioning decision is required for `pubspec.lock`, the web
platform files, and currently tracked generated metadata such as
`.flutter-plugins-dependencies`.

### 3.3 Preservation rules

Before any future code change:

1. retain the current route and screen baseline unless a change is explicitly
   scoped and reviewed;
2. add characterization tests before changing legacy score parsing or display;
3. do not treat the existing mock or backend response shape as the future Phase
   7 API contract;
4. isolate new score/evaluability models from the legacy `Product` model until
   an adapter and migration plan are reviewed;
5. do not expose credentials, backend-internal review actions, or generated
   artifacts through the mobile UI.

## 4. Contract gap specification

### 4.1 Score and evaluability gaps

| Gap | Current baseline | Required Phase 8 resolution |
| --- | --- | --- |
| Mandatory numeric scores | Flutter `Product` requires ingredient and final scores | Permit absence of a score; a number is valid only for a `computable` component |
| Fallback to zero | Missing JSON score fields can become `0` | Remove all missing-to-zero parsing, display, history, and mock fallbacks |
| Mandatory overall | `finalScore` drives the main score card | Treat overall as unavailable/deferred; do not derive, average, or visually imply one |
| Client/mock aggregation | Mock client uses an ingredient/nutrition weighted formula | Remove the assumption; no client-side overall formula is authorized |
| Legacy server scoring | `/analyze` emits a legacy score and the product flow can store placeholder scores | Classify as legacy/non-authoritative; do not map it to the Phase 7 view model |
| Evaluability | No explicit typed evaluability state in the DTO/UI | Model `computable`, `not_computable`, and `non_applicable` explicitly |
| Evidence qualifiers | Coverage, confidence, uncertainty, and missingness are absent or mixed into score presentation | Carry and display them as independent disclosures/gates, never score points |
| Zero semantics | A missing score and zero can follow the same UI path | Preserve zero only as a computed endpoint; never render it for unavailable data |

`not_computable` is a successful semantic output, not a technical error and not
a low score. It must never be hidden, converted to zero, a midpoint, average,
placeholder, fallback, or imputation. `non_applicable` is independently typed
and is neither favorable nor unfavorable. Losing data must not improve a score,
coverage, or confidence.

### 4.2 Product, image, extraction, and security gaps

| Gap | Current baseline | Required Phase 8 resolution |
| --- | --- | --- |
| Product response | Barcode lookup returns a nested legacy `{product, score, ingredients}` shape; nutrition is not a complete frontend contract | Specify a versioned response and an explicit adapter before integration |
| Product creation | Creation returns product data while existing client expects immediately usable score fields | Separate capture/persistence acknowledgement from future assessment results |
| Placeholder scoring | Backend creation can persist `50/80/65` legacy values | Do not surface or reinterpret placeholder values as Phase 7 results |
| Image handling | Existing UI sends base64/data URLs to legacy image analysis | Plan the canonical capture, upload, finalization, and provenance sequence |
| New upload API | Presigned upload endpoints require `product_id` and image API credentials | Resolve product identity ordering and a server-side credential design; never embed a shared image key in the app |
| Label extraction | New extraction flow has image/document type, idempotency, run, item, and provenance concepts | Define an extraction-result DTO and review/correction UX before integration |
| Mapping review | Review endpoints are protected operational workflows | Keep them outside ordinary consumer UI unless a separate role/authorization design approves access |
| User auth | No consumer authentication contract is currently established | Do not infer one from image-key protection; specify it separately if needed |

### 4.3 Claims and terminology gaps

The current baseline contains terminology and concepts requiring review before
any UI release. Their presence in legacy code or documentation does not approve
them for the MVP:

- “Safety Score”, “salubrità”, “healthiness”, or equivalent safety/health
  certification implications;
- “dangerous substances”, hazard/risk labels, colors, grades, or bands that
  could become safety, clinical, or legal conclusions;
- personalized allergy, diet, country, premium fact-check, or profile features
  that imply individual suitability or personal advice;
- consumption programmes, intake logging, quantities, frequency, thresholds,
  reminders, or exposure recommendations;
- medical, clinical, therapeutic, dietetic, dose, portion, or frequency wording;
- certification, compliance, approval, validation, or suitability statements.

This is a terminology review list, not a request to rewrite existing UI copy in
this subphase. Final labels, colors, badges, grades, rankings, and marketing
copy remain outside scope.

## 5. Proposed frontend scoring view-model constraints

This section is a contract sketch, not Dart production code and not a scoring
algorithm. The future API and frontend may use different field names only if
they preserve the following semantics.

```text
AssessmentComponentView
  kind: ingredient | nutrition
  evaluability_status: computable | not_computable | non_applicable
  goodness_percent: integer 0..100 | absent
  assessment_coverage: separate coverage value/state | absent only when not supplied
  confidence_state: policy-defined independent state | absent only when not supplied
  uncertainty: structured disclosure | absent only when not supplied
  missing_inputs: list of structured missing/conflicting/non-comparable inputs
  limitations: list of traceable disclosure items
  explanation: non-claiming explanatory content or reference

ProductAssessmentView
  ingredient_component: AssessmentComponentView
  nutrition_component: AssessmentComponentView
  ingredient_score: optional internal ingredient-level candidate reference,
                    never an alias for product ingredient goodness
  overall_status: unavailable_or_deferred
  overall_goodness_percent: absent
  product_disclosures: separate informational and limitation disclosures
```

Required invariants:

1. `goodness_percent` may exist only when the corresponding component has
   `evaluability_status = computable`.
2. A `computable` value may be exactly `0`; its presence and evaluability state,
   not a color or fallback, distinguish it from missing data.
3. `not_computable` and `non_applicable` must have an absent numeric score.
4. No parser, adapter, fixture, widget, history record, mock, or cache may
   synthesize a numeric score from a missing value.
5. Coverage, confidence, uncertainty, missingness, limitations, flags, and
   evaluability remain separate from each other and from any score.
6. `ingredient_goodness_percent` and `nutrition_goodness_percent` are separate
   product-component outputs. Neither is an overall output or input to an
   unapproved client-side overall calculation.
7. `ingredient_score` remains an internal ingredient-level candidate construct;
   it must not be silently relabeled as a product score, safety result, or
   goodness percent.
8. `overall_goodness_percent` is absent in this phase. Its UI state is
   unavailable/deferred, not zero, null-with-fallback, or an inferred average.

## 6. Future UI behavior constraints

Future UX work must implement stateful presentation, not a single mandatory
score card.

| Topic | Required behavior |
| --- | --- |
| Ingredient score | If ever shown, identify it as an internal ingredient-level candidate; do not present it as safety, health, or product-wide goodness |
| Ingredient goodness | Show a 0–100 value only for a computable product ingredient component; preserve a genuine computed zero |
| Nutrition goodness | Show separately from ingredients and only for a computable nutrition component |
| Overall | Show unavailable/deferred state; no number, band, ring, color implication, formula, or average |
| `not_computable` | Show the typed unavailable state and relevant limitations/missing inputs; no substitute score or score color |
| `non_applicable` | Show a distinct neutral state; do not present it as positive, negative, or unavailable due to error |
| Coverage/confidence/missingness | Present as separate supporting information; do not merge into percentage, grade, or implied quality guarantee |
| Informational scope | Reserve a visible broad-information limitation requirement for relevant result surfaces |
| Not-a-doctor scope | Reserve a visible non-medical limitation requirement for relevant result surfaces |

The wording above describes UI requirements only. It intentionally does not
create final Italian copy, visual hierarchy, colors, badges, grades, or user
claims.

## 7. Phase 8 roadmap refinement

| Subphase | Objective | Gate / output |
| --- | --- | --- |
| 8.1 | Baseline preservation and contract-gap specification | This document; no runtime/code change |
| 8.2 | Typed frontend score/evaluability models and fixture tests | Local DTO/view-model contract and characterization tests; no scoring runtime connection |
| 8.3 | Remove client-side fallback and overall assumptions | Explicit migration plan for legacy DTO, widgets, mock, history, and parser paths |
| 8.4 | Result-state UX | Minimal Flutter UI for computable, not-computable, non-applicable, and deferred/unavailable overall states; component qualifiers remain separate |
| 8.5 | Product capture/upload integration planning | Canonical capture, identity, presigned upload, finalization, provenance, and credential boundary |
| 8.6 | Mobile E2E test & log capture | Real-phone flow validation with device, app, backend, API, and user-flow logs for debugging |
| 8.7 | Integration hardening | Versioned API contracts, authentication/authorization boundary, error semantics, idempotency, retries, accessibility, and tests |
| 8.8 | Final UX/checkpoint review | Product, governance, and claim/disclosure review before seeking any runtime or release authorization |

The detailed Phase 8.5 product-identity, binary-upload, finalization,
provenance, extraction-recovery, mobile-security, and Phase 8.6 logging contract
is recorded in `WYE_PHASE_8_CAPTURE_UPLOAD_FLOW.md`. That artifact is a
specification only and does not authorize frontend or backend implementation.

The proposed file-by-file implementation sequence, DTOs, state machine,
mobile-safe FastAPI boundary, fake/test strategy, logging hooks, and rollback
gates are recorded in `WYE_PHASE_8_CAPTURE_UPLOAD_IMPLEMENTATION_PLAN.md`.
That plan is documentation only; live mobile integration remains blocked until
a separately reviewed mobile facade/session exists.

The mobile-boundary decision is recorded in
`WYE_PHASE_8_MOBILE_UPLOAD_FACADE_DECISION.md`. Option A, a dev-only FastAPI
facade, was approved on 2026-09-03 for local/dev MVP integration and real-device
test preparation only. Phase 8.5.4 now implements the backend-only,
disabled-by-default `/mobile/dev/v1/capture` facade with short-lived scoped
Bearer capabilities. Its dev-only store is process-local, so backend restart
invalidates all tokens and multi-worker sessions are unsupported. Review/commit
and Flutter integration remain separate; scoring, production deployment,
public release, and mobile-embedded secrets remain unauthorized.

The roadmap order is intentional: result semantics and explicit absence must be
made safe before visual refinement or live backend integration.

## 8. Risks and open questions

### Risks

- Legacy DTO and `ScoreCard` contracts can convert missing data into a
  misleading numerical result.
- Legacy backend analysis, fixed placeholder scores, and mock aggregation can
  silently bypass Phase 7 governance.
- Existing terminology and personal-feature concepts can exceed the MVP
  informational/non-medical boundary.
- Base64 image submission lacks the provenance, upload lifecycle, and
  credential separation of the newer backend image flow.
- Minimal frontend testing increases migration regression risk.
- Ignored web and lockfile files create a reproducibility/versioning decision
  that must be made deliberately, not through cleanup.

### Open questions requiring future authorization or decision

1. What versioned frontend-facing API will represent component evaluability,
   coverage, confidence, uncertainty, missingness, and provenance?
2. Which future inputs make ingredient or nutrition components computable,
   not-computable, or non-applicable under the still-open policy decisions?
3. How will the backend separate product creation, extraction, normalization,
   assessment availability, and any future approved candidate output?
4. What trusted service boundary will perform image upload/extraction without
   placing shared credentials in Flutter?
5. Is the Phase 8 MVP strictly packaged foods, and which legacy cosmetic,
   premium, personal, allergy, or consumption concepts are retained, deferred,
   or retired?
6. Which documentation and platform files should be versioned in a dedicated
   housekeeping decision?

## 9. Next implementation candidate

The safest next implementation subphase is:

```text
Phase 8.5.4.1 — review and commit the dev-only, mobile-safe FastAPI facade and
its scoped authorization boundary before any Flutter integration.
```

The review must verify the default-off feature flag, server-side operator
authorization, hashed TTL-bound mobile capabilities, upload/extraction scope,
safe structured errors/logs, service reuse, and focused fake-service tests. The
following Flutter integration phase must validate both `API_BASE_URL` and the
presigned storage host before a separately authorized real-phone run. Neither
phase may enable scoring, introduce an overall number, authorize production or
release, or fall back to legacy base64/analysis paths.

## 10. Checkpoint record

    checkpoint: Phase 8.5.4 dev/local mobile upload facade implementation
    prior_verdict: READY_FOR_PHASE_8_5_4_MOBILE_FACADE_IMPLEMENTATION
    approved_option: OPTION A — DEV-ONLY FASTAPI MOBILE FACADE
    approval_date: 2026-09-03
    approval_scope: LOCAL/DEV MVP INTEGRATION AND REAL-DEVICE TEST PREPARATION ONLY
    feature_flag: WYE_MOBILE_UPLOAD_FACADE_ENABLED — DEFAULT FALSE
    backend_dev_implementation: IMPLEMENTED — REVIEW AND COMMIT PENDING
    flutter_runtime_implementation: NONE
    next_recommended_subphase: Phase 8.5.4.1 review and commit mobile facade
    production_runtime_authority: NONE
    release_authority: NONE
    scoring_runtime_authority: NONE
    implementation_completed_by_this_checkpoint: DEV/LOCAL BACKEND FACADE ONLY
    overall_numerical_candidate: NONE / DEFERRED
    production_deployment_authority: NONE
    git_push_authority: NONE

Expected current verdict:

```text
READY_FOR_PHASE_8_5_4_1_REVIEW_AND_COMMIT
```
