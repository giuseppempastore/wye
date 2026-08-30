# WYE — Endpoint-Specific Evidence Synthesis Contract

## Status and scope

This document is the canonical Phase 7.3 specification for endpoint-specific
evidence synthesis and the multidimensional substance hazard profile. It
specializes, but does not replace, the contracts in:

- `WYE_PHASE_7.md`;
- `WYE_SCORING_SEMANTICS.md`;
- `WYE_SCORING_PROTOCOL.md`;
- `WYE_SCORING_EXECUTION_MODEL.md`;
- `WYE_EVIDENCE_SELECTION.md`.

Phase 7.3 defines what a future deterministic synthesis engine must produce from
an immutable selected-evidence set. It does not implement that engine, persistence,
an API, a hazard algorithm, ingredient projection, exposure estimation, product
risk, formulas, weights, thresholds, rankings or a numerical score.

Review baseline:

```text
branch: ingredients_score
HEAD: 4f3c2d13d3171a6f27e46beaf8abe641243e9611
origin/ingredients_score: 4f3c2d13d3171a6f27e46beaf8abe641243e9611
working tree before Phase 7.3: clean
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017_ingredient_mapping_history
```

The canonical documents, migrations through `0018`, ingestion contracts, real
EFSA QPS and OpenFoodTox adapters, assessment/finding persistence and current
local data state were reviewed. The local scientific assessment/finding tables
do not provide representative populated evidence, so provider readiness is
derived from the versioned real-adapter output contracts and their validated
fixtures, not from invented data.

## Non-negotiable boundaries

```text
selected evidence != scientific conclusion
same endpoint value != same scientific meaning
different endpoints must not be averaged
evidence count != evidence strength
source prestige != evidence quality
agreement != proof of safety
conflict != automatic danger
absence of evidence != evidence of danger
hazard != exposure != risk
AI != scientific source of truth
```

Quality, relevance, consistency, coverage, uncertainty and confidence remain
separate dimensions. No deterministic implementation may collapse them unless a
published, externally reviewed future protocol explicitly justifies the
transformation.

## Synthesis boundary and units

```text
selected findings and context-only records
→ dependency-aware evidence lines
→ scientific comparability decisions
→ comparison groups
→ endpoint syntheses
→ multidimensional substance hazard profile
```

| Concept | Definition | Role |
|---|---|---|
| Finding | Normal atomic selected record from Phase 7.2 | Preserves the source-derived proposition and provenance |
| Evidence line | Dependency-aware representation of one scientific proposition in one coherent study/context lineage | Normal synthesis input; prevents record multiplication from becoming false corroboration |
| Comparison group | Canonical set of evidence lines that address the same sufficiently well-formed scientific question | Boundary within which consistency and conflict may be assessed |
| Synthesis unit | One comparison group of selected evidence lines | Normal unit processed into one endpoint synthesis |
| Endpoint synthesis | Multidimensional conclusion state for one endpoint/question scope | Scientific component of the substance profile |

The normal synthesis unit is therefore the evidence line inside a comparison
group, not the individual database finding. A finding may be its own evidence
line, but a record count never substitutes for an independent-line count or a
scientific appraisal.

## Evidence-line model

An evidence line groups selected records that derive from the same underlying
scientific proposition or materially dependent lineage in one endpoint and
context. Its logical contract contains:

- stable `evidence_line_key` and `evidence_line_digest`;
- target and frozen substance/form identity;
- underlying study identity and identity-resolution state;
- parent assessment and source/release/run lineage;
- canonically ordered selected finding references and their selection roles;
- proposition identity and evidence channel;
- endpoint raw label, normalized identity, family and ontology mapping state;
- population/model, sex, route, duration/scenario and study-design context;
- dose/value construct, qualifier, basis, unit and reference-point context;
- dependency group, relationship and resolution provenance;
- line-level quality, relevance and uncertainty observations;
- rules and governed normalization/review artifacts used to construct the line.

Construction rules:

1. A single independent finding normally forms one evidence line.
2. Exact duplicates and equivalent normalized reingestions are represented by
   one line and retain all source representations in provenance.
3. Multiple findings from one study belong to the same line only when they
   express the same proposition under compatible endpoint and context. Different
   endpoints, time points, populations or dose constructs form separate but
   dependency-linked lines.
4. A secondary record citing the same primary study is a derived/dependent line
   or context-only representation; it never creates independent corroboration.
5. A regulatory assessment and the primary studies it summarizes remain linked.
   Their distinct semantic roles are not erased by grouping.
6. Unknown study/dependency identity is preserved as uncertainty. The engine
   must not infer independence from different providers, IDs or equal values.

`record_count`, `evidence_line_count` and `independent_line_count` may be exposed
as descriptive audit facts. None is evidence strength or a score.

## Comparison-group model

Evidence lines may enter the same comparison group only when the protocol can
establish compatibility for the exact scientific question across:

```text
target substance and relevant form
endpoint semantic identity and measurement construct
population/species/model and material sex context
route
duration/scenario
dose/value construct, basis and reference-point meaning
study-design/assessment context
evidence channel and semantic role
current/historical release and correction scope
```

The comparison decision is one of:

| State | Meaning | Synthesis consequence |
|---|---|---|
| `directly_comparable` | All material dimensions match under the same governed vocabulary | May enter direct consistency/conflict appraisal |
| `conditionally_comparable` | A published, externally reviewed equivalence or transfer rule permits comparison with explicit assumptions | May be appraised only in a separately labelled conditional group |
| `contextually_different` | Both lines are meaningful, but a material scientific context differs | Keep in separate groups; difference is not conflict |
| `not_comparable` | Constructs, channels or questions are categorically different | Never combine for consistency/conflict |
| `comparability_unresolved` | Missing ontology/context/review prevents a determination | Preserve lines and uncertainty; do not infer agreement/conflict |

The canonical comparison-group signature contains the normalized values and
vocabulary versions for every material dimension, the question-context digest,
and any approved equivalence rule. Provider name is provenance, not a primary
grouping key. Group construction is order-independent.

## Endpoint identity requirements

Endpoint identity has five separate representations:

```text
raw_endpoint_label
normalized_endpoint_key
endpoint_semantic_identity
endpoint_family
ontology_mapping_status and provenance
```

The semantic identity must define the construct, measurement/observation type,
scope of adversity if applicable, expected value/reference-point semantics and
compatible contexts. A future versioned vocabulary must provide stable keys,
definitions, exact/equivalent/broader/narrower/related/incompatible relations,
mapping provenance, review status and immutable historical mappings.

```text
same text != necessarily same endpoint
different text != necessarily different endpoint
```

EFSA QPS `qps_status` and `qps_qualification` are regulatory-status semantic
roles. OpenFoodTox effect/admin labels are raw toxicological endpoint material.
They cannot share a toxicological comparison group solely because the target
substance is the same.

## Direction-of-effect requirement

A synthesis-capable protocol needs an optional, versioned direction-of-effect
representation. The current data do not justify universal automatic mapping.
The minimum envelope is:

```text
raw_conclusion
normalized_direction
normalization_status
normalization_provenance
direction_vocabulary_version
scope and stated_conditions
```

A provisional representational vocabulary may distinguish:

```text
adverse_effect_reported
no_adverse_effect_reported_under_stated_conditions
mixed_or_complex
unclear
not_applicable
```

These terms report what the evidence line states; they are not WYE safety or
risk claims. Concrete mappings, adversity interpretation and the vocabulary
itself require external scientific review. QPS recommendation/qualification has
direction `not_applicable` for experimental toxicology.

## Endpoint synthesis state model

Each declared endpoint/question scope produces exactly one canonical synthesis
state. It normally references one comparison group; `no_selected_evidence`,
`not_comparable` and `comparability_unresolved` are valid boundary outcomes when
no ordinary comparable group can be formed:

| State | Definition and trigger | Allowed conclusion | Uncertainty / continuation |
|---|---|---|---|
| `no_selected_evidence` | No selected line exists for the declared endpoint/question | Only that no evidence was selected under this protocol/snapshot | Valid endpoint state; may enter profile as a gap |
| `insufficient_evidence` | Lines exist but reviewed sufficiency requirements for the requested conclusion are not met | Descriptive evidence/limitations only | Valid state; conclusion is constrained, not a technical failure |
| `single_evidence_line` | Exactly one non-duplicate scientific line is interpretable | Scoped description of that line if allowed | Independence/corroboration remains unavailable |
| `multiple_lines_consistency_unresolved` | More than one line exists, but direction or consistency cannot be appraised | Describe lines and unresolved mapping | Continue only after governed resolution; may enter profile with limitation |
| `consistent_evidence` | Comparable lines support compatible scoped propositions under reviewed rules | Endpoint-scoped synthesis no stronger than sufficiency/confidence permit | Agreement is not proof of safety |
| `mixed_evidence` | Comparable lines show partial agreement plus material heterogeneity/discordance that does not meet true-conflict criteria | Report the mixed pattern and scopes | Preserve contrary/supporting lines and limitations |
| `conflicting_evidence` | Comparable eligible lines remain materially incompatible after contextual, correction, dependency, quality and relevance appraisal | Report true unresolved conflict | No mean, vote, provider tie-break or automatic danger conclusion |
| `not_comparable` | Selected lines address categorically distinct constructs/contexts and no endpoint group supports joint synthesis | Separate scoped descriptions only | Valid profile content; no cross-group conclusion |
| `comparability_unresolved` | Material identity/context prevents group assignment | Only unresolved-comparability statement | Propagate blocking uncertainty |

`no_selected_evidence` is preferred over the ambiguous `no_evidence`: excluded
records may still exist in the snapshot. A state may appear in a substance
profile when its scope and limitations are explicit. Synthesis completion is
separate from execution completion.

## Agreement and consistency semantics

Consistency is a relationship between comparable evidence lines, not equality
of stored values. A reviewed appraisal considers, as applicable:

- normalized direction of effect;
- qualitative proposition and endpoint interpretation;
- dose/value and reference-point context;
- compatibility of magnitude only where units/bases are governed;
- population/model, route, duration and substance form;
- study design, evidence channel and assessment purpose;
- dependency and correction lineage.

The relationship vocabulary is:

| State | Meaning |
|---|---|
| `agreement` | Scoped scientific propositions are compatible |
| `partial_agreement` | A shared core proposition exists, with material qualified differences |
| `discordance` | Comparable propositions are materially incompatible |
| `consistency_unresolved` | Direction/meaning/magnitude cannot be governedly compared |
| `not_applicable` | Consistency is meaningless because fewer than two comparable lines exist |

No numeric tolerance, vote or majority rule is defined. Any quantitative
magnitude comparison requires reviewed unit, dose-basis and endpoint semantics.

## Conflict semantics

Conflict classification proceeds only after comparison and preserves these
distinct states:

| State | Meaning | Handling |
|---|---|---|
| `apparent_conflict` | Surface labels/values/conclusions differ before comparability is resolved | Preserve both; perform no tie-break |
| `resolved_contextual_difference` | Difference is explained by endpoint, form, route, population, sex, duration, dose, design or role | Keep separate scoped groups |
| `resolved_supersession_or_correction` | Explicit applicable lineage identifies the governing corrected record | Preserve predecessor; use successor only in the declared current scope |
| `resolvable_discordance` | A documented, reviewed quality/relevance/context limitation explains the difference without deleting evidence | Retain both and state the limited resolution rationale |
| `true_unresolved_conflict` | Directly/conditionally comparable lines remain materially discordant | Emit `conflicting_evidence` and propagate conflict uncertainty |

Before a true conflict is declared, the trace must show appraisal of endpoint,
route, population/species, sex, duration, dose, study design, substance form,
release/correction, dependency, quality and relevance. Conflict is a valid
scientific outcome, not an execution failure and not evidence of danger by
itself.

## Quality aggregation model

Quality remains a structured profile, never a source rank or arithmetic mean.
The endpoint-level `quality_profile` records:

- the versioned appraisal framework and assessability status;
- canonically ordered line-level observations and criterion coverage;
- distribution across reviewed qualitative states, if such states exist;
- missing quality fields and quality-completeness gaps;
- limiting lines/criteria and heterogeneity;
- any minimum quality gate already applied in selection;
- review artifacts and uncertainty references.

An ordered range may be reported only if an externally reviewed vocabulary
defines the order. A “dominant evidence line” is not an architectural default;
it is allowed only under a future reviewed protocol rule with explicit rationale.
No provider or publication type is a proxy for quality.

## Relevance aggregation model

The `relevance_profile` is derived from the Phase 7.2 dimension vectors and
retains target, endpoint, population/model, sex, route, duration, dose, design,
scenario and substance-form states. Its representational summary may be:

```text
all_directly_relevant
mixed_direct_and_conditional_relevance
conditional_relevance_only
limited_relevance
relevance_unresolved
not_applicable
```

These states are structured summaries, not strength grades. Conditional and
limited relevance must name every transfer assumption. Concrete transfer and
applicability rules require external scientific review.

## Evidence sufficiency model

Sufficiency is always sufficiency for a declared endpoint conclusion, never a
generic property of a source or a finding count. The logical result is:

```text
sufficiency_state
conclusion_scope
criteria_version
criterion_results[]
critical_data_gaps[]
limiting_evidence_lines[]
rationale and rule references
```

Representable states are `sufficient_for_declared_conclusion`,
`sufficient_for_limited_conclusion`, `insufficient_evidence` and
`sufficiency_not_assessable`. A protocol may not use the positive states until
external scientific review has approved concrete criteria covering at least:

- endpoint and context coverage;
- evidence-line independence;
- quality and relevance;
- consistency/conflict;
- endpoint completeness and study diversity;
- critical data gaps.

Counts may describe inputs but never establish sufficiency on their own.

## Coverage model

Coverage is a multidimensional vector, not a percentage or a safety signal:

| Dimension | What is represented |
|---|---|
| Endpoint | Declared endpoint/question space represented by selected lines |
| Population/model | Human, animal/species, in-vitro or other declared contexts |
| Route | Declared route contexts |
| Duration | Declared time/scenario contexts |
| Dose context | Dose basis, range, effect/reference-point context |
| Study design | Declared study/evidence-design contexts |

Each dimension stores `covered`, `partially_covered`, `not_covered`, `unknown`
or `not_applicable`, plus evidence references, missing contexts and governing
rules. A coverage gap means missing representation. It is neither a negative
finding nor evidence of safety/danger.

## Uncertainty propagation

Uncertainty is represented as typed items, not compressed into a number:

| Type | Typical source | Propagation target |
|---|---|---|
| `identity_uncertainty` | Substance/form/study identity ambiguity | Evidence line, group, endpoint and profile |
| `endpoint_uncertainty` | Unresolved ontology or construct mapping | Group and endpoint |
| `population_transfer_uncertainty` | Species/model/population transfer assumption | Endpoint and profile |
| `route_uncertainty` | Missing/ambiguous or transferred route | Group and endpoint |
| `duration_uncertainty` | Missing/ambiguous duration classification | Group and endpoint |
| `dose_value_uncertainty` | Unit, basis, qualifier, range or reference-point ambiguity | Line, endpoint and dose-readiness summary |
| `dependency_uncertainty` | Unknown/partial shared lineage | Line count interpretation, endpoint and profile |
| `quality_uncertainty` | Missing appraisal inputs or framework limitations | Quality profile and confidence statement |
| `model_uncertainty` | Limits of scientific model/protocol construct | Endpoint and profile |
| `conflict_uncertainty` | Unresolved discordance | Endpoint and profile |

Every item records source, scope, direction if known, potential impact,
reducibility, reduction action/data, propagation target, blocking/qualifying
effect and provenance. Propagation is lossless: line items are carried to the
group, endpoint and profile where material; identical items may be referenced
once by semantic key but never silently cancelled. A protocol may transform an
item only through a versioned rule visible in the trace.

## Confidence semantics

Confidence means confidence in one explicitly scoped synthesis conclusion. It
is not evidence quality, safety probability, risk probability or certainty that
no harm exists.

The logical representation is a `confidence_statement` containing:

- exact conclusion and scope;
- `not_assessable`, `assessment_pending_review` or a value from a future
  externally reviewed qualitative vocabulary;
- structured basis across quality, relevance, consistency, coverage and
  uncertainty;
- limiting dimensions and evidence-line references;
- assumptions, rationale and rule/vocabulary versions.

Phase 7.3 approves this representation only. It approves no formula or
`limited/supported/strongly_supported` scale. A conclusion-strength vocabulary
and calculation framework require external scientific review.

## Endpoint-synthesis object

```text
endpoint_synthesis
├── endpoint_synthesis_key and digest
├── protocol, snapshot, target and selection digests
├── endpoint identity, family and ontology version
├── scientific question and scope
├── comparison_group(s) and evidence_line references
├── synthesis_state
├── direction/conclusion, only when supportable
├── consistency and conflict states
├── evidence sufficiency
├── quality profile
├── relevance profile
├── coverage profile
├── uncertainty items
├── confidence statement
├── supporting, contrary and context-only evidence references
├── assumptions and forbidden interpretations
└── synthesis trace reference
```

One endpoint identity may have multiple scoped comparison groups. Each produces
a separate endpoint-synthesis component linked to that identity; an endpoint
name is not permission to combine different route/population/duration/dose
questions.

## Substance hazard profile

The first Phase 7 scientific output is the non-scalar:

```text
substance_hazard_profile
├── profile key, schema version and digest
├── frozen substance/form identity
├── protocol version, evidence snapshot and selection digest
├── endpoint_syntheses[]
├── regulatory_context_components[]
├── endpoint-scoped sufficiency statements
├── quality and relevance profiles
├── coverage summary
├── uncertainty profile
├── conflict summary
├── endpoint-scoped confidence statements
├── assumptions and explicit data gaps
└── explanation/synthesis trace reference
```

The profile describes hazard evidence under stated contexts. It does not estimate
exposure or risk and has no central `hazard_score: float`. Different endpoints
and scientific channels remain distinct. A partial or conflicting profile is a
valid result. Profile-level summaries are inventories of endpoint states and
limitations, never an implicit cross-endpoint ranking.

## Positive, negative and missing observations

The model distinguishes:

| State | Meaning | Forbidden interpretation |
|---|---|---|
| `adverse_effect_reported` | Source reports an adverse effect under stated conditions | Product or universal risk established |
| `no_adverse_effect_reported_under_stated_conditions` | Source reports no adverse effect under its tested/reported conditions | Proof of safety or absence under other conditions |
| `absence_of_observed_effect` | Observation found no effect within sensitivity/context | Endpoint cannot occur |
| `absence_of_measured_effect` | Measurement did not detect effect under stated method | Safety established |
| `endpoint_not_evaluated` | Study/source did not evaluate the endpoint | Negative result |
| `no_selected_evidence` | Protocol selected no line for the endpoint | Danger or safety |
| `negative_study_result` | Governed study interpretation is negative for the exact proposition | Generic safety claim |

No state may be broadened beyond its population, route, duration, dose,
measurement and study context.

## Dose-response readiness

Phase 7.3 performs no dose-response modelling or unit conversion.

| Required concept | Current readiness | Evidence from current adapters/schema |
|---|---|---|
| Dose/effect value | Partial | OpenFoodTox may persist one numeric/text effect value; QPS not applicable |
| Dose basis | Partial/data gap | May exist in raw IUCLID material but has no governed normalized field |
| Unit | Partial | Finding unit is nullable/free text; no versioned unit mapping |
| Duration | Requires normalization | May exist in raw OpenFoodTox payload; no canonical duration field |
| Route | Requires normalization | OpenFoodTox route is raw and concatenated into population context |
| Effect level | Partial | One source-reported effect-level construct is captured, semantics heterogeneous |
| Reference-point type | Missing/ontology required | No canonical NOAEL/LOAEL/BMD/etc. identity model |
| Species/population | Partial/requires normalization | Raw/combined OpenFoodTox context; QPS is not an experimental population |
| Study design | Partial | Assessment type/raw IUCLID fields exist; no governed design vocabulary |

Hazard characterisation based on dose-response remains blocked by normalization,
ontology and external scientific review.

## Provider and cross-source treatment

### EFSA QPS

QPS is represented in the substance profile as a separate
`regulatory_status_and_qualification` context component. It is not an
experimental endpoint synthesis and is excluded from toxicological comparison
groups. `qps_status` and each qualification retain release, assessment, taxon
identity, scope and qualification text.

QPS neither proves safety nor automatically changes toxicological confidence.
Any future influence on confidence or applicability requires an explicit,
externally reviewed protocol rule. QPS receives no precedence or weight.

### OpenFoodTox

OpenFoodTox contributes selected `experimental_toxicology` findings. Its real
adapter provides study UUID, literature reference, assessment type, raw/admin
endpoint, optional numeric/text value and unit, combined species/sex/route
context, raw method/effect data and provenance.

Study-level grouping is comparatively ready within one source document UUID.
Broad endpoint comparison, direction interpretation, duration, dose basis,
species/route normalization, cross-provider study identity and quality appraisal
remain data/review gaps. A raw field is not a governed semantic mapping.

### Cross-source rule

```text
semantic compatibility > source identity
```

- The same study indexed twice is one dependency cluster, not two independent
  lines.
- Independent studies from different sources may share a comparison group only
  when all material semantic dimensions are compatible.
- A regulatory summary and experimental study retain different roles; a
  summary may link to the study but does not become a duplicate scientific vote.
- Different scientific channels remain separate unless a reviewed protocol
  explicitly defines their joint role.

There is no global provider precedence.

## Dependency-aware synthesis

| Dependency state | Synthesis behavior |
|---|---|
| `independent` | Retain as a distinct evidence line; no automatic strength increment |
| `partially_dependent` | Retain in one dependency cluster; expose overlap and avoid claims requiring full independence |
| `derived` | Preserve as context/interpretation linked to parent evidence; do not count as independent corroboration |
| `duplicate` | Collapse to one canonical line while preserving every representation in provenance |
| `unknown_dependency` | Preserve uncertainty; never assume independence; may block sufficiency claims requiring independent support |

Five records derived from one study remain one underlying evidence lineage.
Dependency resolution changes grouping, not the observed scientific content.

## Determinism and digest model

Canonical synthesis input is:

```text
protocol_digest
+ snapshot_digest
+ target/input_digest
+ selection_digest
+ versioned endpoint/context/dependency/quality vocabularies
+ governed normalization and review artifacts
```

Three derived digests are useful at different proof boundaries:

| Digest | Includes | Excludes |
|---|---|---|
| `comparison_group_digest` | Group schema/version, question/context signature, sorted evidence-line digests, comparability and dependency decisions, ontology/rule refs | Row order, DB IDs, timestamps, prose |
| `endpoint_synthesis_digest` | Protocol/snapshot/selection refs, sorted group digests, synthesis/consistency/conflict states, conclusion if any, quality/relevance/sufficiency/coverage/uncertainty/confidence payload and trace-step digest | Presentation, AI text, runtime metadata |
| `substance_profile_digest` | Frozen target, protocol/snapshot/selection, sorted endpoint-synthesis digests, sorted regulatory context digests, profile summaries/gaps/assumptions and trace digest | UI order, colours, localized text, execution timestamps |

Evidence-line digests and regulatory-context component digests are internal
content identities, not additional mandatory top-level execution boundaries.
Canonical serialization sorts set-like collections by stable semantic key and
preserves order only when order is scientifically meaningful.

```text
same protocol version
+ same snapshot and target
+ same selection digest
+ same comparison grouping and governed vocabularies
→ same endpoint syntheses and substance profile digests
```

Parser/normalization or mapping changes enter only through a new snapshot,
selection, protocol or governed artifact. Runtime timestamps, worker order,
database row order and generated prose never affect synthesis.

## Synthesis trace

The canonical machine trace records:

- selected and context-only evidence references;
- evidence-line construction and duplicate/dependency decisions;
- comparison signatures, group membership and comparability decisions;
- endpoint, direction, unit and context normalization mappings;
- supporting, contrary and unresolved propositions;
- consistency and conflict analysis, including rejected conflict hypotheses;
- quality/relevance observations and their frameworks;
- coverage and sufficiency criterion outcomes;
- every uncertainty source and propagation edge;
- endpoint states, conclusions, assumptions and forbidden interpretations;
- substance-profile composition and canonical ordering;
- rule, vocabulary, protocol, snapshot, selection and digest references.

AI may render this frozen trace in separately labelled prose. AI cannot modify,
complete or override the trace, evidence grouping, scientific state or result.

## Edge-case behavior

| # | Case | Evidence lines / groups | State and uncertainty | Allowed / forbidden conclusion | Historical behavior |
|---:|---|---|---|---|---|
| 1 | One selected finding | One line, one group | `single_evidence_line`; corroboration uncertainty | Describe scoped line / no general safety or strength claim | Frozen line replays identically |
| 2 | Two coherent findings from same study | One or dependency-linked lines in one group | Consistency not independent; dependency visible | Describe within-study coherence / not two-study corroboration | Same study identity retained |
| 3 | Two coherent independent findings | Two lines, one compatible group | Potential `consistent_evidence` after reviewed appraisal | Scoped agreement / no proof of safety | Digests stable under reorder |
| 4 | Five derived records from same study | One underlying lineage, derived context refs | Dependency uncertainty only if lineage incomplete | One lineage with multiple representations / not five votes | All representations retained |
| 5 | Same endpoint, different routes | Separate groups | `contextually_different` | Route-scoped statements / no conflict or average | Replay keeps historical route mappings |
| 6 | Same endpoint, different species | Separate or conditional reviewed groups | Transfer uncertainty | Species-scoped statements / no automatic human inference | Mapping/version frozen |
| 7 | Same endpoint, incompatible dose context | Separate groups | Dose-context limitation | Separate scoped results / no magnitude comparison | Raw/basis state frozen |
| 8 | Missing endpoint identity | No governed comparison group | `comparability_unresolved`; endpoint uncertainty | Mapping unresolved / no endpoint conclusion | Future ontology requires refresh/counterfactual |
| 9 | Same value, different meaning | Separate lines/groups by construct | Contextual difference | Distinct propositions / not duplicate or agreement | Semantic keys preserve difference |
| 10 | QPS plus OpenFoodTox same substance | Regulatory component plus toxicology group | Cross-channel separation | Display both scoped channels / no merged conclusion | Both source lineages retained |
| 11 | No eligible evidence | No lines | `no_selected_evidence` | State evidence absence / no safety or danger | Historical selection remains exact |
| 12 | Eligible lines but no comparability | Separate/not-comparable groups | `not_comparable` | Scoped descriptions / no overall consistency state | Group decisions immutable |
| 13 | True unresolved conflict | Comparable independent lines in one group | `conflicting_evidence`; conflict uncertainty | Report conflict / no mean, vote or danger claim | Conflict preserved until new execution |
| 14 | Low-quality evidence only | Lines/groups retained if selected | Quality-limited; sufficiency may be insufficient | Describe quality limitations / no unsupported strong conclusion | Framework/version frozen |
| 15 | High-quality, low-relevance evidence | Separate limited/conditional group | Relevance limitation | Narrow contextual statement / no target-context transfer | Relevance decisions frozen |
| 16 | Adequate quality, major coverage gap | Interpretable groups plus missing contexts | Coverage gap; limited sufficiency | Covered-scope conclusion / no universal claim | Gap remains historical fact |
| 17 | Assessment superseded after snapshot | Historical predecessor line only | Historical state unchanged | Historical conclusion under old snapshot / no claim it is current | Refresh handles successor |
| 18 | Counterfactual protocol version | Same lines/snapshot, new grouping/rules possible | New immutable states/digests | Rule-impact comparison / no overwrite | Baseline preserved |
| 19 | Parser/normalization change | Old representation in replay; new in refresh | Mapping/content differences explicit | Compare version impact / no silent replacement | Snapshot determines representation |
| 20 | Dependency unknown | Lines in uncertainty-linked cluster | `unknown_dependency`; may limit sufficiency | Describe possible dependence / no independence claim | Later resolution creates new execution |

## Conceptual deterministic synthesis vectors

Digest expectations describe equality/difference, not literal hashes. Unless a
vector explicitly varies them, line-level quality and relevance observations are
carried through unchanged, their state is `not_assessable` where no reviewed
framework exists, and no uncertainty beyond the one stated is introduced.

| # | Selected input and grouping | Consistency / profiles / uncertainty | Expected endpoint/profile effect | Digest expectation |
|---:|---|---|---|---|
| 1 | One valid finding → one line/group | Consistency N/A; quality/relevance retained; single-line uncertainty | `single_evidence_line`; one scoped endpoint component | Same canonical input reproduces all digests |
| 2 | Two findings, same study/proposition → one line | Within-line coherence only; dependency explicit | No independent corroboration added | Finding order does not change line/group digest |
| 3 | Two independent compatible lines | Agreement after reviewed direction mapping; adequate contextual coverage | Candidate `consistent_evidence` endpoint state | Reordering sources leaves digests unchanged |
| 4 | Five duplicate/derived records → one lineage | Derived records context-only | One underlying line in profile | Adding a source representation changes provenance input, not line count semantics |
| 5 | Oral and dermal lines | Contextually different; route coverage split | Two scoped groups, no conflict | Group digests differ by route |
| 6 | Human and animal lines | Separate/conditional; transfer uncertainty | Separate scopes unless reviewed transfer rule exists | Rule/vocabulary change changes digest |
| 7 | Compatible endpoint, incompatible dose bases | Consistency unresolved; dose uncertainty | Separate groups or `comparability_unresolved` | Basis normalization resolution changes future digest |
| 8 | Raw endpoint without governed identity | Endpoint uncertainty blocks group | `comparability_unresolved` in profile | Ontology mapping version changes digest |
| 9 | Equal numbers for distinct endpoint constructs | Not comparable despite same value | Separate endpoint syntheses | Distinct semantic identities produce distinct digests |
| 10 | QPS recommendation plus OpenFoodTox finding | Different channels; no cross-channel consistency | Regulatory component plus toxicology component | Source input order irrelevant |
| 11 | Empty selected set for endpoint | No quality/consistency inference; coverage absent | `no_selected_evidence` | Stable for same selection digest |
| 12 | Two selected but categorically different lines | Not comparable; structured relevance retained | `not_comparable`, separate descriptions | No combined-group digest is created |
| 13 | Comparable independent adverse/no-adverse propositions | Discordant; true conflict after reviewed checks | `conflicting_evidence`; conflict uncertainty | Tie/order changes nothing |
| 14 | Selected lines with quality not assessable | Quality gap and uncertainty | `insufficient_evidence` or `sufficiency_not_assessable` | Quality framework ref is committed |
| 15 | Direct endpoint but conditional target relevance | Conditional relevance and transfer uncertainty | Narrow/limited endpoint component | Assumption artifact changes digest |
| 16 | Consistent lines, missing chronic context | Agreement plus duration coverage gap | Consistent only in covered scope; profile gap explicit | Missing context is canonical content |
| 17 | Historical snapshot before correction | Historical line/group/state | Replay reproduces original profile | Exact digest equality required |
| 18 | Refresh after explicit correction | Corrected line, predecessor provenance | New endpoint/profile; old immutable | Snapshot/selection and outputs differ |
| 19 | Same snapshot, counterfactual protocol v2 | Grouping/sufficiency rules may differ | New immutable counterfactual result | Protocol and affected output digests differ |
| 20 | Two lines with unresolved dependency | Possible shared lineage; independence unavailable | Dependency uncertainty; reviewed sufficiency may be blocked | Resolving dependency changes new execution digest |

No vector produces a numeric hazard score, exposure estimate, product risk or
cross-endpoint scalar.

## Scientific-review boundary matrix

| Decision area | Classification | Rationale |
|---|---|---|
| Evidence line/comparison/result envelopes | ARCHITECTURALLY APPROVED | Preserve identity, dependency and multidimensional outputs |
| Duplicate collapse and no record-count strength | ARCHITECTURALLY APPROVED | Provenance/identity rule prevents false independence |
| Canonical ordering, digests and trace | ARCHITECTURALLY APPROVED | Reproducibility and audit mechanism |
| Separation of consistency, quality, relevance, coverage, uncertainty and confidence | ARCHITECTURALLY APPROVED | Prevents category errors and premature scalarization |
| QPS regulatory channel separated from experimental toxicology | ARCHITECTURALLY APPROVED | Matches current adapter semantics; exact QPS scientific scope still reviewed |
| Endpoint equivalence/family mappings | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Scientific construct identity |
| Direction/adversity normalization | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Changes scientific meaning and allowed claims |
| Conditional population/route/duration/dose comparability | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Transfer assumptions affect conclusions |
| Concrete quality criteria | REQUIRES EXTERNAL SCIENTIFIC REVIEW | No source rank or arbitrary rubric is valid |
| Sufficiency and conclusion-strength criteria | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Evidence count cannot establish support |
| Confidence framework and hazard interpretation | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Determinism is not scientific validation |
| Dose-response/reference-point semantics | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Requires domain method and normalized inputs |
| Endpoint/study/dependency ontologies | DATA GAP | Not represented generally through `0018` |
| Structured route/duration/population/dose basis | DATA GAP | Current OpenFoodTox representation is partial/raw |
| Quality/relevance/coverage/uncertainty source fields | DATA GAP | No general persisted normalized model |
| Ingredient projection | DEFINED IN 7.4 / EXTERNAL REVIEW AND DATA REQUIRED | `WYE_INGREDIENT_PROJECTION.md` defines the non-scalar mapping-aware envelope; form/composition transfer remains review-gated |
| Exposure/product assessment | DEFINED IN 7.5 / EXTERNAL REVIEW AND DATA REQUIRED | `WYE_PRODUCT_ASSESSMENT.md` defines readiness and risk non-computability without changing hazard synthesis |
| Persistence/runtime/API | DEFERRED TO LATER PHASE | Persistence and rollout phases; not authorized here |

## Current-schema gap matrix

| Required concept | Status through `0018` | Current basis / gap | Future requirement |
|---|---|---|---|
| Endpoint ontology | Missing/needs normalization | Free-text finding endpoint; QPS fixed source keys | Versioned definitions, mappings and history |
| Study identity | Partial | OpenFoodTox document UUID/reference; no general cross-source identity | Canonical study identity/equivalence model |
| Evidence-line identity | Missing | Can be derived only for limited current lineage | Immutable line contract/persistence or snapshot projection |
| Comparison groups | Missing | 7.2 conceptual group key only | Canonical group payload and reviewed mapping inputs |
| Effect direction | Missing | Raw conclusion/value text only | Versioned direction vocabulary and reviewed mapping |
| Quality representation | Missing | No general appraisal structure | Framework/version, observations and review provenance |
| Relevance representation | Partial/documental | Selection contract defines vector; no persistence | Immutable decision/profile representation |
| Coverage | Missing | No endpoint/context coverage model | Multidimensional profile structure |
| Uncertainty | Missing | Raw limitations may exist in prose | Typed uncertainty and propagation model |
| Dependency lineage | Missing/partial | Run/fingerprint and OpenFoodTox UUID help; no general edges | Immutable dependency/study relations |
| Dose normalization | Partial | Numeric/text/unit plus raw IUCLID context | Unit, dose basis, qualifier and duration normalization |
| Reference-point semantics | Missing | No governed reference-point identity | Versioned NOAEL/LOAEL/BMD/etc. model if scientifically approved |
| Synthesis persistence | Missing/future persistence | No Phase 7 result storage | Immutable document/rows designed in persistence phase |
| Hazard-profile persistence | Missing/future persistence | No non-scalar profile model | Immutable canonical profile and query projections |

No schema or migration is proposed by this matrix.

## Implementation-readiness matrix

Classification does not authorize implementation.

| Future component | Classification | Reason |
|---|---|---|
| Evidence-line envelope and canonical digest | READY FOR IMPLEMENTATION | Logical identity/content boundary is defined |
| Exact-duplicate/reingestion grouping | READY FOR IMPLEMENTATION | Phase 6 fingerprints and Phase 7.2 rules provide anchors |
| Comparison-group envelope and canonical ordering | READY FOR IMPLEMENTATION | Structure and deterministic signature are defined |
| Endpoint-synthesis and substance-profile skeletons | READY FOR IMPLEMENTATION | Non-scalar output envelopes are defined |
| Synthesis trace and digest envelopes | READY FOR IMPLEMENTATION | Causal content and proof boundaries are defined |
| General study/dependency grouping | BLOCKED BY DATA MODEL | Cross-source study/dependency identity is missing |
| Endpoint/population/route/duration/dose grouping | BLOCKED BY DATA MODEL | Normalized vocabularies/mappings are missing |
| Direction-of-effect mapping | BLOCKED BY SCIENTIFIC REVIEW | Scientific meaning requires expert validation |
| Quality profile content | BLOCKED BY SCIENTIFIC REVIEW | No approved framework/criteria |
| Relevance transfer rules | BLOCKED BY SCIENTIFIC REVIEW | Applicability assumptions affect claims |
| Uncertainty transformation rules | BLOCKED BY SCIENTIFIC REVIEW | Representation is ready; material-impact semantics are not |
| Consistency/conflict classification runtime | BLOCKED BY SCIENTIFIC REVIEW | Concrete equivalence/discordance criteria are unvalidated |
| Evidence sufficiency/confidence | BLOCKED BY SCIENTIFIC REVIEW | No approved framework or conclusion vocabulary |
| Scientific hazard interpretation | BLOCKED BY SCIENTIFIC REVIEW | Profile envelope does not validate hazard conclusions |
| Ingredient projection envelope | READY FOR IMPLEMENTATION | Phase 7.4 defines mapping-aware non-scalar entries; concrete form/composition transfer remains blocked by data/review |
| Exposure/product assessment envelopes | READY FOR IMPLEMENTATION | Phase 7.5 defines non-numeric readiness/gate objects; exposure/risk methods remain blocked |
| DB persistence/API/rollout | DEFERRED TO LATER PHASE | Requires persistence design, validation and governance |

## Phase 7.3 exit criteria

- [x] Synthesis unit defined as dependency-aware evidence lines within comparison groups.
- [x] Evidence-line semantics and construction rules defined.
- [x] Comparison-group compatibility and states defined.
- [x] Endpoint identity and vocabulary requirements defined.
- [x] Multidimensional synthesis states defined without scores.
- [x] Agreement/consistency semantics defined.
- [x] Apparent, resolved and true conflict semantics defined.
- [x] Direction-of-effect representation requirement defined and review-gated.
- [x] Non-arithmetic quality aggregation model defined.
- [x] Relevance aggregation model defined.
- [x] Evidence sufficiency representation and review boundary defined.
- [x] Multidimensional coverage model defined.
- [x] Typed uncertainty propagation defined.
- [x] Confidence representation separated from quality and risk.
- [x] Endpoint-synthesis object defined.
- [x] Multidimensional substance hazard profile defined.
- [x] Positive, negative and missing observations distinguished.
- [x] Dose-response readiness assessed without modelling.
- [x] QPS regulatory-context treatment defined.
- [x] OpenFoodTox experimental-evidence readiness defined.
- [x] Cross-source and dependency-aware synthesis rules defined.
- [x] Deterministic ordering and digest model defined.
- [x] Canonical synthesis trace defined.
- [x] Twenty edge cases analyzed.
- [x] Twenty conceptual deterministic test vectors defined.
- [x] Scientific-review boundaries classified.
- [x] Current-schema gaps documented.
- [x] Implementation readiness classified.

## Phase 7.4 specialization and roadmap

The Phase 7 roadmap remains unchanged. Ingredient projection is specialized in
`WYE_INGREDIENT_PROJECTION.md` without changing this substance-synthesis
contract.

The proposed next checkpoint is:

```text
Phase 7.5 — Exposure Readiness and Product Assessment Semantics
```

Phase 7.5 is defined in `WYE_PRODUCT_ASSESSMENT.md` without changing this
substance-synthesis contract. Hazard/profile uncertainty remains separately
traceable and cannot be converted into product risk without sufficient exposure
and reviewed reference semantics.

## Phase 7.6 persistence specialization

`WYE_SCORING_PERSISTENCE.md` defines immutable typed artifacts for evidence
lines, comparison groups, endpoint syntheses and substance profiles. Their
domain digests are component roots beneath the canonical `result_digest`; query
tables may flatten them but cannot replace or reinterpret their payloads. No
synthesis runtime or scientific categorization is authorized by persistence.
