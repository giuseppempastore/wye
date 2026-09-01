# WYE Product Scoring Contract

## Document status

```text
DRAFT — NOT SCIENTIFICALLY APPROVED
NOT A PUBLISHED SCORING POLICY
NO RUNTIME AUTHORITY
```

This document defines the semantic and governance boundary for a future WYE
food-product tri-score protocol. It does not define an executable policy, a
numerical formula, weights, thresholds, score bands, evaluability gates, a
numeric missing-data fallback, a database schema, an API or a runtime
implementation.

The frozen selection-policy candidate remains a separate review subject:

```text
policy: efsa_qps_evidence_selection
version: 1.0.0-candidate.1
status: frozen candidate awaiting external scientific approval
```

Nothing in this document modifies, approves, supersedes or promotes that
candidate, its golden corpus, its delivery package or its external approval
gate. Any future product-scoring candidate requires a new governed identity,
version, digest, scientific review and validation corpus.

## 1. Scope and authority boundary

This contract is documentation only. It establishes vocabulary, intended use,
non-claims, mandatory future output fields, invariants and governed decision
states.

It has no authority to:

- calculate or publish a score;
- select a nutrient-profile model;
- assign a number to an ingredient assessment state;
- define a cap, penalty, weight, threshold or zero override;
- infer a missing quantity, dose, concentration, serving or exposure;
- create or approve a scoring protocol;
- change scientific evidence selection or the Phase 7 QPS candidate;
- authorize a migration, schema change, API, worker or user-facing rollout.

Runtime numerical scoring remains blocked until all blocking decisions in the
decision matrix are resolved through governed artifacts and the resulting
candidate has completed scientific review, validation and publication.

### 1.1 Immediate document audience

The immediate audience of this contract is internal to the WYE project:

- product owners;
- methodology owners;
- developers and technical reviewers;
- future scientific and regulatory reviewers;
- governance and quality-assurance owners.

These are readers and users of the document, not the final target population of
the WYE application. This document does not authorize them to make diagnoses,
prescriptions or clinical assessments. The first-release target population,
intended users and claims boundary are decided under `PSC-OD-001`; exact final
user-facing language and release approval remain governed separately.

## 2. Intended use and non-claims

This tri-score contract applies exclusively within the food domain: foods,
beverages and packaged food products for which declared ingredients and a
nutrition declaration are applicable. Within that domain, WYE is intended to
provide a general, product-specific and user-independent assessment of the
favourability of the declared composition under a versioned WYE protocol.

This contract does not automatically apply to cosmetics, medicinal products,
supplements governed by specific regimes, feed or other non-food domains. Any
assessment in one of those domains requires a separate methodological contract.
A nutrition score must not be invented for a product to which nutrition
assessment is not applicable.

For a food that is lawfully exempt from a nutrition declaration, this contract
does not invent a number. A future evaluability and missing-data policy must
determine the result while preserving the possibility of `not_computable`.

This food-domain boundary did not by itself define the final target population,
intended users or permitted claims. Those first-release product decisions are
now recorded under `PSC-OD-001`; exact external wording remains subject to
`PSC-OD-020` and the applicable scientific, communication and legal/regulatory
review gates.

The product promise is:

> WYE evaluates what the label and applicable evidence allow it to state under
> versioned rules, while reporting coverage, confidence, criticality and
> limitations separately.

The base assessment concerns the identified product and the information that
can be canonically attributed to that product. It is not an assessment of one
person's diet, behaviour, medical history or likely health outcome.

WYE does not:

- diagnose a disease or condition;
- prescribe a food, diet, dose, treatment or behaviour;
- replace a doctor, nutritionist or dietitian;
- establish absolute safety or safety at unlimited intake;
- predict an individual's probability of disease or adverse effect;
- assess undeclared ingredients, contamination, adulteration or batch-specific
  defects that are not represented by eligible evidence;
- know the user's total diet, actual portion, intake frequency or consumed
  quantity;
- currently produce personalized assessments;
- present a bibliography or scientific-reference list as a required
  user-facing feature.

Scientific, regulatory and methodological sources remain mandatory internal
provenance. Their absence from the ordinary user interface does not reduce the
requirement for source identity, version, effective date, cutoff and audit.

## 3. Mandatory future output contract

Every future in-scope food tri-score result must contain exactly one value for
each of the following support fields:

```text
evaluability_status:
  computable
  not_computable

assessment_coverage_percent: integer 0..100
confidence_state:
  high
  moderate
  low

critical_flags[]
limitations[]
missing_inputs[]
scoring_version
```

When `evaluability_status = computable`, the result must also contain exactly
one value for each score field:

```text
ingredient_goodness_percent: integer 0..100
nutrition_goodness_percent: integer 0..100
overall_goodness_percent: integer 0..100
```

When `evaluability_status = not_computable`, the result must contain no
substitute numeric score. A score field must be absent or carry an explicitly
typed non-value according to the future published serialization contract.
Absence, null or an equivalent typed non-value does not mean zero. `0` is a
computed endpoint, never a fallback for missing or insufficient data.

None of the three scores is currently calculable: numerical mappings,
evaluability gates, an ordinary aggregation function, caps, zero-override
rules, precision and rounding have not been scientifically approved or
published.

Until those decisions are approved, implementations must fail closed rather
than substitute legacy scores, placeholders, AI-generated values or implicit
defaults.

For every score field that is produced, `percent`:

- does not mean a probability;
- does not mean clinical safety;
- does not mean the percentage of ingredients that are safe;
- does not mean the predicted chance of a favourable health outcome;
- means only the position reached within the applicable, versioned WYE
  protocol.

`evaluability_status`, `assessment_coverage_percent`, `confidence_state`,
`critical_flags`, `limitations` and `missing_inputs` support interpretation.
Evaluability, coverage and confidence are independent dimensions. None may be
used as a synonym or undocumented proxy for another, and none may be compressed
into an untraceable score adjustment. Support fields do not become substitute
scores when a result is `not_computable`.

An overall score cannot be `computable` when an indispensable component is
`not_computable`, unless a future scientifically approved and published policy
explicitly defines the component's applicability and aggregation treatment.
The minimum conditions for computability remain `OPEN`; this contract defines
no coverage, confidence or completeness threshold.

`scoring_version` must identify a published immutable protocol and its governed
dependencies. A version label without the corresponding canonical rule and
source artifacts is insufficient.

## 4. Cross-domain semantic separation

The future protocol must keep at least these concepts distinct:

```text
declared composition != actual batch composition
hazard != exposure != risk
confidence != safety
coverage != confidence
missing evidence != negative evidence
regulatory authorization != harmlessness at every dose
ingredient goodness != nutrition goodness
general product assessment != personalized assessment
```

Evidence availability, evidence eligibility, scientific interpretation,
product applicability and numerical aggregation are separate governed steps.
An AI model, source-prestige shortcut or mutable database row must not collapse
them into a runtime judgment.

## 5. Ingredient goodness contract

`ingredient_goodness_percent` is defined semantically as:

> Degree of favourability of the declared ingredient composition under
> versioned WYE rules, considering identity, regulatory status, qualified
> evidence and applicability that can actually be demonstrated for the
> product.

It is not a count of recognized ingredients and is not a natural-versus-
artificial index.

### 5.1 Conceptual pipeline

```text
label identity
→ canonical ingredient
→ ingredient/substance relationship
→ product applicability
→ regulatory state
→ endpoint-specific evidence
→ exposure computability
→ ingredient assessment state
→ product-level ingredient aggregation
```

Every transition must be deterministic under a published vocabulary and must
retain its input identity, decision, reason code, uncertainty and provenance.
Failure at one transition must remain visible and must not be silently replaced
with a favourable or adverse assumption.

### 5.2 Ingredient assessment states

The minimum state vocabulary is:

| State | Semantic meaning | Forbidden interpretation |
|---|---|---|
| `no_identified_concern` | No concern was identified within the reviewed question, evidence scope and cutoff. | Proven safe in every context or dose. |
| `authorised_with_conditions` | The applicable use is authorized only under identified categories, levels, specifications or other conditions. | Authorization is unconditional safety. |
| `exposure_dependent` | Scientific interpretation materially depends on quantity, concentration, intake, frequency, duration or population. | A qualitative label presence establishes risk. |
| `under_re_evaluation` | An authoritative reassessment or follow-up relevant to the question is incomplete. | The substance is either unsafe or cleared. |
| `evidence_uncertain` | Eligible evidence is limited, indirect, imprecise, heterogeneous or otherwise uncertain. | Uncertainty is evidence of danger or safety. |
| `conflicting_evidence` | Eligible and applicable evidence reaches materially conflicting conclusions. | Conflicts may be averaged or resolved by source prestige alone. |
| `critical_concern` | A serious qualified concern has been identified and may be applicable to the product. | A critical disqualifier or automatic zero already exists. |
| `not_authorised` | The identified use is not authorized for the relevant jurisdiction, date, product category and conditions. | The product is necessarily poisonous. |
| `withdrawn` | A relevant authorization, assessment or use has been withdrawn; the withdrawal type and scope must be stated. | Every historical or differently scoped use is prohibited. |
| `unresolved` | Identity, relationship, form, regulatory match or product applicability cannot be resolved canonically. | The ingredient is harmful because it is unknown. |
| `insufficient_data` | The target is sufficiently identified, but the data required for the scoped assessment are insufficient. | Absence of data proves safety or danger. |

These states are not one ordered scale and have no numerical mapping in this
contract. Multiple states or dimensions may coexist. A future policy may define
a primary state only through explicit precedence while preserving all secondary
states and reasons.

### 5.3 Required dimensions

An ingredient assessment must keep these dimensions separate:

- `regulatory_status`;
- `evidence_state`;
- `hazard`;
- `exposure`;
- `risk`;
- `applicability`;
- `confidence`;
- `uncertainty`.

No dimension may be used as an undocumented proxy for another. In particular,
hazard cannot become risk without compatible exposure and applicability.

### 5.4 Ingredient interpretation constraints

- An additive is not automatically negative because it is an additive.
- `natural` does not automatically mean safe.
- `artificial` does not automatically mean dangerous.
- `authorised` does not mean harmless at every dose or in every use.
- Hazard does not automatically mean risk.
- The presence of an allergen does not automatically lower the general,
  user-independent product score.
- An allergen may produce an informational flag; personal incompatibility is a
  separate future personalized assessment.
- QUID is quantitative only when an applicable declared quantity and basis are
  actually available.
- Ingredient-list order is ordinal information and does not authorize WYE to
  invent percentages, concentration intervals or doses.
- Relationship types such as `contains`, `represents`, `equivalent_to`,
  `mixture_component` and `derived_from` do not have interchangeable
  composition or exposure consequences.

## 6. Nutrition goodness contract

`nutrition_goodness_percent` is defined semantically as:

> Positioning of the declared nutritional composition against a general,
> category-aware WYE protocol on the relevant standardized basis, without
> estimating total diet, personal portion or clinical risk.

### 6.1 Conceptual pipeline

```text
nutrition extraction
→ basis/unit normalization
→ sold/prepared-state resolution
→ solid/liquid classification
→ product-category classification
→ plausibility and consistency checks
→ nutrient-profile components
→ missingness/confidence treatment
→ nutrition score
```

The pipeline must preserve raw label values and provenance. Normalization may
create canonical values only under published unit, basis and preparation rules.

### 6.2 Minimum input domain

The future nutrition policy must be able to represent:

- energy, preserving declared kJ and kcal when available;
- fat;
- saturated fat;
- carbohydrate;
- sugars;
- protein;
- salt;
- fibre, when available;
- supplementary nutrients explicitly admitted by the future policy;
- values per 100 g;
- values per 100 ml;
- values per serving as additional information rather than assumed intake;
- product category;
- solid or liquid classification;
- product state as sold, prepared or reconstituted;
- the manufacturer instruction and provenance supporting any prepared or
  reconstituted state.

A declared serving is not an observed consumption amount. Values per serving
must not replace the applicable per-100-g or per-100-ml basis unless a future
published policy explicitly defines a lawful and scientifically reviewed case.

### 6.3 Minimum semantic checks

Before scoring, the future protocol must perform deterministic checks for:

- non-negative numeric values;
- recognized units and convertible units under a versioned conversion table;
- `saturated_fat <= fat`, unless values have non-comparable bases;
- `sugars <= carbohydrate`, unless values have non-comparable bases;
- consistency of declared kJ and kcal within an approved tolerance;
- an explicit distinction between salt and sodium;
- duplicate or conflicting values without automatic averaging;
- no invented preparation or reconstitution instruction;
- comparison only between values using the same quantity basis and product
  state;
- review of physically or compositionally implausible values under versioned
  checks;
- category and solid/liquid consistency;
- traceable handling of missing mandatory and optional nutrients.

A failed plausibility check does not prove poor nutritional quality. It affects
input usability, coverage and confidence and may contribute to a future
evaluability decision without predetermining that decision.

## 7. Internal nutrient-profile benchmark register

```text
research cutoff: 2026-09-01
internal methodological provenance only
not a user-facing bibliography feature
```

This register identifies comparison benchmarks. It does not select a definitive
base model and does not authorize transfer of a benchmark score, class,
threshold or formula into WYE.

| Benchmark | Intended use and target | Required components | Category-specific features | Current WYE data gaps | Potentially reusable | Not directly transferable / future justification required |
|---|---|---|---|---|---|---|
| EU nutrition-claim conditions, Regulation (EC) No 1924/2006 and applicable annex | Legal eligibility of individual nutrition claims for foods marketed to the EU consumer; not an overall health score. | Claim-specific energy, fat, saturates, sugars, salt/sodium, fibre, protein, vitamins, minerals or comparative data. | Conditions can distinguish solids, liquids, energy bases and comparable product categories; claims concern food ready for consumption under applicable instructions. | Reliable claim context, comparable-product set, complete vitamin/mineral data and some prepared-state information. | Binary compliance checks, definitions, units and legally governed conditions for individual attributes. | A permitted claim cannot become positive WYE points automatically. Combining claim thresholds into a general percentage requires new scientific justification. |
| WHO/Europe Nutrient Profile Model 2023, second edition | Supports policies restricting marketing of foods and non-alcoholic beverages to children in the WHO European Region. | Category-dependent total fat, saturated fat, total or added sugars, non-sugar sweeteners, sodium and energy. | Strong category matrix, including beverage subcategories and category-specific eligibility or thresholds. | Governed category mapping, added sugars, structured sweetener presence and complete category-dependent fields. | Category vocabulary, marketing-policy benchmark and adversarial cases for children-focused classification. | A marketing eligibility gate is not a universal product-health percentage. Population and policy transfer require justification. |
| UK NPM 2004/05 | Current UK policy tool for identifying less healthy food and drink in advertising and promotion contexts. | Energy, saturated fat, total sugars, sodium, protein, fibre, fruit/vegetable/nut proportion. | Common point structure with different final food/drink classification thresholds; reconstituted products use manufacturer instructions. | Governed fruit/vegetable/nut percentage, robust category/state and complete preparation data. | Reproducible benchmark, sensitivity comparison and established handling of food versus drink. | Its regulatory advertising classification, original dietary basis and numerical score cannot be relabelled as WYE goodness. |
| UK NPM 2018, guidance published 2026 and not yet applied to policy at cutoff | Updated less-healthy classification reflecting UK advice on free sugars and fibre. | Energy, saturated fat, free sugars, salt, protein, AOAC fibre, fruit/vegetable/nut/seed proportion. | No general category-specific criteria; food/drink final thresholds differ; reconstitution follows manufacturer instructions. | Free sugars, AOAC method identity, fruit/vegetable/nut/seed proportion and reviewed reconstitution inputs. | Updated nutrient definitions, worked examples and a benchmark for sensitivity to free sugars and fibre. | Free-sugar estimation from incomplete labels, FVNS reconstruction and conversion to 0..100 require new validation. The model's pending policy status must remain visible. |
| Updated Nutri-Score 2023, implementation including France 2025 | Voluntary front-of-pack comparison of nutritional quality, complementary to mandatory nutrition information. | Energy, sugars, saturated fat, salt, protein, fibre, fruit/vegetable/legume proportion and non-nutritive sweeteners for beverages. | General foods plus specific handling for beverages, cheeses, red meat, and animal/vegetable fats, nuts and seeds; controlled prepared-state cases. | Authoritative product categorization, fruit/vegetable/legume proportion, sweetener identification and reliable prepared-state inputs. | Transparent comparison benchmark, category edge cases and validation datasets. | Nutri-Score classes or underlying points cannot be mapped directly to WYE percentages; category rules and any divergence require scientific rationale. |

Minimum internal provenance references for a future source register include:

- Regulation (EC) No 1924/2006 and its current consolidated annex;
- WHO Regional Office for Europe nutrient profile model, second edition,
  published 2023;
- UK NPM 2004/05 technical guidance and policy status at cutoff;
- UK NPM 2018 technical guidance, published 2026, and its policy status at
  cutoff;
- Nutri-Score updated algorithm reports, technical FAQ and national
  implementation status at cutoff.

For every future use, the repository must freeze the exact source document,
version or consolidation date, jurisdiction, access date, cutoff, locator and
content digest. A web page title alone is not reproducible provenance.

## 8. Overall goodness contract

`overall_goodness_percent` is not an arithmetic mean. Its conceptual pipeline
is hierarchical:

```text
ingredient score
+
nutrition score
→ base aggregation candidate
→ incomplete-data guardrail
→ applicable critical caps
→ zero override, only if valid
→ overall_goodness_percent
```

The base aggregation family is an open scientific decision. This contract does
not choose weighted, geometric or any other formula.

### 8.1 Aggregation families under consideration

| Family | Potential advantages | Risks and edge cases | Required future evidence |
|---|---|---|---|
| Weighted aggregation with guardrails | Interpretable contribution by domain; simple sensitivity analysis; explicit priorities. | Arbitrary weights and excessive compensation can let one domain erase another. | Rationale for weights, calibration set, sensitivity analysis and guardrail validation. |
| Geometric aggregation | Limits compensation and makes jointly weak domains more visible. | Zero is absorbing; near-zero values dominate; exponents and any floor require justification. | Scale properties, treatment of zero, robustness and calibration against reference judgments. |
| Minimum-dominant aggregation | Conservative and easy to explain when the weakest domain should dominate. | Discards information from the stronger domain and creates discontinuities around the minimum. | Evidence that the intended use warrants dominance rather than balanced comparison. |
| Nonlinear penalties | Can distinguish severity, multiplicity and interactions without a universal linear decrement. | High flexibility can hide arbitrary curves, overfitting and non-monotonic behaviour. | Prespecified functional family, calibration, external validation and adversarial tests. |
| Score caps | Prevents an excellent ordinary profile from masking a qualified critical concern. | Threshold discontinuities; an incorrectly triggered cap has large impact. | Cap eligibility, cap level, identity/applicability gates and false-positive analysis. |
| Critical override | Can represent a formally disqualifying condition, including a future zero rule. | Conflation of hazard and risk or weak identity may produce unjustified extreme results. | Published rule, strong applicability, qualified source, validation and release approval. |
| Hierarchical combination | Keeps ordinary aggregation, missingness and criticality as separately auditable layers. | More governance and explanation complexity; interactions between layers must be frozen. | Layer order, no-double-counting invariants, trace schema and end-to-end validation. |

### 8.2 Mandatory invariants

Every future aggregation candidate must satisfy and test these invariants:

1. Worsening a qualified input cannot improve the applicable score, all other
   canonical inputs being equal.
2. Losing data cannot improve a score, coverage or confidence.
3. A cap can only maintain or reduce the uncapped result.
4. A `hazard_flag` is not equivalent to a `risk_flag`.
5. Evidence outside the frozen cutoff or declared scope does not modify the
   score.
6. Technical row, object or ingestion order does not modify the result; only
   semantically declared order may be used by a published rule.
7. Missing data never becomes an invented dose, concentration or zero.
8. The same canonical input and the same scoring version produce the same
   output.

Additional candidate tests must demonstrate that a guardrail is not counted
again as an ordinary penalty and that removing an applicable adverse condition
cannot make a score worse.

## 9. Criticality contract

The criticality vocabulary is:

```text
hazard_flag
risk_flag
critical_disqualifier
```

Scientific flag type and scoring effect are separate concepts. A future
published policy may classify the scoring effect of a specific, fully traced
flag as:

```text
informational_only
score_affecting
ceiling_blocking
override_triggering
```

This contract assigns no individual flag to a score-affecting,
ceiling-blocking or override-triggering category. Only a future approved policy
may make such an assignment through an explicit rule. An unassigned scoring
effect has no numerical consequence.

### 9.1 `hazard_flag`

A `hazard_flag` records a qualified potential to cause harm for a stated
endpoint and context. It is informative. Its presence alone applies no
penalty, cap, ceiling or override, does not prevent a score of `100` and does
not imply that product exposure is sufficient to create risk.

### 9.2 `risk_flag`

A `risk_flag` requires compatible hazard, exposure and applicability under a
future approved risk protocol. It may enable a penalty or cap only when a
published product-scoring policy explicitly binds the flag to that action.

### 9.3 `critical_disqualifier`

A `critical_disqualifier` is a formally satisfied rule, not a descriptive
opinion. It may enable a severe cap or zero only through a published rule. Every
future disqualifier must include at least:

```text
rule_id
rule_version
reason_code
target_identity
identity_confidence
jurisdiction
effective_date
product_category
applicability_evidence
qualifying_source
source_version
source_cutoff
override_action
trace_reference
```

The rule must also preserve the evidence and product-input digests used to
establish these fields.

The following are not sufficient for a disqualifier:

- being artificial;
- being controversial;
- being poorly known;
- one study in isolation;
- hazard without exposure;
- fuzzy or unresolved identity;
- simple presence of an allergen in the general assessment;
- an open re-evaluation without further qualifying evidence.

## 10. Missing-data, evaluability, coverage and confidence contract

The future protocol must keep these concepts separate:

```text
available_evidence_assessment
evaluability_status
assessment_coverage
confidence
incomplete_data_guardrail
```

- `available_evidence_assessment` describes what the eligible, usable data
  support without inventing missing inputs.
- `evaluability_status` states whether the complete in-scope tri-score can be
  computed under the applicable published policy.
- `assessment_coverage` describes how much of the required assessment input is
  available and usable.
- `confidence` describes reliability of identity, measurement, provenance,
  applicability, evidence and method.
- `incomplete_data_guardrail` prevents missing information from improving a
  displayed score while remaining explicitly epistemic rather than a risk
  penalty.

Coverage must not be represented only by a raw field count. The internal
breakdown must include at least:

```text
ingredient_identity_coverage
ingredient_regulatory_coverage
composition_quantity_coverage
nutrition_required_field_coverage
nutrition_basis_coverage
category_coverage
critical_gate_coverage
```

The breakdown calculation, required-input sets and any overall coverage
aggregation remain open. Their future rules must be versioned and traced.

### 10.1 Evaluability states

```text
computable
not_computable
```

- `computable`: all policy-required conditions for producing the complete
  in-scope food tri-score are satisfied; all three integer scores are present.
- `not_computable`: at least one condition required by the future published
  evaluability policy is not satisfied; no numeric substitute score is
  produced.

`not_computable` is a successful semantic result, not a technical failure and
not evidence that the product is favourable, unfavourable or scored zero. The
future user interface must distinguish an actual computed score of `0` from
“valutazione non disponibile”.

The future policy must define required inputs, component indispensability and
the treatment of missing or unusable data. Those choices remain open. This
contract defines no minimum coverage, confidence or completeness threshold and
no numeric fallback for insufficient data.

### 10.2 Confidence states

```text
high
moderate
low
```

- `high`: all policy-required identity, provenance, applicability and input
  quality gates for the claimed output pass. Exact gates remain open.
- `moderate`: limitations exist but the assessment remains sufficiently stable
  for the future approved intended use.
- `low`: material uncertainty or weak input quality limits interpretation, but
  the exact canonical conclusion can still be stated under a future rule.

Confidence describes confidence in the exact result or non-computability
conclusion that is emitted. It is neither an evaluability state nor confidence
that the product is safe. A confidence label cannot make a `not_computable`
result numeric.

The future evaluability and confidence policies must determine the materiality
and effect of conditions including:

- unresolved identity for a material declared ingredient;
- unresolved ingredient/substance relationship or product applicability;
- missing solid/liquid classification where it changes the nutrition method;
- missing or ambiguous per-100-g/per-100-ml basis;
- unresolved product category required by the selected nutrient model;
- conflicting nutrition declarations without governed resolution;
- non-canonical sold, prepared or reconstituted state;
- failed material plausibility or consistency check pending review;
- missing product-composition snapshot or label provenance required for
  replay;
- a possible critical concern that cannot be confirmed or rejected because
  identity, quantity or applicability is insufficient;
- coverage below a future published evaluability gate;
- absence of another input declared critical by the applicable protocol.

The list does not determine whether any condition alone makes a result
`not_computable`; that mapping remains an open policy decision. Missing data
must never be converted into a numeric score merely to satisfy an output shape.

### 10.3 Component and overall non-computability

If either the ingredient or nutrition component is indispensable under the
future policy and is `not_computable`, the overall component is also
`not_computable` and `overall_goodness_percent` is absent or carries the future
typed non-value. A different treatment requires an explicit, scientifically
approved and published policy; it cannot arise from an implicit default.

Until evaluability, coverage, confidence and aggregation policies are approved,
numerical product-scoring runtime remains blocked.

## 11. Meaning of score endpoints

Endpoint semantics are protocol bounds, not absolute facts about health.
They apply only to scores produced in a `computable` result. A missing score in
a `not_computable` result is neither endpoint `0` nor endpoint `100`.

| Endpoint | Required semantic meaning |
|---|---|
| `ingredient_goodness_percent = 0` | The future published ingredient policy's lower bound has been reached through a fully defined domain-floor or ingredient zero rule with sufficient traceability. It does not automatically mean poisonous, illegal or certain to cause disease. |
| `ingredient_goodness_percent = 100` | The future ingredient policy's ceiling has been reached with its required coverage and confidence, no applicable concern preventing the ceiling, and every material assessable criterion satisfied. It does not establish unlimited safety. |
| `nutrition_goodness_percent = 0` | The future nutrition policy's least favourable category- and basis-specific bound has been reached with sufficient usable data. It is not a toxicological or clinical conclusion. |
| `nutrition_goodness_percent = 100` | The future nutrition policy's most favourable category- and basis-specific bound has been reached with required coverage and confidence. It does not make the product suitable in unlimited amounts or for every diet. |
| `overall_goodness_percent = 0` | A future formally published, reproducible `zero_override` has been satisfied. Ordinary averaging, controversy, missing data or one low component cannot silently create overall zero. |
| `overall_goodness_percent = 100` | Both domains are at their published ceiling, required coverage is satisfied, confidence is `high`, and no specifically published ceiling-blocking condition or cap applies. An informational `hazard_flag` alone does not prevent this endpoint. |

For every score:

`0` does not automatically mean:

- poisonous;
- prohibited;
- a certain cause of disease.

`100` does not mean:

- perfect;
- safe in unlimited quantities;
- appropriate for every person;
- a substitute for a balanced diet.

## 12. User-facing contract

For a `computable` result, the required Italian labels are:

```text
Bontà degli ingredienti: NN%
Bontà dei valori nutrizionali: NN%
Valutazione complessiva del prodotto: NN%

Copertura della valutazione: NN%
Affidabilità: alta | moderata | bassa
```

For a `not_computable` result, the interface must not render `0%` or another
numeric placeholder. It must instead show:

```text
Valutazione complessiva del prodotto: valutazione non disponibile
```

Component labels must use the same non-numeric wording when the corresponding
score is absent. Coverage, confidence, limitations and missing inputs remain
separately visible as required by the future communication policy.

The required short disclaimer for a `computable` result is:

> Valutazione generale e versionata del prodotto, calcolata sui dati
> disponibili. Non è una diagnosi, una prescrizione o una raccomandazione
> personale.

For a `not_computable` result, the required short disclaimer is:

> La valutazione numerica generale del prodotto non è disponibile con i dati
> utilizzabili. Non equivale a un punteggio zero e non è una diagnosi, una
> prescrizione o una raccomandazione personale.

Possible descriptive bands are recorded only as unapproved vocabulary:

```text
molto limitata
limitata
intermedia
buona
molto buona
```

No boundary, threshold, color or behavioral recommendation is defined for
these bands. They must not be exposed until their thresholds, comprehension,
accessibility and claim implications have been reviewed and approved.

The ordinary user experience is not required to display a bibliography. It
must nevertheless be possible for governance and audit tooling to trace every
rule to its internal methodological provenance.

## 13. Future premium boundary

The only approved conceptual separation is:

```text
general_product_assessment
personalized_assessment
```

- `general_product_assessment` remains product-specific and user-independent.
- A future `personalized_assessment` is a separate result and must not mutate,
  overwrite or retroactively reinterpret the general product score.
- Personalized assessment belongs to a separate premium Wave.
- The current capability flag is `personalized_assessment_v1 = false`.
- No personal or health-data table is introduced by this contract.
- No personal dose, portion, frequency or daily-diet contribution is calculated
  by this contract.
- GDPR/legal review, explicit purpose and legal basis, consent where required,
  data minimisation, security design, retention/deletion rules, access control,
  audit and a DPIA determination are mandatory gates before implementation.

This file does not design the definitive premium schema, payment model,
subscription flow or personal recommendation engine.

## 14. AI and source governance

AI may assist future governed work with research, extraction, structuring,
comparison, citation verification, explanation drafting and adversarial review.

AI must not:

- act as the runtime scientific source of truth;
- create a score when the policy is absent or non-executable;
- invent weights, thresholds, evaluability gates or missing quantities;
- select a winning benchmark without governed scientific authority;
- alter a deterministic score after calculation;
- produce different results for the same canonical input and version.

Source updates must create new governed source snapshots and, when observable
results may change, a new scoring version plus impact analysis. Historical
results retain the original inputs, source cutoff, rule version and trace.

## 15. Relationship to current WYE Phase 7 artifacts

The current Phase 7 architecture for canonical artifacts, evidence snapshots,
mapping state, execution identity, results, trace and historical replay may be
reused by a future product-scoring protocol after an authorized design freeze.

Current limitations remain binding:

- the QPS candidate selects EFSA QPS evidence for substance findings and is not
  a product-scoring policy;
- its candidate and golden corpus remain frozen and unapproved;
- the current scientific execution target contract supports `substance` and
  `ingredient`, not `product`;
- product composition, nutrition state and product history are not yet a
  complete replay-safe scoring input;
- legacy `product_scores`, legacy risk fields and placeholder scoring are not
  scientific inputs to this contract;
- no future product-scoring candidate exists yet.

A future implementation must begin with a new product-scoring candidate and
corpus, not an in-place change to `1.0.0-candidate.1`.

## 16. Decision matrix

`PSC-OD-001` and `PSC-OD-002` are `DECIDED` through explicit product-owner
approval recorded on `2026-09-01`. The remaining 20 decisions, `PSC-OD-003`
through `PSC-OD-022`, remain `OPEN`.

| Decision ID | Description | Domain | Prerequisites | Required decision authority | Future artifact | Blocking? | Current status |
|---|---|---|---|---|---|---|---|
| `PSC-OD-001` | First-release intended use, general reference population and permitted product-claims boundary: Option A. | Cross-domain/product | Claims inventory, user scenarios and completed internal RFC review; external wording reviews remain separate gates | Product owner; scientific and legal/regulatory review remain downstream release gates | Intended-use and claims decision record | RESOLVED FOR PRODUCT DECISION | `DECIDED` |
| `PSC-OD-002` | Goodness is a transparent, versioned methodological assessment of compositional and nutritional favourability under declared WYE criteria, not personal health or clinical risk. | Cross-domain/scientific | Intended use, construct review, alternative definitions | Product owner for semantic/product boundary; multidisciplinary scientific validation remains a downstream gate | Goodness Construct decision record | RESOLVED FOR SEMANTIC/PRODUCT DECISION | `DECIDED` |
| `PSC-OD-003` | Define jurisdiction-, date-, category- and condition-aware regulatory-status ontology. | Ingredient/regulatory | Source inventory, legal mappings, temporal model | Regulatory specialist + data steward | Regulatory ontology candidate | BLOCKING | `OPEN` |
| `PSC-OD-004` | Freeze non-numeric ingredient-state resolution, coexistence and primary-state precedence. | Ingredient | Regulatory ontology, evidence/applicability vocabularies | Toxicology reviewer + regulatory specialist | Ingredient-state policy candidate | BLOCKING | `OPEN` |
| `PSC-OD-005` | Map approved ingredient states and dimensions to a 0..100 ingredient scale without conflating missingness or uncertainty with risk. | Ingredient/numeric | Approved state policy, reference judgments, calibration corpus | Scientific review panel + validation owner | Ingredient numerical-mapping candidate | BLOCKING | `OPEN` |
| `PSC-OD-006` | Select and validate product-level aggregation across multiple ingredients, relationships and quantities. | Ingredient/aggregation | Ingredient mapping, QUID/order semantics, adversarial cases | Scientific review panel + validation owner | Ingredient aggregation candidate | BLOCKING | `OPEN` |
| `PSC-OD-007` | Select the base nutrient-profile construct or justified WYE-specific combination. | Nutrition | Benchmark comparison, intended use, WYE data audit | Nutrition-science panel + public-health reviewer | Nutrient-profile selection RFC | BLOCKING | `OPEN` |
| `PSC-OD-008` | Freeze authoritative product-category, solid/liquid and sold/prepared/reconstituted rules. | Nutrition/product | Category sources, label-state model, edge-case corpus | Nutrition reviewer + regulatory specialist + data steward | Category and preparation policy candidate | BLOCKING | `OPEN` |
| `PSC-OD-009` | Define total, added and free-sugar semantics and what may be derived from declared data. | Nutrition | Label availability study, source definitions, derivation validation | Nutrition-science panel | Sugar semantics and derivation RFC | BLOCKING | `OPEN` |
| `PSC-OD-010` | Define treatment of protein, fibre, fruit/vegetable/legume components, sweeteners and supplementary nutrients. | Nutrition | Intended use, category policy, data coverage study | Nutrition-science panel | Nutrient component policy candidate | BLOCKING | `OPEN` |
| `PSC-OD-011` | Map approved nutrition components to a category-aware 0..100 scale. | Nutrition/numeric | Selected nutrient model, category rules, calibration corpus | Nutrition-science panel + validation owner | Nutrition numerical-mapping candidate | BLOCKING | `OPEN` |
| `PSC-OD-012` | Select the ordinary overall aggregation family and its parameters. | Overall/aggregation | Approved domain scales, construct study, sensitivity analysis | Multidisciplinary scientific panel + validation owner | Overall aggregation candidate | BLOCKING | `OPEN` |
| `PSC-OD-013` | Define flag-effect classification, applicable critical caps, severity classes and no-double-counting behavior without treating hazard alone as a score effect. | Criticality/overall | Criticality ontology, validation corpus, false-positive analysis | Scientific panel + regulatory reviewer + validation owner | Critical cap and flag-effect policy candidate | BLOCKING | `OPEN` |
| `PSC-OD-014` | Define the closed set of zero-override rules and prove reproducibility and user-safe interpretation. | Criticality/overall | Disqualifier contract, legal/scientific cases, communication testing | Scientific reviewer + legal reviewer + release approver | Zero-override RFC and golden cases | BLOCKING | `OPEN` |
| `PSC-OD-015` | Define required-input sets and aggregation of coverage, including critical-gate coverage. | Missing data | Input inventory, domain policies, missingness simulations | Scientific reviewers + data steward + validation owner | Coverage policy candidate | BLOCKING | `OPEN` |
| `PSC-OD-016` | Define the evaluability and missing-data policy, including component indispensability, `not_computable` conditions and interaction with overall aggregation, without a numeric fallback. | Missing data/evaluability | Coverage policy, user testing, sensitivity and bias analysis | Scientific panel + validation owner + product communication reviewer | Evaluability and missing-data RFC | BLOCKING | `OPEN` |
| `PSC-OD-017` | Freeze confidence dimensions, state derivation and interaction with evaluability without using confidence as an evaluability proxy. | Confidence/uncertainty | Evidence-quality framework, data-quality audit, use cases | Scientific reviewers + data steward | Confidence policy candidate | BLOCKING | `OPEN` |
| `PSC-OD-018` | Freeze integer precision, intermediate arithmetic, rounding, boundary and canonical serialization rules. | Determinism/technical | Approved formulas, canonicalization compatibility analysis | Data/model steward + validation owner | Numeric execution profile | BLOCKING | `OPEN` |
| `PSC-OD-019` | Define golden corpus, external benchmarks, sensitivity, monotonicity, robustness and comprehension validation. | Validation | All policy candidates, representative product corpus | Independent validation owner + external scientific reviewers | Product-scoring validation plan and corpus | BLOCKING | `OPEN` |
| `PSC-OD-020` | Approve user-facing language, bands, colors, limitations and non-misleading interpretation. | Communication/claims | Final scale behavior, endpoint study, accessibility and comprehension tests | Product communication reviewer + scientific reviewer + legal reviewer | User communication and claims package | BLOCKING FOR USER RELEASE | `OPEN` |
| `PSC-OD-021` | Freeze internal source-register schema, source hierarchy, update cadence, cutoff and supersession procedure. | Provenance/governance | Benchmark register, source ingestion capabilities | Scientific governance owner + data steward | Source governance RFC | BLOCKING | `OPEN` |
| `PSC-OD-022` | Define the legal and scientific boundary between general product information and future personalized recommendations. | Premium/privacy | Intended use, GDPR analysis, medical-device and consumer-law screening | Privacy counsel + legal reviewer + clinical governance reviewer | Premium boundary and DPIA pre-assessment | NON-BLOCKING FOR BASE CANDIDATE; BLOCKING FOR PREMIUM | `OPEN` |

### 16.1 `PSC-OD-001` decision record

```text
decision_id: PSC-OD-001
decision_status: DECIDED
decision_owner: Product owner
decision: Option A
decision_date: 2026-09-01
source_of_authority: Explicit product-owner approval
```

The first WYE product-scoring release is a general informational tool for adults
in the general population consulting packaged foods and beverages within this
contract's domain. Its outputs are methodological and versioned. Numeric scores
may be shown only when `evaluability_status = computable`; `not_computable` is a
valid non-numeric outcome and is not score zero.

The decision authorizes no personal, professional, clinical, therapeutic or
dietary assessment; dose, portion, frequency or individual recommendation;
scientific or clinical approval; legal/regulatory approval; scoring formula;
runtime; or user-facing release. Pregnancy, minors, allergies, diseases,
medicines, specifically regulated supplements and non-food domains are outside
the supported use or require a separate policy. External wording remains
subject to scientific, communication and legal/regulatory review. The ordinary
UI requires no bibliography, and premium personalization remains deferred to a
separate future Wave.

### 16.2 `PSC-OD-002` decision record

```text
decision_id: PSC-OD-002
decision_status: DECIDED
decision_owner: Product owner
decision: Option B
decision_date: 2026-09-01
source_of_authority: Explicit product-owner approval
decision_scope: semantic and product boundary of the construct
scientific_status: internal evidence-informed methodology; no external scientific validation performed
legal_or_regulatory_status: no legal or regulatory approval implied
implementation_status: no formulas, scales or runtime approved
```

For WYE, goodness is a transparent, versioned methodological assessment of the
compositional and nutritional favourability of a packaged food or beverage
against declared and applicable WYE criteria for adults in the general
population. It does not represent personal health, absolute healthiness,
universal safety, probability of clinical benefit or harm, exposure, dose,
clinical risk, regulatory compliance or individual suitability.

This product-owner decision closes only the semantic and product boundary in
`PSC-OD-002`. It does not approve a formula, weight, threshold, nutrient-profile
model, ingredient rule, aggregation method, runtime, release or publication. It
does not constitute external scientific validation or scientific, clinical,
legal or regulatory certification. Method validation, internal scientific
governance and all applicable downstream decision gates remain required.

## 17. Acceptance checklist

- [x] The tri-score domain is limited to applicable food products, and the
  first-release target population and claims boundary are decided separately in
  `PSC-OD-001`.
- [x] Immediate internal document audiences are identified separately from
  final intended users.
- [x] Non-claims are explicit.
- [x] Evaluability, the three conditional scores and support metadata are
  defined separately.
- [x] `not_computable` emits no substitute numeric score, and score `0` remains
  a computed endpoint.
- [x] Percentage is explicitly distinct from probability and clinical safety.
- [x] Ingredient, nutrition and overall semantics are separated.
- [x] Regulatory status, evidence, hazard, exposure, risk, applicability,
  confidence and uncertainty remain separate.
- [x] `hazard_flag`, `risk_flag` and `critical_disqualifier` are distinct.
- [x] Missingness is separate from scientific risk.
- [x] Coverage and confidence are explicit.
- [x] Minimum coverage-breakdown dimensions are recorded.
- [x] Evaluability, coverage, confidence and missing data remain distinct.
- [x] An informational `hazard_flag` alone has no score effect and does not
  block endpoint `100`.
- [x] No definitive scoring formula is introduced.
- [x] No weights are introduced.
- [x] No WYE score thresholds are introduced.
- [x] No numeric missing-data fallback is introduced.
- [x] No cap value or zero rule is approved.
- [x] No runtime authority is granted.
- [x] The QPS candidate `1.0.0-candidate.1` is not modified or promoted.
- [x] Premium implementation and definitive schema remain out of scope.
- [x] Sources remain internal provenance without a required user-facing
  bibliography feature.
- [x] The benchmark register does not select a base model.
- [x] `PSC-OD-001` and `PSC-OD-002` are `DECIDED` through explicit
  product-owner approval; `PSC-OD-003` through `PSC-OD-022` are exactly 20
  decisions and remain `OPEN`.

## 18. Exit state

```text
food-product tri-score semantic contract: DRAFT
scientific approval: NOT PRESENT
PSC-OD-001: DECIDED — OPTION A — PRODUCT OWNER APPROVED
PSC-OD-002: DECIDED — OPTION B — PRODUCT OWNER APPROVED
PSC-OD-003 through PSC-OD-022: OPEN
legal/regulatory review of external wording: REQUIRED
published scoring policy: NOT PRESENT
product-scoring candidate: NOT PRESENT
numeric runtime authority: BLOCKED
personalized_assessment_v1: false
```

The recorded product decisions must pass their dedicated reviews before
downstream use. Subsequent work must resolve one bounded `OPEN` decision through
its declared authority and artifact. It must not implement numerical scoring,
persistence or runtime from this draft.
