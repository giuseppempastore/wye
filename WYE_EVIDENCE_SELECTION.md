# WYE — Evidence Eligibility and Selection Contract

## Status and scope

This document is the canonical Phase 7.2 specification for evidence eligibility,
applicability and deterministic selection. It specializes the frozen contracts
in:

- `Checkpoints/WYE_PHASE_7.md`;
- `WYE_SCORING_SEMANTICS.md`;
- `WYE_SCORING_PROTOCOL.md`;
- `WYE_SCORING_EXECUTION_MODEL.md`.

It defines the output contract of a future selector. It does not implement that
selector and does not define endpoint synthesis, hazard conclusions, formulas,
weights, thresholds, ranking or a numerical score.

Review baseline:

```text
branch: ingredients_score
HEAD: 398581fe93b154ffdb49d6a93005485f6888bbca
origin/ingredients_score: 398581fe93b154ffdb49d6a93005485f6888bbca
working tree before Phase 7.2: clean
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017_ingredient_mapping_history
```

The five canonical documents, migrations through `0018`, scientific ingestion
contracts, persistence model and real EFSA QPS/OpenFoodTox adapters were reviewed.
The local scientific assessment/finding tables are currently empty, so provider
semantics below are derived from versioned adapter output contracts rather than
assuming representative local rows.

## Non-negotiable boundaries

```text
scientific evidence != scientific scoring
evidence availability != evidence eligibility
evidence eligibility != evidence relevance
evidence relevance != evidence quality
included evidence != positive evidence
excluded evidence != negative evidence
absence of evidence != evidence of danger
AI != scientific source of truth

different endpoints are not averaged
providers have no global weights
EFSA is not automatically superior to OpenFoodTox
OpenFoodTox is not automatically inferior to EFSA
```

Source precedence is permitted only for explicit supersession,
correction/retraction, question-specific regulatory applicability,
protocol-defined relevance or an explicit scientifically reviewed rationale.

## Selection boundary

```text
Evidence Snapshot
→ Candidate Evidence
→ Eligibility
→ Relevance / Applicability
→ Duplicate / Dependency Resolution
→ Selection Decisions
→ Selected Evidence Set
→ Phase 7.3 synthesis, not defined here
```

Selection classifies evidence for a question. It never determines whether an
effect is adverse, whether findings agree, or what hazard conclusion follows.

## Evidence-object taxonomy

### Provenance and selection roles

| Object | Role in selection | First-protocol selection unit? |
|---|---|---|
| `source_dataset_release` | Scientific release identity, publication/acquisition context and release lifecycle gate | No |
| `scientific_release_artifact` | Immutable raw-byte provenance and checksum proof | No |
| `scientific_ingestion_run` | Specific parser/normalization representation of one release | No |
| `scientific_assessment` | Scientific and lifecycle context for its findings; may carry a source-level proposition | Normally no; declared exception only |
| `scientific_assessment_finding` | Smallest persisted source-derived proposition with endpoint/value/context | Yes, normally the atomic candidate |
| dependency-aware evidence line | One or more candidate records sharing an underlying study/proposition lineage | Grouping unit used to prevent false independence |

### Selection-unit decision

For the first protocol:

```text
finding = atomic evidence candidate
assessment = mandatory context and lifecycle envelope
evidence line = dependency-aware grouping for future synthesis
```

This is not the claim that every finding is an independent study. One assessment
may produce multiple related findings, and multiple assessments may represent
the same underlying study.

An assessment-level candidate is allowed only when all are true:

- the source proposition exists at assessment level and is not reducible to a
  finding;
- a published protocol declares the assessment-level semantic role;
- identity, provenance, question and dependency handling remain explicit;
- no finding and its parent assessment are counted as two independent lines.

The current real adapters do not require this exception. EFSA QPS materializes
its recommendation and qualifications as findings; OpenFoodTox materializes one
reported-study finding under its assessment.

### Non-synonymous evidence states

| Term | Definition |
|---|---|
| `available evidence` | Frozen snapshot member whose historical content/provenance is available, before protocol classification |
| `candidate evidence` | Available assessment/finding placed in scope for one target/question and assigned a candidate identity |
| `eligible evidence` | Candidate that passes structural, identity, provenance, time, lifecycle, release/run, channel and protocol gates |
| `relevant evidence` | Eligible candidate whose endpoint and scientific context can contribute to the declared question |
| `applicable evidence` | Relevant candidate that may transfer to the exact target context under protocol-approved assumptions |
| `selected evidence` | Candidate with final decision `included` and an explicit selection role |
| `excluded evidence` | Candidate with final decision `excluded`; retained in trace with reasons |
| `deferred evidence` | Excluded for this execution because a required resolution/input is absent; marked potentially resolvable rather than scientifically negative |

Availability does not guarantee candidacy. Eligibility does not guarantee
applicability. Inclusion says only that the record may enter the next protocol
stage in its declared role.

## Candidate construction

A snapshot member becomes a candidate when the canonical candidate-builder can
associate it with the frozen target or an explicit unresolved target candidate
and the declared question. Candidate construction records:

- stable source/release/run/assessment/finding identity;
- candidate semantic-content digest;
- target identity or unresolved identity reference;
- parent assessment context;
- raw evidence channel and evidence type;
- question and protocol context;
- available source-native lineage keys.

A finding with a missing/invalid parent assessment is still represented as a
candidate if discoverable in the snapshot, but is structurally ineligible. This
ensures the orphan is audited rather than silently disappearing. An assessment
without findings remains context-only unless the protocol declares the
assessment-level exception; otherwise it produces no selected evidence unit.

## Eligibility and applicability model

### Eligibility

Eligibility answers:

```text
May this candidate participate in this protocol at all?
```

The eligibility gate covers independently recorded dimensions:

| Dimension | Examples of passing conditions |
|---|---|
| Identity | Target identity is resolved or the protocol explicitly supports an unresolved review output |
| Provenance | Source, dataset, release, artifact, successful run and record lineage are auditable |
| Snapshot/time | Record was available by `snapshot_as_of` and scientifically admissible under `evidence_cutoff` |
| Release/run | Release status and one normalized ingestion representation satisfy the protocol |
| Lifecycle | Assessment status is permitted for the execution mode |
| Structure | Parent context and protocol-required fields exist |
| Channel/type | Evidence channel and evidence type are supported by the protocol |
| Quality gate | Only an externally reviewed minimum criterion, if declared, may exclude; source prestige is never a proxy |

### Relevance

Relevance answers whether the evidence addresses the declared question. It is a
vector, not a source-level flag:

```text
target entity
endpoint
population/species/model system
sex, when material
route
duration
dose/value context
study/evidence type
scenario and assessment purpose
substance form
```

Each dimension is one of:

```text
match
mismatch
unknown
not_applicable
requires_governed_mapping
```

### Applicability

Applicability answers whether relevant evidence may be used for the exact target
context. Its state is:

```text
applicable
not_applicable
undetermined
not_evaluated
```

An eligible record may be irrelevant or not applicable. Unknown context is not a
match. A protocol may permit `included` with an explicit unknown optional
dimension only after scientific review has declared that dimension non-blocking
for the exact question.

Quality remains separate. A relevant/applicable record may have limitations; a
high-quality record may be irrelevant.

## Decision lifecycle

The logical lifecycle is a staged evaluation with independently preserved
dimensions:

```text
candidate_constructed
→ eligibility_evaluated
→ relevance_dimensions_evaluated
→ applicability_evaluated
→ duplicate_dependency_evaluated
→ final_decision_recorded
```

Dependency grouping may be computed in parallel with relevance because it needs
the entire candidate universe. Finalization waits for both. A short-circuited
stage is stored as `not_evaluated_due_to_<stage>` rather than guessed.

Canonical primary-reason precedence is:

1. candidate/parent identity and structural integrity;
2. provenance, snapshot availability and cutoff;
3. release/run representation and lifecycle;
4. supported domain/channel/type and required structure;
5. relevance and applicability;
6. duplicate/dependency disposition;
7. inclusion role.

All applicable secondary reasons are retained in canonical sorted order. This
precedence chooses one primary explanation; it does not change the underlying
dimension states or allow encounter order to affect the result.

The Phase 7.1 binary `decision` remains:

```text
included | excluded
```

`deferred` is a `resolution_state`, not a third inclusion decision. Deferred
candidates are excluded from the selected set for that execution and carry a
`deferred_*` primary reason. This preserves the Phase 7.1 contract while
distinguishing unresolved data from scientific exclusion.

## Versioned reason-code taxonomy

### Vocabulary model

The model is hybrid:

- `wye_selection_core/v1` owns cross-protocol structural, provenance, time,
  lifecycle and generic dependency reasons;
- each protocol owns a versioned scientific namespace, initially
  `food_tox_evidence_selection/v1`, for question-specific relevance and
  applicability reasons.

Every reason definition contains a stable ID, immutable human definition,
decision stage, required context, determinism basis, retryability and whether
new data/governed resolution may change a future execution.

All applications are deterministic once canonical inputs and governed mappings
are frozen. `reviewed` below means deterministic after a versioned human review
artifact; it never means an AI judgement during execution.

### Inclusion reasons

| Stable ID | Definition / required context | Stage | Basis | Retryable / resolvable |
|---|---|---|---|---|
| `included_applicable` | All required gates pass and candidate is applicable as a contributing evidence unit | Final | Deterministic | No for same inputs; refresh/version may differ |
| `included_applicable_unknown_optional_context` | An explicitly optional dimension is unknown under a scientifically reviewed protocol rule | Final | Reviewed rule | No for same inputs; new data may remove limitation |
| `included_context_only_dependency_declared` | Eligible/applicable derived or dependent record is retained only as context, never independent corroboration | Dependency/final | Deterministic or reviewed lineage | New lineage may refine role |

### Core exclusion reasons

| Stable ID | Definition / required context | Stage | Basis | Retryable / resolvable |
|---|---|---|---|---|
| `excluded_missing_assessment_context` | Finding lacks a valid parent assessment/context | Structure | Deterministic | New/corrected data |
| `excluded_unresolved_identity` | Candidate cannot be assigned to the frozen target | Identity | Deterministic from resolution state | Governed identity decision |
| `excluded_insufficient_provenance` | Origin or transformation cannot be audited | Provenance | Deterministic | New provenance/artifact |
| `excluded_outside_evidence_cutoff` | Scientific publication/effective date is later than cutoff | Time | Deterministic | New execution cutoff only |
| `excluded_not_available_as_of` | Artifact/normalized representation was not available in WYE at snapshot as-of | Time | Deterministic | Later snapshot only |
| `excluded_ineligible_release_status` | Frozen release status is not permitted | Release | Deterministic | New status/snapshot or protocol |
| `excluded_ineligible_ingestion_run` | Run is non-successful or fails declared representation policy | Run | Deterministic | Successful/new allowed run |
| `excluded_unsupported_representation` | Parser/normalization/config version is outside the protocol contract | Run | Deterministic | Protocol/new representation |
| `excluded_pending_review` | Current DB status `pending_review` cannot support published output | Lifecycle | Deterministic | Governed publication/status event |
| `excluded_superseded` | Frozen status or applicable explicit successor establishes that the predecessor is not current | Lifecycle | Deterministic from status; governing successor requires lineage | Historical mode or lineage change |
| `excluded_withdrawn` | Current DB status `withdrawn` is ineligible for current conclusion | Lifecycle | Deterministic | Historical as-of only |
| `excluded_retracted` | Future normalized retraction event makes record ineligible | Lifecycle | Deterministic with event | Historical as-of only |
| `excluded_rejected` | Current DB status `rejected` | Lifecycle | Deterministic | No for same snapshot |
| `excluded_unsupported_evidence_channel` | Protocol does not accept the candidate channel | Channel | Deterministic | Protocol version |
| `excluded_unsupported_evidence_type` | Evidence type is not declared for the channel/question | Channel | Deterministic | Protocol version or normalized type |
| `excluded_exact_duplicate` | Same scientific record, lineage and semantic content is already represented | Dependency | Deterministic | New lineage could disprove duplicate |
| `excluded_reingested_representation` | Same source record/release was materialized by an equivalent run already selected as representative | Dependency | Deterministic | Representation policy/version |
| `excluded_dependent_redundant` | Candidate is fully represented by its dependency parent and adds no declared role | Dependency | Deterministic/reviewed lineage | New lineage/role |

### First-protocol scientific exclusion reasons

| Stable ID | Definition / required context | Stage | Basis | Retryable / resolvable |
|---|---|---|---|---|
| `excluded_wrong_target` | Evidence addresses a different substance/form/target | Relevance | Reviewed identity scope | Corrected mapping/new protocol |
| `excluded_wrong_endpoint` | Normalized endpoint/semantic role cannot answer the question | Relevance | Reviewed ontology/rule | Ontology/protocol version |
| `excluded_wrong_population` | Population/species/model system is incompatible | Relevance/applicability | Scientific review | New question/protocol |
| `excluded_wrong_sex_context` | Sex context is incompatible where material | Relevance/applicability | Scientific review | New question/protocol |
| `excluded_wrong_route` | Explicit route is incompatible | Relevance/applicability | Scientific review | New question/protocol |
| `excluded_wrong_duration` | Explicit duration context is incompatible | Relevance/applicability | Scientific review | New question/protocol |
| `excluded_wrong_scenario` | Dose/use/study scenario is incompatible | Relevance/applicability | Scientific review | New question/protocol |
| `excluded_not_relevant` | Context cannot contribute to the exact scientific question | Relevance | Scientific review | New protocol/context |
| `excluded_not_applicable` | Relevant generally, but transfer to target context is not permitted | Applicability | Scientific review | New protocol/context |
| `excluded_quality_not_assessable` | A declared mandatory quality appraisal cannot be performed | Quality gate | Scientific review | New methodological data |
| `excluded_below_quality_requirement` | Candidate fails an approved, explicit minimum criterion | Quality gate | Scientific review | New protocol or corrected evidence |

### Deferred/unresolved reasons

All of these have final decision `excluded` and `resolution_state=deferred`.

| Stable ID | Definition / required context | Stage | Basis | Retryable / resolvable |
|---|---|---|---|---|
| `deferred_missing_required_context` | A protocol-required dimension is absent | Structure/applicability | Deterministic | New normalized data |
| `deferred_scientific_date_unknown` | Cutoff compliance cannot be established | Time | Deterministic | Source/release date |
| `deferred_endpoint_ontology_unresolved` | Raw endpoint has no governed normalized identity | Relevance | Deterministic from mapping state | Ontology review |
| `deferred_population_model_unresolved` | Population/species/model cannot be normalized | Relevance | Deterministic from mapping state | Normalization/review |
| `deferred_route_unresolved` | Route is missing/ambiguous and material to the question | Applicability | Deterministic | New data/reviewed mapping |
| `deferred_duration_unresolved` | Duration is missing/ambiguous and material | Applicability | Deterministic | New data/reviewed mapping |
| `deferred_unit_semantics_unresolved` | Value/unit/basis cannot be interpreted for the requested use | Structure/applicability | Deterministic | Unit/context normalization |
| `deferred_dependency_unresolved` | Independence/dependence cannot be established where it changes permitted role | Dependency | Deterministic from lineage state | Study/dependency review |
| `deferred_correction_lineage_unresolved` | Correction/supersession claim lacks a provable predecessor/successor relation | Lifecycle | Deterministic | Lineage event |
| `deferred_scientific_review_required` | A protocol-declared governed decision is absent | Any scientific gate | Deterministic from missing review artifact | External review |

The Phase 7.0.1 conceptual codes remain semantic predecessors. Because no Phase
7 selection protocol has been published or executed, the precise Phase 7.2
names introduce no historical break. Mappings include:

```text
included → included_applicable
included_partial_context → included_applicable_unknown_optional_context
excluded_outside_cutoff → excluded_outside_evidence_cutoff
excluded_ineligible_release → excluded_ineligible_release_status
excluded_ineligible_run → excluded_ineligible_ingestion_run
excluded_duplicate → excluded_exact_duplicate or excluded_reingested_representation
excluded_dependent_evidence → excluded_dependent_redundant
```

Published vocabulary versions are immutable. New meanings require new IDs or a
new vocabulary version; deprecated codes are never reused.

## Assessment lifecycle eligibility

### Status reality through `0018`

`scientific_assessments.assessment_status` permits exactly:

```text
pending_review
published
superseded
withdrawn
rejected
```

There is no current DB status named `active`, `current`, `retracted`, `corrected`,
`draft` or `unknown`.

| Concept | Current/future representation | Current-mode selection semantics |
|---|---|---|
| Active/current | Derived view, not a persisted assessment status | `published` plus valid time and no applicable withdrawal/successor may be eligible |
| Published | Current status exists | May pass lifecycle gate; all other gates still apply |
| Pending review | Current status exists; closest current analogue to draft | Excluded from published output |
| Superseded | Current status exists; explicit successor relation is missing | Excluded from current use; missing successor identity adds `deferred_correction_lineage_unresolved` to the trace |
| Withdrawn | Current status exists | Excluded from current scientific use; preserved historically |
| Rejected | Current status exists | Excluded |
| Retracted | Future normalized governance event/status requirement | Excluded current; distinct from generic withdrawal when source semantics support it |
| Corrected | Must be a lineage relation/event, not an in-place mutation | Original and correction preserved; applicable correction may govern current use |
| Draft | Future source-normalized status; must not be silently mapped to published | Excluded from published output |
| Unknown | Future normalization outcome | Deferred or excluded under explicit protocol; never treated as published |

```text
scientific historical preservation != current scientific eligibility
```

Historical snapshots preserve the frozen status and record even when current
selection excludes it. The schema currently lacks temporal status history and
explicit assessment correction/supersession edges, so exact historical status
reconstruction is a data-model gap unless already frozen by a future snapshot.

## Time semantics

| Time concept | Governs | Canonical source |
|---|---|---|
| `snapshot_as_of` | Which identities, mappings, artifacts and normalized representations were available to WYE | Frozen snapshot boundary plus `created_at`/acquisition/run completion and historical mapping state |
| `evidence_cutoff` | Latest scientific publication/effective evidence admissible for the question | Assessment `published_at` or protocol-approved release `released_at`; never ingestion order |
| Release publication | Scientific release chronology | `source_dataset_releases.released_at` |
| Release acquisition | When bytes entered WYE | Release/artifact `acquired_at` |
| Assessment validity | Scientific/effective applicability interval | Assessment `valid_from`/`valid_to`, if populated |
| Ingestion time | Availability of one normalized representation | Run `created_at`, `started_at`, `completed_at` |
| Mapping validity | Target relationship as-of | Mapping `valid_from`/`valid_to`, review/materialization history |

Snapshot membership should include records available by `snapshot_as_of` even
when their scientific date is later than `evidence_cutoff`, so the selector can
record `excluded_outside_evidence_cutoff`. The two boundaries answer different
questions.

```text
latest ingested != latest scientific evidence
```

`created_at`, `acquired_at` and run completion prove WYE availability; they do
not substitute for scientific publication. If scientific date is absent:

- a protocol may use an explicit release-level scientific date only when source
  granularity and rationale are declared;
- otherwise cutoff compliance is deferred with
  `deferred_scientific_date_unknown`;
- ingestion date must never be silently used as publication date.

All time comparisons require UTC timestamps and explicit inclusive/exclusive
boundary semantics in the future protocol canonical representation. Existing
`DATE` mapping/assessment validity requires a published day-boundary convention.

## Release and ingestion-representation policy

Scientific selection references both:

```text
scientific release identity
+ specific normalized ingestion representation
```

Release identity establishes source science. The run establishes how immutable
artifacts became WYE assessment/finding rows.

A canonical representation policy evaluates, in order:

1. exact source/dataset/external-release identity;
2. immutable artifact manifest and raw checksum;
3. successful terminal ingestion status;
4. allowed adapter, acquisition, parser and normalization versions;
5. allowed semantic configuration digest;
6. parser-output and record-content fingerprints;
7. explicit protocol preference when different allowed representations are not
   semantically equivalent.

Equivalent runs are grouped by release identity, artifact manifest, semantic
configuration and equivalent output digests. One representative is selected by
the lexicographically smallest stable run key after canonical normalization;
this tie-break has no scientific precedence. Other equivalent runs receive
`excluded_reingested_representation`.

If allowed parser/normalization versions produce different semantic content,
they are not duplicates. The protocol must designate a representation version
with rationale or defer selection; “newest run wins” is forbidden.

```text
duplicate ingestion != duplicate scientific evidence
```

## Duplicate-evidence model

### Identity layers

| Identity | Purpose | Current anchors |
|---|---|---|
| Artifact identity | Same raw bytes | Artifact SHA-256/size and manifest |
| Release-record identity | Same source-native record within a release | Source/dataset/release plus `source_record_key` |
| Normalized-content identity | Same WYE semantic payload | Assessment normalized checksum and finding fingerprint |
| Study identity | Same underlying experiment/study across records/providers | OpenFoodTox IUCLID document UUID/literature reference where available; otherwise gap |
| Proposition identity | Same endpoint observation/conclusion in same context | Future normalized endpoint/context/dependency key |

### Required outcomes

| Case | Classification and selection handling |
|---|---|
| Byte/content-identical copy with same lineage | `duplicate`; select one canonical representative, exclude copies |
| Same source record reingested | Representation duplicate; select one canonical normalized representation |
| Same study in multiple datasets | Dependent/duplicate only when shared study identity or reviewed lineage proves it; otherwise `unknown dependency` |
| Same endpoint from same study | Usually related findings within one evidence line; not collapsed unless proposition/content are also identical |
| Derived summary of primary evidence | `derived`; preserve dependency and channel, never count as independent |
| Independent study with identical value | Independent; both may be selected because equality of value proves nothing about lineage |

```text
same value != duplicate
```

## Evidence-dependency model

Each dependency edge has:

```text
dependency_relationship
source_candidate_key
target_candidate_key
dependency_group_key
basis_type
basis_reference
resolution_status
review_provenance, when governed
```

Allowed conceptual relationships:

| State | Meaning | Selection implication |
|---|---|---|
| `independent` | Evidence has distinct underlying data/proposition lineage | May contribute independently if all other gates pass |
| `partially_dependent` | Some data, cohort, experiment or analytical basis overlaps | May be selected only with declared non-independent role; no weights inferred |
| `derived` | Record summarizes/indexes/cites parent evidence | Context-only or redundant disposition according to protocol |
| `duplicate` | Same scientific proposition/content and lineage | One canonical representative only |
| `unknown_dependency` | Available data cannot establish relationship | Never assume independence; defer or include context-only only if reviewed protocol allows |

Examples include one provider indexing another, reviews summarizing primary
studies, regulatory assessments citing studies also stored separately and one
experiment producing several findings. This model prevents future double
counting without introducing weights.

## Endpoint semantics and ontology readiness

Three representations are required conceptually:

```text
raw_endpoint
normalized_endpoint_key + ontology_version
endpoint_mapping_status/provenance
```

Current reality:

- EFSA QPS emits fixed source-semantic endpoints `qps_status` and
  `qps_qualification`;
- OpenFoodTox emits raw IUCLID effect-level or administrative endpoint text;
- `scientific_assessment_findings.endpoint` is free text and has no universal
  ontology or mapping history.

`same endpoint` requires the same governed normalized endpoint key/version and
compatible definition/scope. `different endpoint` requires a governed
different/incompatible relation. Otherwise the relation is `unknown`, even when
raw labels look similar.

A future minimal endpoint ontology needs:

- stable endpoint key and ontology version;
- definitions and source mappings;
- exact/equivalent/broader/narrower/related/incompatible relationships;
- mapping method, reviewer/provenance and validity;
- substance form, measurement construct and unit expectations;
- immutable historical mappings.

Full ontology implementation is not part of 7.2. Unresolved mapping produces
`deferred_endpoint_ontology_unresolved` for endpoint-specific questions.

## Population, species and model-system semantics

Normalized model context must distinguish at least:

```text
human
animal + explicit species
in_vitro
other_model_system
unknown
not_applicable
```

OpenFoodTox currently concatenates available species, sex and route into
`population_context`; the underlying keys remain in `raw_payload`. They are not
separate normalized fields. QPS identifies a microbial taxon being recommended,
not an experimental population.

Animal, in-vitro and other evidence remain separate context lines. Any transfer
to human relevance or risk requires a scientifically reviewed applicability
rule. The selector records correspondence/unknown status only; it does not make
that scientific inference.

## Route semantics

The future normalized vocabulary minimally needs:

```text
oral
dermal
inhalation
intravenous
other + source term
unknown
not_applicable
```

Only mappings supported by source data and reviewed vocabulary are valid.
OpenFoodTox may preserve route in raw payload and the combined population text;
QPS status/qualification has route `not_applicable` unless a future scientific
review establishes a narrower role.

For a food-toxicology question requiring oral evidence:

- explicit normalized `oral` may match;
- an explicit different route may be `not_applicable`;
- `unknown` is not equivalent to oral and remains undetermined;
- inclusion with unknown route is allowed only when the published question
  declares route non-material.

## Duration semantics

Required conceptual states are:

```text
acute
short_term
subchronic
chronic
other + source term
unknown
not_applicable
```

Phase 7.2 defines no temporal thresholds for these terms. Boundaries and source
mappings require a recognized domain specification and external scientific
review. Duration may exist in OpenFoodTox raw payload but is not consistently
normalized; QPS status/qualification has duration `not_applicable`. Duration-
specific applicability is therefore a current data gap.

## Dose, value and unit readiness

Phase 7.2 does not calculate dose-response or convert units. A finding is:

| Readiness | Contract |
|---|---|
| `structurally_usable` | Endpoint/proposition is explicit; value semantics, qualifier, unit/basis where dimensioned, and context required by the question are structured |
| `usable_after_normalization` | Raw fields are sufficient but require a governed endpoint/unit/context mapping |
| `ambiguous` | Multiple interpretations remain, such as missing dose basis or qualifier scope |
| `not_interpretable` | Meaning cannot be reconstructed from normalized plus raw payload |
| `not_applicable` | The channel is non-quantitative, for example QPS recommendation status |

OpenFoodTox currently may expose `value_numeric`, `value_text`, `unit` and raw
qualifier/context. A numeric value without unit or dose basis is not automatically
quantitatively comparable. QPS findings are valid text propositions for their
regulatory-status channel; missing numeric value/unit is not a defect there.

## Missing-field policy

Concrete requiredness is part of the published scientific question. The first
protocol envelope sets these defaults without pretending they are scientifically
validated transfer rules:

| Dimension | Eligibility | Applicability | Missing behavior |
|---|---|---|---|
| Endpoint/semantic role | Required to identify question contribution | Required for endpoint-specific question | Defer unresolved ontology; do not wildcard |
| Population/species/model | Protocol-dependent structural field | Required when question is population/model-specific | Unknown dimension or defer if material |
| Sex | Optional unless declared material | Protocol-dependent | Record unknown; never infer both sexes/general population |
| Route | Protocol-dependent | Required for route-specific question | Unknown is not oral; defer if material |
| Duration | Protocol-dependent | Required for duration-specific question | Unknown dimension or defer if material |
| Value/proposition | Some interpretable proposition is required | Quantitative use requires sufficient semantics | Exclude not-interpretable or retain qualitative role if protocol allows |
| Unit/dose basis | Optional for non-quantitative proposition | Required for dimensioned quantitative comparison | Defer unit semantics; no automatic conversion |
| Study/evidence type | Required for channel classification | Protocol-dependent | Exclude unsupported or defer unresolved type |

Missing never automatically means exclude, include, safe, dangerous or zero.
`eligible_with_unknown_dimension` is represented by eligibility passing while
the dimension is `unknown`; final inclusion still requires a published rule that
declares the unknown non-blocking.

## Conflict pre-classification

Phase 7.2 classifies comparability, not agreement or scientific conflict.

A canonical comparison signature covers:

```text
target/substance form
evidence channel and semantic role
normalized endpoint
population/species/model and sex
route
duration
dose/value construct and unit basis
scenario/assessment purpose
time/current-version scope
dependency group
```

| State | Meaning |
|---|---|
| `comparable` | Required signature dimensions match or have an approved equivalence |
| `contextually_different` | Both records are meaningful but differ on a material scoped dimension |
| `not_comparable` | Channels/constructs/questions are categorically different |
| `comparability_unresolved` | Missing ontology/context prevents classification |
| `potential_conflict_set` | Canonical group of comparable selected evidence lines passed to Phase 7.3 |

Only `comparable` records enter the same potential conflict set. Oral chronic
and dermal acute evidence is `contextually_different`, not an immediate conflict.
Phase 7.3 will decide whether comparable contributions are concordant or
discordant.

## EFSA QPS and OpenFoodTox treatment

### EFSA QPS

The real adapter emits:

```text
assessment_type: efsa_qps_recommendation
assessment_status: published
finding endpoint: qps_status
finding value_text: recommended
finding endpoint: qps_qualification, zero or more
evidence_type: efsa_qps_list
target identity: normalized microbial taxon
```

This is a regulatory recommendation/status record with qualification text. It
is not an experimental toxicology endpoint, a universal safety conclusion or a
product-risk estimate. Its exact scientific scope and applicability require
external review of the QPS framework and qualification semantics.

### OpenFoodTox

The real adapter emits:

```text
one IUCLID study assessment per source document UUID
assessment_status: published
assessment_type: source IUCLID Definition
finding endpoint: raw effect-level/admin endpoint
numeric/text value and unit when available
population_context: available species + sex + route
evidence_type: openfoodtox_iuclid_reported_study
raw study/method/effect payload retained
```

This is experimental toxicology evidence represented from an IUCLID study
record. Its endpoint, population, route, duration, unit and study identity need
governed normalization before broad comparison.

### Comparability decision

```text
QPS recommendation != OpenFoodTox experimental endpoint
```

They belong to different evidence channels and are not directly comparable,
even when linked to the same canonical substance/taxon. Neither provider has
global precedence. A protocol may display both scoped channels or use one for a
question-specific purpose only after scientific review.

## Evidence channels

The minimal taxonomy justified by current data is:

| Channel | Current source | Semantic role |
|---|---|---|
| `regulatory_status_and_qualification` | EFSA QPS | Source-specific recommendation/status and conditions/qualifications |
| `experimental_toxicology` | OpenFoodTox IUCLID reported studies | Study-derived endpoint/value/context evidence |
| `source_assessment_context` | Parent assessments from either adapter | Lifecycle, purpose, document and provenance context; not independent by default |

Observational, mechanistic and broad regulatory-assessment channels are reserved
for future adapters/protocol versions; they are not invented as current content.
Sharing a substance does not permit cross-channel aggregation.

## Evidence-selection-decision contract

The complete logical payload is:

| Field | Canonical meaning |
|---|---|
| `selection_schema_version` | Version of this payload/canonicalization contract |
| `decision_key` | Stable digest-derived identity within execution |
| `execution_key` | Owning execution reference; ID excluded from decision digest when non-semantic |
| `snapshot_key`, `snapshot_digest` | Frozen candidate universe |
| `protocol_key`, `protocol_version_key`, `protocol_digest` | Exact effective rule context |
| `target_identity_digest` | Frozen evaluated target |
| `question_key`, `question_context_digest` | Exact endpoint/scenario question |
| `candidate_key`, `candidate_content_digest` | Atomic candidate and semantic payload |
| `selection_unit_type` | Finding or declared assessment-level exception |
| `evidence_channel`, `evidence_type` | Versioned semantic role |
| `representation_key` | Canonical release/run representation |
| `eligibility_state` and dimensions | `eligible`, `ineligible` or `undetermined` plus gate results |
| `relevance_dimensions` | Endpoint/population/sex/route/duration/dose/type/scenario/target states |
| `applicability_state` | Applicable, not applicable, undetermined or not evaluated |
| `quality_gate_state` | Separate minimum-gate state; no numeric quality |
| `dependency_state`, `dependency_group_key` | Independence/dependency result and grouping |
| `representative_candidate_key` | Canonical duplicate/dependency representative, if any |
| `comparison_group_key` | Potential-comparability group, if established |
| `decision` | `included` or `excluded` |
| `selection_role` | `contributing`, `context_only` or `none` |
| `resolution_state` | `resolved` or `deferred` |
| `primary_reason_code`, `secondary_reason_codes` | Versioned canonical explanations |
| `rule_references` | Exact protocol rules producing each state |
| `decision_trace` | Ordered stage inputs/outcomes and dependency edges |
| `decision_digest` | SHA-256 of canonical semantic decision payload |

Presentation-only metadata includes localized definitions, prose explanation,
UI labels, colours, generated timestamps, worker IDs and AI-rendered text. It is
excluded from the decision digest and cannot change selection.

## Determinism and canonical ordering

Canonical selection input consists of:

```text
protocol/version/digest
+ snapshot/digest
+ frozen target identity digest
+ question/context digest
+ candidate content and lineage digests
+ versioned ontology/reason/dependency vocabularies
+ governed mapping/review artifacts
```

The transformation is:

```text
canonical selection input
→ deterministic candidate and group evaluation
→ canonical decision payload per candidate
→ decision_digest
→ canonical ordered decision set
→ selection_digest
```

Selection outcomes are order-independent. Duplicate/dependency groups are built
from the full universe before representative selection. Canonical serialization
sorts candidates by stable candidate key and set-like reason/edge collections by
their stable keys. Source order is retained only as source data, never as a
selection priority.

No runtime timestamp, database row order, surrogate ID, locale, worker,
concurrency schedule, presentation formatting or generated explanation may
affect a decision.

### Selection-set identity

`selection_digest` commits to the minimum complete proof boundary:

- selection schema/canonicalization version;
- protocol and eligibility-policy digest;
- snapshot digest, which commits to the candidate universe;
- target and question-context digests;
- canonically sorted tuples of candidate key, candidate content digest,
  decision digest, decision/role/resolution state and dependency/comparison
  group keys.

The full candidate payload is not duplicated because snapshot and candidate
content digests already commit to it. Reason codes and dimension states are
inside each decision digest. Changing row order, Markdown/UI formatting,
localized or AI explanation, execution timestamp or worker leaves the digest
unchanged.

## Edge-case matrix

`Selected` below never implies a positive or adverse scientific conclusion.

| # | Case | Candidate? | Eligible? | Applicable? | Selected? / primary reason | Historical behavior |
|---:|---|---|---|---|---|---|
| 1 | Finding without valid assessment | Yes, if snapshot-discoverable | No | Not evaluated | No — `excluded_missing_assessment_context` | Orphan and decision retained |
| 2 | Assessment without findings | Context only; candidate only under declared exception | Protocol-dependent | Protocol-dependent | Normally no evidence unit | Assessment remains in snapshot/trace |
| 3 | Source-native identity unresolved | Yes with unresolved target ref | No/undetermined | Not evaluated | No — `excluded_unresolved_identity` | Future resolution causes refresh, not replay mutation |
| 4 | Assessment superseded | Yes | No in current mode with governing lineage | Not evaluated | No — `excluded_superseded` | Historical pre-supersession snapshot remains unchanged |
| 5 | Withdrawn/retracted assessment | Yes | No current | Not evaluated | No — `excluded_withdrawn`/`excluded_retracted` | Historical record retained |
| 6 | Duplicate ingestion | Yes for each representation | One canonical representation eligible | Same as representative | Copy no — `excluded_reingested_representation` | All runs retained |
| 7 | Same study in two datasets | Yes | Potentially | Question-dependent | Dependency-aware; defer if lineage unresolved | Both source records retained |
| 8 | Same finding, different parser version | Yes | Representation policy decides | Same only if semantics equivalent | Equivalent copy excluded; divergent output deferred/designated | Both normalized runs retained |
| 9 | Endpoint missing | Yes | May pass non-endpoint structural gates | Undetermined | No — `deferred_endpoint_ontology_unresolved` or missing-context reason | New normalization creates refresh |
| 10 | Route missing | Yes | Yes if route is not structural eligibility | Undetermined if route material | Deferred, or included with unknown only by published rule | Missing state retained |
| 11 | Population/species missing | Yes | Usually yes | Undetermined if material | Deferred or scoped unknown by published rule | Missing state retained |
| 12 | Unknown unit | Yes | May remain qualitatively eligible | Undetermined for quantitative use | No quantitative role — `deferred_unit_semantics_unresolved` | Raw value/unit retained |
| 13 | Newer scientific release ingested earlier | Yes if available as-of | Scientific chronology, not ingestion order, governs | Question-dependent | Protocol release policy decides | Both times retained |
| 14 | Older release acquired after newer release | Candidate only after acquisition/as-of | Release/current policy decides | Question-dependent | Acquisition order gives no precedence | Both release/acquisition times retained |
| 15 | QPS + OpenFoodTox same target | Yes, separate candidates | Each channel evaluated separately | Different questions/roles | Never merged; usually not comparable | Both channels preserved |
| 16 | Evidence outside cutoff | Yes if available as-of | No | Not evaluated | No — `excluded_outside_evidence_cutoff` | Remains in snapshot decision trace |
| 17 | Evidence corrected after historical snapshot | Historical original only in old snapshot | Frozen old eligibility | Frozen | Replay unchanged; refresh evaluates correction | Both executions/results preserved |
| 18 | Different protocol on same snapshot | Same candidates | Recomputed under new version | Recomputed | Counterfactual decisions/digest may differ | Original selection remains immutable |

## Conceptual deterministic selection vectors

The expected digest is equality/difference semantics, not a literal hash value.

| # | Inputs | Eligibility / applicability | Dependency | Decision and reason | Digest expectation |
|---:|---|---|---|---|---|
| 1 | Published, resolved, in-cutoff finding matching all declared context | Eligible/applicable | Independent | Include — `included_applicable` | Same canonical inputs reproduce decision digest |
| 2 | Matching finding with scientific date after cutoff | Ineligible/not evaluated | Not evaluated | Exclude — `excluded_outside_evidence_cutoff` | Different cutoff changes input/decision digest |
| 3 | Assessment status superseded with applicable successor | Ineligible current | Successor lineage | Exclude — `excluded_superseded` | Historical pre-successor snapshot differs |
| 4 | Frozen normalized retraction event | Ineligible current | Not material | Exclude — `excluded_retracted` | Pre-retraction historical snapshot unchanged |
| 5 | Oral question, explicit dermal evidence | Eligible/not applicable | Independent | Exclude — `excluded_wrong_route` | Stable under row reorder |
| 6 | Oral-required question, route unknown | Eligible/undetermined | Independent | Exclude/defer — `deferred_route_unresolved` | New route data changes refresh digest |
| 7 | Endpoint-specific question, governed different endpoint | Eligible/not relevant | Independent | Exclude — `excluded_wrong_endpoint` | Endpoint mapping version is committed |
| 8 | Raw endpoint without governed mapping | Eligible/undetermined | Independent | Exclude/defer — `deferred_endpoint_ontology_unresolved` | Ontology resolution changes later digest |
| 9 | Same release/source record/content in equivalent run | Representative eligible/applicable | Duplicate representation | Copy excluded — `excluded_reingested_representation` | Adding copy changes universe/selection digest, not representative decision |
| 10 | Secondary record explicitly derived from selected primary | Eligible/applicable as context | Derived | Include context-only — `included_context_only_dependency_declared` | Parent/dependency edge committed |
| 11 | Same endpoint/value from proven independent study | Eligible/applicable | Independent | Include — `included_applicable` | Distinct candidate and decision digests |
| 12 | Candidate substance identity unresolved | Ineligible | Not evaluated | Exclude — `excluded_unresolved_identity` | Governed resolution changes refresh only |
| 13 | QPS recommendation for a QPS-status question | Eligible/applicable after reviewed scope/identity rules | QPS record lineage | Include — `included_applicable` | Channel/question committed; no hazard conclusion |
| 14 | OpenFoodTox study matching toxicology endpoint/context | Eligible/applicable after required normalization | Study lineage | Include — `included_applicable` | Raw and normalized identities committed |
| 15 | Two independent records with matching comparison signature | Eligible/applicable | Independent | Include both; same potential comparison group | Group key stable under input order |
| 16 | Oral chronic versus dermal acute | Eligible in separate scopes | Independent | Separate; `contextually_different` | Different comparison groups; no conflict result |
| 17 | Numeric dimensioned value with missing unit/basis | May be qualitatively eligible; quantitative applicability undetermined | Independent | Defer quantitative role — `deferred_unit_semantics_unresolved` | Supplying unit changes future digest |
| 18 | Same release reprocessed by allowed parser with identical semantic output | One canonical representation | Duplicate representation | Non-representative excluded | Representative chosen by stable run key, not creation order |
| 19 | Snapshot before source correction | Frozen original evaluated under historical state | Historical lineage | Original decision retained | Exact replay matches historical selection digest |
| 20 | Current snapshot after explicit correction | Correction candidate plus predecessor provenance | Correction lineage | Governing correction selected; predecessor excluded if policy says so | New snapshot/selection digest; old unchanged |

No vector produces an endpoint synthesis or hazard conclusion.

## Current-schema gap matrix

| Required concept | Status through `0018` | Current representation / gap | Requirement |
|---|---|---|---|
| Assessment lifecycle | Partially available | Five statuses exist; no temporal status history | Freeze status and add governed lifecycle events/history |
| Finding lifecycle | Missing | Findings have no own status/supersession | Future finding event/lineage model |
| Scientific publication/effective dates | Partially available | Release/assessment dates nullable; validity dates exist | Date-source semantics, provenance and missing-date policy |
| Endpoint identity | Needs normalization | Free-text endpoint; QPS fixed keys, OpenFoodTox raw IUCLID text | Versioned endpoint ontology/mapping history |
| Study identity | Partially available | OpenFoodTox document UUID/literature link; no cross-provider canonical study ID | Study identity and reviewed equivalence model |
| Dependency identity | Missing | No general dependency/group edges | Future immutable dependency records or snapshot projection |
| Route vocabulary | Needs normalization | OpenFoodTox raw/combined context only | Structured versioned route field/mapping |
| Duration vocabulary | Needs normalization/data gap | Possible raw fields, no canonical column | Structured versioned duration mapping |
| Population/species/model vocabulary | Needs normalization | Combined population text/raw payload; QPS target is not population | Structured versioned model context |
| Sex | Partially available | May be in combined/raw OpenFoodTox context | Structured normalized field when material |
| Value/unit normalization | Partially available | Numeric/text/unit persisted; basis/qualifier context heterogeneous | Versioned unit/dose-basis normalization and readiness state |
| Correction/supersession lineage | Missing | Status exists, explicit predecessor/successor edge does not | Append-only lineage/event model |
| Release representation selection | Partially available | Run/artifact/version/digests available | Canonical representation policy and snapshot membership |
| Candidate/decision persistence | Missing | No Phase 7 snapshot/decision tables/documents | Future immutable persistence |
| Evidence channels | Missing as normalized concept | Source `evidence_type` strings only | Versioned channel mapping |
| Comparison groups | Missing | No canonical comparison signature/group | Future selector output/persistence |
| Reason vocabulary/version | Missing | Documentation only | Versioned rule artifact and future persistence |

No migration is designed or authorized by this analysis.

## Scientific-review boundaries

| Area | Classification | Rationale |
|---|---|---|
| Availability/eligibility/relevance/quality separation | ARCHITECTURALLY APPROVED | Prevents category errors |
| Finding as normal atomic candidate; assessment as context | ARCHITECTURALLY APPROVED | Matches current model while preserving exceptions |
| Binary include/exclude plus deferred resolution state | ARCHITECTURALLY APPROVED | Compatible with Phase 7.1 and auditable |
| Provenance, successful-run, cutoff and lifecycle gates | ARCHITECTURALLY APPROVED | Deterministic integrity boundary; concrete protocol allowlists still reviewed |
| Canonical ordering, decision/selection digest | ARCHITECTURALLY APPROVED | Reproducibility mechanism |
| Exact duplicate/reingestion non-independence | ARCHITECTURALLY APPROVED | Identity/provenance rule, not evidence weighting |
| No provider precedence or same-value deduplication | ARCHITECTURALLY APPROVED | Prevents unsupported scientific inference |
| Concrete endpoint mappings/equivalences | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Scientific construct mapping |
| Population/species transfer and route applicability | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Domain inference affects claim |
| Duration categories and boundaries | REQUIRES EXTERNAL SCIENTIFIC REVIEW | No arbitrary thresholds allowed |
| Quality minimum criteria and evidence-type acceptance | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Determinism does not establish scientific validity |
| QPS role, qualification interpretation and target scope | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Regulatory framework-specific meaning |
| Cross-study dependency/equivalence review | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Requires source/study expertise |
| Agreement, discordance and true-conflict synthesis | DEFINED IN 7.3 / EXTERNAL REVIEW REQUIRED | Selection only pre-classifies comparability; synthesis contract is in `WYE_EVIDENCE_SYNTHESIS.md` |
| Endpoint synthesis, hazard profile and confidence | DEFINED IN 7.3 / EXTERNAL REVIEW REQUIRED | Non-scalar representation is defined; concrete scientific rules remain review-gated |
| Endpoint/study/dependency ontologies and lineage | DATA GAP | Not represented generally in current schema |
| Structured route/duration/population/unit basis | DATA GAP | Present only partially/raw |

## Implementation-readiness matrix

Classification does not authorize implementation.

| Future runtime component | Classification | Reason |
|---|---|---|
| Candidate identity envelope and canonical serialization | READY FOR IMPLEMENTATION | Logical fields and stable inputs defined |
| Core structural/provenance/time/lifecycle gates | READY FOR IMPLEMENTATION | Deterministic contract and current anchors defined |
| Successful-run and equivalent-reingestion grouping | READY FOR IMPLEMENTATION | Run/artifact/content digests exist; policy defined |
| Decision payload, binary outcome and deferred state | READY FOR IMPLEMENTATION | Canonical contract defined |
| Canonical ordering, decision and selection digests | READY FOR IMPLEMENTATION | Inclusion/exclusion boundaries defined |
| Snapshot/decision database persistence | BLOCKED BY DATA MODEL | No schema approved; persistence remains future work |
| Explicit correction/supersession handling | BLOCKED BY DATA MODEL | Lineage/event relationships missing |
| Cross-provider study/dependency grouping | BLOCKED BY DATA MODEL | Canonical study/dependency identity missing |
| Endpoint/population/route/duration normalization | BLOCKED BY DATA MODEL | Structured versioned vocabularies missing |
| Protocol evidence-type/channel allowlists | BLOCKED BY SCIENTIFIC REVIEW | Concrete scientific admissibility not validated |
| Endpoint equivalence and applicability rules | BLOCKED BY SCIENTIFIC REVIEW | Requires external domain review |
| Unknown-route/population/duration inclusion policies | BLOCKED BY SCIENTIFIC REVIEW | Transfer assumptions affect scientific claims |
| QPS scientific applicability policy | BLOCKED BY SCIENTIFIC REVIEW | QPS meaning/qualification scope needs expert review |
| Quality threshold/gate implementation | BLOCKED BY SCIENTIFIC REVIEW | No reviewed rubric or threshold exists |
| Evidence agreement/conflict resolution | BLOCKED BY SCIENTIFIC REVIEW | Phase 7.3 defines states and trace; concrete criteria remain unvalidated |
| Endpoint-specific conclusions/hazard profile | BLOCKED BY SCIENTIFIC REVIEW | Phase 7.3 defines the envelope; scientific rules remain unvalidated |

## Phase 7.7.1A machine-contract freeze

`WYE_SELECTION_POLICY_FREEZE.md` is now authoritative for the typed embedded
selection-policy schema, executable-protocol validation, actual assessment,
release and run status matrices, exact representation allowlists, endpoint and
population mapping contracts, target restriction, reingestion identity,
dependency boundary, closed reason/rule registries, canonical decision and
manifest payloads, and structured trace events.

The selection-only integration decision is also frozen: Phase 7.7.1 is a pure
engine and validation harness. It creates no 0021 execution or publication and
uses no fake result or trace. A later synthesis/evaluation slice supplies the
real non-numeric result and complete trace for atomic publication.

No reviewed machine-executable scientific policy instance currently exists.
Phase 7.7.1B prepares a concrete candidate source/dataset and representation
allowlist, channel/type and endpoint/population mappings, dependency disposition
and golden expected decisions. Those values remain the authority of an
independent scientific review, not software architecture or AI assistance.

```text
Phase 7.7.1A:
TECHNICAL CONTRACT FROZEN

Next:
Phase 7.7.1B — Initial Selection Protocol Scientific Review & Golden Cases
```

## Phase 7.7.1B candidate policy and golden oracle

Phase 7.7.1B defines the first concrete candidate instance without claiming
scientific approval:

```text
policy: efsa_qps_evidence_selection / 1.0.0-candidate.1
schema: wye_scientific_evidence_selection_policy / 1
selection_policy_digest:
  d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615
status: CANDIDATE — AWAITING EXTERNAL SCIENTIFIC APPROVAL
```

The candidate is intentionally limited to finding-level EFSA QPS list evidence
for substance targets. It does not admit OpenFoodTox 3: the current v1 evidence
member does not expose governed route/duration fields and the real adapter
combines species, sex and route in free `population_context`. That fail-closed
decision is not a provider-quality judgement and establishes no precedence.

Exact QPS channel/type/endpoint/population mappings, the representation tuple,
date precedence, dependency disposition and claims are frozen in
`WYE_SELECTION_POLICY_FREEZE.md` and the canonical candidate JSON. Their
scientific-policy values remain review-gated. `WYE_SELECTION_GOLDEN_CASES.md`
authors 28 independent oracle cases, each classified as `TECHNICAL` or
`SCIENTIFIC-REVIEW-REQUIRED`; none is self-labelled approved.

Production selector publication and scientific selector implementation remain
blocked until the exact policy digest and mandatory scientific oracles receive
independent reviewer, validation-owner and release-approver sign-off. A later
technical conformance interpreter may use synthetic policies only in a
non-production harness and may not create 0021 scientific publications.

```text
Phase 7.7.1B:
CANDIDATE POLICY FROZEN
```

## Phase 7.7.1C external scientific review gate

The candidate is now accompanied by
`WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md` and the digest-bound
`WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json`. The package classifies every
candidate decision as structural, source-derived, scientific-review-required
or fail-closed; it supplies dedicated review cards and a case-by-case approval
matrix for all 28 golden cases. It records no approval itself.

Production selection remains unauthorized until the exact candidate policy
and golden corpus receive independent scientific review, validation-owner
sign-off and release approval under the documented change-control rule.

```text
Phase 7.7.1C:
SCIENTIFIC REVIEW PACKAGE COMPLETED

Phase 7.7.1:
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL
```

## Phase 7.2 exit criteria

- [x] Evidence-object taxonomy defined.
- [x] Finding selected as normal atomic selection unit with explicit exception.
- [x] Eligibility semantics separated from availability, relevance and quality.
- [x] Applicability/relevance dimensions and states defined.
- [x] Deterministic decision lifecycle and primary-reason precedence defined.
- [x] Versioned reason-code taxonomy defined.
- [x] Actual and future assessment lifecycle semantics distinguished.
- [x] Scientific, availability, ingestion and mapping time semantics defined.
- [x] Release plus normalized-ingestion representation policy defined.
- [x] Duplicate identity and handling defined.
- [x] Dependency relationships and selection implications defined.
- [x] Endpoint comparison and ontology requirements defined.
- [x] Population/species/model relevance boundary defined.
- [x] Route relevance and unknown-route semantics defined.
- [x] Duration readiness defined without arbitrary thresholds.
- [x] Dose/value/unit readiness defined without conversions.
- [x] Dimension-specific missing-field policy defined.
- [x] Conflict comparability pre-classification defined.
- [x] QPS/OpenFoodTox semantic separation defined from real adapters.
- [x] Minimal evidence-channel model defined.
- [x] Complete evidence-selection-decision payload defined.
- [x] Deterministic decision identity and canonical ordering defined.
- [x] Selection-digest boundary defined.
- [x] Eighteen edge cases defined.
- [x] Hybrid reason-code versioning and compatibility defined.
- [x] Scientific-review boundaries classified.
- [x] Twenty conceptual deterministic vectors defined.
- [x] Current-schema gap matrix completed.
- [x] Implementation-readiness matrix completed.

## Phase 7.3 specialization and roadmap

The Phase 7 roadmap remains unchanged. The synthesis specialization is defined
in `WYE_EVIDENCE_SYNTHESIS.md`; it does not alter the immutable selection
contract in this document.

The proposed next checkpoint is:

```text
Phase 7.4 — Substance-to-Ingredient Projection Semantics
```

Phase 7.4 and the later 7.5 semantic specialization are complete. Phase 7.6
defines the immutable candidate-membership and decision-artifact persistence in
`WYE_SCORING_PERSISTENCE.md`: every snapshot candidate retains one canonical
decision and reason trace, while query projections remain rebuildable. This does
not implement the selector or validate protocol-specific scientific rules.
