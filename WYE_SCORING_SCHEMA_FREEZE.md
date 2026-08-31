# WYE — Canonicalization, Persistence Schema and Publication Protocol Freeze

## Status and decision

This document is the canonical Phase 7.6.1 technical freeze. It makes the
Phase 7.6 persistence architecture implementable without changing any
scientific semantic contract from Phases 7.0–7.5.

```text
FINAL DECISION: READY FOR MIGRATION IMPLEMENTATION
first checkpoint: Phase 7.6.2A / 0019_scientific_evaluation_foundation
snapshot checkpoint: Phase 7.6.2B-1 design frozen
snapshot implementation: Phase 7.6.2B-2 IMPLEMENTED + VALIDATED
canonical artifact runtime: Phase 7.6.3A COMPLETED + COMMITTED
snapshot runtime: Phase 7.6.3B COMPLETED + COMMITTED
mapping/input checkpoint: Phase 7.6.4A-1 DESIGN FROZEN — READY FOR IMPLEMENTATION
authority amendment: Phase 7.6.4A-1B AUTHORITY MULTIPLICITY AMENDMENT FROZEN
mapping/input runtime: Phase 7.6.4A-2 COMPLETED + COMMITTED
```

Each decision authorizes only its bounded migration checkpoint. The 7.6.2B-1
freeze does not itself create 0020, authorize a scientific engine or approve any
score, formula, weight, threshold, exposure model or risk model.

Phase 7.6.1 audited baseline:

```text
Git:                    0a3d912725dcc4cafac457c6fa11cb11e242a965
Alembic repository:     0018_scientific_batch_recovery
local database:         0017_ingredient_mapping_history
```

Phase 7.6.2B-1 design-review baseline:

```text
branch:                 ingredients_score
Git HEAD:               0ea3a26283f617e5cc07e7ad83c04c7fa20a67af
origin/ingredients_score: 48a0681e7e928bec47441d468c86f20784d00ea5
Alembic repository:     0019_scientific_evaluation_foundation
local database:         0017_ingredient_mapping_history
```

## Canonical serialization freeze

### Profile identity

The first profile is:

```text
wye-c14n-json-v1
media type: application/vnd.wye.scientific+json
encoding: UTF-8 without BOM
digest: SHA-256 over the exact canonical UTF-8 bytes
```

It is a WYE profile rather than an unqualified claim of RFC 8785 compliance,
because scientific decimal values are strings with schema-declared decimal
semantics rather than IEEE-754 JSON numbers.

Every canonical document has this top-level shape:

```json
{
  "artifact_kind": "...",
  "canonicalization_version": "wye-c14n-json-v1",
  "payload": {},
  "schema_version": "..."
}
```

The complete object is canonicalized and hashed. `artifact_kind`,
`schema_version` and `canonicalization_version` therefore cannot be changed
without changing the digest.

### Object, string and scalar rules

| Type | Frozen rule |
|---|---|
| Object keys | Normalize keys to Unicode NFC, reject duplicate keys after normalization, then sort ascending by unsigned lexicographic UTF-8 byte order |
| Arrays | Preserve order where order is semantic; schema-declared sets are sorted by canonical element bytes, with exact duplicate elements rejected unless the schema explicitly allows multiplicity |
| Whitespace | No bytes outside JSON string content: no spaces, tabs or line breaks between tokens |
| Strings | Unicode NFC; reject unpaired surrogates and non-Unicode scalar values; encode directly as UTF-8 |
| Escaping | Escape `"` and `\\`; encode every U+0000–U+001F control as lowercase six-byte `\u00xx`; do not escape `/` or other Unicode scalars |
| Boolean | Lowercase JSON literals `true` and `false` only |
| Null | JSON `null`, allowed only for schema-nullable fields |
| Missing | Omitted field; never equivalent to explicit `null` |
| Integer | Signed 64-bit JSON number in base 10, optional leading `-`, no `+`, no leading zero except `0`, no decimal point/exponent; `-0` forbidden; parsers must not pass through binary float |
| Scientific decimal | JSON string using the canonical decimal grammar below; never a JSON floating-point number |
| Date | String `YYYY-MM-DD`, Gregorian calendar, valid calendar date only |
| Datetime | String UTC form `YYYY-MM-DDTHH:MM:SS.ffffffZ`, exactly six fractional digits |
| UUID | Lowercase RFC 4122 hyphenated string `8-4-4-4-12`; braces and uppercase forbidden |
| Enum/reason code | Exact lowercase ASCII identifier declared by an explicit vocabulary/schema version |
| Bytes | Base64url string without padding, only in fields declared `format: base64url`; bulk canonical bytes belong in the artifact body/storage layer |

Canonical object keys and canonical schema field names are ASCII. NFC is still
applied defensively. Locale-sensitive sorting, number parsing, case conversion
and date formatting are forbidden.

### Numeric canonicalization

Scientific decimal values use this canonical grammar:

```text
0
-?[1-9][0-9]*
-?(0|[1-9][0-9]*)\.[0-9]*[1-9]
```

Rules:

- parse source values with an arbitrary-precision decimal implementation;
- prohibit binary floating-point input at the canonicalization boundary;
- remove a leading `+`, leading integer zeros and trailing fractional zeros;
- omit the decimal point when the fractional part becomes empty;
- expand exponent notation to ordinary decimal notation;
- normalize positive and negative zero to `"0"`;
- reject `NaN`, positive/negative infinity and values outside the field's
  schema-declared precision/scale limit;
- no global precision truncation or rounding is allowed;
- if significant figures, reported scale or source lexical form matter, persist
  them in separate explicit fields such as `reported_scale`,
  `significant_digits` and `raw_value`.

Consequently, semantic decimal inputs `1`, `1.0`, `1.00` and `1e0` all encode as
the JSON string `"1"`. A schema integer with value one encodes as JSON number
`1`; integer and decimal types remain distinct because the schema is part of the
hashed document.

### Date and time canonicalization

- `DATE` is a real calendar date formatted `YYYY-MM-DD`.
- Canonical datetime precision is PostgreSQL-compatible microseconds, exactly
  six digits; lower-precision inputs are right-padded with zeros.
- An aware offset input is converted to UTC before serialization.
- `+00:00` is serialized as `Z`; all other offsets disappear after conversion.
- Naive datetime, named-zone-only datetime, leap second `:60` and precision
  beyond microseconds are rejected rather than guessed or rounded.
- Audit `created_at` values are generally envelope metadata excluded from
  semantic payloads. Scientific `as_of`, cutoff and effective times are payload
  fields and therefore canonicalized.

### Version evolution

An algorithm, sorting, encoding, type or normalization change requires a new
identifier such as `wye-c14n-json-v2`. Historical bytes and digests always use
their recorded version. No migration may reserialize or reinterpret a published
v1 artifact in place.

## Digest and encoding freeze

### Algorithm and representation

```text
algorithm identifier: sha256
database representation: BYTEA, exactly 32 bytes
document/log/API representation: 64 lowercase hexadecimal characters
```

Base64 is not used for semantic digest presentation. Database constraints check
`digest_algorithm = 'sha256'` and `octet_length(digest) = 32`. Digest fields in
canonical JSON are lowercase hex strings.

### Final acyclic digest graph

```text
protocol_digest

member payload digests + query-definition digest + frozen evidence provenance
    -> snapshot_digest

target artifact + mapping/composition/scenario roots
    -> input_digest

protocol_digest + snapshot_digest + input_digest + execution_type
    + configuration artifact + comparison semantic digest/null
    -> semantic_execution_digest

snapshot members + protocol_digest + question/context
    -> selection_digest

selected decision/line digests
    -> comparison_group_digest[]
    -> endpoint_synthesis_digest[]
    -> substance_profile_digest[]

substance_profile_digest + mapping_snapshot_digest
    -> ingredient_projection_digest[]

product_composition_snapshot_digest + exposure_scenario_digest
    + ingredient_projection_digest[]
    -> exposure_readiness_digest[]
    -> product_assessment_digest[]

typed component digests
    -> result_digest

protocol/snapshot/selection/result and causal edge content
    -> trace_digest

projection row semantic manifest
    -> projection_manifest_digest

execution semantic digest + selection/result/trace/projection roots
    -> publication_bundle_digest
```

`result_digest` never includes `trace_digest`; the trace may include
`result_digest`, and the publication bundle includes both. This removes the only
potential cycle.

### Digest boundary table

| Digest | Canonical input and children | Excluded | Purpose |
|---|---|---|---|
| `protocol_digest` | Published protocol-version artifact including policy/vocabulary references | DB id, publish audit time | Executable rule identity |
| `snapshot_digest` | Query definition, as-of/cutoff, ordered evidence-member payload digests and frozen evidence provenance | Mapping state, target state, protocol, DB ids except stable evidence keys, build time | Exact candidate universe |
| `input_digest` | Target artifact and mapping/composition/scenario artifacts applicable to execution; v1 is target plus mapping state | Evidence snapshot, protocol, configuration, mode, request key, worker/time | Frozen non-protocol, non-evidence domain input root |
| `selection_digest` | Protocol, snapshot, question/context and canonically ordered decision digests | presentation text, row order | Exact selected/excluded universe |
| `comparison_group_digest` | Group identity, evidence-line/dependency digests | query projection ids | Comparable line identity |
| `endpoint_synthesis_digest` | Endpoint identity, group roots, multidimensional synthesis payload | UI labels | Endpoint result proof |
| `substance_profile_digest` | Ordered endpoint roots plus substance identity/context | current substance name | Substance profile proof |
| `mapping_snapshot_digest` | Frozen authoritative effective members plus canonical empty/partial/unavailable observations and validity/provenance | Current mapping state, scoring interpretation | Historical mapping proof |
| `ingredient_projection_digest` | Ingredient/relationship/mapping root, substance profile roots and projection decisions | product state | Ingredient projection proof |
| `product_composition_snapshot_digest` | Frozen product identity, ingredients/order, quantities, serving/label provenance | current product row | Product input proof |
| `exposure_scenario_digest` | Scenario scientific fields, provenance class and explicit assumptions | user identity and secret configuration | Scenario identity |
| `exposure_readiness_digest` | Composition/projection/scenario roots and readiness reasons | runtime failure | Exposure computability proof |
| `product_assessment_digest` | Product, projection, readiness and risk-computability components | legacy score | Product assessment proof |
| `result_digest` | Result kind/status and ordered typed component digests | trace, projection rows, audit time | Canonical result root |
| `trace_digest` | Causal node/edge graph and all relevant roots including result | AI prose, UI, worker logs | Canonical explanation proof |
| `projection_manifest_digest` | Canonically sorted query-projection semantic rows | surrogate ids/index details | Detect/rebuild projection drift |
| `publication_bundle_digest` | Execution semantic root and selection/result/trace/projection roots | publish time/request key | Atomic publication identity |

All rows use `wye-c14n-json-v1` and SHA-256 for v1. Component-specific named
digests are content digests of their canonical artifact or subdocument; they are
not separately hashed aliases.

## Canonical artifact envelope and placement

### Canonical versus external metadata

The canonical content is the top-level JSON document described above. Registry
metadata is outside that content:

```text
artifact_kind, schema_version, canonicalization_version
digest_algorithm, content_digest
content_length, content_type, json_payload
created_at, verified_at

location metadata:
storage_mode, canonical_bytes/storage_object_id, location timestamps/state
```

The duplicated kind/schema/version columns must equal the values inside the
verified canonical bytes. `created_at`, `verified_at`, storage location,
compression and encryption metadata do not enter the content digest.

Artifact identity and physical location are separate. Relocation or an
additional replica inserts a new immutable location row; it never updates the
artifact identity or removes a still-referenced verified location.

### Placement policy

| Artifact | Default | JSONB copy | Reason / expected behavior |
|---|---|---|---|
| Protocol definition/review metadata | Inline canonical bytes | Required | Small, governance/query-heavy, replay-critical |
| Configuration/target identity/scenario | Inline canonical bytes | Required | Small structured payload; scenario access may be restricted |
| Individual selection decision | Relational row plus inline fragment artifact only when needed | Optional | Query-critical columns normalized; canonical selection root covers set |
| Selection manifest | Hybrid, object by default when large | Optional | Size follows candidate count; replay requires full manifest |
| Snapshot query definition | Inline canonical bytes | Required | Small and audit/query relevant |
| Snapshot/member manifest | Object storage | Optional | Potentially large; explicit member rows serve queries |
| Mapping/product-composition manifest | Hybrid | Optional | Size varies; replay critical |
| Primary result root | Inline canonical bytes | Required | Small root over typed component digests |
| Endpoint/profile/projection components | Hybrid | Optional | Multidimensional and variable size; typed projections serve queries |
| Explanation trace | Object storage | No by default | Potentially large graph; compact relational index serves traversal |
| Publication/projection manifest | Inline canonical bytes | Required | Small atomic root and verification material |

There is no schema-level byte threshold. Artifact-kind policy selects a default;
an operational configurable spill threshold may choose object storage only for
artifact kinds marked hybrid. Storage relocation leaves canonical bytes and
digest unchanged.

## Frozen logical schema

The types below are logical PostgreSQL types ready to translate into Alembic.
All canonical-history foreign keys use `ON DELETE RESTRICT` unless explicitly
stated otherwise.

### `scientific_evaluation_artifacts` and locations

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `artifact_kind` | `VARCHAR(80) NOT NULL`, lowercase snake-case CHECK |
| `schema_version` | `VARCHAR(50) NOT NULL`, nonempty |
| `canonicalization_version` | `VARCHAR(50) NOT NULL`, initially CHECK `wye-c14n-json-v1` |
| `digest_algorithm` | `VARCHAR(20) NOT NULL`, initially CHECK `sha256` |
| `content_digest` | `BYTEA NOT NULL`, length 32 CHECK |
| `content_length` | `BIGINT NOT NULL CHECK >= 0` |
| `content_type` | `VARCHAR(100) NOT NULL`, v1 media-type CHECK |
| `json_payload` | `JSONB`, optional verified parsed cache, object-shaped when present |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` |
| `verified_at` | `TIMESTAMPTZ NOT NULL` |

UNIQUE `(canonicalization_version, digest_algorithm, content_digest)`. The
canonical document includes kind/schema, so byte-identical content is safe to
deduplicate globally.

`scientific_evaluation_artifact_locations`:

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `location_key` | `UUID NOT NULL UNIQUE` |
| `artifact_id` | NOT NULL FK artifact RESTRICT |
| `storage_mode` | CHECK `inline, object` |
| `canonical_bytes` | required only for inline; byte length must equal artifact length |
| `storage_object_id` | nullable FK `storage_objects`, required only for object mode |
| `location_status` | query projection CHECK `verified, quarantined, unavailable, retired`; initially verified |
| `created_at`, `verified_at` | audit timestamps; verified time required for verified state |

The mutually exclusive inline/object CHECK is on locations. UNIQUE
`(artifact_id, storage_object_id)` when the object reference is present prevents
duplicate locators. A deferred constraint trigger requires at least one verified
location before an artifact may be referenced by a published/sealed owner.
Cross-table checksum/size verification remains a pre-insert service invariant.
Artifact identity and locator/content fields are immutable. `location_status`
may change only through a governed transaction that appends an artifact-location
event and performs a valid one-way transition; it is a current-state projection,
not history.

### Protocol tables

`scientific_evaluation_protocols`:

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `protocol_key` | `VARCHAR(100) NOT NULL UNIQUE`, lowercase snake-case |
| `domain_key` | `VARCHAR(100) NOT NULL` |
| `target_entity_type` | `VARCHAR(30) NOT NULL` |
| `governance_owner` | `VARCHAR(255) NOT NULL` |
| `created_by` | `VARCHAR(255) NOT NULL` |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` |

The family identity fields are immutable after the first version is published.
Owner change is governance-event driven and updates only the query projection.

`scientific_evaluation_protocol_versions`:

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `protocol_id` | FK to protocol, NOT NULL |
| `semantic_version` | `VARCHAR(50) NOT NULL`, structural SemVer CHECK; full SemVer 2.0 validation before insert |
| `lifecycle_status` | CHECK in `draft, scientific_review, approved, published, deprecated, retired` |
| `canonical_artifact_id` | nullable until approved; FK artifact |
| `protocol_digest` | nullable until approved; 32-byte SHA-256 |
| `review_artifact_id` | nullable FK artifact |
| `effective_from` | nullable `DATE` |
| `created_by` | nonempty actor |
| `created_at` | audit timestamp |
| `published_at` | required from `published` onward |
| `retired_at` | required only for `retired` |

UNIQUE `(protocol_id, semantic_version)` and, when non-null, UNIQUE
`(protocol_id, protocol_digest)`. Digest must equal the referenced artifact.
Supersession/retraction is represented by governance events, not a mutable
successor pointer.

State CHECKs require artifact and digest to be both null or both non-null;
`approved` and later require canonical/review artifacts and digest; `published`
and later require `published_at`; only `retired` permits/requires `retired_at`.
The DB structural SemVer expression accepts `major.minor.patch` plus optional
prerelease/build sections without leading zeros in the three core integers; the
service applies the complete SemVer 2.0 identifier rules.

Lifecycle is linear:

```text
draft -> scientific_review -> approved -> published -> deprecated -> retired
```

`lifecycle_status` is a query projection updated only by a governed service
transaction that inserts the corresponding event. Published semantic columns,
artifact and digest are trigger-protected. Deprecation/retirement changes only
lifecycle projection and event history; historical use remains valid.

### `scientific_evaluation_governance_events`

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `event_key` | `UUID NOT NULL UNIQUE`, generated by application |
| `entity_type` | CHECK in `protocol, protocol_version, artifact, artifact_location, execution, publication` |
| entity FK | exactly one of `protocol_id`, `protocol_version_id`, `artifact_id`, `artifact_location_id`, `execution_id`, `publication_id`, matching `entity_type` |
| `event_type` | CHECK in `submitted_for_review, approved, published, deprecated, retired, supersedes, retracts, integrity_compromised, annotation, review_disposition` |
| `predecessor_event_id` | nullable self-FK RESTRICT for ordered governance chain |
| related entity FKs | nullable second concrete FK set for a predecessor/supersession target; exactly one required for `supersedes`, otherwise protocol-defined |
| `actor_identifier` | `VARCHAR(255) NOT NULL`, authenticated non-secret identity |
| `reason_code` | `VARCHAR(100) NOT NULL` |
| `rationale_artifact_id` | nullable FK artifact |
| `metadata` | nullable object JSONB, noncanonical/non-secret audit metadata |
| `effective_at`, `created_at` | aware audit timestamps |

Exactly-one-FK checks preserve referential integrity without an unsafe generic
`entity_id`. Related FKs must match the governed entity type and cannot equal the
governed row. Rows are append-only. A deferred acyclic-lineage constraint trigger
rejects self/cyclic supersession.

Revision 0019 initially permits protocol, protocol-version, artifact and
artifact-location events and therefore creates those four concrete FKs.
Revision 0021 adds
execution/publication FKs and expands the entity/event CHECKs after those parent
tables exist. No temporarily unenforced polymorphic reference is allowed.

### `scientific_evidence_snapshots`

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `snapshot_key` | `UUID NOT NULL UNIQUE` |
| `snapshot_policy_key` | `VARCHAR(100) NOT NULL`, lowercase snake-case |
| `snapshot_policy_version` | `VARCHAR(50) NOT NULL`, nonempty version |
| `as_of`, `evidence_cutoff` | canonical `TIMESTAMPTZ NOT NULL`; cutoff cannot exceed `as_of` |
| `query_definition_artifact_id` | NOT NULL FK artifact |
| `canonicalization_version` | `VARCHAR(50) NOT NULL`, initially `wye-c14n-json-v1` |
| `digest_algorithm` | `VARCHAR(20) NOT NULL`, initially `sha256` |
| `manifest_artifact_id` | nullable while building, required when sealed |
| `snapshot_digest` | nullable while building, exactly 32 bytes when sealed |
| `member_count` | nullable while building; `BIGINT >= 0` and required when sealed |
| `status` | CHECK `building, sealed` |
| `created_by`, `sealed_by` | non-secret actor/build identity; `sealed_by` required when sealed |
| `created_at`, `sealed_at` | audit timestamps with state-consistency CHECK |

There is deliberately no `protocol_version_id`: snapshot policy freezes the
technical candidate universe, while protocol selection is execution-specific.
This preserves exact counterfactual reuse of one historical universe under a
different protocol. The execution links snapshot and protocol version.

The partial semantic identity is UNIQUE on
`(canonicalization_version, digest_algorithm, snapshot_digest)` when sealed.
`snapshot_key` is a stable public/operational identifier, not scientific
identity. Two equivalent builders may temporarily have different building rows,
but two sealed rows cannot represent the same canonical universe.

### `scientific_evidence_snapshot_members`

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `snapshot_id` | NOT NULL FK snapshot |
| `member_kind` | initially CHECK `finding, assessment` |
| `finding_id` | nullable FK finding; required for `finding` |
| `assessment_id` | NOT NULL FK assessment context |
| `ingestion_run_id` | NOT NULL FK ingestion run |
| `source_dataset_release_id` | NOT NULL FK source dataset release |
| `member_identity_digest` | 32-byte digest of the frozen candidate identity |
| `member_payload_artifact_id` | NOT NULL FK canonical frozen member payload |
| `member_semantic_digest` | 32-byte SHA-256, equals payload artifact digest |
| `membership_ordinal` | `INTEGER NOT NULL CHECK >= 0` |
| `status_as_of` | nonempty normalized status |
| `created_at` | audit timestamp |

UNIQUE `(snapshot_id, membership_ordinal)` and `(snapshot_id,
member_identity_digest)` plus partial UNIQUE `(snapshot_id, finding_id)` for
finding members and `(snapshot_id, assessment_id)` for assessment-only members
prevent duplicate insertion of the same persisted candidate. There is
deliberately no uniqueness rule on `member_semantic_digest`: duplicate
ingestion, two source records referring to the same study, and dependent
evidence remain distinct candidate representations until protocol-specific
selection/dependency handling. Artifact-level byte deduplication is allowed;
scientific deduplication is not performed by snapshot persistence.

All semantic fields needed for replay live in the member payload; FKs alone are
explicitly insufficient. A singular release-artifact FK is not stored because
one ingestion run can consume an ordered artifact manifest. Direct provenance
remains traversable through
`scientific_ingestion_run_artifacts -> scientific_release_artifacts`, and that
exact manifest is also committed in the canonical member payload.

## Phase 7.6.2B-1 evidence snapshot design freeze

### Normative definition and boundary

A **scientific evidence snapshot** is a sealed, protocol-independent,
content-addressed materialization of the technically available scientific
candidate universe resolved under one versioned snapshot policy, one `as_of`
boundary and one scientific `evidence_cutoff`. It freezes both exact candidate
membership and the semantic/provenance payload required to interpret every
candidate historically.

It includes:

- scientific finding identity and content, with mandatory assessment context;
- assessment-only candidates only where the assessment itself is the atomic
  source record and no finding represents that candidate;
- the evidence-linked substance identity fragment and identifier/status state
  required to interpret that assessment at snapshot time;
- ingestion representation, parser/normalization/acquisition versions, source
  release identity and the exact ordered run-artifact provenance manifest;
- canonical query definition, snapshot policy, `as_of`, cutoff, ordered member
  descriptors, counts and digests.

It does **not** include:

- protocol eligibility, applicability, inclusion/exclusion, dependency
  resolution or selected evidence;
- endpoint synthesis, hazard interpretation, result or explanation trace;
- evaluation target identity;
- ingredient-to-substance mapping state, product composition, exposure scenario
  or any current-state alias;
- scoring formula, weight, threshold, source precedence or numerical score.

The evidence-linked substance fragment answers “which scientific identity did
this persisted evidence describe?” It does not replace the independently frozen
evaluation target and it does not freeze ingredient mapping. Therefore the
reproducibility boundary remains:

```text
sealed evidence snapshot
+ separately frozen target/mapping/composition/scenario inputs as applicable
+ published protocol version
= canonical execution input
```

Earlier 7.1 text that used “evidence snapshot” as shorthand for the entire
execution input, including mapping state, is narrowed by this persistence
freeze. This is a boundary clarification, not a merger or silent change:
mapping remains a distinct canonical execution input.

### Candidate granularity

`finding` is the normal atomic candidate. `assessment` is always mandatory
context for a finding. An `assessment` member is permitted only when the
assessment-level record is itself the atomic evidence/status/recommendation
candidate and no finding represents it. The base v1 snapshot policy forbids an
assessment-only member and finding members from the same assessment in one
snapshot; any future relaxation requires a new snapshot-policy version and a
non-overlapping candidate-role definition.

Assessments, releases, ingestion runs, datasets, sources and raw artifacts are
not additional member kinds merely because they are provenance nodes. This
avoids counting one scientific candidate several times. Assessment rows with no
candidate content may remain provenance-only and need not become members. A
sealed zero-member snapshot is valid and represents an empty candidate universe,
not danger, safety or technical failure.

### Canonical artifacts and snapshot digest

Revision 0020 will reuse the 0019 artifact registry for three authoritative
artifact kinds:

| `artifact_kind` | `schema_version` | Role |
|---|---|---|
| `scientific_evidence_snapshot_query` | `1` | canonical construction scope/policy |
| `scientific_evidence_snapshot_member` | `1` | one frozen candidate representation |
| `scientific_evidence_snapshot_manifest` | `1` | sealed snapshot root |

All three use content type `application/vnd.wye.scientific+json`,
canonicalization `wye-c14n-json-v1` and digest algorithm `sha256`.

The query artifact freezes scope, technical inclusion policy and versioned
construction parameters. Each member artifact freezes the stable source/run/
record identity, assessment/finding content, evidence-linked substance state,
status-as-of and the complete provenance/version manifest. The snapshot manifest
freezes policy, `as_of`, cutoff, query digest and canonically ordered member
descriptors.

The minimum canonical payload shapes are:

```text
query/v1:
  artifact_type, schema_version, snapshot_policy_key,
  snapshot_policy_version, as_of, evidence_cutoff, scope,
  technical_predicates, canonicalization_version

member/v1:
  artifact_type, schema_version, member_kind, candidate_identity,
  assessment_context, finding_content when applicable,
  evidence_linked_substance_identity, status_as_of, provenance

manifest/v1:
  artifact_type, schema_version, snapshot_policy_key,
  snapshot_policy_version, as_of, evidence_cutoff,
  query_definition_digest, ordered_members[], member_count
```

`scope` and `technical_predicates` are typed canonical objects, never stored SQL
or unconstrained executable text. The member descriptor in `ordered_members`
contains member kind, identity digest and semantic digest; the full payload is
resolved through the member artifact.

The canonical `member_identity_digest` is SHA-256 over a
`wye-c14n-json-v1` identity object containing `member_kind` and stable
source/dataset/release/run/assessment/finding keys. Finding identity fallback is
deterministic: source finding key, else source ordinal, else verified finding
fingerprint, else the digest of the frozen finding payload, always namespaced by
run and assessment source-record identity. It never relies on a database PK
alone. The ingestion run key is included, so a later reprocessing is a distinct
candidate representation even when normalized scientific values are unchanged.

`snapshot_digest` MUST equal the content digest of
`manifest_artifact_id`; `member_semantic_digest` MUST equal the content digest
of `member_payload_artifact_id`. All referenced canonical artifacts must have a
verified location before seal. The database stores SHA-256 as 32-byte `BYTEA`;
documents/API use lowercase 64-character hexadecimal.

Database PKs, row insertion order, runtime timestamps, worker identity,
presentation metadata and physical storage locations are excluded from
canonical payloads. Stable source/dataset/release/run/record keys and referenced
artifact digests are included. Canonical member ordering is the bytewise order
of the `wye-c14n-json-v1` tuple:

```text
[member_kind, lowercase(member_identity_digest), lowercase(member_semantic_digest)]
```

`membership_ordinal` records that zero-based contiguous order. The same logical
set therefore yields the same manifest and digest independently of query or
insertion order. Duplicate tuple identities are rejected; semantically related
or scientifically duplicate-but-distinct candidate records are retained.

### Referential and provenance invariants

Every canonical FK introduced by 0020 uses `ON DELETE RESTRICT`:

| Child | Parent | Delete action |
|---|---|---|
| snapshot query/manifest | `scientific_evaluation_artifacts` | RESTRICT |
| member | snapshot | RESTRICT |
| member finding | `scientific_assessment_findings` | RESTRICT |
| member assessment | `scientific_assessments` | RESTRICT |
| member ingestion run | `scientific_ingestion_runs` | RESTRICT |
| member source release | `source_dataset_releases` | RESTRICT |
| member payload | `scientific_evaluation_artifacts` | RESTRICT |
| governance snapshot reference | snapshot | RESTRICT |

A deferred consistency trigger validates before commit that a finding belongs to
the member assessment, the assessment belongs to the recorded ingestion run and
release, and the ingestion run belongs to that release. It also validates the
member-kind shape and the no-parent-plus-children rule. Source and dataset remain
directly traversable through the release. Raw artifacts remain directly
traversable through the ingestion-run artifact membership. Their stable keys,
checksums/digests and version fields are additionally materialized inside the
member artifact so later mutable descriptive fields cannot change replay.

The reference/materialization rule is:

| Input | Relational reference | Canonical materialization |
|---|---|---|
| finding/assessment | restrictive FK | stable keys, status-as-of and complete semantic fields |
| substance/identifiers | traversable through assessment/current registry | evidence-linked identity fragment and identifier state used by the candidate |
| ingestion run | restrictive FK | run key, importer/adapter/parser/normalization versions and checksums |
| release/dataset/source | release FK and existing parent chain | stable logical keys, scientific dates/status-as-of and source identity |
| raw release artifacts | existing run-artifact membership | ordered artifact keys, roles, checksums/digests and lengths |
| ingredient mapping/target/product/scenario | none in snapshot membership | none; separate future canonical execution inputs |

The relational references provide efficient traversal and deletion protection;
the canonical copy proves historical semantics. Neither substitutes for the
other.

### Lifecycle and immutability

The only lifecycle states are:

```text
building -> sealed
```

`draft` is redundant with `building`; `finalized` is the semantic name for
`sealed`; `invalidated` is not a mutable lifecycle state. Snapshot policy,
cutoff/as-of, canonicalization/digest algorithm, query artifact, public key and
creation audit are immutable from row creation. Members may be inserted,
replaced or removed only while the parent is building. Seal is a single atomic
transition that sets manifest, digest, count, sealer and `sealed_at`.

After seal:

- the snapshot row and every member are UPDATE/DELETE protected;
- membership, ordinal, metadata, digest and canonical artifacts cannot change;
- no member can be inserted;
- the snapshot cannot be deleted;
- scientific correction creates a new snapshot; the old snapshot remains
  historically reachable.

An unreferenced building snapshot is noncanonical construction state and may be
cleaned up only after its members are explicitly removed. No CASCADE is used.

Snapshot integrity/supersession is represented by append-only governance rather
than mutation. Revision 0020 extends the 0019 concrete governance model with
`evidence_snapshot`, `snapshot_id` and `related_snapshot_id`, both real FKs with
RESTRICT, and updates the exactly-one, related-entity and acyclic-lineage checks.
Ordinary deterministic sealing does not require a governance event. Later
`integrity_compromised`, `retracts`, `supersedes` or `annotation` events may
qualify current use without rewriting the sealed universe.

Historical evidence later superseded, withdrawn, rejected or corrected remains
in every already sealed snapshot. A newer technical universe normally retains
the still-traversable old candidate with its frozen/current-as-of lifecycle state
and adds the corrected representation when it falls inside the new boundaries;
protocol eligibility later decides whether either participates. Only an
explicitly versioned technical snapshot-policy rule may omit an unavailable or
structurally invalid record. Current scientific eligibility never rewrites or
silently filters historical membership.

### Relationship to 0019 and later execution

The 0019 artifact registry owns canonical query/member/manifest bytes and their
verified inline/object locations; location rows never define snapshot identity.
Protocol families and protocol versions are deliberately not referenced by a
snapshot. One sealed evidence universe may be evaluated under multiple protocol
versions for counterfactual analysis. The generic append-only governance table
is extended only because snapshot integrity/supersession is a real governed
relationship with concrete FKs.

No execution FK, selection decision, result or trace is introduced by 0020. A
later execution binds exactly one sealed evidence snapshot to a published
protocol version plus separately frozen target and mapping/composition/scenario
roots. That later binding, not the snapshot, defines the scientific question and
selection context.

### Transaction and concurrency model

Construction follows:

```text
create immutable building header
-> resolve and write/reuse canonical member artifacts
-> insert candidate membership
-> prepare canonical manifest bytes
-> lock snapshot FOR UPDATE
-> re-read and validate the exact canonical member set
-> write/reuse and verify manifest artifact
-> bind manifest/digest/count and transition to sealed
-> commit
```

Member-mutation triggers lock/check the parent snapshot. The finalizer's row
lock therefore serializes against concurrent membership changes. The deferred
seal validator checks verified artifact locations, digest equality, actual
member count, contiguous canonical ordinals, referential consistency and the
complete sealed-state shape. It also checks that query, member and manifest FKs
resolve to the frozen artifact kinds/schema versions and that their
canonicalization/digest algorithms match the snapshot header. Service code
constructs canonical bytes; database constraints/triggers protect identity and
history rather than reimplementing the serializer in PL/pgSQL.

Two workers may build the same universe. The partial UNIQUE semantic identity
allows only one sealed `(canonicalization_version, digest_algorithm,
snapshot_digest)`. The loser may return the winner only after verifying manifest
bytes, policy, cutoff/as-of and every canonical root; otherwise it reports an
integrity conflict. Retry after rollback creates no canonical state. A digest
matching different bytes is a cryptographic integrity failure, never an
idempotent success. PostgreSQL remains final authority; advisory locks may reduce
work but are not correctness controls.

### Future 0020 downgrade and preflight

Downgrade `0020 -> 0019` is allowed only when snapshot tables contain no rows
and no governance event references a snapshot. Building rows count as data.
Draft construction is still information and is not silently deleted. Snapshot
artifacts already registered by 0019 may remain as representable, immutable
artifact rows after an otherwise safe empty downgrade. A permitted downgrade
must remove the snapshot governance columns/check expansions and restore the
exact 0019 governance functions/constraints before dropping the two snapshot
tables.

Before DDL, 0020 must reject collisions for every proposed table, index,
constraint, function and trigger. It must also verify that the 0019 governance
table, constraints and trigger functions have the exact expected foundation
shape before extending them. No PostgreSQL ENUM is created. Preflight runs
before the first schema mutation so an incompatible database cannot be left with
a partial snapshot foundation.

### 0020 migration and integration test plan

The implementation checkpoint must cover at least:

1. fresh chain through 0020 and representative `0019 -> 0020` upgrade;
2. empty downgrade and refusal for building, member, sealed or snapshot-
   governance history;
3. exact table/column/PK/FK RESTRICT/CHECK/UNIQUE/index shape;
4. digest byte length, algorithm/canonicalization and sealed-state checks;
5. finding/assessment shape, provenance consistency and no-parent-plus-children;
6. duplicate persisted-candidate rejection without collapsing distinct
   reingestions or dependent evidence;
7. unordered insertion converging to identical canonical manifest/digest;
8. zero-member sealed snapshot;
9. query/member/manifest artifact verification and digest equality;
10. snapshot/member UPDATE and DELETE rejection after seal;
11. concurrent identical builders, one canonical sealed identity and verified
    loser convergence;
12. concurrent finalization versus member insert/update/delete serialization;
13. retry after rollback and explicit incompatible/digest-collision failure;
14. append-only snapshot governance, related-entity consistency and lineage
    cycle rejection;
15. superseded/withdrawn/corrected source evidence remaining traversable from a
    historical sealed snapshot;
16. collision preflight for tables, indexes, constraints, functions and
    triggers before partial DDL;
17. Phase 6 provenance/data preservation and all 0019 foundation invariants;
18. absence of dependencies on `product_scores`, `ingredient_risk_profiles` or
    `ingredient_evidence` and unchanged legacy behavior.

No 0020 test may require a scientific selection, execution, result or score.

### Target identity freeze

No dedicated target table is required. The initial execution persistence stores:

```text
target_type
target_logical_key
target_current_row_id (nullable traversal hint, no polymorphic FK)
target_snapshot_artifact_id
mapping_state_artifact_id (nullable only for substance)
input_artifact_id
```

The target artifact is authoritative. Phase 7.6.4A-1 v1 supports exactly
`substance` and `ingredient`; `product` requires a later replay-safe
composition/scenario freeze and a new artifact schema version. The current row
id is excluded from `input_digest`; it is only a traversal hint. Mapping state
is a separate canonical root and is never embedded in the target or evidence
snapshot artifact.

### `scientific_evaluation_executions`

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `execution_key` | `UUID NOT NULL UNIQUE` |
| `protocol_version_id` | NOT NULL FK published protocol version |
| `snapshot_id` | NOT NULL FK sealed snapshot |
| `target_type` | CHECK initially `substance, ingredient`; product deferred to a later schema checkpoint |
| `target_logical_key` | `VARCHAR(255) NOT NULL` |
| `target_current_row_id` | nullable `BIGINT`, traversal hint without polymorphic FK |
| `target_snapshot_artifact_id` | NOT NULL FK artifact |
| `mapping_state_artifact_id` | FK artifact; required for ingredient, null for substance |
| `input_artifact_id` | NOT NULL FK `scientific_evaluation_input/1` artifact |
| `execution_type` | CHECK `NORMAL, REPLAY, COUNTERFACTUAL, REFRESH` |
| `comparison_execution_id` | nullable self-FK RESTRICT; required except NORMAL |
| `configuration_artifact_id` | NOT NULL FK artifact |
| `input_digest` | NOT NULL 32 bytes and equal to `input_artifact_id.content_digest` |
| `semantic_execution_digest` | NOT NULL 32 bytes UNIQUE |
| `engine_semantic_version` | `VARCHAR(100) NOT NULL` |
| `engine_source_revision` | `VARCHAR(100) NOT NULL` |
| `engine_build_digest` | NOT NULL 32-byte SHA-256 |
| `dependency_lock_digest` | NOT NULL 32-byte SHA-256 |
| `container_image_digest` | nullable OCI digest string; required for full-reexecution claim |
| `canonicalization_version` | v1 CHECK |
| `technical_status` | CHECK `pending, running, completed, failed, cancelled` |
| `created_by` | nonempty actor identifier |
| `created_at`, `started_at`, `completed_at` | state-consistent timestamps |

`selection_digest`, result/trace and publication roots are not duplicated here;
they belong to the publication row. `scientific_result_status` belongs to the
result. The execution may cache `publication_id` only as a derived projection,
not as a second authority.

Semantic identity is the SHA-256 digest of this canonical object:

```text
protocol_digest
snapshot_digest
input_digest
execution_type
configuration_artifact_digest
comparison_execution_semantic_digest or null
```

Request keys, PKs, engine version, worker and timestamps are excluded. The UNIQUE
applies to all modes; repeated verification uses new attempts/replay reports on
the same semantic execution.

Mode constraints additionally require: NORMAL has no comparison; REPLAY pins the
same protocol/snapshot/input as its comparison; COUNTERFACTUAL pins historical
inputs but changes protocol/configuration; REFRESH records a changed snapshot or
input root.

### `scientific_evaluation_execution_attempts`

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `attempt_key` | `UUID NOT NULL UNIQUE` |
| `execution_id`, `attempt_number` | FK plus positive integer; UNIQUE pair |
| `technical_status` | CHECK `running, completed, failed, cancelled, abandoned` |
| `worker_id` | nullable sanitized operational identifier |
| `lease_token`, `lease_expires_at` | UUID/time required only while running |
| engine/build fields | actual engine metadata used by attempt |
| `started_at`, `ended_at` | state-consistent timestamps |
| `error_class`, `error_message` | nullable sanitized technical failure fields |
| `created_at` | audit timestamp |

Attempt rows may update only while running; terminal attempts are immutable.
Error data must not include credentials, prompts, raw private input or stack
locals.

### `scientific_evidence_selection_decisions`

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `execution_id` | NOT NULL FK execution |
| `snapshot_member_id` | NOT NULL FK member |
| `decision` | CHECK `included, excluded, deferred` |
| `resolution_state` | versioned stable state identifier |
| `reason_namespace`, `reason_version`, `reason_code` | nonempty vocabulary identity |
| `applicability_payload` | object JSONB query copy |
| `dependency_state` | versioned stable state identifier |
| `comparison_group_key` | nullable stable logical key |
| `decision_artifact_id` | NOT NULL FK canonical decision artifact |
| `decision_digest` | NOT NULL 32 bytes, equals artifact digest |
| `trace_fragment_artifact_id` | nullable FK artifact |
| `created_at` | audit timestamp |

UNIQUE `(execution_id, snapshot_member_id)`. A composite FK or deferred trigger
verifies that the member belongs to the execution snapshot. Rows become
insert-only when included in a publication.

### Canonical results and components

`scientific_evaluation_results`:

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `execution_id` | NOT NULL UNIQUE FK execution |
| `result_kind` | CHECK `substance_profile, ingredient_projection, product_assessment, generic_evaluation` |
| `result_schema_version` | nonempty |
| `canonical_artifact_id` | NOT NULL FK artifact |
| `result_digest` | NOT NULL 32 bytes, equals artifact digest |
| `scientific_status` | versioned nonempty state; not technical status |
| `created_at` | audit timestamp |

The execution id, not the digest, is unique. Different executions may own
separate result rows that reference one deduplicated canonical artifact.

`scientific_evaluation_result_components` stores: `id BIGSERIAL`, NOT NULL
`result_id`, `component_kind`, `component_schema_version`,
`component_artifact_id`, 32-byte `component_digest`, nonnegative
`component_ordinal` and `created_at`, with UNIQUE result/ordinal and
result/kind/digest. It does not require a numeric value.

`scientific_evaluation_projection_sets` stores `id BIGSERIAL`, NOT NULL
`result_id`, positive `generation`, `projection_schema_version`, manifest
artifact/32-byte digest, status `building, active, superseded, failed`,
created/sealed timestamps and UNIQUE result/generation.
At most one set per result is active. A rebuild inserts and verifies a new set,
then switches active status transactionally; it must reproduce the publication
projection digest. Published canonical output never changes.

After sealing, manifest/schema/digest fields and member rows are immutable.
Only the query-projection status may move one way from `active` to `superseded`
in the same transaction that activates the verified replacement generation.

Minimal domain projection tables reference a sealed projection set:

- `scientific_endpoint_synthesis_projections`: result, substance, endpoint key,
  synthesis/conflict state, component artifact/digest and ordinal;
- `scientific_substance_profile_projections`: result, substance, profile
  artifact/digest;
- `scientific_ingredient_projection_projections`: result, ingredient,
  substance, relationship/projection state, component artifact/digest, ordinal;
- `scientific_product_assessment_projections`: result, product, scenario digest,
  exposure-readiness and risk-computability states, component artifact/digest.

Only those query-critical fields are normalized. Quality, relevance, coverage,
uncertainty and conclusions remain canonical artifact content unless an approved
7.7 workload proves a new index is required.

### Trace and publication

`scientific_evaluation_traces`:

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `execution_id`, `result_id` | NOT NULL UNIQUE FKs |
| `trace_schema_version` | nonempty |
| `canonical_artifact_id` | NOT NULL FK artifact |
| `trace_digest` | NOT NULL 32 bytes |
| `result_digest`, `protocol_digest`, `snapshot_digest` | NOT NULL 32-byte linkage proofs |
| `created_at` | audit timestamp |

The trace is a canonical artifact plus a compact relational index formed by the
selection/domain projection tables. The result never references the trace.

`scientific_evaluation_publications`:

| Column | Type / constraint |
|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` |
| `publication_key` | `UUID NOT NULL UNIQUE` |
| `execution_id`, `result_id`, `trace_id` | each NOT NULL UNIQUE FK |
| `projection_set_id` | NOT NULL FK to the initial active projection set |
| `selection_manifest_artifact_id` | NOT NULL FK artifact |
| `projection_manifest_artifact_id` | NOT NULL FK artifact |
| `bundle_artifact_id` | NOT NULL UNIQUE FK artifact |
| selection/result/trace/projection/bundle digests | NOT NULL 32-byte fields |
| `published_at`, `created_at` | NOT NULL audit timestamps |

The explicit table is required: it is the single atomic reachability record and
avoids inferring publication from several nullable rows. The bundle artifact
commits to the semantic execution digest, snapshot, all roots and schema
versions. One execution has one publication.

### Replay verification and request idempotency

`scientific_evaluation_replay_reports` records `id BIGSERIAL`, `report_key UUID`,
original and replay execution/attempt FKs, support level, expected/observed
selection/result/trace roots, verifier engine/build/dependency digests, immutable
report artifact/digest and timestamps. Report key is UNIQUE.

Support levels are:

```text
VERIFIED_STORED_RESULT
FULL_REEXECUTION_SUPPORTED
FULL_REEXECUTION_UNAVAILABLE
REPLAY_MISMATCH
ARTIFACT_UNAVAILABLE
ARTIFACT_CORRUPT
ENGINE_INCOMPATIBLE
```

`scientific_evaluation_idempotency_keys` is operational: `id BIGSERIAL`,
`operation_type`, `request_scope`, `request_key`, nullable concrete
protocol-version/snapshot/execution/publication FKs, expected 32-byte semantic
digest, created/expiry timestamps. Exactly one owner FK is set after resolution.
UNIQUE `(operation_type, request_scope, request_key)`. It maps a caller retry to
a semantic entity but is never part of a scientific digest.

## Constraint and mutation freeze

### Enum strategy

Use `VARCHAR` plus named `CHECK` constraints, matching repository convention.
PostgreSQL ENUM is rejected because adding/revising lifecycle values makes
migrations and downgrades harder. Scientific/open vocabularies carry namespace
and version columns; a reference table is introduced only when independently
governed metadata becomes necessary.

### PK and logical-key strategy

Use `BIGSERIAL` internal PKs and `BIGINT` FKs, matching all current tables. Use
application-generated UUIDs as stable public/operational keys for snapshots,
executions, attempts, publications and governance events. Do not introduce a DB
UUID-generation extension. Content digest and protocol key are their natural
logical identities.

### JSONB strategy

Relational columns own query-critical identity, lifecycle, FK, status, reason
and digest data. Canonical multidimensional content is retained as canonical
bytes/object artifacts. `JSONB` is a parsed cache or bounded structured audit
payload; it is never the byte authority and never mutated to change canonical
meaning.

### Immutability triggers

A shared SECURITY DEFINER trigger function with a fixed, safe `search_path`
rejects UPDATE/DELETE for:

- every artifact identity row and every artifact-location locator/content field;
  only governed `location_status` transitions are allowed;
- published/deprecated/retired protocol semantic columns;
- sealed snapshots and all their members;
- published selection decisions;
- results, result components, traces and publications;
- each sealed projection set's semantic fields and domain rows; only the
  controlled `active -> superseded` status projection may change, while rebuild
  creates a new generation;
- governance events and replay reports.

Snapshots/members remain mutable only while status is `building`; attempts only
while nonterminal; executions only through the allowed technical state machine.
Service permissions deny direct table writes except through the application
owner path. Trigger tests are mandatory because service checks alone cannot
protect manual SQL or future code paths.

### FK delete strategy

All canonical/history/provenance relationships use `ON DELETE RESTRICT`,
including links to Phase 6 evidence, `storage_objects`, protocol, snapshot,
execution and result. No canonical table uses CASCADE or SET NULL. CASCADE is
allowed only for a future explicitly noncanonical staging table whose parent is
also unpublished; the frozen schema above has no such cascade.

### Legacy isolation

No new FK, view dependency or digest input may reference `product_scores`,
`ingredient_risk_profiles`, `ingredient_evidence` or the legacy scoring service.
Later shadow comparison uses an explicit adapter outside canonical artifacts.

## Naming freeze

Near-final table list, in dependency order:

```text
scientific_evaluation_artifacts
scientific_evaluation_artifact_locations
scientific_evaluation_protocols
scientific_evaluation_protocol_versions
scientific_evaluation_governance_events
scientific_evidence_snapshots
scientific_evidence_snapshot_members
scientific_evaluation_executions
scientific_evaluation_execution_attempts
scientific_evaluation_idempotency_keys
scientific_evidence_selection_decisions
scientific_evaluation_results
scientific_evaluation_result_components
scientific_evaluation_projection_sets
scientific_endpoint_synthesis_projections
scientific_substance_profile_projections
scientific_ingredient_projection_projections
scientific_product_assessment_projections
scientific_evaluation_traces
scientific_evaluation_publications
scientific_evaluation_replay_reports
```

These names do not overload Phase 6 `scientific_assessments` or imply a score.

## Index and query workload freeze

### Minimum indexes

Beyond PK/UNIQUE indexes:

- protocol versions `(protocol_id, lifecycle_status, semantic_version)`;
- artifacts `(artifact_kind, created_at)`;
- artifact locations `(artifact_id, location_status)` and `storage_object_id`
  when non-null;
- snapshots `(snapshot_digest)` unique and `(status, as_of)`;
- members `(snapshot_id, assessment_id)` and `(ingestion_run_id)`;
- executions `(target_type, target_logical_key, completed_at DESC, id DESC)`
  partial where completed; `(protocol_version_id, technical_status, created_at)`;
- attempts `(execution_id, attempt_number DESC)` and running lease expiry;
- decisions `(execution_id, decision, reason_code)` and `snapshot_member_id`;
- endpoint projections `(substance_id, endpoint_key, result_id)`;
- substance projections `(substance_id, result_id)`;
- ingredient projections `(ingredient_id, result_id)`;
- product projections `(product_id, result_id)` plus risk-computability state;
- publications `(published_at DESC, id DESC)`;
- governance per concrete entity FK plus `(effective_at, id)`;
- replay reports `(original_execution_id, created_at DESC, id DESC)`.

Do not add GIN indexes to JSONB in the foundation. Add one only after a measured
query requires it.

### Frozen workload

The physical design must support:

1. execution by public key/id;
2. latest canonical assessment for an explicit target/protocol/scenario scope;
3. full historical assessment list for that scope;
4. protocol family/version and governance disposition;
5. exact snapshot membership;
6. selected/excluded/deferred evidence with reasons;
7. substance endpoint syntheses/profile;
8. ingredient projections;
9. product assessment, readiness and risk computability;
10. canonical trace retrieval and indexed traversal;
11. replay/counterfactual/refresh lineage and reports;
12. supersession/retraction state as of a requested time.

### Current-state vocabulary

- `published`: a committed publication row exists; not equivalent to current.
- `non_retracted`: no effective retraction/integrity event exists at query time.
- `active protocol version`: published, not deprecated/retired/retracted and
  authorized for a new NORMAL execution at the requested time.
- `current`: the non-retracted leaf of explicit supersession lineage for an
  exact target/protocol/scenario scope as of a requested time.
- `latest`: greatest `(published_at, publication_id)` only inside that explicit
  scope; it is an ordering term, not authority.

If scope or lineage is ambiguous, the query returns multiple candidates or an
ambiguity state; it never silently selects by timestamp.

## Publication protocol freeze

Snapshot building/sealing is a separate idempotent prerequisite transaction.
Result publication is:

1. Load the published protocol, sealed snapshot and frozen input artifacts.
2. Build all decision, result, component, trace, projection-manifest and bundle
   canonical documents in attempt-local staging.
3. Canonicalize with v1 and calculate/verify every SHA-256 root.
4. Upload object-mode artifacts directly to immutable content-addressed final
   keys using conditional create; verify retrieved bytes, digest and length.
5. Prepare inline canonical bytes; do not yet expose any registry ownership as a
   publication.
6. `BEGIN` database transaction.
7. Lock execution row `FOR UPDATE`; recheck semantic digest, running state,
   protocol governance epoch and sealed snapshot.
8. Insert-or-reuse verified artifact registry rows by digest; reject metadata or
   byte mismatch on conflict.
9. Insert all canonical selection decisions and selection manifest reference.
10. Insert result, components and minimal domain projections.
11. Insert trace and projection-manifest reference.
12. Insert the explicit publication row/bundle; UNIQUE constraints resolve a
    duplicate request only if all root digests match.
13. Transition execution and active attempt to completed.
14. `COMMIT`.
15. Return publication identity after a fresh read. Asynchronous reconciliation
    handles only unreferenced objects/projection verification, never missing
    canonical content.

A client-visible canonical result exists only after step 14. Snapshot sealing
uses the same pattern: resolve explicit members, create/verify manifest, then in
one transaction bind manifest/digest/count, transition to sealed and make
members immutable.

### Failure and recovery matrix

| Failure | Canonical state | Idempotent recovery |
|---|---|---|
| Artifact upload fails | No DB publication; attempt remains running/failed | Retry conditional upload with same digest |
| Uploaded bytes fail verification | Object quarantined/noncanonical; no registry/publication | Record sanitized failure and upload correct bytes |
| DB transaction fails/rolls back | No publication or completed execution | Retry from semantic key; verified objects may be reused |
| Commit succeeds, client disconnects | Publication is canonical | Lookup by execution/publication semantic digest; never republish blindly |
| Duplicate publication request | First identical bundle wins UNIQUE | Return existing only after every root digest matches; otherwise integrity conflict |
| Worker crashes before commit | No canonical publication; lease expires | Mark attempt abandoned and start next attempt |
| Worker crashes after commit | Canonical publication remains | Recovery read observes completed execution/publication and closes ambiguity |
| Unreferenced content-addressed object | Noncanonical orphan | Reference-aware GC after grace period and audit |
| Snapshot sealing races | One identical seal wins | Loser verifies membership/digest and reuses; mismatch is conflict |
| Retraction during running execution | No silent substitution | Publication lock rechecks governance epoch; block or publish with explicit policy event |

## Concurrency and semantic idempotency

Prefer constraints/transactions over global application locks:

- protocol version publication: UNIQUE protocol/version plus `FOR UPDATE` on
  version; artifact digest must match on conflict;
- snapshot creation: semantic snapshot digest UNIQUE; builders may race, but
  seal transaction elects one identical result;
- execution creation: `INSERT ... ON CONFLICT` on semantic execution digest,
  followed by digest/input verification;
- publication: UNIQUE execution/result/trace/bundle and execution row lock;
- ambiguous client outcome: query semantic/request key and verify roots;
- advisory locks are reserved for expensive duplicate snapshot work reduction,
  never correctness.

Semantic keys:

```text
protocol version = SHA-256(protocol_key, semantic_version, protocol_digest)
snapshot         = snapshot_digest
execution        = semantic_execution_digest defined above
publication      = publication_bundle_digest
```

Request keys remain separate in the idempotency table and may expire according
to operational policy without affecting scientific identity.

## Security, privacy, engine and retention freeze

### Security and privacy

- migration owner owns tables/functions; application role receives only the
  minimum insert/state-transition paths; read roles cannot mutate;
- canonical bytes/JSON cannot be updated directly;
- digest, length, kind/schema and authorization are verified on write and read;
- object retrieval applies size/depth/media limits before parsing;
- trace and errors exclude API keys, auth tokens, private prompts, raw secret
  configuration, worker secrets and unnecessary user identifiers;
- future user-specific scenarios use an access-restricted artifact and a
  pseudonymous external subject reference; direct identity is outside the
  canonical scientific graph;
- private scenario artifacts are not cross-tenant content-deduplicated merely
  because a digest matches.

RLS/erasure mechanics are required before the later migration that stores
user-specific scenarios, but do not block the non-personal 0019 foundation.

### Engine retention and replay support

Persist engine semantic version, source/git commit, build digest, dependency lock
digest and canonicalization version on execution/attempt. Persist container image
digest when an execution claims `FULL_REEXECUTION_SUPPORTED`; otherwise the
strongest available claim is stored-result verification. Container
infrastructure is not required for 0019.

`VERIFIED_STORED_RESULT` proves retained canonical bytes and digest DAG.
`FULL_REEXECUTION_SUPPORTED` additionally requires retrievable compatible engine,
dependency and optional container artifacts. Unavailability never changes the
historical scientific result.

### Retention

```text
published canonical artifact           retain/reference-protect
sealed snapshot/member manifest        retain/reference-protect
referenced raw source artifact          retain or preserve verified checksum/access state
result, trace, publication, governance retain/reference-protect
unreferenced staging/orphan             GC eligible after grace/audit
AI derivative prose                    optional/regenerable; link to trace digest
request idempotency key                 operational retention; not scientific history
```

Canonical FKs and reachability checks prevent GC. Legal removal produces a
tombstone/integrity event while retaining non-sensitive digest evidence.

## Migration decomposition and Alembic freeze

| Slice | Proposed revision | Dependency and scope |
|---|---|---|
| 7.6.2A | `0019_scientific_evaluation_foundation` | From `0018`; artifact registry/locations, protocols, versions, initial governance, immutable functions/triggers |
| 7.6.2B | `0020_scientific_evidence_snapshots` | Snapshots, members, sealing, artifact links and concrete snapshot-governance extension |
| 7.6.2C | `0021_scientific_evaluation_publication` | Executions, attempts, idempotency, decisions, results/components, traces, publications |
| 7.6.2D | `0022_scientific_evaluation_projections` | Domain projections, replay reports, current views and reconciliation support |

Selection decisions are in 0021, not 0020, because their identity requires an
execution/protocol context. Each slice must be independently testable. No giant
migration is authorized.

### Required future migration tests

For every revision:

- upgrade a fresh/empty DB through the full chain;
- upgrade a representative existing `0018` DB without touching Phase 6/legacy
  rows;
- run preflight detection before adding constraints;
- validate PK/FK/UNIQUE/CHECK/index definitions and names;
- test immutable/sealed/published UPDATE and DELETE rejection;
- test permitted draft/building/attempt transitions;
- race semantic inserts/publication and verify one identical winner;
- retry after rollback and ambiguous commit;
- validate digest length/storage-mode/state consistency;
- prove historical rows and legacy scoring remain unchanged.

Downgrade is lossless only while new tables are empty. Once canonical/history
rows exist, downgrade must fail safely with an explicit preflight exception,
matching the repository's 0014–0018 historical-preservation pattern.

## Remaining blocker audit

No unresolved technical blocker remains for the bounded
`0019_scientific_evaluation_foundation` migration.

The following are explicit later-slice prerequisites, not 0019 blockers:

| Prerequisite | Required before | Owner | Deferrable after 0019? |
|---|---|---|---|
| Implement and fixture-test `wye-c14n-json-v1` serializer | Completed in Phase 7.6.3A | Backend/platform | Implemented and validated |
| Object-store reconciliation/GC operational job | Object-mode publication in 0021 | Platform | Yes |
| User-scenario RLS/erasure implementation | User-specific scenario persistence | Security/privacy | Yes |
| Scientific endpoint/dependency/form/reference policies | Scientific engine/7.7 validation | Scientific governance | Yes |

They are concrete and scoped; none requires changing the 0019 schema contract.

## First implementation checkpoint

```text
Phase 7.6.2A — Scientific Evaluation Persistence Foundation
Alembic revision: 0019_scientific_evaluation_foundation
```

In scope:

- create `scientific_evaluation_artifacts`,
  `scientific_evaluation_artifact_locations`,
  `scientific_evaluation_protocols`,
  `scientific_evaluation_protocol_versions` and
  `scientific_evaluation_governance_events`;
- named PK/FK/UNIQUE/CHECK constraints and minimum foundation indexes;
- artifact and published-content immutability/append-only triggers;
- lifecycle/state constraints and restrictive FK deletion;
- upgrade/preflight/empty-downgrade refusal tests;
- canonicalization/digest column contract tests;
- verification that legacy and Phase 6 tables/data are untouched.

Out of scope:

- snapshots, executions, attempts, selection, results, traces, publications and
  projections (0020–0022);
- object upload/runtime serializer, persistence service and replay engine;
- APIs, Flutter, legacy migration or shadow comparison;
- evidence selection/synthesis/projection/exposure/risk logic;
- numerical score, formula, weight or threshold.

## Phase 7.6.1 exit criteria

- [x] Canonical JSON profile and version frozen.
- [x] Integer/decimal/date/time/UUID/enum/byte rules frozen.
- [x] SHA-256 and BYTEA/lowercase-hex encoding frozen.
- [x] Non-circular digest graph and boundaries frozen.
- [x] Artifact envelope and inline/object policy frozen.
- [x] Artifact registry logical schema frozen.
- [x] Protocol/version/governance schemas and lifecycle frozen.
- [x] Snapshot/member and target-freeze strategy frozen.
- [x] Selection, execution, attempt and semantic identity schemas frozen.
- [x] Result/component/domain projection schemas frozen.
- [x] Trace/publication/replay report schemas frozen.
- [x] Atomic DB/object publication and failure recovery frozen.
- [x] Immutability, append-only and FK-delete enforcement frozen.
- [x] Table names, CHECK enums, BIGSERIAL/UUID and JSONB strategy frozen.
- [x] Minimum indexes and twelve-query workload frozen.
- [x] Current/latest/active/published/non-retracted semantics frozen.
- [x] Privacy/security, engine compatibility and retention frozen.
- [x] Four migration slices and Alembic revision names frozen.
- [x] Migration lifecycle/concurrency/idempotency tests specified.
- [x] Remaining prerequisites classified as non-blocking for 0019.
- [x] Final decision recorded as READY FOR MIGRATION IMPLEMENTATION.

This freeze document did not itself start Phase 7.6.2A. The separately bounded
implementation is now complete and validated: revision
`0019_scientific_evaluation_foundation` creates the five authorized foundation
tables and their database protections. Because the frozen revision identifier
is longer than Alembic's historical `VARCHAR(32)`, the migration also widens the
Alembic metadata column to `VARCHAR(64)` before Alembic records the new head.
The local `wye` database remains at `0017_ingredient_mapping_history`.
Phase 7.6.2B-1 has now completed the design/review freeze for
`0020_scientific_evidence_snapshots` with decision:

```text
DESIGN FROZEN — READY FOR MIGRATION IMPLEMENTATION
```

At the B-1 freeze, migration 0020 had not yet been created and the repository
head was 0019. That design checkpoint introduced no snapshot runtime,
execution, replay or scientific engine.

## Phase 7.6.2B-2 implementation status

The frozen design is implemented by revision
`0020_scientific_evidence_snapshots` and has passed its dedicated PostgreSQL
migration, integrity and concurrency suite. The repository Alembic head is now
0020; the local `wye` database remains at
`0017_ingredient_mapping_history`.

The implementation remains persistence-only: no canonical serializer, artifact
writer, snapshot repository/finalizer, execution, replay or scientific engine
has been added. Formulas, weights, thresholds and numeric scores remain absent,
and legacy scoring remains isolated.

## Phase 7.6.3A runtime foundation status

The frozen serializer prerequisite is implemented, validated and committed.
Runtime support is intentionally narrow: JSON objects/lists/strings/booleans/
null and signed 64-bit integers only, NFC and deterministic UTF-8 ordering,
canonical control escaping, no binary float and no implicit conversion of
Decimal/date/time/UUID/bytes or Python containers.

The scientific artifact writer supports the five currently frozen v1 contracts,
computes canonical SHA-256 internally, uses database uniqueness as final
authority, validates exact stored metadata/cache/inline bytes on reuse and
serializes location creation on the artifact row. It never commits or rolls back
the caller transaction. Remote object-mode upload remains deferred; the inline
writer is the deterministic local/test and small-artifact foundation.

The optional JSONB cache is omitted when canonical strings or keys contain
U+0000, which PostgreSQL JSONB cannot represent. Verified canonical bytes remain
the sole digest authority; no alternate cache serialization is hashed.

No migration was added by 7.6.3A. Snapshot construction/sealing runtime was
subsequently implemented in committed Phase 7.6.3B. Mapping-state persistence,
execution/result persistence, scoring execution, replay, formulas, weights,
thresholds and numeric scores remain outside scope.

## Phase 7.6.3B runtime implementation status

The 0020 contract now has a caller-transaction-owned repository and deterministic
builder/finalizer runtime, `COMPLETED + COMMITTED` in
`f775e0e03a4cce348afc07c052d5a72a7c8568c1`. The typed
request carries versioned snapshot policy, UTC `as_of`/cutoff, typed query scope
and predicates, exact assessment/finding candidate identities and audit actors;
it deliberately contains no mapping state or protocol decision.

The runtime creates the query artifact, building header and canonical member
artifacts, persists relational membership, then locks and reloads the parent and
members before seal. It revalidates provenance and canonical roots, assigns the
frozen bytewise order, creates the manifest through the 7.6.3A writer and uses
its SHA-256 digest as `snapshot_digest`. The runtime never hashes SQL row order.

`status_as_of` is concretely sourced from
`scientific_assessments.assessment_status`; release status is a separate frozen
provenance field and there is no finding lifecycle column to materialize. A
change before seal fails revalidation; a change after seal cannot rewrite the
member row or canonical artifact. This records available schema truth without
claiming a missing bitemporal lifecycle.

Two building UUIDs may coexist. A transaction-scoped digest advisory lock
reduces contention, while the 0020 partial UNIQUE remains final authority. A
loser returns the sealed winner only after compatible query/manifest/member-root
verification and deletes only its own unsealed construction rows. Member trigger
parent locks serialize both mutation-first and seal-first races.

The advisory coordination key uses a dedicated WYE snapshot namespace in the
transaction-scoped two-integer PostgreSQL lock space; digest-prefix collisions
can only serialize unrelated snapshot seals and cannot establish identity. The
0020 UNIQUE constraint remains authoritative. Canonical ordinal reassignment
breaks permutations through a free value in `[0, member_count]`, so immediate
ordinal uniqueness is respected without offset overflow.

No migration changes are required. Evidence selection, mapping state, scoring
execution, result persistence, replay, synthesis, projection, exposure/risk,
formulas, weights, thresholds and numeric scores remain unimplemented.

## Phase 7.6.4A-1 target, mapping and input design freeze

`WYE_MAPPING_EXECUTION_INPUT_FREEZE.md` is authoritative for the exact artifact
payloads and status matrix. It freezes:

```text
scientific_evaluation_target / 1
scientific_mapping_state_member / 1
scientific_mapping_state_manifest / 1
scientific_evaluation_input / 1
```

Target v1 is limited to `substance` and `ingredient`. Product is excluded until
a replay-safe composition/scenario contract exists. The ingredient mapping
manifest contains only controlled accepted/materialized members effective on
the inclusive UTC `mapping_day` and recorded by `as_of`; canonical empty,
partial and unavailable states preserve the difference between absence and
unreconstructible history.

`input_digest` is the `scientific_evaluation_input/1` content digest and binds
the target root plus mapping-state root/not-applicable state. Evidence snapshot,
protocol, execution mode and configuration are excluded and combine later in
`semantic_execution_digest`. This section supersedes older shorthand that put
mapping state inside an evidence snapshot or evidence snapshot inside
`input_digest`.

The 0019 artifact registry is sufficient for the bounded future 7.6.4A runtime;
no migration is required. Future 0021 execution persistence must include
restrictive FKs for protocol version, sealed evidence snapshot, target artifact,
mapping-state artifact when applicable, input artifact and configuration
artifact. This freeze creates no runtime allowlist, repository, service, table
or migration.

Phase 7.6.4A-1B amends mapping member v1 before publication: one member is one
`ingredient_substances` bridge and contains an ordered `authority_chains[]` array
with every valid visible proposal/accept/materialization chain. Multiple
`applied`/`already_current` chains do not create duplicate members. Canonical
non-member observations, their closed reason/impact vocabulary and deterministic
resolution precedence are defined in `WYE_MAPPING_EXECUTION_INPUT_FREEZE.md`.
This remains artifact payload design over existing Phase 6 history and requires
no schema migration. Phase 7.6.4A-2 implements the four frozen runtime artifact
contracts, historical mapping reconstruction and prerequisite validation and is
`COMPLETED + COMMITTED`.
