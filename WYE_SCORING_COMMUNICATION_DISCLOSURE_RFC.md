DRAFT — SCORING COMMUNICATION DECISION REQUIRED

# WYE — Scoring Communication & Disclaimer RFC

## Status and authority

    decision_id: PSC-OD-020
    decision_status: OPEN
    proposal_status: PROPOSED, NOT APPROVED
    document_authority: decision-preparation RFC only
    governance: INTERNAL INFORMATIONAL ASSURANCE
    runtime_authority: NONE
    release_authority: NONE
    external_validation_and_certification: FUTURE / OPTIONAL / NOT PRESENT

This RFC prepares future communication and disclosure policy only. It approves
no production UI copy, runtime behavior, release behavior, API, database
change, numerical method, label, badge, color, grade, ranking or product claim.

## 1. Scope and non-goals

The future policy concerns communication of distinct WYE outputs and states:
"ingredient_score", "ingredient_goodness_percent",
"nutrition_goodness_percent", a possible future "overall_score", and the
"computable", "not_computable" and "non_applicable" states. It also prepares
future disclosure of coverage, confidence, uncertainty, missingness and
evaluability.

These constructs remain distinct. In particular, an ingredient score is not a
nutrition score; neither is a possible future overall score. Coverage,
confidence, uncertainty, missingness and evaluability qualify evidence or
availability and do not establish a user-facing assessment by themselves.

Out of scope are final production UI copy, runtime implementation, API or
database changes, release approval, medical, clinical, therapeutic or personal
dietary advice, dose, frequency or portion advice, and regulatory, safety,
certification or individual-suitability claims.

## 2. Decision context and dependencies

PSC-OD-020 concerns future user-facing language, bands, colors, limitations
and non-misleading interpretation. It remains OPEN. This RFC resolves no
communication decision and confers no presentation authority.

| Dependency | Communication relevance | Current state |
| --- | --- | --- |
| PSC-OD-005 and PSC-OD-006 | Ingredient mapping and product ingredient aggregation boundaries | OPEN |
| PSC-OD-007 through PSC-OD-011 | Nutrition construct, inputs and numeric boundary | OPEN |
| PSC-OD-012 | Future overall-score presentation policy | OPEN |
| PSC-OD-013 through PSC-OD-019 | Criticality, missingness, confidence, determinism and assurance | OPEN |
| PSC-OD-022 | Boundary between general information and future personalization | OPEN |

Current candidates are internal heuristic baselines only. They do not authorize
final user language, a release, a clinical construct or an external-validation
claim.

## 3. Candidate communication alternatives

All alternatives below are CANDIDATE — NOT APPROVED. None establishes final
copy, an implementation, a badge, a grade, a color, a threshold or runtime
behavior.

| Alternative | Candidate communication approach | Main open risk |
| --- | --- | --- |
| Option A — Separate component display | Present component outputs separately, with no single overall label. | May be less concise for a future user journey. |
| Option B — Plain-language notices | Add explanatory notices to separate component presentation. | Wording and comprehension remain untested. |
| Option C — Component display plus confidence/coverage badges | Present separate, explicitly non-authoritative candidate badges with component outputs. | Badges could be mistaken for correctness or quality. |
| Option D — Overall presentation after PSC-OD-012 approval | Consider an overall presentation only after future PSC-OD-012 approval. | Dependencies and interpretation remain unresolved. |
| Option E — Staged MVP disclosure-first model | Use cautious, broad informational explanations; defer authority-bearing presentation. | Requires future comprehension and product review. |

## 4. Recommended MVP direction

PROPOSED, NOT APPROVED

Recommend Option E — staged MVP disclosure-first communication model — for
internal review only. It prioritizes clarity over authority, treats scores as
broad informational indicators, discloses non-computability rather than hiding
it, and keeps external validation and certification separate from the MVP.

This direction does not authorize runtime copy, release behavior, final labels,
grades, colors, badges, rankings, thresholds, formulas, weights or an overall
numerical candidate. Any future user-facing implementation requires separately
authorized communication, product and release work.

## 5. Required disclaimer families

The following are families of future disclaimers, not final UI copy:

| Family | Future disclosure purpose |
| --- | --- |
| General informational use | Explain that WYE provides broad, approximate guidance about packaged foods. |
| Not a doctor | State that WYE is not a doctor and does not diagnose, treat or give clinical advice. |
| No personal advice | Exclude personal dietary, therapeutic, dose, frequency and portion recommendations. |
| No certification or compliance claim | Exclude safety, healthiness, regulatory compliance and individual-suitability certification. |
| External validation boundary | State that external validation and certification are future, optional and not present. |
| Internal heuristic assurance | Explain Internal Informational Assurance and the internal heuristic nature of current candidates. |
| Missing data and unavailable output | Explain missingness and why an output may be not_computable. |
| Numeric zero distinction | Explain that a computed zero is not the same as unavailable data. |
| Confidence and coverage | Explain evidence limitations without presenting confidence as correctness or coverage as quality. |

The MVP goal is not a scientifically perfect or externally certified app. It
is approximate broad food guidance with clear limits; external validation and
certification are optional future work.

## 6. State-specific communication requirements

These are future requirements for a policy and not final labels, numbers,
badges, grades or colors.

| State or situation | Future communication requirement |
| --- | --- |
| Computable score | Preserve its domain identity and broad informational limitation. |
| Numeric zero | Distinguish a valid numeric result from missing or unavailable data. |
| not_computable | Explain availability and the relevant missing, conflicting or non-comparable condition. |
| non_applicable | Preserve non-applicability without framing it as favourable or adverse. |
| Partial coverage | Disclose scope limits without converting coverage into a score effect. |
| Low confidence | Disclose evidence qualification without presenting it as correctness. |
| High uncertainty | Disclose uncertainty without a hidden numerical penalty. |
| Ingredient/nutrition disagreement | Preserve the separate constructs and avoid forcing a single interpretation. |
| Ingredient criticality flags | Preserve contextual flags without turning them into user-facing safety claims. |
| Regulatory/informational flags | Preserve context without suggesting legal status or certification. |
| Future overall score unavailable | Explain that an overall product layer may be unavailable or deferred. |

## 7. Anti-overclaim rules

Future communication must not imply that a product is healthy or unhealthy as
a certified property, safe or unsafe for an individual, medically recommended,
dietarily recommended, legally compliant or non-compliant, approved by an
external body, scientifically proven, clinically validated or individually
suitable.

It must not target children, pregnancy, diseases, allergies, intolerances or
other personal conditions. It must not offer dosage, portion or frequency
advice. It must not turn an internal heuristic, a score, a flag, confidence or
coverage into a safety, efficacy or correctness statement.

## 8. Traceability and user trust

Future user-facing work should:

- show why a score is unavailable when it is not_computable;
- indicate missing or uncertain data without presenting confidence as
  correctness or coverage as quality;
- keep ingredient and nutrition domains separate;
- preserve provenance and deterministic replay internally;
- avoid hiding disagreement, partial evidence or unavailable states;
- avoid implying that a possible future overall score replaces component
  limitations.

## 9. Future review and assurance plan

Before any user-facing use is considered, future, separately authorized work
should check:

- comprehension of disclaimers and unavailable states;
- false-authority wording and overclaim risk;
- misunderstanding of numeric zero versus not_computable;
- misunderstanding of confidence, coverage and uncertainty;
- component disagreement and cross-domain consistency;
- visibility and accessibility of disclaimers;
- consistency across ingredient, nutrition and possible future overall
  displays;
- optional future legal and product review, which is not present now.

This is a future assurance plan only. It creates no test result, validation
claim, final copy, implementation or release authority.

## 10. Proposed decision record draft

    decision_id: PSC-OD-020
    decision_status: OPEN
    proposal_status: PROPOSED, NOT APPROVED
    product_owner_selection: NOT PRESENT
    final_copy: NOT PRESENT
    communication_authorization: NOT PRESENT
    implementation_authorization: NOT PRESENT
    runtime_authority: NONE
    release_authority: NONE
    external_validation: FUTURE / OPTIONAL / NOT PRESENT

## 11. Next steps

1. Read-only review of this decision-preparation RFC.
2. Product-owner discussion of the candidate direction only, if requested.
3. Separate authorization before any final copy, candidate package, user
   research, implementation, release, commit or push is prepared.

    PSC-OD-005: OPEN
    PSC-OD-006: OPEN
    PSC-OD-007 through PSC-OD-012: OPEN
    PSC-OD-013 through PSC-OD-020: OPEN
    PSC-OD-022: OPEN
    runtime: NOT AUTHORIZED
    release: NOT AUTHORIZED
