# WYE — Scientific Evaluation Execution Model

## Status and scope

This document is the Phase 7.1 logical architecture specification. It extends,
but does not replace, the semantic contracts in:

- `Checkpoints/WYE_PHASE_7.md`;
- `WYE_SCORING_SEMANTICS.md`;
- `WYE_SCORING_PROTOCOL.md`.

Phase 7.1 defines how a scientific evaluation is identified, frozen, executed,
audited and replayed. It does not define scientific eligibility criteria,
endpoint synthesis rules, hazard categories, formulas, weights, thresholds,
rankings, colours or a numerical score. It does not authorize persistence or
runtime implementation.

Repository review baseline:

```text
branch: ingredients_score
HEAD: f708b0aa7ab56a506a05ee2f51a8e1001379ca0a
origin/ingredients_score: f708b0aa7ab56a506a05ee2f51a8e1001379ca0a
working tree before Phase 7.1: clean
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017
```

The migrations from `0001` through `0018`, the current ingestion contracts,
canonicalization helpers, scientific persistence repositories and temporal
ingredient-to-substance mapping services were reviewed before defining this
model. No technical contradiction with the Phase 7.0.1 contracts was found.

## Frozen premises

```text
scientific evidence != scientific scoring
hazard != exposure != risk
absence of evidence != evidence of danger
AI != scientific source of truth

endpoint-specific evidence synthesis
+ multidimensional substance hazard profile
= first implementable domain

quantitative product risk
= not implementable with current data

published protocol versions are immutable
historical results are immutable
replay != counterfactual != refresh
no numerical score justified for the first protocol
```

## Naming decision

`scoring_execution` is too narrow because the first protocol produces a
non-scalar scientific synthesis and future protocols may or may not produce
numeric components. The canonical logical execution name is therefore:

```text
scientific_evaluation_execution
```

The Phase 7 programme keeps the established “Scientific Scoring” name. The
following Phase 7.0.1 placeholders are specialized without changing their
meaning:

| Phase 7.0.1 placeholder | Phase 7.1 canonical logical name |
|---|---|
| `scoring_protocol` | `scientific_protocol` |
| `scoring_protocol_version` | `scientific_protocol_version` |
| `scoring_execution` | `scientific_evaluation_execution` |
| `scoring_result_component` | `result_component` |
| `scoring_explanation_trace` | `explanation_trace` |

These are logical entity names, not approved database table names.

## Logical entity catalogue

### `scientific_protocol`

A protocol is the stable semantic family of evaluations. It answers why and
for which claim domain evaluations exist; it does not contain mutable executable
rules.

Minimum contract:

| Field | Meaning |
|---|---|
| `protocol_key` | Stable, machine-readable family identity |
| `title` | Human-readable name |
| `protocol_domain` | Scientific domain and construct |
| `scientific_question` | Question the protocol is designed to answer |
| `intended_use` | Permitted decision-support context |
| `supported_claims` | Explicit claim classes the protocol may support |
| `excluded_claims` | Explicitly forbidden interpretations |
| `target_entity_type` | Substance, ingredient, product or future entity type |
| `target_context` | Population, route, use or other applicable context |
| `lifecycle_status` | Family-level administrative lifecycle |
| `governance_owner` | Accountable governance role or body |
| `created_at` | Audit metadata; not semantic rule content |

One protocol owns many immutable protocol versions. Changing its intended use,
scientific construct or target type beyond backward-compatible clarification
requires a new protocol family, not a silent version edit.

### `scientific_protocol_version`

A protocol version is the immutable, executable semantic specification of one
protocol family.

Minimum contract:

| Field | Meaning |
|---|---|
| `protocol_version_key` | Stable version identity |
| `protocol_key` | Parent protocol |
| `semantic_version` | Governed version number |
| `status` | Lifecycle state |
| `scientific_specification` | Canonical scientific questions and output contract |
| `eligibility_policy_version` | Exact eligibility policy reference |
| `conflict_policy_version` | Exact conflict policy reference |
| `aggregation_policy_version` | Exact aggregation/projection policy reference |
| `missing_evidence_policy` | Explicit non-penalizing missing-data semantics |
| `uncertainty_framework` | Versioned dimensions and allowed states |
| `canonical_rule_representation` | Machine-readable semantic rule artifact |
| `canonicalization_version` | Serialization contract used for the rule artifact |
| `canonical_digest` | Digest of effective semantic content |
| `effective_date` | Governed date from which new normal executions may use it |
| `publication_date` | Publication audit date |
| `superseded_by` | Optional forward reference; does not rewrite history |
| `change_rationale` | Why this version differs from its predecessor |
| `review_metadata` | Scientific, data, engineering and governance review record |

Lifecycle:

```text
draft
→ scientific_review
→ approved
→ published
→ deprecated
→ retired
```

Only `published` versions may initiate normal production evaluations. A
deprecated version remains available for governed replay and historical review.
A retired version cannot initiate a new normal evaluation, but remains usable
for exact replay where policy permits. Publication freezes all semantic fields,
policy references, canonical representation and digest. A correction always
creates a new version. Supersession, deprecation, retirement and retraction are
append-only governance events around the immutable version.

### Canonical rule representation

Phase 7.1 selects conceptually:

```text
versioned canonical JSON + SHA-256
```

No new dependency is required at this stage. A future implementation may use
the standard-library JSON and cryptographic primitives already used by the
Phase 6 canonicalization layer, provided a dedicated protocol canonicalization
version is introduced.

The representation MUST define:

- stable lexicographic object-key ordering;
- preserved array order only where order is semantically meaningful;
- explicit canonical sorting keys for set-like collections;
- UTF-8 encoding and normalization requirements;
- no insignificant whitespace;
- explicit `null` meaning, distinct from absent or unknown;
- explicit units and unit-system version references;
- explicit enum values and enum-vocabulary versions;
- exact policy and ontology version references;
- deterministic numeric lexical representation if a future protocol needs it;
- rejection of non-finite numeric values;
- a canonicalization format/version identifier;
- lowercase SHA-256 output.

The digest includes effective rules, policy references, declared claims,
scientific questions, target semantics, uncertainty and missing-evidence
semantics. It excludes Markdown formatting, comments with no normative meaning,
localized display text, database surrogate IDs, publication timestamps, review
signatures and arbitrary property insertion order.

Semantically meaningful prose cannot be left only in Markdown: it must be
represented by a stable rule or declaration identifier in canonical content.
Phase 7.2 defines the eligibility and selection contract in
`WYE_EVIDENCE_SELECTION.md`; Phase 7.3 defines the evidence-line, endpoint
synthesis and substance-profile contract in `WYE_EVIDENCE_SYNTHESIS.md`;
Phase 7.4 defines the mapping-snapshot and ingredient-projection contract in
`WYE_INGREDIENT_PROJECTION.md`; Phase 7.5 defines the product-composition,
exposure-scenario, readiness and product-assessment contract in
`WYE_PRODUCT_ASSESSMENT.md`.

### `evidence_snapshot`

An evidence snapshot is the immutable universe of scientific and identity data
that was available and eligible to be considered by an execution. It is not the
subset eventually selected for a conclusion.

Minimum header contract:

| Field | Meaning |
|---|---|
| `snapshot_key` | Stable snapshot identity |
| `snapshot_schema_version` | Snapshot document contract |
| `as_of` | Historical database/identity viewpoint |
| `evidence_cutoff` | Latest admissible scientific publication/release time |
| `query_definition` | Canonical deterministic universe definition |
| `query_definition_version` | Version of query semantics |
| `snapshot_policy_version` | Technical availability/status/cutoff semantics used to form the universe |
| `resolved_membership_count` | Audit count by member type |
| `mapping_state_digest` | Frozen target/mapping state digest |
| `identity_state_digest` | Frozen substance identity-state digest |
| `snapshot_digest` | Digest of header semantics and resolved membership |
| `created_at` | Audit time; excluded from semantic digest |

The snapshot policy freezes technical availability, provenance, status and
cutoff semantics. Scientific relevance and endpoint eligibility remain protocol
selection decisions; otherwise a counterfactual could not apply a different
protocol to the same historical candidate universe. The snapshot resolves at
least:

- sources, datasets, releases and release artifacts;
- successful ingestion runs and exact artifact membership;
- assessments and findings visible under cutoff and status rules;
- substance identities and identifier namespace versions;
- ingredient-to-substance mapping state when relevant;
- parser, acquisition, adapter and normalization versions;
- relevant review decisions and materializations;
- explicit unresolved identity candidates relevant to the target.

#### Snapshot universe versus selected evidence

```text
snapshot universe
= every candidate record frozen before scientific selection

selected evidence
= members included after one recorded selection decision per candidate
```

A record can be in the snapshot and excluded by the selection policy. A record
outside the snapshot cannot be selected. `no_eligible_evidence` is determined
after the candidate universe and selection decisions are known; it is not an
empty or failed snapshot by definition.

#### Snapshot representation decision

The selected model is hybrid:

```text
canonical deterministic query definition
+ resolved materialized membership
+ frozen semantic identity/content descriptors
```

The query definition explains why the universe has its boundaries. Materialized
membership proves exactly which rows and artifacts were present. Frozen
descriptors and content fingerprints protect replay from later mutable row
state, deletion, correction, reassignment or mapping changes.

A membership item therefore contains, at minimum:

| Field | Meaning |
|---|---|
| `member_type` | Release, artifact, run, assessment, finding, mapping or identity member |
| `logical_key` | Stable domain identity, not only a surrogate row ID |
| `database_reference` | Optional traversal reference to the Phase 6 row |
| `content_digest` | Digest of the member's semantic payload |
| `semantic_payload` or `artifact_reference` | Frozen content or immutable content-addressed location |
| `validity/status_as_of` | Status and temporal state used by the execution |
| `parent_membership_key` | Deterministic provenance/dependency edge |
| `membership_ordinal` | Canonical order where scientifically meaningful |

Foreign keys alone are insufficient because future changes may alter or remove
the referenced semantic state. Copying every raw byte into the snapshot is also
unnecessary where an immutable, checksummed artifact is retained. The hybrid
model stores normalized semantic membership and points to content-addressed raw
artifacts for proof and reprocessing.

### `target_identity_snapshot`

This immutable object freezes what was evaluated, independently of future
changes to canonical names, identifiers, mappings or composition.

Common contract:

- `target_type`;
- `target_logical_key` and optional current database reference;
- canonical identity payload and identity digest;
- target status as of the snapshot;
- all relevant external identifiers with namespace/version and verification
  state;
- mapping/composition state references and digests;
- source and provenance references;
- unresolved or ambiguous identity state, when present.

For a substance, the payload freezes the substance ID, preferred and normalized
names, type/status and the relevant identifier set. For an ingredient, it also
freezes the ingredient identity and accepted temporal ingredient-to-substance
relationships. For a future product evaluation, it freezes product identity,
the exact extracted label/composition state, product-ingredient materialization
and downstream mapping state.

The Phase 6 temporal `ingredient_substances` history, proposals, decisions,
materializations and closures can reconstruct accepted mappings by an `as_of`
date. A snapshot still records the resolved rows and their semantic payload so
replay does not depend on later corrections or on date-boundary interpretation.
`product_ingredients`, product identity and substance identity do not currently
have equivalent complete temporal snapshots; this is a Phase 7 persistence
requirement before those targets can be replay-safe.

### `evidence_selection_decision`

This is the immutable, execution-scoped contract that a future selection engine
must produce for every candidate evidence line. An assessment
may also receive a parent decision when assessment-level policy makes all of its
findings ineligible.

Minimum contract:

| Field | Meaning |
|---|---|
| `decision_key` | Stable identity within the execution |
| `execution_key` | Owning execution |
| `snapshot_member_key` | Candidate finding/assessment in the snapshot |
| `decision` | `included` or `excluded` |
| `reason_code` | Machine-readable deterministic primary reason |
| `secondary_reason_codes` | Optional ordered additional reasons |
| `protocol_version_key` | Exact deciding version |
| `rule_reference` | Canonical rule identifier |
| `target_scientific_question` | Endpoint/question to which the decision applies |
| `relevance_dimensions` | Frozen structured relevance assessment |
| `dependency_decision_keys` | Duplicate/dependency/parent decision references |
| `decision_trace` | Deterministic inputs and transformation steps |

Reason codes are versioned machine keys, not free text. Human explanations may
be attached as non-canonical display content. Concrete reason-code vocabularies,
relevance dimensions and their review boundaries are defined by Phase 7.2 in
`WYE_EVIDENCE_SELECTION.md`.

### `scientific_evaluation_execution`

An execution is one immutable application of a governed protocol version to a
frozen target identity, independent evidence snapshot and, where applicable,
frozen mapping/domain-input roots.

Minimum contract:

| Field | Meaning |
|---|---|
| `execution_key` | Stable execution identity |
| `protocol_version_key` and `protocol_digest` | Exact effective rules |
| `snapshot_key` and `snapshot_digest` | Exact evidence universe |
| `target_identity_snapshot_key` | Exact evaluated target state |
| `execution_type` | `NORMAL`, `REPLAY`, `COUNTERFACTUAL` or `REFRESH` |
| `comparison_execution_key` | Required where a mode compares with history |
| `as_of` | Evaluation viewpoint, coherent with snapshot |
| `engine_name`, `engine_build_version` | Deterministic implementation identity |
| `semantic_engine_compatibility_version` | Declared behavioral contract |
| `configuration` and `configuration_digest` | Canonical semantic configuration |
| `canonical_input_digest` | Target and non-protocol, non-evidence domain inputs |
| `semantic_execution_key` | Derived idempotency identity |
| `status` | Technical lifecycle state |
| `created_at`, `started_at`, `completed_at` | Audit timestamps |

Execution timestamps, generated IDs, worker identity and retry count do not
alter semantic inputs. If an engine change can alter semantic output, it is not
merely a build change: the relevant protocol, canonicalization or engine
compatibility version must change.

### Execution types

#### `NORMAL`

The first governed evaluation of a target according to the chosen published
protocol version and newly resolved snapshot. It has no required comparison
execution. Equivalent concurrent requests may resolve to one semantic execution
with separate technical attempts.

#### `REPLAY`

```text
same historical target identity
+ same mapping state
+ same evidence snapshot
+ same protocol version
+ compatible deterministic engine
→ identical semantic result and digests
```

A replay references the historical execution being verified. It may have a new
execution/attempt ID and timestamps, but must reuse the historical semantic
inputs and must not resolve any “current” row. The 7.6.4B-1B persistence
amendment makes this a verification of the historical canonical publication:
matching output records `matched`; differing output records `mismatch`. Neither
case creates a new scientific result, trace, selection-decision set or
publication. A mismatch is an integrity finding, not a new scientific result
and not a technical execution failure when computation itself completed.

#### `COUNTERFACTUAL`

```text
same historical target identity
+ same historical evidence snapshot
+ different protocol version
→ new immutable result measuring rule impact
```

The counterfactual references the baseline execution, preserves its target and
snapshot, and records the changed protocol/rule digest. It never supersedes the
baseline result. If the new protocol cannot interpret the old snapshot schema,
the execution fails validation explicitly; it must not silently refresh data.

#### `REFRESH`

```text
new evidence cutoff and/or identity/mapping state
→ new snapshot
→ new immutable evaluation
```

A refresh references the prior execution for comparison but resolves a new
snapshot and target identity state. It may use the same or a different protocol
version, provided the change report separates evidence/mapping changes from
rule changes. It never updates the prior execution.

### Execution lifecycle and failure model

Technical states:

```text
pending → running → completed
                  ↘ failed
pending/running → cancelled
```

`invalidated` is not an execution mutation state. A completed scientific
execution remains immutable. Later discovery of corruption, source retraction
or protocol defect creates an append-only `execution_governance_event` such as
`superseded`, `retracted` or `integrity_compromised`, with reason, authority,
timestamp and replacement reference where available.

```text
technical execution failure != scientific insufficient evidence
```

A database outage, digest mismatch, engine exception or incomplete write is
`failed`. `no_eligible_evidence`, `identity_unresolved`, `insufficient_evidence`
or `conflict_unresolved` are valid scientific outcomes in a `completed`
execution. Partial results are never canonical. `NORMAL`, `REFRESH` and
`COUNTERFACTUAL` completion requires atomic publication of decisions, result,
trace and their digests. `REPLAY` completion instead requires an immutable
replay verification against the comparison publication and owns no new
scientific publication. Implementation may use staging/checkpoint records for
recovery.

### `evaluation_result`

The result is a non-scalar immutable document belonging to exactly one
completed execution.

Logical structure:

```text
evaluation_result
├── result_status
├── endpoint_components[]
├── evidence_sufficiency
├── quality_dimensions[]
├── relevance_dimensions[]
├── uncertainty_dimensions[]
├── conflict_state
├── conclusions[]
├── assumptions[]
└── explanation_trace_reference
```

`result_status` distinguishes valid scientific states such as complete,
insufficient evidence, unresolved identity or non-computable claim from
technical execution state. Phase 7.3 specializes the result into non-scalar
endpoint syntheses and a multidimensional substance hazard profile without
approving concrete hazard conclusions or a numeric score.

### `result_component`

A result component is one typed, scoped, multidimensional output. It is not
required to contain a scalar value.

Minimum envelope:

| Field | Meaning |
|---|---|
| `component_key` | Stable key within the result |
| `component_type` | Versioned type from the protocol output contract |
| `scope` | Target, endpoint, population/context and applicability |
| `semantic_status` | Applicable, unavailable, insufficient, unresolved or completed state |
| `value` | Typed value permitted by the component schema; may be non-numeric or null |
| `unit` | Explicit unit when applicable |
| `quality_dimensions` | Structured evidence-quality output |
| `confidence_dimensions` | Structured support-for-conclusion output |
| `relevance_dimensions` | Structured relevance output |
| `uncertainty_dimensions` | Structured limitation output |
| `conflict_state` | Conflict classification and references |
| `selection_decision_keys` | Evidence basis |
| `rule_references` | Rules producing the component |
| `assumption_references` | Explicit assumptions |

The type system must be extensible to endpoint conclusions, hazard dimensions,
evidence quality, confidence, uncertainty, exposure readiness and future
numeric components. A future numeric value is one possible typed component; a
mandatory `score: float` is explicitly forbidden as the model's centre.

### `explanation_trace`

The explanation trace is the canonical machine-readable causal graph produced
by the deterministic engine. It contains:

- protocol version and digest;
- snapshot and target identity digests;
- all candidate evidence members;
- every inclusion/exclusion decision and reason code;
- included and excluded evidence references;
- duplicate/dependency and conflict relationships;
- mapping and identity state;
- assumptions;
- ordered transformation steps and canonical rule references;
- result-component derivation edges;
- quality, relevance, confidence and uncertainty dimensions;
- final scientific result references.

Each node has a stable type and key; each edge has a versioned relationship
type. Ordering is explicit only where it carries semantics. The trace may point
to immutable snapshot members instead of duplicating their full content.

AI may verbalize this trace in a separately labelled, non-canonical rendering.
It cannot add, remove or change evidence, decisions, conflicts, assumptions,
uncertainties or canonical conclusions. AI-generated prose is excluded from all
scientific digests.

## Digest and determinism model

Six boundary digests are retained because each proves a different invariant:

| Digest | Includes | Excludes |
|---|---|---|
| `protocol_digest` | Canonical effective declaration, rules, policies, vocabularies and version references | Markdown, comments, audit dates, signatures, surrogate IDs |
| `snapshot_digest` | Canonical query definition/version, cutoff/as-of semantics, sorted resolved evidence members, content digests and evidence provenance | Target/mapping state, protocol, snapshot ID, creation time, physical row order, mutable URLs |
| `input_digest` | Target identity digest and non-protocol, non-evidence domain roots; v1 is target plus mapping state/not-applicable | Evidence snapshot, protocol, semantic configuration, execution mode/comparison, execution ID, worker, timestamps, retries |
| `selection_digest` | Canonically ordered decisions, reason/rule references, relevance values and dependency edges | Decision row IDs, audit timestamps, localized prose |
| `result_digest` | Result status, ordered/typed components, conclusions, dimensions, conflicts and canonical references | Presentation, colours, localized/AI prose, storage IDs |
| `trace_digest` | Canonical trace nodes, edges, rule steps, assumptions and uncertainty references | Later verbalization, UI layout, generated timestamps |

`target_identity_digest` is a component of `input_digest`.
`configuration_digest`, evidence snapshot and protocol are sibling roots of the
future semantic execution identity and are not folded into `input_digest`. A
future `output_bundle_digest` may combine the
selection, result and trace digests for publication convenience; it is
derivable and therefore not required by this logical minimum.

Deterministic equality is defined over semantic content:

```text
same protocol_digest
+ same snapshot_digest
+ same input_digest
+ compatible semantic engine version
→ same selection_digest
+ same result_digest
+ same trace_digest
```

Execution IDs, timestamps and attempt metadata may differ. Any output mismatch
under these conditions is an integrity defect and must never be normalized away.

## Idempotency and concurrency

The logical semantic execution key is derived from:

```text
protocol_digest
+ snapshot_digest
+ input_digest
+ execution_type
+ configuration_artifact_digest
+ comparison execution semantic digest or null
```

`input_digest` commits to target identity and domain roots only. Configuration is
included exactly once as the independent term shown above. This is an identity
tuple, not a database `UNIQUE` decision in Phase 7.1.

Two normal requests with the same tuple are semantically equivalent. Two exact
replays of the same baseline are semantically equivalent verification requests.
The 7.6.4B persistence freeze chooses one globally unique semantic execution;
retries and repeated audit occurrences retain separate technical
`execution_attempt` records beneath it.

Separate executions are legitimate when execution type, protocol, snapshot,
target state, semantic configuration or comparison baseline differs. A retry
after technical failure is a new attempt for the same semantic execution, not a
new scientific input. A different engine build under the same declared semantic
compatibility version is a verification attempt expected to produce identical
digests. A behavior-changing engine requires a versioned semantic input change.

## Logical data model

```text
scientific_protocol
└── scientific_protocol_version [immutable when published]
    ├── canonical_rule_artifact ── protocol_digest
    └── scientific_evaluation_execution
        ├── evidence_snapshot [immutable]
        │   ├── canonical query definition
        │   ├── evidence_snapshot_member[]
        │   │   ├── source → dataset → release → artifact
        │   │   ├── ingestion_run → run_artifact membership
        │   │   ├── assessment → finding
        │   │   ├── substance → identifier/namespace
        │   │   └── ingredient_substance mapping history
        │   └── snapshot_digest
        ├── target_identity_snapshot [immutable]
        │   └── target/mapping/composition semantic payload
        ├── evidence_selection_decision[] [immutable]
        │   └── snapshot assessment/finding member
        ├── evaluation_result [exactly one canonical result]
        │   ├── result_component[]
        │   └── result_digest
        ├── explanation_trace
        │   ├── decisions, conflicts, assumptions, transformations
        │   └── trace_digest
        ├── execution_attempt[] [technical, optional future persistence]
        └── execution_governance_event[] [append-only]
```

The arrows to Phase 6 evidence rows are provenance links. Canonical replay is
based on frozen snapshot content and immutable artifacts, not on an assumption
that every future database row remains unchanged.

## Persistence readiness analysis

No table or migration is approved here.

| Logical entity | Preferred future form | Advantages | Disadvantages / storage | Replay and query implications |
|---|---|---|---|---|
| `scientific_protocol` | Database row plus governed metadata document | Discoverable family identity and lifecycle | Small duplication between row and document | Direct queries; history points to stable key |
| `scientific_protocol_version` | Immutable DB row plus content-addressed canonical JSON artifact | Strong lifecycle queryability and byte-level proof | Must enforce publish immutability across row/artifact | Replay loads exact digest-addressed rules |
| canonical rule artifact | Content-addressed JSON artifact | Independent verification and portable publication | Requires durable artifact retention | Digest lookup is exact; semantic fields may need indexed projection |
| `evidence_snapshot` | DB header row plus immutable JSON manifest | Compact lifecycle/index metadata with portable proof | Header/manifest atomicity must be guaranteed | Query by target/cutoff; replay reads manifest |
| snapshot membership | Join/membership tables plus per-member digest and immutable manifest projection | Exact SQL traversal and evidence-count queries | Largest storage consumer; repeated members across snapshots | Membership is fixed; shared content may be deduplicated by digest |
| `target_identity_snapshot` | Immutable JSON document plus indexed DB header | Supports heterogeneous future targets without schema destruction | Selected fields need projections for efficient search | Replay never resolves current identity/mapping |
| `evidence_selection_decision` | Immutable row per candidate plus optional decision payload JSON | Efficient included/excluded/reason queries | High row count; reason vocabulary must be versioned | Exact audit; can prove every inclusion |
| `scientific_evaluation_execution` | DB row | Strong state machine, concurrency and idempotency coordination | Needs careful atomic completion constraints | Natural history and target/protocol queries |
| `execution_attempt` | Append-only DB row | Separates retries/workers from scientific identity | Additional operational records | Replays and retries remain auditable without changing result |
| `evaluation_result` | Immutable canonical JSON document plus DB header/digest | Non-scalar and extensible | Deep analytics require projections | Exact portable replay comparison |
| `result_component` | DB projection rows plus canonical inclusion in result document | Endpoint/type queries without fixing one scalar schema | Dual representation must be digest-consistent | Components queryable; document remains source of canonical result |
| `explanation_trace` | Content-addressed canonical JSON graph/artifact | Large graph can be stored once and verified | Graph queries are less convenient without projection | Exact replay proof; selected edges may be indexed |
| governance events | Append-only DB rows | Preserves retraction/supersession history | Requires effective-state view | Derived current view never mutates historical execution |
| execution status/current protocol views | Derived views | Convenient operational queries | Never sufficient as canonical history | Must be rebuilt from immutable rows/events |

The hybrid avoids storing duplicate raw evidence bytes while retaining exact
semantic membership. Content-addressed artifacts require retention, integrity
checks and a prohibition on in-place replacement under the same digest/key.

## Compatibility with schema through Alembic `0018`

### Existing identity and time anchors

The current schema exposes the following replay-relevant anchors. Their
presence makes historical freezing possible, but does not by itself make the
referenced semantic rows immutable.

| Layer | Stable identifiers / digests already available | Time or version anchors already available |
|---|---|---|
| Product and composition | Product `id`, barcode/GTIN; product-ingredient `id` and extraction-item link | Product/product-ingredient `created_at`, product `updated_at`; extraction run/item identity and ordering |
| Ingredient | Ingredient `id`, canonical name | `created_at`, `updated_at` |
| Ingredient→substance | Mapping `id`; proposal UUID; decision/materialization/closure IDs | `valid_from`, `valid_to`, `created_at`, `reviewed_at`, `materialized_at`, `closed_at` |
| Substance identity | Substance `id`; namespace key/version; normalized identifier; candidate SHA-256 key | Substance `created_at`/`updated_at`; identifier `created_at`; decision and materialization timestamps |
| Source/dataset/release | `source_key`; source-scoped `dataset_key`; dataset-scoped `external_release_key`; release checksum/algorithm | Release `released_at`, `acquired_at`, `created_at` |
| Artifact | Release-scoped `artifact_key`; raw checksum/algorithm; storage-object identity and checksum | `acquired_at`, `validated_at`, `created_at`; optional object version |
| Ingestion | Run UUID; idempotency key; manifest/config/parser-output fingerprints; exact run-artifact membership | Adapter/acquisition/importer/parser/normalization versions; `created_at`, `started_at`, `completed_at` |
| Assessment | Run-scoped `source_record_key`; external ID/version; normalized checksum | Assessment version/status, publication/validity dates, `created_at` |
| Finding | Assessment-scoped source record/finding keys; ordinal; finding fingerprint | Parent assessment/run versions and finding `created_at` |
| Batch/recovery | Plan/work definition SHA-256, work key, execution UUID, run reference | Attempt number/status, leases, `created_at`, `updated_at`, `started_at`, `completed_at` |

| Logical concept | Current representation | Classification | Phase 7 requirement |
|---|---|---|---|
| Product identity | `products` IDs/GTIN/barcode/names/status/timestamps | Partially represented | Freeze semantic row state; define stable product identity/version |
| Product ingredients/composition | `product_ingredients`, extraction item provenance and created time | Partially represented | Historical version/closure or materialized composition snapshot |
| Ingredient identity | `ingredients` ID/name/status/timestamps | Partially represented | Freeze semantic identity; legacy risk fields remain excluded |
| Ingredient→substance mapping | Temporal `ingredient_substances` plus proposals, decisions, materializations and closures | Partially represented, strong history | Freeze resolved membership; define timestamp/date boundary semantics |
| Substance identity | `substances`, versioned identifier namespaces, identifiers, resolution decisions/materializations | Partially represented | Freeze names/type/status/identifier membership; current rows remain mutable |
| Source | Stable `source_key`, metadata, timestamps | Partially represented | Freeze metadata relevant to claims; name/URL/status may change |
| Dataset | Source-scoped `dataset_key`, metadata, timestamps | Partially represented | Freeze relevant metadata; no explicit immutable dataset version |
| Release | Dataset, `external_release_key`, dates, checksum/status | Represented for provenance | Freeze status/metadata used by eligibility |
| Raw artifacts | `scientific_release_artifacts` + `storage_objects`, raw checksum, size, acquisition/validation times | Represented strongly | Retention and no in-place byte replacement required |
| Ingestion run | Exact release, run UUID, importer/adapter/acquisition/parser/normalization versions, digests, status/timestamps | Represented strongly | Snapshot only terminal eligible runs; freeze semantic run projection |
| Run artifact membership | `scientific_ingestion_run_artifacts` with positions | Represented | Include exact membership and artifact digests |
| Assessments | Run/release/substance identity, source key/version, status/dates, raw/normalized checksum, timestamp | Partially represented | Freeze semantic payload and status; explicit correction/supersession relation is missing |
| Findings | Assessment/source identity, endpoint/value/context/raw payload/fingerprint, timestamp | Partially represented | Freeze payload; legacy nullable fingerprints require canonical fallback |
| Identity/mapping review history | Append-only decisions/materializations with reviewer and timestamps | Represented for covered flows | Freeze applicable decision set and resolved state |
| Batch/recovery | Plans, canonical hashes, work items, attempts, leases, run links and timestamps | Represented operationally | Reuse patterns, not records, for evaluation attempts/recovery |
| Scientific protocol | None | Missing | Future persistence required |
| Immutable protocol version/rule artifact | None | Missing | Future persistence required |
| Evidence snapshot/header | None | Missing | Future persistence required |
| Resolved snapshot membership | None | Missing | Future persistence required |
| Target identity snapshot | None | Missing | Future persistence required |
| Selection decision | None | Missing | Future persistence; semantic contract defined in 7.2 |
| Scientific evaluation execution/attempt | None | Missing | Future persistence required |
| Non-scalar result/components | None | Missing | Future persistence; component envelopes specialized in 7.3 |
| Explanation trace | None | Missing | Future persistence required |
| Retraction/supersession event for execution | None | Missing | Future persistence required |

### Replay-critical gaps

The current schema cannot yet prove a complete Phase 7 replay because:

- there is no immutable snapshot query definition or resolved membership;
- assessment/finding status and semantic payload are not protected from all
  later mutation, and historical rows can lack strong content fingerprints;
- assessment correction/supersession lineage is not explicit;
- substance/source/dataset/product/ingredient semantic rows and identifier
  membership are not fully temporal or immutable;
- product-ingredient composition lacks a complete historical lifecycle;
- the `DATE` validity of ingredient-substance mappings and timestamp-based
  snapshots need a published boundary/time-zone convention;
- unresolved identity candidates are auditable, but no evaluation-target state
  freezes how they affected a particular execution;
- there is no protocol, execution, selection, result or trace persistence;
- no versioned endpoint ontology or evidence dependency vocabulary has yet been
  approved.

These are Phase 7 data-model requirements, not reasons to mutate Phase 6 data or
to infer missing evidence.

## Conceptual invariants

1. A published protocol version and its canonical digest are immutable.
2. Any semantic correction creates a new protocol version.
3. A snapshot header, query definition, membership and digest are immutable.
4. Snapshot membership contains frozen semantic content or an immutable,
   digest-addressed artifact reference; a mutable foreign key alone is invalid.
5. A completed execution references exactly one protocol version, one evidence
   snapshot and one target identity snapshot.
6. Selection decisions are immutable within an execution.
7. Every candidate evidence line has a decision or a protocol-defined parent
   decision that deterministically covers it.
8. Included evidence must have an `included` decision.
9. A result cannot reference evidence outside its snapshot.
10. Excluded evidence remains available for explanation and audit.
11. A completed execution, canonical result and trace are immutable.
12. A canonical result belongs to exactly one execution; an execution publishes
    at most one canonical result bundle.
13. Historical mapping and target identity state are resolved from and frozen
    into the execution inputs.
14. Replay resolves no current-state data and must reproduce all semantic output
    digests.
15. Counterfactual and refresh never replace or mutate their baseline execution.
16. Technical failure is not scientific insufficiency; insufficiency is a valid
    completed result.
17. Absence of eligible evidence cannot generate a danger, safety or risk claim.
18. Partial writes and partial results are never canonical completed output.
19. Governance retraction or supersession is append-only and does not erase the
    retracted execution.
20. AI output cannot be a canonical scientific input, decision, result or trace.

## Architecture threat and failure review

| Scenario | Preservation mechanism |
|---|---|
| Protocol changed in place | Publication immutability, canonical artifact digest and append-only new version make the mutation detectable and invalid |
| Assessment later corrected | Old snapshot retains payload/digest; correction is new evidence lineage and appears only in a refresh |
| Finding deleted or superseded | Materialized membership and frozen payload/content-addressed source preserve history; governance event records integrity issues |
| Ingredient→substance mapping changes | Target/mapping snapshot keeps old rows and semantics; refresh resolves the new state, replay does not |
| Source release replaced | Stable release identity plus artifact raw checksums prevent byte replacement from being silently equivalent |
| Parser version changes | Snapshot records run, parser, normalization and output digests; new parsing creates a new run and refresh universe |
| Same evidence ingested twice | Run/artifact and record fingerprints expose duplicates; Phase 7.2 decisions record dependency/deduplication rather than counting twice |
| Identical executions run concurrently | Semantic execution key coordinates equivalence; separate append-only attempts preserve concurrency history |
| Execution crashes halfway | Pending/running staging plus atomic canonical completion; retry is another attempt and partial output is non-canonical |
| Explanation generated later | Canonical trace is completed with the result; later AI/human rendering is separate, labelled and excluded from digest |
| Future model needs numeric output | Typed result components admit an explicit numeric component without making scalarization mandatory |
| Future allergy/nutrition domain | New protocol family, scientific question, evidence policies and component schemas reuse execution/snapshot envelopes without sharing toxicology semantics |

## First conceptual protocol instance

Provisional protocol family name:

```text
Food Toxicological Evidence Synthesis
```

The name is descriptive and does not imply safety certification or quantitative
risk. External scientific review may refine the display name without changing
the logical model; a semantic domain change would require a new family.

| Declaration | Conceptual value |
|---|---|
| Domain | Food toxicological evidence synthesis |
| Target | Canonical scientific substance with frozen identity context |
| Scientific question | What endpoint-specific toxicological evidence and unresolved limitations are represented for this substance under the protocol and snapshot? |
| Inputs | Frozen substance identity; eligible assessment/finding universe; release/artifact/run provenance; context, quality, relevance, conflict and uncertainty inputs defined by future policies |
| Output class | Endpoint-specific evidence synthesis plus multidimensional substance hazard profile |
| Supported claims | Traceable description of represented evidence, sufficiency, conflicts, limitations and protocol-defined hazard dimensions |
| Forbidden claims | Quantitative exposure, individual/product risk probability, generic health/safety score, medical advice, absence-of-evidence safety or danger conclusion |
| Required evidence context | Endpoint, population/model, route where available, evidence type, value/unit or conclusion context, assessment status/version and complete provenance |
| Missing-evidence behavior | Emit explicit missing/not represented/insufficient state; do not impute danger, safety, weight or numeric value |

This instance demonstrates representability only. It defines no final endpoint
vocabulary, category, formula, threshold, weight, rank, colour or score.

## Phase 7.1 logical test vectors

| # | Scenario | Expected execution identity | Snapshot behavior | Historical/result semantics |
|---:|---|---|---|---|
| 1 | New normal execution | New `NORMAL` semantic key | New hybrid snapshot and target freeze | New immutable result; no numeric assumption |
| 2 | Exact replay | `REPLAY` key references baseline; same semantic input digests | Reuses exact membership and target state | Verification records `matched` or `mismatch`; neither creates a new scientific publication, and mismatch is not a technical failure when computation completed |
| 3 | Replay after future mapping change | Same replay identity rules as #2 | Uses historical frozen mapping, never current mapping | Original result reproduced; new mapping is irrelevant to replay |
| 4 | Counterfactual with protocol v2 | New `COUNTERFACTUAL` key with baseline and v2 digest | Reuses baseline snapshot/target | New immutable result; component diff measures rule impact only |
| 5 | Refresh with new release | New `REFRESH` key | New cutoff and membership include eligible new release | Prior result preserved; change report separates evidence from rule changes |
| 6 | No eligible evidence | Completed normal execution | Candidate universe retained; all candidates excluded or universe empty by explicit policy | Valid `no_eligible_evidence`/insufficient result, never technical failure or danger |
| 7 | Unresolved substance identity | New normal execution with unresolved target state | Candidate/identity state frozen; no silent target substitution | Valid `identity_unresolved` or non-evaluable result with trace |
| 8 | True conflicting evidence | One normal semantic key | Both independent conflicting lines remain members and decisions | Completed multidimensional conflict state; no automatic averaging |
| 9 | Technical execution failure | Same semantic key, failed attempt | Snapshot stays immutable if already published; incomplete construction is non-canonical | No canonical scientific result; retry creates another attempt |
| 10 | Duplicate concurrent execution | Same semantic key for both requests | One equivalent snapshot identity | One logical execution or equivalent executions plus distinct attempts; no double-counted result |
| 11 | Protocol retired after historical execution | Historical execution key unchanged | Historical snapshot unchanged | Result remains auditable; governed replay allowed by retirement policy; no new normal use |
| 12 | Evidence source corrected after snapshot | Historical execution key unchanged | Old payload/digest retained; corrected record enters only a new snapshot | Replay keeps original; refresh creates new result and provenance diff |

## Implementation readiness classification

The classification describes logical maturity, not authorization to implement.

| Logical entity / concern | Classification | Reason |
|---|---|---|
| `scientific_protocol` identity and family contract | READY FOR IMPLEMENTATION | Logical identity and lifecycle boundary are defined |
| `scientific_protocol_version` lifecycle/immutability | READY FOR IMPLEMENTATION | Publication and correction semantics are defined |
| Selection canonical rule envelope/content | READY FOR IMPLEMENTATION | Eligibility/reason/dependency contract defined in 7.2; scientific allowlists still require review |
| Protocol canonical JSON/digest envelope | READY FOR IMPLEMENTATION | Canonicalization requirements and digest boundary are defined |
| Evidence snapshot/header and hybrid membership contract | READY FOR IMPLEMENTATION | Universe/membership distinction and freeze boundary are defined |
| Snapshot database schema and storage optimization | REQUIRES FUTURE PERSISTENCE DESIGN | Table/artifact split, retention and indexes belong to persistence work |
| Target identity snapshot envelope | READY FOR IMPLEMENTATION | Required freeze semantics are defined |
| Product composition historical model | REQUIRES FUTURE PERSISTENCE DESIGN | Current schema lacks full temporal composition history |
| Evidence selection decision envelope | READY FOR IMPLEMENTATION | Phase 7.2 defines reason codes, relevance states and canonical decision content |
| `scientific_evaluation_execution` and mode semantics | READY FOR IMPLEMENTATION | Identity, lifecycle and mode invariants are defined |
| Execution/attempt DB concurrency constraints | REQUIRES FUTURE PERSISTENCE DESIGN | No final `UNIQUE`, locking or staging schema is approved |
| `evaluation_result` envelope | READY FOR IMPLEMENTATION | Non-scalar structure and ownership are defined |
| Scientific result component envelope | READY FOR IMPLEMENTATION | Phase 7.3 defines endpoint synthesis and substance-profile structures; scientific vocabularies remain review-gated |
| `explanation_trace` envelope | READY FOR IMPLEMENTATION | Canonical graph boundary and AI separation are defined |
| Selection and synthesis trace envelopes | READY FOR IMPLEMENTATION | Phase 7.2 defines selector stages and Phase 7.3 defines synthesis trace content |
| Digest boundary model | READY FOR IMPLEMENTATION | Six independently verifiable semantic boundaries are defined |
| Governance event persistence | REQUIRES FUTURE PERSISTENCE DESIGN | Append-only semantics are fixed; schema is not |
| Numerical components | DEFERRED | No numerical output is justified for the first protocol |
| Ingredient scientific projection envelope | READY FOR IMPLEMENTATION | Phase 7.4 defines non-scalar entries, mapping snapshot, states, trace and digests; scientific transfer rules remain review-gated |
| Product-composition snapshot and exposure-scenario envelopes | READY FOR IMPLEMENTATION | Phase 7.5 defines freeze, provenance, assumptions, trace and digest boundaries; persistence remains pending |
| Exposure-readiness and risk-computability result envelopes | READY FOR IMPLEMENTATION | Phase 7.5 defines non-numeric states and reason codes without calculation |
| Complete historical product composition reader | REQUIRES FUTURE PERSISTENCE DESIGN | Current product/composition/serving history is incomplete |
| Exposure calculation / reference comparison / risk characterisation | BLOCKED BY SCIENTIFIC REVIEW | Logical gate is defined; scientific methods and required canonical data are not approved |

## Phase 7.1 exit criteria

- [x] Protocol identity defined.
- [x] Immutable protocol version and lifecycle defined.
- [x] Canonical protocol representation and digest requirements defined.
- [x] Evidence snapshot universe and hybrid membership semantics defined.
- [x] Target identity freeze defined.
- [x] Evidence selection decision output contract defined.
- [x] General scientific evaluation execution model defined.
- [x] `NORMAL`, `REPLAY`, `COUNTERFACTUAL` and `REFRESH` semantics defined.
- [x] Multidimensional non-scalar result and component envelopes defined.
- [x] Machine-readable explanation trace defined.
- [x] Digest and determinism model defined.
- [x] Idempotency and concurrent duplicate semantics defined.
- [x] Technical failure versus scientific insufficiency defined.
- [x] Logical data model documented.
- [x] Current-schema compatibility and replay gaps documented.
- [x] Persistence readiness analysis completed without schema design.
- [x] Conceptual invariants formalized.
- [x] Architecture failure analysis completed.
- [x] First real protocol instance shown without scientific synthesis rules.
- [x] Twelve logical test vectors defined.
- [x] Deferred scientific and persistence decisions explicitly classified.

## Phase 7.2–7.5 specializations and next checkpoint

The evidence-selection specialization is defined in:

```text
WYE_EVIDENCE_SELECTION.md
```

The endpoint-synthesis specialization is defined in:

```text
WYE_EVIDENCE_SYNTHESIS.md
```

The ingredient-projection specialization is defined in:

```text
WYE_INGREDIENT_PROJECTION.md
```

The product-assessment and exposure-readiness specialization is defined in:

```text
WYE_PRODUCT_ASSESSMENT.md
```

The Phase 7.6 specialization is defined in:

```text
WYE_SCORING_PERSISTENCE.md
```

It establishes canonical artifacts, rebuildable query projections, separate
execution/attempt lifecycles, atomic publication, governance events, replay
verification and the persisted digest graph for all Phase 7.1–7.5 objects.
The technical freeze is now defined in `WYE_SCORING_SCHEMA_FREEZE.md`. It
resolves migration decision B and records `READY FOR MIGRATION IMPLEMENTATION`
for the bounded Phase 7.6.2A foundation only. The migration and runtime are not
started by this document.

The later Phase 7.6.4A-1 specialization is defined in:

```text
WYE_MAPPING_EXECUTION_INPUT_FREEZE.md
```

It narrows v1 target support to `substance` and `ingredient`, keeps the evidence
snapshot independent from target and mapping state, defines UTC-date historical
mapping semantics, and resolves the digest graph. `input_digest` is the target
plus non-protocol/non-evidence domain roots; protocol, sealed evidence snapshot,
execution type and configuration combine with it only in the future
`semantic_execution_digest`. Product is deferred until historical composition
and scenario inputs can be frozen. The specialization is documentation only and
does not authorize or implement execution persistence or scoring. Phase
7.6.4A-2 now implements the bounded target/mapping/input artifact construction
defined by that specialization and is `COMPLETED + COMMITTED`; evidence snapshot,
protocol and execution mode remain sibling roots for a later execution runtime.

Phase 7.6.4B-1 is specialized in
`WYE_EXECUTION_PERSISTENCE_FREEZE.md`. It makes the existing execution tuple a
canonical `scientific_evaluation_execution_identity/1` artifact whose digest is
the sole `semantic_execution_digest`, and freezes one semantic execution with
multiple operational attempts. Semantic engine compatibility is part of the
configuration root; concrete build provenance belongs to each attempt.

The 0021 publication bundle binds semantic execution, selection, result and
trace roots for `NORMAL`, `REFRESH` and `COUNTERFACTUAL`. REPLAY instead binds
expected and recomputed roots in
`scientific_evaluation_replay_verification/1`, while reusing the global
content-addressed artifacts and creating no new scientific publication.
Rebuildable query projections are excluded from that canonical bundle and
remain a later 0022 concern. This bounded correction supersedes the
preliminary physical sketch only where that sketch mixed engine/build metadata,
selection resolution or query projections with canonical identity. Phase
7.6.4B-1B is the authoritative REPLAY amendment. Phase 7.6.4B-2 implements that
amendment and is completed and committed; it creates no execution, selection,
synthesis, scoring or replay runtime.

## Phase 7.6.4C runtime boundary

Phase 7.6.4C implements the provider-neutral persistence orchestration above
0021. It builds the frozen configuration and semantic-execution artifacts,
creates/reuses executions and operational idempotency bindings, manages attempt
start/heartbeat/failure, and atomically persists caller-supplied canonical
selection/result/trace/publication outputs. REPLAY recomputed payloads are
comparison material: matching bytes reuse global artifact IDs, while one
immutable `matched` or `mismatch` verification completes the REPLAY execution
without new scientific output ownership.

The service is transaction-participating: repositories and artifact writer do
not commit or roll back. Counterfactual authorization remains a separately
created governance fact and is never synthesized by this runtime. Scientific
selection, synthesis, projection, scoring, product evaluation and worker
recovery remain absent. Status: `COMPLETED + COMMITTED`. This closes the
persistence/runtime foundation defined by Phase 7.6; Phase 7.7 runtime is not
started.

## Phase 7.7.1A selection policy and runtime contract freeze

The first scientifically coherent engine slice is deterministic evidence
eligibility and selection:

```text
sealed evidence snapshot
+ published executable protocol
-> one canonical decision per candidate
-> canonical selection manifest
```

The entry-gate ambiguity is technically resolved in
`WYE_SELECTION_POLICY_FREEZE.md`. `protocol_definition/1` embeds the closed
`wye_scientific_evidence_selection_policy/1` object and therefore commits the
policy, registries, mappings and evaluation plan under the protocol digest.
Unknown schemas/operators/registries are fail-closed. Candidate decisions and
the manifest bind the selection-policy sub-root and retain the existing 0021
binary decision plus resolved/deferred model.

Phase 7.7.1 is a pure non-published engine/harness. It creates no execution or
dangling attempt and cannot fabricate result/trace payloads to satisfy 0021.
The later synthesis/evaluation path consumes the same canonical selection
models and supplies the real result and complete trace for atomic publication.

The technical contract is frozen, but no externally reviewed policy instance
or approved golden-case set exists. Phase 7.7.1B prepares candidate scientific
values and authored oracles; independent approval is still required before a
production selector is authorized.

```text
Phase 7.7.1A:
TECHNICAL CONTRACT FROZEN
```

## Phase 7.7.1B candidate execution boundary

The candidate `efsa_qps_evidence_selection/1.0.0-candidate.1` and its golden
corpus do not change the selection-only execution boundary. They create no
0021 execution, attempt, decision row, trace row or publication. The policy
digest is stable candidate identity, not lifecycle approval.

Until independent scientific and validation approval exists, no production
scientific selector may execute this policy. A future technical conformance
interpreter may exercise only synthetic fixtures outside scientific
publication. No fake result/trace is permitted to force a selection-only run
through the atomic publication model.

```text
Phase 7.7.1B:
CANDIDATE POLICY FROZEN
```

## Phase 7.7.1C review-package boundary

The external review package and golden-corpus manifest add governance and
approval identity only. They do not change the selection-only harness boundary
and do not authorize an execution, attempt, result, trace or publication. A
production selector remains blocked until approval is recorded for the exact
governed digests and the final publishable policy bytes are revalidated.

```text
Phase 7.7.1C:
SCIENTIFIC REVIEW PACKAGE COMPLETED

Phase 7.7.1:
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL
```
