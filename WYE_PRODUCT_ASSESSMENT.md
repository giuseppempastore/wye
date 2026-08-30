# WYE — Exposure Readiness and Product Assessment Contract

## Status and scope

This document is the canonical Phase 7.5 specification for determining whether
frozen ingredient scientific projections and product data are sufficient to
support exposure assessment or risk characterisation. It specializes, but does
not replace:

- `Checkpoints/WYE_PHASE_7.md`;
- `WYE_SCORING_SEMANTICS.md`;
- `WYE_SCORING_PROTOCOL.md`;
- `WYE_SCORING_EXECUTION_MODEL.md`;
- `WYE_EVIDENCE_SELECTION.md`;
- `WYE_EVIDENCE_SYNTHESIS.md`;
- `WYE_INGREDIENT_PROJECTION.md`.

Phase 7.5 defines readiness, computability and non-computability contracts. It
does not implement persistence, runtime exposure calculation, reference-point
comparison, risk characterisation, an API, a product score, formulas, weights,
thresholds or numerical health/safety/risk output.

Review baseline:

```text
branch: ingredients_score
HEAD: 7a8a6acf72a5c5d4e1eda85e85fb868254a95f23
origin/ingredients_score: 7a8a6acf72a5c5d4e1eda85e85fb868254a95f23
working tree before Phase 7.5: clean
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017_ingredient_mapping_history
```

The canonical Phase 7 documents, migrations through `0018`, product and label
schema, extraction contracts, product-ingredient materialization services and
local aggregate data state were reviewed. Database inspection used a read-only
transaction. No database state was changed.

## Non-negotiable boundaries

```text
hazard != exposure != risk
presence != concentration
concentration != consumed dose
serving size != actual intake
ingredient order != concentration
unknown exposure != high exposure
missing exposure != danger
worst-case assumption != default scientific conclusion
product contains substance != product is risky
absence of evidence != evidence of danger
```

```text
risk requires exposure context
no sufficient exposure context → risk_not_computable
```

`risk_not_computable` is a valid epistemic product-assessment result. It is not
a technical failure, a risk category or a fallback score.

## Audit of the current product and composition model

### Product identity

`products` currently stores `id`, barcode/GTIN, brand and product name,
category/type, source, verified flag, integer `version`, lifecycle status and
created/updated timestamps. Local data contain ten active products, all with
`version=1`.

The row is mutable and there is no immutable product-version table or governed
history of name, brand, category, formulation or verification. The `version`
field does not by itself preserve prior semantic states. Product identity is
therefore available for current traversal but only partially ready for replay.

### Product ingredient list

`product_ingredients` stores product and optional canonical ingredient,
`raw_name`, `canonical_name`, `position_in_list`, legacy confidence/flags,
creation time, optional extraction-item provenance, normalized text/language,
mapping method/status and JSON provenance.

The Phase 5 path can materialize one row per ingredient extraction item and
preserves the label order. An extracted ingredient `quantity` is copied as an
opaque `extracted_quantity` value in mapping provenance. It is not parsed into a
canonical amount, fraction, range, unit or basis and acceptance of ingredient
identity does not validate its quantity semantics.

Local reality is more limited:

```text
product_ingredients: 27
all mapping_status: legacy_unreviewed
all mapping_method: legacy
rows linked to label_extraction_item: 0
rows with mapping_provenance: 0
rows with extracted_quantity: 0
```

There is no composition-level current/superseded flag, validity interval or
immutable product-ingredient snapshot. Rows have creation time but not a
complete formulation lifecycle.

### Product images and label provenance

The schema can preserve product images by type, checksum, storage object,
capture time, status and same-product/type supersession chain. It also provides:

```text
product_label_documents
→ label_extraction_runs
→ label_extraction_items
```

Extraction runs record method/provider/model/prompt/schema versions, prompt and
request fingerprints, raw response, status and timing. Items retain raw text,
structured JSON, unit, document position, confidence and validation status.
This is a strong provenance envelope, but a detected AI-derived item is not
silently canonical scientific input.

Local counts for images, label documents, extraction runs and extraction items
are all zero. The capability exists in schema/code but no local canonical
composition can currently be reconstructed through this path.

### Ingredient quantity and percentage

The versioned extraction model supports an optional ingredient `quantity` as a
string, and syntax normalization preserves percentages in raw/normalized
ingredient text. There is no governed parser that separates amount, percentage,
range, qualifier, unit and product basis into canonical fields. These values are
therefore `extracted_but_not_canonical`, not exposure-ready quantities.

### Nutrition and serving information

`nutrition_facts` stores one free-text `serving_size`, nutrient-specific numeric
columns, source/verification flags, raw text and timestamps. The versioned label
extraction contract is richer at item level: a nutrition item can record a
basis of `per_100_g`, `per_100_ml`, `per_serving` or `other`, with optional
quantity, unit and raw text.

Limitations:

- nutrition rows describe nutrients, not ingredient- or substance-specific
  composition;
- the legacy product-create path can write `serving_size='100g'` and mark the
  row verified without a Phase 7 extraction/review artifact;
- that path replaces prior `nutrition_facts` rows rather than preserving a full
  serving/formulation history;
- there is no servings-per-container or actual-intake model.

The local DB contains five nutrition rows, all with `serving_size='100g'`, four
with source `photo_submission` and one `manufacturer`. Their flags and text are
insufficient to establish Phase 7 canonical serving or exposure provenance.

### Product/composition readiness summary

| Information | Current classification | Repository reality |
|---|---|---|
| Product identity | Available, partially historical | Stable row ID/barcode/GTIN and timestamps; mutable row, no immutable versions |
| Ingredient list | Available | Raw/canonical name, accepted state where materialized, and list position |
| Ingredient order | Available as ordinal | `position_in_list`; no quantitative semantics |
| Ingredient quantity/percentage | Extracted but not canonical, absent locally | Optional opaque extraction string/provenance |
| Substance quantity/fraction | Missing | No product/ingredient/substance composition model |
| Nutrition table | Partially available | Legacy table plus structured extraction contract; nutrient-specific only |
| Serving/reference basis | Partially available | Free-text legacy value or per-item extraction basis; no canonical serving history |
| Servings per container | Missing | No field/model |
| Portion/actual consumed amount | Missing | No canonical observation or scenario |
| Net quantity | Missing | No canonical field/model |
| Preparation/use instructions | Missing | No canonical field/model |
| Usage frequency/duration | Missing | No canonical field/model |
| Product formulation history | Not historically versioned | Images can be superseded; composition cannot be replayed completely |

Legacy `product_scores`, legacy risk fields and the legacy product-create
defaults are excluded from Phase 7 scientific inputs.

## Exposure terminology

| Concept | Meaning and required context | Does not imply |
|---|---|---|
| `concentration` | Amount of a substance per stated product/formulation amount or volume, with numerator/denominator units and material state | Consumed dose, actual intake or risk |
| `amount_per_product` | Total substance or ingredient amount in one identified product/package, with package identity and unit | Amount consumed or applied |
| `amount_per_serving` | Amount tied to one explicit serving definition and product preparation state | One serving is actually consumed |
| `consumed_amount` | Product or substance amount ingested in a defined event/period, observed or explicitly assumed | Absorption, systemic dose or repeated exposure |
| `applied_amount` | Product/substance amount used externally in a defined event | Ingested dose or target-tissue amount |
| `frequency` | Number/pattern of exposure events per defined time basis | Duration or lifetime pattern |
| `duration` | Period over which the stated exposure pattern applies | Frequency, chronicity class or biological persistence without reviewed mapping |
| `route` | Path of contact/intake, explicitly represented or protocol-governed | Route equivalence or bioavailability |
| `population` | Defined target group to which scenario and reference context apply | Validity for every subgroup |
| `body_weight_context` | Measured or governed body-weight basis, population statistic and provenance | User identity, clinical suitability or automatic dose conversion |
| `use_scenario` | Coherent product state, population, route, amount, frequency, duration, preparation and assumptions | Observed behavior unless provenance says so |
| `exposure_estimate` | Protocol-produced amount/concentration reaching a stated target under one scenario, with units, basis and uncertainty | Risk, safety probability or actual individual exposure |

Terms must retain explicit unit, denominator/basis, time basis, product state,
scenario provenance and assumption status wherever material.

## Composition readiness at product level

Composition is evaluated separately for every ingredient/substance projection:

| State | Meaning | Permitted use |
|---|---|---|
| `product_composition_unknown` | Product formulation/presence cannot be frozen adequately | Identity/provenance gap only |
| `ingredient_presence_known` | Listed/validated ingredient presence is known; no quantity | Presence-scoped association only |
| `ingredient_presence_and_order_known` | Presence plus canonical ordinal label position is known | Ordinal description only |
| `ingredient_quantity_range_known` | Governed ingredient quantity/fraction range, unit, basis and provenance exist | Range-aware readiness; no substance quantity unless fraction is known |
| `ingredient_quantity_known` | Governed ingredient amount/fraction and basis exist | Ingredient amount derivation input only |
| `substance_presence_known_quantity_unknown` | Substance presence follows an eligible projection; amount/fraction absent | Qualitative association only |
| `substance_quantity_range_known` | Governed substance amount/concentration range and basis exist | Range-aware exposure input after scenario checks |
| `substance_quantity_known` | Governed substance amount/concentration and basis exist | Exposure input after route/intake/time checks |
| `composition_not_applicable` | Requested scenario/relationship is genuinely non-compositional | No quantity inference |
| `composition_unresolved` | Extracted values exist but parsing, basis, identity or validation is unresolved | Preserve candidates; do not calculate |

`ingredient_presence_and_order_known` is not an intermediate numeric
concentration. No hidden ordinal-to-quantity conversion is allowed.

## Ingredient-order semantics

Product label order is retained as source-derived ordinal information. Whether
a particular jurisdiction, product category and label date require descending
weight order is a regulatory applicability question and must be supplied by a
versioned, externally reviewed rule with exceptions and provenance.

Even where descending-order law applies:

```text
first ingredient != known percentage
last ingredient != trace amount
position_in_list != concentration
```

Order may support only statements about declared ordinal position and possibly
reviewed inequality constraints under a future protocol. It cannot establish an
exact amount, substitute for a missing concentration or rank hazard/risk.

## Serving and intake semantics

The model separates:

| Serving concept | Meaning |
|---|---|
| `label_serving` | Serving declared on the frozen label with source provenance |
| `standard_reference_serving` | Regulatory/scientific reference quantity under a versioned authority and scope |
| `user_specific_serving` | Explicit amount supplied for a particular assessment, not medical advice |
| `observed_intake` | Measured/recorded consumption with method and time provenance |
| `assumed_intake` | Explicit model assumption under a reviewed protocol |
| `actual_consumed_amount` | Observed amount in the assessed event/period; not inferred from label serving |

A label serving and `per_serving` nutrient basis do not establish that a person
consumes exactly one serving. Serving size, servings per package and intake are
different dimensions.

## Exposure scenario model

The logical object is:

```text
exposure_scenario
├── scenario key, schema version and digest
├── product composition snapshot reference
├── scenario type and provenance type
├── target population and applicability scope
├── route and route basis
├── product/ingredient/substance amount inputs
├── serving/reference/actual-intake basis
├── frequency and time basis
├── duration
├── body-weight basis, only when required
├── product preparation/use state
├── observation and assumption status per field
├── governing protocol/rule/review artifacts
├── missing/unresolved dimensions
└── scenario uncertainty and trace references
```

Scenario provenance is one of:

```text
label_derived
user_provided
regulatory_reference
scientifically_approved_default
model_assumption
observed_intake
```

Every value records its own provenance; a scenario with mixed sources does not
inherit one blanket trust level. User-provided is not observed, label-derived is
not actual intake, and model assumption is never rendered as measured fact.

### No-silent-default policy

```text
no silent default assumptions
```

A future default must freeze protocol version, scientific rationale, domain and
population scope, provenance, review status, uncertainty and rule reference.
Without an approved default, missing data remain missing. A conservative or
worst-case scenario is allowed only as an explicitly named, governed scenario;
it is never the canonical conclusion for unknown exposure.

## Route, population, frequency and duration

### Route

Route state is `explicit`, `domain_implied`, `protocol_assumed`, `unknown` or
`not_applicable`. A food category alone does not silently force `oral`.
`domain_implied` or `protocol_assumed` oral route requires an externally reviewed
rule proving that product intended use and preparation scope exclude material
other uses. The rule and assumption remain visible in the trace.

### Population

The minimal representational vocabulary is:

```text
general_population
children
infants
pregnancy
specific_vulnerable_group
user_specific_population
unknown_population
```

These are envelopes, not approved medical or regulatory subclasses. Definitions,
age bounds and transfer rules require review. General-population hazard or
exposure context does not automatically apply to every subgroup.

### Frequency and duration

Frequency may be represented as a stated event pattern such as single, daily,
weekly, episodic, repeated or unknown, always with its exact source term and
time basis. Duration separately records the scenario period.

`acute`, `chronic` and related scientific duration classes require versioned
external definitions. Phase 7.5 does not introduce temporal thresholds or infer
a class from plain-language frequency.

## Exposure basis and unit readiness

Exposure quantities retain their basis:

```text
absolute_amount
concentration
amount_per_product
amount_per_serving
amount_per_day_or_other_period
amount_per_body_weight_and_period
```

No conversion occurs between incompatible bases. Unit readiness is:

| State | Meaning |
|---|---|
| `unit_known` | Unit and basis are explicit but no conversion is requested |
| `unit_convertible` | A versioned unit system proves compatible dimensions and deterministic conversion |
| `unit_context_incomplete` | Unit is known but denominator/product/time context is missing |
| `dose_basis_incomplete` | Amount lacks the basis required by hazard/reference context |
| `unit_ambiguous` | Source notation permits multiple interpretations |
| `unit_incompatible` | Dimensions/bases cannot be compared for the requested operation |
| `unit_not_applicable` | The component is intentionally non-quantitative |

A numeric value is not usable merely because its unit string is present.
Conversion requires unit, dimensional basis, product state, time basis and
protocol-approved semantics.

## Substance-amount derivation

A future derivation is structurally possible only when all of the following are
canonical and mutually compatible:

- product or serving amount;
- ingredient amount/fraction on the same basis;
- substance fraction/composition within that ingredient;
- form and relationship compatibility;
- units, qualifiers and range semantics;
- source/review provenance and scenario state;
- a protocol-approved dimensional transformation.

The derived amount retains every input, operation rule, range/precision policy
and uncertainty in the trace. It is not stored as an unexplained number.

```text
ingredient quantity known
+ substance fraction unknown
→ substance quantity unknown
```

The system never assumes the ingredient is 100% of the mapped substance. An
exact `represents` identity may permit such a relation only when a reviewed
composition/form policy explicitly establishes it for that product state.

### Mixtures and derivation relationships

For `contains` and `mixture_component`, `known concentration`, `known range`,
`provided upper bound` and `unknown fraction` are distinct. A supplied upper
bound remains an upper-bound scenario, not a central/default estimate. No upper
bound is invented.

`derived_from` remains non-computable for exposure unless residual presence,
residual form and amount/range are governedly established:

```text
derived_from without residual presence/quantity
→ exposure_not_computable_for_derived_substance
```

## Exposure uncertainty

Exposure uncertainty is additional to upstream hazard and projection
uncertainty:

| Type | Source and propagation |
|---|---|
| `composition_uncertainty` | Ingredient/substance fraction or formulation ambiguity; affects amount and exposure |
| `serving_uncertainty` | Serving definition, basis or preparation ambiguity; affects scenario amount |
| `intake_uncertainty` | Difference between declared/assumed and actual consumption; affects exposure estimate |
| `frequency_uncertainty` | Missing/variable event pattern; affects time-based exposure |
| `duration_uncertainty` | Missing/variable exposure period; affects hazard/reference compatibility |
| `population_uncertainty` | Population identity or transfer ambiguity; affects applicability |
| `route_uncertainty` | Explicit/implied route ambiguity; affects exposure and hazard compatibility |
| `body_weight_uncertainty` | Missing, assumed or variable body-weight basis; affects body-weight-normalized output |
| `preparation_uncertainty` | Dilution, cooking, reconstitution or use-state ambiguity; affects composition/amount |
| `scenario_uncertainty` | Structural/model assumptions or mixed provenance; affects the scenario conclusion |

Each item uses the Phase 7 uncertainty envelope and states source, scope,
direction if known, impact, reducibility, required data/action and whether it
blocks or qualifies exposure/risk.

## Exposure-readiness state model and contract

Readiness separates data availability from scientific usability. The canonical
state is one of:

| State | Meaning |
|---|---|
| `exposure_ready` | All protocol-required amount/composition, scenario, unit/basis and compatibility gates are satisfied with governed provenance |
| `exposure_ready_qualified_scenario` | Calculation inputs are structurally complete but include explicit reviewed assumptions/ranges that must qualify any result |
| `exposure_partially_ready` | Some usable dimensions exist, but one or more required inputs block exposure estimation |
| `exposure_not_ready` | Critical composition/scenario inputs are absent or unusable |
| `exposure_unresolved` | Candidate values/mappings exist but canonical meaning or governance is unresolved |
| `exposure_not_applicable` | The declared question legitimately requires no exposure assessment |

Missing dimensions such as concentration, intake, frequency, duration, route or
population are reason codes/dimension states, not mutually exclusive top-level
states.

The deterministic decision pipeline is:

```text
frozen product composition and identity
→ eligible ingredient scientific projections
→ ingredient/substance quantity readiness
→ exposure scenario and provenance
→ route/population/frequency/duration readiness
→ unit, dose-basis and form compatibility
→ exposure-readiness decision
→ separate risk-computability gate
```

Stages may preserve independent dimension outcomes, but finalization waits for
all required gates. A skipped stage is recorded as not evaluated due to the
earlier blocking stage rather than inferred.

The logical object is:

```text
exposure_readiness_assessment
├── readiness key, schema version and digest
├── product identity/composition snapshot and digests
├── ingredient scientific projection references/digests
├── exposure scenario and digest
├── composition and substance-quantity states
├── route, population, frequency and duration states
├── unit and dose-basis readiness
├── hazard/reference compatibility readiness
├── missing and unresolved dimensions
├── carried and exposure-specific uncertainty
├── readiness state and reason codes
├── assumptions and forbidden interpretations
└── deterministic trace reference
```

## Risk-computability gate

Risk characterisation may proceed to a future reviewed engine only when the
same scoped question has:

```text
compatible hazard characterisation/reference context available
+ eligible ingredient-to-product projection
+ sufficient product/substance composition
+ sufficient exposure scenario
+ compatible endpoint, route, duration, population, unit, basis and form
+ protocol-approved risk/reference semantics
→ risk_characterisation_may_proceed
```

If any required gate fails, the product result is `risk_not_computable` with
all blocking reasons. If the gate cannot be classified because candidate
semantics are unresolved, it is `risk_computability_unresolved`. Genuine
non-applicability is separate.

| Gate state | Meaning |
|---|---|
| `risk_characterisation_may_proceed` | Every required data and compatibility gate passes under a published reviewed risk protocol |
| `risk_not_computable` | At least one deterministic required gate fails |
| `risk_computability_unresolved` | Canonical input meaning/review is unresolved |
| `risk_not_applicable` | Risk characterisation is genuinely outside the declared question |

The gate authorizes no calculation in Phase 7.5 and expresses no risk level.
Reference-point availability is not permission to use it; compatibility and a
reviewed interpretation policy are required.

### `risk_not_computable`

```text
risk_not_computable != low risk
risk_not_computable != high risk
risk_not_computable != product safe
risk_not_computable != product dangerous
```

It means only that this protocol, product snapshot and scenario lack a complete,
scientifically compatible basis for the requested risk characterisation. Hazard
information and ingredient associations may remain available as separately
named components.

```text
technical execution failure != risk_not_computable
```

A database/engine failure produces no completed canonical scientific result;
non-computability is a successfully completed semantic assessment with reasons.

## Canonical product-level object and naming

The canonical name is:

```text
product_scientific_assessment
```

It is preferred because one result can report evidence associations, hazard
context, exposure readiness and non-computability without pretending to be a
risk, health or safety score.

```text
product_scientific_assessment
├── assessment key, schema version and digest
├── product identity and composition snapshot
├── protocol, evidence and mapping snapshot references
├── ingredient scientific projections[]
├── exposure scenario sub-results[]
│   ├── exposure readiness assessment
│   ├── exposure estimate, only in a future authorized protocol
│   └── risk computability state
├── scientific dimensions[]
├── missing-data summary
├── hazard/evidence uncertainty
├── projection uncertainty
├── composition/exposure/reference uncertainty
├── conflict summary
├── assumptions and forbidden claims
└── canonical explanation trace
```

There is no central `product_score`, `risk_score`, `health_score` or
`safety_score`.

## Product-level output and aggregation boundaries

These outputs remain separately typed:

```text
ingredient evidence association
hazard-related information
regulatory context
exposure readiness
exposure estimate
risk characterisation
nutrition assessment
allergy assessment
```

Availability of one type cannot silently fill another. Phase 7.5 performs no:

```text
worst ingredient wins
sum of hazards
average hazards
maximum risk
cross-substance mixture inference
composite product score
```

The normal product output is a structured collection of ingredient projections,
scenario-specific readiness states and risk-computability states. Every
ingredient/substance/scenario remains separately traceable.

## Multiple scenarios and generic/user-specific boundary

The same product may have different serving, population, route, frequency,
duration or preparation scenarios. Each scenario produces an independently
keyed sub-result. A protocol may publish one assessment bundle containing a
canonically sorted scenario set or one execution per scenario, but it must
choose one identity rule before publication. No scenario overwrites another.

A `generic_product_assessment` may use only label data and explicitly approved
reference scenarios. A `user_specific_exposure_assessment` includes
user-supplied scenario inputs and is a different target/context digest. Phase
7.5 defines no diagnosis, personalized medical recommendation or clinical
fitness rule.

## Historical semantics and product composition snapshot

The logical `product_composition_snapshot` is a hybrid frozen manifest:

```text
product_composition_snapshot
├── product identity/status/version payload
├── as_of and snapshot boundary semantics
├── selected product images and checksums
├── label documents and source provenance
├── extraction runs, prompt/schema/model versions and fingerprints
├── extraction items and validation/review states
├── product ingredients, raw order and mapping state
├── declared ingredient quantities/ranges and validation state
├── nutrition facts and per-item basis
├── serving, net quantity and preparation/use metadata
├── manual correction/review artifacts
├── missing/unresolved composition observations
└── canonical composition snapshot digest
```

Current schema can supply some members, but complete immutable composition and
serving history is missing.

| Execution mode | Product/scenario behavior |
|---|---|
| `NORMAL` | Resolve current governed product/composition, ingredient mappings, substance profiles and selected scenario; freeze them before assessment |
| `REPLAY` | Reuse exact historical product composition, mappings, profiles, scenario, protocol and governed artifacts; query no mutable current value |
| `COUNTERFACTUAL` | Reuse historical composition, mappings, profiles and scenario; apply a different compatible protocol version |
| `REFRESH` | Freeze a new product formulation/label, serving/scenario, mapping/profile or evidence state into a new immutable assessment |

A changed serving size or formulation never alters a historical result. A new
scenario with the same product snapshot is a new semantic input and distinct
sub-result/execution according to the published bundling rule.

## Label data provenance and AI boundary

Every label-derived exposure input must traverse:

```text
product image/storage object/checksum
→ label document
→ extraction run, provider/model/prompt/schema/fingerprint
→ extraction item and raw text
→ normalization/validation/manual review artifact
→ canonical composition or scenario field
```

`extraction_status=detected`, provider confidence or an accepted ingredient
identity mapping does not by itself validate amount, basis or serving semantics.
AI may transcribe candidates under the existing governed pipeline, but cannot
silently create canonical quantities, assumptions, exposure results or risk
conclusions.

## Nutrition, allergy and regulatory/reference boundaries

```text
nutrition assessment != toxicological risk assessment
allergen presence != general toxicological hazard
```

Nutrition facts may provide product quantity/reference-basis evidence only when
the exact field is semantically applicable. Aggregate nutrient values do not
establish the quantity of a named ingredient or mapped substance. Nutrition and
allergy require separate protocol families and cannot be merged into this
toxicological product assessment.

No ADI, TDI, UL, reference dose or regulatory limit is selected in Phase 7.5.
A future exposure-to-reference comparison requires protocol-approved reference
semantics and compatibility of:

```text
endpoint/reference meaning
route
duration
population
unit and dose basis
substance identity/form
scenario and applicability scope
```

Two numeric values are not comparable merely because units can be converted.

## Uncertainty and confidence at product level

The product result preserves distinct layers:

```text
hazard/evidence uncertainty
projection uncertainty
composition uncertainty
exposure uncertainty
reference-point uncertainty
risk-model uncertainty
```

No downstream layer cancels an upstream limitation. Equivalent uncertainty
items may share a semantic reference but remain attached to all affected
components.

Product-assessment confidence is confidence in one exactly worded conclusion,
such as an exposure-readiness or non-computability statement. It is not the
probability that the product is safe. Phase 7.5 defines the representation and
non-strengthening constraint only; no formula or qualitative scale is approved.

## Versioned reason-code taxonomy

The hybrid vocabulary is:

- `wye_exposure_core/v1` for product identity, provenance, composition,
  scenario and unit/readiness reasons;
- `food_tox_exposure/v1` for route/population/reference and toxicological
  compatibility reasons.

All codes have immutable definition, decision stage, required context,
deterministic basis, resolvability and rule reference.

### Readiness reasons

| Code | Meaning |
|---|---|
| `ready_complete_exposure_context` | Every required composition, scenario, unit and compatibility dimension is governed and usable |
| `ready_qualified_scenario` | Inputs are complete under explicit reviewed assumptions/ranges |
| `partial_exposure_context` | Some usable dimensions exist but at least one required dimension blocks calculation |
| `not_applicable_exposure_question` | Exposure is genuinely outside the declared question |

### Core blocking/unresolved reasons

| Code | Meaning |
|---|---|
| `blocked_product_snapshot_unavailable` | Product identity/composition cannot be frozen |
| `blocked_missing_ingredient_projection` | Required ingredient scientific projection is absent/ineligible |
| `blocked_missing_composition` | Product/ingredient composition required by the question is absent |
| `blocked_missing_concentration` | Required ingredient/substance concentration and denominator basis are absent |
| `blocked_missing_substance_quantity` | Substance amount/concentration cannot be established |
| `blocked_missing_serving_basis` | Required serving/reference basis is absent |
| `blocked_missing_intake_amount` | Consumed/applied amount is absent |
| `blocked_missing_frequency` | Required exposure frequency is absent |
| `blocked_missing_duration` | Required exposure duration is absent |
| `blocked_missing_route` | Required route is absent |
| `blocked_missing_population` | Required target population is absent |
| `blocked_missing_body_weight_basis` | Required body-weight context is absent |
| `blocked_missing_preparation_state` | Required preparation/use state is absent |
| `blocked_incompatible_units` | Value dimensions/bases are incompatible |
| `blocked_missing_reference_context` | Compatible hazard/reference context is absent |
| `blocked_derived_from_residual_quantity_unknown` | Derivation does not establish residual presence/amount |
| `unresolved_product_composition` | Candidate formulation/quantity data exist but canonical selection is unresolved |
| `unresolved_scenario` | Scenario inputs/assumptions cannot be resolved deterministically |
| `unresolved_unit_or_basis` | Unit, denominator or time/body-weight basis is ambiguous |
| `unresolved_route_or_population_applicability` | Scientific transfer requires a missing review artifact |

### Risk-computability reasons

| Code | Meaning |
|---|---|
| `risk_gate_passed_context_complete` | Gate inputs are complete and compatible; future risk engine may proceed |
| `risk_not_computable_missing_hazard_context` | No compatible hazard characterisation/reference meaning |
| `risk_not_computable_missing_projection` | Product association cannot be established |
| `risk_not_computable_missing_exposure` | One or more exposure-critical dimensions are missing |
| `risk_not_computable_incompatible_context` | Hazard/reference and exposure differ materially |
| `risk_not_computable_protocol_not_approved` | No published reviewed risk-characterisation method exists |
| `risk_computability_unresolved` | Governed mapping/review is required before gate classification |

Published vocabularies are immutable. Localized or AI-rendered wording is
non-canonical.

## Explanation trace

The canonical traversal is:

```text
product identity
→ product composition snapshot
→ image/document/extraction/review provenance
→ product ingredient and ingredient scientific projection
→ substance hazard profile
→ exposure scenario and assumption provenance
→ quantity/composition derivation steps
→ exposure readiness decision and reasons
→ hazard/reference compatibility gate
→ risk computability state
→ product scientific assessment components
```

The trace lists every accepted, rejected, missing and unresolved input; units
and bases; preparation state; mapping/profile references; uncertainty
propagation; rule/vocabulary versions; allowed conclusions and forbidden
interpretations. AI may verbalize the frozen trace but cannot alter it.

## Determinism and digest model

The minimum additional semantic boundaries are:

| Digest | Includes | Excludes |
|---|---|---|
| `product_composition_snapshot_digest` | Frozen product identity/state, canonical image/document/extraction/review membership, ingredients/order, validated quantities, nutrition/serving/net/preparation metadata, missing states and canonicalization versions | Mutable current rows alone, DB order, runtime timestamps, UI and AI wording |
| `exposure_scenario_digest` | Scenario type, product-state reference, population, route, amounts/bases, frequency, duration, body weight/preparation, provenance, assumptions, review/rule refs and uncertainty | Scenario ID, author display name, runtime/UI metadata |
| `exposure_readiness_digest` | Composition/projection/profile/scenario digests, dimension states, missing data, unit/reference compatibility, reasons, uncertainty and trace-step digest | Presentation and execution timing |
| `product_assessment_digest` | Protocol/input digests, product snapshot, sorted ingredient projections, sorted scenario readiness/risk-computability components, missing/conflict/uncertainty summaries, assumptions and trace digest | UI ordering, colours, localized/AI prose, workers and timestamps |

`product_composition_snapshot_digest` and scenario digest are normally committed
through the Phase 7.1 input digest. They need not become redundant top-level
execution digests.

```text
same product composition snapshot
+ same ingredient projections/substance profiles
+ same exposure scenario set
+ same protocol and governed vocabularies
→ same readiness, risk-computability and product-assessment digests
```

Set-like ingredients/scenarios are sorted by stable semantic key. Source label
order is retained inside its explicit ordered field but does not control
processing precedence.

## Edge-case behavior

| # | Case | Composition / exposure readiness | Risk computability | Allowed / forbidden conclusion | Uncertainty / history |
|---:|---|---|---|---|---|
| 1 | Ingredient presence only | `ingredient_presence_known`; `exposure_not_ready` | `risk_not_computable` | Presence may be stated / no concentration or risk | Composition gap frozen |
| 2 | Ingredient amount known, substance fraction unknown | Ingredient-ready, substance quantity missing | Not computable | Ingredient amount under basis / no substance dose | Fraction uncertainty |
| 3 | Substance amount known | Composition may be ready; scenario gates remain | Depends on intake/time/context | Amount under exact basis / no risk yet | Other dimensions preserved |
| 4 | Quantity range known | Qualified composition/readiness | Only future range-aware method may proceed | Supplied range / no point estimate | Range provenance frozen |
| 5 | Label serving known, intake unknown | Serving available; exposure partial | Not computable | Declared serving / no actual intake | Intake uncertainty |
| 6 | Explicit consumed amount known | Intake dimension ready | Other gates decide | Stated/observed amount / no automatic risk | Provenance-specific |
| 7 | Frequency missing | Exposure partial/not ready | Not computable for time-dependent question | Frequency missing / no chronic estimate | Missing state frozen |
| 8 | Duration missing | Exposure partial/not ready | Not computable when material | Duration missing / no acute/chronic mapping | Duration uncertainty |
| 9 | Population missing | Exposure unresolved/not ready | Not computable for population-specific claim | Population unknown / no generalization | Population uncertainty |
| 10 | Route missing | Exposure unresolved/not ready | Not computable when route material | Route unknown / food is not silent oral | Route uncertainty |
| 11 | Unknown unit | Quantity unresolved | Not computable | Raw value shown / no conversion | Unit uncertainty |
| 12 | Incompatible unit/basis | Quantity not usable | Not computable | Incompatibility shown / no comparison | Basis uncertainty |
| 13 | Mixture fraction unknown | Presence only | Not computable for component | Component association / no amount | Fraction uncertainty |
| 14 | `derived_from` without residual presence | Composition not applicable/blocked for source substance | Not computable | Derivation provenance / no exposure | Residual uncertainty |
| 15 | Multiple ingredient projections | Separate readiness per entry | Per scenario/entry gate | Structured inventory / no aggregation | Per-entry uncertainty |
| 16 | Nutrition table, no ingredient composition | Nutrient data available; substance composition missing | Not computable for mapped substance | Nutrition values / no ingredient fraction | Composition gap |
| 17 | Historical serving changed | Replay uses old serving snapshot | Historical gate unchanged | Historical result / no current serving substitution | Refresh stores new serving |
| 18 | Same product, two scenarios | Two independently keyed readiness sub-results | May differ by scenario | Scenario-scoped states / no overwrite | Both digests retained |
| 19 | QPS context only | Regulatory component; exposure basis absent | Not computable | QPS context / no product safety | Qualification scope |
| 20 | Hazard profile, no exposure | Hazard visible; exposure not ready | Not computable | Hazard context / no product risk | Exposure gaps explicit |
| 21 | Exposure data, no compatible reference | Exposure may be ready | Not computable | Exposure estimate may later be stated / no risk | Reference uncertainty |
| 22 | Numeric exposure/reference, route mismatch | Inputs numeric but incompatible | Not computable | Route mismatch / no ratio/comparison | Compatibility gap |
| 23 | Formulation changed after snapshot | Replay freezes prior composition | Historical gate/result preserved | Historical formulation / no silent refresh | New refresh digest |
| 24 | AI-extracted serving not validated | Candidate serving unresolved | Not computable if required | Candidate transcription / no canonical serving claim | Review/provenance gap |

## Conceptual deterministic test vectors

Digest expectations describe equality/difference, not literal hashes. No vector
performs an exposure calculation or emits a risk score.

| # | Product/projections/composition | Scenario | Expected readiness and reason codes | Risk state, uncertainty and trace | Digest expectation |
|---:|---|---|---|---|---|
| 1 | Frozen product; one valid projection; presence only | Complete except amount | `exposure_not_ready`; `blocked_missing_substance_quantity` | `risk_not_computable` + `risk_not_computable_missing_exposure`; composition gap traced | Same inputs stable |
| 2 | Ingredient quantity known; substance fraction absent | Otherwise complete | `exposure_partially_ready`; `blocked_missing_substance_quantity` | `risk_not_computable` + `risk_not_computable_missing_exposure`; fraction uncertainty and blocked derivation traced | Adding fraction changes digest |
| 3 | Governed substance amount/basis | Intake/frequency/duration absent | `exposure_partially_ready`; `blocked_missing_intake_amount`, `blocked_missing_frequency`, `blocked_missing_duration` | `risk_not_computable` + `risk_not_computable_missing_exposure`; all three gaps traced | Missing set canonical |
| 4 | Governed substance quantity range | Reviewed range scenario complete | `exposure_ready_qualified_scenario`; `ready_qualified_scenario` | `risk_not_computable` + `risk_not_computable_protocol_not_approved`; range uncertainty/assumptions traced | Range endpoints committed |
| 5 | Label serving only | No actual/assumed intake | `exposure_partially_ready`; `blocked_missing_intake_amount` | `risk_not_computable` + `risk_not_computable_missing_exposure`; label-serving versus intake gap traced | Label serving digest stable |
| 6 | Substance amount and observed intake | Route/population/time complete | `exposure_ready`; `ready_complete_exposure_context` | `risk_not_computable` + `risk_not_computable_protocol_not_approved`; observation provenance traced | Observation provenance committed |
| 7 | Full amount/intake; frequency absent | Duration-dependent question | `exposure_partially_ready`; `blocked_missing_frequency` | `risk_not_computable` + `risk_not_computable_missing_exposure`; no repeated-exposure claim | Adding frequency changes scenario digest |
| 8 | Full amount/intake/frequency; duration absent | Duration-specific question | `exposure_partially_ready`; `blocked_missing_duration` | `risk_not_computable` + `risk_not_computable_missing_exposure`; duration gap traced | Missing state committed |
| 9 | Complete quantity/time; population absent | Population-specific question | `exposure_not_ready`; `blocked_missing_population` | `risk_not_computable` + `risk_not_computable_missing_exposure`; population uncertainty traced | Stable under row order |
| 10 | Complete quantity/time; route unknown | Oral-specific question | `exposure_unresolved`; `blocked_missing_route`, `unresolved_route_or_population_applicability` | `risk_computability_unresolved`; no food→oral inference; route review gap traced | Reviewed route changes future digest |
| 11 | Numeric quantity, unknown unit | Otherwise complete | `exposure_unresolved`; `unresolved_unit_or_basis` | `risk_computability_unresolved`; raw unit and prohibited conversion traced | Raw unit state committed |
| 12 | Exposure/reference bases incompatible | Complete fields | `exposure_not_ready`; `blocked_incompatible_units` | `risk_not_computable` + `risk_not_computable_incompatible_context`; basis mismatch traced | Basis refs determine digest |
| 13 | `contains`; unknown fraction | Complete consumption scenario | `exposure_not_ready`; `blocked_missing_concentration`, `blocked_missing_substance_quantity` | `risk_not_computable` + `risk_not_computable_missing_exposure`; composition uncertainty traced | Relationship/profile stable, readiness blocked |
| 14 | `derived_from`; no residual data | Complete product use | `exposure_not_ready`; `blocked_derived_from_residual_quantity_unknown` | `risk_not_computable` + `risk_not_computable_missing_exposure`; residual uncertainty traced | New residual artifact creates refresh |
| 15 | Two ingredient projections with complete separate quantities | One complete scenario | Two `exposure_ready` paths; `ready_complete_exposure_context` on each | `risk_not_computable` + `risk_not_computable_protocol_not_approved` per path; no max/sum/worst-entry node in trace | Projection input order irrelevant |
| 16 | Nutrition per 100 g only | Product amount known | `exposure_not_ready`; `blocked_missing_composition`, `blocked_missing_substance_quantity` | `risk_not_computable` + `risk_not_computable_missing_exposure`; nutrition kept in separate trace channel | Nutrition digest does not fill composition |
| 17 | Historical snapshot with complete exposure inputs | Historical serving/scenario | Replay reproduces `exposure_ready`; `ready_complete_exposure_context` | Reproduces baseline `risk_not_computable` + `risk_not_computable_protocol_not_approved` and exact historical trace | Assessment digest equality; current state excluded |
| 18 | Same complete snapshot, scenario A/B | Different governed intake amounts | Two `exposure_ready` sub-results; `ready_complete_exposure_context` | Separate `risk_not_computable` results with `risk_not_computable_protocol_not_approved` and scenario traces; no overwrite | Scenario digests differ |
| 19 | QPS regulatory association only | Exposure question not applicable to the regulatory component | `exposure_not_applicable`; `not_applicable_exposure_question` | `risk_not_applicable`; QPS qualification trace retained without safety inference | Regulatory digest separate |
| 20 | Substance hazard profile available | No product quantity/scenario | `exposure_not_ready`; `blocked_missing_composition`, `blocked_missing_intake_amount` | `risk_not_computable` + `risk_not_computable_missing_exposure`; hazard trace unchanged | Hazard digest unchanged |
| 21 | Exposure-ready product | Hazard reference context absent | `exposure_ready`; `ready_complete_exposure_context` | `risk_not_computable` + `risk_not_computable_missing_hazard_context`; missing reference edge traced | Gate reason changes product digest |
| 22 | Exposure and reference numeric | Route differs | `exposure_ready`; `ready_complete_exposure_context` for exposure alone | `risk_not_computable` + `risk_not_computable_incompatible_context`; route mismatch traced | Route committed |
| 23 | Refresh after formulation change with complete new inputs | New composition snapshot, same protocol/scenario | New `exposure_ready`; `ready_complete_exposure_context` | New `risk_not_computable` + `risk_not_computable_protocol_not_approved`; prior assessment/trace immutable | Composition/product digests differ |
| 24 | Detected AI serving candidate | No validation artifact | `exposure_unresolved`; `unresolved_scenario` | `risk_computability_unresolved`; AI provenance and missing review traced | Review artifact changes new digest |

## Current-schema gap matrix

| Required concept | Status through local `0017` | Current basis / gap | Future requirement |
|---|---|---|---|
| Product identity | Partial | Row ID/barcode/GTIN/version/status; mutable content | Immutable identity/version snapshot |
| Product formulation history | Missing | Product update/version does not preserve prior payload | Append-only version/event or frozen snapshot membership |
| Product ingredient identity/order | Available/partial | Rows and extraction item/order; local rows legacy | Governed accepted composition membership |
| Ingredient quantities/percentages | Extracted but not canonical | Optional string in extraction/provenance | Parsed value/range/qualifier/unit/basis and review |
| Substance fraction/composition | Missing | Ingredient-substance bridge has no product fraction | Product-specific composition object |
| Serving information | Partial | Free-text table and structured extraction basis | Canonical serving object plus history/review |
| Serving history | Missing | Legacy row mutable/replaced | Frozen serving/formulation membership |
| Net quantity | Missing | No canonical field | Versioned quantity and package basis |
| Consumption scenario | Missing | No object | Immutable scenario document/persistence |
| Frequency/duration | Missing | No product/scenario fields | Versioned time-basis representation |
| Population/body weight | Legacy/missing for protocol | User profile exists but no scientific scenario contract | Separate governed assessment inputs; no silent legacy reuse |
| Preparation/use state | Missing | No canonical field | Versioned product-use state/provenance |
| Label provenance | Strong envelope, empty locally | Images/docs/runs/items/versioned prompts; validation status exists | Selection/review rule and immutable snapshot membership |
| Product composition snapshot | Missing | No Phase 7 manifest/digest | Future immutable snapshot persistence |
| Exposure readiness/result | Missing | Documentation only | Future immutable result/component persistence |
| Reference-point semantics | Missing | Legacy risk-profile fields excluded; scientific findings heterogeneous | Reviewed ontology/policy and compatibility contract |
| Risk characterisation | Missing | Legacy scoring excluded | Separate validated protocol and persistence |

No migration or SQL schema is designed by this matrix.

## Scientific-review boundaries

| Area | Classification | Rationale |
|---|---|---|
| Hazard/exposure/risk separation | ARCHITECTURALLY APPROVED | Prevents category errors |
| Explicit readiness/non-computability states | ARCHITECTURALLY APPROVED | Missing inputs remain visible without danger/safety inference |
| No silent defaults and assumption provenance | ARCHITECTURALLY APPROVED | Required for auditability |
| Structured product/scenario objects, trace and digests | ARCHITECTURALLY APPROVED | Deterministic representation boundary |
| Scenario-specific results and no product aggregation | ARCHITECTURALLY APPROVED | Preserves scientific scope and traceability |
| Label AI as non-canonical candidate source | ARCHITECTURALLY APPROVED | Matches WYE governance and existing validation states |
| Ingredient-order quantitative interpretation | REQUIRES EXTERNAL SCIENTIFIC/REGULATORY REVIEW | Jurisdiction/category/date rules and exceptions matter |
| Default consumption scenarios | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Defaults directly affect exposure |
| Oral route inference | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Intended use/preparation may differ |
| Population transfer/categories | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Applicability affects claims |
| Frequency/duration normalization | REQUIRES EXTERNAL SCIENTIFIC REVIEW | No arbitrary thresholds allowed |
| Body-weight assumptions | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Population statistics and uncertainty required |
| Mixture range/upper-bound handling | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Scenario meaning and interactions matter |
| Substance-amount derivation policy | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Identity/form/composition assumptions affect dose |
| Reference point selection/compatibility | REQUIRES EXTERNAL SCIENTIFIC/REGULATORY REVIEW | Endpoint, route, duration, population and form must align |
| Risk-characterisation and confidence framework | REQUIRES EXTERNAL SCIENTIFIC REVIEW | Determinism is not validation |
| Quantities, composition, serving history and scenarios | DATA GAP | Not generally canonical/persisted |
| Nutrition and allergy assessment | DEFERRED | Separate protocol families |
| Runtime exposure/risk and persistence | DEFERRED | Later phases and reviews |

## Implementation-readiness matrix

Classification describes logical maturity, not authorization.

| Future component | Classification | Reason |
|---|---|---|
| Product-composition snapshot envelope | READY FOR IMPLEMENTATION | Membership, provenance and freeze boundary are defined |
| Complete historical product snapshot reader | BLOCKED BY DATA MODEL | Product/composition/serving history is incomplete |
| Label extraction provenance reader | READY FOR IMPLEMENTATION | Images/documents/runs/items expose deterministic anchors |
| Serving extraction/readiness envelope | READY FOR IMPLEMENTATION | Basis states and governance boundary are defined |
| Canonical serving materialization | BLOCKED BY DATA MODEL | No reviewed canonical serving/history model |
| Exposure-scenario envelope | READY FOR IMPLEMENTATION | Fields, provenance and assumption status are defined |
| Quantity/unit readiness classifier skeleton | READY FOR IMPLEMENTATION | Structural states and missing behavior are defined |
| Exposure-readiness state machine | READY FOR IMPLEMENTATION | States, gate order and reasons are defined |
| Reason-code, trace and digest production | READY FOR IMPLEMENTATION | Canonical content/ordering are defined |
| Ingredient/substance composition parser | BLOCKED BY DATA MODEL | Quantity/range/unit/basis not canonical |
| Substance-amount derivation | BLOCKED BY SCIENTIFIC REVIEW | Reviewed form/composition transformation absent |
| Domain-implied route/default scenarios | BLOCKED BY SCIENTIFIC REVIEW | Assumptions affect exposure claim |
| Actual exposure calculation | BLOCKED BY SCIENTIFIC REVIEW | No approved model, units, populations or assumptions |
| Reference-point comparison | BLOCKED BY SCIENTIFIC REVIEW | No approved reference ontology/compatibility policy |
| Risk characterisation | BLOCKED BY SCIENTIFIC REVIEW | No validated risk protocol |
| Product-assessment persistence | DESIGNED IN 7.6; IMPLEMENTATION DEFERRED | Canonical artifact/index/publication contract is defined; schema freeze and migration remain pending |
| API/shadow rollout | DEFERRED TO 7.8+ | Validation and persistence precede exposure of results |
| Numerical product/health/safety/risk score | DEFERRED | Not justified or defined |

## Phase 7.5 exit criteria

- [x] Product/composition model and local data audited.
- [x] Exposure terminology and required contexts defined.
- [x] Exposure-readiness states separate availability from usability.
- [x] Product-level composition readiness defined.
- [x] Ingredient-order semantic boundary defined.
- [x] Serving/reference/actual-intake concepts separated.
- [x] Exposure-scenario object and provenance defined.
- [x] No-silent-default policy defined.
- [x] Route, population, frequency and duration semantics defined.
- [x] Exposure basis and unit-readiness states defined.
- [x] Substance-amount derivation preconditions defined.
- [x] Mixture and `derived_from` exposure behavior defined.
- [x] Exposure-specific uncertainty taxonomy defined.
- [x] Exposure-readiness payload defined.
- [x] Risk-computability gate and reasons defined.
- [x] `risk_not_computable` separated from risk/safety claims.
- [x] Non-scalar `product_scientific_assessment` defined.
- [x] Product-level output and aggregation boundaries defined.
- [x] Multiple-scenario and generic/user-specific boundaries defined.
- [x] Historical execution semantics defined.
- [x] Product-composition snapshot contract defined.
- [x] Label provenance and AI governance boundary defined.
- [x] Nutrition, allergy and reference-point boundaries defined.
- [x] Product-level uncertainty/confidence semantics defined.
- [x] Hybrid versioned reason-code vocabulary defined.
- [x] Canonical explanation trace defined.
- [x] Determinism and digest boundaries defined.
- [x] Twenty-four edge cases analyzed.
- [x] Twenty-four deterministic conceptual vectors defined.
- [x] Current-schema gaps documented.
- [x] Scientific-review boundaries classified.
- [x] Implementation readiness classified.
- [x] Product-level naming decision recorded.

## Roadmap and next checkpoint

The Phase 7 roadmap remains unchanged. Phase 7.5 confirms that persistence must
freeze product composition and scenario inputs before replay can be trusted.

The Phase 7.6 persistence specialization is defined in:

```text
WYE_SCORING_PERSISTENCE.md
```

It freezes product-composition/scenario inputs as canonical artifacts and binds
scenario-specific readiness/assessment results to immutable publication bundles.
User-specific scenarios require a distinct privacy boundary. Migration decision
B requires a canonicalization/schema/publication freeze before implementation.
The proposed Phase 7.6.1 checkpoint is not started by this document.
