# WYE — Scientific Evaluation Persistence, Explainability and Replay Contract

## Status and scope

This document is the canonical architecture specification for Phase 7.6. It
specializes the semantic contracts in `WYE_SCORING_EXECUTION_MODEL.md`,
`WYE_EVIDENCE_SELECTION.md`, `WYE_EVIDENCE_SYNTHESIS.md`,
`WYE_INGREDIENT_PROJECTION.md` and `WYE_PRODUCT_ASSESSMENT.md` into a
persistence and verification design.

It defines durable identity, immutable publication, query projections,
explanation trace, replay verification and historical governance. It does not
define a SQL schema, create a migration, authorize runtime evaluation or add a
scientific rule. In particular, it introduces no score, formula, weight,
threshold, exposure estimate or risk calculation.

The audited baseline is:

```text
Git / Alembic repository: 0018_scientific_batch_recovery
local database:           0017_ingredient_mapping_history
```

## Frozen principles

```text
same frozen semantic inputs + same published protocol version
    = same canonical semantic output

canonical scientific artifact != query projection
completed scientific execution != technical attempt
technical failure != scientific insufficiency
supersession/retraction != historical deletion
replay != counterfactual != refresh
AI wording != canonical explanation trace
```

A completed result is never edited to reflect later evidence, mappings,
composition, scenarios, protocol rules or engine builds. Later knowledge creates
a new artifact and, where required, an append-only governance relationship.

## Audit of persistence patterns through `0018`

The current schema offers reusable engineering patterns, not Phase 7 result
persistence:

| Existing structure | Useful pattern | Limitation for Phase 7 |
|---|---|---|
| `storage_objects` | Provider/bucket/key/version identity, checksum metadata, byte size | Location identity is unique, but content addressability, publication state and canonicalization version are not enforced |
| `scientific_release_artifacts` | Release-bound immutable provenance, raw checksum, media type, acquisition/validation times | Represents acquired source artifacts, not generated canonical evaluation artifacts |
| `scientific_ingestion_runs` | Run identity, idempotency key, parser/normalization/build versions and output checksums | Ingestion lifecycle is not scientific-evaluation lifecycle |
| `scientific_ingestion_run_artifacts` | Explicit ordered membership with restrictive foreign keys | Membership pattern is useful; its rows cannot serve as evidence snapshots |
| assessments/findings hardened in `0010` | Stable run/source-record identities and normalized fingerprints | Lifecycle/correction/dependency/ontology gaps remain; source rows alone are not frozen snapshots |
| substance identity/review/materialization in `0011`–`0016` | Versioned namespaces, append-only decisions, auditable materialization | Current registry rows remain mutable inputs unless captured in an identity snapshot |
| mapping history in `0017` | Accepted current uniqueness, validity intervals, proposal/decision/materialization/closure audit | No immutable mapping-snapshot manifest or ingredient-identity history |
| batch recovery in `0018` | Definition digest, work identity, leases, attempts, recovery counters | Batch work is operational; its mutable work item is not a canonical scientific execution |

`ON DELETE RESTRICT`, partial unique indexes, append-only event rows, checksums,
explicit membership and separate attempt history should be reused as design
patterns. Existing source and ingestion tables remain authoritative provenance
anchors and must not be renamed or overloaded.

## Canonical artifact and query-projection split

### Canonical layer

The canonical layer contains immutable, deterministic semantic payloads and
their digests. It is the source of truth for replay and audit. Each canonical
artifact has a common envelope:

```text
logical artifact type
artifact schema version
canonicalization profile/version
digest algorithm and digest
canonical media type
canonical byte length
storage disposition and verified storage reference
created provenance
publication state
```

The digest is computed from canonical bytes before persistence. A PostgreSQL
`JSONB` value is useful for querying but is not itself proof of the original
canonical byte representation. Therefore an implementation must retain the
canonical bytes, inline for bounded small artifacts or in object storage for
large artifacts, while optionally storing a parsed `JSONB` projection.

### Projection layer

Projection rows and views expose indexed fields such as protocol, target,
snapshot, mode, status, endpoint, reason code and current-governance state.
They are:

- derived from exactly one canonical artifact or publication bundle;
- bound to that artifact digest and projection-schema version;
- rebuildable without changing scientific meaning;
- non-authoritative if their digest link or rebuild verification fails.

Projection repair changes only query infrastructure. It must not generate a new
scientific result, silently reinterpret a payload or alter a canonical digest.

### Content-addressed storage decision

Use a hybrid content-addressed artifact registry:

- small canonical payloads may retain canonical bytes and parsed JSON inline;
- large manifests, result graphs and traces use immutable object storage;
- both use the same SHA-256 content identity and verified artifact envelope;
- an identical payload may be physically deduplicated but each semantic owner
  retains explicit membership/reference rows;
- storage key or object version is a locator, never the semantic identity.

The inline/object cutoff is an operational parameter outside scientific
semantics. Moving identical bytes between storage classes cannot change a
digest. Compression and encryption are storage transforms outside the canonical
byte boundary and require integrity verification after retrieval.

## Persistent logical model

Names below are logical names. Final plural SQL names, column types and migration
identifiers belong to a later schema-design checkpoint.

### Persistence inventory classification

| Classification | Logical objects |
|---|---|
| Canonical persistence | `scientific_protocol_version`, `evidence_snapshot`, `target_identity_snapshot`, `evidence_selection_decision`, `evaluation_result`, `result_component`, `explanation_trace`, evidence lines/groups, endpoint synthesis, substance profile, ingredient projection, composition snapshot, scenario, readiness and product assessment |
| Normalized identity/governance persistence | `scientific_protocol`, `scientific_evaluation_execution`, `execution_governance_event`, publication bundle |
| Derived/operational persistence | `execution_attempt`, replay-verification report, artifact reachability and reconciliation state |
| Query projection | Protocol/execution indexes plus candidate, endpoint, ingredient, product, reason, current-state and trace-edge projections |
| Ephemeral runtime only | Unpublished partial payloads, serializer buffers, caches, worker logs and staging manifests |
| Future-only because source data/review is missing | Concrete exposure/reference-point result components and any reviewed numerical component; their generic envelopes are canonical-ready but their scientific content is not |

Every Phase 7.1–7.5 object appears in durable identity, canonical, derived or
projection form; none may exist only as an in-memory fact if a published result
depends on it.

| Logical entity/artifact | Authoritative representation | Query support | Immutability boundary |
|---|---|---|---|
| `scientific_protocol` | Governed DB identity row | Domain, owner, lifecycle | Identity metadata changes only through governed fields/events |
| `scientific_protocol_version` | DB header + canonical rule artifact | Protocol, semver, lifecycle, dates, digest | Published version and rule bytes immutable |
| `evidence_snapshot` | DB header + canonical sealed manifest | `as_of`, cutoff, scope, digest, state | Membership and query definition immutable after sealing |
| `evidence_snapshot_member` | Restrictive membership row + member semantic digest | Evidence type/native row/provenance | Append only while building; immutable after seal |
| `target_identity_snapshot` | Canonical artifact + target-type projection | Target lookup and historical identity | Immutable once referenced by execution |
| `mapping_snapshot` | Canonical manifest of mapping/materialization/validity state | Ingredient/substance/as-of lookup | Immutable once sealed |
| `product_composition_snapshot` | Canonical manifest/document | Product/provenance/as-of lookup | Immutable once sealed |
| `exposure_scenario` | Canonical artifact; privacy-classified metadata projection | Scenario type/population/route, restricted | Immutable per digest; correction creates new artifact |
| `scientific_evaluation_execution` | DB identity/lifecycle row | Protocol, target, mode, status, semantic key | Terminal scientific links immutable after publication |
| `execution_attempt` | Append-only operational row | Attempt/status/build/error/lease | Each closed attempt immutable; new retry is a new row |
| `evidence_selection_decision` | Canonical decision payload + candidate projection row | Decision, reason, evidence identity | Immutable within a publication |
| evidence-line/comparison-group artifacts | Canonical documents or result sub-artifacts | Optional endpoint/dependency projections | Immutable within a publication |
| `endpoint_synthesis` | Canonical result component | Endpoint/state/conflict lookup | Immutable |
| `substance_hazard_profile` | Canonical result artifact | Substance/protocol/snapshot lookup | Immutable |
| `ingredient_scientific_projection` | Canonical result artifact | Ingredient/mapping/substance/state lookup | Immutable |
| `exposure_readiness_assessment` | Canonical result artifact | Product/scenario/readiness/reasons | Immutable |
| `product_scientific_assessment` | Canonical result artifact | Product/scenario/risk-computability | Immutable |
| `evaluation_result` | Publication-owned canonical root | Target/result class/status | Immutable |
| `result_component` | Typed canonical membership + query projection | Type/scope/status | Membership and component digest immutable |
| `explanation_trace` | Content-addressed canonical graph artifact | Trace type/root digest/access policy | Immutable |
| `publication_bundle` | DB commit record binding all root digests | Completion and verification lookup | Immutable once published |
| `execution_governance_event` | Append-only DB event + optional canonical rationale artifact | supersession/retraction/current views | Event immutable; no rewrite of governed artifact |

### Representation trade-offs

| Representation | Why used | Costs and controls |
|---|---|---|
| Normalized row | Strong identity, constraints, concurrency and common queries | Migration/FK complexity; must not fragment semantic payload across mutable columns |
| Canonical JSON/bytes | Exact replay, audit and schema-versioned multidimensional content | Less convenient queries; requires canonicalization fixtures and retained bytes |
| Membership/join row | Referential integrity, selective lookup and deterministic membership | Storage grows with snapshots; bulk inserts/seal must be transactional |
| Content-addressed object | Large immutable manifests/results/traces, deduplication and independent verification | Cross-store atomicity, retention and retrieval security require explicit protocol |
| Projection/index row or view | Fast endpoint/product/current queries | Derived only; version/digest checks and rebuild tooling prevent silent divergence |
| Hybrid | Combines relational integrity/queryability with canonical replay | Highest initial migration/operational complexity, justified by audit and historical stability |

Deduplication applies to identical canonical bytes, not logical ownership.
Concurrency is controlled at normalized identities/publication rows. Auditability
and replay always resolve back to canonical bytes, not projection columns.

### Protocol persistence

A protocol family row is stable identity, not executable rules. A version may
move through draft/review/approved before publication. Publication atomically
binds the version metadata to the canonical rule artifact and
`protocol_digest`. Thereafter metadata that affects semantics, dates,
vocabularies or referenced policies cannot change. Typographical or scientific
correction creates a new version. Deprecation/retirement is a governance state
or event and does not invalidate historical execution.

### Snapshot persistence

Snapshot construction has two states: `building` and `sealed`. During building,
membership can be resolved under a recorded deterministic query definition. The
seal operation verifies and freezes:

- query-definition artifact and cutoff/as-of semantics;
- exact resolved members in canonical order;
- each evidence, identity, parser/normalization and provenance reference;
- mapping/identity state references needed by the execution domain;
- member count, membership digest and root `snapshot_digest`.

The resolved membership is mandatory. Re-executing a stored query against future
tables is never replay. A snapshot with no candidate evidence is still a valid
sealed universe.

Candidate findings require explicit membership rows because selection,
inclusion/exclusion queries and FK enforcement operate at that atomic unit. Each
row also identifies its mandatory assessment context and the chosen normalized
ingestion representation; release, ingestion run and source artifact are
restrictive provenance references on that member and are redundantly committed
in the canonical manifest. Assessment-only candidates, if a future protocol
explicitly permits them, use the same typed membership shape. Target identity,
mapping state and product composition are separate sealed input artifacts linked
from `input_digest`, not misleading evidence-member rows. The manifest retains
complete frozen semantic payloads/digests even when the DB reference points to a
row that may later change.

### Selection and synthesis persistence

Every candidate in the sealed universe receives one canonical terminal
selection outcome for the given target question: included, excluded or deferred/
unresolved as allowed by the published protocol. Included evidence must have a
decision; a decision cannot reference evidence outside its snapshot.

Evidence-line grouping, dependencies, comparison groups, endpoint syntheses and
the substance profile are stored as typed canonical components. Query rows may
flatten endpoint, state, quality/relevance/uncertainty dimensions and conflict
codes, but the ordered component graph and supporting/contrary references remain
in canonical artifacts. Counts never replace dependency identity.

Evidence lines and comparison groups are execution-scoped canonical result
sub-artifacts: their logical identities do not become global scientific facts.
Identical bytes may be physically deduplicated, while ownership remains tied to
the publication. Minimal projection rows expose line/group/endpoint/dependency
keys needed for trace and query; all grouping rationale remains canonical.

### Ingredient and product persistence

An ingredient projection binds a frozen ingredient identity, mapping snapshot,
relationship semantics, source substance-profile digest, projected/blocked
dimensions, uncertainty, reasons and trace. Multiple substances remain separate
components.

A product assessment binds a product-composition snapshot, ingredient-projection
digests and one explicit exposure-scenario digest. Multiple scenarios produce
separate assessment components or executions. `risk_not_computable` is stored as
a valid scientific state, not as technical failure or a null score.

## Execution, attempt and publication lifecycle

### Scientific execution

```text
requested -> pending -> running -> completed
                         |    \
                         |     -> cancelled
                         -> failed
```

`completed` means a verified canonical publication bundle became reachable in a
successful database transaction. It does not merely mean that computation
ended. A completed execution remains completed even if later superseded or
retracted; its current governance disposition is derived from events.

### Attempt lifecycle

Retries never overwrite execution history. Each attempt records attempt number,
worker/build identity, engine compatibility profile, lease ownership and expiry,
start/end times, technical status, error class, staging references and verifier
summary. Runtime timestamps and worker identity are operational and excluded
from semantic digests.

`no_eligible_evidence`, `insufficient_evidence`, `risk_not_computable` and
conflicting evidence can complete successfully. Connection failure, corrupt
artifact, engine incompatibility and canonicalization failure are technical
attempt failures.

### Atomic publication across database and object storage

There is no distributed transaction assumption. Publication uses a reachability
protocol:

1. Produce canonical bytes in isolated staging and compute digests.
2. Put every large artifact at its final immutable content-addressed key, or
   verify an existing byte-identical object.
3. Read/verify digest, size and media type; register artifacts as verified but
   not yet canonical/reachable.
4. In one database transaction insert all immutable ownership/membership rows,
   query projections, root digests and the publication bundle; transition the
   execution to `completed` only in that transaction.
5. After commit, the bundle is canonical. After rollback, verified unreferenced
   objects are noncanonical orphans eligible for delayed reconciliation/GC.

Object finalization must not occur after the authoritative DB commit. A pointer
to an unverified or mutable object cannot be published. Reconciliation may
repair/retry staging or projection work, but cannot synthesize a missing
canonical result.

### Canonical boundary

Intermediate files, partial components, logs, model caches and attempt summaries
are noncanonical. Canonicality begins only at the committed publication bundle.
The bundle binds exactly one execution, protocol version, frozen input roots,
selection root, result root and trace root. Partial outputs must never be exposed
as completed scientific results.

## Immutability, supersession, retraction and invalidity

Updates/deletes to sealed snapshots, published protocol versions, published
selection decisions, result components, traces and bundle links are forbidden.
Correction creates a new immutable artifact or execution.

Append-only governance events express:

- `supersedes`: a later artifact/result is preferred for a defined scope;
- `retracts`: the issuer withdraws current reliance while retaining history;
- `integrity_compromised`: verification found a provenance/digest defect;
- `annotation`: non-semantic audit note;
- `review_disposition`: governed approval/rejection without mutating payload.

Events record actor, authority, reason code, rationale artifact, effective time,
recorded time and predecessor/successor scope. Cycles and self-reference are
forbidden. “Current” is a derived, time-aware view; it is not an `is_current`
flag that rewrites history.

## Replay, counterfactual and refresh

| Mode | Frozen/reused | Allowed difference | Historical effect |
|---|---|---|---|
| `NORMAL` | Chosen protocol version, snapshot, identities and configuration | New logical input | New immutable execution |
| `REPLAY` | Exact protocol bytes, snapshot membership, target/mapping/composition/scenario artifacts and semantic configuration | Attempt/build may differ only if compatibility permits | Expected identical semantic digests; never replaces original |
| `COUNTERFACTUAL` | Historical scientific inputs and snapshots | Explicitly different protocol/rules/configuration | New result linked as comparison; original unchanged |
| `REFRESH` | Protocol may be same; target scope preserved | New evidence/mapping/product/scenario snapshot | New current candidate; original unchanged |

Historical replay never relies on current display names or mutable product rows.
An ID alone is insufficient: substance, ingredient, source/dataset and product
identities are stored as ID plus frozen semantic payload and digest. Product
replay additionally pins composition/ingredient membership, label provenance,
nutrition/serving values and preparation metadata as actually available; missing
historical fields remain explicitly missing rather than being filled from the
current product.

### Replay verifier

The verifier operates without trusting query projections:

1. Verify canonical artifact availability, bytes, digest and schema profile.
2. Verify the digest DAG and all membership/referential invariants.
3. Verify engine/build compatibility with protocol and canonicalization profiles.
4. Recompute using exact frozen roots in an isolated attempt.
5. Compare selection, result and trace semantic digests.
6. Record an immutable verification report: `verified_identical`,
   `semantic_mismatch`, `artifact_unavailable`, `artifact_corrupt`,
   `engine_incompatible` or `verification_failed`.

A mismatch never overwrites either result. It is a technical/integrity incident
requiring governance review.

### Engine compatibility

An execution records engine name/version, build or source revision, dependency
lock digest, runtime profile and canonicalization implementation/profile. The
protocol version declares accepted compatibility requirements. Exact binary
retention is preferred for strong replay; where unavailable, a later engine may
verify only if it declares and tests semantic compatibility. “Latest engine” is
not sufficient. Incompatibility yields a replay-verification state, not a new
scientific conclusion.

## Explanation and provenance model

The canonical explanation is a machine-readable directed acyclic graph. Nodes
are typed immutable artifacts/events; edges carry stable semantic roles such as
`governed_by`, `snapshot_contains`, `selected_as`, `grouped_into`,
`supports`, `contradicts`, `projected_via`, `derived_quantity_from`,
`blocked_by` and `supersedes`.

It must traverse:

```text
protocol/version
 -> snapshot and candidate evidence
 -> selection decisions and reason codes
 -> evidence lines and dependencies
 -> comparison groups and endpoint synthesis
 -> substance profile
 -> mapping snapshot and ingredient projection
 -> product-composition snapshot and scenario
 -> exposure readiness / risk-computability
 -> product scientific assessment
```

Every normalization, assumption, missing dimension, conflict, blocked transfer,
uncertainty and governance action is explicit. Presentation labels, localized
text and AI summaries are excluded from canonical digests. An AI may render the
verified graph, but cannot add/remove nodes, choose evidence, change reasons or
become the canonical output. Generated prose stores its model/prompt/provenance
and source trace digest as a noncanonical presentation artifact.

## Canonicalization profile

The initial technical candidate is canonical JSON plus SHA-256, but the exact
profile must be frozen and fixture-tested before migration implementation. It
requires:

- UTF-8 canonical bytes and stable object-key ordering;
- arrays ordered by protocol-defined semantic keys; sets sorted before encoding;
- explicit null/missing semantics; omitted and null are never silently equal;
- string Unicode normalization and prohibited locale-sensitive transforms;
- explicit enum and reason-vocabulary versions;
- explicit unit, time-zone and temporal precision semantics;
- no non-finite number values; scientific decimals retain declared lexical/
  scale policy rather than binary floating-point ambiguity;
- referenced semantic digests, not generated DB ids or storage locations;
- exclusion of runtime time, worker, row order, UI and AI wording.

Changing canonicalization creates a new profile/version. Existing artifact
digests remain verifiable with their original profile; bulk rewriting is not
allowed.

## Digest graph and minimum proof set

The digest graph is acyclic:

```text
protocol_digest
        + evidence/member/identity roots
        -> snapshot_digest
        -> selection_digest
        -> synthesis/substance_profile_digest
        + mapping_snapshot_digest
        -> ingredient_projection_digest
        + product_composition_snapshot_digest
        + exposure_scenario_digest
        -> exposure_readiness/product_assessment/result_digest
        -> trace_digest
        -> publication_bundle_digest
```

The six public verification boundaries remain:

```text
protocol_digest
snapshot_digest
input_digest
selection_digest
result_digest
trace_digest
```

Domain-specific digests are component roots beneath `result_digest`. The
`input_digest` commits to target identity plus all domain input roots and
semantic configuration. The semantic result does not include `trace_digest`;
the trace may include `result_digest`, and the bundle commits to both. This
prevents circular hashing. DB ids, physical object keys and timestamps not
scientifically meaningful are excluded.

## Referential integrity and constraints

### Database-enforceable

- non-null restrictive foreign keys between ownership/membership rows;
- unique protocol semantic version within protocol family;
- unique digest identity within algorithm/profile/artifact type;
- one publication bundle and one canonical result root per completed execution;
- candidate membership uniqueness and one terminal decision per candidate,
  question and execution;
- unique attempt number per execution and unique attempt execution key;
- valid state/check constraints and mutually consistent completion fields;
- no self-supersession; deferred acyclic governance validation;
- no delete of referenced canonical artifacts (`ON DELETE RESTRICT`);
- scoped uniqueness for in-flight idempotency and canonical semantic result.

### Service-enforced with DB guardrails

- byte/digest verification against object storage;
- canonical serialization/profile compliance;
- immutable-column enforcement after seal/publication, preferably backed by
  restrictive triggers/permissions;
- artifact DAG completeness and projection-to-canonical consistency;
- lease acquisition/recovery and atomic publication orchestration;
- authorized governance transitions and privacy access.

### Scientific/protocol validation

Eligibility, endpoint equivalence, evidence dependency, synthesis, projection,
exposure readiness, reference compatibility and confidence semantics remain
protocol-scoped and externally reviewable. Database validity is not scientific
validity.

## Idempotency, concurrency and recovery

Two identities are distinct:

- request idempotency: caller-supplied key scoped to owner/operation, used to
  return the same accepted request;
- semantic identity: canonical key over protocol version, execution mode,
  input digest and semantic configuration.

Equivalent concurrent NORMAL/REFRESH requests may converge on one execution and
publication. REPLAY verification attempts may be legitimately repeated and are
separate attempts/reports. COUNTERFACTUAL executions differ by protocol/config.

Semantic keys are defined separately for protocol publication
(`protocol identity + semantic version + protocol digest`), snapshot sealing
(`protocol/scope + query definition + resolved membership digest`), execution
creation (`protocol version + mode + input digest + semantic configuration`) and
result publication (`execution + result digest + trace digest`). Request keys do
not enter these digests.

Concurrency behavior:

1. Same protocol version publication: scoped uniqueness elects one winner;
   loser verifies and reuses or reports conflict.
2. Same snapshot build: building leases may duplicate work, but only identical
   membership/digest can seal the same semantic snapshot.
3. Same execution: one active lease; expired attempt becomes abandoned and a
   new attempt resumes from canonical inputs, not mutable partial output.
4. Same artifact upload: conditional create at digest key; byte verification is
   mandatory before reuse.
5. Same publication: unique execution/bundle and semantic key make commit
   idempotent.
6. Projection rebuild versus reads: build a versioned replacement and switch the
   projection-version pointer transactionally.
7. Governance event race: serialize per governed artifact and reject competing
   incompatible events or retain both for explicit review; never silently win by
   timestamp.

If a referenced protocol/input is retracted while an execution is running, the
publication transaction rechecks its governance epoch. Protocol policy decides
whether publication is blocked or published with an explicit governance event;
it may never silently substitute current input or erase the attempt.

## Retention, security and privacy

Canonical artifacts reachable from published protocol versions, sealed
snapshots, completed executions, verification reports or governance events have
reference-aware indefinite scientific retention unless a higher legal policy
requires restricted handling. Garbage collection may remove only verified
unreferenced staging objects after a grace period and audit record.

Loss, corruption or legally mandated removal is recorded as an integrity/
availability event; references and digests remain to prove what is missing.
Source licenses and access controls may restrict raw artifacts independently of
derived trace access.

User-specific exposure scenarios may contain sensitive personal data. They must
be segregated from generic scientific artifacts, access controlled, minimally
projected, encrypted as appropriate and governed by a retention/deletion policy.
If erasure is required, use privacy-preserving tombstone/digest evidence and
revoke access; do not expose personal content through traces or shared
content-addressed deduplication. Generic and user-specific assessments cannot
share an authorization boundary merely because semantic fields match.

Canonical payloads and traces must reject secrets, credentials, API keys,
private prompts and unnecessary personal identifiers. Artifact retrieval must
verify authorization, expected digest, byte length and media type before parsing;
parsers apply size/depth limits. Creation/publication/governance events record an
authenticated audit actor without putting authentication material in the trace.

## Query model and current views

Required indexed access patterns include:

- protocol family/version/lifecycle/digest;
- execution by target type/id snapshot, protocol, mode, status and time;
- snapshot membership by evidence type/native identity/release/run;
- decisions by evidence, reason, question and inclusion state;
- endpoint syntheses by substance/endpoint/state/conflict;
- ingredient projections by ingredient/substance/relationship/state;
- product assessments by product/scenario/readiness/risk-computability;
- trace traversal by artifact digest and edge role;
- replay reports by original execution/verifier state;
- governance lineage and effective current disposition.

“Latest/current” views are explicitly derived from governance effective time,
protocol status, snapshot scope and publication lineage. They never delete older
rows and must expose ambiguity when two candidates cannot be deterministically
ordered. Query projections carry canonical digest and projection schema version;
clients can request the canonical artifact for proof.

## Naming and legacy coexistence

Use `scientific_evaluation_*` for execution/result infrastructure. Do not call a
non-numeric result `score`, and do not overload existing Phase 6
`scientific_assessments`/`scientific_assessment_findings`. Candidate SQL families
are therefore conceptually `scientific_protocol_*`, `evidence_snapshot_*`,
`scientific_evaluation_*`, `scientific_result_*` and domain projections.

Legacy `score`, `confidence`, `ingredient_risk_profiles`, product score fields
and scoring services remain isolated. They are not copied into protocol inputs,
canonical result components or digests. Coexistence and comparison may occur
only later in shadow mode with an explicit adapter and labels that prevent
semantic equivalence claims.

## Migration boundary and decomposition

### Decision

```text
B — migration possible only after specific design gaps are resolved
```

The semantic entity graph and immutability/publication model are stable. A
migration is not yet authorized because these implementation-critical items
must be frozen and fixture-tested:

1. exact canonical JSON/decimal/time profile and cross-language fixtures;
2. artifact envelope, inline threshold and object-store verification contract;
3. precise SQL names/types, immutable-column protections and RLS/access model;
4. publication/reconciliation failure protocol and operational SLOs;
5. engine/dependency artifact retention and compatibility policy;
6. privacy/erasure design for user-specific scenarios;
7. projection schemas and exact indexed query workload;
8. data-model remediation for endpoint/study/dependency/form/composition and
   product history where later runtime semantics require it.

Recommended future migration decomposition, without assigning revision ids:

1. artifact registry, protocol/version and governance foundation;
2. snapshot, membership, target/mapping/product/scenario freeze structures;
3. execution, attempts, selection, result components, trace and atomic
   publication bundle;
4. domain query projections, current views, replay reports, reconciliation and
   immutable-state constraints.

Each migration must have preflight checks, restrictive foreign keys, a safe
downgrade refusal once nonrepresentable history exists, and independent rollout
validation. No giant all-in-one migration is recommended.

## Edge-case review

| # | Scenario | Required persistent behavior |
|---:|---|---|
| 1 | Protocol changed in place | Block update after publication; create new version/artifact |
| 2 | Snapshot source row later corrected | Historical member/digest stays; refresh uses new snapshot and governance links correction |
| 3 | Finding deleted upstream | Restrictive references/canonical member proof preserve execution; availability event if bytes disappear |
| 4 | Mapping changes | Replay uses mapping snapshot; refresh creates new projection |
| 5 | Product formulation changes | New composition snapshot; historical assessment unchanged |
| 6 | Parser/normalizer changes | New ingestion representation and snapshot; replay pins old versions |
| 7 | Same evidence ingested twice | Provenance may have two runs; dependency/duplicate identity prevents scientific double counting |
| 8 | Two identical executions race | Semantic uniqueness elects/reuses one publication; attempts remain auditable |
| 9 | Crash before object verification | No canonical publication; staging is retryable/GC eligible |
| 10 | Crash after object verification before DB commit | Verified orphan remains noncanonical and reconcilable |
| 11 | DB commit succeeds | All roots become reachable atomically and execution completes |
| 12 | Projection build fails after publication | Canonical result remains valid; projection rebuild is operational |
| 13 | Trace generated later | Only permitted as noncanonical presentation; canonical trace must publish with bundle |
| 14 | AI explanation differs | Canonical digests unchanged; renderings link to trace digest |
| 15 | Artifact object is corrupt | Verifier records integrity incident; result is not rewritten |
| 16 | Engine version unavailable | Replay report is `engine_incompatible`/unavailable, not a changed result |
| 17 | Protocol retired | Historical execution remains verifiable; new NORMAL use is governance-blocked |
| 18 | Result scientifically retracted | Append event/current view changes; result bytes remain |
| 19 | User-specific scenario needs erasure | Apply privacy design/tombstone without exposing or silently changing generic science |
| 20 | Future numeric component | Add reviewed typed component/version; do not alter existing result envelope or historic digests |

## Conceptual persistence and replay vectors

| # | Vector | Canonical expectation | Verification expectation |
|---:|---|---|---|
| 1 | Publish protocol v1 | Rule bytes and digest sealed once | Later byte change rejected |
| 2 | Empty evidence snapshot | Sealed zero-member manifest | Replay reproduces empty root and valid insufficiency result |
| 3 | Snapshot with two findings | Sorted membership commits both semantic identities | Row order cannot change digest |
| 4 | Excluded finding | Decision and reason persist beside candidate | Trace reaches candidate although not selected |
| 5 | Deferred identity | Deferred decision is canonical, not technical failure | Same frozen state replays identically |
| 6 | Duplicate ingestion | Two provenance members may resolve to one evidence line | No double-counting; grouping digest stable |
| 7 | Substance synthesis | Endpoint components and profile are immutable roots | Component reorder cannot change semantic digest |
| 8 | Ingredient `contains` projection | Qualified component records unknown quantity | No exposure/risk component invented |
| 9 | Multi-substance ingredient | Separate ordered projection components | No max/sum/average digest input |
| 10 | Product risk not computable | Product result stores missing dimensions/reasons | Successful completed execution, not failed |
| 11 | Same product, two scenarios | Two scenario digests and scoped results | Neither overwrites the other |
| 12 | Exact replay | Original roots and protocol reused | Selection/result/trace digests identical |
| 13 | Replay after mapping correction | Old mapping snapshot reused | Identical historical result expected |
| 14 | Counterfactual v2 | Same scientific roots, different protocol digest | New immutable result; comparison link only |
| 15 | Refresh with new release | New snapshot and input digest | Old execution remains reachable |
| 16 | Attempt crashes halfway | Partial objects stay noncanonical | Retry creates new attempt and one final bundle |
| 17 | Concurrent identical request | One semantic execution/publication | Both callers resolve to same result identity |
| 18 | Object store has same digest | Verify bytes then reuse physical artifact | Ownership/membership remains explicit |
| 19 | Projection table corrupted | Rebuild from canonical artifact | Canonical/result digests unchanged |
| 20 | Result retracted | Append governance event | Historical replay still verifies; current view shows retraction |

## Current-schema gap matrix

| Required concept | State through `0018` | Gap / future persistence requirement |
|---|---|---|
| Canonical artifact registry | Partial (`storage_objects`, checksums) | Content identity, schema/canonicalization profile, publication/reachability and inline bytes missing |
| Protocol/version | Missing | Family, immutable version, lifecycle, rule artifact and digest |
| Snapshot/membership | Partial anchors only | Sealed manifest, resolved membership and snapshot digest |
| Target identity snapshot | Missing | Historical target payload and digest |
| Mapping snapshot | Partial temporal rows | Immutable resolved mapping manifest/digest |
| Product composition snapshot | Missing | Historical membership, quantities, label provenance and digest |
| Exposure scenario | Missing | Versioned/provenanced scenario and privacy boundary |
| Execution/attempt | Partial analogous `0018` pattern | Separate scientific lifecycle, semantic key, attempts and publication |
| Selection decision | Missing | Immutable per-candidate outcomes/reasons/trace |
| Evidence line/comparison group | Missing | Dependency-aware canonical components |
| Synthesis/profile/projection/product result | Missing | Typed non-scalar canonical artifacts and projections |
| Explanation trace | Missing | Canonical DAG, edges, root and access policy |
| Governance/replay verification | Missing | Append-only events and verifier reports |
| Endpoint/study/dependency identity | Partial/missing | Versioned scientific vocabularies/lineage needed before reviewed runtime |
| Form/composition/exposure/reference data | Partial/missing | Domain persistence and review gaps remain; architecture must preserve unavailable states |

## Implementation-readiness matrix

| Capability | Classification | Rationale |
|---|---|---|
| Logical artifact graph and ownership | READY FOR SCHEMA DESIGN | Entity boundaries and immutable roots are defined |
| Canonical/projection separation | READY FOR SCHEMA DESIGN | Authority and rebuild behavior are defined |
| Execution/attempt lifecycle | READY FOR SCHEMA DESIGN | Terminal and technical states are separated |
| Atomic publication protocol | READY FOR IMPLEMENTATION DESIGN | Reachability sequence defined; failure/SLO fixtures still required |
| Governance events/current views | READY FOR SCHEMA DESIGN | Append-only semantics defined |
| Replay verifier envelope | READY FOR IMPLEMENTATION DESIGN | Inputs/outcomes defined; engine packaging policy pending |
| Digest DAG | READY FOR IMPLEMENTATION DESIGN | Non-circular boundaries defined |
| Exact canonicalization implementation | BLOCKED BY TECHNICAL FREEZE | Profile and cross-language fixtures required |
| Object-store/inline artifact envelope | BLOCKED BY TECHNICAL FREEZE | Exact cutoff, encryption and reconciliation operations required |
| Privacy persistence for user scenarios | BLOCKED BY PRIVACY DESIGN | Access, retention and erasure policy required |
| Query projections/indexes | REQUIRES WORKLOAD VALIDATION | Canonical fields known; physical access plan not benchmarked |
| Evidence selection/synthesis runtime | BLOCKED BY SCIENTIFIC REVIEW/DATA MODEL | Deterministic envelopes do not validate scientific rules |
| Composition/exposure/risk runtime | BLOCKED BY DATA AND SCIENTIFIC REVIEW | Required quantities/reference semantics are absent/unapproved |
| Numerical score | DEFERRED | Not justified for first protocol |
| API/shadow rollout | DEFERRED TO 7.8 | Persistence and validation must precede it |

## Phase 7.6 exit criteria

- [x] Current persistence patterns through `0018` audited.
- [x] Canonical artifact and query-projection boundary defined.
- [x] Content-addressed hybrid artifact strategy defined.
- [x] Persistence contract defined for every Phase 7.1–7.5 logical entity.
- [x] Execution and separate attempt lifecycles defined.
- [x] Atomic DB/object publication and canonical boundary defined.
- [x] Immutability, supersession, retraction and integrity events defined.
- [x] Replay, counterfactual and refresh persistence semantics defined.
- [x] Replay verifier and engine-compatibility requirements defined.
- [x] Machine-readable explanation/provenance graph and AI boundary defined.
- [x] Canonicalization requirements and non-circular digest DAG defined.
- [x] Referential integrity and enforcement ownership classified.
- [x] Idempotency, concurrency, crash recovery and orphan behavior defined.
- [x] Retention, security and privacy boundaries defined.
- [x] Query/current-view strategy defined.
- [x] Naming and legacy coexistence boundary defined.
- [x] Twenty failure/edge cases analyzed.
- [x] Twenty conceptual persistence/replay vectors defined.
- [x] Current-schema gap and implementation-readiness matrices completed.
- [x] Migration authorization decision and decomposition recorded.

## Roadmap decision and next checkpoint

Phase 7.6 completes the persistence architecture but does not authorize a
migration. Before Phase 7.7 scientific validation, WYE needs a bounded technical
checkpoint:

```text
Phase 7.6.1 — Canonicalization, Persistence Schema and Publication Protocol Freeze
```

It should resolve the eight Decision B gaps, produce exact schema/constraint and
canonical byte fixtures, define object-store/privacy operations and specify
migration slices. A subsequent implementation checkpoint may create the
approved persistence foundation; only then should replay fixtures and expert
validation in Phase 7.7 rely on durable runtime artifacts.

This document does not start 7.6.1 or 7.7.
