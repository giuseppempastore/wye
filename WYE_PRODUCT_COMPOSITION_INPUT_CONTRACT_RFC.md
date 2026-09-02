DRAFT — PRODUCT/SCORING INPUT CONTRACT REQUIRED

# WYE — Product Composition Input Contract RFC

## Document status and authority

```text
artifact_id: WYE-PRODUCT-COMPOSITION-INPUT-CONTRACT-RFC
artifact_status: DRAFT — PRODUCT/SCORING INPUT CONTRACT REQUIRED
decision_context: PSC-OD-006 readiness only
decision_status: OPEN — NOT STARTED AS A DECISION
document_authority: preparatory product-composition input contract
governance: INTERNAL INFORMATIONAL ASSURANCE
runtime_authority: NONE
release_authority: NONE
external_validation_and_certification: FUTURE / OPTIONAL / NOT PRESENT
mapping_mvp: Option A — ordinal lookup based on internal profiles and traceable reference judgments
policy_architecture: Option C — Layered state model
future_mapping_option: Option B — possible multi-attribute development only
```

This RFC defines the product-composition input vocabulary and traceability
requirements that must exist before a future `PSC-OD-006` process can design
or select an ingredient aggregation method. It does not start, decide or
partially approve `PSC-OD-006`. `PSC-OD-005` and all other open decisions
remain open.

## 1. Purpose and decision boundary

The purpose is to make a product composition snapshot sufficiently explicit,
versioned and auditable for future product-level ingredient aggregation work.
It defines what information must be retained about product identity, declared
ingredients, relationships, quantities and provenance before any aggregation
choice is considered.

This contract is distinct from:

- ingredient-level mapping and its candidate score;
- nutrition scoring;
- overall product scoring;
- coverage, confidence, uncertainty, missingness and evaluability policies;
- runtime, API, UI, database or release behavior.

No aggregation method, product-level numeric behavior or decision alternative
is selected by this document.

## 2. MVP positioning and non-claims

WYE is an informational packaged-food guidance tool for general, non-personal
use. It is not a doctor and does not provide medical, clinical, therapeutic or
personal dietary advice. It does not diagnose, treat, certify safety, certify
regulatory compliance, or establish individual suitability.

`INTERNAL INFORMATIONAL ASSURANCE` is the current MVP documentation model.
The ingredient candidate is an internal heuristic, informational baseline and
is not independently validated. External validation and certification are
future, optional and not present. These disclosures are limits on
interpretation; they do not authorize unsupported claims.

## 3. Product composition snapshot

A future product input record must preserve a coherent, versioned composition
snapshot. This RFC defines concepts only; it does not prescribe a persistence
format or an extraction implementation.

| Concept | Required descriptive content | Boundary |
|---|---|---|
| Product identity | Stable product reference, brand or label context where available, market or jurisdiction scope and declared product form | Not a person, consumer profile or consumption scenario |
| Snapshot identity | Immutable identifier for the exact composition representation under review | A later label or reformulation is a distinct snapshot |
| Ingredient-list source | Source document, label image or other governed artifact from which the list was obtained | Source availability does not establish scientific validity |
| Ingredient order | The declared ordinal list position and original expression | Order is not an inferred amount or contribution |
| Declared quantity | Exact source expression, unit, basis, scope and whether the declaration applies to the ingredient entry | A declaration is not an aggregation rule |
| QUID information | Applicable quantitative declaration, source wording, basis and scope | QUID is not interchangeable with list order |
| Units and bases | Declared mass, volume, percentage or other source basis together with comparability status | Incompatible bases remain visible, not normalized by assumption |
| Extraction confidence | Confidence in the composition extraction, transcription and normalization | It is not a score modifier or safety statement |
| Provenance | Source identifiers, source image/document/run references, acquisition context, reviewer or extraction trace | Provenance must survive normalization and derivation |
| Timestamp and cutoff | Observation time, source version/date where present and declared source cutoff | Time does not repair absent or conflicting evidence |

Every snapshot must retain the raw declared entry alongside any normalized
identity or relationship record so that historical replay can distinguish
source text from later interpretation.

## 4. Ingredient identity and relationship vocabulary

The following candidate relationships must be represented as typed,
provenance-bearing statements. They do not define runtime behavior or numeric
contribution.

| Relation or entity | Descriptive meaning | Required preservation |
|---|---|---|
| Direct ingredient | Ingredient explicitly declared for the product | Original label expression and source scope |
| Sub-ingredient | Ingredient declared within another ingredient expression | Parent relationship and nesting context |
| Compound ingredient | Declared ingredient whose composition contains named components | Parent record and component-source boundary |
| Mixture component | Component of a declared mixture | Whether the component is directly declared or derived |
| `represents` | Declared entry maps to a governed normalized identity | Mapping evidence, alternatives and resolution state |
| `contains` | One governed entity contains another under a stated scope | Direction, scope and source support |
| `derived_from` | Identity or relation is established through a documented derivation chain | Every transformation and source dependency |
| Ambiguous relation | More than one plausible relation remains | Alternatives, uncertainty and unresolved reason |
| Unresolved relation | No governed relationship can yet be established | Missing evidence and affected downstream scope |

`contains`, `represents`, `derived_from`, parent/sub-ingredient and mixture
relations are non-interchangeable. A relationship record is not permission to
duplicate an ingredient, duplicate evidence, or infer an amount.

## 5. Quantity and denominator readiness

Before any future aggregation denominator can be selected, a decision package
must know the source state and comparability limits of each quantity. This RFC
does not select a denominator rule.

| Quantity state | Required record | What must remain undecided |
|---|---|---|
| Explicit percentage | Exact declared expression, source and basis | Whether and how it is used by aggregation |
| Explicit mass or volume | Unit, reference basis, source scope and comparability | Any conversion or contribution treatment |
| Order-only evidence | Original ordinal position and source | Any inferred amount, share or equal treatment |
| Partial QUID evidence | Declared scope, covered entity and uncovered elements | Extension beyond the declared scope |
| Missing quantity | Explicit absence and reason where known | Any default, substitute or inferred quantity |
| Unreliable quantity | Conflict, stale source, extraction concern or unsupported basis | Any silent acceptance or correction |
| Incomparable basis | Why the basis cannot be aligned to another record | Any normalization or comparability conclusion |
| Estimated quantity | Estimation provenance, method reference and uncertainty | Use as if declared evidence |
| Derived quantity | Full derivation chain, input sources and assumptions | Equivalence to an explicit declaration |

Missing, estimated, unreliable or incomparable quantities must remain typed
states. They cannot be converted automatically into a zero quantity, equal
quantity, absence of an ingredient, or a product-level result.

## 6. State propagation requirements

The following situations require explicit future policy treatment. This RFC
records the questions and guardrails without assigning a numeric effect.

| Ingredient or input state | Future question | Guardrail |
|---|---|---|
| Computable ingredient result | Is the result applicable to the exact product snapshot and relationship? | Do not assume cross-product comparability |
| `not_computable` ingredient | Is it indispensable for the requested product component? | No substitute numeric result, midpoint, average or imputation |
| `non_applicable` ingredient | Is it outside the declared product perimeter? | It is not favourable, adverse or a numeric zero |
| Partial mapping | Is identity and conclusion scope sufficient for the product question? | Preserve partial resolution and alternatives |
| `history_unavailable` | Is the source chain sufficient for reproducible replay? | Do not silently reconstruct missing history |
| Ambiguous identity | Can a governed identity be established for the entry? | Do not select an identity by convenience |
| Ambiguous relationship | Is the parent/component or represented entity relationship established? | Do not treat alternatives as simultaneous contributions |
| Missing quantity | Is the information indispensable to product evaluability? | Do not infer quantity from order or presence |
| Low confidence | What exact conclusion does confidence qualify? | Confidence is separate from goodness and evaluability |
| High uncertainty | What source of uncertainty remains unresolved? | Uncertainty is not an adverse numeric effect |
| Criticality flag | Does a separate future policy classify a product consequence? | No automatic cap, floor, veto or override |
| Regulatory flag | What scoped authority statement is present? | No automatic goodness, safety or compliance inference |
| Nutrition overlap | Is a property reserved to the nutrition component? | Do not reuse it in ingredient aggregation |

The product-level propagation policy remains a future responsibility of
`PSC-OD-006`, `PSC-OD-015`, `PSC-OD-016`, `PSC-OD-017` and the applicable
criticality and validation decisions.

## 7. Separation rules

Future product records must keep the following concepts structurally and
semantically separate:

| Concept | Must not be treated as |
|---|---|
| `ingredient_score` | A product aggregate, nutrition result, safety conclusion or personal advice |
| Future `ingredient_goodness_percent` | An ingredient-level mapping, nutrition result or overall result |
| `nutrition_goodness_percent` | Ingredient favourability reused through nutrition properties |
| Overall product score | An automatic consequence of one component |
| Coverage | Goodness, confidence or a hidden score adjustment |
| Confidence | Safety, goodness or an evaluability proxy |
| Uncertainty | An adverse result or a numeric penalty |
| Missingness | Negative evidence or numeric zero |
| Evaluability | Confidence, coverage or technical execution alone |
| Criticality | An automatic ingredient or product score effect |
| Hazard, exposure and risk | Interchangeable concepts or automatic goodness directions |
| Regulatory status | Goodness, universal safety or product compliance |
| Ontology labels and informational flags | Score-bearing dimensions by label alone |

## 8. Anti-double-counting constraints

Any future aggregation proposal must demonstrate that it does not duplicate a
contribution through:

- repeated ingredient aliases for the same declared entry;
- the same substance appearing through several ingredient records;
- compound or sub-ingredient expansion together with the parent ingredient;
- a mixture component and its source mixture without an explicit relationship
  policy;
- nutrition-property overlap between ingredient and nutrition components;
- regulatory flags being reused as ingredient goodness;
- criticality flags being reused as a direct score effect;
- repeated source evidence being treated as independent support.

Typed identities, relationship provenance, source scope and a future
adversarial corpus are required controls. This RFC defines no deduplication
algorithm or aggregation behavior.

## 9. Readiness checklist for a future PSC-OD-006 RFC

Before a future decision RFC may select an aggregation alternative, the
following non-numeric readiness conditions should be evidenced:

1. a governed product composition snapshot and source/version contract;
2. typed declared, normalized, parent/component, derived and unresolved
   relationship records;
3. explicit quantity, QUID, order and comparability states with provenance;
4. accountable policy scope for coverage, missingness, evaluability and
   indispensability;
5. separate confidence, uncertainty, criticality, hazard, exposure, risk and
   regulatory fields;
6. a documented nutrition and overall boundary preventing double counting;
7. replay identity across product snapshot, candidate, policy and sources;
8. a product-level validation plan covering ambiguity, missingness, mixtures,
   duplicate evidence and non-computability; and
9. reviewed disclosure language preserving the informational, non-personal MVP
   boundary while runtime and release remain unauthorized.

These are readiness conditions only. They are neither a decision nor approval
criteria for a runtime or release.

## 10. Open questions and decision dependencies

| Open area | Related decision context | What remains to be decided |
|---|---|---|
| Exact ingredient mapping | `PSC-OD-005` | Governed upstream mapping disposition and its product applicability |
| Product ingredient aggregation | `PSC-OD-006` | Aggregation alternative, state propagation and relationship treatment |
| Nutrition and overall boundaries | `PSC-OD-007`–`PSC-OD-012` | Nutrition construct, nutrition mapping and overall combination |
| Criticality effects | `PSC-OD-013` and `PSC-OD-014` | Flag classification and any future exceptional behavior |
| Coverage and evaluability | `PSC-OD-015` and `PSC-OD-016` | Required-input sets, indispensability and non-computability policy |
| Confidence and technical profile | `PSC-OD-017` and `PSC-OD-018` | Confidence derivation and deterministic execution requirements |
| Validation and communication | `PSC-OD-019` and `PSC-OD-020` | Product corpus, robustness, comprehension and user-facing limitations |
| Personalization boundary | `PSC-OD-022` | Separation from future personal recommendations |

All listed decisions remain `OPEN`. This RFC neither closes nor changes their
status.

## 11. Non-goals

This RFC explicitly excludes:

- an aggregation formula or product-level score;
- weights, denominators, thresholds, caps, floors, vetoes or overrides;
- runtime, API, UI, database schema, migration or implementation behavior;
- nutrition score and overall score design;
- personalization, dose, frequency or portion recommendations;
- release authorization, external certification or scientific approval.

## 12. Traceability

This RFC is conceptually dependent on and must remain consistent with:

- `WYE_PRODUCT_AGGREGATION_READINESS_DEPENDENCY_BUNDLE.md`;
- `WYE_INGREDIENT_SCORE_MAPPING_RFC.md`;
- `WYE_INGREDIENT_SCORE_CANDIDATE_V1.json`;
- `WYE_PRODUCT_SCORING_CONTRACT.md`.

It preserves their current distinction between ingredient-level candidate
mapping, future product aggregation, nutrition, overall scoring and
non-numeric support dimensions.

## 13. Proposed next step

The next step is a read-only review of this RFC for terminology, dependency
coverage, anti-double-counting guardrails and disclosure coherence. That review
must not start `PSC-OD-006`, and no commit should be recommended until the
review passes.

```text
PSC-OD-005: OPEN
PSC-OD-006: OPEN
PSC-OD-007 through PSC-OD-020: OPEN
PSC-OD-022: OPEN
runtime: NOT AUTHORIZED
release: NOT AUTHORIZED
```
