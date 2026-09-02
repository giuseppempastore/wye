DRAFT — OVERALL PRODUCT SCORE DECISION REQUIRED

# WYE — Overall Product Score Policy RFC

## Status and authority

    decision_id: PSC-OD-012
    decision_status: OPEN
    proposal_status: PROPOSED, NOT APPROVED
    document_authority: decision-preparation RFC only
    governance: INTERNAL INFORMATIONAL ASSURANCE
    runtime_authority: NONE
    release_authority: NONE
    external_validation_and_certification: FUTURE / OPTIONAL / NOT PRESENT

This RFC prepares a future overall product-score policy only. It selects,
closes, approves and implements no decision, formula, numerical candidate,
runtime behavior, release behavior or product claim.

## 1. Purpose, scope and boundaries

A future "overall_score" is a possible product-level presentation layer over
the distinct component outputs "ingredient_goodness_percent" and
"nutrition_goodness_percent". It is not an ingredient score, nutrition
score, medical assessment, safety assessment or individual recommendation.

The future presentation layer must remain separate from "ingredient_score",
"ingredient_goodness_percent", "nutrition_goodness_percent", coverage,
confidence, uncertainty, missingness, evaluability, criticality, hazard,
exposure, risk, regulatory status, ontology labels and informational flags.
Those dimensions may need disclosures or gates in a future policy; none is a
score input, proxy, multiplier, penalty or hidden effect under this RFC.

Out of scope are runtime, API, UI, database, migrations, release behavior,
personalization, dose, frequency, portion advice, diagnosis, treatment,
medical or clinical claims, therapeutic advice, regulatory claims,
certification and individual-suitability claims.

## 2. Decision context and dependencies

"PSC-OD-012" asks for selection of the ordinary overall aggregation family
and its parameters. It remains OPEN; this RFC neither resolves its
dependencies nor converts internal candidates into authority.

| Dependency | Why it matters | Current state |
| --- | --- | --- |
| PSC-OD-005 | Ingredient-scale semantics and mapping boundary | OPEN |
| PSC-OD-006 | Product ingredient aggregation/evaluability | OPEN |
| PSC-OD-007–011 | Nutrition construct, inputs and scale boundary | OPEN |
| PSC-OD-013–019 | Criticality, missingness, confidence, determinism and validation | OPEN |
| PSC-OD-020 | User-facing language and non-misleading interpretation | OPEN |

Current ingredient and nutrition packages are internal heuristic baselines
only. Their existence does not authorize a future overall score or a component
combination method.

## 3. Candidate alternatives for PSC-OD-012

All alternatives below are CANDIDATE — NOT APPROVED. None establishes a
formula, weight, threshold, cap, floor, veto, override, category rule or
runtime behavior.

| Alternative | Candidate description | Principal open risk |
| --- | --- | --- |
| Option A — Separate components | No single overall score in the MVP; show ingredient and nutrition components separately when suitable. | May not satisfy a future presentation need. |
| Option B — Simple two-component mean | A future simple combination when both components are computable. | Conceals unresolved semantic and communication choices. |
| Option C — Evidence-gated composite | A future composite only when both components and required disclosures pass defined gates. | Gates and their meaning remain unresolved. |
| Option D — Category-aware composite | A future product-type or category-aware combination. | Category rules and transferability remain unresolved. |
| Option E — Staged MVP overall policy | Disclosure-first staged policy; defer an overall score until component readiness and communication gates are satisfied. | Requires bounded future evidence and communication work. |

## 4. Recommended candidate direction

PROPOSED, NOT APPROVED

Recommend Option E — staged MVP overall policy, disclosure-first — for
internal review only. It allows WYE to continue broad informational food
guidance without presenting a premature single product judgment. In the MVP,
the default preparation direction is to preserve distinct component outputs
and their limitations until readiness and communication gates are explicitly
considered.

This recommendation does not authorize a formula, weight, threshold, cap,
floor, veto, override, category rule, aggregation family, numerical behavior,
runtime or release. An exact numerical overall candidate package may be
prepared later only after explicit product-owner authorization and a separately
bounded preparation task.

## 5. State handling and open gates

The following are open questions for a future policy; they have no numerical
resolution in this RFC.

| Situation | Future policy question |
| --- | --- |
| One component computable and the other not_computable | Whether to present one component, defer a product layer, or use a typed unavailable state. |
| One component non_applicable | How to preserve non-applicability without treating it as favourable or adverse. |
| Both components computable but low coverage | Which disclosure and evaluability rules are needed without converting coverage into points. |
| Confidence or uncertainty mismatch | How to disclose evidence differences without using confidence or uncertainty as a score modifier. |
| Ingredient/nutrition disagreement | How to present distinct constructs without masking, reconciling or numerically forcing agreement. |
| Criticality flags | Which future gate or disclosure rules apply without turning hazard alone into a score effect. |
| Regulatory or informational flags | How to preserve context without creating hidden score effects. |
| Missingness and evaluability | Which required inputs are indispensable and when no product layer can be produced. |
| User-facing disclosure | Which limits, provenance and unavailable-state language is necessary under PSC-OD-020. |

No missing component may be replaced by zero, a midpoint, an inferred value or
another numeric fallback. A numeric zero, where a future approved component
can produce one, remains distinct from not_computable.

## 6. Semantic separation and anti-double-counting

Any future overall policy must preserve a strict evidence boundary:

- Ingredient favourability must not be reused as nutrition favourability.
- Nutrition panel properties must not be reused as ingredient favourability.
- Criticality, regulatory and ontology flags must not become hidden score
  effects.
- Component confidence, coverage, uncertainty, missingness or evaluability
  must not be converted directly into score points.
- The same evidence must not be counted through both ingredient and nutrition
  components before a future product layer is presented.
- A future overall score must not be described as an ingredient score,
  nutrition score, healthiness score, safety finding or individual assessment.

## 7. Communication dependency and MVP disclaimers

PSC-OD-020 remains an explicit dependency for any future overall-score
presentation. Before any user-facing use, future work must define
non-misleading language, limitations, unavailable states and comprehension
requirements. This RFC creates no user-facing language, bands, colors or
claim authorization.

WYE provides broad, approximate informational food guidance only. WYE is not a
doctor and does not provide diagnosis, treatment, medical, clinical,
therapeutic or personal dietary advice, or dose, frequency or portion
recommendations. WYE does not certify safety, healthiness, regulatory
compliance or individual suitability. External validation and certification are
future, optional and not present.

## 8. Future corpus and assurance plan

Before a numerical overall candidate is considered, a future, separately
authorized corpus and assurance plan should cover:

- both components high, low and mixed;
- ingredient computable with nutrition not_computable;
- nutrition computable with ingredient not_computable;
- both components not_computable;
- disagreement between ingredient and nutrition constructs;
- low coverage and conflicting confidence/uncertainty disclosures;
- criticality and regulatory/informational flags;
- category and product-state ambiguity;
- numeric zeros distinct from unavailable states;
- replay, deterministic serialization, boundary behavior and disclosure
  completeness.

The plan is future preparation only. It creates no corpus files, validation
claim, numerical rule or external benchmark result.

## 9. Proposed decision record draft

    decision_id: PSC-OD-012
    decision_status: OPEN
    proposal_status: PROPOSED, NOT APPROVED
    product_owner_selection: NOT PRESENT
    numerical_method: NOT PRESENT
    component_weighting: NOT PRESENT
    communication_authorization: NOT PRESENT
    implementation_authorization: NOT PRESENT
    runtime_authority: NONE
    release_authority: NONE
    external_validation: FUTURE / OPTIONAL / NOT PRESENT

## 10. Next steps

1. Read-only review of this decision-preparation RFC.
2. Product-owner discussion of the candidate direction only, if requested.
3. Separate authorization before any numerical candidate, corpus or review is
   prepared.
4. No runtime, release, implementation, commit or push authority follows from
   this RFC.

    PSC-OD-005: OPEN
    PSC-OD-006: OPEN
    PSC-OD-007 through PSC-OD-012: OPEN
    PSC-OD-013 through PSC-OD-019: OPEN
    PSC-OD-020: OPEN
    PSC-OD-022: OPEN
    runtime: NOT AUTHORIZED
    release: NOT AUTHORIZED
