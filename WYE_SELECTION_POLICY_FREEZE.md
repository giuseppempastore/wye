# WYE deterministic evidence-selection policy freeze

Status:

```text
Phase 7.7.1A
TECHNICAL CONTRACT FROZEN

Phase 7.7.1B
CANDIDATE POLICY FROZEN

Phase 7.7.1
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL
```

Sections 1–24 are the authoritative machine-contract freeze for the first
Phase 7.7 engine slice. Sections 25–32 add the Phase 7.7.1B candidate policy
instance and review preparation. The candidate is not scientifically approved
and this document authorizes no production selector implementation.

## 1. Boundary and authoritative inputs

The bounded transformation is:

```text
sealed scientific evidence snapshot
+ published protocol_definition/1 with executable selection_policy
+ canonical target/input context
-> one decision per snapshot member
+ one canonical selection manifest model
+ one canonical selection trace fragment
```

The selector does not query current evidence, select a newer release, resolve a
current mapping, call a network service, use AI, or produce synthesis or a
score. Snapshot membership is the complete candidate universe.

Legacy `product_scores`, `ingredient_risk_profiles`, `ingredient_evidence` and
legacy `scoring.py` are not inputs, fallbacks, fixtures or validation targets.

The selector v1 scientific target is `substance`. An ingredient evaluation
must first expose each governed mapped substance as a separate substance-level
selection context; ingredient projection remains a later stage. Product is not
supported.

## 2. Readiness against the implemented schema

| Concern | Classification | Actual representation / restriction |
|---|---|---|
| Sealed candidate identity and payload | FROZEN + IMPLEMENTABLE | 0020 member identity and semantic artifact |
| Finding plus assessment context | FROZEN + IMPLEMENTABLE | Finding member artifact freezes both |
| Assessment-level candidate | FROZEN + IMPLEMENTABLE | Allowed only by explicit policy flag |
| Assessment lifecycle | FROZEN + IMPLEMENTABLE | Five checked database states |
| Finding lifecycle | FROZEN BUT ABSENT | Finding inherits assessment lifecycle; no invented status |
| Release and run provenance | FROZEN + IMPLEMENTABLE | Frozen release/run projections in member artifact |
| Recorded availability | FROZEN + IMPLEMENTABLE WITH LIMITATION | Uses frozen release acquisition and run completion; schema is not fully bitemporal |
| Exact representation versions | FROZEN + IMPLEMENTABLE | Adapter/importer/parser/normalization strings and checksums |
| Evidence channel/type ontology | NOT YET SCIENTIFICALLY FROZEN | Raw assessment/finding strings require exact reviewed mappings |
| Endpoint ontology | FROZEN CONTRACT, VALUES ABSENT | Free-text endpoint may be used only through an exact reviewed mapping |
| Population/model | FROZEN CONTRACT, VALUES ABSENT | Free-text `population_context` requires exact reviewed mapping |
| Route and duration | FROZEN BUT NOT REPRESENTABLE | No general normalized columns; v1 must declare them `not_applicable` |
| General correction/successor lineage | FROZEN BUT NOT REPRESENTABLE | Assessment status is available; successor identity is not general |
| Cross-source study/dependency identity | FROZEN BUT NOT REPRESENTABLE | v1 returns `unknown` unless explicit frozen lineage exists |
| Exact reingestion grouping | FROZEN + IMPLEMENTABLE | Stable source/release/record/finding identity excluding run identity |
| Selection persistence | FROZEN + IMPLEMENTABLE LATER | 0021 requires atomic result/trace/publication; selection-only does not publish |

## 3. Policy schema and protocol integration

The schema identifier is:

```text
wye_scientific_evidence_selection_policy / 1
```

It is embedded as the required `selection_policy` object in the canonical
payload of `protocol_definition / 1`. A separate artifact is not introduced.
Embedding makes the protocol digest commit atomically to the policy, reason and
rule registries, mappings, and evaluation plan.

`selection_policy_digest` is SHA-256 over the
`wye-c14n-json-v1` bytes of the `selection_policy` object alone. It is a
sub-root used by decision and manifest payloads; the encompassing protocol
digest remains the authoritative published protocol root.

The object has this closed top-level shape; every field is required, including
empty arrays and explicit `null` values:

```json
{
  "candidate_policy": {},
  "context_policy": {},
  "dependency_policy": {},
  "endpoint_ontology": {},
  "evidence_vocabulary": {},
  "evaluation_plan": [],
  "policy_key": "reviewed_instance_key",
  "policy_version": "reviewed_instance_version",
  "reason_registry": {},
  "representation_policy": {},
  "rule_registry": {},
  "schema_id": "wye_scientific_evidence_selection_policy",
  "schema_version": "1",
  "source_release_policy": {},
  "target_policy": {},
  "temporal_policy": {}
}
```

Objects reject unknown fields. Set-like arrays are sorted by unsigned UTF-8
bytes for strings or by `wye-c14n-json-v1` bytes for objects. Semantically
ordered arrays retain declared order. The canonical JSON value domain remains
the existing narrow v1 domain; no float or `Decimal` is admitted.

No policy default exists in Python. A missing object, missing disposition,
unknown field, or unsupported schema makes the protocol non-executable.

Nested objects are closed as follows:

| Object | Required fields |
|---|---|
| `candidate_policy` | `supported_member_kinds` (sorted non-empty subset of `finding`,`assessment`), `assessment_level` (boolean consistent with that set) |
| `target_policy` | `target_type`=`substance`, `query_scope_binding`=`target_artifact_digest`, `identity_projection_fields` equal to the five fields in section 11 |
| `temporal_policy` | ordered `scientific_date_source_order`, `cutoff_timezone`=`UTC`, `cutoff_boundary`=`inclusive`, `availability_fields` equal to `release_acquired_at`,`run_completed_at` |
| `source_release_policy` | sorted exact `source_dataset_entries`, `unmapped_disposition`=`deferred`, and a total `release_status_matrix` |
| `representation_policy` | total `run_status_matrix` and sorted exact `allowed_representations` tuples from section 9 |
| `evidence_vocabulary` | `namespace`, `version`, sorted `channel_mappings`, sorted `evidence_type_mappings`, and explicit denied mappings |
| `endpoint_ontology` | `namespace`, `version`, sorted closed `endpoint_keys`, sorted exact `raw_mappings`, and required/optional disposition |
| `context_policy` | `population_ontology`, `population_required`, `population_unknown_disposition`, `route`=`not_applicable`, `duration`=`not_applicable` |
| `dependency_policy` | `vocabulary_version`, exact-reingestion rule, `unknown_disposition`, `derived_disposition` |
| `reason_registry` | exactly the two registry descriptors in section 15, each with unique closed definitions |
| `rule_registry` | namespace/version plus unique rule definitions using only section 17 IDs, fields and operators |
| `evaluation_plan` | every active rule ID exactly once in increasing `(stage_ordinal, precedence_ordinal)` order |

All mapping rows contain exact raw keys, one canonical key or disposition, and
a review-reference identifier. The scientific values of those rows are absent
until Phase 7.7.1B; their shape and validation are frozen here.

Closed disposition values are `allowed`, `denied`, `deferred`,
`not_applicable`, `contributing`, and `context_only`, only in the fields whose
tables above admit them. `population_unknown_disposition` is
`deferred|allowed` (the latter requires a reviewed optional-context rule).
`unknown_disposition` and `derived_disposition` are
`contributing|context_only|deferred`. No free-form disposition is valid.

## 4. Protocol executability

A protocol version is selection-executable only when all of the following are
true:

1. lifecycle permits the requested execution mode and `published_at` exists;
2. the stored protocol digest equals the verified `protocol_definition/1`
   artifact digest;
3. `selection_policy` has the exact schema above;
4. all five assessment states, five release states, five run states and every
   required dimension have an explicit disposition;
5. policy, reason, rule and ontology identifiers are syntactically valid and
   unique;
6. all rule operators and field references belong to the closed v1 sets;
7. every emitted reason and rule reference exists in its registry;
8. precedence is a duplicate-free total order over every emit-capable reason;
9. every source/dataset, representation and raw-to-canonical mapping is exact;
10. candidate kinds and target type are supported;
11. required scientific review metadata and the independently approved golden
    case set identify this exact policy digest.

Protocol publication validation covers items 2–11 that depend only on the
artifact. Execution revalidates artifact integrity and checks snapshot, target,
input and candidate compatibility. Malformed policy is a protocol error: it
produces no candidate decisions.

Lifecycle remains mode-specific: `NORMAL` and `REFRESH` require `published`;
`REPLAY` permits a historically published version currently `published`,
`deprecated` or `retired`; `COUNTERFACTUAL` permits those historically
published states only with the separately persisted governed authorization.

## 5. Candidate model

The pure input candidate is an immutable projection of one sealed snapshot
member:

```json
{
  "member_identity_digest": "32-byte lowercase hex",
  "member_kind": "finding|assessment",
  "member_semantic_digest": "32-byte lowercase hex",
  "snapshot_member_payload": {},
  "status_as_of": "assessment status"
}
```

The member payload must be the verified
`scientific_evidence_snapshot_member/1` artifact whose digest equals
`member_semantic_digest`. A finding requires non-null finding content and its
assessment context. An assessment candidate requires null finding content and
`candidate_policy.assessment_level = true`; otherwise it is excluded as an
unsupported candidate kind with `excluded_unsupported_candidate_kind`. The
engine never converts an assessment into a synthetic finding.

`status_as_of` must equal the status embedded in `assessment_context`; a
mismatch is snapshot-integrity failure and yields no scientific decision.

## 6. Assessment and finding lifecycle

The v1 assessment matrix is fixed:

| `assessment_status` | Gate result | Decision mapping | Primary reason |
|---|---|---|---|
| `published` | continue | determined by later gates | none |
| `pending_review` | block | excluded/resolved/none | `excluded_pending_review` |
| `superseded` | block | excluded/resolved/none | `excluded_superseded` |
| `withdrawn` | block | excluded/resolved/none | `excluded_withdrawn` |
| `rejected` | block | excluded/resolved/none | `excluded_rejected` |

No general finding status exists. Finding eligibility inherits the frozen
assessment status. Finding-local identity, minimum content, endpoint, evidence
type, population context, value/unit and raw payload may affect structural or
applicability gates; none is interpreted as a lifecycle state.

`superseded` is enough to exclude current-use evidence, but it does not prove a
successor identity. The trace records the lineage limitation. No “newer date
wins” rule exists. Historical REPLAY uses the historical snapshot and protocol
and never re-evaluates current status.

## 7. Scientific and recorded time

The v1 policy supports exactly two scientific-date sources:

```text
assessment_published_date
release_released_at
```

Each reviewed policy instance declares a non-empty ordered `source_order` using
those keys without duplicates. The first present value is authoritative. No
ingestion timestamp is a scientific date. When all configured sources are
missing, the decision is excluded/deferred with
`deferred_scientific_date_unknown`.

`evidence_cutoff` is normalized to UTC. A DATE source is compared inclusively
to `DATE(evidence_cutoff UTC)`. A TIMESTAMPTZ source is normalized to UTC and
compared inclusively to the exact cutoff instant. A later scientific date emits
`excluded_outside_evidence_cutoff`. Lower-priority dates do not override the
chosen date; all source values and the chosen source remain in the trace.

Recorded availability is separate. The frozen release `acquired_at` and
successful run `completed_at` must both be present and no later than snapshot
`as_of`. A known later value emits `excluded_not_available_as_of`; a missing
required value emits `deferred_availability_unknown`. The selector performs no
mutable timestamp lookup. Phase 6 is not fully bitemporal, and this v1 rule does
not claim otherwise.

## 8. Source, dataset and release policy

`source_release_policy` contains exact, reviewed entries keyed by
`[source_key, dataset_key]`. Each entry is `allowed` or `denied`; the complete
instance MUST define `unmapped_disposition` as `deferred`. Authority level,
display name, URL and provider reputation are never eligibility inputs.

The release-status matrix is fixed:

| `release_status` | Result | Reason when blocking |
|---|---|---|
| `validated` | continue | none |
| `declared` | deferred | `deferred_release_not_validated` |
| `acquired` | deferred | `deferred_release_not_validated` |
| `superseded` | deferred | `deferred_release_supersession_unresolved` |
| `rejected` | excluded/resolved | `excluded_ineligible_release_status` |

A denied source/dataset emits `excluded_unsupported_evidence_channel`; an
unmapped pair emits `deferred_evidence_channel_unmapped`. There are no weights
and no global provider precedence.

## 9. Ingestion and representation policy

The run-status matrix is fixed:

| `run_status` | Result | Reason when blocking |
|---|---|---|
| `succeeded` | continue | none |
| `pending` | deferred | `deferred_ingestion_incomplete` |
| `running` | deferred | `deferred_ingestion_incomplete` |
| `failed` | excluded/resolved | `excluded_ineligible_ingestion_run` |
| `cancelled` | excluded/resolved | `excluded_ineligible_ingestion_run` |

An executable policy contains an exact allowlist of representation tuples:

```text
importer_name
importer_version
source_adapter_version
acquisition_version
parser_version
normalization_schema_version
config_checksum_algorithm|null
config_checksum_value|null
```

Matching is string equality after canonical string normalization. There is no
semantic-version comparison, minimum version, “latest run”, or implicit
`legacy_unknown` acceptance. An unlisted tuple emits
`excluded_unsupported_representation`.

The actual run schema has no `partial`, `recovered` or `superseded` state.
Recovery that produces a valid representation is a distinct `succeeded` run;
failed/cancelled and in-progress runs retain the dispositions above.

## 10. Evidence vocabulary and endpoint ontology

The implemented schema provides unconstrained `assessment_type`, finding
`evidence_type`, endpoint text and population text. Therefore v1 defines only
exact governed mapping tables; it defines no scientific values itself.

`evidence_vocabulary` contains:

- a vocabulary namespace/version;
- exact channel mappings keyed by source, dataset and assessment type;
- exact evidence-type mappings scoped by channel and raw evidence type;
- explicit denied mappings.

Missing mappings defer with `deferred_evidence_channel_unmapped` or
`deferred_evidence_type_unmapped`. Explicit denial excludes with the
corresponding unsupported-channel/type reason.

`endpoint_ontology` contains a namespace/version, closed endpoint keys and
exact mappings scoped by channel, evidence type and raw endpoint. Matching is
Unicode-normalized exact equality; fuzzy, substring and model-generated
matching are forbidden. Required endpoint missing or unmapped emits
`deferred_endpoint_ontology_unresolved`; an explicit mapped non-match emits
`excluded_wrong_endpoint`.

The only generally stored contextual dimension supported by v1 is
`population_context`, also through exact reviewed mappings. Required missing or
unmapped population emits `deferred_population_model_unresolved`; an explicit
mapped non-match emits `excluded_wrong_population`.

Route and duration have no general normalized field and are unsupported v1
operators. An executable v1 policy must declare both dimensions
`not_applicable`. A scientific question requiring either dimension is not
selection-executable under schema v1.

## 11. Target applicability

V1 requires:

- target type `substance`;
- the snapshot query scope to bind the canonical target artifact digest;
- the execution input target digest to equal that scope digest;
- candidate `evidence_linked_substance_identity` to equal the target’s frozen
  substance identity projection for the common fields `normalized_name`,
  `preferred_name`, `scientific_name`, `status`, and `substance_type`.

Failure of the root bindings is an input-integrity error. A valid candidate
whose frozen linked-substance projection differs emits `excluded_wrong_target`.
No synonym, chemical similarity, ingredient mapping or fuzzy inference occurs.
The lack of a substance internal ID in the v1 member artifact is an explicit
limitation; the snapshot root binding plus exact frozen projection is the
narrow supported contract.

## 12. Unknown dimensions and fail-closed behavior

For a valid policy applied to candidate data:

- required missing/unmapped scientific date, endpoint, population, channel,
  type, availability or dependency information maps to excluded/deferred/none;
- an explicitly optional unknown dimension may pass only when the reviewed
  policy contains that exact allowance and emits
  `included_applicable_unknown_optional_context`;
- an unsupported representation is excluded/resolved;
- an explicitly non-applicable dimension is not evaluated.

For the policy itself, unknown schema, field, operator, ontology version,
reason, rule, required dimension or malformed registry invalidates the whole
protocol. Protocol invalidity never becomes an eligible or deferred candidate.

## 13. Correction, supersession and withdrawal

Assessment status is the only general current lifecycle authority available in
the frozen member. `withdrawn`, `rejected` and `superseded` are excluded as in
the matrix. An explicit correction/successor relation may be used only when it
is materialized in canonical candidate input under a future compatible schema.
Absent lineage is never reconstructed by dates, values or display text.

If two published candidates claim correction/succession without canonical
lineage, neither is silently discarded. Their dependency is `unknown`; the
reviewed policy must determine whether unknown dependency remains contributing,
context-only, or deferred. That policy value belongs to Phase 7.7.1B.

## 14. Reingestion and dependency

The reingestion identity key is canonical JSON over:

```text
source_key
dataset_key
external_release_key
assessment_source_record_key
member_kind
finding_identity|null
```

It deliberately excludes run identity. Candidates sharing this key are exact
reingestion candidates only when this `scientific_content_digest` also matches:

```text
SHA-256(wye-c14n-json-v1({
  assessment_context,
  evidence_linked_substance_identity,
  finding_content,
  member_kind,
  status_as_of
}))
```

No ingestion-run or release-provenance object enters that digest. Among allowed
equivalent representations, the representative is the lowest `run_key` by
unsigned UTF-8 bytes; remaining copies emit
`excluded_reingested_representation`. Divergent content is never collapsed.

The dependency vocabulary is closed:

```text
independent
derived
duplicate
exact_reingestion
unknown
```

Current schema can prove `exact_reingestion`; other states require explicit
canonical lineage. Similar endpoint/value/text across sources is `unknown`, not
duplicate. V1 selection does not resolve conflict and does not weight
independence. Otherwise eligible conflicting candidates remain selected.
The Phase 7.7.1B policy must explicitly choose the role or deferred behavior for
`unknown` and `derived`; no hidden default exists.

## 15. Reason registries v1

The v1 reason model is the closed union of two registries:

```text
wye_selection_core / 1
food_tox_evidence_selection / 1
```

The core registry owns structural, identity, provenance, time, lifecycle,
release/run and generic dependency codes. The food-toxicology registry owns
the three inclusion codes and the endpoint/population applicability codes.
Both code sets and meanings are technically frozen below; Phase 7.7.1B decides
which reviewed rules may emit the scientific codes. A published policy embeds
both complete registries, so it cannot add arbitrary codes.

The closed codes and compatible outcomes are:

| Code | Compatible outcome |
|---|---|
| `included_applicable` | included/resolved/contributing |
| `included_applicable_unknown_optional_context` | included/resolved/contributing or context_only |
| `included_context_only_dependency_declared` | included/resolved/context_only |
| `excluded_missing_assessment_context` | excluded/resolved/none |
| `excluded_unsupported_candidate_kind` | excluded/resolved/none |
| `excluded_unresolved_identity` | excluded/resolved/none |
| `excluded_insufficient_provenance` | excluded/resolved/none |
| `excluded_not_available_as_of` | excluded/resolved/none |
| `excluded_outside_evidence_cutoff` | excluded/resolved/none |
| `excluded_ineligible_release_status` | excluded/resolved/none |
| `excluded_ineligible_ingestion_run` | excluded/resolved/none |
| `excluded_unsupported_representation` | excluded/resolved/none |
| `excluded_pending_review` | excluded/resolved/none |
| `excluded_superseded` | excluded/resolved/none |
| `excluded_withdrawn` | excluded/resolved/none |
| `excluded_rejected` | excluded/resolved/none |
| `excluded_unsupported_evidence_channel` | excluded/resolved/none |
| `excluded_unsupported_evidence_type` | excluded/resolved/none |
| `excluded_wrong_target` | excluded/resolved/none |
| `excluded_wrong_endpoint` | excluded/resolved/none |
| `excluded_wrong_population` | excluded/resolved/none |
| `excluded_exact_duplicate` | excluded/resolved/none |
| `excluded_reingested_representation` | excluded/resolved/none |
| `excluded_dependent_redundant` | excluded/resolved/none |
| `deferred_scientific_date_unknown` | excluded/deferred/none |
| `deferred_availability_unknown` | excluded/deferred/none |
| `deferred_release_not_validated` | excluded/deferred/none |
| `deferred_release_supersession_unresolved` | excluded/deferred/none |
| `deferred_ingestion_incomplete` | excluded/deferred/none |
| `deferred_evidence_channel_unmapped` | excluded/deferred/none |
| `deferred_evidence_type_unmapped` | excluded/deferred/none |
| `deferred_endpoint_ontology_unresolved` | excluded/deferred/none |
| `deferred_population_model_unresolved` | excluded/deferred/none |
| `deferred_dependency_unresolved` | excluded/deferred/none |
| `deferred_correction_lineage_unresolved` | excluded/deferred/none |
| `deferred_scientific_review_required` | excluded/deferred/none |

Arbitrary reason strings are forbidden. Every reason reference is the triple
`[namespace, version, code]`; a bare code is never sufficient canonical
identity.

## 16. Primary and secondary reasons

Every emit-capable rule has a unique `precedence_ordinal`. The v1 registry
freezes this stage order:

```text
10 candidate shape and assessment context
20 identity and provenance
30 recorded availability
40 scientific date and cutoff
50 release status
60 ingestion state and representation
70 assessment lifecycle
80 target applicability
90 channel and evidence type
100 exact reingestion and dependency
110 endpoint
120 population/context
130 reviewed optional/quality gates
140 final inclusion
```

Within a stage, the reviewed policy lists rules in semantic order; ties are
forbidden. The emitted reason with the lowest ordinal is primary. All other
emitted reason references are secondary, sorted by `(precedence_ordinal,
namespace unsigned UTF-8, version unsigned UTF-8, code unsigned UTF-8)`, with
duplicate triples removed. Implementation evaluation order cannot alter this
result.

## 17. Rule registry and operators

Namespace and version:

```text
wye_selection_rules / 1
```

The closed architectural rule IDs are:

```text
candidate_shape
assessment_context
identity_resolved
provenance_complete
availability_as_of
scientific_date_cutoff
release_status
ingestion_run_status
representation_allowed
assessment_status
target_applicability
evidence_channel
evidence_type
reingestion_identity
dependency_disposition
endpoint_applicability
population_applicability
final_inclusion
```

Each rule definition contains `rule_id`, `stage_ordinal`,
`precedence_ordinal`, `operator`, a closed `field_ref`, canonical operands and
outcome/reason mappings. Rule IDs are scientific identifiers, not Python names.

V1 operators are exactly:

```text
exists
equals
in
canonical_equals
date_lte
```

V1 `field_ref` values are exactly:

```text
candidate.member_kind
candidate.assessment_context
candidate.status_as_of
candidate.identity
candidate.provenance
candidate.release.acquired_at
candidate.release.released_at
candidate.release.status
candidate.run.completed_at
candidate.run.status
candidate.run.representation_tuple
candidate.assessment.published_at
candidate.assessment.assessment_type
candidate.finding.evidence_type
candidate.finding.endpoint
candidate.finding.population_context
candidate.finding.identity
candidate.target_identity_projection
context.as_of
context.evidence_cutoff
context.target_artifact_digest
context.snapshot_query_target_artifact_digest
derived.reingestion_identity
derived.dependency_state
```

`date_lte` uses only the date semantics in section 7. There is no arbitrary
expression, regex, fuzzy matching, scripting, `eval`, numerical comparison or
user-defined operator.

Rules execute as ordered gates. All rules in a reachable stage are evaluated;
reasons are collected and precedence selects the primary. A blocking resolved
or deferred outcome makes later scientific stages `not_evaluated` in the trace.

## 18. Decision vocabulary

The only valid 0021 combinations are:

| Meaning | `decision` | `resolution_state` | `selection_role` |
|---|---|---|---|
| Selected contributor | `included` | `resolved` | `contributing` |
| Selected context | `included` | `resolved` | `context_only` |
| Deterministically excluded | `excluded` | `resolved` | `none` |
| Unresolved under valid policy/input | `excluded` | `deferred` | `none` |

Deferred is a scientific resolution state, not an engine failure. Included
means only that the candidate passes the protocol’s selection gates. Excluded
means only that a preserved snapshot candidate is not selected under this
protocol version. Neither implies safety, danger, confidence or risk.

## 19. Selection-decision artifact v1

The authoritative payload remains
`scientific_evidence_selection_decision / 1`. Its fixed envelope is:

```json
{
  "artifact_type": "scientific_evidence_selection_decision",
  "content": {
    "dependency_disposition": {},
    "ordered_rule_refs": [],
    "relevance_dimensions": {},
    "secondary_reasons": [],
    "selection_policy": {},
    "target_applicability": {},
    "trace_events": []
  },
  "decision": "included|excluded",
  "execution_semantic_digest": "hex",
  "member_identity_digest": "hex",
  "member_semantic_digest": "hex",
  "primary_reason_code": "code",
  "reason_namespace": "registry namespace",
  "reason_version": "1",
  "resolution_state": "resolved|deferred",
  "schema_version": "1",
  "selection_role": "contributing|context_only|none",
  "snapshot_member_kind": "finding|assessment"
}
```

`selection_policy` has exactly `schema_id`, `schema_version`, `policy_key`,
`policy_version`, and `selection_policy_digest`. `ordered_rule_refs` contain
exactly `rule_namespace`, `rule_registry_version`, and `rule_id`.
`secondary_reasons` contain the reason identity triples from section 15. No
prose, timestamp, worker, DB ID or score is canonical decision content.

## 20. Selection manifest v1

The authoritative payload is
`scientific_evidence_selection_manifest / 1`:

```json
{
  "artifact_type": "scientific_evidence_selection_manifest",
  "decision_count": 0,
  "deferred_count": 0,
  "evidence_snapshot_digest": "hex",
  "excluded_count": 0,
  "execution_semantic_digest": "hex",
  "included_count": 0,
  "ordered_decisions": [],
  "protocol_digest": "hex",
  "schema_version": "1",
  "selection_policy": {},
  "selection_state": "selected|selected_with_deferred|no_eligible_evidence|selection_deferred"
}
```

Counts equal the descriptor population and decision classifications.
`selection_state` is derived exactly:

```text
included > 0 and deferred = 0 -> selected
included > 0 and deferred > 0 -> selected_with_deferred
included = 0 and deferred = 0 -> no_eligible_evidence
included = 0 and deferred > 0 -> selection_deferred
```

`no_eligible_evidence` is not a risk result. Decision descriptors are sorted by
unsigned bytewise:

```text
member_identity_digest
member_semantic_digest
decision_digest
```

Each descriptor has the exact shape:

```json
{
  "decision": "included|excluded",
  "decision_digest": "hex",
  "member_identity_digest": "hex",
  "member_kind": "finding|assessment",
  "member_semantic_digest": "hex",
  "primary_reason": {"code": "code", "namespace": "namespace", "version": "version"},
  "resolution_state": "resolved|deferred",
  "selection_role": "contributing|context_only|none"
}
```

No DB ID, insertion order or execution timestamp participates.

## 21. Trace event model

Each candidate decision contains one event for every reachable rule and an
explicit `not_evaluated` marker for later registered rules after a blocking
gate. Event shape:

```json
{
  "emitted_reason_codes": [],
  "field_ref": "closed_field_key",
  "input_ref": {"artifact_digest": "hex", "json_pointer": "/path"},
  "operator": "closed_operator",
  "outcome": "pass|block|defer|not_evaluated",
  "rule_id": "closed_rule_id",
  "stage_ordinal": 10
}
```

Trace order is `(stage_ordinal, rule precedence ordinal, rule_id unsigned
UTF-8)`. `input_ref` points to committed inputs and does not copy whole source
payloads. Canonical trace is authoritative; localized or AI-generated prose is
derived later and non-authoritative.

## 22. Scientific policy and golden-case review

No externally reviewed selection-policy instance exists in the repository.
Phase 7.7.1A therefore freezes the schema only. Phase 7.7.1B MUST supply:

- intended question and claims;
- source/dataset, representation, channel/type and endpoint mappings;
- population/context policy and requiredness;
- unknown/dependency role choices;
- any scientifically justified optional-context allowance;
- independently approved golden cases tied to the exact policy digest.

Each golden case is canonical data with:

```text
case_key
case_schema_version
candidate_snapshot_fixture/root
target/input context/root
protocol policy fixture/root
expected ordered decisions
expected decision/resolution/role
expected primary and secondary reasons
expected ordered rule references
expected manifest summary
scientific review reference and approval identity
```

Expected results are authored and approved independently of implementation.
Implementation code may verify them but may not generate them.

Minimum reviewed categories are: eligible evidence; every assessment-status
block; withdrawal; explicit supersession; exact cutoff boundary; unsupported
release and representation; target mismatch; endpoint unknown; population or
context unknown; unresolved dependency; exact reingestion; independent
conflicting evidence retained; zero selected evidence; input-order invariance;
and policy-version sensitivity.

## 23. Selection-only execution boundary

Phase 7.7.1 is frozen as a pure engine and validation harness. It creates no
execution, attempt, selection row, result, trace row or publication. Unit,
golden and integration adapters load/verify frozen inputs before calling the
pure engine, then compare the returned canonical models and bytes.

The models use the same decision and manifest contracts that the future
execution runtime will persist. A later synthesis/evaluation phase supplies a
real non-numeric result and complete trace and calls the existing atomic 0021
publication path. Fake result or trace payloads and dangling development
execution rows are forbidden.

Conceptual pure boundary:

```text
SelectionPolicy
+ SelectionContext
+ CandidateEvidence[]
-> SelectionDecision[]
+ SelectionManifestModel
+ SelectionTrace
```

All semantic inputs, including `execution_semantic_digest`, are explicit. The
engine reads no clock, random source, environment variable, database, network,
AI service or mutable global state. Reordering a semantically unordered
candidate set produces byte-identical decisions, manifest and trace. A different
published policy version may legitimately change output, and every artifact
binds that policy identity.

## 24. Persistence decision and next gate

No migration is required. The policy is content inside the existing
`protocol_definition/1` artifact, and 0019 already provides immutable canonical
artifact identity and protocol-version binding. 0020 provides the candidate
snapshot; 0021 already provides the future selection/publication rows.

Runtime integration will need to construct the fully frozen decision content
and manifest summary defined here, but this is an application change for a
later authorized checkpoint, not a schema extension.

The technical freeze originally required:

```text
Phase 7.7.1B
Initial Selection Protocol Scientific Review & Golden Cases
```

Phase 7.7.1B now supplies candidate bytes and authored fixtures in sections
25–32. Only after independent scientific review, validation-owner sign-off and
release approval of the exact digest may production selector implementation
begin.

## 25. Phase 7.7.1B candidate policy instance

Phase 7.7.1B instantiates this contract without self-approving scientific
choices. The canonical candidate is:

```text
file: WYE_SELECTION_POLICY_CANDIDATE_V1.json
schema: wye_scientific_evidence_selection_policy / 1
policy_key: efsa_qps_evidence_selection
policy_version: 1.0.0-candidate.1
canonical_bytes: 16284
selection_policy_digest:
  d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615
lifecycle: draft candidate, not approved, not published
```

The prerelease suffix prevents the candidate from being confused with an
approved `1.0.0`. Scientific review may approve this exact candidate digest as
the reviewed subject, but promotion to `1.0.0` changes canonical bytes because
`policy_version` is inside the payload. The resulting final digest therefore
requires reviewer confirmation and release approval. Any changed mapping,
rule, disposition, review reference or golden expectation likewise requires a
new candidate digest and review.

The first instance is deliberately QPS-specific rather than a broad toxicology
policy. It supports only:

```text
target: substance
member kind: finding
source/dataset: efsa / efsa_qps
assessment type: efsa_qps_recommendation
evidence type: efsa_qps_list
channel: regulatory_status_and_qualification
endpoints: qps_status, qps_qualification
route: not_applicable
duration: not_applicable
population: not_applicable at the QPS taxonomic-unit question boundary
```

`openfoodtox/openfoodtox_3` is explicitly denied in this policy instance. This
is not a source-quality judgement. Its committed adapter preserves free IUCLID
endpoint text and combines species, sex and route in `population_context`;
route and duration are not governed v1 fields. Allowing it here would hide
unreviewed endpoint/context inference inside configuration. A later protocol
may admit an exact reviewed OpenFoodTox ontology without provider weighting or
precedence.

Fixture-only datasets `efsa_chemical_assessments` and
`openfoodtox_effects` are not policy entries and are never production evidence.

## 26. Source authority and limitations

The source-derived preparation references are:

| Reference | Supported fact | Limitation |
|---|---|---|
| `SRC-EFSA-QPS-TOPIC` — `https://www.efsa.europa.eu/en/topics/topic/qualified-presumption-safety-qps` | QPS is an EFSA taxonomic-unit pre-assessment with qualifications and periodic updates | Does not approve WYE selection or a product-safety claim |
| `SRC-EFSA-QPS-ASSESSMENT` — `https://www.efsa.europa.eu/en/applications/qps-assessment` | QPS status is qualified and does not replace the specific regulated-product assessment | Does not assign WYE selection roles |
| `SRC-EFSA-QPS-RECORD-21216051` — `https://zenodo.org/records/21216051` | Pinned QPS release identity used by the real adapter | Record identity is not a WYE scientific approval |
| `SRC-OFT3-RECORD-19388272` — `https://zenodo.org/records/19388272` | OpenFoodTox 3 is the EFSA IUCLID/OHT chemical-hazard dataset | Does not provide the missing WYE endpoint/population/route mappings |

The policy claim is only:

> Selects frozen EFSA QPS list findings that meet the candidate policy's
> structural, provenance, lifecycle, temporal, exact-representation, target and
> reviewed QPS applicability gates for later, separately governed synthesis.

It does not claim that selected evidence proves harm or safety, that QPS status
authorizes a product, that a qualification is satisfied for a product, that a
source has a quality score, or that WYE computed risk, confidence or a clinical
recommendation.

## 27. Exact source, release, run and representation instance

Source/dataset dispositions are:

| Source | Dataset | Disposition | Authority |
|---|---|---|---|
| `efsa` | `efsa_qps` | candidate `allowed` | Source identity is structural/source-derived; WYE intended use requires scientific approval |
| `openfoodtox` | `openfoodtox_3` | `denied` for this policy | Structural data-gap boundary, not scientific source ranking |
| any unmapped pair | `deferred` | Frozen fail-closed architecture |

Release and run matrices remain exactly sections 8 and 9. No scientific
exception was introduced.

The single accepted representation tuple is:

```text
importer_name: wye_scientific_ingestion
importer_version: scientific_ingestion_service_v1
source_adapter_version: efsa-qps-adapter-1
acquisition_version: zenodo-record-acquisition-1
parser_version: efsa-qps-xlsx-parser-1
normalization_schema_version: wye-scientific-record-1
config_checksum_algorithm: sha256
config_checksum_value:
  8ef910ea3478b3c4e561a2db489548e5e35f551db9d85228edc34a51b0369c5f
```

The checksum describes `scientific_ingestion_config_v1` with semantic
configuration `{"dataset":"qps","max_records":500,"provider":"efsa"}`.
The configured bound must be shown to cover the pinned release before
publication; the checksum alone does not prove release completeness.

## 28. Scientific-date and applicability instance

Scientific date precedence is:

```text
1. assessment_published_date
2. release_released_at
```

An assessment-specific date is more specific to the candidate. QPS adapter
records currently fall back to the release date. The two dates describe
different events; unequal present values are traced and are not treated as a
conflict or resolved by a numeric tolerance. Both absent emits
`deferred_scientific_date_unknown`.

The cutoff is UTC and inclusive. DATE values compare to the UTC cutoff date;
timestamps compare to the exact UTC instant. Availability remains a separate
`release_acquired_at` and successful `run_completed_at` as-of check.

Exact mappings are:

| Raw scope | Canonical value | Candidate disposition | Authority |
|---|---|---|---|
| `efsa/efsa_qps/efsa_qps_recommendation` | `regulatory_status_and_qualification` | allowed | Source-derived shape; scientific intended use pending |
| `efsa_qps_list` within that channel | `qps_list_entry` | allowed | Source-derived shape; scientific intended use pending |
| `qps_status` | `wye_qps_endpoint/1-candidate.1:qps_recommendation_status` | allowed | Exact adapter field; scientific mapping pending |
| `qps_qualification` | `wye_qps_endpoint/1-candidate.1:qps_qualification` | allowed | Exact adapter field; scientific mapping pending |
| `population_context=null` in the QPS channel | `wye_qps_population_context/1-candidate.1:not_applicable_qps_taxonomic_unit` | not applicable | Proposed QPS question boundary; scientific approval pending |

Other channel/type/endpoint/population values are never fuzzy-matched. An
unmapped required value defers. Route and duration are exactly
`not_applicable`; a protocol needing either is non-executable under this policy.

Target matching is substance-only and exact under section 11. No ingredient,
product, synonym, similarity or mapping inference is admitted.

## 29. Reingestion, dependency and conflict instance

Exact reingestion uses the identity/content rule in section 14. The lowest
unsigned UTF-8 `run_key` is the representative and equivalent copies emit
`excluded_reingested_representation`. This rule never deduplicates across
sources or divergent scientific content.

Candidate v1 dependency dispositions are:

| Dependency | Disposition | Approval class |
|---|---|---|
| `exact_reingestion` | one representative contributing; copies excluded | STRUCTURAL / SOFTWARE |
| `unknown` | preserve otherwise eligible record as `contributing`; dependency state remains explicit | SCIENTIFIC POLICY DECISION — pending |
| `derived` | deferred | UNRESOLVED / UNSUPPORTED without canonical lineage |
| `duplicate` | only when canonical lineage proves it; otherwise not inferred | STRUCTURAL boundary |
| `independent` | only when canonical lineage proves it; never inferred | STRUCTURAL boundary |

Unknown dependency therefore does not assert independence. Cross-source
similarity is not duplication. Otherwise eligible conflicting findings are all
selected; synthesis, not selection, owns agreement and conflict interpretation.

## 30. Rule, reason and trace instance

The candidate activates all eighteen `wye_selection_rules/1` rule IDs once in
the evaluation-plan order in the JSON. Stage ordinals remain 10 through 140;
precedence ordinals are unique:

```text
100 candidate_shape
110 assessment_context
200 identity_resolved
210 provenance_complete
300 availability_as_of
400 scientific_date_cutoff
500 release_status
600 ingestion_run_status
610 representation_allowed
700 assessment_status
800 target_applicability
900 evidence_channel
910 evidence_type
1000 reingestion_identity
1010 dependency_disposition
1100 endpoint_applicability
1200 population_applicability
1400 final_inclusion
```

`evaluation_plan` is the semantic execution order. The rule-definition array
has its own fixed documentation order in the candidate bytes; it is not used as
execution order and changing it still changes the candidate digest. Reason
definitions are ordered by code. No SQL, Python mapping or insertion order is
an authority.

All rules use only `exists`, `equals`, `in`, `canonical_equals` or `date_lte`.
The JSON embeds the complete frozen reason registries. Active outcomes use:

```text
included_applicable
excluded_missing_assessment_context
excluded_unsupported_candidate_kind
excluded_unresolved_identity
excluded_insufficient_provenance
excluded_not_available_as_of
deferred_availability_unknown
excluded_outside_evidence_cutoff
deferred_scientific_date_unknown
excluded_ineligible_release_status
deferred_release_not_validated
deferred_release_supersession_unresolved
excluded_ineligible_ingestion_run
deferred_ingestion_incomplete
excluded_unsupported_representation
excluded_pending_review
excluded_superseded
excluded_withdrawn
excluded_rejected
excluded_wrong_target
excluded_unsupported_evidence_channel
deferred_evidence_channel_unmapped
excluded_unsupported_evidence_type
deferred_evidence_type_unmapped
excluded_reingested_representation
deferred_dependency_unresolved
excluded_wrong_endpoint
deferred_endpoint_ontology_unresolved
excluded_wrong_population
deferred_population_model_unresolved
```

No new reason was invented. The primary reason is the lowest unique precedence
ordinal among emitted reasons. Secondary reasons retain all remaining unique
reason triples in precedence/UTF-8 order. Trace events use the exact section 21
shape; blocked later rules are `not_evaluated` and source payloads/prose are not
copied.

The assessment-status rule binds every blocking value explicitly:

| Status | Rule | Primary reason | Rationale class |
|---|---|---|---|
| `pending_review` | `assessment_status` | `excluded_pending_review` | Structurally not a published assessment and cannot support published output |
| `superseded` | `assessment_status` | `excluded_superseded` | Current-use policy excludes the predecessor without inventing successor lineage |
| `withdrawn` | `assessment_status` | `excluded_withdrawn` | The authoritative lifecycle has withdrawn the assessment; history remains preserved |
| `rejected` | `assessment_status` | `excluded_rejected` | The authoritative lifecycle records rejection |

There is no optional scientific dimension in this candidate. Endpoint is
required. Population is explicitly `not_applicable` only for the exact null QPS
taxonomic-unit mapping; any other population value is unmapped and deferred.
Route and duration are explicitly non-applicable, not optional wildcards.

## 31. Scientific-review matrix

| Decision | Candidate value | Authority class | Review evidence | Approval state |
|---|---|---|---|---|
| Target/member/snapshot boundary | substance, finding, sealed snapshot | A — structural/software | 0020 plus 7.7.1A freeze | technically frozen |
| Assessment/release/run matrices | frozen total matrices | A — structural/software | checked schema/lifecycles | technically frozen |
| UTC inclusive cutoff | frozen section 7 behavior | A — structural/software | canonical execution contract | technically frozen |
| QPS source/release identity | EFSA QPS record 21216051 | B — source-derived | EFSA/Zenodo references | source verified; WYE use pending |
| QPS channel admission | allow regulatory-status channel | C — scientific policy | `SCI-QPS-CHANNEL` | awaiting reviewer |
| QPS endpoint mappings | exact status/qualification keys | C — scientific policy | `SCI-QPS-ENDPOINTS` | awaiting reviewer |
| QPS population N/A | null context -> taxonomic-unit N/A | C — scientific policy | `SCI-QPS-POPULATION` | awaiting reviewer |
| QPS representation completeness | bounded config tuple | C plus validation/data check | config checksum and pinned release | awaiting reviewer/validation owner |
| OpenFoodTox exclusion in this policy | denied because v1 context is insufficient | A/D — fail-closed data gap | adapter shape and 7.7.1A limits | frozen for this candidate |
| Unknown dependency role | contributing, never independent | C — scientific policy | `SCI-DEPENDENCY-UNKNOWN` | awaiting reviewer |
| Conflict retention | include otherwise eligible records | A/C boundary | selection/synthesis separation | scientific review pending |
| Exact reingestion | collapse equivalent run copies | A — structural/software | frozen identity/content contract | technically frozen |

Repository search found no named scientific-review approval, validation-owner
sign-off or release-approver record. This document and AI assistance are not an
approval authority.

## 32. Golden corpus and implementation gate

`WYE_SELECTION_GOLDEN_CASES.md` defines 28 authored cases covering all required
categories, deterministic ordering and policy sensitivity. No expected output
was produced by selector code. Cases are individually labelled `TECHNICAL` or
`SCIENTIFIC-REVIEW-REQUIRED`; none is labelled `SCIENTIFIC-APPROVED`.

Production selector publication remains blocked until all policy-sensitive
values and mandatory scientific golden oracles are approved against this exact
digest. A later checkpoint may implement a technical conformance interpreter
only for synthetic/test policies, with no production protocol publication and
no 0021 scientific publication, while approval remains absent.

```text
Phase 7.7.1B:
CANDIDATE POLICY FROZEN
```

## 33. Phase 7.7.1C external review package

`WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md` packages the complete
A/B/C/D decision audit, scientific review cards, source evidence, 28-case
golden approval matrix, approval roles and digest-bound publication gate.
`WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json` gives the exact corpus review
identity. These artifacts prepare external review; neither is an approval
record and neither changes the candidate policy bytes.

```text
Phase 7.7.1C:
SCIENTIFIC REVIEW PACKAGE COMPLETED

Phase 7.7.1:
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL
```
