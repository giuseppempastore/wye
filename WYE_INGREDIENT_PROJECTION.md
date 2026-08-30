# WYE — Substance-to-Ingredient Projection Contract

## Status and scope

This document is the canonical Phase 7.4 specification for projecting an
immutable `substance_hazard_profile` onto a frozen ingredient identity through
the historical ingredient-to-substance bridge. It specializes, but does not
replace:

- `WYE_PHASE_7.md`;
- `WYE_SCORING_SEMANTICS.md`;
- `WYE_SCORING_PROTOCOL.md`;
- `WYE_SCORING_EXECUTION_MODEL.md`;
- `WYE_EVIDENCE_SELECTION.md`;
- `WYE_EVIDENCE_SYNTHESIS.md`.

Phase 7.4 defines a logical projection contract. It does not implement a runtime
projector, persistence, an API, exposure assessment, product assessment,
ingredient/product scoring, formulas, weights, thresholds or numerical output.

Review baseline:

```text
branch: ingredients_score
HEAD: 6e9f4d465edcd795fac60fac983fb085865bd418
origin/ingredients_score: 6e9f4d465edcd795fac60fac983fb085865bd418
working tree before Phase 7.4: clean
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017_ingredient_mapping_history
```

The seven canonical Phase 7 documents, schema and migrations through `0017`,
mapping repository/service and mapping integrity/history tests were read before
defining this contract. The local mapping workflow tables are currently empty;
schema and behavior therefore come from the versioned repository contracts and
tests, not from inferred local examples.

## Non-negotiable boundaries

```text
substance identity != ingredient identity
presence relationship != quantitative composition
contains != concentration known
mixture_component != dose known
derived_from != substance necessarily present
hazard != exposure != risk
ingredient order != concentration
mapping confidence != scientific confidence
missing composition != worst-case composition
absence of evidence != evidence of danger
```

```text
relationship semantics govern projection semantics
all ingredient_substance links are not equivalent
```

Projection preserves a scoped scientific association. It never invents amount,
concentration, dose, exposure frequency/duration, product contribution, product
risk, safety, ranking or health score.

## Audit of the current mapping model

### `ingredients`

Current fields are `id`, `canonical_name`, `ingredient_group`, legacy
`risk_level`, `allergen_flag`, legacy `evidence_level`, `cas_number`,
`einecs_number`, `common_name`, `status`, `created_at` and `updated_at`.
Ingredient status is `active`, `deprecated` or `review_pending`. Identity fields
are mutable and have no complete temporal history. Legacy risk/evidence fields
are excluded from Phase 7 inputs.

### `substances`

Current fields are `id`, `preferred_name`, `normalized_name`, `scientific_name`,
`substance_type`, `status`, `description`, `created_at` and `updated_at`.
`substance_type` is limited to `additive`, `chemical_substance`,
`biological_substance`, `contaminant`, `nutrient`, `mixture` and `unknown`.
Status is `active`, `deprecated` or `review_pending`. This is not a chemistry
form/speciation model.

### `ingredient_substances`

The materialized bridge contains:

```text
id
ingredient_id
substance_id
relationship_type
mapping_method
mapping_status
mapping_confidence
source_dataset_release_id
ingestion_run_id
provenance
reviewed_by / reviewed_at
valid_from / valid_to
created_at
```

Actual relationship vocabulary:

```text
represents
contains
derived_from
mixture_component
equivalent_to
```

Actual mapping methods are `manual_review`, `dataset`, `deterministic` and
`legacy`; controlled proposals accept the first three only. Actual bridge
statuses are `accepted`, `pending_review`, `ambiguous`, `rejected` and
`legacy_unreviewed`.

`mapping_confidence` is nullable and constrained only to `[0,1]`. The schema
does not define its construct, calibration or scientific meaning. It cannot be
used as scientific or projection confidence.

### Controlled history introduced by `0017`

| Object | Effective fields and states | Historical role |
|---|---|---|
| Proposal | UUID key, ingredient, substance, relationship, method, confidence, release/run, proposer, provenance; `pending_review`, `accepted`, `rejected` | Append-only proposed mapping identity |
| Decision | Proposal, `accept`/`reject`/`defer`, accepted `effective_from`, reviewer/time, reason, notes/provenance | Review history; one terminal accept/reject, multiple defer decisions possible |
| Materialization | Decision, proposal, bridge row, `applied`/`already_current`, actor/time/provenance | Proves controlled acceptance was applied or converged on an existing current row |
| Closure | Bridge row, inclusive `valid_to`, actor/time, reason/provenance | Append-only closure of one open accepted mapping |

The bridge permits many substances per ingredient, many ingredients per
substance, and multiple relationship types between the same pair. It permits
only one open accepted row for the same ingredient, substance and relationship.
Closed rows remain historical.

### Effective validity behavior

The repository resolves a mapping for an `as_of` date only when:

```text
mapping_status = accepted
valid_from IS NOT NULL
valid_from <= as_of
valid_to IS NULL OR valid_to >= as_of
```

Both bounds are inclusive. Closing on a date keeps the mapping applicable for
that date; reacceptance cannot begin until a later date. `as_of` is a `DATE`, not
a timestamp, and the repository does not publish a timezone/day-boundary rule.
That convention remains a future protocol/persistence requirement.

Acceptance through the controlled service requires an active substance and a
materialization. Historical/pre-0017 accepted rows can exist without a 0017
materialization, so a future projector must distinguish governed materialized
acceptance from legacy/directly persisted acceptance and appraise provenance.
Ingredient existence is checked on proposal, but acceptance does not currently
require ingredient status `active`.

### Current gaps

The model does not represent:

- normative scientific definitions or scoped rationale for relationship types;
- equivalence kind or scope;
- salt/hydrate/isomer/speciation/formulation compatibility;
- ingredient-specific composition, component fraction or quantity range;
- product/batch-specific presence evidence;
- transformation, residual presence or process fate;
- calibrated meaning for `mapping_confidence`;
- full temporal ingredient/substance identity history;
- timestamp-level validity semantics;
- frozen mapping snapshots or ingredient projection persistence.

## Relationship-type semantic contract

The following meanings are protocol contracts, not claims that the current row
contains all required scientific evidence.

| Relationship | Minimum semantic meaning | Minimum additional evidence | May project | Must not project | Composition/exposure consequence | Historical use |
|---|---|---|---|---|---|---|
| `represents` | Ingredient identity denotes the assessed substance in the reviewed scope | Accepted valid mapping, resolved identities, compatible form and protocol domain | Scoped substance evidence/profile dimensions, with ingredient target label | Exposure, risk, product contribution or unreviewed forms | Quantity still unknown; exposure unavailable | Only while the frozen mapping is effective |
| `equivalent_to` | Ingredient and substance are equivalent only under a stated reviewed equivalence scope | Equivalence kind, rationale, form/context and question coverage | Direct or qualified carryover only within reviewed scope | Universal chemical identity or out-of-scope conclusions | Equivalence does not provide amount/exposure | Use the equivalence artifact frozen as-of |
| `contains` | Ingredient is asserted to include the substance qualitatively in the stated scope | Accepted presence basis; composition state for any quantitative use | Qualitative association and presence-scoped evidence context | Hazard magnitude, dose, risk or product contribution without quantity | `contains != concentration known`; exposure blocked | Only for the historical presence assertion represented by the mapping |
| `mixture_component` | Substance is a component of an ingredient mixture | Component identity; fraction/range and mixture context when requested | Qualitative component association; qualified scoped profile where reviewed | Whole-mixture equivalence, fraction, interactions, dose or risk by default | Unknown proportion permits qualitative association only | Component set and composition state must be frozen as-of |
| `derived_from` | Ingredient has provenance or transformation lineage from the substance | Transformation/residual-presence evidence for any presence-dependent transfer | Derivation provenance; exceptional qualified association after review | Current presence, retained form, hazard carryover, dose or risk by default | Residual presence and amount are unknown | Historical derivation may be shown; later process evidence requires refresh |

Mapping certainty never broadens these meanings. A perfectly certain
`derived_from` mapping still does not establish residual presence.

## `represents`

`represents` supports the closest available form of direct semantic carryover
when all of these are frozen and satisfied:

```text
accepted mapping
controlled materialization or otherwise sufficient governed provenance
mapping valid at evaluation as_of
resolved and eligible ingredient/substance identities
compatible substance form/speciation
compatible protocol domain and conclusion scope
available immutable substance profile
```

The output is still an `ingredient_scientific_projection`: the endpoint and
hazard-related evidence profile is relabelled with an ingredient scope and the
mapping is exposed. It is not an intrinsic scalar “ingredient hazard”, exposure
or risk.

## `equivalent_to`

Equivalence may mean chemical identity, functional equivalence, regulatory
equivalence or label/catalog equivalence. The current schema stores none of
these distinctions. Therefore an accepted `equivalent_to` row alone does not
authorize direct scientific projection.

Direct carryover is allowed only when a governed review artifact identifies the
equivalence kind, relevant substance form, scientific question, endpoint/domain
scope and limitations. A narrower or function-only equivalence produces a
qualified projection or blocks the requested dimension. Missing scope yields
`projection_unresolved`, never assumed total identity.

## `contains`

`contains` is a qualitative presence/composition relation at the mapping scope.
The future protocol must still establish whether the assertion applies to the
ingredient definition, a formulation, a source dataset or a specific
product/batch.

Without concentration, the projector may expose:

```text
substance hazard evidence associated with this ingredient through contains
```

It must not expose ingredient hazard magnitude, dose, exposure, risk or product
risk contribution. Even when a quantity becomes known, exposure/risk remains a
later protocol decision requiring basis, scenario, route, frequency, duration
and population.

## `mixture_component`

A mixture component is represented with one composition state:

```text
component identity known / unresolved
fraction unknown
fraction known
fraction range known
mixture otherwise unspecified
```

These are conceptual states; the current bridge does not store them. With an
unknown fraction the output is qualitative association only. A known fraction
or range may make a future composition-aware projection possible, but it does
not automatically transfer whole-mixture hazard, account for interactions or
compute exposure/risk.

## `derived_from`

```text
derived_from != current presence
```

The normal projection is provenance-only and presence-dependent endpoint
dimensions are blocked. An exception requires governed evidence describing the
transformation, residual identity/form, residual presence and applicable
scientific transfer. Such rules require external scientific review and a new
snapshot/execution when new residual evidence appears.

## Substance form and identity compatibility

The projector needs only a minimal compatibility assessment, not a complete
chemistry ontology:

```text
exact_form_match
reviewed_form_equivalence
form_difference_material
form_unresolved
not_applicable
```

Form context may distinguish salt, hydrate, isomer, mixture, complex,
derivative, parent compound, metabolite and formulation when material to the
endpoint. The canonical substance family or shared name is not enough to prove
interchangeability. A reviewed mapping must identify the source and target form,
scope, endpoint/domain applicability, vocabulary version and provenance.

The current coarse `substance_type`, names and identifiers do not supply these
semantics. Form compatibility is therefore generally a data gap and scientific
review boundary.

## Projection eligibility model

The deterministic pipeline is:

```text
candidate mapping set
→ accepted/materialized/provenance state
→ historical validity at frozen as_of
→ relationship semantic dispatch
→ ingredient/substance identity and form compatibility
→ substance-profile and protocol compatibility
→ composition/presence readiness for requested dimensions
→ immutable projection decision
```

The final state is one of:

| State | Meaning | Risk implication |
|---|---|---|
| `direct_projection` | Scoped semantic dimensions may be carried through `represents` or fully reviewed equivalence | None; exposure/risk remain unavailable |
| `qualified_projection` | Dimensions may be carried only with explicit relationship/form/composition assumptions and limitations | None |
| `qualitative_association` | Substance profile may be linked/listed, but its hazard conclusion is not transferred as an ingredient property | None |
| `projection_blocked` | A deterministic ineligible condition prevents requested carryover | Not danger, safety or worst case |
| `projection_unresolved` | Required mapping, equivalence, form, presence or composition semantics cannot be determined | No automatic candidate or worst-case choice |

Projection state is assessed per substance-profile component/dimension. One
ingredient projection can contain entries in different states.

## Canonical logical object and naming

The canonical output is:

```text
ingredient_scientific_projection
```

“Ingredient hazard profile” is rejected as the primary name because it can
suggest a unique intrinsic hazard property and hide multiple substances,
relationships and blocked dimensions.

```text
ingredient_scientific_projection
├── projection key, schema version and digest
├── ingredient identity snapshot and digest
├── mapping snapshot key/digest and as_of semantics
├── protocol version/digest and requested scientific scope
├── substance_projection_entries[]
│   ├── mapping identity/history state
│   ├── relationship type and semantic-policy version
│   ├── frozen substance identity/form
│   ├── substance hazard profile reference/digest
│   ├── projection state and reason codes
│   ├── projected, qualified and blocked dimensions
│   ├── composition/presence readiness
│   ├── carried and projection-induced uncertainty
│   ├── confidence statement
│   └── assumptions and trace references
├── unresolved/rejected/absent mapping observations[]
├── cross-entry aggregation status: not_performed
└── ingredient projection trace reference
```

There is no `ingredient_score` and no implicit whole-ingredient conclusion.

## Projection of substance-profile dimensions

| Substance-profile dimension | Direct carryover | Qualified/association behavior | Blocked behavior |
|---|---|---|---|
| Endpoint identity | Carry exact scoped identity/version for compatible `represents` or reviewed equivalence | Retain as substance endpoint associated through `contains`/component relation | Block when form/relationship changes endpoint meaning |
| Hazard conclusion/state | Carry only within matching form, endpoint and target scope | Qualify as substance conclusion associated with ingredient; never hazard magnitude | Block for `derived_from` without residual proof or incompatible form |
| Quality profile | Preserve unchanged as quality of the substance evidence basis | May be referenced; never recast as mapping quality | Never replace missing mapping evidence |
| Relevance profile | Re-evaluate ingredient applicability; retain original basis | Add transfer assumptions and limitations | Block dimensions not applicable to ingredient/form |
| Coverage | Preserve original covered/missing scopes | Add projection-specific gaps; never expand coverage | Missing scope remains missing |
| Uncertainty | Carry all substance uncertainty | Add projection-induced items | Never delete/cancel upstream uncertainty |
| Confidence | Recompute/represent for the projected conclusion | Constrain by mapping/form/composition limitations | Do not copy when projection is blocked/unresolved |
| Regulatory context | Keep separate channel and exact qualification scope | Associate only where relationship and target scope permit | Never convert to toxicological endpoint or safety claim |

“Direct” means semantic scope may carry, not that every field is copied
unchanged. Relevance, uncertainty and confidence always account for the new
ingredient target.

## Projection-induced uncertainty

The projector adds, without replacing substance-profile uncertainty:

| Type | Source | Typical effect |
|---|---|---|
| `mapping_identity_uncertainty` | Ingredient/substance candidate ambiguity | Blocks or narrows target association |
| `relationship_semantic_uncertainty` | Relationship meaning/scope missing | Blocks direct dispatch |
| `substance_form_uncertainty` | Salt/isomer/mixture/etc. compatibility unresolved | Blocks affected endpoints or qualifies transfer |
| `composition_uncertainty` | Ingredient composition not represented | Blocks magnitude/composition-dependent dimensions |
| `presence_uncertainty` | Actual ingredient/product presence not established | Limits to mapping/provenance statement |
| `mixture_fraction_uncertainty` | Component proportion/range absent | Limits to qualitative component association |
| `transformation_residual_uncertainty` | Fate/residual identity after derivation unknown | Blocks presence-dependent projection |
| `temporal_mapping_uncertainty` | `DATE` boundary/history or snapshot state unresolved | Blocks exact historical projection |

Each item uses the Phase 7 uncertainty envelope: source, scope, direction if
known, impact, reducibility, required data/action, propagation target and
blocking/qualifying effect.

## Confidence propagation

Ingredient projection confidence is confidence in the exact projected
conclusion. It is distinct from both substance-synthesis confidence and mapping
confidence.

```text
ingredient projection confidence cannot exceed what is justified by
the substance conclusion and the mapping/projection basis
```

This is an ordering constraint, not a minimum, mean or formula. The
representation contains upstream confidence reference, mapping decision basis,
relationship/form/composition limitations, added uncertainties, exact projected
claim, review status and governing rule. If no reviewed confidence framework
exists, the state is `not_assessable`.

A certain `contains` mapping with unknown concentration can support confidence
in the qualitative relationship while leaving quantitative projection and risk
unavailable. `mapping_confidence` is never copied into this field.

## Temporal execution semantics

| Execution mode | Mapping behavior |
|---|---|
| `NORMAL` current | Resolve accepted mappings effective on the declared current `as_of`, freeze rows/history/identity state, then project |
| `REPLAY` | Reuse exact frozen mapping snapshot and ingredient/substance identities; query no current mapping row |
| `COUNTERFACTUAL` | Reuse historical mapping snapshot and substance inputs; apply a different protocol version without refreshing mappings |
| `REFRESH` | Resolve a new mapping/identity state and/or new substance profile into a new snapshot and immutable projection |

A correction, closure or new mapping never mutates a historical projection.
Current service resolution uses inclusive `DATE` bounds; the future canonical
snapshot must freeze the chosen boundary convention and resolved membership.

## Multiple-substance and ambiguous mappings

An ingredient projection is an ordered-by-canonical-key collection of separate
substance projection entries. Cases such as one `represents` plus several
`contains`, several mixture components or several reviewed forms remain separate
with their own relationship, scope, states and uncertainty.

```text
multiple projected substance profiles remain separately traceable
```

Multiple unresolved candidate mappings produce `projection_unresolved` and
`projection_not_available` for the requested association. The projector never
chooses the most hazardous, highest-confidence, most similar or first database
row.

## Absent, rejected and historical mapping states

| Mapping observation | Meaning | Projection behavior |
|---|---|---|
| No mapping exists | No bridge assertion is available in the frozen universe | `projection_blocked`; no absence/safety inference |
| Explicitly rejected | A proposal/legacy row was rejected in its reviewed scope | Do not project that candidate; retain reason/history |
| Closed/superseded | Accepted row has an inclusive `valid_to` or closure event; `superseded` is derived, not a bridge status | Project only for historical dates inside its interval |
| Invalid for `as_of` | Accepted row exists but interval does not cover the frozen date | Block for that execution |
| Pending/ambiguous/legacy unreviewed | No accepted deterministic bridge | `projection_unresolved` or blocked per state; never auto-select |
| Accepted but provenance/materialization insufficient | Row says accepted but Phase 7 cannot prove governed scope | Block or unresolved under the protocol; do not trust status alone |

These observations remain in the trace and are not negative scientific evidence.

## Versioned projection reason codes

The hybrid vocabulary is:

- `wye_projection_core/v1` for identity, history, state and technical provenance;
- `food_tox_ingredient_projection/v1` for relationship/form/scientific scope.

Every code has an immutable definition, stage, required context, deterministic
basis, retryability/resolvability and rule reference.

### Core reasons

| Code | Meaning |
|---|---|
| `blocked_no_mapping` | Frozen universe contains no candidate bridge |
| `blocked_mapping_not_accepted` | Mapping state is rejected, pending, ambiguous or legacy-unreviewed for published projection |
| `blocked_mapping_not_materialized` | Controlled accepted decision lacks required materialization/proof |
| `blocked_mapping_not_valid_as_of` | Accepted interval does not include frozen `as_of` |
| `blocked_unresolved_identity` | Ingredient or substance identity is unresolved |
| `blocked_inactive_substance` | Substance state is ineligible for requested current projection |
| `blocked_substance_profile_unavailable` | No immutable compatible substance profile exists |
| `unresolved_multiple_candidate_mappings` | Candidates exist without accepted deterministic resolution |
| `unresolved_temporal_mapping_state` | Exact historical interval/boundary cannot be established |
| `unresolved_mapping_provenance` | Acceptance/scope provenance is insufficient |

### Food-toxicology projection reasons

| Code | Meaning |
|---|---|
| `projected_direct_represents` | Valid `represents` mapping and compatible form/scope permit direct semantic carryover |
| `projected_direct_equivalent_scope_reviewed` | Reviewed equivalence explicitly covers the projected question |
| `projected_qualified_contains_presence_only` | `contains` permits qualitative presence-scoped association without magnitude |
| `projected_qualified_mixture_component` | Component profile is associated with explicit mixture limitation |
| `projected_qualified_derived_from_residual_reviewed` | A reviewed residual-presence/form artifact permits a narrowly scoped derivation projection |
| `associated_regulatory_context` | Separate regulatory context is associated without toxicological/safety conversion |
| `blocked_relationship_not_projectable` | Relationship cannot carry the requested dimension |
| `blocked_protocol_domain_incompatible` | Substance profile domain/question cannot be applied to ingredient target |
| `blocked_substance_form_incompatible` | Material form difference prevents transfer |
| `blocked_missing_composition_for_requested_dimension` | Requested dimension requires unavailable composition |
| `blocked_presence_not_established` | Actual presence required by the claim is not established |
| `blocked_derived_from_no_residual_presence` | Derivation provides no residual-presence basis |
| `unresolved_equivalence_scope` | Kind/scope of `equivalent_to` is unspecified |
| `unresolved_substance_form` | Form compatibility cannot be established |
| `unresolved_mixture_fraction` | Component proportion needed by requested projection is absent |
| `unresolved_transformation_residual` | Derivation fate/residual state is unknown |

Published vocabulary versions are immutable. Human/localized text and AI
rendering are non-canonical.

## Composition readiness

| State | Meaning | Projection boundary |
|---|---|---|
| `composition_unknown` | Presence and quantity are not adequately established | Mapping/provenance context only |
| `presence_known_quantity_unknown` | Qualitative presence is supported; no amount/fraction | Qualitative association; no magnitude/exposure/risk |
| `quantity_range_known` | Governed quantity/fraction range, unit, basis and provenance exist | Future composition-aware work may use it; exposure still separate |
| `quantity_known` | Governed quantity/fraction, unit, basis and provenance exist | Does not alone supply use/intake/exposure scenario |
| `not_applicable` | Relationship/question is non-compositional, such as derivation provenance | No quantity inference |

The current ingredient-substance bridge cannot generally distinguish these
states beyond mapping semantics; quantity/range fields are missing.

## Direct versus qualified projection

`direct_projection` means a compatible `represents` or explicitly scoped
equivalence can carry endpoint-scoped substance conclusions into an ingredient
target statement without changing scientific meaning. It still adds target and
mapping trace, preserves uncertainty and excludes exposure/risk.

`qualified_projection` means the relationship or form permits only a narrower
statement with explicit caveats. `contains` and `mixture_component` normally
produce qualified or qualitative association. Qualification cannot be used to
hide a blocked dimension.

## Cross-substance aggregation boundary

Phase 7.4 performs no cross-substance scientific aggregation. It forbids:

```text
maximum hazard
average hazard
sum of hazards
worst substance wins
source/profile voting
```

The result is a structured set. A future aggregation policy would need its own
scientific question, interaction/dependency method, composition/exposure inputs,
validation and protocol version.

## Regulatory-context projection

QPS and other regulatory context may be associated with an ingredient only
through an eligible relationship and matching taxon/substance/form/scope. It
remains a `regulatory_status_and_qualification` component separate from
toxicological endpoints.

```text
QPS qualified status != ingredient safe
absence/non-applicability of QPS != ingredient dangerous
```

Qualifications, jurisdiction, release and reviewed relationship scope remain
visible. Regulatory context does not automatically change toxicological or
projection confidence.

## Ingredient projection trace

The canonical trace must allow traversal through:

```text
ingredient identity snapshot
→ candidate/current/historical mapping records
→ proposal / decision / materialization / closure where applicable
→ relationship type and validity at as_of
→ substance identity/form
→ immutable substance hazard profile
→ projection decision and reason codes
→ projected, qualified and blocked dimensions
→ carried and newly introduced uncertainty
→ final substance projection entry
```

It records excluded/rejected/ambiguous mappings, composition state, assumptions,
rules/vocabularies and every confidence limitation. AI may verbalize the frozen
trace but cannot choose mappings, alter projection states or create conclusions.

## Determinism and digest model

The minimum additional proof boundaries are:

| Digest | Includes | Excludes |
|---|---|---|
| `mapping_snapshot_digest` | Ingredient identity digest, as-of/boundary semantics, sorted mapping rows and semantic payloads, proposal/decision/materialization/closure references, substance identity/form states and provenance digests | Row order, mutable display names not frozen, runtime timestamps, DB surrogate identity alone |
| `ingredient_projection_digest` | Projection schema/canonicalization version, protocol digest, ingredient identity digest, mapping snapshot digest, sorted substance-profile digests, per-entry states/reasons/dimensions/composition/uncertainties/confidence/assumptions and canonical trace-step digest | UI order, colors, localized/AI prose, workers and execution timestamps |

`mapping_snapshot_digest` refines the Phase 7.1 mapping-state digest for this
domain and may be embedded in the execution input digest rather than duplicated
as another top-level execution boundary.

```text
same ingredient identity snapshot
+ same mapping snapshot
+ same substance profile digests
+ same protocol/versioned projection policies
→ same ingredient scientific projection and digest
```

Set-like mapping and substance entries are sorted by stable semantic keys.
Database row order, concurrency schedule and presentation never affect output.

## Edge-case behavior

| # | Case | Eligibility/state | Carries / blocked | New uncertainty | Allowed / forbidden conclusion | Historical behavior |
|---:|---|---|---|---|---|---|
| 1 | Exact `represents` | Eligible; `direct_projection` | Scoped endpoint/profile dimensions / exposure-risk blocked | Mapping target context | Ingredient represents substance for profile / no ingredient risk | Frozen mapping replays |
| 2 | Ambiguous `equivalent_to` scope | `projection_unresolved` | Mapping link only / scientific carryover blocked | Relationship/equivalence uncertainty | Equivalence requires review / no total identity | Later review creates refresh/counterfactual |
| 3 | `contains`, quantity unknown | `qualitative_association` | Presence-scoped association / magnitude blocked | Composition uncertainty | Contains associated substance / no concentration or risk | Historical assertion retained |
| 4 | `contains`, quantity known | `qualified_projection` if governed | Association plus quantity metadata / exposure-risk still blocked | Scenario/exposure uncertainty | Quantity under stated basis / no risk | Quantity snapshot frozen |
| 5 | Mixture component, fraction unknown | `qualitative_association` | Component link / fraction and mixture hazard blocked | Mixture-fraction uncertainty | Substance is component / no dose | Historical component state retained |
| 6 | Mixture component, known range | Qualified if reviewed | Range metadata and scoped component profile / whole-mixture inference blocked | Interaction/scenario uncertainty | Range under stated basis / no product risk | Range digest frozen |
| 7 | `derived_from`, no presence proof | `projection_blocked` for hazard; provenance-only | Derivation trace / presence-dependent dimensions blocked | Residual/transformation uncertainty | Derived from source / source currently present forbidden | Future evidence causes refresh |
| 8 | Substance-form mismatch | `projection_blocked` | Identity/provenance only / endpoint carryover blocked | Form incompatibility | Forms differ materially / no interchangeability | Frozen form state retained |
| 9 | Accepted today, invalid in historical snapshot | Blocked for historical `as_of` | Historical mapping observation / profile transfer blocked | None if interval known | Mapping not effective then / no current-row substitution | Replay remains unchanged |
| 10 | Closed/superseded mapping | Eligible only inside interval | Historical profile in interval / current projection blocked | Successor-scope uncertainty if missing | Mapping was effective in stated interval | Closure preserved |
| 11 | Rejected mapping | `projection_blocked` | Rejection reason / no profile | None or review-scope uncertainty | Candidate rejected / substance absence not proven | Decision retained |
| 12 | No mapping | `projection_blocked` | No scientific profile | Mapping gap | No mapping available / no danger or safety | New mapping requires refresh |
| 13 | Two substances both `contains` | Two qualitative/qualified entries | Separate profiles / combined conclusion blocked | Composition per entry | Two associations / no sum or worst-case | Canonical order stable |
| 14 | One `represents`, one `contains` | Direct entry plus qualitative entry | Each relationship scope / cross-entry aggregation blocked | Contains composition uncertainty | Separate associations / no unified score | Both histories frozen |
| 15 | Unresolved candidate mapping | `projection_unresolved` | Candidate identities in trace / no chosen profile | Mapping identity uncertainty | Review required / no worst candidate selection | Resolution creates new snapshot |
| 16 | QPS on represented substance | Eligible regulatory association | QPS context separately / safety claim blocked | Qualification applicability | QPS status/qualification applies in scope / ingredient safe forbidden | Release and mapping frozen |
| 17 | OpenFoodTox profile through `contains` | Qualitative/qualified association | Toxicology profile reference / magnitude and risk blocked | Presence/composition/form | Substance evidence associated / ingredient risk forbidden | Evidence and mapping snapshots frozen |
| 18 | High substance confidence, low mapping certainty | Unresolved/qualified | Substance profile retained / strong projection confidence blocked | Mapping uncertainty | Evidence confidence is high for substance / ingredient certainty not inherited | Historical basis retained |
| 19 | Low substance confidence, certain mapping | Eligible mapping; qualified result | Low-confidence substance state / stronger conclusion blocked | Upstream evidence uncertainty | Mapping certain / scientific conclusion remains limited | Upstream profile immutable |
| 20 | Mapping corrected after execution | Historical state unchanged | Original projection in replay / corrected mapping excluded from replay | None if snapshots complete | Current refresh may differ / historical result not overwritten | New refresh records correction |

## Conceptual deterministic projection vectors

Digest expectations are equality/difference requirements, not literal hashes.
Unless varied explicitly, ingredient/substance identities are resolved, the
substance profile is immutable, and upstream uncertainty is carried unchanged.

| # | Ingredient / mapping / relationship | Substance profile / composition | Expected state and reasons | Added uncertainty / trace | Digest expectation |
|---:|---|---|---|---|---|
| 1 | Active ingredient; accepted/materialized valid `represents` | Compatible form; composition unknown | `direct_projection`; `projected_direct_represents` | Mapping target scope; full mapping→profile trace | Same inputs reproduce digest |
| 2 | Accepted `equivalent_to`; no equivalence kind | Profile available; composition N/A | `projection_unresolved`; `unresolved_equivalence_scope` | Relationship uncertainty; review gap traced | Reviewed scope changes future digest |
| 3 | Accepted `equivalent_to`; reviewed chemical/form/question scope | Compatible profile | `direct_projection`; `projected_direct_equivalent_scope_reviewed` | Reviewed equivalence reference | Artifact/version committed |
| 4 | Valid `contains` | `presence_known_quantity_unknown` | `qualitative_association`; `projected_qualified_contains_presence_only` | Composition uncertainty | Stable under row reorder |
| 5 | Valid `contains` | `quantity_known` with governed basis | `qualified_projection`; `projected_qualified_contains_presence_only` | Exposure/scenario uncertainty | Quantity payload changes digest |
| 6 | Valid `mixture_component` | Fraction unknown | `qualitative_association`; `projected_qualified_mixture_component` | Mixture fraction/interaction uncertainty | Same mapping/profile stable |
| 7 | Valid `mixture_component` | Governed fraction range | `qualified_projection`; `projected_qualified_mixture_component` | Interaction/scenario uncertainty | Range/basis committed |
| 8 | Valid `derived_from` | No residual-presence data | `projection_blocked`; `blocked_derived_from_no_residual_presence` | Transformation/residual uncertainty | Adding evidence requires new digest |
| 9 | Valid `derived_from` | Reviewed residual compatible form/presence | `qualified_projection`; `projected_qualified_derived_from_residual_reviewed` | Residual amount/form uncertainty; residual artifact traced | Policy/evidence refs committed |
| 10 | Accepted mapping outside `as_of` | Profile available | `projection_blocked`; `blocked_mapping_not_valid_as_of` | None if boundary resolved | Different as-of changes mapping snapshot digest |
| 11 | Rejected proposal/row | Profile exists for candidate | `projection_blocked`; `blocked_mapping_not_accepted` | Review scope retained in trace | Rejection reason committed |
| 12 | No mapping member | Profile not associated | `projection_blocked`; `blocked_no_mapping` | Mapping gap | New mapping produces different refresh digest |
| 13 | Two unresolved candidates | Two possible profiles | `projection_unresolved`; `unresolved_multiple_candidate_mappings` | Identity/mapping uncertainty | Candidate order irrelevant |
| 14 | Two accepted `contains` mappings | Two profiles; quantities unknown | Two qualitative entries; each `projected_qualified_contains_presence_only`; no aggregation | Per-entry composition uncertainty and trace | Sorted entry order deterministic |
| 15 | One `represents` plus one `contains` | Two profiles | `projected_direct_represents` plus `projected_qualified_contains_presence_only` | Contains uncertainty only on its entry; both paths traced | No cross-entry aggregate digest content |
| 16 | `represents` to form-mismatched substance | Profile for other form | `projection_blocked`; `blocked_substance_form_incompatible` | Form uncertainty/known incompatibility | Form mapping change alters future digest |
| 17 | `represents`; form not represented | Profile available | `projection_unresolved`; `unresolved_substance_form` | Form uncertainty | Governed resolution changes digest |
| 18 | Represented QPS taxon | QPS regulatory component | Separate association; `associated_regulatory_context` | Qualification applicability | Regulatory component kept separate |
| 19 | Certain `represents`; conflicting/low-confidence substance endpoint | Upstream conflict/uncertainty; composition N/A | `direct_projection`; `projected_direct_represents`, carrying exact limited/conflict state | Upstream uncertainty unchanged; mapping path traced | Cannot strengthen result; same profile digest stable |
| 20 | Exact historical replay after mapping correction | Frozen old `represents` mapping/profile; composition N/A | Original `direct_projection` and `projected_direct_represents` reproduced | Current correction excluded from replay trace | Projection digest must equal baseline |

No vector emits an ingredient score, product score, exposure estimate, risk or
cross-substance scalar.

## Current-schema gap matrix

| Required concept | Status through local `0017` | Current representation / gap | Requirement |
|---|---|---|---|
| Mapping temporal state | Available/partial | Accepted rows with inclusive `DATE` intervals, closure history and as-of reader | Freeze membership; publish timezone/day boundary semantics |
| Relationship vocabulary | Available | Five validated string values | Versioned semantic definitions and scoped review artifacts |
| Relationship scientific semantics | Missing/review required | No per-row semantic scope beyond type/provenance | Protocol-specific relationship policy |
| Mapping confidence | Partial/unusable scientifically | Optional `[0,1]`, construct/calibration undefined | Define construct or retain as non-scientific metadata |
| Controlled acceptance state | Available/partial | Proposal, decision, materialization and closure; legacy accepted rows possible | Snapshot exact workflow/provenance state |
| Substance form/speciation | Missing | Coarse `substance_type`, names and identifiers only | Minimal versioned form compatibility model |
| Composition/fraction | Missing | No quantity, range, basis or unit on bridge | Governed composition object before quantitative projection |
| Presence evidence | Partial/missing | Relationship and provenance may assert scope; no general product/batch presence object | Explicit presence scope/evidence model |
| Transformation/residual state | Missing | `derived_from` has no fate/residual fields | Transformation/residual evidence object and review policy |
| Ingredient identity history | Partial | Current row/timestamps only; no immutable version history | Ingredient identity snapshot/frozen payload |
| Substance identity history | Partial | Identity review history exists, current substance row mutable | Freeze identity/form membership in execution |
| Mapping snapshot | Missing/future persistence | Can resolve rows as-of but no immutable manifest | Canonical mapping snapshot and digest |
| Projection decisions/results | Missing/future persistence | Documentation only | Immutable projection entries, trace and digest |

No migration or SQL schema is designed by this matrix.

## Implementation-readiness matrix

Classification describes logical maturity, not authorization.

| Future component | Classification | Reason |
|---|---|---|
| Accepted mapping snapshot reader | READY FOR IMPLEMENTATION | Repository has deterministic accepted/as-of query and canonical order |
| Historical mapping resolution | READY FOR IMPLEMENTATION | Inclusive interval and closure behavior are defined; timestamp convention must be explicit |
| Relationship-type dispatch skeleton | READY FOR IMPLEMENTATION | Vocabulary and conservative default states are defined |
| Projection decision envelope | READY FOR IMPLEMENTATION | States, dimensions and ownership are defined |
| Core reason-code production | READY FOR IMPLEMENTATION | State/provenance/time reasons are deterministic |
| Trace and digest envelopes | READY FOR IMPLEMENTATION | Canonical inputs, ordering and exclusions are defined |
| Governed legacy accepted-row eligibility | BLOCKED BY DATA MODEL | Materialization/scope may be absent for pre-0017 rows |
| Composition-aware projection | BLOCKED BY DATA MODEL | Quantity/range/unit/basis are missing |
| General substance-form compatibility | BLOCKED BY DATA MODEL | Form/speciation model and mappings are missing |
| `equivalent_to` direct scientific projection | BLOCKED BY SCIENTIFIC REVIEW | Equivalence kind/scope is unrepresented and unvalidated |
| `contains` conclusion-transfer policy | BLOCKED BY SCIENTIFIC REVIEW | Presence scope and permitted hazard wording require review |
| Mixture component scientific handling | BLOCKED BY SCIENTIFIC REVIEW | Fractions, interactions and mixture method unvalidated |
| `derived_from` residual transfer | BLOCKED BY SCIENTIFIC REVIEW | Transformation/residual semantics require domain evidence |
| Confidence propagation vocabulary | BLOCKED BY SCIENTIFIC REVIEW | Representation constraint exists; no approved framework |
| Multi-substance structured collection | READY FOR IMPLEMENTATION | Separate entries/canonical order/no aggregation are defined |
| Exposure/product assessment envelopes | READY FOR IMPLEMENTATION | Phase 7.5 defines composition/exposure readiness and risk-computability states; actual calculation remains review/data blocked |
| Persistence/API/runtime rollout | DEFERRED | Later persistence, validation and rollout phases |

## Scientific-review boundaries

| Area | Classification | Rationale |
|---|---|---|
| Relationship-aware dispatch and no uniform link semantics | ARCHITECTURALLY APPROVED | Prevents category errors |
| Accepted/as-of mapping requirement and immutable replay | ARCHITECTURALLY APPROVED | Historical determinism boundary |
| Structured non-scalar projection set | ARCHITECTURALLY APPROVED | Preserves multi-substance traceability |
| No cross-substance aggregation, exposure or risk inference | ARCHITECTURALLY APPROVED | Required input/construct separation |
| Additive uncertainty and non-increasing confidence constraint | ARCHITECTURALLY APPROVED | Prevents unsupported strengthening; calculation remains reviewed |
| QPS regulatory channel separation | ARCHITECTURALLY APPROVED | Preserves Phase 7.3 semantic role |
| `equivalent_to` scientific scope | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Chemical/functional/regulatory/label equivalence differ |
| Substance-form interchangeability and cross-form transfer | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Endpoint meaning may change with form/speciation |
| `contains` projection limits and claim wording | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Presence does not define magnitude/applicability |
| Mixture composition/interactions | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Component evidence is not whole-mixture evidence |
| `derived_from` residual presence/transfer | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Transformation can remove/change source substance |
| Confidence vocabulary/propagation method | REQUIRES EXTERNAL SCIENTIFIC REVIEW | No formula or qualitative scale validated |
| Form, composition, presence and residual data | DATA GAP | Not generally represented through `0017` |
| Projection persistence/snapshot documents | DATA GAP | No Phase 7 storage exists |
| Exposure readiness and product assessment | DEFINED IN 7.5 / REVIEW AND DATA REQUIRED | `WYE_PRODUCT_ASSESSMENT.md` preserves separate entries and does not infer exposure/risk |
| Runtime/persistence/API/rollout | DEFERRED | Later roadmap checkpoints |

## Phase 7.4 exit criteria

- [x] Current mapping model, fields, states and history audited.
- [x] Five relationship-type semantics defined separately.
- [x] Projection eligibility pipeline and states defined.
- [x] `represents` direct-projection boundary defined.
- [x] `equivalent_to` scope gap and reviewed behavior defined.
- [x] `contains` qualitative presence/composition boundary defined.
- [x] `mixture_component` fraction/readiness boundary defined.
- [x] `derived_from` provenance-only default defined.
- [x] Minimal substance-form compatibility model defined.
- [x] `ingredient_scientific_projection` object and naming defined.
- [x] Projected, qualified and blocked dimensions defined.
- [x] Projection-induced uncertainty taxonomy defined.
- [x] Confidence and mapping-confidence separation defined.
- [x] Current/replay/counterfactual/refresh mapping semantics defined.
- [x] Multi-substance structured collection defined without aggregation.
- [x] Ambiguous, rejected, closed and absent mapping behaviors defined.
- [x] Hybrid versioned projection reason codes defined.
- [x] Composition readiness states defined.
- [x] Direct versus qualified projection defined.
- [x] Cross-substance aggregation explicitly excluded.
- [x] Regulatory-context projection separated from toxicology.
- [x] Ingredient explanation trace defined.
- [x] Mapping/projection digest model defined.
- [x] Twenty edge cases analyzed.
- [x] Twenty deterministic conceptual vectors defined.
- [x] Current-schema gaps documented.
- [x] Implementation readiness classified.
- [x] Scientific-review boundaries classified.

## Roadmap and next checkpoint

The Phase 7 roadmap remains unchanged. Phase 7.4 introduces no reason to reorder
Phases 7.5–7.9.

The proposed next checkpoint is:

```text
Phase 7.5 — Exposure Readiness and Product Assessment Semantics
```

It should define the data sufficiency boundary for concentration, quantity,
amount/use, frequency, duration, route, target population and scenario; separate
hazard-only product views from exposure/risk; and make `risk_not_computable` a
first-class outcome. It must not invent missing exposure or begin runtime work.

Phase 7.5 is defined in `WYE_PRODUCT_ASSESSMENT.md` without changing this
projection contract. It consumes only frozen projection entries and preserves
their separate scope, uncertainty and non-aggregation boundary.

Phase 7.6 now defines the canonical mapping-snapshot and ingredient-projection
artifact envelopes in `WYE_SCORING_PERSISTENCE.md`. Historical mappings and
separate substance projections are digest-bound and immutable; physical query
projections remain rebuildable. Composition/form scientific gaps are unchanged.
