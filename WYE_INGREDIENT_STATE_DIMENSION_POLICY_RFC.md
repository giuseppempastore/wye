DRAFT — SCIENTIFIC/PRODUCT DECISION REQUIRED

# WYE Candidate Ingredient State and Dimension Policy RFC

## Document status and authority

```text
phase: Fase 7.14.10
governed_decision: PSC-OD-005
decision_status: OPEN
document_status: DRAFT — SCIENTIFIC/PRODUCT DECISION REQUIRED
methodological_dependency: Option B selected only as candidate design direction
candidate_direction_status: PROPOSED, NOT APPROVED
policy_option_c_selection_date: 2026-09-02
policy_option_c_selection_authority: Product owner
policy_option_c_status: PRODUCT-OWNER CANDIDATE DIRECTION — NOT SCIENTIFICALLY OR INDEPENDENTLY VALIDATED
scientific_approval: NOT CLAIMED
validation_owner_approval: NOT PRESENT
runtime_authority: NONE
implementation_authorization: NOT PRESENT
publication_release: NOT APPROVED
assurance_governance: INTERNAL INFORMATIONAL ASSURANCE ADOPTED 2026-09-02
external_validation: FUTURE / OPTIONAL / NOT PRESENT
data_source_cutoff: 2026-09-02
parent_artifact: WYE_INGREDIENT_SCORE_MAPPING_RFC.md
parent_sha256: 874FA2818DB8C74FFC59B6B1BA051F7D77BB47EA45F0D40F951729382BB1CBD2
```

This RFC is a reversible decision-support draft under the existing
`PSC-OD-005`. It creates no new `PSC-OD-*` decision, does not change the state
of any existing decision, and does not start `PSC-OD-006`.

Option B in the parent Mapping RFC is a product-owner candidate design
direction only. It is not a selected scientific method. For the informational
MVP, the accountable internal methodology and validation functions may reject,
replace or materially revise every state, dimension and boundary in this
document, and the product owner must accept the exact internally assured
candidate. Future external reviewers have no current MVP blocking role. Nothing
here is a formula,
weight, threshold, parameter, numerical mapping, comparability claim, runtime
output, publication decision or implementation authorization.

The remediation findings `ISDP-REV-001` through `ISDP-REV-005` are `CLOSED`.
Their closure does not approve Policy Option C, any state or dimension, or
`PSC-OD-005`.

## A. Canonical objective and perimeter

> Specify candidate ingredient scientific states, score-bearing dimensions,
> applicability rules and support-dimension boundaries that a future exact
> Option B mapping candidate could consume, without approving numerical
> transformations, weights, thresholds, comparability or runtime outputs.

The policy answers the following design questions without closing them
scientifically:

| Question | Candidate policy answer | Remaining authority |
|---|---|---|
| Which information could become score-bearing? | Only a scientifically defined ingredient-favourability construct with explicit subject, direction, applicability, provenance, dependency controls and a feasible validation plan. | Scientific review panel and validation owner. |
| Which information remains support-only? | Evidence state, applicability, exposure readiness, coverage, confidence, uncertainty, mapping resolution and evaluability. | Any departure requires an explicit downstream decision and validation. |
| Which information remains informational or regulatory fact? | Ontology labels, authorization and withdrawal assertions, label roles and scoped regulatory dispositions. | Competent regulatory review plus the applicable scoring decision. |
| Which states affect applicability or computability? | Reviewed non-applicability, unresolved indispensable identity or mapping, insufficient required evidence, unresolved conflict and missing indispensable context may qualify or block a future conclusion. | Exact indispensability and gates belong to `PSC-OD-016`. |
| What prevents a number? | `not_computable`, unresolved indispensable inputs, no approved direction, no approved dimension policy, absent reference judgments, absent validation corpus, or a failed publication gate. | `PSC-OD-016`, `PSC-OD-019` and the publication authority. |
| How is double counting controlled? | By separate canonical identities, an explicit dependency register, prohibition of undocumented proxies, and validation against paired perturbations. | Scientific review panel and validation owner. |
| What requires explicit scientific direction? | Every proposed score-bearing dimension, every state-to-dimension interpretation and every claimed monotonic relationship. | Scientific review panel. |
| What remains unresolved pending judgments and corpus? | Dimension boundaries, direction, transforms, interactions, compensability, criticality effects, computability gates and user interpretation. | Existing open decisions, especially `PSC-OD-013` through `PSC-OD-020`. |

### A.1 Non-claims

This draft does not establish that any ingredient is favourable, adverse, safe,
dangerous, legal, illegal, comparable, scoreable or non-scoreable in a real
product. It does not turn the Contract's minimum vocabulary into an ordered
scale. It does not approve a primary ingredient state. It does not define a
product-level ingredient aggregation, nutrition method or overall score.

## B. Mandatory level separation

The future policy must preserve the following levels as independently
identified and traceable objects:

| Level | Meaning | Must not become automatically |
|---|---|---|
| Source observation | A bounded statement or record in a governed source artifact. | A WYE classification, scientific conclusion or score input. |
| Source-backed regulatory or scientific classification | A scoped interpretation attributable to a source and review. | An ontology label, goodness direction or product conclusion. |
| Ontology label | A WYE category assertion for a stated subject and context. | Authorization, hazard, risk or goodness. |
| Mapping/bridge resolution state | Completeness and trustworthiness of ingredient-to-substance reconstruction. | Ingredient scientific state, penalty or risk indicator. |
| Evidence-selection state | Eligibility, relevance, applicability, dependency and selection disposition for a question. | Evidence synthesis, favourability or score. |
| Evidence-synthesis result | Endpoint-scoped interpretation of selected evidence, with sufficiency, conflict and limitations. | Whole-ingredient goodness or product risk. |
| Ingredient scientific state | A candidate, reviewed statement about the ingredient for an exact scientific question and scope. | A numerical value or product-wide state. |
| Score-bearing dimension | A candidate construct that could affect a future mapping only after all eligibility and approval gates pass. | An approved dimension merely because it is listed here. |
| Support dimension | Context needed to interpret or qualify a conclusion. | Goodness, penalty, multiplier or proxy score. |
| Informational flag | A traced notice with no automatic numerical consequence. | A score-bearing dimension, cap, floor or override. |
| Criticality candidate | A candidate for separately governed flag-effect review. | A critical disqualifier, cap, floor or override. |
| Evaluability state | Whether the requested conclusion can be produced under the applicable policy. | Confidence, coverage, goodness or technical execution status. |
| Future numerical score output | A result of a separately approved and validated mapping. | An intrinsic fact, safety probability, risk probability or regulatory conclusion. |

No automatic conversion is permitted between these levels. A future conversion
must identify its source level, target level, governed rule, rationale,
authority, version, applicability, limitations and validation evidence.

### B.1 Required invariants

```text
regulatory classification != goodness
hazard != risk
hazard != automatic score direction
evidence existence != favourability
confidence != goodness
uncertainty != penalty
missingness != zero
criticality candidate != automatic cap, floor or override
informational flag != score-bearing dimension
not_computable != zero
```

Absence of evidence is not an adverse outcome. Evidence uncertainty does not
automatically lower goodness. An incomplete upstream state may prevent
computation without imposing a penalty. A regulatory state does not generate a
directional scientific state. A `not_computable` result emits no number.

## C. Frozen upstream mapping and resolution vocabularies

The following vocabulary is copied without renaming from
`WYE_MAPPING_EXECUTION_INPUT_FREEZE.md`. It remains upstream technical input.

### C.1 Mapping resolution states

| Canonical state | Canonical meaning | Policy boundary |
|---|---|---|
| `resolved` | Authoritative members exist and no extending or reconstruction-invalidating observation remains. | Does not prove scientific sufficiency, favourable status or risk. |
| `empty` | No authoritative member exists and history is sufficiently complete. | Does not mean safe, harmful, absent from a product or score zero. |
| `partially_resolved` | A trustworthy non-empty subset exists but extending observations may add membership. | May block an indispensable projection; it is not a penalty. |
| `history_unavailable` | Complete trustworthy reconstruction cannot be asserted. | May block evaluation; it is not scientific uncertainty about harm. |

The canonical precedence remains owned by the input freeze. This RFC neither
restates an executable resolver nor changes the effect of multiple valid
authority chains.

### C.2 Observation kinds, reason codes and resolution impacts

The closed observation kinds remain `bridge`, `proposal`, `decision`,
`materialization`, `closure` and `authority_chain`.

| Canonical observation reason code | Canonical resolution impact |
|---|---|
| `pending_proposal` | `extends_set` |
| `pending_review_bridge` | `extends_set` |
| `ambiguous_bridge` | `extends_set` |
| `rejected_decision` | `none` |
| `rejected_bridge` | `none` |
| `deferred_decision` | `extends_set` |
| `accepted_not_materialized_as_of` | `extends_set` |
| `accepted_authority_not_effective` | `none` |
| `materialization_inconsistent` | `invalidates_reconstruction` |
| `legacy_unreviewed_bridge` | `extends_set` |
| `uncontrolled_accepted_bridge` | `extends_set` |
| `history_incomplete` | `invalidates_reconstruction` |
| `closure_history_inconsistent` | `invalidates_reconstruction` |
| `out_of_effective_range` | `none` |

The primary `resolution_reason_codes` remain
`authoritative_mapping_complete`, `no_mapping_records`,
`no_authoritative_effective_mapping`, `additional_candidates_unresolved` and
`historical_reconstruction_incomplete`.

These observation and mapping-quality terms describe mapping history,
authority, completeness or resolution. They are not ingredient scientific
states, goodness dimensions, penalties, numerical values or risk indicators.
The policy consumes them only through an explicit applicability or evaluability
assessment. No upstream name or meaning is modified here.

## D. Policy architecture alternatives

### D.1 Alternatives

| Criterion | Option A — Unified ingredient-state profile | Option B — Per-dimension applicability and state | Option C — Layered state model |
|---|---|---|---|
| Semantic clarity | Compact but combines scientific and evaluability meanings. | Clear inside each dimension but cross-dimension state meaning may drift. | Strongest separation of resolution, evidence, applicability, evaluability and score-bearing state. |
| Auditability | One summary is easy to display but difficult to decompose. | Good per-dimension trace; shared upstream causes may be repeated. | Strong end-to-end lineage with explicit hand-offs between layers. |
| Scalability | State combinations can grow and become unstable. | New dimensions can be added with their own cards. | Scales through versioned layers and dimension cards, at the cost of governance overhead. |
| Conflation risk | Highest because a single state may hide regulatory, evidence and missingness reasons. | Moderate if card authors misuse common labels. | Lowest when conversion rules and forbidden inferences are enforced. |
| Multi-axis and multi-label ontology | Weak fit; pressure toward a primary state. | Strong fit per dimension. | Strong fit while preserving all assertions and contextual precedence. |
| Compatibility with Mapping RFC Option B | Moderate; a profile must be decomposed before use. | Strong; directly exposes candidate attributes. | Strong; score-bearing candidates are exposed only after upstream and support layers remain separate. |
| Missingness handling | Easy to hide inside a summary state. | Explicit by dimension but may be inconsistently interpreted. | Explicit support layer and separate evaluability outcome. |
| Double-counting risk | High because one profile may encode overlapping causes. | Moderate; requires a cross-card register. | Lowest candidate risk when dependency edges and shared evidence identities are retained. |
| Versionability | A change to one aspect can force a whole-profile version. | Fine-grained but may create incompatible card versions. | Explicit layer and card versions with a policy-set identity. |
| Validation requirements | Requires whole-profile judgment and decomposition tests. | Requires per-dimension plus integration validation. | Requires layer transition, dimension, dependency and end-to-end validation. |

### D.2 Reversible recommendation

`PROPOSED, NOT APPROVED`: Option C, the layered state model, is recommended as
the policy-organization candidate. It best preserves the already approved
multi-axis ontology boundary while allowing a future Mapping RFC Option B model
to consume only explicitly eligible dimension states. Option B in this section
is a policy-architecture alternative and must not be confused with Option B in
the parent Mapping RFC.

The recommendation was reversible until the product-owner candidate-direction
selection recorded below. That selection is not scientific approval, independent
validation or a final method decision. Internal methodology review may require a
hybrid or replacement. A future exact candidate must show that layer transitions
do not lose provenance, strengthen conclusions or turn support states into score
directions.

### D.3 Product-owner candidate-direction selection

```text
selection_date: 2026-09-02
selection_authority: Product owner
selected_candidate_direction: Policy Option C — Layered state model
selection_nature: CANDIDATE DESIGN DIRECTION ONLY
selection_status: PRODUCT-OWNER CANDIDATE DIRECTION — NOT SCIENTIFICALLY OR INDEPENDENTLY VALIDATED
PSC-OD-005: OPEN
scientific_approval: NOT CLAIMED
independent_validation: NOT PRESENT
implementation_authority: NONE
release_authority: NONE
```

The product owner selects Policy Option C — Layered state model exclusively as
the candidate design direction for the Candidate Ingredient State and Dimension
Policy. This selection preserves the separation between upstream mapping,
evidence, scientific state, score-bearing dimensions, support dimensions,
informational flags, criticality, evaluability and future numerical output. It
does not approve any state, dimension, formula, transformation, weight,
threshold, parameter, comparability or numerical output. `PSC-OD-005` remains
`OPEN`; `PSC-OD-006` remains not started.

## E. Candidate ingredient-state policy

### E.1 Allocation rule

The Contract's minimum ingredient assessment vocabulary is retained verbatim,
but its terms are allocated to distinct candidate semantic roles. Retention
does not approve the allocation. Multiple compatible terms may coexist; no
primary-state precedence or transition order is approved.

| Contract term | Candidate semantic allocation | Candidate role |
|---|---|---|
| `no_identified_concern` | Ingredient scientific state | Scientific conclusion candidate. |
| `authorised_with_conditions` | Source-backed regulatory classification | Informational/regulatory fact. |
| `exposure_dependent` | Ingredient scientific state with mandatory context dependency | Scientific state candidate that is not intrinsically directional. |
| `under_re_evaluation` | Source-backed regulatory or scientific lifecycle classification | Informational/support fact. |
| `evidence_uncertain` | Evidence-synthesis support state | Support only. |
| `conflicting_evidence` | Evidence-synthesis result | Support only until a separately reviewed scientific-state rule exists. |
| `critical_concern` | Criticality candidate | No automatic scoring effect. |
| `not_authorised` | Source-backed regulatory classification | Informational/regulatory fact. |
| `withdrawn` | Source-backed regulatory or scientific lifecycle classification | Informational/regulatory fact with exact scope required. |
| `unresolved` | Ingredient scientific-state boundary outcome | Candidate blocker only when the unresolved item is indispensable. |
| `insufficient_data` | Evidence support/evaluability boundary | Support-only candidate blocker, not an adverse state. |

### E.2 Common card rules

All state cards below have approval status `CANDIDATE — NOT APPROVED`, require
the exact source cutoff and immutable provenance, and are governed by the
scientific review panel plus validation owner for any scoring use. Product or
regulatory reviewers retain their separate semantic authorities. None of the
cards is runtime-ready. Their shared scientific disposition is
`REQUIRES_SCIENTIFIC_REVIEW`. Entry and exit conditions describe conceptual
review transitions only.

### E.3 State card — `no_identified_concern`

- **Candidate state ID:** `IS-CAND-NO-IDENTIFIED-CONCERN`.
- **Label:** `no_identified_concern`.
- **Definition:** no concern was identified for the exact reviewed question,
  subject, evidence scope, applicable context and cutoff.
- **Semantic level:** ingredient scientific state candidate.
- **Entry conditions:** governed identity and mapping; approved question;
  eligible and applicable synthesis; reviewed sufficiency; explicit scope and
  limitations.
- **Exit conditions:** changed evidence or cutoff, scope change, unresolved
  applicability, material conflict, supersession or review withdrawal.
- **Required inputs:** endpoint synthesis, applicability, provenance,
  sufficiency, uncertainty and confidence statement.
- **Forbidden inputs:** regulatory authorization alone, category label, source
  count, absence of selected evidence, source prestige or AI inference.
- **Applicability:** meaningful only for the exact reviewed scope.
- **Evaluability:** may support a future evaluability decision but does not make
  a result computable by itself.
- **Missingness:** missing required evidence prevents this state; it never
  supplies a favourable default.
- **Confidence and uncertainty:** reported separately and cannot strengthen the
  state beyond the supported conclusion.
- **Possibility of a number:** `UNRESOLVED`; never automatic.
- **Allowed output:** bounded non-numeric scientific conclusion with trace.
- **Forbidden output:** universal safety, absence of hazard, favourable score or
  cross-context transfer.
- **Source/provenance requirements:** immutable source, selection, synthesis,
  mapping and review identities.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-016`, `PSC-OD-017`,
  `PSC-OD-019` and `PSC-OD-020`.
- **Validation requirements:** reference judgments, adversarial scope changes,
  reproducibility and false-reassurance review.
- **Authority:** scientific review panel plus validation owner; communication
  review for external wording.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.4 State card — `authorised_with_conditions`

- **Candidate state ID:** `IS-CAND-AUTHORISED-WITH-CONDITIONS`.
- **Label:** `authorised_with_conditions`.
- **Definition:** a scoped authority assertion records authorization subject to
  identified jurisdiction, date, category, use, specification or conditions.
- **Semantic level:** source-backed regulatory classification, not ingredient
  scientific state.
- **Entry conditions:** competent source, exact subject and scope,
  applicability review and provenance.
- **Exit conditions:** scope no longer matches, authority changes, withdrawal,
  supersession, conflict or review reversal.
- **Required inputs:** regulatory artifact, source version, jurisdiction,
  effective time, use and conditions.
- **Forbidden inputs:** label name alone, category membership alone, hazard
  conclusion or assumed compliance.
- **Applicability:** explicitly contextual; never entity-global by default.
- **Evaluability:** may be a required fact for a future question but does not
  establish scientific evaluability.
- **Missingness:** absent authorization evidence remains unknown, not adverse.
- **Confidence and uncertainty:** separate review statements; neither changes
  regulatory meaning.
- **Possibility of a number:** `NO` from this state alone.
- **Allowed output:** scoped regulatory fact and conditions.
- **Forbidden output:** goodness direction, universal safety, product compliance
  or score effect.
- **Source/provenance requirements:** immutable competent-source artifact and
  reviewed applicability trace.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-016` and
  `PSC-OD-020`.
- **Validation requirements:** scope, temporal, jurisdiction and proxy-leakage
  cases.
- **Authority:** regulatory reviewer for classification; scientific panel and
  validation owner for any proposed scoring use.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.5 State card — `exposure_dependent`

- **Candidate state ID:** `IS-CAND-EXPOSURE-DEPENDENT`.
- **Label:** `exposure_dependent`.
- **Definition:** interpretation materially depends on compatible quantity,
  concentration, intake, frequency, duration, route, population or scenario.
- **Semantic level:** ingredient scientific state candidate with support-layer
  dependency.
- **Entry conditions:** a reviewed scientific question identifies exposure as
  material and the dependence is traceable.
- **Exit conditions:** a compatible exposure context is assessed, the question
  changes, or scientific review declares exposure non-material.
- **Required inputs:** scoped hazard/evidence conclusion, projection context,
  exposure-readiness state and applicability.
- **Forbidden inputs:** ingredient-list presence as dose, label order as amount,
  or assumed consumption.
- **Applicability:** depends on the exact endpoint and product scenario.
- **Evaluability:** can block the requested conclusion when exposure is
  indispensable and unavailable.
- **Missingness:** absent exposure context is a named gap, not badness.
- **Confidence and uncertainty:** exposure and transfer uncertainty remain
  separate support items.
- **Possibility of a number:** `NO` without an approved compatible context and
  all later gates; otherwise still `UNRESOLVED` here.
- **Allowed output:** non-numeric dependency statement and blocking reasons.
- **Forbidden output:** risk, penalty or goodness direction inferred from hazard
  or presence.
- **Source/provenance requirements:** endpoint, projection, composition and
  scenario trace.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-006`, `PSC-OD-016`,
  `PSC-OD-017` and `PSC-OD-019`.
- **Validation requirements:** compatible and incompatible scenario pairs,
  missing-exposure cases and transfer tests.
- **Authority:** scientific review panel plus validation owner.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.6 State card — `under_re_evaluation`

- **Candidate state ID:** `IS-CAND-UNDER-RE-EVALUATION`.
- **Label:** `under_re_evaluation`.
- **Definition:** a relevant authoritative assessment or follow-up is not yet
  complete for the stated scope.
- **Semantic level:** source-backed lifecycle classification.
- **Entry conditions:** governed authority artifact and applicable open
  reassessment status.
- **Exit conditions:** completion, withdrawal, supersession, scope mismatch or
  source correction.
- **Required inputs:** authority, subject, question, status, dates and source
  version.
- **Forbidden inputs:** rumor, popularity, controversy or an unverified mutable
  page.
- **Applicability:** must match subject, jurisdiction or scientific remit,
  question and cutoff.
- **Evaluability:** may qualify or block only if a future approved policy makes
  it indispensable.
- **Missingness:** an unknown lifecycle status is not this state.
- **Confidence and uncertainty:** separately records uncertainty about the
  current conclusion; it is not an adverse direction.
- **Possibility of a number:** `NO` from this state alone.
- **Allowed output:** scoped lifecycle fact and unresolved review limitation.
- **Forbidden output:** danger, clearance, penalty, cap or provisional score.
- **Source/provenance requirements:** immutable status artifact and temporal
  trace.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-016` and
  `PSC-OD-020`.
- **Validation requirements:** temporal replay, completion and scope-change
  cases.
- **Authority:** competent source reviewer; scientific panel for downstream
  interpretation.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.7 State card — `evidence_uncertain`

- **Candidate state ID:** `IS-CAND-EVIDENCE-UNCERTAIN`.
- **Label:** `evidence_uncertain`.
- **Definition:** eligible evidence has material limitations in relevance,
  quality, precision, indirectness, heterogeneity or completeness.
- **Semantic level:** evidence-synthesis support state.
- **Entry conditions:** a governed synthesis identifies and scopes uncertainty
  items.
- **Exit conditions:** new evidence, reviewed resolution, scope change or
  synthesis supersession.
- **Required inputs:** evidence-line trace, quality and relevance profiles,
  uncertainty items and synthesis scope.
- **Forbidden inputs:** source count, provider prestige or generic reputation.
- **Applicability:** attached to the exact conclusion and evidence scope.
- **Evaluability:** may qualify or block only through an approved
  indispensability rule.
- **Missingness:** uncertainty and missingness remain distinct and both are
  named.
- **Confidence and uncertainty:** uncertainty is primary support information;
  confidence is a separate conclusion-specific statement.
- **Possibility of a number:** `NO` as an automatic consequence.
- **Allowed output:** uncertainty statement, limitations and reduction needs.
- **Forbidden output:** penalty, adverse state, danger or low goodness.
- **Source/provenance requirements:** immutable evidence and synthesis artifacts
  plus review references.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-016`, `PSC-OD-017`,
  `PSC-OD-019` and `PSC-OD-020`.
- **Validation requirements:** uncertainty propagation, reviewer agreement and
  penalty-leakage tests.
- **Authority:** scientific review panel plus validation owner.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.8 State card — `conflicting_evidence`

- **Candidate state ID:** `IS-CAND-CONFLICTING-EVIDENCE`.
- **Label:** `conflicting_evidence`.
- **Definition:** comparable eligible evidence remains materially incompatible
  after context, correction, dependency, relevance and quality appraisal.
- **Semantic level:** evidence-synthesis result.
- **Entry conditions:** governed comparability and true-conflict review.
- **Exit conditions:** reviewed contextual resolution, correction,
  supersession, new evidence or changed question.
- **Required inputs:** all supporting and contrary lines, comparison basis,
  dependency edges and conflict trace.
- **Forbidden inputs:** surface disagreement, non-comparable evidence, vote,
  averaging or source-prestige tie-break.
- **Applicability:** scoped to the exact endpoint and context.
- **Evaluability:** candidate blocker for an affected indispensable conclusion;
  exact effect remains open.
- **Missingness:** conflict is not missing evidence and must not be collapsed
  into insufficiency.
- **Confidence and uncertainty:** conflict uncertainty is retained; confidence
  cannot resolve the conflict.
- **Possibility of a number:** `NO` for a blocked conclusion; otherwise
  `UNRESOLVED` pending approved policy.
- **Allowed output:** explicit conflict state and bounded descriptions.
- **Forbidden output:** mean conclusion, automatic danger, automatic penalty or
  provider winner.
- **Source/provenance requirements:** comparison groups, evidence lineage,
  synthesis and review artifacts.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-016`, `PSC-OD-017`,
  `PSC-OD-019` and `PSC-OD-020`.
- **Validation requirements:** apparent-versus-true conflict corpus,
  dependency cases and reproducibility.
- **Authority:** scientific review panel plus validation owner.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.9 State card — `critical_concern`

- **Candidate state ID:** `IS-CAND-CRITICAL-CONCERN`.
- **Label:** `critical_concern`.
- **Definition:** a serious, qualified concern candidate has been identified
  and may be applicable, without assigning a scoring effect.
- **Semantic level:** criticality candidate.
- **Entry conditions:** exact endpoint, subject, evidence, scope, applicability
  and reviewed concern rationale.
- **Exit conditions:** non-applicability, conflict resolution, new evidence,
  supersession or rejected criticality review.
- **Required inputs:** scientific conclusion, applicability, provenance and
  candidate criticality rationale.
- **Forbidden inputs:** controversy, artificiality, one isolated study,
  unresolved identity or hazard alone.
- **Applicability:** must be established for the exact product question before
  any downstream effect is considered.
- **Evaluability:** separate; an unresolved candidate may block only under an
  approved rule.
- **Missingness:** missing data cannot create criticality.
- **Confidence and uncertainty:** remain explicit and do not become severity.
- **Possibility of a number:** `NO` from the candidate state.
- **Allowed output:** traced criticality candidate for separate review.
- **Forbidden output:** `critical_disqualifier`, cap, floor, override, zero or
  automatic score direction.
- **Source/provenance requirements:** immutable scientific and applicability
  trace.
- **Dependent decisions:** `PSC-OD-013`, `PSC-OD-014`, `PSC-OD-016`,
  `PSC-OD-019` and `PSC-OD-020`.
- **Validation requirements:** false-positive, no-double-counting,
  reproducibility and communication studies.
- **Authority:** authorities named in `PSC-OD-013` and `PSC-OD-014`; this RFC
  grants none.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.10 State card — `not_authorised`

- **Candidate state ID:** `IS-CAND-NOT-AUTHORISED`.
- **Label:** `not_authorised`.
- **Definition:** an identified use is not authorized for an exact jurisdiction,
  date, product category and conditions.
- **Semantic level:** source-backed regulatory classification.
- **Entry conditions:** competent authority source, exact identity, use and
  applicability review.
- **Exit conditions:** authorization change, scope mismatch, supersession,
  correction or review reversal.
- **Required inputs:** source artifact, jurisdiction, date, use, category,
  conditions and identity.
- **Forbidden inputs:** absence from a list without an approved completeness
  rule, category label alone or scientific hazard evidence.
- **Applicability:** strictly scoped; no global entity status is inferred.
- **Evaluability:** a future policy may require the fact, but this state does not
  decide computability.
- **Missingness:** missing authorization evidence remains unresolved.
- **Confidence and uncertainty:** separate from the regulatory assertion.
- **Possibility of a number:** `NO` from this state alone.
- **Allowed output:** scoped regulatory fact.
- **Forbidden output:** poisonous, dangerous, low goodness, product
  non-compliance or automatic criticality.
- **Source/provenance requirements:** immutable competent-source and
  applicability trace.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-014`,
  `PSC-OD-016` and `PSC-OD-020`.
- **Validation requirements:** jurisdiction, use, temporal and false-proxy
  cases.
- **Authority:** regulatory reviewer for status; scientific panel and
  validation owner for any score proposal.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.11 State card — `withdrawn`

- **Candidate state ID:** `IS-CAND-WITHDRAWN`.
- **Label:** `withdrawn`.
- **Definition:** a relevant authorization, assessment or use was withdrawn;
  withdrawal type, subject and scope are explicit.
- **Semantic level:** source-backed regulatory or scientific lifecycle
  classification.
- **Entry conditions:** governed withdrawal event with predecessor, authority,
  scope and effective time.
- **Exit conditions:** correction, reinstatement, scope mismatch or superseding
  authority event.
- **Required inputs:** immutable lifecycle lineage and applicability review.
- **Forbidden inputs:** a missing current record, rumor or an unrelated
  jurisdiction.
- **Applicability:** bounded by the withdrawn object and scope.
- **Evaluability:** candidate blocker only if an approved policy makes that
  lifecycle fact indispensable.
- **Missingness:** absence of history is `history_unavailable`, not `withdrawn`.
- **Confidence and uncertainty:** separate; history uncertainty cannot be
  rewritten as withdrawal.
- **Possibility of a number:** `NO` from this state alone.
- **Allowed output:** scoped lifecycle fact and lineage.
- **Forbidden output:** universal prohibition, danger, penalty or score
  direction.
- **Source/provenance requirements:** predecessor, event, source version and
  effective-time trace.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-016` and
  `PSC-OD-020`.
- **Validation requirements:** historical replay, reinstatement and scope cases.
- **Authority:** competent source reviewer; separate scientific authority for
  downstream use.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.12 State card — `unresolved`

- **Candidate state ID:** `IS-CAND-UNRESOLVED`.
- **Label:** `unresolved`.
- **Definition:** a required identity, relationship, form, regulatory match,
  scientific interpretation or applicability question cannot be resolved
  canonically.
- **Semantic level:** ingredient scientific-state boundary outcome; the exact
  unresolved layer must always be named.
- **Entry conditions:** a governed process reaches a recorded unresolved result
  with candidates and missing resolution evidence preserved.
- **Exit conditions:** competent review or new governed evidence resolves the
  exact issue.
- **Required inputs:** layer identifier, candidate interpretations, reasons,
  provenance and resolution need.
- **Forbidden inputs:** a generic unknown label with no affected question or
  arbitrary worst-case selection.
- **Applicability:** cannot be inferred while a material applicability question
  is unresolved.
- **Evaluability:** may produce `not_computable` only when the unresolved item is
  indispensable under an approved policy.
- **Missingness:** may coexist with missing inputs but is not their numerical
  replacement.
- **Confidence and uncertainty:** uncertainty is recorded; confidence cannot
  manufacture resolution.
- **Possibility of a number:** `NO` when indispensable; otherwise
  `UNRESOLVED` pending policy.
- **Allowed output:** typed unresolved result and required resolution action.
- **Forbidden output:** danger, safety, zero, imputation, midpoint or guessed
  candidate.
- **Source/provenance requirements:** complete attempted-resolution trace and
  candidate identities.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-015`, `PSC-OD-016`,
  `PSC-OD-017` and `PSC-OD-019`.
- **Validation requirements:** layer-specific unresolved cases and recovery
  transitions.
- **Authority:** scientific review panel plus validation owner for policy use.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.13 State card — `insufficient_data`

- **Candidate state ID:** `IS-CAND-INSUFFICIENT-DATA`.
- **Label:** `insufficient_data`.
- **Definition:** the target is sufficiently identified, but data required for
  the exact scoped conclusion do not meet reviewed sufficiency requirements.
- **Semantic level:** evidence support and evaluability boundary.
- **Entry conditions:** governed sufficiency appraisal names unmet criteria and
  critical data gaps.
- **Exit conditions:** new eligible evidence, a reviewed narrower conclusion or
  a changed question.
- **Required inputs:** question, sufficiency criteria version, criterion results,
  gaps and evidence trace.
- **Forbidden inputs:** raw record count, lack of a preferred outcome or
  confidence label alone.
- **Applicability:** assessed only after subject and question applicability are
  known.
- **Evaluability:** candidate `not_computable` trigger for an indispensable
  conclusion; exact rule remains open.
- **Missingness:** explicitly identifies missing scientific support without
  assigning outcome.
- **Confidence and uncertainty:** separate statements; low confidence is not a
  substitute for insufficiency.
- **Possibility of a number:** `NO` for the unsupported conclusion.
- **Allowed output:** insufficiency conclusion, available descriptive evidence
  and required data.
- **Forbidden output:** adverse outcome, safety, penalty, neutral value or zero.
- **Source/provenance requirements:** selection, synthesis, criteria and review
  artifacts.
- **Dependent decisions:** `PSC-OD-005`, `PSC-OD-015`, `PSC-OD-016`,
  `PSC-OD-017` and `PSC-OD-019`.
- **Validation requirements:** sufficiency boundary, narrower-conclusion and
  missing-data bias cases.
- **Authority:** scientific review panel plus validation owner.
- **Approval status:** `CANDIDATE — NOT APPROVED`.

### E.14 Conceptual transitions only

A future state-transition proposal may move between scoped review states only
after a new immutable evidence, mapping, applicability or decision artifact.
No transition is triggered by elapsed time, source count, AI output, UI action
or score target. This is a conceptual governance statement, not a state machine
or runtime specification.

## F. Dimension eligibility policy

Before a dimension can be considered score-bearing, its reviewed card must
satisfy every candidate criterion below:

- construct relevance to the favourability boundary decided under
  `PSC-OD-002`;
- a non-ambiguous scientific definition;
- explicit subject and target conclusion;
- source backing and immutable provenance;
- scientifically defensible directionality;
- definable applicability and non-applicability;
- enough evidence semantics to distinguish missingness from outcome;
- a testable monotonicity hypothesis in its declared domain;
- an assessable double-counting risk;
- documented dependencies and correlations;
- separation from coverage, confidence and uncertainty;
- no automatic overlap with nutrition score;
- no unjustified regulatory proxy;
- a feasible validation plan;
- versionable canonical identity;
- interpretable use within the non-clinical intended use.

A dimension remains non-score-bearing when it is only a flag, measures evidence
quality rather than goodness, represents missingness, represents confidence or
uncertainty, duplicates another dimension, overlaps nutrition without
justification, uses regulatory status as a proxy, lacks defensible direction,
or cannot be validated and reproduced.

Passing this eligibility screen would create only a candidate for scientific
review. It would not approve a direction, transformation or score effect.

## G. Candidate dimension inventory

### G.1 Inventory summary

| Candidate dimension ID | Canonical name | Candidate classification | Main reason |
|---|---|---|---|
| `DIM-CAND-INGREDIENT-FAVOURABILITY` | ingredient scientific favourability | `UNRESOLVED` | Required construct link exists, but no validated scientific definition, direction or reference judgments exist. |
| `DIM-CAND-HAZARD` | `hazard` | `UNRESOLVED` | Scientifically relevant input, but hazard has no automatic goodness direction and is not risk. |
| `DIM-INFO-REGULATORY-STATUS` | `regulatory_status` | `INFORMATIONAL ONLY` | Scoped regulatory fact cannot proxy goodness. |
| `DIM-SUPPORT-EVIDENCE-STATE` | `evidence_state` | `SUPPORT ONLY` | Describes evidence support, not favourability. |
| `DIM-SUPPORT-EXPOSURE` | `exposure` | `SUPPORT ONLY` | Contextual dependency needed for risk-like questions, not intrinsic ingredient goodness. |
| `DIM-SUPPORT-RISK` | `risk` | `SUPPORT ONLY` | Requires compatible hazard and exposure and remains outside a context-free ingredient property. |
| `DIM-SUPPORT-APPLICABILITY` | `applicability` | `SUPPORT ONLY` | Governs whether a conclusion applies, not its goodness direction. |
| `DIM-SUPPORT-CONFIDENCE` | `confidence` | `SUPPORT ONLY` | Confidence in a conclusion is not goodness. |
| `DIM-SUPPORT-UNCERTAINTY` | `uncertainty` | `SUPPORT ONLY` | Limitations are not penalties. |
| `DIM-SUPPORT-MAPPING-RESOLUTION` | mapping resolution | `SUPPORT ONLY` | Technical mapping completeness is not scientific outcome. |
| `DIM-SUPPORT-COVERAGE` | coverage | `SUPPORT ONLY` | Extent of usable support within the applicable perimeter is not favourability or confidence. |
| `DIM-SUPPORT-MISSINGNESS` | missingness and incomplete-data guardrail | `SUPPORT ONLY` | Absence or unavailability of required data is not an outcome, penalty or numerical value. |
| `DIM-CAND-CRITICALITY` | criticality/flag effect | `CRITICALITY CANDIDATE` | Separate decisions own any effect. |
| `DIM-EXCL-NUTRITION-PROPERTY` | ingredient nutritional property | `EXCLUDED` | Automatic reuse would duplicate the future nutrition score. |
| `DIM-INFO-ONTOLOGY-LABEL` | ontology/category label | `INFORMATIONAL ONLY` | Multi-label role assertion has no automatic direction. |

No listed dimension currently qualifies as an approved score-bearing dimension.
The minimum missing artifact is a scientifically reviewed dimension-card set
with reference judgments, applicability cases, dependency annotations and a
validation corpus. This gap is deliberate; it must not be filled by an
unsupported label-to-score mapping.

### G.2 Dimension card — ingredient scientific favourability

- **Candidate dimension ID / name:** `DIM-CAND-INGREDIENT-FAVOURABILITY` /
  ingredient scientific favourability.
- **Definition / construct link:** a still-unresolved ingredient-level aspect of
  protocol-relative compositional favourability under `PSC-OD-002`; it is not
  safety, risk or regulatory compliance.
- **Score-bearing status / status:** `UNRESOLVED`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** a canonically identified ingredient in the bounded
  packaged-food domain and an exact scientific question.
- **Source types / evidence inputs:** governed scientific assessments,
  endpoint syntheses and ingredient projections; no source type is sufficient
  by prestige alone.
- **Directionality / monotonicity:** `UNRESOLVED`; a scientific rationale and
  bounded monotonicity hypothesis are required.
- **Applicability / non-applicability:** requires resolved subject, compatible
  question and reviewed product context; not applicable outside the declared
  domain or question.
- **Missing-data / confidence / uncertainty:** remain support outputs; none
  supplies a direction or value.
- **Regulatory / hazard-exposure-risk relationship:** regulatory facts remain
  separate; hazard may inform review but is not direction; risk requires
  compatible exposure and context.
- **Nutrition overlap / dependencies / double counting:** potential overlap with
  nutrient properties is unresolved; depends on scientific states and support
  dimensions; high risk of proxy duplication.
- **Forbidden interpretations:** intrinsic goodness, universal safety, clinical
  benefit, risk probability or product compliance.
- **Validation needs / decisions:** construct validity, expert judgments,
  monotonicity, robustness and comprehension under `PSC-OD-005`,
  `PSC-OD-016`, `PSC-OD-019` and `PSC-OD-020`.

### G.3 Dimension card — hazard

- **Candidate dimension ID / name:** `DIM-CAND-HAZARD` / `hazard`.
- **Definition / construct link:** endpoint-scoped potential for an adverse
  effect under stated conditions; any link to ingredient favourability remains
  unresolved under `PSC-OD-002`.
- **Score-bearing status / status:** `UNRESOLVED`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** substance or ingredient scientific projection for an
  exact endpoint and compatible form.
- **Source types / evidence inputs:** selected scientific evidence, endpoint
  synthesis, hazard profile and projection trace.
- **Directionality / monotonicity:** `UNRESOLVED`; hazard presence or severity
  has no automatic score direction, and non-monotonicity risks require review.
- **Applicability / non-applicability:** form, endpoint, route, population and
  conditions must match; non-applicable where transfer is not permitted.
- **Missing-data / confidence / uncertainty:** preserve gaps, synthesis
  confidence and uncertainty separately.
- **Regulatory / hazard-exposure-risk relationship:** not regulatory status;
  does not establish exposure or risk.
- **Nutrition overlap / dependencies / double counting:** ordinarily separate
  from nutrition, but shared biological endpoints require review; overlaps
  criticality candidates and risk evidence.
- **Forbidden interpretations:** risk, penalty, cap, override, product danger or
  goodness direction.
- **Validation needs / decisions:** endpoint and direction judgments,
  applicability, criticality no-double-counting and adversarial cases under
  `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-016` and `PSC-OD-019`.

### G.4 Dimension card — regulatory status

- **Candidate dimension ID / name:** `DIM-INFO-REGULATORY-STATUS` /
  `regulatory_status`.
- **Definition / construct link:** scoped authority assertion; relevant to the
  Contract trace but not a direct goodness construct.
- **Score-bearing status / status:** `INFORMATIONAL ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** exact entity, use, jurisdiction, time, product category
  and conditions.
- **Source types / evidence inputs:** competent regulatory artifacts and reviewed
  ontology assertions.
- **Directionality / monotonicity:** not approved and not presumed.
- **Applicability / non-applicability:** exact scope match required; otherwise
  non-applicable or unresolved.
- **Missing-data / confidence / uncertainty:** absence remains unknown; review
  quality and uncertainty stay separate.
- **Regulatory / hazard-exposure-risk relationship:** is the regulatory channel;
  implies none of hazard, exposure or risk.
- **Nutrition overlap / dependencies / double counting:** may overlap category
  rules in nutrition; automatic reuse is forbidden; depends on ontology and
  source applicability.
- **Forbidden interpretations:** goodness, safety, risk, compliance of a product
  or automatic criticality.
- **Validation needs / decisions:** jurisdictional, temporal, proxy-leakage and
  scope cases under `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-016` and `PSC-OD-020`.

### G.5 Dimension card — evidence state

- **Candidate dimension ID / name:** `DIM-SUPPORT-EVIDENCE-STATE` /
  `evidence_state`.
- **Definition / construct link:** selection and synthesis disposition for an
  exact scientific question; supports interpretation but does not measure
  favourability.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** evidence line, comparison group, endpoint synthesis and
  scoped ingredient projection.
- **Source types / evidence inputs:** governed evidence artifacts, selection
  trace, sufficiency and conflict appraisal.
- **Directionality / monotonicity:** not applicable as goodness direction.
- **Applicability / non-applicability:** question-specific; non-applicable when
  the evidence channel cannot answer the question.
- **Missing-data / confidence / uncertainty:** explicitly distinguishes no
  selected evidence, insufficiency, conflict, confidence and uncertainty.
- **Regulatory / hazard-exposure-risk relationship:** regulatory channels remain
  separate; evidence state alone establishes none of hazard, exposure or risk.
- **Nutrition overlap / dependencies / double counting:** separate domain
  evidence policies may share source artifacts but not conclusions; overlaps
  confidence, uncertainty and coverage if poorly designed.
- **Forbidden interpretations:** more evidence means better or worse, low
  quality means low goodness, or conflict means danger.
- **Validation needs / decisions:** evidence-state reproducibility,
  dependency-aware cases and leakage tests under `PSC-OD-005`, `PSC-OD-017`
  and `PSC-OD-019`.

### G.6 Dimension card — exposure

- **Candidate dimension ID / name:** `DIM-SUPPORT-EXPOSURE` / `exposure`.
- **Definition / construct link:** amount or contact under a stated scenario;
  support for context-dependent interpretation, not intrinsic favourability.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** ingredient or substance in a product scenario with
  route, population, duration and basis.
- **Source types / evidence inputs:** governed composition, quantity, scenario
  and exposure-readiness artifacts.
- **Directionality / monotonicity:** no universal goodness direction; contextual
  and potentially non-monotonic.
- **Applicability / non-applicability:** required only for questions that depend
  on exposure; legitimately non-applicable otherwise.
- **Missing-data / confidence / uncertainty:** missing amount or scenario may
  block; it is not a penalty; exposure uncertainty is separate.
- **Regulatory / hazard-exposure-risk relationship:** neither regulatory status
  nor hazard; required with compatible hazard for risk characterization.
- **Nutrition overlap / dependencies / double counting:** consumption and basis
  concepts may overlap nutrition inputs; reuse requires explicit policy;
  causally upstream of risk.
- **Forbidden interpretations:** label presence as dose, ingredient order as
  quantity, missing exposure as low or high risk.
- **Validation needs / decisions:** scenario compatibility, no-default and unit
  semantics under `PSC-OD-005`, `PSC-OD-006`, `PSC-OD-016` and `PSC-OD-019`.

### G.7 Dimension card — risk

- **Candidate dimension ID / name:** `DIM-SUPPORT-RISK` / `risk`.
- **Definition / construct link:** context-specific characterization requiring
  compatible hazard, exposure and applicability; it is not the decided
  ingredient-goodness construct.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** a defined product, scenario, population and endpoint.
- **Source types / evidence inputs:** reviewed hazard, exposure, projection and
  risk-protocol artifacts.
- **Directionality / monotonicity:** no ingredient-goodness direction is
  approved; any relationship is context- and protocol-specific.
- **Applicability / non-applicability:** requires all compatible gate inputs;
  otherwise non-computable, unresolved or non-applicable.
- **Missing-data / confidence / uncertainty:** missing inputs prevent risk
  characterization without supplying a risk level; confidence and uncertainty
  remain separate.
- **Regulatory / hazard-exposure-risk relationship:** not regulatory status;
  downstream of compatible hazard and exposure.
- **Nutrition overlap / dependencies / double counting:** may share population
  or consumption context but must not become nutrition score; duplicates hazard
  and exposure if counted independently.
- **Forbidden interpretations:** context-free ingredient property, personal
  prediction or substitute for goodness.
- **Validation needs / decisions:** compatible-context, causal dependency and
  non-computability tests under `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-016` and
  `PSC-OD-019`.

### G.8 Dimension card — applicability

- **Candidate dimension ID / name:** `DIM-SUPPORT-APPLICABILITY` /
  `applicability`.
- **Definition / construct link:** whether a source-backed proposition or
  dimension answers the exact subject, domain and question.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** every source assertion, evidence line, synthesis,
  projection and candidate dimension.
- **Source types / evidence inputs:** scope, identity, context and reviewed
  transfer rules.
- **Directionality / monotonicity:** none; applicable does not mean favourable.
- **Applicability / non-applicability:** its own outcome is explicit and
  dimension-specific; unknown is not a match.
- **Missing-data / confidence / uncertainty:** missing material context yields
  unresolved applicability, not an adverse value.
- **Regulatory / hazard-exposure-risk relationship:** independently assessed in
  each channel.
- **Nutrition overlap / dependencies / double counting:** shared governance
  pattern but separate domain questions; hierarchical relation with
  evaluability.
- **Forbidden interpretations:** applicable as true, favourable, safe or
  score-bearing; non-applicable as zero.
- **Validation needs / decisions:** scope transfer, unknown and exception cases
  under `PSC-OD-005`, `PSC-OD-016` and `PSC-OD-019`.

### G.9 Dimension card — confidence

- **Candidate dimension ID / name:** `DIM-SUPPORT-CONFIDENCE` / `confidence`.
- **Definition / construct link:** support for one exact conclusion, not
  favourability.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** a defined conclusion at evidence, projection or product
  level.
- **Source types / evidence inputs:** quality, relevance, consistency, coverage,
  uncertainty, provenance and method limitations.
- **Directionality / monotonicity:** no goodness direction; higher confidence in
  an adverse or favourable conclusion has different content.
- **Applicability / non-applicability:** only where the exact conclusion exists;
  may describe confidence in a non-computability conclusion.
- **Missing-data / confidence / uncertainty:** missingness and uncertainty can
  inform confidence but are not synonyms; no multiplier is authorized.
- **Regulatory / hazard-exposure-risk relationship:** conclusion-specific and
  never a proxy for any channel.
- **Nutrition overlap / dependencies / double counting:** separate confidence
  statements are required by domain; overlaps evidence quality and uncertainty
  unless identities are retained.
- **Forbidden interpretations:** goodness, safety probability, evaluability or
  penalty.
- **Validation needs / decisions:** derivation, reviewer agreement and proxy
  leakage under `PSC-OD-017` and `PSC-OD-019`.

### G.10 Dimension card — uncertainty

- **Candidate dimension ID / name:** `DIM-SUPPORT-UNCERTAINTY` / `uncertainty`.
- **Definition / construct link:** typed limitations affecting inputs, method or
  conclusion; not favourability.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** source, evidence, mapping, projection, exposure, risk
  and method layers.
- **Source types / evidence inputs:** traceable uncertainty items with source,
  scope, impact and reduction needs.
- **Directionality / monotonicity:** no automatic direction and no penalty.
- **Applicability / non-applicability:** attaches only to affected conclusions
  and propagates without cancellation.
- **Missing-data / confidence / uncertainty:** missingness may create an
  uncertainty item but remains separately named; confidence is a separate
  conclusion statement.
- **Regulatory / hazard-exposure-risk relationship:** can affect each channel
  but is not any of them.
- **Nutrition overlap / dependencies / double counting:** domain-specific items
  may share provenance; duplicate use as both uncertainty and score is
  forbidden.
- **Forbidden interpretations:** adverse evidence, penalty, score decrement or
  probability of harm.
- **Validation needs / decisions:** propagation, reduction and sensitivity
  review under `PSC-OD-017` and `PSC-OD-019`.

### G.11 Dimension card — mapping resolution

- **Candidate dimension ID / name:** `DIM-SUPPORT-MAPPING-RESOLUTION` / mapping
  resolution.
- **Definition / construct link:** completeness and trustworthiness of the
  frozen ingredient-substance mapping reconstruction.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** ingredient mapping manifest at a frozen viewpoint.
- **Source types / evidence inputs:** mapping members, observations, reason
  codes, authority chains and digests.
- **Directionality / monotonicity:** no goodness direction.
- **Applicability / non-applicability:** required for ingredient projection;
  other target types may use the upstream `not_applicable` state.
- **Missing-data / confidence / uncertainty:** incomplete history may block
  projection; it is not scientific evidence or low goodness.
- **Regulatory / hazard-exposure-risk relationship:** establishes none.
- **Nutrition overlap / dependencies / double counting:** separate from
  nutrition; upstream dependency of projection and evaluability.
- **Forbidden interpretations:** resolved means safe or favourable; empty means
  no concern; unresolved means dangerous.
- **Validation needs / decisions:** unchanged upstream golden cases plus
  downstream no-penalty tests under `PSC-OD-005`, `PSC-OD-016` and
  `PSC-OD-019`.

### G.12 Dimension card — coverage

- **Candidate dimension ID / name:** `DIM-SUPPORT-COVERAGE` / coverage.
- **Definition / construct link:** extent or completeness of available and
  usable support relative to the applicable required-input perimeter; it is not
  favourability, a raw field count or a confidence statement.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** applicable required-input set for one dimension,
  component or assessment.
- **Source types / evidence inputs:** applicable-input inventory, selection,
  synthesis, mapping, composition and assessment traces.
- **Directionality / monotonicity:** no goodness direction; greater coverage is
  neither greater goodness nor greater confidence and emits no automatic number.
- **Applicability / non-applicability:** only applicable requirements may enter
  a future coverage perimeter; denominator and aggregation rules remain open.
- **Missing-data / confidence / uncertainty:** named missing inputs may explain
  a coverage gap but retain separate identities; confidence and uncertainty are
  not coverage.
- **Regulatory / hazard-exposure-risk relationship:** describes support extent
  for each channel, not regulatory, hazard, exposure or risk outcome.
- **Nutrition overlap / dependencies / double counting:** ingredient and
  nutrition coverage inventories remain separate; coverage depends on
  applicability and may inform, but does not decide, evaluability.
- **Forbidden interpretations:** goodness, confidence, penalty, risk, zero,
  neutral value or automatic numerical output.
- **Validation needs / decisions:** applicable-input, denominator, bias and
  coverage-structure simulations under `PSC-OD-015` and `PSC-OD-019`.

### G.13 Dimension card — missingness

- **Candidate dimension ID / name:** `DIM-SUPPORT-MISSINGNESS` / missingness and
  incomplete-data guardrail.
- **Definition / construct link:** explicit absence, unavailability or
  unusability of data required for the exact applicable question; it is an
  epistemic support condition, not favourability.
- **Score-bearing status / status:** `SUPPORT ONLY`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** one named policy-required input for a dimension,
  component or assessment.
- **Source types / evidence inputs:** required-input definition, attempted-use
  trace, absence or unusability reason, provenance and applicability decision.
- **Directionality / monotonicity:** no goodness direction; missingness cannot
  lower goodness, create a penalty or emit an automatic number.
- **Applicability / non-applicability:** missingness exists only for an
  applicable required input; genuine non-applicability is not missingness.
- **Missing-data / confidence / uncertainty:** this card records the missing
  input and incomplete-data guardrail; coverage may record its scoped effect,
  while confidence and uncertainty remain separate conclusions.
- **Regulatory / hazard-exposure-risk relationship:** absence in any channel is
  not that channel's adverse outcome and establishes no regulatory, hazard,
  exposure or risk state.
- **Nutrition overlap / dependencies / double counting:** missingness remains
  domain- and requirement-specific; the same absent fact must not create
  separate ingredient and nutrition penalties.
- **Forbidden interpretations:** low goodness, adverse evidence, confidence,
  risk, penalty, zero, neutral value, imputation or automatic numerical output.
- **Validation needs / decisions:** indispensability, missing-data bias,
  non-applicability and guardrail cases under `PSC-OD-016` and `PSC-OD-019`.

### G.14 Dimension card — criticality

- **Candidate dimension ID / name:** `DIM-CAND-CRITICALITY` / criticality and
  flag effect.
- **Definition / construct link:** candidate classification of a fully traced
  concern for separate effect review; it does not itself measure goodness.
- **Score-bearing status / status:** `CRITICALITY CANDIDATE`;
  `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** exact concern, endpoint, ingredient/product context and
  candidate rule.
- **Source types / evidence inputs:** scientific conclusion, regulatory context
  where relevant, applicability and rule provenance.
- **Directionality / monotonicity:** not approved; effect classes are governed
  separately.
- **Applicability / non-applicability:** exact critical rule scope must match;
  informational flags otherwise remain non-score-bearing.
- **Missing-data / confidence / uncertainty:** cannot be created from missing or
  uncertain data; all limitations remain explicit.
- **Regulatory / hazard-exposure-risk relationship:** hazard alone is
  insufficient; risk requires exposure; regulatory status is not a proxy.
- **Nutrition overlap / dependencies / double counting:** may overlap hazard,
  risk, regulatory and overall rules; highest no-double-counting priority.
- **Forbidden interpretations:** automatic penalty, cap, floor, override or
  disqualifier.
- **Validation needs / decisions:** false-positive, severity, critical cases and
  communication under `PSC-OD-013`, `PSC-OD-014`, `PSC-OD-019` and
  `PSC-OD-020`.

### G.15 Dimension card — ingredient nutritional property

- **Candidate dimension ID / name:** `DIM-EXCL-NUTRITION-PROPERTY` / ingredient
  nutritional property.
- **Definition / construct link:** nutrient or nutritional characteristic that
  belongs to the nutrition-quality question unless a reviewed boundary proves
  a distinct ingredient construct.
- **Score-bearing status / status:** `EXCLUDED`; `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** nutrient, nutritional component or product nutritional
  profile.
- **Source types / evidence inputs:** nutrition declarations and future
  nutrient-profile sources, not ingredient hazard evidence.
- **Directionality / monotonicity:** owned by future nutrition policy and not
  imported here.
- **Applicability / non-applicability:** excluded from ingredient scoring while
  overlap remains unresolved.
- **Missing-data / confidence / uncertainty:** governed in the nutrition domain;
  no ingredient fallback.
- **Regulatory / hazard-exposure-risk relationship:** separate from all four.
- **Nutrition overlap / dependencies / double counting:** direct overlap risk;
  automatic duplication is prohibited.
- **Forbidden interpretations:** nutritional property as an ingredient bonus or
  penalty in addition to nutrition scoring.
- **Validation needs / decisions:** cross-domain construct and ablation review
  under `PSC-OD-007` through `PSC-OD-012` and `PSC-OD-019`.

### G.16 Dimension card — ontology/category label

- **Candidate dimension ID / name:** `DIM-INFO-ONTOLOGY-LABEL` /
  ontology/category label.
- **Definition / construct link:** multi-label, context-scoped role assertion
  governed under `PSC-OD-003` and `PSC-OD-004`; not goodness.
- **Score-bearing status / status:** `INFORMATIONAL ONLY`;
  `CANDIDATE — NOT APPROVED`.
- **Subject / domains:** ingredient, substance, component, agent or product/use
  context.
- **Source types / evidence inputs:** governed ontology assertion and source
  applicability trace.
- **Directionality / monotonicity:** none; labels do not establish direction.
- **Applicability / non-applicability:** contextual precedence answers one
  bounded question and preserves all secondary assertions.
- **Missing-data / confidence / uncertainty:** unknown and ambiguous labels are
  explicit, never adverse defaults.
- **Regulatory / hazard-exposure-risk relationship:** a category is not
  authorization, hazard, exposure or risk.
- **Nutrition overlap / dependencies / double counting:** `added_nutrient` and
  related labels may inform a nutrition question but cannot score in both
  domains automatically.
- **Forbidden interpretations:** additive means adverse, natural means safe,
  allergen means general-population penalty, or category means score.
- **Validation needs / decisions:** multi-label, contextual-precedence and proxy
  leakage cases under `PSC-OD-005`, `PSC-OD-013` and `PSC-OD-019`.

## H. Governed direction and applicability card template

Every future dimension proposal must complete this template before scientific
review. Blank, `UNRESOLVED` and rejected fields remain visible.

| Field | Required content | Current constraint |
|---|---|---|
| Direction hypothesis | Exact candidate direction for the defined subject and construct. | Candidate only; no direction is inferred from a name. |
| Scientific rationale required | Why the direction represents ingredient favourability. | Must cite governed evidence and identify normative judgment. |
| Evidence basis | Source IDs, artifacts, syntheses and reference cases. | Source prestige and record count are insufficient. |
| Applicable subject/domain | Entity type, question, domain, population and context. | No silent transfer. |
| Contextual modifiers | Form, route, use, population, product and other material context. | Modifiers remain typed; no parameters here. |
| Monotonicity domain | Conditions within which direction is hypothesized. | No universal monotonicity claim. |
| Known exceptions | Cases where the hypothesis may fail or not apply. | Exceptions cannot be hidden in prose after validation. |
| Non-monotonicity risk | Scientific reasons for reversals or contextual behavior. | Must be tested, not forced into an order. |
| Transform family | Candidate class only. | No function, value, weight, threshold or parameter. |
| Endpoint interpretation | Bounded meaning and non-claims. | Not safety, risk probability or intrinsic fact. |
| Missingness behavior | Named missing inputs and candidate blocking role. | No zero, midpoint, imputation or penalty. |
| Uncertainty behavior | Propagation and qualification. | No automatic decrement. |
| Confidence behavior | Conclusion-specific statement. | No goodness proxy or multiplier. |
| Criticality interaction | Candidate relationship to flags and effects. | No cap, floor or override without separate approval. |
| Dependence/correlation | Causal, hierarchical, overlapping or unresolved links. | Independence requires support. |
| Double-counting checks | Shared evidence, proxy and paired-perturbation tests. | Failures block approval. |
| Reference-judgment requirements | Reviewer roles, case strata, dissent and trace. | Judgments are absent today. |
| Falsification cases | Cases that would reject the direction or boundary. | Must be predeclared. |
| Validation-owner checks | Construct, robustness, stability, reproducibility and comprehension. | Independent sign-off required. |
| Approval fields | Scientific panel, validation owner, decision and publication state. | All currently not approved. |
| Canonical identity and version | Stable card key, semantic version, digest, cutoff and supersession. | Required before any exact candidate can be tested. |

## I. Ingredient, nutrition and overall separation

The Contract's tri-score has three distinct future outputs:

| Domain | Subject | This RFC permits | This RFC forbids |
|---|---|---|---|
| Ingredient-level goodness | Declared ingredient composition and applicable ingredient evidence under future WYE criteria. | Candidate states, dimension boundaries and support traces. | Nutrition duplication, product aggregation, clinical safety or risk claims. |
| Nutrition quality | Declared nutritional profile under a future applicable nutrient method. | Explicit cross-domain exclusion records. | Selecting a nutrient model or importing nutrient direction into ingredient scoring. |
| Overall product score | Future synthesis of approved ingredient and nutrition components. | Identification of dependency and overlap risks only. | Deciding `PSC-OD-006`, ordinary aggregation, compensation, caps or overrides. |

Potential overlaps are governed as follows:

| Possible overlap | Risk | Required resolver | Interim control |
|---|---|---|---|
| Added nutrient or fortified-substance label | The same nutritional fact may affect both domains. | Nutrition-science panel, ingredient scientific panel and validation owner. | Informational in ingredient policy; no double counting. |
| Ingredient source associated with nutrient content | Source identity may be mistaken for product nutritional quantity. | Nutrition reviewer and data steward. | Require product-basis data; do not infer quantity from identity. |
| Exposure or consumption context | Scenario variables may resemble nutrition basis variables. | Scientific panels and validation owner. | Preserve distinct question and canonical identity. |
| Biological endpoint related to nutrient adequacy or excess | Construct could be classified as hazard or nutrition. | Multidisciplinary scientific review. | `UNRESOLVED`; exclude from both score-bearing sets until assigned. |
| Regulatory nutrition category | Regulatory status could proxy nutritional favourability. | Regulatory and nutrition reviewers. | Informational only; no direction. |

Until an overlap policy is approved, the same proposition, evidence line or
derived fact cannot affect both ingredient and nutrition components. Overall
aggregation remains outside this RFC, and `PSC-OD-006` remains waiting.

## J. Candidate dependency and double-counting register

| Dimension A | Dimension B | Candidate relationship | Source of relationship | Double-counting risk | Proposed control | Scientific review | Validation test | Status |
|---|---|---|---|---|---|---|---|---|
| Hazard | Risk | Causal dependency | Contract and product-assessment boundary | High | Risk cannot be counted as independent of its hazard basis. | Required | Paired hazard/exposure/risk cases and ablation. | `CANDIDATE — NOT APPROVED` |
| Exposure | Risk | Causal dependency | Product-assessment risk-computability gate | High | Preserve shared input identities and do not score both as independent effects. | Required | Change exposure context while holding hazard fixed. | `CANDIDATE — NOT APPROVED` |
| Hazard | Criticality | Overlapping evidence and proxy risk | Contract criticality boundary | High | Separate hazard flag from effect classification; require explicit no-double-counting rule. | Required | Hazard-only versus qualified critical case. | `CANDIDATE — NOT APPROVED` |
| Regulatory status | Ingredient scientific state | Proxy risk | Ontology and Contract separations | High | No automatic conversion or direction. | Required | Authorized/not-authorized paired cases with identical science. | `CANDIDATE — NOT APPROVED` |
| Evidence state | Confidence | Overlapping evidence and hierarchical relationship | Evidence-synthesis confidence semantics | High | Retain distinct canonical conclusions and contributing factors. | Required | Same evidence state with different applicability limitations. | `CANDIDATE — NOT APPROVED` |
| Confidence | Uncertainty | Overlapping but non-inverse relationship | Evidence-synthesis and Contract semantics | High | No arithmetic inversion or shared score effect. | Required | High confidence in a qualified conclusion with material uncertainty. | `CANDIDATE — NOT APPROVED` |
| Coverage | Missingness | Hierarchical relationship | Contract coverage and incomplete-data boundary | Medium | Keep separately versioned support cards: named missing items may explain a coverage gap but neither becomes goodness, confidence or penalty. | Required | Same outcome with different applicable coverage and missing-input patterns. | `CANDIDATE — NOT APPROVED` |
| Applicability | Evaluability | Hierarchical relationship | Evidence selection and Contract | High | Dimension applicability precedes policy-level evaluability; neither proxies the other. | Required | Non-applicable optional versus unresolved indispensable dimension. | `CANDIDATE — NOT APPROVED` |
| Mapping resolution | Ingredient scientific state | Causal dependency and proxy risk | Mapping freeze and projection contract | High | Resolution can enable or block projection but cannot create scientific direction. | Required | Resolved, partial, empty and unavailable mapping cases. | `CANDIDATE — NOT APPROVED` |
| Ingredient scientific favourability | Nutrition quality | Unresolved overlap | `PSC-OD-002` tri-score construct | High | Maintain separate card sets and proposition identities. | Required | Cross-domain ablation and duplicate-proposition detection. | `CANDIDATE — NOT APPROVED` |
| Ontology label | Regulatory status | Hierarchical or overlapping context | Regulatory Ontology RFC | High | Preserve assertion kind; category is not authorization. | Required | Same category with different scoped authorization. | `CANDIDATE — NOT APPROVED` |
| Evidence state | Ingredient scientific favourability | Unresolved | Mapping RFC and synthesis boundary | High | Require a reviewed conclusion-to-dimension rule; evidence availability alone has no direction. | Required | Same evidence volume with opposite or absent conclusion. | `CANDIDATE — NOT APPROVED` |

No pair is declared independent. Independence may be recorded only after a
scientific basis and validation test support it for the exact version and
domain.

## K. Conceptual scenarios and test-vector design

The scenarios describe expected semantic behavior only. They contain no score,
mapping value or approved gate.

| Scenario | Input level | Candidate state | Applicable dimensions | Number allowed | Forbidden inference | Required gate |
|---|---|---|---|---|---|---|
| Resolved mapping and sufficient reviewed evidence | Mapping, synthesis and projection | Scientific state candidate may be reviewable | Scientific candidate plus all support dimensions | `UNRESOLVED` | Resolved and sufficient automatically means favourable or computable. | Approved dimension, direction, reference judgments and validation. |
| Partially resolved mapping | Mapping resolution | `partially_resolved`; downstream state unresolved for missing members | Mapping resolution, applicability, coverage and evaluability | `NO` when completeness is indispensable; otherwise `UNRESOLVED` | Partial mapping is a penalty or worst case. | `PSC-OD-016` indispensability review. |
| Mapping history unavailable | Mapping resolution | `history_unavailable` | Mapping resolution and evaluability | `NO` for conclusions needing complete reconstruction | Unavailable history means danger or empty mapping. | Historical reconstruction or approved non-indispensability. |
| No relevant selected evidence | Evidence synthesis | `no_selected_evidence`; possible `insufficient_data` | Evidence state, missingness and evaluability | `NO` for unsupported conclusion | No selected evidence means no concern or adverse outcome. | Sufficiency and evaluability policy. |
| Materially conflicting evidence | Evidence synthesis | `conflicting_evidence` | Evidence state, uncertainty, confidence and evaluability | `NO` for blocked conclusion; otherwise `UNRESOLVED` | Average, vote, prestige tie-break or danger. | Scientific conflict review and validation case. |
| Low-confidence conclusion | Confidence support | Contract confidence label remains support-only | Confidence, uncertainty and exact conclusion | `UNRESOLVED` | Low confidence means low goodness or non-computable. | `PSC-OD-017` and dimension policy. |
| Elevated uncertainty | Uncertainty support | `evidence_uncertain` may apply | Uncertainty, confidence and evaluability | `UNRESOLVED` | Uncertainty is a penalty or adverse evidence. | Reviewed materiality and `PSC-OD-017`. |
| Dimension not applicable | Applicability | `not_applicable` for the dimension | Applicability and evaluability | `UNRESOLVED` | Non-applicable is favourable, adverse or zero. | Approved denominator and indispensability rule. |
| Regulatory label with no goodness direction | Ontology/regulatory | Scoped regulatory or category fact | Regulatory status and ontology label | `NO` from that fact alone | Authorization or category implies goodness. | Explicit scientific direction and proxy review. |
| Hazard with no exposure information | Synthesis/projection/product context | `exposure_dependent`; `risk_not_computable` at the `risk-computability gate` | Hazard, exposure readiness, risk and evaluability | `NO` for risk characterization or a numerical ingredient conclusion | `risk_not_computable` means negative goodness, zero, an ingredient score state or authorization for a risk score. | Compatible exposure and reviewed risk protocol. |
| Critical flag candidate | Criticality | `critical_concern` candidate | Hazard or risk context plus criticality | `NO` from the flag alone | Automatic cap, floor, override or disqualifier. | `PSC-OD-013` and, if relevant, `PSC-OD-014`. |
| Multiple contextual labels | Ontology | Coexisting/contextually preferred/ambiguous as appropriate | Ontology label and applicability | `NO` from labels alone | First label or preferred label is universal primary truth. | `PSC-OD-004`-consistent contextual review. |
| Possible double counting | Dimension dependency | Relationship `unresolved` | Both candidate dimensions and shared provenance | `NO` until controlled | Two labels imply independent evidence. | Dependency review and paired perturbation test. |
| Possible nutrition overlap | Cross-domain construct | `UNRESOLVED`; nutritional property excluded here | Ingredient candidate and nutrition boundary | `NO` in ingredient mapping pending resolution | Nutritional fact may be rewarded or penalized in both domains. | Multidisciplinary construct and ablation review. |
| Non-computable ingredient conclusion | Evaluability | `not_computable` | Evaluability, missingness, coverage and reasons | `NO` | Non-computable means zero, neutral, technical failure or adverse. | Approved `PSC-OD-016` rule and trace. |
| Hypothetical computed zero distinct from non-computable | Future output boundary | A computable endpoint state would be required; no such state is approved here | Future score output and evaluability | `UNRESOLVED` in this RFC | Zero can stand in for missing, unresolved or unavailable. | Approved mapping, endpoint, evaluability and validation. |

Every future test vector must freeze source cutoff, subject, question, mapping
state, evidence/synthesis identities, context, policy/card versions, expected
non-numeric state, forbidden inference and reviewer authority. A numerical
expected result is outside this RFC.

`risk_not_computable` belongs only to the product-assessment
`risk-computability gate`. It is distinct from the Product Scoring Contract's
`not_computable` evaluability state. It is not negative goodness, emits no zero,
is not an ingredient scientific or score state, and authorizes no risk score.

## L. Governance, versioning and validation gates

### L.1 Lifecycle and authority

| Role | May do | May not do through this draft |
|---|---|---|
| Protocol proposer, including Codex/ChatGPT | Draft alternatives, cards, gaps, scenarios and falsification questions. | Impersonate reviewers, approve a dimension, validate a state or authorize runtime. |
| Product owner | Confirm product semantics, transparency needs and intended-use boundaries; maintain Option B as candidate direction. | Confer scientific validity, validation sign-off or numerical authority. |
| Scientific review panel / internal methodology review function | Review construct, states, dimensions, direction, applicability and interactions for the MVP assurance package. | Claim external independence, certification or scientific approval; bypass downstream decisions. |
| Validation owner / internal validation function | Define golden, adversarial, regression, sensitivity and comprehension tests and accept or reject internal evidence that the exact candidate meets its bounded claims. | Claim independent external validation; invent missing rationale or approve a different undocumented candidate. |
| Future external scientific panel / independent validator | Optionally review a frozen candidate in a future Level 2 assurance process. | Block the informational MVP solely because Level 2 is absent; be simulated by Codex/ChatGPT or an internal role. |
| Regulatory reviewer | Review source competence, status scope and regulatory interpretation. | Turn regulatory status into goodness or scientific validity. |
| Data/model steward | Govern canonical identity and serialization, the future numeric execution profile, deterministic arithmetic, rounding and representation rules, digests, versioning, replay and technical change-impact analysis under `PSC-OD-018` and `PSC-OD-021`. | Confer scientific or validation-owner approval; choose the construct or scientific direction; approve reference judgments; close `PSC-OD-005`; or authorize publication or release alone. |
| Release approver | Consider publication only after all required gates pass and the other accountable authorities have completed their work. | Treat draft completion, technical approval or product preference as release approval. |

### L.2 Canonical identity and change control

A future candidate policy set must have a stable policy key, semantic version,
canonical serialization rule, content digest, source cutoff, parent identities,
dimension-card versions, state-vocabulary version, dependency-register version
and supersession relation. Any semantic change creates a new immutable version
and an impact analysis. Published versions are immutable; correction or update
occurs by supersession without rewriting historical results.

Provenance must connect source artifacts, mapping manifests, selection and
synthesis artifacts, projections, product context, reviewer judgments,
dimension cards, policy decision and validation package. Localized or AI prose
is not canonical scientific input.

### L.3 Prerequisites and gates

Internal methodology review requires complete card definitions, source-use
dispositions, explicit direction hypotheses, applicability cases, dependency
annotations, reference-judgment protocol and documented source gaps.

Internal validation requires an exact frozen candidate, a governed corpus with
an internally separated hold-out where applicable, predeclared falsification
cases, monotonicity and exception tests, double-counting tests, sensitivity and
stability analysis, historical replay and comprehension review. Technical
reproducibility alone is insufficient.

Informational MVP publication requires completion of the Internal Informational
Assurance package, internal methodology and validation dispositions,
data/model-steward verification, product-owner acceptance, resolution of
blocking open decisions, source-governance acceptance, versioned canonical
identity, impact report and separate release approval. Independent external
validation is future and optional for the MVP and is not currently present.
Implementation requires publication plus a separate technical authorization.
This draft satisfies none of those gates.

## M. Open decisions and unresolved questions

| Existing decision | Question retained as open by this RFC |
|---|---|
| `PSC-OD-005` | Definitive state and dimension boundaries; scientific direction; transform family; mapping and comparability. |
| `PSC-OD-013` | Flag effects, criticality classes, critical caps and no-double-counting. |
| `PSC-OD-014` | Closed zero-override rules and reproducible interpretation. |
| `PSC-OD-015` | Required-input sets, coverage representation and any coverage aggregation. |
| `PSC-OD-016` | Evaluability, indispensability, missingness and exact `not_computable` conditions. |
| `PSC-OD-017` | Confidence dimensions, derivation and interaction with evaluability. |
| `PSC-OD-018` | Numerical execution, intermediate arithmetic, precision, rounding and canonical serialization. |
| `PSC-OD-019` | Reference judgments, golden corpus, calibration/validation separation, robustness and comprehension. |
| `PSC-OD-020` | User-facing interpretation, limitations, language, bands and visual presentation. |

Compensability, interaction, direction, non-monotonic exceptions, overlap with
nutrition, criticality effects and numerical execution remain unresolved. This
document changes no decision status.

## N. Sources and provenance

Only source IDs already present in the governed `PSC-OD-021` source-governance
artifact are used below. External source references proposed only in the parent
Mapping RFC are not promoted by this document.

| Source ID | Principle transferred | Transferability limit | Linked WYE decision |
|---|---|---|---|
| `SRC-EFSA-EVIDENCE-2015` | Evidence use should be planned, conducted, verified, documented and reported as distinct stages. | Does not define WYE ingredient states, direction or scoring. | `PSC-OD-005`, `PSC-OD-019`, `PSC-OD-021`. |
| `SRC-EFSA-UNCERTAINTY-2018` | Identified uncertainty and its effect on conclusions should remain explicit. | Does not prescribe a goodness dimension, penalty or missing-data policy. | `PSC-OD-005`, `PSC-OD-017`, `PSC-OD-021`. |
| `SRC-CODEX-RISK-2007` | Risk assessment, management and communication remain distinct; hazard and exposure cannot be silently collapsed. | Government food-safety framework, not a WYE goodness or clinical scoring authority. | `PSC-OD-005`, `PSC-OD-013`, `PSC-OD-020`, `PSC-OD-021`. |
| `SRC-W3C-PROV-O-2013` | Entities, activities, agents, derivation and attribution can remain distinguishable in provenance. | General provenance model; no scientific truth, schema adoption or score authority. | `PSC-OD-005`, `PSC-OD-019`, `PSC-OD-021`. |
| `SRC-FAIR-2016` | Persistent identity, rich metadata, qualified references and detailed provenance support reuse and audit. | FAIRness does not establish scientific quality, applicability or correctness. | `PSC-OD-005`, `PSC-OD-019`, `PSC-OD-021`. |

### N.1 Internal canonical sources

The primary internal basis is the Product Scoring Contract, the parent
Ingredient Score Mapping RFC, the decided Goodness Construct, Regulatory
Ontology, Category Coexistence and Precedence and Source Governance RFCs, the
mapping execution input freeze, and the evidence selection, synthesis,
ingredient projection and product assessment contracts. These documents govern
semantic boundaries; they do not scientifically approve this policy.

### N.2 Typed gap register

| Gap type | Description | Why unresolved | Required artifact | Decision | Required authority | Blocks drafting | Blocks decision closure | Blocks validation | Blocks runtime | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `SOURCE GAP` | Ingredient-level construct | No governed external source establishes a validated construct directly equivalent to WYE ingredient scientific favourability. | Reviewed construct evidence package with exact transferability limits, or an explicit documented absence of an external equivalent. | `PSC-OD-005` | Scientific review panel | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `POLICY GAP` | Dimension boundaries | No approved policy defines the exact inclusions, exclusions and cross-domain boundaries of candidate dimensions. | Versioned scientific dimension-card set and boundary rationale. | `PSC-OD-005` | Scientific review panel + validation owner | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `POLICY GAP` | Directionality | No dimension has an approved scientific direction or exception domain. | Reviewed direction and applicability cards with falsification cases. | `PSC-OD-005` | Scientific review panel | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `VALIDATION-ARTIFACT GAP` | Correlation and independence | No governed study establishes correlation structure or independence among candidate dimensions. | Dependency, correlation and paired-perturbation analysis on the governed corpus. | `PSC-OD-019` | Validation owner + scientific review panel | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `POLICY GAP` | Compensability | No approved rule determines whether one candidate dimension may compensate for another. | Reviewed compensability policy and adversarial cases. | `PSC-OD-005`, `PSC-OD-013` | Scientific review panel + validation owner | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `POLICY GAP` | Interaction | No approved rule defines cross-dimension or criticality interactions. | Versioned interaction and no-double-counting policy. | `PSC-OD-005`, `PSC-OD-013` | Scientific review panel + validation owner | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `VALIDATION-ARTIFACT GAP` | Extreme cases | Legitimate endpoint, near-boundary and adversarial cases have not been governed or executed. | Independently reviewed extreme-case corpus and expected non-misleading outcomes. | `PSC-OD-019` | Validation owner + external scientific reviewers | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `REFERENCE-JUDGMENT GAP` | Reference judgments | No governed ingredient-state or ordering judgments are present. | Versioned elicitation protocol, reviewer records, dissent trace and frozen judgments. | `PSC-OD-005`, `PSC-OD-019` | Scientific review panel + validation owner | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `VALIDATION-ARTIFACT GAP` | Calibration corpus | No representative governed calibration corpus exists. | Frozen calibration corpus with provenance, strata and digest. | `PSC-OD-005`, `PSC-OD-019` | Scientific review panel + validation owner | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `VALIDATION-ARTIFACT GAP` | Validation corpus | No independent representative hold-out corpus exists. | Independently governed validation corpus with provenance and digest. | `PSC-OD-019` | Validation owner + external scientific reviewers | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `VALIDATION-ARTIFACT GAP` | External independent validation | No exact candidate has external independent validation, and none is claimed. | Optional future external validation report for one frozen candidate if Level 2 is activated. | `PSC-OD-005`, `PSC-OD-019` | Future qualified external panel / independent validator | `NO` | `NO` | `NO` for MVP; `YES` only for a Level 2 claim | `NO` for informational MVP | `FUTURE / OPTIONAL / NOT PRESENT` |
| `POLICY GAP` | Exact candidate | No frozen mapping candidate defines the complete state, dimension, applicability and transformation package. | Canonically identified candidate with version, digest and complete cards; formulas remain outside this RFC. | `PSC-OD-005` | Scientific review panel + validation owner | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `VALIDATION-ARTIFACT GAP` | Sensitivity analysis | No governed analysis tests plausible methodological choices, dependencies and missingness behavior. | Predeclared sensitivity analysis and reproducible results package. | `PSC-OD-019` | Validation owner | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |
| `VALIDATION-ARTIFACT GAP` | Impact report | No version-impact report evaluates ordering, endpoint interpretation, history and user comprehension. | Candidate-versus-baseline impact report with trace and review dispositions. | `PSC-OD-018`, `PSC-OD-019`, `PSC-OD-020` | Data/model steward + validation owner + communication reviewer | `NO` | `YES` | `YES` | `YES` | `OPEN — NOT RESOLVED` |

These gaps are not adverse evidence, penalties or score inputs. They do not
block reversible drafting. Every Internal Informational Assurance gap blocks
the applicable internal decision, validation or runtime gate until its named
artifact and authority requirements are satisfied. The external-independent-
validation gap alone is future and non-blocking for the informational MVP. No
network research, invented source or AI inference is used to fill any gap.

## O. Decision-state and exit check

The canonical Product Scoring Contract matrix contains all existing decisions
from `PSC-OD-001` through `PSC-OD-022`: five remain `DECIDED` and seventeen
remain `OPEN`. Specifically, `PSC-OD-005` remains `OPEN`. This RFC adds no
decision identifier and changes no matrix entry.

The draft is ready for policy review only if its mechanical validation confirms
that it is the sole working-tree change, remains untracked and unstaged, contains
no approved numerical method or runtime authority, preserves the parent and
Contract artifacts, and passes structural and encoding checks.

## P. Candidate exit state

```text
document_status: DRAFT — SCIENTIFIC/PRODUCT DECISION REQUIRED
decision_status: PSC-OD-005 OPEN
option_b_status: CANDIDATE DESIGN DIRECTION ONLY
policy_option_c_status: PRODUCT-OWNER CANDIDATE DIRECTION — NOT SCIENTIFICALLY OR INDEPENDENTLY VALIDATED
scientific_approval: NOT CLAIMED
validation_owner_approval: NOT PRESENT
implementation_authorization: NOT PRESENT
runtime_authority: NONE
publication_release: NOT APPROVED
psc_od_006: NOT STARTED
internal_assurance_governance: ADOPTED
internal_assurance_package: NOT COMPLETE
external_validation: FUTURE / OPTIONAL / NOT PRESENT
```
