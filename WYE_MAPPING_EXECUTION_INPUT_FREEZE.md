# WYE — Mapping State and Canonical Execution Input Freeze

## Status and authority

This document is the canonical Phase 7.6.4A-1 design freeze. It resolves the
target, ingredient-to-substance mapping-state and non-protocol execution-input
ambiguities identified by the first Phase 7.6.4A implementation gate.

```text
Phase 7.6.4A-1:
DESIGN FROZEN — READY FOR IMPLEMENTATION

Phase 7.6.4A-1B:
AUTHORITY MULTIPLICITY AMENDMENT FROZEN

Phase 7.6.4A-2:
COMPLETED + COMMITTED
```

The 7.6.4A-1/1B checkpoints defined artifact contracts and future persistence
references without implementation. The later 7.6.4A-2 status recorded at the end
of this document implements only those frozen runtime contracts. No checkpoint
here creates a migration, executes a scientific protocol, selects or synthesizes
evidence, or produces a scientific result.

The following later freeze supersedes older shorthand where an evidence
snapshot or target snapshot was described as also containing mapping state:

```text
evidence snapshot
!= target identity
!= mapping state
!= protocol version
!= execution
!= result
```

## Supported targets in v1

The initial target vocabulary is exactly:

```text
substance
ingredient
```

`product` is excluded. The current schema cannot reconstruct a complete
historical product formulation, ingredient quantity, serving or preparation
state. Product support requires a separately frozen and implemented canonical
product-composition/scenario input checkpoint. It must not be added to artifact
schema version 1 merely for symmetry.

## Canonical target artifact

The target identity artifact contract is:

```text
artifact_kind: scientific_evaluation_target
schema_version: 1
canonicalization_version: wye-c14n-json-v1
digest_algorithm: sha256
content_type: application/vnd.wye.scientific+json
```

Its artifact content digest is the `target_identity_digest`. The runtime writer
hashes the complete canonical envelope. Target labels and mutable descriptive
fields are frozen semantic state but are not the stable target key.

### Stable identity rule

The current schema guarantees no ingredient/substance UUID that is portable
across unrelated databases. V1 therefore uses the honest local-lineage key:

```text
identity_namespace: wye_internal_id_v1
entity_type: substance | ingredient
entity_id: signed 64-bit database identity
```

The key is stable inside the WYE database lineage, backups and replicas. It is
not claimed to identify an entity across independently seeded WYE databases.
The artifact additionally freezes the current semantic row state and available
identifiers, so reuse cannot depend on the BIGINT alone.

### Common payload

All fields below are required unless explicitly nullable:

| Field | V1 rule |
|---|---|
| `artifact_type` | Exact `scientific_evaluation_target` |
| `schema_version` | Exact string `1` |
| `target_type` | `substance` or `ingredient` |
| `identity_as_of` | Canonical UTC timestamp |
| `identity_namespace` | Exact `wye_internal_id_v1` |
| `entity_id` | Signed 64-bit integer |
| `identity_resolution_state` | Exact `resolved` in v1 artifacts |
| `identity_recorded_at` | Canonical UTC timestamp from the authoritative row `updated_at`, or `created_at` only where the schema has no later-state timestamp |
| `identity_state` | Target-type payload below |

A historical artifact may be constructed from the current row only when the
runtime can establish that the frozen row state was already recorded by
`identity_as_of` and was not changed afterwards. If `identity_recorded_at` is
later than `identity_as_of`, or the required prior state is otherwise absent,
construction fails with `historical_target_state_unavailable`; it must not copy
the current row and label it historical.

### Substance identity state

The substance payload contains:

```text
preferred_name: string
normalized_name: string
scientific_name: string | null
substance_type: current frozen vocabulary value
status: active | deprecated | review_pending
```

`substance_identifiers` is deliberately excluded from target artifact schema
version 1. Those rows have `created_at` but no `updated_at` or lifecycle history,
so their verification/primary state cannot be reconstructed honestly for a past
`identity_as_of`. Stable target identity therefore uses the namespaced WYE row
identity, not a mutable identifier-table projection. A later identifier-aware
target schema requires its own versioned history contract; v1 must fail rather
than silently attach current identifier state to a historical target.

### Ingredient identity state

The ingredient payload contains:

```text
canonical_name: string
common_name: string | null
ingredient_group: string | null
status: active | deprecated | review_pending
declared_identifiers: set-like array
```

Declared CAS/EINECS values are retained with their source field and without
upgrading them to verified registry identifiers. Legacy risk/evidence fields,
allergen semantics and scoring fields are excluded.

## Canonical mapping state

A canonical mapping state is the immutable representation of the authoritative
ingredient-to-substance relationships that were both:

1. scientifically effective for the frozen mapping day; and
2. recorded/materialized in WYE by the frozen `as_of` timestamp.

It is not all current bridge rows and it is not a projection decision. It
preserves `relationship_type` without interpreting its scientific effect.

V1 mapping policy identity is:

```text
mapping_policy_key: ingredient_substance_authoritative_state
mapping_policy_version: 1
```

### Effective time and recorded time

The canonical request timestamp is converted to mapping time as follows:

```text
as_of_utc = canonical UTC timestamp
mapping_day = calendar DATE of as_of_utc in UTC
```

No host locale or Europe/Rome daylight-saving rule participates. Mapping
validity is inclusive:

```text
valid_from <= mapping_day
AND (effective valid_to IS NULL OR effective valid_to >= mapping_day)
```

V1 is best-supportable bitemporal reconstruction, not a claim that the Phase 6
schema is fully bitemporal. A governed mapping is visible only when its bridge,
accept decision and materialization timestamps are not later than `as_of_utc`.
For a controlled closure, `valid_to` applies historically only when the closure
`closed_at`/`created_at` is visible by `as_of_utc`; a later-recorded closure is
ignored for the earlier recorded-time view. A bridge `valid_to` with no matching
closure/history proof cannot be back-projected safely and produces an
unavailable/partial history state.

### Membership and status matrix

| Phase 6 state visible at `as_of` | Classification | V1 behavior |
|---|---|---|
| Accepted bridge with one or more valid visible authority chains; effective on `mapping_day` | INCLUDED AS MEMBER | One bridge member with every valid chain in `authority_chains[]` |
| Same governed mapping closed later than `as_of` | INCLUDED AS MEMBER when otherwise effective | Later closure is not retroactively visible |
| Governed mapping whose inclusive interval contains `mapping_day`, even if now closed/superseded | INCLUDED AS MEMBER | Historical member; closure provenance frozen when visible |
| Governed mapping ended before `mapping_day` | PROVENANCE ONLY | Not an effective member |
| Pending proposal | PROVENANCE ONLY | Never treated as accepted |
| Bridge `pending_review` or `ambiguous` | PROVENANCE ONLY | Non-authoritative observation |
| Rejected proposal/decision or bridge `rejected` | PROVENANCE ONLY | Rejection is not an effective relation and not evidence of absence |
| Deferred review decision | PROVENANCE ONLY | Unresolved review observation |
| `legacy_unreviewed` bridge | PROVENANCE ONLY | Never trusted as an execution mapping |
| `accepted` bridge without provable terminal accept/materialization lineage | PROVENANCE ONLY | `uncontrolled_accepted_bridge`; partial with another member, otherwise unavailable |
| Materialization inconsistency or a purported failed materialization | PROVENANCE ONLY | No member; integrity reason recorded. The normal Phase 6 service has no committed `failed` materialization state |
| Row/event recorded after `as_of` | EXCLUDED | Not historically visible |
| Mapping for another ingredient | EXCLUDED | Outside target scope |

Non-members do not become mapping members. Canonical observation descriptors
are retained only where needed to prove why the state is empty, partial or
unavailable; they never receive a weight or scientific contribution.

### Legacy policy

Migration 0017 does not retroactively create proposal/decision/materialization
authority for pre-existing bridge rows. Therefore:

- `legacy_unreviewed` rows are never members;
- accepted rows without reconstructible controlled authority are not members;
- a pre-workflow accepted bridge becomes controlled for viewpoints at/after a
  valid visible `already_current` adoption chain and may then be a member;
- such rows remain provenance observations;
- if they could materially change the execution mapping, the manifest is
  `partially_resolved` when another trustworthy member subset exists and
  `history_unavailable` when no trustworthy member exists or history is invalid;
- a future governed proposal/review/materialization creates a new mapping state;
  it does not rewrite the old manifest.

## Phase 7.6.4A-1B authority multiplicity amendment

### Bridge identity and authority history

A **mapping bridge** is one historical `ingredient_substances` row representing
one ingredient/substance/relationship relationship over its validity interval.
One canonical mapping member represents one bridge. Separate bridge rows remain
separate members even when their ingredient, substance and relationship type
match; proposals or materializations never create an additional member by
themselves.

An **authority chain** is one internally consistent proposal -> terminal accept
decision -> materialization path that supports, adopts or confirms a bridge.
Migration 0017 makes `decision_id` unique in materializations but deliberately
does not make `ingredient_substance_id` unique. The Phase 6 service may therefore
materialize multiple accepted proposals onto the same current bridge, with one
`applied` chain and zero or more `already_current` chains. This is authoritative
history, not duplicate scientific membership.

Cardinality is frozen as:

```text
mapping member -> zero or more authority chains
included mapping member -> one or more valid visible authority chains
```

Every complete, valid authority chain visible at `as_of` is represented. No
chain is selected by first/latest row, lowest id, `applied` precedence or worker
arrival. Incomplete or inconsistent chains never enter `authority_chains`; when
visible and relevant, they become non-member observations.

### Valid authority-chain rule

An authority chain is valid for a bridge at the requested historical viewpoint
only when all of the following hold:

1. proposal ingredient, substance and relationship type equal the bridge;
2. the terminal decision belongs to that proposal and is `accept`;
3. the materialization references that decision, proposal and bridge;
4. materialization status is `applied` or `already_current`;
5. bridge, proposal, decision and materialization are recorded no later than
   `as_of`;
6. decision `effective_from` is not later than `mapping_day`;
7. the bridge is `accepted` and effective on `mapping_day` after applying only
   historically visible closure information.

Recorded visibility uses `proposal.created_at`, both `decision.reviewed_at` and
`decision.created_at`, and both `materialization.materialized_at` and
`materialization.created_at`; every applicable timestamp must be `<= as_of`.
A proposal/decision visible before its required materialization is not authority
and is represented as `accepted_not_materialized_as_of` when execution-relevant.
Rows/events recorded after `as_of` are excluded entirely, including from
observations, so later knowledge does not leak into an earlier canonical view.

### Authority-chain identity and payload

`authority_chain_identity_digest` is SHA-256 over this exact canonical object:

```json
{
  "bridge_id": 7001,
  "decision_id": 9001,
  "identity_namespace": "wye_internal_id_v1",
  "identity_type": "ingredient_substance_mapping_authority_chain",
  "identity_version": "1",
  "materialization_id": 10001,
  "proposal_id": 8001,
  "proposal_key": "11111111-1111-4111-8111-111111111111"
}
```

Local BIGINT identities and the proposal UUID are historical identities already
supported by Phase 6. They are not claimed portable across unrelated WYE database
lineages.

Each `authority_chains[]` element has exactly these required fields:

```text
authority_chain_identity_digest
proposal
decision
materialization
```

`proposal` contains `proposal_id`, `proposal_key`, `ingredient_id`,
`substance_id`, `relationship_type`, `mapping_method`, `mapping_confidence`,
nullable `source_dataset_release_id`, nullable `ingestion_run_id`, `proposed_by`,
nullable `provenance`, and `created_at`. `mapping_confidence` is a canonical
decimal string or null, never a binary float.

`decision` contains `decision_id`, exact `decision_type=accept`,
`effective_from`, `reviewed_by`, `reviewed_at`, `reason_code`, nullable
`provenance`, and `created_at`. Free-form `notes` is excluded.

`materialization` contains `materialization_id`, `materialization_status`,
`materialized_by`, `materialized_at`, nullable `provenance`, and `created_at`.
All timestamps are canonical UTC strings. All database JSON is normalized into
the canonical JSON v1 domain; unsupported values fail rather than stringify.

Authority chains are ordered by the unsigned bytewise tuple:

```text
(materialized_at canonical UTF-8,
 authority_chain_identity_digest bytes)
```

The digest is a deterministic tie-breaker when timestamps are equal. `applied`
and `already_current` have no precedence: both are valid authority provenance,
neither changes bridge relationship semantics, and neither receives scientific
weight.

### Controlled adoption of a pre-workflow bridge

An accepted bridge that predates controlled history is `uncontrolled` before a
valid authority chain becomes visible. A later valid `already_current` chain is
sufficient controlled adoption from its recorded/effective viewpoint onward;
the same bridge may then be INCLUDED. It does not retroactively authorize an
earlier `as_of`. A `legacy_unreviewed` bridge is not silently upgraded: the
normal Phase 6 workflow creates or resolves an accepted bridge, and only an
accepted bridge with a valid chain can become a member.

Adding another valid chain later preserves `member_identity_digest`, changes the
member semantic artifact because `authority_chains[]` changed, and may therefore
change the later `mapping_snapshot_digest`.

## Mapping member artifact

The canonical member contract is:

```text
artifact_kind: scientific_mapping_state_member
schema_version: 1
canonicalization_version: wye-c14n-json-v1
digest_algorithm: sha256
```

The contract remains schema version `1`: no runtime member artifact has yet been
implemented or published, so this amendment completes the initial v1 freeze
rather than versioning an already released singular-authority payload.

Required payload:

```text
artifact_type
schema_version
mapping_policy_key
mapping_policy_version
member_identity_digest
ingredient_target_digest
substance_target_digest
relationship_type
effective_state
authority_chains[]
provenance
```

`relationship_type` is exactly one of `represents`, `contains`, `derived_from`,
`mixture_component`, `equivalent_to`. No equivalence, transfer, quantity,
weight or projection is calculated.

`effective_state` contains `mapping_status=accepted`, `valid_from`, effective
`valid_to` or null, `mapping_day`, `recorded_as_of`, and the visible closure
descriptor or null. `authority_chains` is the complete canonically ordered array
defined by the 7.6.4A-1B amendment and must contain at least one element for an
included member. `provenance` contains normalized bridge mapping method, source
release/run references and schema-safe canonical provenance fields. Unsupported
raw Python or PostgreSQL values must be adapted explicitly; they are never
stringified implicitly.

### Member identity digest

`member_identity_digest` is SHA-256 over the canonical v1 identity object:

```json
{
  "identity_namespace": "wye_internal_id_v1",
  "identity_type": "ingredient_substance_mapping",
  "identity_version": "1",
  "ingredient_id": 42,
  "mapping_row_id": 7001,
  "relationship_type": "contains",
  "substance_id": 99
}
```

The database row identity is intentionally used because Phase 6 exposes no
portable mapping UUID. It is namespaced and accompanied by ingredient,
substance and relationship identity, so it is neither an ordering key alone nor
a claim of cross-database portability. `valid_from`, `valid_to`, status and
closure are semantic payload, not identity: a later closure changes the member
artifact digest while preserving the identity of the historical bridge row.

## Non-member observations

A non-member observation is a visible historical mapping fact that affects the
completeness or explainability of reconstruction but does not satisfy canonical
membership. It is part of the mapping-state manifest semantic content, is
included in `mapping_snapshot_digest`, and must never be treated as a scientific
mapping relationship.

Allowed `observation_kind` values are exactly:

```text
bridge
proposal
decision
materialization
closure
authority_chain
```

### Observation identity

`subject_identity_digest` is SHA-256 over this fixed canonical identity shape:

```text
identity_namespace: wye_internal_id_v1
identity_type: mapping_non_member_observation_subject
identity_version: 1
observation_kind
bridge_id: integer | null
proposal_id: integer | null
decision_id: integer | null
materialization_id: integer | null
closure_id: integer | null
```

At least one local historical id is required. Null fields remain present. The
reason code is not part of subject identity: the same historical subject can be
observed under a different deterministic reason at a different viewpoint.

### Closed observation reason vocabulary

| Reason code | Resolution impact | Meaning |
|---|---|---|
| `pending_proposal` | `extends_set` | Visible unresolved proposal could add a relationship |
| `pending_review_bridge` | `extends_set` | Visible pending bridge could become authoritative |
| `ambiguous_bridge` | `extends_set` | Visible ambiguous bridge could alter membership |
| `rejected_decision` | `none` | Visible terminal rejection; retained for explanation only |
| `rejected_bridge` | `none` | Visible rejected bridge; not evidence of an accepted mapping |
| `deferred_decision` | `extends_set` | Review was deferred and remains potentially execution-relevant |
| `accepted_not_materialized_as_of` | `extends_set` | Accept decision is visible/effective but required materialization is not |
| `accepted_authority_not_effective` | `none` | Accepted authority starts after `mapping_day` |
| `materialization_inconsistent` | `invalidates_reconstruction` | Proposal/decision/materialization/bridge references or states disagree |
| `legacy_unreviewed_bridge` | `extends_set` | Effective legacy bridge lacks controlled authority |
| `uncontrolled_accepted_bridge` | `extends_set` | Effective accepted bridge has no valid visible authority chain |
| `history_incomplete` | `invalidates_reconstruction` | Required historical facts cannot be reconstructed |
| `closure_history_inconsistent` | `invalidates_reconstruction` | Bridge validity and visible closure history disagree |
| `out_of_effective_range` | `none` | Visible controlled relationship is not effective on `mapping_day` |

There is no `recorded_after_as_of` observation: later records are excluded from
the historical canonical input. Phase 6 has no `failed` materialization status;
unsupported/cross-linked materialization rows use
`materialization_inconsistent` rather than inventing a state.

### Observation payload and digest

Each manifest observation contains exactly:

```text
observation_kind
reason_code
resolution_impact
subject_identity
subject_identity_digest
observation_semantic_digest
bridge_context
authority_chain_identity_digest: lowercase digest | null
recorded_at: canonical UTC timestamp
effective_from: date | null
effective_to: date | null
```

`subject_identity` is the fixed identity object above. `bridge_context` contains
required `ingredient_id` and nullable `bridge_id`, `substance_id`, and
`relationship_type`. `observation_semantic_digest` is SHA-256 over the exact
observation body excluding only the `observation_semantic_digest` field itself.
Free-form notes/messages are excluded.

Observations are ordered by the unsigned bytewise tuple:

```text
(reason_code UTF-8,
 observation_kind UTF-8,
 subject_identity_digest bytes,
 observation_semantic_digest bytes)
```

SQL order, event insertion order and worker order are not semantic.

## Mapping-state manifest artifact

The mapping root contract is:

```text
artifact_kind: scientific_mapping_state_manifest
schema_version: 1
canonicalization_version: wye-c14n-json-v1
digest_algorithm: sha256
```

Its content digest is `mapping_snapshot_digest`. Required payload:

```text
artifact_type
schema_version
mapping_policy_key
mapping_policy_version
as_of
mapping_day
ingredient_target_digest
resolution_state
resolution_reason_codes[]
ordered_members[]
non_member_observations[]
member_count
observation_count
```

Allowed `resolution_state` values are:

| State | Meaning |
|---|---|
| `resolved` | One or more authoritative members exist; no observation with `extends_set` or `invalidates_reconstruction` exists |
| `empty` | Zero members; history is sufficiently complete; no observation could add/alter membership |
| `partially_resolved` | One or more authoritative members form a trustworthy subset, but at least one `extends_set` observation could extend it |
| `history_unavailable` | Reconstruction cannot truthfully establish a complete mapping state |

State derivation has this exact precedence:

| Condition | Result |
|---|---|
| Any `invalidates_reconstruction` observation | `history_unavailable` |
| No invalidating observation, at least one `extends_set` observation, and `member_count > 0` | `partially_resolved` |
| No invalidating observation, at least one `extends_set` observation, and `member_count = 0` | `history_unavailable` |
| No blocking observation and `member_count > 0` | `resolved` |
| No blocking observation and `member_count = 0` | `empty` |

Thus `history_unavailable` means no complete trustworthy state can be asserted;
`partially_resolved` means a trustworthy non-empty subset exists but completeness
is unresolved. Multiple valid authority chains for one member do not affect the
resolution state by themselves.

`resolution_reason_codes` is ordered as one primary code followed by the sorted
unique blocking observation reason codes. Primary codes are closed:

```text
authoritative_mapping_complete
no_mapping_records
no_authoritative_effective_mapping
additional_candidates_unresolved
historical_reconstruction_incomplete
```

`resolved` uses `authoritative_mapping_complete`. `empty` uses
`no_mapping_records` when no visible mapping/proposal history exists, otherwise
`no_authoritative_effective_mapping`. `partially_resolved` uses
`additional_candidates_unresolved`; `history_unavailable` uses
`historical_reconstruction_incomplete`. Empty and unresolved states are
canonical technical inputs, not danger, safety or scientific conclusions.

`ordered_members` descriptors contain:

```text
relationship_type
substance_target_digest
member_identity_digest
member_semantic_digest
```

They are sorted by the unsigned bytewise tuple:

```text
(relationship_type UTF-8,
 substance_target_digest bytes,
 member_identity_digest bytes,
 member_semantic_digest bytes)
```

All digests are lowercase hexadecimal in JSON and 32-byte `BYTEA` in database
metadata. `member_count` and `observation_count` exactly equal their array
lengths. The observation order is the amended order defined above. SQL order,
BIGSERIAL order, insertion order and worker order are excluded.

### Full canonical ordering graph

```text
mapping members:
  (relationship_type UTF-8,
   substance_target_digest bytes,
   member_identity_digest bytes,
   member_semantic_digest bytes)

authority chains within one member:
  (materialized_at canonical UTF-8,
   authority_chain_identity_digest bytes)

non-member observations:
  (reason_code UTF-8,
   observation_kind UTF-8,
   subject_identity_digest bytes,
   observation_semantic_digest bytes)
```

## Canonical non-protocol execution input

The conflict around `input_digest` is resolved as follows:

```text
input_digest
= digest of canonical non-protocol, non-evidence domain input
```

For artifact schema version 1 it contains the target root and mapping-state
root only. It explicitly excludes:

- evidence snapshot digest;
- protocol digest/version;
- execution mode;
- comparison execution;
- semantic configuration;
- engine/build metadata;
- runtime/request/audit metadata.

The artifact contract is:

```text
artifact_kind: scientific_evaluation_input
schema_version: 1
canonicalization_version: wye-c14n-json-v1
digest_algorithm: sha256
```

Required payload:

```text
artifact_type
schema_version
input_as_of
target: {target_type, target_artifact_digest}
mapping_state: {
  applicability,
  resolution_state,
  manifest_digest
}
domain_inputs: []
```

For an ingredient, mapping applicability is `required` and the manifest digest
is mandatory even when the manifest state is empty or unavailable. For a
substance, applicability is `not_applicable`, resolution state is
`not_applicable` and manifest digest is null. `domain_inputs` is an exact empty
array in v1; product composition/scenario support requires a new artifact schema
version after its own freeze.

The content digest of `scientific_evaluation_input/1` is exactly `input_digest`.
No broader execution-request artifact is introduced.

## Final digest graph

The unambiguous v1 graph is:

```text
target artifact digest
+ mapping-state manifest digest or explicit not_applicable state
    -> input artifact digest = input_digest

protocol_digest
+ sealed evidence snapshot_digest
+ input_digest
+ execution_type
+ configuration_artifact_digest
+ comparison semantic execution digest or null
    -> semantic_execution_digest
```

Evidence snapshot and protocol are independent siblings of `input_digest`.
They are not duplicated inside the input artifact. The future execution row
binds them. This narrows older Phase 7.1 wording that treated snapshot or target
as an umbrella for mapping state.

## Execution mode and protocol lifecycle

The existing execution-type vocabulary remains exactly:

```text
NORMAL
REPLAY
COUNTERFACTUAL
REFRESH
```

`REPRODUCE` and `RECALCULATE` are operation names, not new persisted modes:
exact reproduction uses `REPLAY`; changed rules use `COUNTERFACTUAL`; changed
inputs use `REFRESH`.

Execution type is excluded from `input_digest` and included once in
`semantic_execution_digest`. It governs which roots may be resolved or reused:

| Mode | Protocol lifecycle rule |
|---|---|
| `NORMAL` | Exact `published` only, effective for the requested normal execution |
| `REFRESH` | Exact `published` only; creates new input/evidence roots |
| `COUNTERFACTUAL` | A version that reached publication; current state may be `published`, `deprecated` or `retired`, subject to explicit governed authorization |
| `REPLAY` | The exact historical version, currently `published`, `deprecated` or `retired`; used for verification, not authorization of a new production conclusion |

`draft`, `scientific_review` and `approved` are never executable. Retraction or
integrity-compromised governance never changes historical bytes; it may block a
new NORMAL/REFRESH and must be reported by replay/counterfactual governance
validation.

## Future execution persistence references

No new table is required for the bounded 7.6.4A runtime: 0019 already provides
immutable, content-addressed artifacts and verified locations. Artifact
allowlist expansion is runtime work for the later implementation checkpoint.

Future migration 0021 MUST include explicit restrictive references for:

```text
protocol_version_id
snapshot_id
target_snapshot_artifact_id
mapping_state_artifact_id nullable only for substance targets
input_artifact_id
configuration_artifact_id
```

Phase 7.6.4B-1 freezes those references and the surrounding
execution/publication schema in `WYE_EXECUTION_PERSISTENCE_FREEZE.md`. It adds a
canonical execution-identity artifact whose content digest is the sole
`semantic_execution_digest`; this does not change the input artifact or fold
protocol/evidence/mode/configuration into `input_digest`.

It also stores `input_digest`, which must equal `input_artifact_id`'s content
digest. Deferred validation must enforce artifact kind/schema, sealed snapshot,
target-type/mapping applicability and root consistency. `mapping_state_artifact_id`
is required for ingredient targets and null for substance targets. These direct
references avoid replay depending on parsing a digest out of an unreferenced
document and preserve FK `ON DELETE RESTRICT` history.

This was a design-time correction to the earlier 0021 logical column list. The
later Phase 7.6.4B-2 migration implements the separately frozen execution
persistence contract without changing this input-digest boundary.

## Golden structural payloads

The examples below are normative field/shape fixtures. Digest strings use
recognizable repeated bytes so relationships are readable. Literal SHA-256
vectors will be generated from these exact envelopes by the implementation
test suite; this documentation-only checkpoint does not claim hand-calculated
hashes.

### Ingredient target

```json
{
  "artifact_kind": "scientific_evaluation_target",
  "canonicalization_version": "wye-c14n-json-v1",
  "payload": {
    "artifact_type": "scientific_evaluation_target",
    "entity_id": 42,
    "identity_as_of": "2026-08-30T12:00:00.000000Z",
    "identity_namespace": "wye_internal_id_v1",
    "identity_recorded_at": "2026-08-01T09:30:00.000000Z",
    "identity_resolution_state": "resolved",
    "identity_state": {
      "canonical_name": "citric acid",
      "common_name": null,
      "declared_identifiers": [
        {"identifier_system": "cas", "value": "77-92-9"}
      ],
      "ingredient_group": "acidulant",
      "status": "active"
    },
    "schema_version": "1",
    "target_type": "ingredient"
  },
  "schema_version": "1"
}
```

### Mapping member with one `applied` authority chain

```json
{
  "artifact_kind": "scientific_mapping_state_member",
  "canonicalization_version": "wye-c14n-json-v1",
  "payload": {
    "artifact_type": "scientific_mapping_state_member",
    "authority_chains": [
      {
        "authority_chain_identity_digest": "1111111111111111111111111111111111111111111111111111111111111111",
        "decision": {
          "created_at": "2026-01-02T10:00:00.000000Z",
          "decision_id": 9001,
          "decision_type": "accept",
          "effective_from": "2026-01-01",
          "provenance": null,
          "reason_code": "identity_verified",
          "reviewed_at": "2026-01-02T10:00:00.000000Z",
          "reviewed_by": "reviewer:example"
        },
        "materialization": {
          "created_at": "2026-01-02T10:01:00.000000Z",
          "materialization_id": 10001,
          "materialization_status": "applied",
          "materialized_at": "2026-01-02T10:01:00.000000Z",
          "materialized_by": "worker:example",
          "provenance": null
        },
        "proposal": {
          "created_at": "2026-01-02T09:00:00.000000Z",
          "ingredient_id": 42,
          "ingestion_run_id": null,
          "mapping_confidence": null,
          "mapping_method": "manual_review",
          "proposal_id": 8001,
          "proposal_key": "11111111-1111-4111-8111-111111111111",
          "proposed_by": "proposer:example",
          "provenance": null,
          "relationship_type": "represents",
          "source_dataset_release_id": null,
          "substance_id": 99
        }
      }
    ],
    "effective_state": {
      "closure": null,
      "mapping_day": "2026-08-30",
      "mapping_status": "accepted",
      "recorded_as_of": "2026-08-30T12:00:00.000000Z",
      "valid_from": "2026-01-01",
      "valid_to": null
    },
    "ingredient_target_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "mapping_policy_key": "ingredient_substance_authoritative_state",
    "mapping_policy_version": "1",
    "member_identity_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "provenance": {
      "ingestion_run_id": null,
      "mapping_method": "manual_review",
      "source_dataset_release_id": null
    },
    "relationship_type": "represents",
    "schema_version": "1",
    "substance_target_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  },
  "schema_version": "1"
}
```

### Same bridge with `applied` and `already_current` chains

The complete member payload is identical to the previous fixture except that
`authority_chains` contains both elements below in this chronological/digest
order. The bridge/member identity fields remain unchanged; the member semantic
artifact digest changes.

```json
[
  {
    "authority_chain_identity_digest": "1111111111111111111111111111111111111111111111111111111111111111",
    "decision": {
      "created_at": "2026-01-02T10:00:00.000000Z",
      "decision_id": 9001,
      "decision_type": "accept",
      "effective_from": "2026-01-01",
      "provenance": null,
      "reason_code": "identity_verified",
      "reviewed_at": "2026-01-02T10:00:00.000000Z",
      "reviewed_by": "reviewer:example"
    },
    "materialization": {
      "created_at": "2026-01-02T10:01:00.000000Z",
      "materialization_id": 10001,
      "materialization_status": "applied",
      "materialized_at": "2026-01-02T10:01:00.000000Z",
      "materialized_by": "worker:example",
      "provenance": null
    },
    "proposal": {
      "created_at": "2026-01-02T09:00:00.000000Z",
      "ingredient_id": 42,
      "ingestion_run_id": null,
      "mapping_confidence": null,
      "mapping_method": "manual_review",
      "proposal_id": 8001,
      "proposal_key": "11111111-1111-4111-8111-111111111111",
      "proposed_by": "proposer:example",
      "provenance": null,
      "relationship_type": "represents",
      "source_dataset_release_id": null,
      "substance_id": 99
    }
  },
  {
    "authority_chain_identity_digest": "2222222222222222222222222222222222222222222222222222222222222222",
    "decision": {
      "created_at": "2026-02-03T10:00:00.000000Z",
      "decision_id": 9002,
      "decision_type": "accept",
      "effective_from": "2026-01-01",
      "provenance": null,
      "reason_code": "independent_confirmation",
      "reviewed_at": "2026-02-03T10:00:00.000000Z",
      "reviewed_by": "reviewer:second"
    },
    "materialization": {
      "created_at": "2026-02-03T10:01:00.000000Z",
      "materialization_id": 10002,
      "materialization_status": "already_current",
      "materialized_at": "2026-02-03T10:01:00.000000Z",
      "materialized_by": "worker:second",
      "provenance": null
    },
    "proposal": {
      "created_at": "2026-02-03T09:00:00.000000Z",
      "ingredient_id": 42,
      "ingestion_run_id": null,
      "mapping_confidence": null,
      "mapping_method": "manual_review",
      "proposal_id": 8002,
      "proposal_key": "22222222-2222-4222-8222-222222222222",
      "proposed_by": "proposer:second",
      "provenance": null,
      "relationship_type": "represents",
      "source_dataset_release_id": null,
      "substance_id": 99
    }
  }
]
```

### Non-member observation and partially resolved mapping-state manifest

```json
{
  "artifact_kind": "scientific_mapping_state_manifest",
  "canonicalization_version": "wye-c14n-json-v1",
  "payload": {
    "artifact_type": "scientific_mapping_state_manifest",
    "as_of": "2026-08-30T12:00:00.000000Z",
    "ingredient_target_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "mapping_day": "2026-08-30",
    "mapping_policy_key": "ingredient_substance_authoritative_state",
    "mapping_policy_version": "1",
    "member_count": 1,
    "non_member_observations": [
      {
        "authority_chain_identity_digest": null,
        "bridge_context": {
          "bridge_id": null,
          "ingredient_id": 42,
          "relationship_type": "contains",
          "substance_id": 100
        },
        "effective_from": null,
        "effective_to": null,
        "observation_kind": "proposal",
        "observation_semantic_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "reason_code": "pending_proposal",
        "recorded_at": "2026-08-01T08:00:00.000000Z",
        "resolution_impact": "extends_set",
        "subject_identity": {
          "bridge_id": null,
          "closure_id": null,
          "decision_id": null,
          "identity_namespace": "wye_internal_id_v1",
          "identity_type": "mapping_non_member_observation_subject",
          "identity_version": "1",
          "materialization_id": null,
          "observation_kind": "proposal",
          "proposal_id": 8100
        },
        "subject_identity_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
      }
    ],
    "observation_count": 1,
    "ordered_members": [
      {
        "member_identity_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "member_semantic_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "relationship_type": "represents",
        "substance_target_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
      }
    ],
    "resolution_reason_codes": [
      "additional_candidates_unresolved",
      "pending_proposal"
    ],
    "resolution_state": "partially_resolved",
    "schema_version": "1"
  },
  "schema_version": "1"
}
```

### Canonical input

```json
{
  "artifact_kind": "scientific_evaluation_input",
  "canonicalization_version": "wye-c14n-json-v1",
  "payload": {
    "artifact_type": "scientific_evaluation_input",
    "domain_inputs": [],
    "input_as_of": "2026-08-30T12:00:00.000000Z",
    "mapping_state": {
      "applicability": "required",
      "manifest_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "resolution_state": "resolved"
    },
    "schema_version": "1",
    "target": {
      "target_artifact_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "target_type": "ingredient"
    }
  },
  "schema_version": "1"
}
```

## Idempotency, concurrency and integrity

Identical canonical target, member, manifest or input bytes converge through
the 0019 UNIQUE artifact identity `(canonicalization_version,
digest_algorithm, content_digest)`. No target/mapping/input UUID or mutable
header row is introduced.

A retry is compatible only when kind, schema, canonicalization, media type,
JSON cache where present and authoritative canonical bytes all match. Same
digest with different bytes/metadata, unavailable authoritative bytes or a
different root graph is an integrity failure. Concurrent writers may race; one
artifact row wins and every other caller verifies/reuses it through the existing
writer contract. No repository may commit the caller transaction.

## Future implementation test plan

### Unit tests

1. Substance and ingredient target payload/golden bytes.
2. Unsupported product target rejection.
3. Mutable labels change target digest but never stable identity namespace/key.
4. Historical target-state availability guard, including rejection of current
   `substance_identifiers` as historical target state.
5. Mapping member identity and relationship-type distinction.
6. Validity range excluded from member identity but included in semantic digest.
7. UTC timestamp-to-DATE boundary, including midnight and offset-equivalent input.
8. Status inclusion matrix and legacy/uncontrolled classifications.
9. Canonical member/observation order and input-order independence.
10. Empty, partially resolved and unavailable manifest states.
11. Mapping manifest and execution-input golden bytes/digests.
12. Root sensitivity to target, mapping state and `as_of`.
13. Evidence snapshot/protocol/mode changes do not change `input_digest`.
14. Semantic-execution fixture changes when snapshot/protocol/mode changes.
15. One bridge with one `applied` and one `already_current` chain remains one
    member, with deterministic authority order and a changed semantic digest.
16. Authority identity and tie-breaking when materialization timestamps match.
17. Observation identity, semantic digest, closed reason vocabulary and order.
18. Exact resolution-state precedence for blocking observation combinations.

### PostgreSQL integration tests

1. Current and historical governed mapping retrieval.
2. Inclusive `valid_from`/`valid_to` dates.
3. Materialization recorded after `as_of` is not historically visible.
4. Closure recorded after `as_of` is not retroactively applied.
5. Pending/ambiguous/rejected/deferred/legacy rows never become members.
6. Controlled accepted/materialized relationship becomes a member.
7. Accepted row without controlled authority produces `partially_resolved` with
   another authoritative member, otherwise `history_unavailable`.
8. Empty mapping with no records versus non-authoritative candidates.
9. All five relationship types remain distinct.
10. Substance target uses mapping `not_applicable`; ingredient requires manifest.
11. Building evidence snapshot rejected by future execution validation; sealed accepted.
12. NORMAL/REFRESH protocol lifecycle versus REPLAY/COUNTERFACTUAL rules.
13. Target/member/manifest/input artifact persistence and exact retry.
14. Concurrent identical artifact creation converges.
15. Canonical bytes/incompatible identity failure.
16. Historical mapping change creates a new root without mutating the old artifact.
17. Caller transaction rollback removes uncommitted artifacts/locations.
18. No dependency on legacy score tables/services.
19. Multiple accepted proposals/materializations on one bridge become one member
    with every valid visible authority chain.
20. Controlled `already_current` adoption of a pre-workflow accepted bridge.
21. New authority after historical `as_of` is excluded and does not rewrite the
    earlier member artifact.
22. `extends_set` with/without a trustworthy member subset produces respectively
    `partially_resolved`/`history_unavailable`.
23. Invalid authority/closure history takes precedence as
    `history_unavailable`.

## Schema sufficiency decision

```text
7.6.4A runtime substrate:
NO SCHEMA EXTENSION REQUIRED

future 0021 execution persistence:
0021 MUST INCLUDE EXPLICIT REFERENCES
```

The existing 0019 artifact registry and verified location writer are sufficient
to implement target, mapping member/manifest and input artifacts. 0020 supplies
the sealed evidence root needed by future execution validation. No mapping or
execution-input table is needed before the bounded runtime.

Authority multiplicity does not change this decision. It is represented inside
canonical member/manifest artifact payloads over existing Phase 6 rows; no new
column, table, uniqueness constraint or migration is required. Phase 6 behavior
and its one-bridge/many-materializations relationship remain unchanged.

The later 0021 design must adopt the explicit FK corrections above before its
migration is implemented. This checkpoint does not create or authorize 0021.

## Explicit boundaries

This freeze introduces no evidence selection, synthesis, projection decision,
execution row, result, replay engine, formula, weight, threshold or numerical
score. Relationship types are preserved data. Legacy scoring remains isolated.
Phase 7.6.4A-2 implements this amended authority/observation contract and is
`COMPLETED + COMMITTED`. The implementation adds only
content-addressed target, mapping member/manifest and evaluation-input artifacts,
plus bounded sealed-snapshot/protocol prerequisite validation. It creates no
migration, execution/result row, product target or scientific scoring behavior.
