# WYE — Scientific Scoring Protocol Contract

## Purpose

This document defines the deterministic contract every future WYE scientific
assessment protocol must satisfy. It defines no formula, source weight, threshold,
score band or database schema.

The first protocol is limited to endpoint-specific evidence synthesis and a
multidimensional substance hazard profile. Product risk remains unavailable until
exposure inputs and a separately validated protocol exist.

## Protocol declaration

Every protocol version MUST publish an immutable declaration containing:

- stable protocol key and immutable version;
- lifecycle status and intended predecessor/successor, if any;
- scientific question and construct being assessed;
- domain and intended use;
- permitted and forbidden claims;
- target population/species;
- endpoint or controlled endpoint set;
- route;
- duration and scenario;
- substance form or identity scope where relevant;
- evidence cutoff and as-of semantics;
- eligible source dataset releases and release-selection rationale;
- eligible ingestion-run criteria, including parser/normalisation constraints;
- eligible assessment statuses;
- inclusion and exclusion criteria;
- evidence-line dependency and duplicate policy;
- supersession/correction policy;
- current versus historical policy;
- minimum completeness requirements;
- quality, relevance, consistency and uncertainty method;
- conflict-resolution boundaries;
- allowed partial outputs and blocking statuses;
- aggregation and projection rules;
- explanation and user-communication contract;
- canonical ordering, serialisation, precision and rounding policy, even when the
  protocol has no numeric result;
- engine/build compatibility contract;
- canonical digest of the complete rule artifact;
- scientific review, validation and publication approvals.

Omitted dimensions MUST be explicitly marked `not_applicable` with rationale;
they cannot be silently wildcarded.

## Evidence snapshot

An evidence snapshot is the immutable, content-addressed input universe from
which eligibility decisions are made. It is not merely “the current database”.

It MUST freeze or canonically reference:

- cutoff and as-of date/time;
- source, dataset and release identities;
- selected immutable artifacts and checksums;
- successful ingestion runs and all semantic versions/config digests;
- assessments and findings with content fingerprints;
- source-native identity and dependency information;
- substance identifiers and status;
- historical ingredient–substance mapping state when projection is requested;
- historical product–ingredient state when product assessment is requested;
- explicit snapshot canonicalisation version and digest.

Database surrogate IDs alone are not a portable content identity. They MAY be
recorded for traversal but MUST be accompanied by stable identities/digests.

Snapshot construction MUST NOT fetch remote data, invoke AI or choose a newer
release implicitly during an execution.

## Evidence eligibility and selection

Selection is a deterministic classification of every candidate evidence line in
the snapshot against one protocol version. It MUST retain a decision for included
and excluded candidates.

Phase 7.2 specializes this contract in `WYE_EVIDENCE_SELECTION.md`, including
the finding-level default selection unit, assessment context, binary decision
plus deferred resolution state, evidence channels, dependency model, canonical
decision payload and selection digest. That specialization defines no runtime
engine and no synthesis.

### Selection order

The protocol MUST apply a documented canonical sequence equivalent to:

```text
establish identity and provenance
→ establish cutoff/release/run eligibility
→ identify dependencies and duplicates
→ compare endpoint and assessment context
→ compare population/species, sex, route, duration and scenario
→ apply assessment status and supersession/correction policy
→ appraise minimum quality and relevance
→ record include/exclude decision and reason
→ evaluate completeness
```

Changing this sequence when it can change a result is a protocol-version change.

### Current and as-of modes

- **Current mode** applies the protocol's declared current-release and freshness
  policy at execution time, then freezes the resulting snapshot.
- **As-of mode** considers only evidence and mappings available/effective at the
  declared historical boundary.
- A later release does not automatically withdraw an earlier assessment.
- Absence from a later dataset is not supersession or withdrawal.
- Explicit source correction/supersession MAY take precedence when its identity,
  scope and applicability are recorded.
- Historical replay always uses the frozen snapshot/mapping state, never whatever
  is current when replay is requested.

### Assessment status

Each protocol MUST declare allowed source/WYE assessment statuses rather than
assuming all persisted assessments are usable.

- `published` MAY be eligible if all other criteria pass.
- `withdrawn` MUST be excluded from a current scientific conclusion and retained
  in the trace.
- `superseded` MUST be handled according to the explicit succession relation and
  historical mode; it is not silently deleted.
- `rejected` MUST be excluded.
- `pending_review` MUST NOT support a published scientific conclusion unless a
  future protocol explicitly defines a non-public review output that cannot be
  mistaken for an approved conclusion.

### Duplicate and dependency handling

- Byte-identical artifacts, repeated release records and reprocessed parser output
  are not automatically independent evidence.
- Records derived from the same study/assessment MUST be grouped into the same
  dependency-aware evidence line where the lineage establishes dependence.
- Cross-provider copies or summaries MUST NOT be counted as independent without
  evidence of independent underlying data.
- A corrected record may replace an earlier record only under the declared
  correction policy; both remain in provenance.
- If dependency cannot be resolved, the uncertainty and potential double-counting
  impact MUST be reported. The system MUST NOT guess independence.

### Selection reason codes

Reason codes are machine-readable stable concepts. Human text may be localised;
the code and semantic meaning may not change within a published version.

The table below is the frozen Phase 7.0.1 conceptual vocabulary. Phase 7.2
refines it into versioned core and protocol-specific namespaces and records the
explicit compatibility mapping in `WYE_EVIDENCE_SELECTION.md`. No published
protocol or historical execution used the conceptual aliases.

| Code | Decision meaning |
|---|---|
| `included` | Candidate satisfies all declared eligibility criteria |
| `included_partial_context` | Protocol permits inclusion with an explicit, non-blocking context limitation |
| `excluded_unresolved_identity` | Substance or record identity cannot be established |
| `excluded_insufficient_provenance` | Origin/transformation cannot support auditable use |
| `excluded_wrong_domain` | Evidence addresses a different assessment domain |
| `excluded_wrong_endpoint` | Endpoint does not answer the protocol question |
| `excluded_wrong_population` | Population/species is outside permitted relevance/applicability |
| `excluded_wrong_sex_context` | Sex-specific context is incompatible where material |
| `excluded_wrong_route` | Route is incompatible |
| `excluded_wrong_duration` | Duration is incompatible |
| `excluded_wrong_scenario` | Dose/use/assessment scenario is incompatible |
| `excluded_outside_cutoff` | Evidence was not available within the frozen cutoff |
| `excluded_ineligible_release` | Dataset release is not selected by the protocol |
| `excluded_ineligible_run` | Ingestion/parser/normalisation run fails protocol eligibility |
| `excluded_pending_review` | Assessment is not approved for the requested output |
| `excluded_withdrawn` | Source assessment is explicitly withdrawn |
| `excluded_superseded` | An applicable explicit successor controls current-mode use |
| `excluded_rejected` | Persisted assessment is rejected |
| `excluded_duplicate` | Same source-native record/content is duplicated |
| `excluded_dependent_evidence` | Record is represented through its parent evidence line and cannot add independent support |
| `excluded_quality_not_assessable` | Required quality appraisal cannot be performed |
| `excluded_below_quality_requirement` | Evidence fails a protocol-specific approved quality criterion |
| `excluded_not_relevant` | Evidence cannot contribute to the exact question |
| `excluded_not_applicable` | Evidence may be relevant generally but cannot transfer to the target context |
| `excluded_other_protocol_rule` | Only allowed with an additional protocol-versioned sub-code and rationale |

An implementation MAY refine codes with versioned subcodes. It MUST NOT collapse
materially different exclusions into `other` for convenience.

## Minimum completeness

Completeness is question-specific and MUST be declared before selection. It MUST
not be inferred from record count.

The declaration specifies:

- mandatory identity/provenance fields;
- required context dimensions;
- required evidence-line or quality characteristics, without arbitrary default
  quantities;
- endpoint coverage needed for a complete conclusion;
- which missing dimensions allow a partial conclusion;
- which semantic status is returned for every failure path.

Failure to meet completeness produces a status from the Missing Evidence Policy.
It never produces a fallback value or numeric penalty.

## Conflict policy

Two conclusions are candidate conflicts only when they address the same
well-formed scientific question and make incompatible contributions to its
answer.

Before declaring conflict, the evaluator MUST compare:

- endpoint and endpoint definition;
- dose/value and substance form;
- species/population;
- sex where relevant;
- route;
- duration;
- study design and evidence type;
- assessment context and intended purpose;
- release/version and time;
- explicit supersession or correction;
- evidence quality;
- relevance and applicability;
- known dependency between evidence lines.

### Conflict states

| State | Definition | Required handling |
|---|---|---|
| `apparent_conflict` | Surface conclusions differ, but comparability has not yet been established | Preserve both; do not average or conclude conflict |
| `resolved_contextual_difference` | Difference is explained by endpoint, dose, population, route, duration, design, context, version or applicability | Keep separate scoped conclusions and record resolution rationale |
| `resolved_supersession_or_correction` | Explicit applicable correction/successor governs current use | Use governing record for current conclusion; preserve predecessor in trace/history |
| `true_unresolved_conflict` | Comparable, eligible evidence lines remain materially incompatible after appraisal | Return `conflicting_evidence` for the affected question and expose uncertainty |

No automatic mean, vote, “most recent wins” rule or provider rank is allowed.

There is no global precedence such as `EFSA > OpenFoodTox`. Protocol-specific
precedence is permissible only for documented:

- supersession/correction;
- regulatory applicability to the exact question/jurisdiction;
- relevance/applicability;
- explicit approved scientific rationale.

Precedence affects a stated question, not the universal quality of a source. Its
application MUST appear in the explanation trace.

Phase 7.3 specializes comparison completion, evidence-line grouping,
consistency, conflict, sufficiency, coverage, uncertainty propagation and the
non-scalar substance profile in `WYE_EVIDENCE_SYNTHESIS.md`. It preserves every
conflict state above and introduces no runtime engine or numeric output.

## Quality, confidence and uncertainty outputs

Protocols MUST implement the separate dimensions defined in
`WYE_SCORING_SEMANTICS.md`. Until a scientifically reviewed rubric exists, the
first protocol may use structured qualitative appraisals and explicit
`not_assessable`; it MUST NOT invent numeric grades.

The Phase 7.3 contract keeps quality, relevance, consistency, coverage,
uncertainty and confidence as separate profiles. Concrete endpoint equivalence,
direction, quality, sufficiency, confidence and hazard-interpretation rules
remain subject to external scientific review.

An uncertainty item has the logical fields:

```text
uncertainty_key
source_or_cause
affected_component
direction_if_known
potential_impact
reducibility
reduction_action_or_data
effect_on_conclusion
rationale
```

Final conclusion confidence is derived only by the published protocol and remains
traceable to its limiting dimensions. It is never an alias for safety.

## Ingredient projection specialization

Phase 7.4 specializes the ingredient-level projection contract in
`WYE_INGREDIENT_PROJECTION.md`. Projection dispatch is governed by the frozen
historical relationship type, validity, identity/form compatibility and
composition readiness. The canonical output is the non-scalar
`ingredient_scientific_projection`, not an ingredient hazard/risk score.

Multiple projected substance profiles remain separate. No `maximum`, average,
sum, worst-substance rule, exposure assumption or product-risk inference is
permitted. Concrete equivalence, cross-form, mixture, residual-presence and
confidence-transfer rules remain subject to external scientific review.

## Product assessment and exposure-readiness specialization

Phase 7.5 specializes the product-level contract in
`WYE_PRODUCT_ASSESSMENT.md`. It freezes product composition and scenario inputs,
separates label serving from actual intake, classifies composition/exposure
readiness and makes `risk_not_computable` a first-class scientific result.

Ingredient order, presence and nutrition totals do not supply concentration or
consumed dose. No silent default scenario, cross-ingredient aggregation,
reference-point comparison, risk inference or product score is permitted.
Concrete exposure models, population/route transfer, reference semantics and
risk characterisation require external scientific/regulatory review.

## Logical versioning and reproducibility model

The following are logical concepts, not approved database tables.

Phase 7.1 specializes these placeholders in
`WYE_SCORING_EXECUTION_MODEL.md`. In particular, the canonical general-purpose
execution name is `scientific_evaluation_execution`; the naming refinement does
not change this frozen semantic contract and does not imply a database table.

### `scoring_protocol`

Stable identity for one intended use, scientific construct and domain. It owns
the lifecycle and protocol family, not mutable rules.

### `scoring_protocol_version`

Immutable published rule artifact. Contains the declaration, canonical digest,
compatibility metadata, review approvals and change log.

### `evidence_snapshot`

Immutable input universe and historical mapping state, with canonical digest and
cutoff/as-of semantics.

### `evidence_selection_decision`

One included/excluded decision per candidate evidence line, including reason
code, protocol rule, rationale and dependency resolution.

### `scoring_execution`

One immutable application of a protocol version to canonical inputs and a frozen
snapshot. The name does not imply that a numeric score exists.

### `scoring_result_component`

One semantic result at endpoint, substance, ingredient or product level,
including status, conclusion, scope and uncertainty references. Different
endpoints remain different components.

### `scoring_explanation_trace`

Ordered, machine-readable graph of inputs, decisions, rules, mappings,
contributions, conflicts, uncertainties and outputs.

## Execution freeze contract

Every future execution MUST freeze:

- protocol key/version and canonical rule digest;
- engine/build version;
- evidence cutoff and as-of date/time;
- canonical input identities/checksums;
- evidence snapshot identity/digest;
- historical product → ingredient and ingredient → substance mappings;
- all included/excluded evidence decisions;
- assumptions and semantic configuration;
- canonical ordering and serialisation version;
- numeric precision and rounding policy, even if marked not applicable;
- complete explanation trace and result-component digest;
- execution start/completion metadata that do not participate in semantic identity.

No network, mutable “latest” lookup, random input, locale-dependent ordering,
wall-clock-dependent rule or AI decision may affect a deterministic execution.

### Replay

```text
same canonical inputs
+ same evidence snapshot
+ same mapping state
+ same scoring protocol version
+ compatible deterministic engine
→ identical semantic result and result digest
```

Timestamps and execution IDs may differ but MUST NOT alter the semantic result.

### Counterfactual

```text
same historical canonical inputs
+ same evidence snapshot
+ same mapping state
+ different protocol version
→ new immutable execution comparing rule impact
```

The comparison MUST identify changed rules and changed result components. It does
not replace the historical execution.

### Refresh

```text
new evidence and/or mapping state and/or cutoff
+ selected protocol version
→ new evidence snapshot and new immutable assessment
```

A refresh is not a replay. The change report MUST separate input/evidence changes
from protocol changes.

No historical execution or result is overwritten by replay, counterfactual or
refresh.

## Explainability contract

Every result MUST be traversable through:

```text
result
→ product component, when applicable
→ ingredient projection
→ substance component
→ assessment
→ finding
→ ingestion run
→ release artifact
→ release
→ dataset
→ source
```

The trace MUST also expose:

- protocol rule and version applied at each decision;
- canonical inputs and historical mapping decisions;
- included evidence and inclusion reason;
- excluded evidence and reason code;
- dependency/duplicate handling;
- apparent, context-resolved and unresolved conflicts;
- quality and relevance appraisals;
- endpoint coverage;
- assumptions;
- uncertainty sources and their effect;
- partial/blocking status transitions;
- aggregation/projection steps;
- final claim scope and forbidden interpretations.

Machine trace and user explanation are separate projections. The machine trace is
authoritative and immutable. User-facing text SHOULD be produced by deterministic
templates for published claims.

AI MAY render an already frozen trace in natural language. AI MUST NOT:

- change trace or result;
- select or exclude evidence;
- appraise quality/relevance autonomously for a published result;
- resolve scientific conflicts;
- invent rationale, uncertainty or missing data;
- widen a claim beyond the protocol.

Any AI-rendered explanation MUST retain links to the authoritative trace and MUST
be labelled as presentation, not scientific source material.

## Conceptual test vectors

These vectors define semantic expectations only. They contain no numeric result.

| Vector | Conceptual input | Eligibility outcome | Expected status | May conclude | Must not conclude |
|---|---|---|---|---|---|
| Coherent substance evidence | Resolved substance; eligible independent lines address the same endpoint/context and agree | Lines included | `sufficient` for that endpoint after required quality review | Scoped endpoint synthesis/hazard conclusion | Universal safety or product risk |
| Substance without evidence | Resolved substance; snapshot has no candidate assessment | Nothing included | `no_eligible_evidence` | No eligible evidence under snapshot/protocol | No hazard or dangerous |
| Identity unresolved | Finding identifier has unresolved candidate/review | Excluded unresolved identity | `unresolved_identity` | Identity review is required | Associate evidence with any candidate substance |
| Withdrawn assessment | Current-mode snapshot contains explicitly withdrawn assessment | Excluded withdrawn; retained in trace | `no_eligible_evidence` or `insufficient_evidence` depending on other lines | Assessment was withdrawn and not used | Its prior conclusion is current |
| Superseded assessment | Explicit applicable predecessor/successor relation | Predecessor excluded in current mode; historical mode preserves it | `sufficient`, `insufficient_evidence` or other status based on successor | Which version governed and why | Newest record always wins absent explicit policy |
| Concordant same endpoint | Comparable eligible lines agree | Included as dependency-aware distinct lines | `sufficient` if completeness met | Concordance for exact question | Evidence count is a score |
| Apparent route conflict | Same substance/endpoint; oral and dermal contexts differ | Both eligible only in their respective scoped questions | `resolved_contextual_difference` | Route-specific conclusions differ | True conflict or averaged conclusion |
| True unresolved conflict | Comparable eligible lines for same question remain incompatible | Both included; neither silently preferred | `conflicting_evidence` | Conflict and uncertainty exist | Mean, vote, safety or danger |
| Ingredient represents substance | Accepted, temporally valid `represents` mapping; matching substance form | Substance hazard component eligible for direct ingredient projection | Substance status propagated with ingredient scope | Ingredient represents assessed substance for this profile | Product exposure/risk |
| Ingredient contains substance, unknown concentration | Accepted `contains`; presence supported; no composition quantity | Evidence link included; concentration-dependent projection blocked | `missing_exposure` for risk; conditional hazard/presence view | Containment/presence if actually established | Dose or quantitative risk |
| Derived-from without presence proof | Accepted `derived_from`; no residual presence data | Derivation link retained; presence-dependent evidence excluded | `insufficient_evidence` or `not_applicable` for requested presence claim | Derivation relationship exists | Source substance is present |
| Product with known hazard, unknown exposure | Valid ingredient projection; no concentration/intake/use scenario | Hazard evidence eligible; exposure path incomplete | Hazard profile component available; `missing_exposure` for risk | Product contains/relates to an ingredient with scoped hazard evidence | Product is unsafe or risk magnitude |
| Ingredient list without concentration | Accepted ingredients with positions only | Presence-level inputs eligible; quantitative exposure inputs unavailable | `missing_exposure` for concentration-dependent assessment | Listed ingredient identities/order | Exact or relative concentration |
| Historical replay | Frozen inputs, snapshot, mapping state and protocol version | Same decisions reproduced | Same semantic statuses and digest | Result is reproducible | Current evidence was considered |
| Counterfactual | Same historical inputs/snapshot/mappings; different protocol version | Decisions recomputed under new rules | New immutable result plus rule-impact diff | Effect of rule change | Historical result is overwritten |
| Refresh with new release | New eligible scientific release and cutoff; protocol unchanged | New snapshot and eligibility decisions | New immutable assessment; status may change | Effect of new evidence/input | This is a replay or prior result is invalidated silently |

## Pre-implementation acceptance gate

No Phase 7 runtime implementation may be published until the target protocol has:

- a complete immutable declaration;
- external scientific review appropriate to the domain;
- approved intended use and claims;
- reviewed eligibility, conflict, missing-evidence and uncertainty methods;
- conceptual vectors extended into frozen implementation fixtures;
- deterministic canonicalisation and digest specification;
- an approved logical data model/ADR;
- an independent validation plan;
- explicit handling for all unavailable states;
- confirmation that no legacy score or field is treated as scientific input.
