# WYE Phase 7.7.1C — Initial selection policy scientific review package

Status:

```text
Phase 7.7.1C:
SCIENTIFIC REVIEW PACKAGE COMPLETED
Phase 7.7.1:
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL
candidate is not scientifically approved
candidate is not published
```

This package is written for the independent scientific reviewer, validation
owner and release approver. It organizes the review; it does not perform or
record their approvals. It must be read together with:

- `WYE_SELECTION_POLICY_CANDIDATE_V1.json`;
- `WYE_SELECTION_POLICY_FREEZE.md`;
- `WYE_SELECTION_GOLDEN_CASES.md`;
- `WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json`.

## 1. Exact review subject

```text
policy_key: efsa_qps_evidence_selection
policy_version: 1.0.0-candidate.1
schema: wye_scientific_evidence_selection_policy / 1
canonicalization: wye-c14n-json-v1
canonical byte length: 16284
selection_policy_digest:
  d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615
lifecycle: draft candidate
```

Technical verification found 18 unique rule identities, 18 unique evaluation
plan entries, complete operands/outcome mappings and 36 unique reason
identities. JSON parsing and canonical digest verification succeed.

```text
TECHNICALLY CONFORMANT — NOT SCIENTIFICALLY APPROVED
```

## 2. Scope and reviewer-facing claim

The candidate accepts only finding-level members from a sealed scientific
evidence snapshot for an exact `substance` target. Its proposed evidence domain
is the pinned EFSA QPS list representation.

The claim submitted for review is:

> QPS findings satisfying the candidate's structural, provenance, lifecycle,
> temporal, exact-representation, target and reviewed applicability gates may
> enter a later, separately governed scientific synthesis.

The candidate does **not** claim that:

- QPS guarantees the safety of a product or use;
- a QPS qualification is satisfied for any product;
- QPS replaces exposure-, strain- or product-specific assessment;
- selected evidence proves safety or harm;
- source identity is a quality weight;
- WYE determines exposure, consumer risk, a health recommendation or a score.

OpenFoodTox 3 is denied only in this candidate because v1 lacks governed
endpoint, route, duration and decomposed population mappings. This is not a
provider-quality judgement and establishes no source precedence.

## 3. Authority classification rules

| Class | Meaning | Approval treatment |
|---|---|---|
| A — structural/software | Determined by schema, canonicalization, persistence or frozen deterministic architecture | Technical review may verify it; scientific reviewer need not re-author it |
| B — source-derived | Direct representation of a primary regulatory/scientific source or committed adapter output | Reviewer verifies faithful scope; source fact does not itself approve WYE use |
| C — scientific policy decision | A WYE applicability, role, intended-use or claims choice capable of changing selection | Mandatory external scientific decision |
| D — unresolved/unsupported | Current data or governance cannot support the behavior safely | Must remain fail-closed or be resolved before publication if in scope |

## 4. Exhaustive policy decision matrix

### 4.1 Identity, candidate and target

| Policy path | Proposed value | Class | Review consequence | Status |
|---|---|---|---|---|
| `/schema_id`, `/schema_version` | `wye_scientific_evidence_selection_policy/1` | A | Machine contract identity | technically verified |
| `/policy_key`, `/policy_version` | `efsa_qps_evidence_selection/1.0.0-candidate.1` | A | Draft identity only | technically verified |
| `/candidate_policy/supported_member_kinds` | `[finding]` | A | Finding is frozen atomic candidate | technically verified |
| `/candidate_policy/assessment_level` | `false` | A | No assessment-only selection | technically verified |
| `/target_policy/target_type` | `substance` | A | Ingredient/product unsupported | technically verified |
| `/target_policy/query_scope_binding` | `target_artifact_digest` | A | Exact canonical-root binding | technically verified |
| `/target_policy/identity_projection_fields` | five frozen substance fields | A | No fuzzy identity | technically verified |

### 4.2 Time, lifecycle and provenance

| Policy path | Proposed value | Class | Why review matters | Status |
|---|---|---|---|---|
| `/temporal_policy/cutoff_timezone` | `UTC` | A | Deterministic time basis | technically verified |
| `/temporal_policy/cutoff_boundary` | `inclusive` | A | Frozen comparison mechanic | technically verified |
| `/temporal_policy/availability_fields` | release acquisition + run completion | A | Separates recorded availability from scientific date | technically verified |
| `/temporal_policy/scientific_date_source_order` | assessment publication, then release date | C | Precedence can alter cutoff eligibility | awaiting scientific review |
| `/source_release_policy/release_status_matrix` | validated/declared/acquired/superseded/rejected total matrix | A | Frozen lifecycle behavior | technically verified |
| `/representation_policy/run_status_matrix` | succeeded/in-progress/failed/cancelled total matrix | A | Frozen run lifecycle behavior | technically verified |
| assessment status outcome mappings | published continues; four other states excluded | A | Exact checked assessment lifecycle | technically verified |
| availability missing/later outcomes | deferred/excluded respectively | A | No current-clock inference | technically verified |

### 4.3 Source and representation

| Policy path | Proposed value | Class | Why review matters | Status |
|---|---|---|---|---|
| `/source_release_policy/source_dataset_entries/efsa/efsa_qps` | `allowed` | C, based on B | Selecting this regulatory channel for later WYE synthesis is an intended-use choice | awaiting scientific review |
| `/source_release_policy/source_dataset_entries/openfoodtox/openfoodtox_3` | `denied` | D/A | Current v1 cannot represent required context safely | fail-closed, non-blocking for QPS-only scope |
| `/source_release_policy/unmapped_disposition` | `deferred` | A | Fail-closed unknown source | technically verified |
| `/representation_policy/allowed_representations/0` identity/version fields | exact committed QPS ingestion tuple | A/B | Faithful committed adapter identity | technically verified |
| same tuple `config_checksum_value` | exact checksum for `max_records=500` configuration | A/B plus validation | Checksum proves identity, not completeness | validation-owner evidence required |

### 4.4 Evidence vocabulary and applicability

| Exact policy path | Proposed value | Class | Why scientific approval is required | Current status |
|---|---|---|---|---|
| `/evidence_vocabulary/channel_mappings/0` | QPS assessment -> `regulatory_status_and_qualification` | C based on B | Determines the scientific channel admitted by WYE | awaiting reviewer |
| `/evidence_vocabulary/evidence_type_mappings/0` | `efsa_qps_list` -> `qps_list_entry` | C based on B | Determines selectable evidence type | awaiting reviewer |
| `/endpoint_ontology/raw_mappings[qps_status]` | `qps_recommendation_status`, allowed | C | Defines semantic endpoint identity and later role | awaiting reviewer |
| `/endpoint_ontology/raw_mappings[qps_qualification]` | `qps_qualification`, allowed | C | Qualification must not be misread as an independent safety result | awaiting reviewer |
| `/endpoint_ontology/required` | `true` | C | Missing endpoint blocks selection | awaiting reviewer |
| `/context_policy/population_ontology/raw_mappings[null]` | `not_applicable_qps_taxonomic_unit` | C based on B | Decides that ordinary population context is N/A, not unknown | awaiting reviewer |
| `/context_policy/population_required` | `false` for exact QPS N/A mapping | C | Affects applicability/deferred behavior | awaiting reviewer |
| `/context_policy/population_unknown_disposition` | `deferred` | A/C boundary | Fail-closed unknown; reviewer confirms suitability | awaiting reviewer confirmation |
| `/context_policy/route` | `not_applicable` | C/D | QPS question is not an experimental route comparison | awaiting reviewer |
| `/context_policy/duration` | `not_applicable` | C/D | QPS question is not an experimental duration comparison | awaiting reviewer |

### 4.5 Dependency, role and claims

| Exact policy path | Proposed value | Class | Why scientific approval is required | Current status |
|---|---|---|---|---|
| `/dependency_policy/exact_reingestion` | deterministic representative by UTF-8 run key | A | Representation identity, not scientific deduplication | technically verified |
| `/dependency_policy/unknown_disposition` | `contributing` | C | May preserve records whose independence is unproven | awaiting reviewer |
| `/dependency_policy/derived_disposition` | `deferred` | D/A | No general canonical lineage exists | fail-closed |
| `/rule_registry/.../final_inclusion` | all passing QPS endpoints -> `contributing` | C | Assigns contribution role to status and qualification findings | awaiting reviewer |
| conflict boundary | retain all otherwise eligible findings | A/C | Selection does not resolve scientific agreement | reviewer confirmation required |
| policy claim/non-claims | section 2 | C/governance | Defines permissible interpretation and communication | awaiting reviewer/release approver |

### 4.6 Registries and all 18 rule instances

The registry identities, operator vocabulary, unique ordinals, reason triples
and trace shape are Class A. The policy-sensitive operands referenced by a rule
retain the class assigned above.

| Rule | Class of mechanism | Class of active value | Review status |
|---|---|---|---|
| `candidate_shape` | A | A | technically verified |
| `assessment_context` | A | A | technically verified |
| `identity_resolved` | A | A | technically verified |
| `provenance_complete` | A | A | technically verified |
| `availability_as_of` | A | A | technically verified |
| `scientific_date_cutoff` | A | C date precedence | reviewer required |
| `release_status` | A | A | technically verified |
| `ingestion_run_status` | A | A | technically verified |
| `representation_allowed` | A | B plus validation completeness | validation owner required |
| `assessment_status` | A | A | technically verified |
| `target_applicability` | A | A | technically verified |
| `evidence_channel` | A | C mapping | reviewer required |
| `evidence_type` | A | C mapping | reviewer required |
| `reingestion_identity` | A | A | technically verified |
| `dependency_disposition` | A | C/D dispositions | reviewer required |
| `endpoint_applicability` | A | C mappings | reviewer required |
| `population_applicability` | A | C mapping | reviewer required |
| `final_inclusion` | A | C contribution role | reviewer required |

## 5. Scientific blockers requiring decisions

Mandatory Category C decisions are:

1. admit `efsa/efsa_qps` for the declared selection claim;
2. approve the QPS channel and `qps_list_entry` evidence type;
3. approve both exact endpoint mappings;
4. decide whether qualification findings are `contributing`, `context_only`,
   deferred, or otherwise governed;
5. decide whether null population is truly N/A;
6. confirm route and duration N/A for this QPS-only question;
7. approve scientific-date precedence;
8. decide unknown dependency disposition;
9. approve the intended claim/non-claims;
10. approve all scientific golden oracle outputs.

Validation/release blockers are representation completeness, validation-owner
approval of the corpus, and release-approver authorization of the final exact
digest.

## 6. EFSA QPS source review card

```text
Card: SCI-QPS-CHANNEL
Policy path: /source_release_policy/source_dataset_entries/efsa/efsa_qps
Proposed value: allowed
```

**WYE proposes:** QPS records that pass all candidate gates may enter later
scientific synthesis in their explicitly scoped regulatory-status and
qualification channel.

**WYE does not propose:** product safety, automatic satisfaction of a
qualification, replacement of product/exposure assessment, universal risk
status, provider precedence or a score.

Primary references:

- `https://www.efsa.europa.eu/en/topics/topic/qualified-presumption-safety-qps`
- `https://www.efsa.europa.eu/en/applications/qps-assessment`
- `https://zenodo.org/records/21216051`

Reviewer decision: `[ ] APPROVE  [ ] REJECT  [ ] AMEND`

Rationale/reference: `_______________________________________________`

## 7. QPS endpoint review cards

### 7.1 Recommendation status

```text
Source field: qps_status
Proposed key: wye_qps_endpoint/1-candidate.1:qps_recommendation_status
Proposed role after all gates: contributing
```

Intended meaning: the taxonomic unit is represented by a recommendation-status
entry in the pinned QPS list. Later synthesis may preserve this scoped
regulatory status. It must not be read as product authorization, universal
safety, qualification satisfaction or an experimental toxicology endpoint.

Supporting sources: EFSA QPS topic and assessment pages and pinned Zenodo
record 21216051 listed in section 6. They support the source/QPS framework and
release identity, not WYE's proposed endpoint mapping or contribution role.

Reviewer decision: `[ ] APPROVE  [ ] REJECT  [ ] AMEND`

Rationale/reference: `_______________________________________________`

### 7.2 Qualification

```text
Source field: qps_qualification
Proposed key: wye_qps_endpoint/1-candidate.1:qps_qualification
Current proposed role after all gates: contributing
```

Intended meaning: exact qualification text attached to the QPS taxonomic-unit
entry. Later synthesis may preserve it as a condition/context. It must not be
interpreted as proof that a product satisfies the condition, as an independent
safety vote, or as an experimental endpoint.

Supporting sources: EFSA QPS topic and assessment pages and pinned Zenodo
record 21216051 listed in section 6. They support the existence and conditional
nature of QPS qualifications, not WYE's proposed canonical endpoint or role.

The reviewer must explicitly choose the role:

`[ ] contributing  [ ] context_only  [ ] deferred  [ ] other: __________`

Overall decision: `[ ] APPROVE  [ ] REJECT  [ ] AMEND`

Rationale/reference: `_______________________________________________`

## 8. Population N/A review card

```text
Policy path: /context_policy/population_ontology/raw_mappings[raw_value=null]
Proposed value: not_applicable_qps_taxonomic_unit
```

QPS is framed at taxonomic-unit level rather than as one ordinary experimental
study population. The null stored population field may therefore mean that the
dimension does not belong to this regulatory question, but that interpretation
is a WYE scientific policy choice.

Reviewer choice:

- `[ ] N/A is correct for this exact question`
- `[ ] null must defer as unresolved`
- `[ ] another governed context is required: ________________________`

Rationale/reference: `_______________________________________________`

## 9. Unknown-dependency review card

```text
Policy path: /dependency_policy/unknown_disposition
Current proposal: contributing
```

Alternatives:

| Choice | Selection implication | Later synthesis implication |
|---|---|---|
| A — contributing | Preserves otherwise eligible record | Must retain uncertainty and must not claim independence |
| B — deferred | Removes it from selected set pending lineage | Synthesis receives no contribution from unresolved record |
| C — context_only | Preserves context without contribution role | Synthesis may display but not use as contributing evidence |
| D — reviewer alternative | Must be represented by a new governed value/rule | Requires impact review and new candidate digest |

Reviewer choice: `[ ] A  [ ] B  [ ] C  [ ] D: ______________________`

Overall decision: `[ ] APPROVE  [ ] REJECT  [ ] AMEND`

Rationale/reference: `_______________________________________________`

## 10. Scientific-date and route/duration cards

### Date precedence

Proposal: assessment publication date first, release date second. The values
describe different events and an unequal lower-priority value is traced rather
than treated as a conflict.

Reviewer decision: `[ ] APPROVE  [ ] REJECT  [ ] AMEND`

### Route and duration

Proposal: both are `not_applicable` for the QPS-only regulatory-status question,
not optional wildcards.

Reviewer decision: `[ ] APPROVE  [ ] REJECT  [ ] AMEND`

Rationale/reference: `_______________________________________________`

## 11. Representation-completeness review

The accepted tuple is pinned exactly in the candidate. Its configuration
checksum commits to:

```json
{"dataset":"qps","max_records":500,"provider":"efsa"}
```

The checksum proves which configuration ran; it does not prove that 500 covers
the complete pinned release, that every relevant row was parsed, or that parser
omissions are scientifically acceptable.

Validation-owner questions:

- `[ ] Is the 500-record bound intentional?`
- `[ ] Is the complete pinned release proven to contain no more than the bound?`
- `[ ] If the release is larger, is this explicitly a bounded validation-only policy?`
- `[ ] Is Zenodo record 21216051 and its exact artifact/checksum pinned?`
- `[ ] Are workbook sheet/header/row omissions enumerated?`
- `[ ] Are blank-species and malformed-row outcomes quantified and reviewed?`
- `[ ] Are qualification columns completely represented?`
- `[ ] Is adapter normalization deterministic for all rows in the declared scope?`
- `[ ] Is this candidate intended for validation corpus use or production?`
- `[ ] Is a complete ingestion report attached? Reference: _______________`

Validation decision: `[ ] ACCEPT  [ ] REJECT  [ ] CHANGES REQUESTED`

## 12. Source evidence table

| Policy decision | Organization | Primary resource | Version/date | Source supports | Source does not support | Review relevance |
|---|---|---|---|---|---|---|
| QPS channel candidate | EFSA | QPS topic | reviewed 2026; periodically updated | QPS is a taxonomic-unit safety pre-assessment with qualifications | WYE selection role or product safety | Channel and claims review |
| QPS intended scope | EFSA | QPS assessment/application page | current page reviewed for 7.7.1B/C | QPS is qualified and does not replace specific regulated-product assessment | Automatic qualification satisfaction | Claims/non-claims review |
| Pinned release | EFSA Knowledge Junction / Zenodo | record 21216051 | PS24 / 2026 | Exact QPS workbook release identity | Completeness of WYE bounded ingestion | Representation validation |
| OpenFoodTox data gap boundary | EFSA / Zenodo | OpenFoodTox 3 record 19388272 | v7, 2026-04-30 | IUCLID/OHT structured chemical-hazard database and available content classes | WYE's absent endpoint/route/population mappings | Justifies fail-closed exclusion, not quality ranking |
| QPS adapter fields | WYE committed adapter | `efsa_qps.py` | adapter/parser v1 | Exact emitted assessment/type/endpoint fields | Scientific role assigned by WYE | Mapping fidelity review |

The source statement and WYE decision are deliberately separate: a source fact
is Category B; admitting or interpreting it in WYE remains Category C.

## 13. Golden corpus audit and identity

The corpus now contains 28 unique case keys: the original 27 required cases and
`GC-MULTI-FAILURE-PRECEDENCE`.

Audit results:

- all case keys are unique;
- all rule references exist in `wye_selection_rules/1`;
- all reason references exist in the candidate registries;
- every case inherits a complete rule-relevant base fixture plus explicit
  mutations;
- expected decisions, roles, resolution states, reasons and manifest counts are
  authored in the document, not produced by selector code;
- manifest counts/states are internally coherent;
- no case is labelled `SCIENTIFIC-APPROVED`.

The corpus identity is frozen by
`WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json`:

```text
manifest schema: wye_selection_golden_corpus_manifest / 1
case_count: 28
golden document canonicalization: UTF-8, CRLF/CR -> LF, NFC
golden document canonical bytes: 17040
golden document SHA-256:
  d05f6c8832df5111f3ad93611a088b86fd5b5853831bc6892966f06ace7e0e60
manifest wye-c14n-json-v1 bytes: 1162
golden_corpus_digest:
  db535148ece59c222eaac2004594ae19a1e00a2e65448c42a4804dd8cefd8b15
```

The manifest binds the ordered set of case keys, exact normalized review
document bytes and candidate policy digest. Scientific outputs remain manually
authored; hashing does not generate or approve them.

## 14. Golden-case approval matrix

| Case key | Category | Status | Approval required from | Current state | Oracle reference |
|---|---|---|---|---|---|
| `GC-ELIGIBLE-QPS` | applicability | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | golden corpus §5 row 1 |
| `GC-ASSESSMENT-PENDING` | lifecycle | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 2 |
| `GC-ASSESSMENT-SUPERSEDED` | lifecycle | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 3 |
| `GC-ASSESSMENT-WITHDRAWN` | lifecycle | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 4 |
| `GC-ASSESSMENT-REJECTED` | lifecycle | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 5 |
| `GC-CUTOFF-INCLUSIVE` | time | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 6 |
| `GC-AFTER-CUTOFF` | time | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 7 |
| `GC-DATE-MISSING` | time | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 8 |
| `GC-RELEASE-VALIDATED` | source applicability | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 9 |
| `GC-RELEASE-NOT-VALIDATED` | lifecycle | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 10 |
| `GC-RELEASE-REJECTED` | lifecycle | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 11 |
| `GC-RUN-SUCCEEDED` | source applicability | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 12 |
| `GC-RUN-FAILED` | lifecycle | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 13 |
| `GC-REPRESENTATION-UNSUPPORTED` | representation | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 14 |
| `GC-SOURCE-UNMAPPED` | fail-closed source | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 15 |
| `GC-TARGET-MISMATCH` | identity | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 16 |
| `GC-ENDPOINT-MAPPED` | endpoint | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 17 |
| `GC-ENDPOINT-UNKNOWN` | endpoint coverage | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 18 |
| `GC-POPULATION-NOT-APPLICABLE` | population | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 19 |
| `GC-POPULATION-UNKNOWN` | population coverage | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 20 |
| `GC-EXACT-REINGESTION` | identity | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 21 |
| `GC-DEPENDENCY-UNKNOWN` | dependency | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 22 |
| `GC-CONFLICT-RETAINED` | selection/synthesis boundary | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 23 |
| `GC-NO-ELIGIBLE` | manifest state | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 24 |
| `GC-SELECTION-DEFERRED` | manifest state | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 25 |
| `GC-INPUT-ORDER-INVARIANT` | determinism | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 26 |
| `GC-POLICY-VERSION-SENSITIVE` | policy sensitivity | SCIENTIFIC-REVIEW-REQUIRED | scientific reviewer + validation owner | pending | row 27 |
| `GC-MULTI-FAILURE-PRECEDENCE` | reason precedence | TECHNICAL | validation owner | TECHNICALLY REVIEWED | row 28 |

Summary: 18 technically reviewed mechanics; 10 scientific-review-required
oracles; zero scientifically approved oracles.

## 15. Governance roles

**Scientific reviewer** — owns scientific meaning, applicability, intended use,
roles, claims and Category C decisions.

**Validation owner** — owns corpus completeness, fixture sufficiency,
reproducibility evidence, representation completeness and independent oracle
verification.

**Release approver** — authorizes publication/use of the exact final policy and
golden-corpus digests after required reviews.

The roles remain distinct even if future governance permits one person to hold
more than one role. No names are fabricated here.

## 16. Approval record format

Each decision must be recorded using this closed logical template:

```yaml
approval_schema: wye_selection_policy_approval_record
approval_schema_version: "1"
approval_key: <stable external key>
policy_key: efsa_qps_evidence_selection
policy_version: 1.0.0-candidate.1
selection_policy_digest: d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615
role: scientific_reviewer | validation_owner | release_approver
reviewer_identity: <governed person/role identity>
decision: approved | rejected | changes_requested
reviewed_at: <RFC3339 UTC timestamp>
scope: <closed list of reviewed cards/categories>
approved_category_C_items: []
golden_case_set_reference:
  schema: wye_selection_golden_corpus_manifest/1
  digest: db535148ece59c222eaac2004594ae19a1e00a2e65448c42a4804dd8cefd8b15
notes_reference: <immutable document/artifact reference or null>
governed_audit_reference: <signature/audit-system reference or null>
approval_record_digest: <sha256 or null before finalization>
```

`approval_record_digest` is SHA-256 over `wye-c14n-json-v1` bytes of the record
excluding `approval_record_digest`. Before publication, reviewer identity must
be authenticated either by a digital signature or by a governed immutable audit
system referenced in `governed_audit_reference`. This checkpoint creates no DB
table and no approval record.

## 17. Digest-bound approval rule

Approval applies only to the exact `selection_policy_digest` and exact
`golden_corpus_digest`. Policy key or human title alone is insufficient.

Any canonical-byte change invalidates approval for the changed policy. It
requires a new candidate version/digest, impact review and new approval records.
The same applies to any change in golden oracle content or manifest identity.

Promotion from `1.0.0-candidate.1` to `1.0.0` changes canonical policy bytes
because `policy_version` is inside the payload. Promotion therefore produces a
new digest and requires final reviewer confirmation plus release approval of
that new exact digest; the candidate approval cannot be copied silently.

## 18. Publication gate

The policy remains non-executable for production until all are true:

1. every mandatory Category C card is approved;
2. every mandatory scientific golden oracle is approved;
3. validation owner approves corpus digest and representation-completeness
   evidence;
4. no blocking Category D item remains within the declared QPS-only scope;
5. claims/non-claims are approved;
6. the final non-candidate policy bytes and digest are generated without hidden
   semantic changes;
7. reviewer confirms the final digest after promotion;
8. release approver authorizes that exact final digest and corpus digest;
9. the immutable protocol publication lifecycle is completed separately.

No condition is satisfied merely because this package is complete.

## 19. Partial approval and change flow

Partial scientific approval may be recorded per card and digest. It does not
make the full policy executable while any mandatory Category C item remains
pending, rejected or changes-requested.

If a reviewer rejects or amends a decision:

1. preserve the old candidate and review record;
2. keep it draft/non-executable;
3. create a new candidate version with changed bytes;
4. calculate a new policy digest;
5. update affected golden cases and corpus manifest;
6. run technical conformance again;
7. obtain new scientific, validation and release decisions.

No approval flag is mutated in place on the old digest.

## 20. External reviewer checklist

### Scientific reviewer

- QPS source/channel admission: `[ ] approve [ ] reject [ ] changes requested`
- QPS status endpoint mapping/role: `[ ] approve [ ] reject [ ] changes requested`
- QPS qualification endpoint mapping/role: `[ ] approve [ ] reject [ ] changes requested`
- Population null -> N/A: `[ ] approve [ ] reject [ ] changes requested`
- Route/duration N/A: `[ ] approve [ ] reject [ ] changes requested`
- Scientific-date precedence: `[ ] approve [ ] reject [ ] changes requested`
- Unknown dependency disposition: `[ ] approve [ ] reject [ ] changes requested`
- Conflict-retention boundary: `[ ] approve [ ] reject [ ] changes requested`
- Claims/non-claims: `[ ] approve [ ] reject [ ] changes requested`
- Ten scientific golden oracles: `[ ] approve [ ] reject [ ] changes requested`

Reviewer identity: `____________________`

Rationale/reference: `____________________________________________________`

### Validation owner

- Policy schema/digest independently reproduced: `[ ]`
- Representation-completeness questions resolved: `[ ]`
- 28 case identities and fixtures reviewed: `[ ]`
- 18 technical oracles independently confirmed: `[ ]`
- 10 scientific oracles match reviewer decisions: `[ ]`
- Multi-failure primary/secondary oracle confirmed: `[ ]`
- Corpus digest independently reproduced: `[ ]`

Validation owner identity: `____________________`

Evidence/reference: `____________________________________________________`

### Release approver

- All mandatory approvals present: `[ ]`
- No blocking in-scope Category D: `[ ]`
- Exact final policy digest confirmed: `[ ]`
- Exact corpus digest confirmed: `[ ]`
- Intended use and claims approved: `[ ]`
- Publication lifecycle authorization: `[ ] approve [ ] reject`

Release approver identity: `____________________`

Audit/signature reference: `______________________________________________`

## 21. Optional technical conformance interpreter

A future checkpoint may implement developer tooling that interprets synthetic
policy instances and only the TECHNICAL cases. Such tooling is optional and
must be visibly non-production. It must not:

- publish a protocol;
- create production execution, decision, result, trace or publication rows;
- run scientific-review-required rules as approved behavior;
- be presented as a scientifically validated selector.

It does not block external review and is not implemented by this checkpoint.

## 22. Package outcome

The package is complete for external review. Approval itself remains entirely
external and absent.

```text
Phase 7.7.1C:
SCIENTIFIC REVIEW PACKAGE COMPLETED

Phase 7.7.1:
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL
```
