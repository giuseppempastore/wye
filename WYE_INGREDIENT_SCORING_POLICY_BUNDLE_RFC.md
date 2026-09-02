# WYE Consolidated Ingredient Scoring Policy Bundle RFC

## Document status and authority

```text
phase: 7.15.2
document_status: PRODUCT-OWNER DIRECTION RECORDED — EXACT INTERNAL CANDIDATE AUTHORIZED
governance: INTERNAL INFORMATIONAL ASSURANCE
scientific_approval: NOT CLAIMED
independent_validation: NOT PRESENT
certification: NOT PRESENT
runtime_authority: NONE
release_authority: NONE
cutoff: 2026-09-02
PSC-OD-005: OPEN
PSC-OD-013: OPEN
PSC-OD-014: OPEN
PSC-OD-015: OPEN
PSC-OD-016: OPEN
PSC-OD-017: OPEN
PSC-OD-018: OPEN
PSC-OD-019: OPEN
PSC-OD-006: NOT STARTED
product_owner_direction_date: 2026-09-02
mvp_mapping_candidate_direction: Mapping Option A — Reviewed ordinal lookup with bounded anchors
future_mapping_research_option: Mapping Option B — Transparent monotone multi-attribute model
exact_numerical_candidate: PRESENT — UNREVIEWED INTERNAL HEURISTIC CANDIDATE
```

This RFC consolidates the candidate product-policy choices that precede an exact
ingredient numerical-scoring candidate. The product owner selected the bundle
as candidate direction on `2026-09-02` and authorized preparation of the exact
internal package. That direction closes no decision and approves no
score-bearing dimension, formula, weight, threshold, parameter, curve, scale
value, cap value, floor value or override value. The exact unreviewed candidate
is defined in its separate versioned artifacts. This RFC authorizes neither
implementation nor release.

## 1. Canonical perimeter

The bundle consumes, without reopening:

- the `PSC-OD-002` goodness construct: a transparent, versioned assessment of
  compositional and nutritional favourability under declared WYE criteria, not
  personal health, safety or clinical risk;
- the `PSC-OD-003` domain-scoped, layered and source-backed ontology;
- the `PSC-OD-004` multi-label model with contextual precedence and no universal
  primary category;
- Mapping Option A as the MVP candidate direction for a transparent, ordered
  lookup over internally governed profiles and traced reference judgments;
- Mapping Option B as a future possible multi-attribute development, not as the
  current MVP candidate direction;
- Policy Option C as the candidate layered state model; and
- Internal Informational Assurance as the mandatory MVP assurance tier.

External independent validation remains future, optional and not present. Its
absence does not block internal policy work, but every internal methodology,
technical, test, provenance, disclosure and product-acceptance gate remains
mandatory.

The intended output is an informative and indicative WYE indicator. It is not a
clinical measure, safety guarantee, regulatory conclusion, personal dietary
recommendation or statement of individual suitability.

## 2. Canonical decision questions

The quoted questions below reproduce the decision descriptions in the Product
Scoring Contract. The surrounding fields explain the candidate bundle without
changing those questions.

### 2.1 `PSC-OD-005` — ingredient numerical mapping

**Canonical question:** “Map approved ingredient states and dimensions to a
0..100 ingredient scale without conflating missingness or uncertainty with
risk.”

- **Inputs:** an approved state/dimension policy, governed reference judgments,
  calibration corpus, exact applicability and direction cards, and the
  dependent policy decisions in this bundle.
- **Output:** one exact ingredient numerical-mapping candidate in a later phase.
- **Dependencies:** `PSC-OD-002`–`004`, `PSC-OD-013`–`019`; `PSC-OD-006` remains
  downstream and is not started.
- **MVP decision owner:** protocol proposer prepares; internal validation
  function and data/model steward verify; product owner accepts bounded MVP use.
- **Internally decidable:** construct-preserving dimension set, ordinal intent,
  applicability, direction, dependency controls and exact-candidate readiness.
- **Future/optional:** independent external validation and any stronger claim.
- **Not decided here:** formula, transformation, weight, threshold, parameter,
  endpoint value, numerical comparability or runtime behavior.

### 2.2 `PSC-OD-013` — flag effects and criticality

**Canonical question:** “Define flag-effect classification, applicable critical
caps, severity classes and no-double-counting behavior without treating hazard
alone as a score effect.”

- **Inputs:** criticality ontology, validation corpus and false-positive
  analysis.
- **Output:** critical cap and flag-effect policy candidate.
- **Dependencies:** hazard/risk separation, `PSC-OD-005`, `PSC-OD-014`,
  `PSC-OD-019` and the later communication decision.
- **MVP decision owner:** internal methodology and validation functions plus
  regulatory-scope review; product owner accepts bounded MVP use.
- **Internally decidable:** flag classes, default non-numeric behavior,
  eligibility conditions and no-double-counting rules.
- **Future/optional:** external specialist review for stronger or regulated
  claims.
- **Not decided here:** cap, floor, veto, penalty or override values; automatic
  conversion of hazard or regulatory status into a score effect.

### 2.3 `PSC-OD-014` — zero override

**Canonical question:** “Define the closed set of zero-override rules and prove
reproducibility and user-safe interpretation.”

- **Inputs:** disqualifier contract, legal/scientific cases and communication
  testing.
- **Output:** zero-override RFC and golden cases.
- **Dependencies:** `PSC-OD-013`, `PSC-OD-016`, `PSC-OD-019` and the later claim
  and release gates.
- **MVP decision owner:** the Contract roles are interpreted as accountable
  internal methodology, claim/legal-scope and release functions; product-owner
  acceptance remains required before MVP use.
- **Internally decidable:** whether the initial MVP should have no numerical
  zero override and what evidence would be needed to reconsider it.
- **Future/optional:** specialist review for stronger claims or regulated scope.
- **Not decided here:** any zero-triggering condition or numerical override.

### 2.4 `PSC-OD-015` — coverage

**Canonical question:** “Define required-input sets and aggregation of coverage,
including critical-gate coverage.”

- **Inputs:** input inventory, domain policies and missingness simulations.
- **Output:** coverage policy candidate.
- **Dependencies:** applicability, `PSC-OD-016`, `PSC-OD-017` and
  `PSC-OD-019`.
- **MVP decision owner:** internal methodology and validation functions plus
  data/model steward; product owner accepts bounded MVP use.
- **Internally decidable:** required-input identities, coverage disclosure and
  indispensable-input eligibility behavior.
- **Future/optional:** external validation of coverage bias or stronger claims.
- **Not decided here:** numerical coverage multiplier, score penalty or hidden
  imputation.

### 2.5 `PSC-OD-016` — evaluability and missing data

**Canonical question:** “Define the evaluability and missing-data policy,
including component indispensability, `not_computable` conditions and
interaction with overall aggregation, without a numeric fallback.”

- **Inputs:** coverage policy, user testing, sensitivity and bias analysis.
- **Output:** evaluability and missing-data RFC.
- **Dependencies:** `PSC-OD-015`, `PSC-OD-017`, `PSC-OD-019`; interaction with
  product aggregation remains downstream of `PSC-OD-006`.
- **MVP decision owner:** internal methodology and validation functions plus
  product communication review; product owner accepts bounded MVP use.
- **Internally decidable:** `computable`, `not_computable`, non-applicability,
  indispensable-input and trace semantics.
- **Future/optional:** external comprehension validation for stronger claims.
- **Not decided here:** numeric fallback, implicit zero, midpoint, imputation or
  penalty for missing data.

### 2.6 `PSC-OD-017` — confidence

**Canonical question:** “Freeze confidence dimensions, state derivation and
interaction with evaluability without using confidence as an evaluability
proxy.”

- **Inputs:** evidence-quality framework, data-quality audit and use cases.
- **Output:** confidence policy candidate.
- **Dependencies:** evidence synthesis, `PSC-OD-015`, `PSC-OD-016` and
  `PSC-OD-019`.
- **MVP decision owner:** internal methodology function and data/model steward;
  product owner accepts bounded MVP use.
- **Internally decidable:** separate confidence disclosure, derivation trace and
  a narrowly typed invalid-evidence gate independent of goodness.
- **Future/optional:** external evaluation of interpretation or calibration.
- **Not decided here:** score modifier, multiplier or inverse-goodness proxy.

### 2.7 `PSC-OD-018` — deterministic numerical profile

**Canonical question:** “Freeze integer precision, intermediate arithmetic,
rounding, boundary and canonical serialization rules.”

- **Inputs:** the future approved formula and canonicalization compatibility
  analysis.
- **Output:** numeric execution profile.
- **Dependencies:** exact `PSC-OD-005` candidate, `PSC-OD-019`, provenance and
  replay contracts.
- **MVP decision owner:** data/model steward plus internal validation function;
  product owner accepts bounded MVP use.
- **Internally decidable:** deterministic arithmetic family, one declared
  rounding locus, boundary-error semantics, canonical serialization, digest and
  replay requirements.
- **Future/optional:** independent reproducibility review.
- **Not decided here:** precision count, scale factor, rounding rule, clipping
  value, formula or score value.

### 2.8 `PSC-OD-019` — validation package

**Canonical question:** “Define golden corpus, external benchmarks, sensitivity,
monotonicity, robustness and comprehension validation.”

- **Inputs:** all frozen policy candidates and a representative product corpus.
- **Output:** product-scoring validation plan and corpus.
- **Dependencies:** every other decision in this bundle, exact candidate
  identity, source provenance and disclosure contract.
- **MVP decision owner:** internal validation function plus data/model steward;
  product owner accepts residual MVP product risk. External validation remains
  future and optional.
- **Internally decidable:** reference judgments, calibration/hold-out split,
  golden and adversarial cases, sensitivity, monotonicity, regression,
  comprehension, impact and limitations artifacts.
- **Future/optional:** independent external validation and benchmarks requiring
  an external authority.
- **Not decided here:** claim of independence, certification or acceptance of an
  exact numerical candidate that does not yet exist.

## 3. Candidate score-bearing model

### 3.1 Layered consumer model

The MVP candidate combines Policy Option C with Mapping Option A:

1. upstream mapping and provenance establish identity and reconstruction state;
2. evidence selection and synthesis produce scoped, non-scalar conclusions;
3. ingredient projection preserves context and relationship semantics;
4. support layers expose applicability, evidence state, confidence,
   uncertainty, coverage, missingness and mapping resolution;
5. informational layers expose regulatory and ontology facts;
6. a separate criticality layer exposes candidate warnings or gates; and
7. only an eligible score-bearing proposition may reach a future numerical
   mapping.

No support, informational or criticality output becomes score-bearing merely by
being available.

### 3.2 Candidate inventory disposition

| Candidate dimension | Bundle disposition | Reason / required internal assumption |
|---|---|---|
| `DIM-CAND-INGREDIENT-FAVOURABILITY` | `UNRESOLVED` candidate score-bearing construct | Only possible score-bearing construct currently identified. Requires an internal construct definition, reference judgments, bounded direction and falsification evidence. |
| `DIM-CAND-HAZARD` | `UNRESOLVED — NOT SCORE-BEARING` | Hazard may inform a conclusion but has no automatic goodness direction and is not risk. |
| `DIM-INFO-REGULATORY-STATUS` | `INFORMATIONAL ONLY` | Regulatory status is not goodness, hazard, risk or penalty. |
| `DIM-SUPPORT-EVIDENCE-STATE` | `SUPPORT ONLY` | Evidence support is not favourability. |
| `DIM-SUPPORT-EXPOSURE` | `SUPPORT ONLY` | Exposure is contextual and is not intrinsic ingredient goodness. |
| `DIM-SUPPORT-RISK` | `SUPPORT ONLY` | Risk requires compatible hazard and exposure and remains context-bound. |
| `DIM-SUPPORT-APPLICABILITY` | `SUPPORT ONLY` | Determines whether a proposition applies, not its direction. |
| `DIM-SUPPORT-CONFIDENCE` | `SUPPORT ONLY` | Confidence qualifies a conclusion and is not goodness. |
| `DIM-SUPPORT-UNCERTAINTY` | `SUPPORT ONLY` | Uncertainty is not adverse evidence or a penalty. |
| `DIM-SUPPORT-MAPPING-RESOLUTION` | `SUPPORT ONLY` | Technical reconstruction cannot create scientific direction. |
| `DIM-SUPPORT-COVERAGE` | `SUPPORT ONLY` | Support extent is separate from outcome and confidence. |
| `DIM-SUPPORT-MISSINGNESS` | `SUPPORT ONLY` | Missing required data is not zero, neutral or adverse. |
| `DIM-CAND-CRITICALITY` | `CRITICALITY CANDIDATE — SEPARATE LAYER` | Any warning, gate or future effect requires `PSC-OD-013` and `014`; no automatic penalty. |
| `DIM-EXCL-NUTRITION-PROPERTY` | `EXCLUDED` | Reuse would duplicate the future nutrition score. |
| `DIM-INFO-ONTOLOGY-LABEL` | `INFORMATIONAL ONLY` | Multi-label category assertion has no automatic direction. |

No concrete dimension is numerically approved. The future exact candidate must
either substantiate the favourability construct or stop; it must not populate
the gap with hazard, regulatory status, evidence quantity or another proxy.

### 3.3 Forbidden proxies and overlaps

- regulatory authorization or prohibition is not ingredient goodness;
- hazard is not risk, direction or automatic criticality;
- exposure and risk are not context-free ingredient properties;
- evidence count, source prestige and confidence are not score weights;
- uncertainty, missingness and low coverage are not penalties;
- mapping resolution and ontology labels are not scientific outcomes;
- critical flags are not automatic caps, floors, vetoes or overrides; and
- nutritional properties remain outside the ingredient score unless a future
  construct review proves non-duplication.

Every proposition and source identity must be traceable across layers. Shared
evidence or causal ancestry prevents a declaration of independence until tested.

## 4. Direction and applicability bundle

### 4.1 Candidate direction card — ingredient scientific favourability

- **Definition:** protocol-relative favourability of a canonically identified
  ingredient for the exact reviewed question under declared WYE criteria; not
  safety, clinical benefit, risk probability or regulatory compliance.
- **Candidate direction:** a case internally judged more favourable for the same
  applicable proposition should not receive a less favourable future ordering.
- **Applicability:** resolved ingredient identity, compatible evidence question,
  governed projection, applicable scope and all indispensable inputs present.
- **Non-applicability:** outside the food/intended-use domain, incompatible
  question, genuinely irrelevant dimension or unsupported subject transfer.
- **Exceptions:** conflicting propositions, non-monotonic context, dependence on
  form/use/population, unresolved nutrition overlap or criticality interaction.
- **Non-monotonicity risk:** favourability may reverse across questions or
  contexts; universal ordering is forbidden.
- **Dependencies:** applicability, evidence state, projection, confidence,
  uncertainty, coverage, missingness, criticality and dependency register.
- **Possible interactions:** only explicitly governed interactions may enter the
  later exact candidate; correlated or hierarchical inputs cannot be counted
  independently.
- **Internal rationale:** one transparent construct minimizes proxy leakage while
  preserving an auditable Mapping Option A lookup consumer.
- **Falsification cases:** contextual reversal; identical science with different
  regulatory labels; identical conclusion with different confidence; additional
  missing optional input; shared-evidence duplicate; nutrition-only change;
  hazard without exposure; unresolved indispensable identity.
- **Source/gap:** existing canonical Contract, Mapping RFC and Policy RFC;
  construct definition, reference judgments and validation corpus remain gaps.
- **Status:** `CANDIDATE — NOT NUMERICALLY APPROVED`.

### 4.2 Monotonicity and applicability constraints

Monotonicity is a bounded test hypothesis, not a universal law. It applies only
when subject, question, context, applicability, dependency structure and all
other score-bearing propositions are held compatible. Support-only changes must
not silently change goodness. Non-applicable items are removed from the
applicable perimeter; they are not set to zero or a midpoint.

The future exact candidate must fail validation if a regulatory-label-only,
confidence-only, coverage-only, missingness-only or ontology-only change alters
the ingredient ordering without a separately governed causal proposition.

## 5. Candidate decisions for `PSC-OD-013`–`019`

### 5.1 `PSC-OD-013` — flag and criticality policy

| Alternative | Behavior | Principal risk | Candidate disposition |
|---|---|---|---|
| A — Informational warning only | Flags remain visible with provenance and no numerical consequence. | A material condition may be under-emphasized. | Retain as baseline. |
| B — Separate qualified criticality gate | Default is informational; a future effect is eligible only for a closed, source-backed, applicable critical class with no-double-counting proof. | Governance complexity and false positives. | Recommended candidate architecture. |
| C — Direct penalty from flag/status | A flag immediately changes the score. | Conflates hazard/regulation with goodness and double counts evidence. | Reject for the MVP bundle. |

**Recommendation:** Alternative B as architecture, with Alternative A as the
current behavior until an exact qualified effect is separately accepted. No
flag, hazard or regulatory status has an automatic numerical effect.

### 5.2 `PSC-OD-014` — zero override

| Alternative | Behavior | Principal risk | Candidate disposition |
|---|---|---|---|
| A — No zero override | Critical information is disclosed or may block computability, but cannot manufacture a numerical zero. | Less forceful presentation. | Recommended initial MVP policy. |
| B — Closed qualified override set | Only an exact, finite, reproducible and comprehensible disqualifier set may trigger a future override. | Extreme false-positive impact and confusion with safety/risk. | Future candidate only. |

**Recommendation:** Alternative A. Zero remains a valid computed endpoint only
for a future formula; it is never a representation of missingness,
non-computability, hazard alone or an informational warning.

### 5.3 `PSC-OD-015` — coverage policy

| Alternative | Behavior | Principal risk | Candidate disposition |
|---|---|---|---|
| A — Display only | Coverage is reported but never affects eligibility. | A score may appear despite an indispensable gap. | Transparency baseline, insufficient alone. |
| B — Disclosure plus indispensable-input gate | Coverage remains separate; named indispensable omissions yield `not_computable`. | Over-broad indispensability could suppress useful outputs. | Recommended. |
| C — Numerical multiplier | Coverage scales the score. | Turns missingness into a penalty and entangles coverage with goodness. | Not recommended; not approved. |

**Recommendation:** Alternative B. Coverage is always disclosed and remains
non-score-bearing. Its only candidate operational role is through explicit
required-input eligibility, never as a multiplier.

### 5.4 `PSC-OD-016` — computability and missing data

| Alternative | Behavior | Principal risk | Candidate disposition |
|---|---|---|---|
| A — Permissive partial result | Emits a result for a declared reduced perimeter despite unavailable inputs. | Users may compare results with different semantic scope. | Retain only as a future explicitly scoped comparison. |
| B — Fail-closed indispensable-input gate | Emits `not_computable` when any named indispensable input or gate is unavailable. | Over-broad indispensability may suppress useful results. | Recommended. |
| C — Numerical missing-data fallback | Substitutes a number for unavailable input or result. | Converts absence into an outcome and hides uncertainty. | Forbidden. |

| State | Candidate meaning | Numerical output |
|---|---|---|
| `computable` | Exact candidate, applicable perimeter and every indispensable input satisfy their governed gates. | Future exact result may be emitted only after authorization. |
| `not_computable` | At least one named indispensable input or gate is unresolved, missing, unusable or invalid. | None; no fallback. |
| non-applicable | The dimension or proposition does not apply to the exact question. | Excluded from the applicable perimeter; never zero. |
| missing required input | A named applicable requirement is absent or unusable. | Causes trace and, when indispensable, `not_computable`; never a penalty. |

Distinct alternatives are: permissive partial output with explicit reduced
scope, fail-closed non-computability for indispensable gaps, and numerical
fallback. The bundle recommends fail-closed non-computability for indispensable
gaps while allowing only explicitly defined non-applicability. Numerical
fallback is forbidden. A computed zero is distinct from absent data and from
`not_computable`.

### 5.5 `PSC-OD-017` — confidence policy

| Alternative | Behavior | Principal risk | Candidate disposition |
|---|---|---|---|
| A — Separate disclosure | Confidence qualifies the exact conclusion without changing goodness. | Users may overlook it. | Recommended default. |
| B — Typed validity gate | A specifically invalid or unsupported conclusion blocks its own use; the confidence label itself is not the gate. | Gate may be misdescribed as a confidence threshold. | Recommended only with named validity reasons. |
| C — Score modifier | Confidence changes the numerical output. | Conflates certainty with favourability. | Reject for the MVP bundle. |

**Recommendation:** Alternative A plus the narrow validity behavior in B.
Confidence remains visible, traceable and separate; it is neither goodness nor a
multiplier.

### 5.6 `PSC-OD-018` — deterministic execution profile

| Topic | Alternatives | Recommended candidate constraint |
|---|---|---|
| Arithmetic | exact rational; fixed-point integer; floating point | Exact rational during candidate derivation or fixed-point integer at runtime; floating point requires a separate determinism proof. |
| Precision | declared fixed scale; context-dependent scale | One versioned fixed scale for the exact candidate; scale remains unresolved here. |
| Rounding | intermediate rounding; terminal rounding | One named terminal rounding locus; the rule remains unresolved here. |
| Clipping | silent clipping; explicit bounded transform; error | No silent clipping; boundaries belong to the formula, and unexpected overflow is an error. |
| Serialization | implementation-native; canonical governed JSON | Canonical governed JSON with stable ordering and representations. |
| Digest | partial-object digest; full candidate/input digest | Digest binds exact policy, arithmetic profile, inputs and output trace using the governed digest profile. |
| Replay | best effort; exact historical replay | Exact version-bound replay with immutable inputs and artifacts. |

No precision, rounding mode, bound or digest algorithm is selected in this
bundle. The data/model steward must freeze them together with the exact
candidate and prove cross-run determinism.

### 5.7 `PSC-OD-019` — Internal Assurance validation package

| Alternative | Behavior | Principal risk | Candidate disposition |
|---|---|---|---|
| A — Conformance-only package | Uses deterministic and golden regression checks without a separated hold-out or sensitivity package. | Can prove implementation consistency but not robustness of the policy choice. | Insufficient alone. |
| B — Full Internal Informational Assurance package | Adds internal judgments, calibration, sealed hold-out, adversarial, sensitivity, monotonicity, impact and limitations artifacts. | Higher preparation and governance burden. | Recommended. |
| C — External-validation-only gate | Defers acceptance until a future independent external review exists. | Incorrectly blocks the informational MVP and leaves internal product accountability incomplete. | Future optional tier only; not the MVP gate. |

The required MVP package contains:

- internal reference judgments with disagreement and reviewer trace;
- a representative calibration set;
- a sealed internal hold-out set not used to tune the candidate;
- immutable golden regression cases;
- adversarial proxy, missingness, criticality and boundary cases;
- sensitivity analysis over every plausible methodological choice;
- bounded monotonicity and contextual-reversal tests;
- extreme-case and endpoint-interpretation tests;
- dependency, shared-evidence and double-counting tests;
- deterministic regression and historical replay;
- candidate-versus-baseline impact report;
- known-limitations register;
- disclosure and comprehension mapping; and
- product-owner acceptance of the exact candidate and residual product risk.

This is Internal Informational Assurance. It is not independent validation,
scientific certification, clinical validation or regulatory approval.

## 6. Reference-judgment and corpus plan

### 6.1 Case-card contract

Every internal judgment case records:

```text
judgment_status: INTERNAL AI-ASSISTED JUDGMENT — NOT INDEPENDENTLY VALIDATED
case_key: stable internal identifier
case_version: immutable version
question_and_subject: exact governed scope
frozen_inputs: source, mapping, evidence, projection and context identities
provenance: artifact identities, cutoff and digests
rationale: construct-linked internal reasoning
expected_ordinal_relationship: less / equivalent / more / incomparable / unresolved
expected_evaluability: computable / not_computable / non-applicable
forbidden_inference: explicit non-claim
disagreement_record: reviewer positions and disposition
reviewer_trace: human accountability and AI-assistance disclosure
```

No case in this phase contains an expected numerical score.

### 6.2 Corpus partitions

| Partition | Purpose | Separation rule |
|---|---|---|
| Calibration set | Elicit and test construct, direction and candidate choices. | May inform the exact candidate; all use is logged. |
| Internal hold-out | Evaluate ordering, robustness and comprehension after freeze. | Sealed before exact-candidate tuning and opened only by the internal validation function. |
| Golden regression set | Preserve deterministic expected states, traces and ordinal relations. | Version-bound; changes require explicit supersession and impact analysis. |
| Adversarial set | Challenge proxies, double counting, missingness, context transfer and criticality. | Authored independently from ordinary happy-path cases where practicable. |

Codex/ChatGPT may assist drafting, counterexample generation and consistency
review. A named human internal authority owns each final case and disposition;
AI assistance never becomes independent review.

## 7. Exact-candidate readiness contract

### 7.1 Entry conditions for the next Sol pass

The next exact-candidate pass may begin only when:

- the product owner selects one consolidated bundle as candidate direction;
- all involved decisions remain explicitly `OPEN` pending exact evidence;
- the score-bearing construct and bounded direction card are complete enough to
  falsify;
- applicability, indispensability, criticality and dependency policies are
  internally consistent;
- reference-judgment protocol and corpus partitions are frozen;
- source/gap and known-limitations registers are current;
- no unresolved contradiction would force the numerical method to invent policy;
  and
- the use of Sol for one consolidated generation is explicitly authorized.

### 7.2 Required exact-candidate outputs

The next pass must produce, as one version-bound candidate package:

- exact formula and frozen dimension set;
- transformations and their domains;
- weights or an explicit no-weight rule;
- compensability and interaction rules;
- cap, floor, veto and override dispositions;
- computability and missing-input rules;
- deterministic arithmetic, precision, rounding and boundary profile;
- canonical JSON representation and content digest;
- calibration and golden cases with exact expected outputs;
- sensitivity and impact reports;
- limitations register; and
- disclosure mapping to the informational intended use.

### 7.3 Exit criteria

The exact candidate remains non-runtime until it has a stable identity and
digest, complete trace, deterministic replay, no unresolved blocking test,
successful internal hold-out evaluation, documented sensitivity, no forbidden
proxy leakage, accepted impact/limitations package and explicit product-owner
acceptance. Release requires its separate downstream authority.

If this bundle contains a substantive contradiction, the Sol pass must not
start. The contradiction must be returned to product-policy review rather than
resolved by inventing a numerical convention.

## 8. Consolidated alternatives and recommendation

| Decision | Recommended candidate | Retained comparison | Rejected or deferred |
|---|---|---|---|
| `PSC-OD-005` | Mapping Option A lookup consuming Policy Option C layers; single unresolved favourability construct | future Option B multi-attribute model; non-compensatory stress case | exact mapping deferred |
| `PSC-OD-013` | separate qualified criticality layer; informational by default | informational-only baseline | direct penalty rejected |
| `PSC-OD-014` | no zero override for initial MVP | future closed qualified override set | any automatic zero trigger |
| `PSC-OD-015` | coverage disclosure plus indispensable-input gate | display-only baseline | numerical multiplier |
| `PSC-OD-016` | fail-closed `not_computable` for indispensable gaps | explicit non-applicability | numerical fallback |
| `PSC-OD-017` | separate disclosure plus typed invalid-conclusion gate | disclosure-only baseline | score modifier |
| `PSC-OD-018` | exact/fixed-point deterministic family, terminal rounding locus, canonical JSON and replay | exact rational derivation | concrete precision/rule deferred |
| `PSC-OD-019` | internal judgments, calibration, sealed hold-out, golden/adversarial/sensitivity/impact package | future external assurance | any claim of independence |

### 8.1 Recommended bundle

`RECOMMENDED INTERNAL MVP POLICY BUNDLE — SELECTED AS CANDIDATE DIRECTION`

The recommended bundle uses the simplest transparent layered architecture:

- one internally instantiated but still-unapproved ingredient-favourability
  score-bearing construct;
- support and informational dimensions kept outside numerical goodness;
- criticality separated and informational by default;
- no initial zero override;
- coverage and confidence disclosed separately, with only named validity or
  indispensability gates;
- `not_computable` as a non-numeric outcome with no fallback;
- deterministic exact/fixed-point execution to be frozen only with the formula;
- an internal calibration/hold-out/golden/adversarial validation package; and
- complete provenance, limitations, impact and disclosure mapping.

This bundle favors simplicity, auditability, deterministic replay, conservative
missing-data behavior, explanation, double-counting control and compatibility
with the informational disclaimer. It remains revisable. The separate exact
candidate package instantiates parameters and values for internal review only;
they are not approved policy or runtime authority.

## 9. Product-owner direction recorded

The product owner supplied the following direction on `2026-09-02`; this records
candidate selection and preparation authority only, without closing any decision
or granting runtime or release authority:

> I select the `RECOMMENDED INTERNAL MVP POLICY BUNDLE`
> described in the WYE Consolidated Ingredient Scoring Policy Bundle RFC as the
> candidate direction for `PSC-OD-005` and `PSC-OD-013` through `PSC-OD-019`.
> All those decisions remain `OPEN`. I authorize preparation of one exact
> numerical candidate package under Internal Informational Assurance and confirm
> that external validation remains future, optional and not present. I authorize
> no runtime or release. I authorize one future consolidated use of GPT-5.6 Sol
> at High reasoning for that candidate package, subject to the readiness
> conditions and without starting `PSC-OD-006`.

The product owner subsequently selected Mapping Option A as the MVP candidate
direction for the exact internal candidate, while retaining Policy Option C for
layer separation. Mapping Option B remains a future possible multi-attribute
development. This direction leaves `PSC-OD-005` and `PSC-OD-013` through
`PSC-OD-019` open and authorizes neither runtime, release nor push.

## 10. Current finding and exit state

No substantive internal conflict is identified in this draft. The unresolved
ingredient-favourability construct, reference judgments, corpus and exact
arithmetic choices are declared gaps, not silently resolved assumptions.

```text
bundle_status: SELECTED AS CANDIDATE DIRECTION — DECISIONS REMAIN OPEN
product_owner_selection: RECORDED 2026-09-02
exact_candidate: PRESENT — UNREVIEWED INTERNAL HEURISTIC CANDIDATE
internal_assurance_package: PRESENT — GENERATOR SELF-CHECK COMPLETE / REVIEW REQUIRED
external_validation: FUTURE / OPTIONAL / NOT PRESENT
runtime_authority: NONE
release_authority: NONE
PSC-OD-005: OPEN
PSC-OD-013: OPEN
PSC-OD-014: OPEN
PSC-OD-015: OPEN
PSC-OD-016: OPEN
PSC-OD-017: OPEN
PSC-OD-018: OPEN
PSC-OD-019: OPEN
PSC-OD-006: NOT STARTED
```
