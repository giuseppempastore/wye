DRAFT — PRODUCT/SCORING DECISION REQUIRED

# WYE — Product Ingredient Aggregation RFC

## Document status and authority

```text
decision_id: PSC-OD-006
decision_status: OPEN
proposal_status: PROPOSED, NOT APPROVED
document_authority: decision-preparation RFC only
governance: INTERNAL INFORMATIONAL ASSURANCE
runtime_authority: NONE
release_authority: NONE
external_validation_and_certification: FUTURE / OPTIONAL / NOT PRESENT
```

This RFC prepares a future decision on product-level ingredient aggregation. It
does not close, select or partially approve `PSC-OD-006`, and creates no
runtime, release or production authority.

## 1. Purpose

The future purpose of `PSC-OD-006` is to determine how WYE may aggregate
ingredient-level `ingredient_score` outputs into a product-level
`ingredient_goodness_percent`, subject to governed identity, relationship,
quantity, coverage, evaluability, provenance and disclosure requirements.

The decision is downstream of the ingredient mapping candidate and must not
retroactively change that mapping. It is distinct from nutrition scoring and
from any future overall product score.

## 2. Scope and non-scope

### 2.1 In scope

- product-level aggregation of applicable ingredient-score outputs;
- multiple declared ingredients and their typed relationships;
- declared quantities, QUID, order and missing or unreliable quantity states;
- product coverage and evaluability implications;
- `not_computable` and `non_applicable` propagation questions;
- anti-double-counting, replay and provenance;
- candidate alternatives and their validation requirements.

### 2.2 Out of scope

- changes to the ingredient-level mapping or candidate package;
- nutrition score and overall score design;
- runtime, API, UI, database, migration or implementation behavior;
- personalization, dose, frequency or portion advice;
- scientific approval, external validation or certification;
- release authorization;
- an approved product aggregation formula, weight, denominator, threshold,
  cap, floor, veto, override or numeric behavior.

## 3. MVP disclaimer and assurance position

WYE is an informational food-guidance tool for broad, non-personal packaged-
food guidance. It is not a doctor and does not provide diagnosis, treatment,
medical, clinical, therapeutic or personal dietary advice. It does not certify
food safety, regulatory compliance or individual suitability.

The MVP uses `INTERNAL INFORMATIONAL ASSURANCE`. The ingredient candidate
`1.0.1-internal` is an internal heuristic and informational baseline, not
independently validated. External validation and certification are future,
optional and not present. These limits are substantive non-claims, not a
substitute for evidence or an authorization to release a product score.

## 4. Inputs and prerequisites

| Source | What it contributes | What it does not authorize |
|---|---|---|
| Product Composition Input Contract RFC | Versioned product snapshot, source list, quantity, relationship and provenance vocabulary | An aggregation rule or extraction runtime |
| Aggregation Readiness/Dependency Bundle | Dependency register, state questions, validation scope and anti-double-counting risks | A selected aggregation family |
| Ingredient Score Candidate V1 | Option A ingredient baseline, typed output states, canonical replay and non-claim boundaries | Product-level aggregation or independent validation |
| Product Scoring Contract | Future product output vocabulary and separation of component, support and informational dimensions | A formula, evaluability gate or score parameter |
| Ingredient Score Mapping RFC | Current Option A mapping direction and Option C layered architecture | Closure of `PSC-OD-005` or `PSC-OD-006` |

Minimum prerequisites for a decision include a governed product snapshot,
resolved or explicitly unresolved ingredient relationships, quantity-state
records, provenance/replay identity, and policies for coverage, evaluability,
confidence and criticality. These prerequisites remain incomplete.

## 5. Candidate aggregation alternatives

All alternatives in this section are `CANDIDATE — NOT APPROVED`. They are
comparison objects for a future decision package, not implementation designs.
Their Option A–E labels are local to the `PSC-OD-006` aggregation comparison
and do not replace, revise or select the separate Mapping Option A or Mapping
Option B directions.

| Alternative | Candidate description | Potential strengths | Principal risks and open dependencies |
|---|---|---|---|
| Option A — Simple computable-ingredient mean | Uses only ingredient results that are computable in the declared product scope; retains non-computability separately | Transparent baseline and easy replay | Ignores order and quantity; may overstate products with many minor ingredients; requires an explicit applicable perimeter |
| Option B — Quantity-aware weighted aggregation | Considers declared quantities or QUID only when their source, basis and comparability are governed | Can reflect declared composition where evidence is adequate | Quantity data may be absent, partial, unreliable or incomparable; requires a future denominator and validation policy |
| Option C — Order-aware bounded heuristic | Treats ingredient-list order as limited contextual evidence when quantity is unavailable | May preserve label-order information without inventing a percentage | Can create false precision and hidden weighting; order is not quantity and must not become an inferred amount |
| Option D — Non-compensatory or criticality-sensitive aggregation | Retains criticality in a separate layer that may constrain interpretation after separate review | Makes exceptional concerns visible | Can become a hidden veto, cap or penalty; depends on `PSC-OD-013` and `PSC-OD-014` |
| Option E — Evidence-gated staged MVP | Uses the Option A ingredient baseline with product inputs only where identity, relationship, provenance and quantity state are explicitly known; unresolved cases remain disclosed for future policy treatment | Conservative, explainable and compatible with layered state separation | Requires exact future gates and may limit coverage; cannot substitute for a quantity, evaluability or validation policy |

No option establishes a product score, denominator, weight, threshold or
criticality effect in this RFC.

## 6. Recommended MVP direction

`PROPOSED, NOT APPROVED`

The recommended candidate direction for further review is **Option E —
Evidence-gated staged MVP**, using the current Option A ingredient baseline and
the Option C layered policy architecture.

This recommendation is deliberately conservative:

- it does not impute missing quantities or treat list order as quantity;
- it does not convert `not_computable` into zero, a midpoint, an average or a
  fallback;
- it keeps coverage, evaluability, confidence, uncertainty and missingness
  outside the ingredient goodness construct;
- it keeps criticality in a separate qualified layer and does not introduce a
  hidden cap or veto;
- it requires provenance and replay for every future product conclusion; and
- it remains limited to broad informational guidance and explainable
  disclosures.

The recommendation grants no product-owner selection, scientific approval,
runtime authority, release authority or claim authorization. A future decision
may reject, modify or replace it.

## 7. Non-approved numerical behavior

No formula or pseudo-formula is specified. No final denominator, weighting,
threshold, cap, floor, veto, override or product-level numeric behavior is
approved. If a future decision package uses an illustration, it must label it
`ILLUSTRATIVE ONLY — NOT APPROVED` and test it under a governed validation
plan.

## 8. Handling of special states

| State or condition | Future decision question | Required guardrail |
|---|---|---|
| `not_computable` | Is the ingredient indispensable for the requested product component? | No numeric fallback, zero substitution, midpoint, average or imputation |
| `non_applicable` | Is the entry outside the declared product perimeter? | It is neither a favourable nor adverse result |
| Partial mapping | Is identity and conclusion scope sufficient for the product context? | Preserve partiality and alternatives |
| `history_unavailable` | Is the product/source chain replayable? | Do not reconstruct missing history silently |
| Ambiguous identity | Can a governed identity be established? | Do not choose by convenience |
| Ambiguous relationship | Can parent, mixture, component or represented-entity scope be established? | Do not count alternatives simultaneously |
| Missing quantity | Is quantity indispensable for the future aggregation context? | Do not infer quantity from order or presence |
| Unreliable quantity | Is the declaration conflicting, stale or non-comparable? | Do not silently normalize or accept it |
| Low confidence | What exact conclusion does confidence qualify? | Confidence is not goodness or an evaluability proxy |
| High uncertainty | What remains uncertain in evidence or composition? | Uncertainty is not an adverse score effect |
| Criticality flag | Does a future separate policy define a qualified consequence? | No automatic cap, floor, veto or override |
| Regulatory flag | What scoped authority statement is present? | No automatic goodness, safety or compliance inference |
| Nutrition overlap | Is the property reserved to nutrition scoring? | Do not reuse it in ingredient aggregation |

## 9. Semantic separation controls

The future product record must maintain distinct fields and explanations for:

- `ingredient_score`;
- future `ingredient_goodness_percent`;
- `nutrition_goodness_percent`;
- overall product score;
- coverage, confidence, uncertainty, missingness and evaluability;
- criticality, hazard, exposure and risk;
- regulatory status, ontology labels and informational flags.

None of these labels is an interchangeable proxy for another. In particular,
hazard is not risk, confidence is not safety, missingness is not negative
evidence, and regulatory status is not goodness.

## 10. Anti-double-counting controls

A future candidate must prevent duplicated contribution through:

- repeated aliases for one declared ingredient entry;
- the same substance represented through several ingredient records;
- compound ingredients, sub-ingredients and mixtures together with their
  parent records;
- repeated source evidence treated as independent evidence;
- nutrition-property overlap between ingredient and nutrition components;
- regulatory labels reused as goodness;
- criticality flags reused as direct score effects.

Controls require typed identity and relationship records, provenance-preserving
deduplication review, explicit source scope and adversarial validation. This
RFC selects no deduplication algorithm.

## 11. Product-level golden corpus plan

A future corpus plan, not a corpus itself, must include cases for:

- one ingredient;
- several ingredients with the same ingredient result;
- mixed ingredient results;
- leading and trailing low-result ingredients;
- quantity missing, QUID available and order-only evidence;
- compound ingredients, sub-ingredients, mixtures and duplicated substances;
- `not_computable`, `non_applicable`, partial mapping and unavailable history;
- ambiguous identity and relationship;
- criticality and regulatory informational flags;
- nutrition overlap;
- low confidence and high uncertainty;
- replay/provenance changes; and
- adversarial double-counting, order and quantity cases.

Ingredient-level golden cases remain evidence for the ingredient candidate
only. They do not validate a product aggregation approach.

## 12. Internal assurance plan

Future internal assurance must review:

- deterministic replay and schema consistency;
- boundary and falsification cases;
- monotonicity where a future approved method claims it;
- zero distinct from `not_computable`;
- absence of numeric fallback for non-computability;
- denominator stability, if a future decision introduces a denominator;
- order and quantity sensitivity;
- anti-double-counting controls;
- disclosure, provenance and limitation coverage.

This is an assurance plan for future work, not a validation result or an
independent certification.

## 13. Product-owner candidate-direction checkpoint

```text
decision_id: PSC-OD-006
decision_status: OPEN
product_owner_candidate_direction_date: 2026-09-02
product_owner_candidate_direction_authority: Product owner
product_owner_candidate_direction: Option E — Evidence-gated staged MVP
candidate_direction_nature: CANDIDATE DIRECTION ONLY
recommendation_status: PROPOSED, NOT APPROVED
final_method_approval: NOT PRESENT
numerical_approval: NOT PRESENT
implementation_authorization: NOT PRESENT
runtime_authority: NONE
release_authority: NONE
external_validation: FUTURE / OPTIONAL / NOT PRESENT
certification: FUTURE / OPTIONAL / NOT PRESENT
```

The product owner selects Option E only as the current candidate direction for
further internal MVP preparation. `PSC-OD-006` remains `OPEN`. This candidate
direction does not approve a final formula, denominator, weight, threshold,
cap, floor, veto, override, score, runtime behavior, release behavior, API,
UI, database change or migration.

Option E remains under Internal Informational Assurance only. WYE remains a
broad informational food guidance tool, not a doctor and not a source of
medical, personal dietary, certification or regulatory advice. External
validation and certification are future, optional and not present. Any exact
numerical candidate package for `PSC-OD-006` requires a separate future
artifact and review.

## 14. Next steps

1. Perform a read-only review of this RFC for decision coherence, state
   handling, non-claims and anti-double-counting coverage.
2. Remediate any review finding without changing an open decision status.
3. Request a product-owner candidate-direction checkpoint only after review
   passes.
4. Do not recommend a commit until the review passes and a separate local
   commit authorization is given.

```text
PSC-OD-005: OPEN
PSC-OD-006: OPEN
PSC-OD-007 through PSC-OD-020: OPEN
PSC-OD-022: OPEN
runtime: NOT AUTHORIZED
release: NOT AUTHORIZED
```
