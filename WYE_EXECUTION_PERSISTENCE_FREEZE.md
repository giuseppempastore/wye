# WYE — Scientific Evaluation Execution and Result Persistence Freeze

## Status and authority

This is the normative Phase 7.6.4B-1 design/schema freeze for:

```text
0021_scientific_evaluation_publication
```

Status:

```text
DESIGN FROZEN — READY FOR PHASE 7.6.4B 0021 IMPLEMENTATION
```

Implementation status:

```text
Phase 7.6.4B-1B: REPLAY SEMANTICS AMENDMENT FROZEN
Phase 7.6.4B-2: COMPLETED + COMMITTED
Phase 7.6.4C: COMPLETED + COMMITTED
repository head: 0021_scientific_evaluation_publication
local wye:       0017_ingredient_mapping_history
```

It specializes `WYE_SCORING_EXECUTION_MODEL.md`,
`WYE_SCORING_PERSISTENCE.md`, `WYE_SCORING_SCHEMA_FREEZE.md` and
`WYE_MAPPING_EXECUTION_INPUT_FREEZE.md`. Where the preliminary 7.6.1 physical
sketch differs, this later bounded freeze is authoritative. This checkpoint
introduced no migration at design-freeze time. The later bounded B-2 migration
implements this persistence contract only; it introduces no runtime, selector,
synthesis rule, formula, weight, threshold or numerical score.

## Corrections to the preliminary physical sketch

1. Concrete engine build/source/dependency identity belongs to an attempt. The
   semantic engine contract belongs to the canonical configuration root.
2. Query projections are rebuildable and non-canonical, so no projection digest
   enters the canonical publication bundle. Phase 0022 binds projection
   generations separately.
3. Selection `decision` is `included` or `excluded`; `resolution_state` is
   separately `resolved` or `deferred`. `deferred` is not a decision value.

These corrections remove persistence ambiguity without changing prior
scientific semantics.

## REPLAY semantics amendment

This section supersedes the earlier requirement that every completed execution
owns a new canonical scientific publication and that REPLAY proves equality
inside that new publication. That requirement conflicts with the global
content-addressed artifact identity frozen by 0019 and the exclusive ownership
of result, trace and publication selection artifacts frozen by 0021.

The global artifact rule remains non-negotiable:

```text
same canonical bytes
    -> same scientific_evaluation_artifacts row
```

REPLAY is therefore a reproducibility verification of one historical canonical
publication, not a new scientific interpretation or publication. It has its
own semantic execution and ordinary operational attempts, recomputes canonical
selection/result/trace roots, compares them with the historical publication,
and persists one immutable verification. It creates no new selection-decision,
result, result-component, trace or publication row.

Mode-specific completion is normative:

```text
NORMAL / REFRESH / COUNTERFACTUAL completed
    -> exactly one canonical scientific publication
    -> no replay verification

REPLAY completed
    -> exactly one replay verification
    -> no publication owned by the REPLAY execution
```

The B-2 migration and tests implement this amendment and are completed and
committed. Rich replay reconciliation/reporting remains a later concern;
the bounded verification fact required to make REPLAY persistence coherent is
part of 0021.

This is MODEL A, the verification model. MODEL B (new result/trace relational
occurrences sharing old canonical artifacts) is rejected because it turns an
operational verification into duplicate scientific ownership and requires
removing otherwise valid publication uniqueness. MODEL C (new canonical output
artifacts) is rejected because identical deterministic bytes must reuse the 0019
content identity; different bytes are a mismatch to record, not a successful
new REPLAY publication.

The REPLAY identity continues to use the exact semantic-identity payload above:
`execution_mode = REPLAY` and the non-null
`comparison_semantic_execution_digest` identify the historical execution being
verified. Mode plus comparison digest prevents collision with its original
NORMAL execution. The exact output authority is that comparison execution's
unique canonical publication, referenced by
`comparison_publication_id` from the verification row.

## Semantic execution identity

```text
protocol_digest
+ evidence_snapshot_digest
+ input_digest
+ execution_mode
+ configuration_digest
+ comparison_semantic_execution_digest or null
    -> scientific_evaluation_execution_identity/1 content digest
    = semantic_execution_digest
```

Required identity artifact:

```text
artifact_kind: scientific_evaluation_execution_identity
schema_version: 1
canonicalization_version: wye-c14n-json-v1
digest_algorithm: sha256
```

Exact payload:

```json
{
  "artifact_type": "scientific_evaluation_execution_identity",
  "comparison_semantic_execution_digest": null,
  "configuration_digest": "<64 lowercase hex>",
  "evidence_snapshot_digest": "<64 lowercase hex>",
  "execution_mode": "NORMAL",
  "input_digest": "<64 lowercase hex>",
  "protocol_digest": "<64 lowercase hex>",
  "schema_version": "1"
}
```

The artifact content digest is the only `semantic_execution_digest`; there is
no competing tuple hash. Runtime timestamps, request keys, DB IDs, attempts,
workers, concrete builds and errors are excluded.

## Execution versus attempt

```text
semantic execution = one canonical deterministic operation identity
execution attempt   = one operational effort to compute/publish it
```

One execution owns zero or more attempts. Failure or abandonment does not alter
semantic identity. Retry creates a new attempt and never overwrites a closed
one. Request occurrence/idempotency is a third, operational identity.

## Modes and comparison rules

The persisted v1 vocabulary is exactly `NORMAL`, `REPLAY`, `COUNTERFACTUAL`,
`REFRESH`.

| Mode | Comparison | Root rule | Protocol lifecycle at request |
|---|---|---|---|
| `NORMAL` | null | current governed roots | `published` only |
| `REPLAY` | required | same protocol, snapshot, input and configuration as comparison | historically published; current `published`, `deprecated` or `retired` |
| `COUNTERFACTUAL` | required | same snapshot/input; protocol or configuration differs | historically published; current `published`, `deprecated` or `retired`; governed authorization required |
| `REFRESH` | required | same target scope; snapshot or input differs | `published` only |

Mode participates in semantic identity. Comparison is lineage, not
supersession. `REPRODUCE` and `RECALCULATE` remain operation names.

## Configuration and engine identities

V1 requires:

```text
scientific_evaluation_configuration / 1
```

with exact payload boundary:

```json
{
  "artifact_type": "scientific_evaluation_configuration",
  "canonicalization_profiles": ["wye-c14n-json-v1"],
  "engine_contract": {
    "engine_key": "<stable machine key>",
    "semantic_compatibility_version": "<nonblank version>"
  },
  "schema_version": "1",
  "semantic_parameters": []
}
```

`semantic_parameters` is exactly empty in v1. Scientific thresholds, weights,
formulas and hidden knobs are forbidden. Technical limits are operational.

Every attempt references `scientific_evaluation_engine_build/1`, whose payload
freezes engine key, semantic compatibility version, source revision, source-tree
SHA-256, dependency-lock SHA-256, build SHA-256, canonicalization
implementation version and optional OCI image digest. It excludes runtime time,
worker and secrets. Engine key/compatibility must equal the configuration.

The concrete build is not in semantic identity. Builds claiming the same
semantic contract must produce identical canonical output. In REPLAY, different
output is persisted as a `mismatch` verification; in canonical-publication
modes it is an integrity failure. It is never a second result for the same
semantic execution.

## Primary references and target model

Every execution uses `ON DELETE RESTRICT` references to:

- protocol version and 32-byte digest;
- sealed evidence snapshot and 32-byte digest;
- `scientific_evaluation_target/1` artifact;
- `scientific_mapping_state_manifest/1` for ingredient, null for substance;
- `scientific_evaluation_input/1` and `input_digest`;
- configuration artifact/digest;
- execution-identity artifact/semantic digest.

The target artifact is historical authority. Operational traversal uses
concrete nullable `substance_id` and `ingredient_id` FKs rather than an
unconstrained polymorphic row ID. Exactly one is non-null and agrees with
`target_type`; these FKs are excluded from digests.

Deferred DB validation checks artifact kind/schema/digest, target/mapping/input
consistency, protocol digest, sealed snapshot/digest, comparison-mode rules and
verified locations. Services reconstruct canonical payloads; the DB protects
the immutable graph.

## Table model

0021 creates exactly:

```text
scientific_evaluation_executions
scientific_evaluation_execution_attempts
scientific_evidence_selection_decisions
scientific_evaluation_results
scientific_evaluation_result_components
scientific_evaluation_traces
scientific_evaluation_publications
scientific_evaluation_replay_verifications
scientific_evaluation_idempotency_keys
```

It alters `scientific_evaluation_governance_events`. It creates no generic
execution-artifact link, query projection, rich replay-report/reconciliation or
domain-result table.
Fixed publication roots use explicit FKs; intermediates are reachable through
result components and trace. Projection and richer replay-report persistence
remain 0022.

## Executions

`scientific_evaluation_executions` columns:

| Column | Frozen type/rule |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `execution_key` | `UUID NOT NULL UNIQUE` |
| `protocol_version_id` | `BIGINT NOT NULL` FK RESTRICT |
| `evidence_snapshot_id` | `BIGINT NOT NULL` FK RESTRICT |
| `target_type` | `VARCHAR(20)`, `substance` or `ingredient` |
| `substance_id`, `ingredient_id` | concrete nullable FKs RESTRICT; exact-one shape |
| `target_artifact_id` | artifact FK RESTRICT |
| `mapping_state_artifact_id` | nullable artifact FK; ingredient only |
| `input_artifact_id` | artifact FK RESTRICT |
| `configuration_artifact_id` | artifact FK RESTRICT |
| `semantic_identity_artifact_id` | artifact FK RESTRICT, UNIQUE |
| `comparison_execution_id` | nullable self-FK RESTRICT |
| `execution_mode` | closed mode CHECK |
| `protocol_digest`, `evidence_snapshot_digest`, `input_digest`, `configuration_digest` | 32-byte cached linkage proofs |
| `semantic_execution_digest` | `BYTEA(32 semantics) NOT NULL UNIQUE` |
| `technical_status` | closed execution status |
| `requested_by` | nonblank actor |
| `requested_at`, `created_at` | `TIMESTAMPTZ NOT NULL` |
| `started_at`, `completed_at` | nullable state-consistent `TIMESTAMPTZ` |

Target shape:

```text
substance -> substance_id set; ingredient_id and mapping artifact null
ingredient -> ingredient_id and mapping artifact set; substance_id null
```

Digest columns equal their referenced immutable rows/artifacts.

Execution lifecycle:

```text
pending -> running -> completed
pending -> cancelled
running -> pending       after retryable failed/abandoned attempt
running -> failed
running -> cancelled
failed  -> running       only with a new running retry attempt
```

`completed` and `cancelled` are terminal. `failed -> running` is an explicit
retry; attempts preserve failure history. For `NORMAL`, `REFRESH` and
`COUNTERFACTUAL`, completion is allowed only in the transaction inserting a
publication and marking its attempt `succeeded`. For `REPLAY`, completion is
allowed only in the transaction inserting a replay verification and marking
its attempt `succeeded`; that execution must own no publication.
Execution roots are immutable from INSERT and executions reject DELETE.

## Attempts and recovery

`scientific_evaluation_execution_attempts` columns:

| Column | Frozen type/rule |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `attempt_key` | `UUID NOT NULL UNIQUE` |
| `execution_id`, `attempt_number` | FK RESTRICT plus positive integer; UNIQUE pair |
| `attempt_status` | `running`, `succeeded`, `failed`, `cancelled`, `abandoned` |
| `engine_build_artifact_id` | artifact FK RESTRICT |
| `worker_id` | nullable sanitized identifier |
| `lease_token`, `lease_expires_at`, `heartbeat_at` | required while running |
| `started_at` | `TIMESTAMPTZ NOT NULL` |
| `ended_at` | required for terminal status |
| `error_category`, `error_code`, `retryable` | state-consistent technical fields |
| `error_artifact_id` | nullable FK to `scientific_evaluation_attempt_error/1` |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` |

The optional error artifact contains only stable category/code, bounded
sanitized detail and technical references. It excludes secrets, prompts,
private raw input, environment dumps and stack locals.

A partial UNIQUE permits at most one running attempt per execution. Identity,
start and build fields never update. While running, only lease/heartbeat and one
terminal transition are allowed. Terminal attempts are immutable; DELETE is
forbidden. An interrupted attempt remains running until a later recovery service
locks it, proves lease expiry and marks it abandoned. 0021 implements no worker.

## Selection persistence

`scientific_evidence_selection_decisions` contains:

- `id BIGSERIAL PRIMARY KEY`;
- execution and snapshot-member FKs RESTRICT;
- `decision` CHECK `included, excluded`;
- `selection_role` CHECK `contributing, context_only, none`;
- `resolution_state` CHECK `resolved, deferred`;
- nonblank reason namespace/version/primary code;
- decision artifact FK and equal 32-byte digest;
- `created_at`.

UNIQUE `(execution_id, snapshot_member_id)`. Deferred validation proves the
member belongs to the execution snapshot. Canonical-publication modes require
exact coverage of every member. REPLAY computes selection transiently and does
not insert new selection-decision rows. Rows are insert-only and use
`scientific_evidence_selection_decision/1`. The canonically ordered set uses
`scientific_evidence_selection_manifest/1`; its digest is `selection_digest`.
Scientific selection runtime remains absent.

## Results and components

`scientific_evaluation_results` contains `id BIGSERIAL`, UUID `result_key`,
UNIQUE execution FK, nonblank result kind/schema, versioned scientific-status
namespace/version/code, UNIQUE canonical artifact FK, equal 32-byte digest and
created time. Contract:

```text
scientific_evaluation_result / 1
```

It binds semantic execution, result kind/schema, scientific status and ordered
component descriptors. It excludes trace to prevent a digest cycle. Scientific
status is not technical status and is protocol-versioned, not a DB-closed
vocabulary. A completed execution may validly report insufficient evidence,
conflict, `risk_not_computable`, exposure unknown or another non-numeric state.

`scientific_evaluation_result_components` contains result FK, component
kind/schema/role, component artifact/equal digest, nonnegative ordinal and time.
UNIQUE `(result_id, ordinal)` and scoped role/kind/digest. Contract:

```text
scientific_evaluation_result_component / 1
```

It freezes a generic envelope, scope, versioned scientific status and payload.
The payload schema is owned by its reviewed component kind/version. 0021 defines
no score field or numerical semantics. Result/component rows are immutable.

## Trace and explainability

`scientific_evaluation_traces` contains BIGSERIAL/UUID identities, UNIQUE
execution and result FKs, trace schema version, UNIQUE canonical artifact FK,
32-byte trace/result/selection/protocol/snapshot/input digests and created time.
Contract:

```text
scientific_evaluation_trace / 1
```

The trace is a canonical machine DAG binding candidates, decisions, rules,
intermediate artifact references, components and causal edges. It may include
result digest; result excludes trace digest. AI prose/UI layout are excluded.
Intermediates need no generic 0021 link because trace/components preserve their
reachability. The trace row is immutable. A REPLAY execution does not own a
trace row; its recomputed canonical trace root is recorded by the replay
verification.

## Atomic publication

`scientific_evaluation_publications` contains BIGSERIAL/UUID identities; UNIQUE
execution, result, trace and successful-attempt FKs; UNIQUE selection-manifest
and bundle artifact FKs; 32-byte selection/result/trace/bundle digests;
nonblank publisher; publication/creation times.

Bundle contract:

```text
scientific_evaluation_publication_bundle / 1

semantic_execution_digest
+ selection_digest
+ result_digest
+ trace_digest
    -> publication_bundle_digest
```

The payload repeats protocol, snapshot, input and configuration digests as
checked proofs. It excludes time, attempt/build metadata and projections.
Deferred validation requires verified root locations, exact decision coverage,
matching result/trace roots, a succeeded attempt and execution completion in
the same transaction. Publications reject `REPLAY` ownership.

Publication means canonical reachability, not automatic API visibility or
scientific endorsement. Review/current disposition is governance-derived.
Partial output is never canonical. All publication-owned rows are immutable.

## Replay verification

`scientific_evaluation_replay_verifications` is the append-only technical proof
that a REPLAY execution reproduced, or failed to reproduce, an exact historical
publication. It contains:

| Column | Frozen type/rule |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `verification_key` | application UUID, `NOT NULL UNIQUE` |
| `execution_id` | REPLAY execution FK RESTRICT, `NOT NULL UNIQUE` |
| `comparison_publication_id` | historical publication FK RESTRICT |
| `successful_attempt_id` | succeeded attempt FK RESTRICT, `NOT NULL UNIQUE` |
| `verification_artifact_id` | artifact FK RESTRICT, `NOT NULL UNIQUE` |
| `verification_digest` | equal 32-byte artifact digest |
| `expected_publication_bundle_digest` | comparison bundle digest, 32 bytes |
| `expected_selection_digest`, `expected_result_digest`, `expected_trace_digest` | comparison roots, 32 bytes |
| `recomputed_selection_artifact_id`, `recomputed_result_artifact_id`, `recomputed_trace_artifact_id` | artifact FKs RESTRICT; deliberately not UNIQUE |
| `recomputed_selection_digest`, `recomputed_result_digest`, `recomputed_trace_digest` | equal artifact digests, 32 bytes |
| `verification_status` | `matched` or `mismatch` |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` |

The verification artifact contract is:

```text
scientific_evaluation_replay_verification / 1
```

Exact canonical payload boundary:

```json
{
  "artifact_type": "scientific_evaluation_replay_verification",
  "comparison_publication_bundle_digest": "<64 lowercase hex>",
  "comparison_semantic_execution_digest": "<64 lowercase hex>",
  "expected_roots": {
    "result_digest": "<64 lowercase hex>",
    "selection_digest": "<64 lowercase hex>",
    "trace_digest": "<64 lowercase hex>"
  },
  "recomputed_roots": {
    "result_digest": "<64 lowercase hex>",
    "selection_digest": "<64 lowercase hex>",
    "trace_digest": "<64 lowercase hex>"
  },
  "replay_semantic_execution_digest": "<64 lowercase hex>",
  "root_matches": {
    "result": true,
    "selection": true,
    "trace": true
  },
  "schema_version": "1",
  "verification_status": "matched"
}
```

It excludes timestamps, DB/attempt/build/worker IDs, secrets and free-form
diagnostics. `matched` requires all three roots equal; `mismatch` requires at
least one unequal root.

Recomputed output artifacts are globally content-addressed but are not owned by
new scientific result/trace/publication rows. A match therefore resolves the
same global selection/result/trace artifact rows already referenced by the
historical publication. A mismatch may preserve new canonical artifacts for
diagnosis without promoting them to scientific output. V1 adds no separate
diagnostic artifact; runtime failures use the existing attempt-error artifact.

Deferred validation reloads final rows and proves: the execution is REPLAY; its
comparison execution owns the comparison publication; the successful attempt
belongs to the execution and is `succeeded`; expected roots equal that
publication; recomputed artifact kind/schema/digest and verified locations are
valid; status agrees with root equality; and verification, successful attempt
and completed execution become valid in the same transaction. The verification
row is INSERT-only and rejects UPDATE and DELETE.

## Idempotency and concurrency

`semantic_execution_digest` is globally UNIQUE: identical semantic requests
converge on one execution. Audit occurrences and retries use request keys and
attempts rather than duplicate scientific rows.

`scientific_evaluation_idempotency_keys` is operational. It stores nonblank
operation type/scope/key, expected semantic digest, nullable resolved
execution/attempt/publication FKs, creation and expiry times, with UNIQUE
`(operation_type, request_scope, request_key)`. It never enters a digest and may
expire under operational policy. REPLAY resolution needs no additional nullable
column: the resolved execution's UNIQUE verification is loaded by execution ID.

Concurrency rules:

1. Concurrent identical execution inserts elect one semantic row; a loser
   verifies every referenced root before reuse.
2. A partial UNIQUE permits one running attempt per execution.
3. Execution row locking serializes attempt start, terminal transition and
   mode-appropriate publication or replay verification.
4. Publication uniqueness elects one bundle. Reuse requires all roots and
   authoritative bytes to match.
5. Replay verification uniqueness elects one immutable proof per REPLAY
   execution; recomputed artifacts intentionally permit global reuse.
6. Incompatible roots/build claims fail explicitly; no UUID is reassigned and
   no immutable row is rewritten.

The DB is final authority. Advisory locks may reduce work, never provide
correctness.

Repeated requests for the same REPLAY semantic digest converge on one execution
and, after completion, its one verification. Operational retries append
attempts. Different semantic configuration or comparison identity creates a
different semantic execution; verification rows are never superseded or
rewritten. Different concrete builds claiming the same semantic compatibility
may create attempts under the same execution, and the successful build remains
preserved through `successful_attempt_id` without entering semantic identity.

## Technical failure versus scientific status

Technical state belongs to execution/attempt; scientific state belongs to the
canonical result:

```text
attempt failed                 -> no canonical result or replay verification
NORMAL/REFRESH/COUNTERFACTUAL completed -> publication exists
REPLAY completed               -> replay verification exists; no own publication
completed + insufficient data  -> valid non-numeric scientific result
```

Closed v1 technical error categories are:

```text
validation
artifact_integrity
engine_incompatible
canonicalization
database
resource
cancelled
unexpected
```

Stable `error_code` refines the category. Details are sanitized and never
scientific output.

## Immutability and lineage

- Execution semantic roots are immutable immediately; technical status follows
  only the frozen graph.
- Active attempts permit lease/heartbeat and one terminal closure; closed rows
  are immutable and all attempts reject DELETE.
- Decisions, results, components, traces, publications and replay verifications
  are insert-only.
- Changed evidence, input, protocol or semantic engine contract creates a
  different execution identity.
- Comparison lineage is not currentness or supersession.
- Supersession, retraction and integrity disposition are append-only governance.

No canonical/history FK uses `CASCADE` or `SET NULL`.

## Governance extension

0021 adds concrete RESTRICT FKs:

```text
execution_id
related_execution_id
result_id
related_result_id
```

The exactly-one governed-entity CHECK adds:

```text
evaluation_execution
evaluation_result
```

Related references remain zero-or-one and same-type. Self-reference and cycles
are rejected by the extended lineage validator. The event vocabulary adds only
`counterfactual_authorized`; existing `supersedes`, `retracts`,
`integrity_compromised`, `annotation` and `review_disposition` apply to
executions/results.

For `supersedes`, the primary entity is the successor and related entity is the
predecessor. Counterfactual creation requires a valid authorization event for
the new execution, checked by a deferred trigger. Attempts are operational and
publication is governed through execution/result, so neither becomes a new
governed entity type.

Replay verification likewise adds no governance entity columns. A mismatch is
an immutable factual observation. A later governance event may annotate the
REPLAY execution or mark integrity concerns, but no automatic supersession,
retraction or scientific disposition follows from insertion.

## Result publication boundary

0021 has no mutable result-lifecycle column. A result is inserted atomically
with canonical publication. Scientific status is content, not publication
state. Canonical publication does not imply user visibility, external
validation or endorsement. Phase 7.7 governance determines claims/visibility
without editing the result.

No `current_result` flag exists. Current state is derived from immutable
executions/publications and governance events as of a requested time.

## Replay, refresh and counterfactual persistence

- `REPLAY` reuses historical protocol/snapshot/input/configuration roots and
  verifies the exact comparison publication. A successful computation persists
  `matched` or `mismatch`; mismatch is a completed technical verification, not
  an execution failure or new scientific result.
- `REFRESH` requires changed snapshot or input and creates a new immutable
  publication.
- `COUNTERFACTUAL` holds snapshot/input fixed, changes protocol/configuration
  under governed authorization and never supersedes automatically.
- `NORMAL` creates or reuses the requested identity under a published protocol.

Matching REPLAY selection decisions, result components and trace structure are
transient canonical computations: only their recomputed artifacts/digests and
the verification fact are persisted. Rich reports and reconciliation workflows
remain 0022.

## Keys, timestamps and representation

- `BIGSERIAL` internal PKs and `BIGINT` FKs.
- Application-generated UUID keys for execution, attempt, result, trace,
  publication and replay verification; no UUID DB extension.
- SHA-256 as exactly 32-byte `BYTEA`; document form lowercase 64-char hex.
- `VARCHAR` plus named CHECK, never PostgreSQL ENUM.
- Operational time as `TIMESTAMPTZ`.
- Semantic `input_as_of` stays inside the input artifact; `requested_at` never
  replaces it.
- Canonical tables need no JSONB. Artifact JSONB remains a verified cache.

Time checks include start not before request, terminal end not before start,
lease expiry after heartbeat while running, and publication/completion
consistent with the successful attempt.

## UNIQUE and CHECK constraints

Mandatory uniqueness:

- execution key, semantic digest and semantic-identity artifact;
- attempt key and `(execution_id, attempt_number)`;
- partial one running attempt per execution;
- decision `(execution_id, snapshot_member_id)`;
- result key, execution and canonical artifact;
- component `(result_id, ordinal)` and scoped role/kind/digest;
- trace key, execution, result and canonical artifact;
- publication key, execution, result, trace, successful attempt, selection
  manifest and bundle artifact;
- replay verification key, execution, successful attempt and verification
  artifact;
- idempotency `(operation_type, request_scope, request_key)`.

Named CHECKs cover target/mapping shape, modes/comparison, 32-byte digests,
nonblank keys/actors/schema identifiers, state/timestamps, error fields,
positive attempt number, nonnegative component ordinal,
decision/role/resolution vocabularies and idempotency shape.

Cross-row/root consistency uses deferred constraint triggers so statement order
inside the atomic transaction cannot bypass validation.

## Indexes

Do not duplicate UNIQUE indexes. Add only:

- executions by concrete target/request time;
- executions `(protocol_version_id, technical_status, created_at)`;
- execution snapshot and non-null comparison;
- attempts `(execution_id, attempt_number DESC)`;
- partial running-attempt lease expiry;
- decisions `(execution_id, decision, resolution_state, primary_reason_code)`
  and snapshot member;
- components `(result_id, component_kind, component_ordinal)`;
- publications `(published_at DESC, id DESC)`;
- replay verifications by comparison publication and
  `(verification_status, created_at DESC, id DESC)`;
- governance primary/related execution/result indexes;
- idempotency expiry for operational cleanup.

No JSONB GIN or domain-projection index belongs to 0021.

## Delete and downgrade policy

Every canonical/history FK is `ON DELETE RESTRICT`. Execution, attempt,
decision, result, component, trace, publication, replay verification and
governance rows reject DELETE. Only expired operational idempotency rows may be
deleted by policy.

Downgrade `0021 -> 0020` is allowed only when all nine new tables are empty and
no governance event references execution/result. Pending, running, failed,
cancelled and unpublished rows all count as history. Otherwise a preflight
raises before destructive DDL. Safe downgrade restores exactly the 0020
governance columns, checks, lineage function and indexes. Compatible 0019
artifacts may remain.

## Migration preflight

Before the first mutating DDL, 0021 verifies:

1. expected 0019/0020 tables, columns, constraints, triggers and functions;
2. absence of every new table/index/constraint/trigger/function name, including
   replay-verification objects;
3. absence of execution/result governance columns and incompatible vocabulary;
4. Alembic version-column capacity;
5. no partial prior installation.

Any mismatch aborts before foundation creation; no unknown schema is adapted.

## Required artifact contracts

Already frozen: protocol definition/review; evidence snapshot query/member/
manifest; target; mapping member/manifest; evaluation input.

Newly frozen here:

```text
scientific_evaluation_configuration / 1
scientific_evaluation_execution_identity / 1
scientific_evaluation_engine_build / 1
scientific_evaluation_attempt_error / 1
scientific_evidence_selection_decision / 1
scientific_evidence_selection_manifest / 1
scientific_evaluation_result_component / 1
scientific_evaluation_result / 1
scientific_evaluation_trace / 1
scientific_evaluation_publication_bundle / 1
scientific_evaluation_replay_verification / 1
```

Generic result/component/trace envelopes are persistence-frozen; their
protocol-owned scientific vocabularies/rules remain review-gated. Runtime
allowlist changes are not migration DDL.

## Exact 0021 scope

```text
revision:      0021_scientific_evaluation_publication
down_revision: 0020_scientific_evidence_snapshots
```

CREATE the nine tables listed above. ALTER governance with execution/result
primary and related FKs, exact-one/same-type/not-self CHECKs and
`counterfactual_authorized`.

Functions/triggers:

- execution immutable-root/state guard;
- deferred execution root/mode/protocol/snapshot/artifact validator;
- attempt state/terminal guard and deferred execution consistency;
- selection insert-only guard and deferred snapshot-membership validator;
- result/component/trace/publication immutability guards;
- replay-verification insert-only guard;
- deferred mode-specific atomic publication/root/coverage validator;
- deferred replay-verification/comparison/root validator;
- extended governance lineage validator;
- downgrade-history preflight.

The existing 0019 governance append-only trigger remains. Create only the
indexes frozen above.

Not in 0021: projections/current views, rich replay reports/reconciliation,
product composition/scenario, runtime engines, API/frontend or legacy
integration.

## Migration test plan

Future PostgreSQL tests cover:

1. fresh chain and 0020-to-0021 upgrade;
2. exact shape, PK/FK RESTRICT, CHECK, UNIQUE and indexes;
3. empty downgrade and refusal with any history;
4. artifact kind/schema/digest mismatch;
5. building snapshot rejection/sealed acceptance;
6. mode/comparison/protocol lifecycle matrix;
7. concurrent semantic execution uniqueness;
8. target concrete-FK/mapping applicability;
9. concurrent one-running-attempt rule;
10. one-way attempt closure and history;
11. execution state/terminal immutability;
12. selection member outside snapshot rejection;
13. complete decision coverage;
14. immutable result/component/trace/publication/replay verification;
15. publication root/unverified artifact/wrong attempt rejection;
16. same-transaction completion independent of statement order;
17. rollback leaves no canonical publication or replay verification;
18. governance authorization/supersession/cycle protection;
19. preflight collision with no partial install;
20. 0019/0020 and Phase 6 preservation;
21. matching REPLAY reuses global artifacts, completes with `matched`
    verification and creates no result/trace/publication/decision rows;
22. mismatched REPLAY records expected/recomputed roots, preserves the
    historical publication and technically completes;
23. REPLAY runtime error leaves a failed attempt and no verification;
24. REPLAY cannot complete without verification and canonical-publication modes
    cannot complete without publication;
25. concurrent/idempotent REPLAY elects one verification;
26. replay-verification downgrade/preflight/FK/immutability coverage;
27. legacy scoring isolation.

## Phase 7.6.4C runtime realization

The provider-neutral Phase 7.6.4C runtime realizes this persistence contract
without adding schema. Its tests cover fixed identity/configuration vectors;
root sensitivity; operational-field insensitivity; retry/concurrent convergence;
attempt history and heartbeat/lease primitives; failed attempt then retry; atomic
selection/result/trace/bundle publication; completed-result reuse after byte/root
verification; stale/building prerequisite rejection; REPLAY matched/mismatch/
error behavior and global artifact reuse without a new scientific publication;
COUNTERFACTUAL fail-closed authorization; REFRESH root change; valid non-numeric
insufficiency/conflict/not-computable output; historical preservation; offline
operation; and legacy isolation.

All canonical scientific outputs are supplied explicitly by the caller. This
runtime does not implement the scientific algorithms that produce them, nor a
background worker/recovery service.

## Legacy and scientific boundaries

0021 has no FK, view, digest, backfill, read or write dependency on
`product_scores`, `ingredient_risk_profiles`, `ingredient_evidence` or legacy
`scoring.py`. Product target remains excluded. No legacy score is an input or
fallback.

This freeze persists deterministic identity, attempts and future canonical
output envelopes only. It implements no evidence selection, synthesis,
hazard/risk/exposure calculation, ingredient projection, product assessment,
replay engine, formula, weight, threshold or numerical score.
