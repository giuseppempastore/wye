DRAFT — PRODUCT/SCORING DECISION REQUIRED

# WYE — Nutrition Scoring Policy RFC

## Status and authority

```text
decision_bundle: PSC-OD-007 through PSC-OD-012
decision_status: OPEN
document_authority: decision-preparation RFC only
governance: INTERNAL INFORMATIONAL ASSURANCE
runtime_authority: NONE
release_authority: NONE
external_validation_and_certification: FUTURE / OPTIONAL / NOT PRESENT
```

This RFC prepares the nutrition decision space only. It closes, selects and approves no decision, formula, score, runtime, release, implementation or overall-score behavior.

## 1. Purpose and scope

It prepares a future `nutrition_goodness_percent` for broad packaged-food guidance: nutrition facts, nutrient normalization, serving/per-100g/per-100ml bases, solid/liquid and preparation questions, nutrient roles, missingness/evaluability, separation from ingredients and future overall score, and Internal Informational Assurance.

Out of scope: medical, clinical, therapeutic or personal dietary advice; dose, frequency, portion advice; diagnosis/treatment; disease-specific scoring; runtime/API/UI/database/migrations; final overall score; external validation/certification.

## 2. Exact Contract decision mapping

| Decision | Exact Contract question | Status |
|---|---|---|
| `PSC-OD-007` | Select the base nutrient-profile construct or justified WYE-specific combination. | OPEN |
| `PSC-OD-008` | Freeze authoritative product-category, solid/liquid and sold/prepared/reconstituted rules. | OPEN |
| `PSC-OD-009` | Define total, added and free-sugar semantics and what may be derived from declared data. | OPEN |
| `PSC-OD-010` | Define treatment of protein, fibre, fruit/vegetable/legume components, sweeteners and supplementary nutrients. | OPEN |
| `PSC-OD-011` | Map approved nutrition components to a category-aware 0..100 scale. | OPEN |
| `PSC-OD-012` | Select the ordinary overall aggregation family and its parameters. | OPEN |

`PSC-OD-012` is a dependency boundary only: no overall score or aggregation family is defined here.

## 3. Candidate alternatives

All alternatives are `CANDIDATE — NOT APPROVED`.

| Alternative | Description | Risk |
|---|---|---|
| Option A — Transparent rule-based nutrition baseline | Explicit nutrient rules and simple bands. | Coarse; needs approved thresholds. |
| Option B — Existing nutrition-profile inspired model | Public-profile inspired, without certification claim. | Transferability/jurisdiction mismatch. |
| Option C — Internal balanced nutrient model | Limiting and beneficial nutrients separated. | Weights and normative choices unresolved. |
| Option D — Strict evaluability-first model | `not_computable` for missing key data. | Many products may have no output. |
| Option E — Staged MVP nutrition heuristic | Conservative, transparent internal MVP direction. | Needs future policy, corpus and assurance. |

No alternative establishes a formula, weight, threshold, cap, floor, veto, override, denominator or score.

## 4. Recommended MVP direction

`PROPOSED, NOT APPROVED`

Recommend Option E — Staged MVP nutrition heuristic for review only: internal, heuristic, broad food guidance only; preserve `not_computable` for insufficient data; keep coverage, confidence, uncertainty, missingness and evaluability separate; avoid interaction with ingredient scoring; and create no overall-score behavior. It grants no numerical, scientific, runtime, release or claim authorization.

## 5. Input contract and normalization questions

Future inputs retain energy, fat, saturated fat, carbohydrates, sugars, protein, salt/sodium, fibre if available, serving size if available, per-100g/per-100ml and per-serving bases, unit/conversion state, source document/image/run, extraction confidence, missingness, provenance and source cutoff. This is conceptual vocabulary, not a database schema.

No rule is approved for per-100g versus per-100ml, serving, solid/liquid, sold/prepared/reconstituted state, energy basis, sodium-to-salt conversion, fibre optionality or unit conversion. Missing/conflicting/non-comparable panels remain typed; serving size, category, QUID and ingredient order cannot repair evidence.

## 6. Nutrient roles and state handling

Limiting, beneficial and neutral/contextual nutrient roles are future policy only; no role has a weight or numeric effect. Nutrient absence differs from missingness. Confidence and uncertainty qualify extraction/evidence, not goodness or penalties. Total, added and free-sugar semantics remain open under `PSC-OD-009`.

| State | Non-final principle |
|---|---|
| `computable` | Requires future approved input, basis and component policy. |
| `not_computable` | No zero, midpoint, imputation, fallback or hidden penalty. |
| `non_applicable` | Outside perimeter; neither favourable nor adverse. |
| Partial panel/missing nutrient | Preserve missingness/evaluability. |
| Conversion unavailable/conflict | Preserve non-comparability. |
| Low confidence/high uncertainty | Disclosure only; no modifier. |
| Product type/serving ambiguity | Do not infer category, portion or preparation. |

Any future zero is numeric, never a missing-data sentinel.

## 7. Semantic separation and anti-double-counting

`nutrition_goodness_percent`, `ingredient_score`, `ingredient_goodness_percent` and future `overall_score` are distinct. Coverage, confidence, uncertainty, missingness, evaluability, criticality, hazard, exposure, risk, regulatory status, ontology labels and informational flags cannot become nutrition multipliers, penalties or proxies.

Do not reuse ingredient favourability/criticality, regulatory flags, ontology labels or additive/preservative labels as nutrient effects. Do not score a panel property through both ingredient and nutrition paths, duplicate converted/derived values, or present nutrition as overall score.

## 8. Future corpus and assurance plan

Future corpus only: complete panels; missing salt/sodium; sodium-to-salt conversion; missing fibre; high sugar/saturated fat/salt/protein/fibre; low/high energy; liquids/solids; serving-only/per-100-only; conflicts; low confidence; non-comparable units; unavailable panel; ingredient-side overlap.

Future assurance: deterministic replay, conversion, boundaries, schema consistency, zero distinct from `not_computable`, no numeric fallback, coverage/evaluability and confidence/uncertainty separation, anti-double-counting and disclosure completeness. This is a plan, not validation.

## 9. MVP disclaimers

WYE gives broad food guidance only. It is not a doctor and provides no diagnosis, treatment, medical, clinical, therapeutic or personal dietary advice, or dose, frequency or portion recommendations. It does not certify safety, regulatory compliance, healthiness or individual suitability. External validation/certification is future, optional and not present. Internal Informational Assurance is the MVP assurance model.

## 10. Proposed decision record draft

```text
decision_ids: PSC-OD-007 through PSC-OD-012
status: OPEN
recommendation: PROPOSED, NOT APPROVED
product_owner_selection: NOT PRESENT
numerical_approval: NOT PRESENT
implementation_authorization: NOT PRESENT
runtime_authority: NONE
release_authority: NONE
external_validation: FUTURE OPTIONAL NOT PRESENT
certification: FUTURE OPTIONAL NOT PRESENT
```

## 11. Product-owner candidate-direction checkpoint

```text
product_owner_candidate_direction_date: 2026-09-02
product_owner_candidate_direction_authority: Product owner
product_owner_candidate_direction: Option E — Staged MVP nutrition heuristic
candidate_direction_nature: CANDIDATE DIRECTION ONLY
decision_ids: PSC-OD-007 through PSC-OD-012
decision_status: OPEN
final_method_approval: NOT PRESENT
numerical_approval: NOT PRESENT
nutrient_weight_approval: NOT PRESENT
threshold_approval: NOT PRESENT
category_rule_approval: NOT PRESENT
serving_rule_approval: NOT PRESENT
conversion_rule_approval: NOT PRESENT
implementation_authorization: NOT PRESENT
runtime_authority: NONE
release_authority: NONE
external_validation: FUTURE OPTIONAL NOT PRESENT
certification: FUTURE OPTIONAL NOT PRESENT
```

Option E is selected only as the current candidate direction for further
internal MVP preparation. `PSC-OD-007` through `PSC-OD-012` remain `OPEN`.
`PSC-OD-012` is not closed and does not approve overall-score behavior.

This selection does not approve final formulas, nutrient weights, thresholds,
caps, floors, vetoes, overrides, denominators, category rules, serving rules,
conversion rules, scores, runtime behavior, release behavior, API, UI,
database change, migration, test or implementation. The direction remains
under Internal Informational Assurance only.

WYE remains a broad informational food guidance tool, not a doctor and not a
source of medical, clinical, personal dietary, therapeutic, safety,
certification or regulatory advice. External validation and certification are
future, optional and not present. Any exact numerical nutrition candidate
package requires a separate future artifact and review.

## 12. Next steps

1. Read-only review of this RFC.
2. Remediate findings without changing an open status.
3. Product-owner candidate-direction checkpoint only after review passes.
4. No commit until review passes and separate authorization is given.

```text
PSC-OD-005: OPEN
PSC-OD-006: OPEN
PSC-OD-007 through PSC-OD-012: OPEN
PSC-OD-013 through PSC-OD-019: OPEN
runtime: NOT AUTHORIZED
release: NOT AUTHORIZED
```
