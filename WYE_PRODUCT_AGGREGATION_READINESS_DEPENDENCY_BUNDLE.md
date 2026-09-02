DRAFT — PRODUCT/SCORING DECISION PREPARATION REQUIRED

# WYE — Product Aggregation Readiness and Dependency Bundle

## Document status and authority

```text
artifact_id: WYE-PRODUCT-AGGREGATION-READINESS-DEPENDENCY-BUNDLE
artifact_status: DRAFT — PRODUCT/SCORING DECISION PREPARATION REQUIRED
decision_scope: PSC-OD-006
decision_status: OPEN
document_authority: preparatory dependency register; not a decision record
governance: INTERNAL INFORMATIONAL ASSURANCE
runtime_authority: NONE
release_authority: NONE
external_validation: FUTURE / OPTIONAL / NOT PRESENT
candidate_dependency: WYE-INGREDIENT-SCORE-CANDIDATE-V1 / 1.0.1-internal
mapping_direction: Option A — ordinal lookup based on internal profiles and traceable reference judgments
policy_architecture: Option C — Layered state model
future_option: Option B — possible multi-attribute development only
```

This bundle inventories the information and governance work needed before a
future product-aggregation decision. It does not start `PSC-OD-006`, select an
aggregation family, or confer authority on the ingredient candidate.

## 1. Scope and non-scope

### 1.1 Future decision perimeter

`PSC-OD-006` is the future decision to select and validate product-level
aggregation of the ingredient component across multiple product ingredients,
their declared or derived relationships, available quantities and the complete
provenance of the product composition snapshot.

The future work must distinguish an ingredient-level result from the product
level `ingredient_goodness_percent` described by the Product Scoring Contract.
The aggregation decision must also expose the product-level state and
disclosures that qualify the result, without turning those disclosures into
score inputs by implication.

### 1.2 Explicit non-scope

This bundle does not:

- close or approve `PSC-OD-005`;
- define a product aggregation formula or any numeric transformation;
- define weights, thresholds, caps, floors, vetoes, overrides or a numeric
  fallback;
- define the nutrition score or the overall score;
- decide how critical flags change a score;
- authorize runtime, API, UI, database, release, publication or
  personalization;
- establish medical, clinical, therapeutic, dietary, safety or individual-
  suitability claims.

Nutrition remains a separate future component. Overall scoring remains a
separate future decision and cannot be inferred from this dependency bundle.

## 2. Inputs already available

The following inputs exist as preparatory material only:

| Input | Current state | Permitted use in readiness work | Limitation |
|---|---|---|---|
| Ingredient candidate | `1.0.1-internal`; internal heuristic; not independently validated | Describe the upstream record shape, provenance and state vocabulary | Not an approved product aggregation authority |
| Mapping direction | Option A, reviewed ordinal lookup direction | Preserve the intended MVP upstream dependency | `PSC-OD-005` remains `OPEN`; profiles and reference judgments are not scientifically approved |
| Policy architecture | Option C layered state model | Keep data, evidence, scientific state, support dimensions, flags and output separate | Does not decide product-level propagation |
| Ingredient states | `computable`, `not_computable`, `non_applicable` and related support states | Enumerate product-level questions and validation cases | No product-level rule is selected here |
| Ingredient score semantics | Numeric result is distinct from support and informational dimensions | Prevent conflation and double counting | Ingredient mapping cannot be averaged or otherwise combined by assumption |
| Canonicalization and replay | Candidate and corpus define version, digest, provenance and replay identity | Specify future traceability requirements | No product snapshot or aggregation digest exists |
| Golden corpus | 30 ingredient-level synthetic cases | Reuse state and replay concepts as a pattern | It is not a product-level corpus and does not validate aggregation |
| Product contract | Tri-score vocabulary, coverage, confidence and evaluability concepts | Bound future output and state requirements | Product aggregation and all downstream gates remain `OPEN` |
| Intended use | General, informational, non-personal packaged-food context | Bound disclosures and prohibited interpretation | Does not authorize runtime or user release |

These inputs are useful for preparing a decision package but are insufficient
to choose or validate a product-level aggregation method.

## 3. Dependency register

The register is deliberately descriptive. A dependency marked `OPEN` is not a
choice and is not silently resolved by this bundle.

| Dependency | State | Why it is needed | Related decisions | Risk if absent | What this bundle does not authorize |
|---|---|---|---|---|---|
| Canonical product composition snapshot | MISSING | Establish the exact product, ingredient entries, source version and acquisition context being assessed | `PSC-OD-006`, `PSC-OD-019`, `PSC-OD-021` | Irreproducible or non-auditable product result | No database schema, ingestion or runtime contract |
| Ingredient identity resolution | PARTIAL / UPSTREAM OPEN | Link each declared entry to a governed ingredient or substance identity | `PSC-OD-005`, `PSC-OD-006`, `PSC-OD-016` | Ambiguous entries can be counted, omitted or conflated incorrectly | No identity resolver or fallback mapping |
| Declared, normalized and derived relationships | MISSING POLICY | Distinguish direct ingredients, represented substances, mixture components and derived entities | `PSC-OD-006`, `PSC-OD-013`, `PSC-OD-016` | Duplicate or non-equivalent contributions and false provenance | No relationship precedence or numerical treatment |
| Quantity and quantitative basis | MISSING POLICY | Record declared amount, unit, basis and applicability where available | `PSC-OD-006`, `PSC-OD-008`, `PSC-OD-015` | Concentration or contribution may be invented or compared on incompatible bases | No weight, share or quantity transformation |
| QUID and ingredient-list order semantics | OPEN | Preserve the distinction between quantitative declaration and ordinal label order | `PSC-OD-006`, `PSC-OD-008` | Order may be mistaken for a percentage or an implicit weighting | No inference from order and no QUID imputation |
| Missing, estimated or unreliable quantities | OPEN | Define how unusable quantitative evidence affects product evaluability | `PSC-OD-006`, `PSC-OD-016`, `PSC-OD-017` | Hidden defaults can create false precision and bias | No default quantity, equal contribution or numeric substitute |
| Product coverage requirements | OPEN | Define required-input sets and how coverage is reported for the product perimeter | `PSC-OD-015` | A result may appear complete while material inputs are absent | No coverage threshold or score modifier |
| Product evaluability and indispensability | OPEN | Decide when an ingredient or component is indispensable and how `not_computable` propagates | `PSC-OD-006`, `PSC-OD-016` | Missing information could be silently ignored or converted to zero | No fallback or propagation rule is selected |
| Confidence and uncertainty | OPEN | Report reliability of the exact product conclusion separately from computability | `PSC-OD-017` | Confidence could be misused as a score multiplier or gate | No confidence adjustment to a score |
| Missingness and partial resolution | OPEN | Preserve the reason and scope of incomplete product evidence | `PSC-OD-015`, `PSC-OD-016`, `PSC-OD-017` | Different missing states may be collapsed into one misleading result | No imputation or midpoint behavior |
| Criticality and flag effects | OPEN | Determine whether any qualified critical condition affects product output | `PSC-OD-013`, `PSC-OD-014` | Hazard or a flag could be treated as an automatic product penalty | No cap, floor, veto or override |
| Nutrition component boundary | OPEN downstream | Keep ingredient favourability separate from nutrition properties | `PSC-OD-007`–`PSC-OD-011` | Nutrition facts could be counted once through ingredients and again through nutrition | No nutrition score or cross-component aggregation |
| Overall aggregation boundary | OPEN downstream | Define any future overall product output only after component policies exist | `PSC-OD-012` | An ingredient component could be presented as an overall judgment | No overall score or aggregation family |
| Product validation corpus | MISSING | Test relationships, quantities, states, replay and adversarial cases on representative products | `PSC-OD-006`, `PSC-OD-019` | The method may pass abstract cases but fail real composition patterns | No fixture or corpus is created here |
| Disclosure and communication | OPEN | Explain product state, limitations and non-claims without misleading interpretation | `PSC-OD-020` | A product percentage could be read as safety, health or suitability | No user-facing language approval |
| Source and artifact governance | GOVERNANCE AVAILABLE; OPERATIONAL INPUT MISSING | Bind every product result to immutable source and candidate versions | `PSC-OD-018`, `PSC-OD-019`, `PSC-OD-021` | Replay and change impact cannot be established | No source acquisition or release process |

## 4. Minimum product-level vocabulary and relations

The terms below require governance before an aggregation decision. Their
presence does not imply a numeric meaning.

| Term | Descriptive meaning | Required distinction |
|---|---|---|
| Product | A versioned packaged-food composition snapshot under a declared label state | Product identity is not a person or consumption scenario |
| Declared ingredient | An entry as presented in the authoritative product composition source | Label order does not supply a percentage unless a quantity is explicitly declared |
| Normalized ingredient | A governed identity linked to a declared entry | Normalization must preserve the source entry and uncertainty |
| Substance | A chemical or conceptual entity referenced by an ingredient or source | A substance is not automatically a separate declared ingredient |
| Mixture component | A component nested within a declared mixture or compound | Parent and component relationships are not interchangeable |
| Direct relationship | A source-supported relation explicitly attached to a product entry | Must retain source and scope |
| Derived relationship | A relation inferred through a governed transformation or source chain | Must be traceable and cannot be treated as direct evidence by default |
| Uncertain relationship | A relationship whose identity, direction or scope is unresolved | Must remain visible and may affect evaluability |
| Declared quantity | An amount supplied with unit, basis, source and applicability | It is not automatically a score contribution |
| Missing or unreliable quantity | Quantity absent, estimated, conflicting, stale or non-comparable | It is not zero and does not authorize equal treatment |
| Ingredient-list order | Ordinal position in the declared list | It is not concentration, dose or a numeric weight |
| QUID | A governed quantitative ingredient declaration and its applicable basis | Must not be conflated with list order |
| Provenance | Source identifiers, acquisition context, cutoff, reviewer/judgment and transformations | Required for replay and change impact |
| Version | Immutable identity of the product snapshot, candidate and policy dependencies | A product result without dependency versions is not reproducible |

Relationship types such as `contains`, `represents`, `equivalent_to`,
`mixture_component` and `derived_from` must retain their non-interchangeable
semantics. No relationship is treated as a contribution rule by this bundle.

## 5. State and propagation questions

These are questions for a future decision package, not answers.

| Product situation | Question that remains open | Mandatory guardrail |
|---|---|---|
| Ingredient `not_computable` | Is the ingredient indispensable for the requested product component, and what product state follows? | No score member may be fabricated; zero is not a substitute |
| Ingredient non-applicable | Is the entry outside the declared product perimeter, and how is the applicable perimeter disclosed? | Non-applicable is neither favourable nor adverse and is not zero |
| Mapping partially resolved | Is identity or conclusion validity sufficient for the exact product question? | Preserve unresolved portions; do not invent a mapped result |
| Ambiguous identity or relationship | Can the relationship be governed without collapsing alternatives? | Ambiguity remains visible and may block evaluability |
| Quantity absent or unreliable | Is the product component still evaluable without quantitative evidence? | No inferred concentration, dose, equal share or hidden default |
| Duplicate ingredient entries | Are entries aliases, separate declarations or repeated evidence? | Deduplication must be explicit and provenance-preserving |
| Duplicate evidence | Does the same source or judgment support several records? | Shared evidence is not independent evidence by repetition |
| Mixture and sub-components | Which relationship and source scope governs the parent and nested component? | Parent/component records remain distinct until governed |
| Conflicting evidence | Can conflict be resolved for the exact question? | Preserve conflict; do not average or conceal it |
| History unavailable | Is the product snapshot or source chain incomplete? | Replay identity is incomplete; no silent reconstruction |
| Coverage insufficient | Which required input is missing and is it material? | Coverage remains separate from score and confidence |

None of these states may be converted automatically into a numeric zero,
average, midpoint, imputation, or equal quantity.

## 6. Separation and anti-double-counting

The future product package must maintain separate fields and explanations for:

- ingredient favourability;
- nutrition score;
- overall score;
- coverage;
- confidence;
- uncertainty;
- missingness;
- evaluability;
- criticality;
- hazard, exposure and risk;
- regulatory status;
- ontology labels and informational flags.

The ingredient candidate's score-bearing construct cannot silently consume
nutrition properties, hazard assertions, exposure assumptions, risk estimates,
criticality labels, regulatory status or ontology labels. Those dimensions may
qualify a result or a future gate only under their own open decisions.

The future validation package must test at least these double-counting risks:

1. a nutrition property appearing both in an ingredient record and in the
   separate nutrition component;
2. the same hazard or evidence source repeated through a parent ingredient and
   a mixture component;
3. duplicate ingredient declarations represented as independent entities;
4. a quantity and a derived relationship describing the same information;
5. confidence or coverage being used again as a hidden score adjustment;
6. a regulatory or informational flag being interpreted as goodness or safety.

No anti-double-counting algorithm is selected here. The required control is
explicit provenance, typed fields, dependency versioning and adversarial
validation.

## 7. Validation readiness requirements

A future product-level corpus must contain representative, synthetic and
adversarial cases covering:

- complete product composition and provenance;
- missing, estimated, conflicting and non-comparable quantities;
- QUID present, absent and inconsistent with order semantics;
- several declared ingredients with distinct identities;
- mixtures and nested sub-components;
- duplicated declarations and duplicated evidence;
- direct, derived and uncertain relationships;
- partially resolved identity or mapping;
- `not_computable` ingredient states;
- non-applicable entries;
- insufficient product coverage;
- conflicting evidence and unavailable history;
- nutrition-overlap and overall-separation controls;
- criticality, hazard, exposure, risk and regulatory non-influence controls;
- canonical replay, provenance changes and candidate-version changes;
- communication comprehension and non-claim interpretation.

The corpus must bind each case to an immutable product snapshot, candidate and
policy dependency versions, source cutoff, provenance chain and replay identity.
No product fixture or corpus is created by this bundle.

## 8. Decisions and gates

The decision states remain unchanged.

| Decision | State | Relevance to this bundle |
|---|---|---|
| `PSC-OD-005` | `OPEN` | Upstream ingredient mapping remains a candidate dependency |
| `PSC-OD-006` | `OPEN` | Future product-level ingredient aggregation decision; not started here |
| `PSC-OD-013`–`PSC-OD-019` | `OPEN` | Criticality, zero behavior, coverage, evaluability, confidence, precision and validation dependencies |
| `PSC-OD-007`–`PSC-OD-012` | `OPEN` | Nutrition and overall dependencies; relevant for a complete product output but outside ingredient aggregation selection |
| `PSC-OD-020` | `OPEN` | Communication and claim boundary for any future user-facing output |
| `PSC-OD-021` | `DECIDED` | Source-governance model available as a constraint, not as a scoring approval |

No decision is closed, selected or renumbered by this bundle.

### Entry criteria for a future PSC-OD-006 RFC

Before drafting a decision RFC that selects an aggregation alternative, the
following non-numeric conditions should be satisfied:

1. the current Option A and Policy Option C direction is unambiguous and
   `PSC-OD-005` has a governed upstream candidate disposition;
2. product composition, identity, relationship, quantity, QUID and order
   semantics have an explicit source and version contract;
3. product-level coverage, evaluability, missingness and indispensability
   questions have an accountable owner and testable policy scope;
4. confidence, uncertainty and criticality remain typed and separate from any
   future score-bearing construct;
5. the nutrition and overall boundaries are documented sufficiently to prevent
   double counting, without being imported into the ingredient component;
6. a representative product-level validation plan and provenance/replay design
   exist; and
7. communication, non-claim and release gates are identified while runtime and
   release remain unauthorized.

These are readiness conditions, not approval criteria and not a selection of
any aggregation method.

## 9. Governance and disclosure

This bundle is governed under `INTERNAL INFORMATIONAL ASSURANCE`. The
ingredient candidate remains an internal heuristic baseline and is not
independently validated, scientifically approved, certified or authorized for
runtime or release. External validation is future, optional and not present.

The permitted product context remains general and informational for packaged
foods. Any future output must not be presented as a medical, clinical,
therapeutic, dietary, safety, regulatory-compliance or individual-suitability
determination. A disclaimer communicates these limits; it does not authorize
unsupported claims.

This document creates no API, UI, database, migration, runtime, publication,
release or personalized recommendation authority.

## 10. Traceability and review boundary

Preparatory sources consulted for this bundle are:

- `WYE_PRODUCT_SCORING_CONTRACT.md`;
- `WYE_INGREDIENT_SCORE_MAPPING_RFC.md`;
- `WYE_INGREDIENT_STATE_DIMENSION_POLICY_RFC.md`;
- `WYE_INGREDIENT_SCORING_POLICY_BUNDLE_RFC.md`;
- `WYE_INGREDIENT_SCORE_CANDIDATE_V1.json`;
- `WYE_INGREDIENT_SCORE_CANDIDATE_V1_GOLDEN.json`;
- `WYE_INGREDIENT_SCORE_CANDIDATE_V1_INTERNAL_ASSURANCE_REPORT.md`;
- `Checkpoints/WYE_PHASE_7.md`.

This bundle is ready only for a subsequent read-only review of its scope,
dependencies and disclosures. That review must not be treated as a decision
on `PSC-OD-006`.

```text
PSC-OD-005: OPEN
PSC-OD-006: OPEN
PSC-OD-013 through PSC-OD-019: OPEN
mapping_mvp: Option A
policy_architecture: Option C
option_b: future multi-attribute development only
runtime: NOT AUTHORIZED
release: NOT AUTHORIZED
```
