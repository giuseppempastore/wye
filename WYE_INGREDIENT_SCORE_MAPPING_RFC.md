DRAFT — SCIENTIFIC/PRODUCT DECISION REQUIRED

# WYE — Ingredient Score Mapping RFC

## Document status and authority

```text
decision_id: PSC-OD-005
decision_status: OPEN
proposal_status: PROPOSED, NOT APPROVED
canonical_question: Map approved ingredient states and dimensions to a 0..100 ingredient scale without conflating missingness or uncertainty with risk.
document_authority: decision-support RFC only
scientific_approval: NOT PRESENT
product_approval: NOT PRESENT
validation_status: NOT PERFORMED
runtime_authority: NONE
cutoff: 2026-09-01
assurance_governance: INTERNAL INFORMATIONAL ASSURANCE ADOPTED 2026-09-02
external_validation: FUTURE / OPTIONAL / NOT PRESENT
```

This RFC compares methodological families for a future ingredient-level mapping.
It does not approve a formula, state policy, weight, threshold, mapping value,
computability gate, implementation or release. `PSC-OD-005` remains `OPEN`.

For the informational MVP, a protocol proposer prepares the candidate, the
internal validation function and data/model steward verify its assurance and
technical properties, and the product owner may accept the exact methodology
for bounded informational use. This acceptance cannot confer scientific,
clinical or regulatory validity. Independent external review is future and
optional under `WYE_INTERNAL_ASSURANCE_AND_DISCLOSURE_RFC.md`.

This RFC is distinct from:

- a scientific decision, which must bind an exact reviewed candidate;
- validation, which must test that candidate against independent reference
  judgments and a governed corpus;
- publication, which requires the Phase 7 approval lifecycle;
- implementation, which requires separate technical authorization after
  publication.

## A. Canonical perimeter and dependency audit

### A.1 Exact decision perimeter

The decision matrix defines `PSC-OD-005` exactly as:

> Map approved ingredient states and dimensions to a 0..100 ingredient scale
> without conflating missingness or uncertainty with risk.

The future output considered here is an ingredient-level mapped result. It is
not yet the product-level `ingredient_goodness_percent`: combining multiple
ingredients, relationships, quantities or ordering belongs to `PSC-OD-006`.
`ingredient_score` is therefore a working RFC label, not a newly approved API or
serialization field.

### A.2 Inputs already authorized

| Input | Authority | What may be relied upon | What is not authorized |
|---|---|---|---|
| `PSC-OD-001` | Product owner, Option A | First-release packaged-food domain, adults in the general population, informational and non-personal use. | Clinical, dietary, personal or release claims. |
| `PSC-OD-002` | Product owner, Option B | Goodness as transparent, versioned compositional and nutritional favourability under declared WYE criteria. | Measurement method, formula or scientific validation. |
| `PSC-OD-003` | Product owner, Option B | Domain-scoped, layered, source-backed ontology and mandatory separation of regulatory and methodological dimensions. | Specific classifications, operational sources or score effects. |
| `PSC-OD-004` | Product owner, Option B | Multi-label coexistence, contextual precedence, preservation of secondary assertions, ambiguity and conflict. | Operational precedence rules, state resolution or numerical consequences. |
| `PSC-OD-021` | Product owner, Option B | Domain-scoped source register, immutable artifacts, checksums, contextual authority and decision-linked provenance. | Selection of scoring sources or scientific correctness. |
| Phase 7 semantic architecture | Frozen architectural contracts | Evidence, hazard, exposure, risk, uncertainty, confidence and missingness remain distinct; deterministic versioned trace is required. | Scientific approval of ingredient dimensions or numeric scoring. |

### A.3 Candidate inputs that are not approved mapping premises

The following material can structure research and test design but must not be
treated as an approved numeric input:

- the Product Scoring Contract's ingredient assessment vocabulary, including
  `no_identified_concern`, `authorised_with_conditions`, `exposure_dependent`,
  `under_re_evaluation`, `evidence_uncertain`, `conflicting_evidence`,
  `critical_concern`, `not_authorised`, `withdrawn`, `unresolved` and
  `insufficient_data`;
- its ingredient dimensions: regulatory status, evidence state, hazard,
  exposure, risk, applicability, confidence and uncertainty;
- candidate ontology category families and review dispositions in
  `WYE_REGULATORY_ONTOLOGY_RFC.md`;
- candidate precedence rules and dispositions in
  `WYE_CATEGORY_PRECEDENCE_RFC.md`;
- evidence-selection, synthesis and ingredient-projection state vocabularies;
- the QPS selection policy `1.0.0-candidate.1` and its golden corpus, which
  remain unapproved and govern a separate evidence-selection question.

These candidates may appear in hypothetical test vectors only when labeled as
such. Their names do not supply an order, distance, weight or score direction.

### A.4 Missing prerequisites and open dependencies

The decision matrix names three direct prerequisites that do not yet exist as
approved artifacts:

1. an approved ingredient-state policy;
2. governed reference judgments;
3. a representative calibration corpus.

Additional linked decisions remain open:

| Decision | Dependency relationship |
|---|---|
| `PSC-OD-006` | Consumes the future ingredient-level mapping; multi-ingredient aggregation must not be hidden here. |
| `PSC-OD-013` and `PSC-OD-014` | Own flag effects, caps and zero overrides; this RFC assigns none. |
| `PSC-OD-015` | Owns coverage inputs and aggregation. |
| `PSC-OD-016` | Owns evaluability, indispensability, missing-data behavior and `not_computable` gates. |
| `PSC-OD-017` | Owns confidence derivation and its interaction with evaluability. |
| `PSC-OD-018` | Owns intermediate arithmetic, rounding and canonical numeric serialization. |
| `PSC-OD-019` | Owns the final validation plan, corpus, robustness and comprehension gates. |
| `PSC-OD-020` | Owns final user-facing language, bands, colors and interpretation. |

Consequently, coherent methodological alternatives can be reviewed now, but no
complete mapping can be approved from current inputs.

### A.5 Explicit exclusions

This RFC does not decide product-level ingredient aggregation, nutrition
mapping, overall aggregation, criticality, missing-data policy, coverage,
confidence, precision, UI, premium, personalization, API, runtime, database,
migration, code, fixtures, publication or release.

## B. Proposed scale semantics

### B.1 Direction and subject

Higher values would represent greater protocol-relative ingredient
favourability under the exact future WYE mapping and its applicable scope.
Lower values would represent lower favourability under that same mapping. The
direction is methodological, not clinical, regulatory or personal.

Compatibility of subject, question, protocol version, source cutoff and
applicable context is necessary but not sufficient for scientific
comparability. Compatibility alone does not authorize scientifically valid
comparisons, and no comparability across ingredients, categories or products is
approved. Comparability may be declared only after validation and approval of
the exact mapping candidate, its domain and the scale interpretation.
Cross-version comparisons require an impact analysis; cross-domain comparisons
are not authorized.

### B.2 Endpoints

For a `computable` result only:

- `0` would mean that the future published ingredient policy's defined lower
  endpoint was reached with the trace and prerequisites required by that policy;
- `100` would mean that its defined upper endpoint was reached with all material
  assessable criteria satisfied and any separately approved endpoint conditions
  met;
- neither endpoint is a probability or an intrinsic fact about the ingredient.

`0` does not demonstrate poison, illegality, clinical harm or personal risk.
`100` does not establish universal safety, benefit, unlimited safe use or legal
compliance. An informational `hazard_flag` alone cannot block `100`.

### B.3 Intermediate values and measurement level

Before calibration and validation, the defensible interpretation is a bounded
ordered index: a higher value means more favourable under one frozen protocol.
Equal numerical differences must not yet be interpreted as equal biological,
toxicological or product differences. In particular, an illustrative
ten-point difference is not evidence of a linear biological difference.

The Product Scoring Contract requires an eventual emitted score to be an integer
within `0..100`. `PSC-OD-018` still owns intermediate arithmetic, rounding and
canonical serialization; this RFC defines none of them.

Treating the scale as interval-like is a future empirical claim, not a property
created by printing integers. Ratio interpretations are excluded: a score of
`80` is not “twice as good” as `40`.

### B.4 Monotonicity properties

A future candidate must predeclare directional assumptions per approved input.
For two otherwise identical canonical cases:

- worsening an applicable, score-relevant input must not improve the score;
- improving it must not worsen the score;
- removing data must not improve the score, coverage or confidence;
- changing only confidence, coverage or missingness must not silently change the
  score through an undocumented penalty;
- an inapplicable dimension must not be treated as favourable or adverse;
- technical row order, source prestige, recency and AI output must not change the
  result unless an approved rule gives the semantic input a legitimate role.

Monotonic direction itself requires scientific review for each dimension. A
category or state name does not establish it.

### B.5 Conditions for `not_computable`

`not_computable` remains a valid non-numeric outcome. It emits no zero, neutral
anchor, midpoint, imputation or provisional percentage. The exact gates belong
to `PSC-OD-016`; this RFC can only identify candidate blocking conditions for
later review.

## C. Mandatory semantic separations

| Dimension | Meaning | Forbidden conversion into score |
|---|---|---|
| Ingredient score | Position under an approved, versioned mapping for the stated ingredient question. | Probability, safety, clinical risk or regulatory compliance. |
| Evidence available | Source-backed material eligible for review. | More records automatically mean a better or worse ingredient. |
| Missing data | Required or potentially relevant inputs not available or usable. | Zero, midpoint, benefit, danger or hidden penalty. |
| Coverage | Extent of policy-required inputs that were available and usable. | Ingredient favourability or confidence. |
| Confidence | Support for the exact conclusion emitted. | Safety probability, score multiplier or evaluability proxy. |
| Uncertainty | Limitations affecting the question, inputs, method or conclusion. | Adverse evidence or automatic decrement. |
| Hazard | Potential to cause an adverse effect under some conditions. | Exposure, risk, penalty, cap or override. |
| Exposure | Amount/contact under a stated scenario. | Ingredient-list presence or hazard. |
| Risk | Compatible hazard and exposure characterization for a defined context. | Context-free property or personal prediction. |
| Regulatory status | Scoped authority statement for entity, use, jurisdiction, date and conditions. | Goodness, universal safety or product compliance. |
| Critical flags | Separately governed contextual notices. | Numerical effect without `PSC-OD-013` or `PSC-OD-014`. |
| Evaluability | Whether the applicable policy can emit its requested conclusion. | Confidence level, coverage percentage or score direction. |
| Limitations | Boundaries on interpretation and transfer. | Numerical adjustment unless separately approved and traced. |

Invariant statements:

```text
missingness != risk
low confidence != penalty
absence of evidence != evidence of absence
hazard != exposure != risk
regulatory authorization != goodness
regulatory category != score
critical flag != automatic score effect
not_computable != zero
```

## D. Methodological alternatives

All formulas and structures in this section are `CANDIDATE — NOT APPROVED`.
No candidate may be used by runtime, fixtures or user-facing output.

### D.1 Option A — Reviewed ordinal lookup with bounded anchors

`CANDIDATE — NOT APPROVED`

**Description.** A scientific panel would define a finite set of approved,
contextual ingredient-state profiles and map each profile to an ordered anchor
or bounded band. Multi-label cases would require an explicit reviewed profile;
there would be no implicit “worst label wins” behavior.

**Candidate representation.** `score = M(reviewed_state_profile)`, where `M` is
a versioned lookup and every entry is a normative WYE decision supported by a
review rationale and validation case.

**Assumptions and inputs.** Requires an approved state policy, complete profile
definitions, contextual precedence, reference judgments and explicit treatment
of profiles not represented in the lookup.

**Properties.** Strongly ordinal and easy to audit. Monotonicity is inspectable
between declared neighboring profiles, but distances between anchors have no
automatic interval meaning.

**Partial inputs and extremes.** An incomplete or unmatched profile is not
assigned the nearest anchor; it follows the future evaluability policy. Endpoints
must be explicitly represented and independently reviewed.

**Weights and thresholds.** No weights are required, but every anchor and profile
boundary is a normative mapping choice requiring provenance, sensitivity tests
and validation. None is proposed here.

**Advantages.** High transparency, deterministic replay and clear explanation.

**Limitations.** Combinatorial growth, brittle coverage of multi-label states,
step changes at profile boundaries and pressure to impose a false total order on
scientifically incomparable dimensions.

**Validation and runtime impact.** Golden cases can test every lookup entry and
unmatched case. Runtime would be simple only after the table and all gates are
approved and published.

### D.2 Option B — Transparent monotone multi-attribute model

`CANDIDATE — NOT APPROVED`

**Description.** Approved score-relevant dimensions would retain separate
transformation cards, monotonic direction, applicability gate and trace. A
prespecified aggregation family would combine only evaluable dimension values;
coverage, confidence, uncertainty and critical flags would remain support
outputs rather than score multipliers.

**Candidate representation.** The abstract family is:

```text
dimension value d_j = f_j(approved input x_j, applicable context)
latent ingredient position L = A(d_1, ..., d_k; theta)
ingredient_score = R_0_100(L)
```

Every `f_j`, aggregation operator `A`, parameter in `theta` and rescaling rule
`R_0_100` is a normative WYE choice unless a reviewed source supports the exact
transfer. No function, weight or parameter value is proposed here.

**Assumptions and inputs.** Requires approved dimensions, directional semantics,
state-resolution policy, reference judgments, compensability policy and a
calibration corpus. It must declare interactions and avoid double counting
correlated or causally dependent dimensions.

**Properties.** Can enforce monotonicity explicitly and preserve a decomposable
trace. Its output remains ordinal unless calibration demonstrates stronger
measurement properties. Different normalizations and aggregation families may
produce materially different results.

**Partial inputs and extremes.** Missing dimensions are not set to a favorable,
adverse or average value. The future evaluability policy determines whether a
narrow computable profile exists or the result is `not_computable`. Endpoints
require documented conditions rather than mathematical clipping alone.

**Weights and thresholds.** Weighting, normalization, compensability and any
piecewise boundary are candidate choices requiring elicitation provenance,
uncertainty and sensitivity analysis, falsification criteria and independent
validation. None is approved by this RFC.

**Advantages.** Best balance of transparency, monotonic constraints,
decomposition, versioning, sensitivity analysis and compatibility with the
multi-axis ontology.

**Limitations.** Easily creates false precision; apparent simplicity can hide
normative weights, compensability and correlated inputs. It cannot proceed
without an approved state policy and robust calibration evidence.

**Validation and runtime impact.** Supports component-level golden cases,
counterfactuals and sensitivity analysis. Future runtime would require a frozen
canonical expression and parameter digest after scientific and validation gates.

### D.3 Option C — Reference-judgment calibrated latent scale

`CANDIDATE — NOT APPROVED`

**Description.** A governed panel would make blinded, structured pairwise or
ordered judgments on reference ingredient cases. A statistical model would
estimate a latent order and map it onto the bounded scale while retaining
disagreement and uncertainty.

**Candidate representation.** `latent position = fit(reference judgments,
case features, model assumptions)`, followed by a separately governed bounded
transformation. No model family or numeric anchor is selected here.

**Assumptions and inputs.** Requires representative cases, elicitation protocol,
reviewer competence and conflict-of-interest controls, inter-rater analysis,
held-out validation and an explicit construct link.

**Properties.** Can test ordering and reviewer agreement empirically, but scale
spacing depends on the fitted model. Monotonicity must be constrained and tested;
it does not follow automatically from expert judgments.

**Partial inputs and extremes.** Cases outside the calibrated support are not
extrapolated silently. Missing or conflicted judgments remain uncertainty or a
validation failure, not a score penalty.

**Weights and thresholds.** Model coefficients, priors, anchors and decision
boundaries would be candidate methodological choices with elicitation
provenance, sensitivity analysis and out-of-sample validation. None is proposed.

**Advantages.** Makes reference judgments explicit and provides empirical tests
of agreement and calibration.

**Limitations.** Resource intensive, vulnerable to framing and panel bias,
harder to explain, and at risk of converting normative consensus into apparent
scientific measurement precision.

**Validation and runtime impact.** Requires independent hold-out cases,
reproducible fitting and model-version artifacts. Runtime complexity and model
governance would be materially higher than Options A or B.

### D.4 Option D — Non-compensatory outranking followed by bounded reporting

`CANDIDATE — NOT APPROVED`

**Description.** Ingredient profiles would first be compared through a governed
partial-order or outranking procedure that can retain incomparability. A bounded
number would be emitted only where a separately justified reporting transform
preserves that order.

**Assumptions and inputs.** Requires approved veto/discordance concepts,
comparability rules and reference profiles. Those elements must not be borrowed
from criticality or missing-data policy.

**Properties.** Resists unlimited compensation and can represent incomparable
profiles. A single number may nevertheless destroy the very incomparability the
method protects.

**Partial inputs and extremes.** Unresolved comparisons remain unresolved; they
are not forced into the middle of the scale. Endpoints need independent rules.

**Weights and thresholds.** Preference, concordance, discordance and veto
parameters would all be normative candidate choices requiring sensitivity and
validation; none is proposed.

**Advantages.** Strong protection against hidden compensation and forced total
ordering.

**Limitations.** Complex explanation, possible non-transitivity and weak fit with
a mandatory single integer unless information loss is scientifically justified.

**Validation and runtime impact.** Requires adversarial cycle and incomparability
cases plus a justified scalarization step. Runtime remains unauthorized.

### D.5 Comparison

| Criterion | Option A | Option B | Option C | Option D |
|---|---|---|---|---|
| Transparency | High for represented profiles | High if all cards and parameters are published | Moderate | Moderate |
| Monotonicity | Reviewed profile order | Explicit constraints | Must be constrained and tested | Partial-order dependent |
| Multi-axis fit | Limited by profile growth | Strong | Strong if features are governed | Strong |
| False-precision risk | Moderate | High unless interpretation is restrained | High | Moderate at scalarization |
| Sensitivity analysis | Anchor/profile perturbation | Strong and decomposable | Model and panel perturbation | Rule/parameter perturbation |
| `not_computable` compatibility | Strong | Strong if external gates remain separate | Strong outside calibrated support | Strong for incomparability |
| Golden-corpus validation | Exhaustive lookup cases | Dimension, integration and end-to-end cases | Training/hold-out separation required | Cycle and scalarization cases required |

## E. Recommendation

### E.1 Recommended family

`PROPOSED, NOT APPROVED`

Option B is recommended as the research and decision-package family, not as an
approved formula. It best preserves the decided multi-axis ontology, permits
explicit monotonicity, exposes normative choices, separates score from evidence
quality, and supports versioned sensitivity analysis.

The recommendation is conditional on these safeguards:

1. approve the ingredient-state policy before mapping any state;
2. publish a dimension card for every candidate input, including construct link,
   direction, applicability, dependencies and forbidden interpretations;
3. treat the initial scale as ordered, not interval or ratio;
4. keep missingness, coverage, confidence and uncertainty outside the score
   calculation unless a later decision explicitly and scientifically justifies
   a different relationship;
5. use structured reference judgments and a representative calibration corpus
   to test, not merely decorate, normative choices;
6. compare Option B against at least the transparent lookup baseline in Option A
   and the non-compensatory stress case in Option D;
7. reject the candidate if plausible choices produce unstable ordering or
   clinically misleading endpoint interpretations.

Option C may support calibration and validation but is not recommended as the
primary explanatory model. Option D is valuable as a non-compensation stress
test. Option A is the required transparency baseline.

### E.2 Why the recommendation does not decide `PSC-OD-005`

No approved dimension transformations, aggregation family, parameters,
reference judgments or calibration corpus exist. The recommendation therefore
selects only a family for further scientific development. It grants no product,
scientific, validation, publication or runtime authority.

## F. Missingness, uncertainty and computability scenarios

All dispositions below are `CANDIDATE — NOT APPROVED` and defer exact gates to
`PSC-OD-015`, `PSC-OD-016` and `PSC-OD-017`.

| Scenario | Candidate `evaluability_status` | Numeric score | Coverage | Confidence | Uncertainty and limitations | Missing inputs |
|---|---|---|---|---|---|---|
| Complete approved evidence and state inputs | `computable` only if every future required gate passes | Emitted under the approved mapping | Report separately | Report separately | Retain residual model and evidence uncertainty | Explicit empty set only after governed review |
| Partial evidence but sufficient for the exact approved conclusion | Candidate `computable`; sufficiency gate remains open | May be emitted only if the future policy permits the narrower input profile | Reduced or dimension-specific | Conclusion-specific | State omitted scope and sensitivity to missing inputs | Name every absent required/optional input |
| Evidence insufficient for the requested mapping | `not_computable` | Not emitted | Report available portion | Confidence in the non-computability conclusion, if defined | State insufficiency without danger/safety inference | Required evidence or state inputs |
| Applicable sources materially conflict | Candidate `not_computable` for the affected conclusion unless a future policy permits an explicit conflict result | Not emitted for the blocked conclusion | Report separately | Not a conflict-resolution proxy | Preserve both lines, comparability assessment and unresolved uncertainty | Resolution or additional evidence needed |
| Regulatory status not applicable | Depends on whether the dimension is indispensable for this exact question | No favorable/adverse substitute | Exclude only under a future declared denominator rule | Separate | `not_applicable` is neither good nor bad | None merely because the dimension is inapplicable |
| Ingredient identity ambiguous | Candidate `not_computable` where identity is indispensable | Not emitted | Report identity coverage separately | Separate | Preserve candidate identities and transfer limits | Canonical identity evidence/review |
| Dimension not assessed | Candidate `not_computable` if required; otherwise narrower conclusion only if approved | No default or midpoint | Report as unassessed | Separate | Distinguish unassessed from inapplicable | Required assessment output |
| Dimension not pertinent | Candidate treatment under future applicability policy | No default benefit or penalty | Denominator treatment remains open | Separate | Record rationale and scope | None if reviewed as truly inapplicable |
| Acquired artifact integrity compromised | `not_computable` for any conclusion depending on that artifact until replaced or verified | Not emitted | Report unusable dependency | Separate | Record integrity event and provenance | Verified replacement or restored integrity evidence |

Technical execution failure remains distinct from a scientifically valid
`not_computable` result.

## G. Future validation plan

This is a non-operative plan. `PSC-OD-019` retains authority over the final
validation package.

### G.1 Required studies

- **Construct trace:** verify that every mapped dimension measures the decided
  ingredient-favourability construct rather than risk, regulatory compliance,
  popularity or data availability.
- **Monotonicity tests:** perturb one approved input at a time across applicable
  contexts and test all predeclared directions.
- **Sensitivity analysis:** vary normalization, transformations, parameters,
  compensability assumptions, state resolution and reference judgments; report
  effects on values, ordering and endpoint reachability.
- **Extreme analysis:** test legitimate lower/upper cases, near-boundary cases
  and confirm that missingness or an informational hazard flag cannot create an
  endpoint.
- **Local stability:** test whether small, non-material input changes create
  disproportionate score changes.
- **Reviewer agreement:** measure agreement and disagreement on state cards,
  directions and reference cases; preserve dissent and uncertainty.
- **Contradictory cases:** include multi-label, ambiguous, conflicting,
  non-applicable and apparently similar cases with different source scopes.
- **Golden corpus:** maintain independently authored expected outcomes, provenance,
  role labels and a digest distinct from implementation.
- **Calibration review:** separate calibration from hold-out validation and
  document all data-driven and normative choices.
- **Version impact:** compare every candidate version with its predecessor and
  retain historical results.
- **Comprehension review:** test whether users misread endpoints, differences or
  uncertainty as clinical safety or personal advice.

### G.2 Falsification criteria

A candidate must return to draft if any material condition holds:

- required monotonicity fails without a scientifically defensible explanation;
- plausible alternative assumptions materially reverse reference ordering;
- one undocumented dimension dominates output behavior;
- missingness, low confidence or uncertainty acts as an implicit penalty;
- regulatory category or authorization produces an automatic direction;
- an informational hazard flag changes the score;
- reference reviewers cannot reach reproducible judgments for the claimed scale;
- endpoint wording is predictably interpreted as universal safety or clinical
  danger;
- replay under identical canonical inputs and version is not deterministic.

### G.3 Approval gate

Approval requires an exact candidate identity and digest, complete source and
decision provenance, internal methodology and validation dispositions,
data/model-steward verification, product-owner acceptance, resolved blocking
dependencies, approved internal golden corpus, impact report and a separate
release decision. Passing technical checks is insufficient; independent
external validation remains an optional future tier.

## H. Internal evidence register

Access date for all sources: `2026-09-01`. The sources support methodological
principles only; none supplies or approves a WYE ingredient mapping.

| Source ID | Source | Identifier or official locator | Methodological role | Transferability limit | `PSC-OD-021` link |
|---|---|---|---|---|---|
| `SRC-OECD-JRC-CI-2008` | OECD, European Union and EC-JRC, *Handbook on Constructing Composite Indicators: Methodology and User Guide* (2008) | [DOI 10.1787/9789264043466-en](https://doi.org/10.1787/9789264043466-en) | Conceptual framework, normalization, weighting, aggregation, robustness, decomposition and transparency. | Developed mainly for policy composite indicators; not food science, toxicology or WYE validation. | New proposed register record; immutable artifact and exact use must be governed before decision use. |
| `SRC-JRC-COIN-NORM-2020` | European Commission JRC COIN, *Step 5: Normalisation* (2020 revision) | [Official K4P page](https://knowledge4policy.ec.europa.eu/composite-indicators/toolkit_en/navigation-page/10-step-guide_en/step-5-normalisation_en) | Supports the need to choose normalization according to data properties and indicator purpose. | A methodological guide, not authority for WYE dimensions or scale endpoints. | New proposed register record. |
| `SRC-JRC-COIN-SA-2020` | European Commission JRC COIN, *Step 8: Sensitivity analysis* (2020 revision) | [Official K4P page](https://knowledge4policy.ec.europa.eu/composite-indicators/toolkit_en/navigation-page/10-step-guide_en/step-8-sensitivity-analysis_en) | Supports plural scenarios and uncertainty/sensitivity analysis for robustness and transparency. | Examples concern composite indicators generally; no WYE-specific acceptance criterion. | New proposed register record. |
| `SRC-SAISANA-SA-2005` | Saisana, Saltelli and Tarantola, *Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators* (2005) | [DOI 10.1111/j.1467-985X.2005.00350.x](https://doi.org/10.1111/j.1467-985X.2005.00350.x) | Peer-reviewed basis for using uncertainty and sensitivity analysis to inspect robustness and policy-message dependence. | Country-level indicator application; does not validate transfer to ingredient scoring. | New proposed register record requiring artifact acquisition and review. |
| `SRC-EFSA-UNCERTAINTY-2018` | EFSA Scientific Committee, *Guidance on Uncertainty Analysis in Scientific Assessments* (2018) | [DOI 10.2903/j.efsa.2018.5123](https://doi.org/10.2903/j.efsa.2018.5123) | Supports identifying, characterizing and reporting uncertainty and its effect on conclusions. | EFSA scientific-assessment guidance; does not prescribe a goodness score or missing-data penalty. | Candidate link to existing evidence-governance concepts; exact register identity still required. |
| `SRC-EFSA-WOE-2017` | EFSA Scientific Committee, *Guidance on the use of the weight of evidence approach in scientific assessments* (2017) | [DOI 10.2903/j.efsa.2017.4971](https://doi.org/10.2903/j.efsa.2017.4971) | Supports question-specific evidence lines and explicit reliability, relevance and consistency considerations. | Weight of evidence is not numeric WYE goodness and cannot be reused as a score weight without separate justification. | Candidate link to WYE evidence selection/synthesis; not an operational scoring source. |
| `SRC-EFSA-BIOREL-2017` | EFSA Scientific Committee, *Guidance on the assessment of the biological relevance of data in scientific assessments* (2017) | [DOI 10.2903/j.efsa.2017.4970](https://doi.org/10.2903/j.efsa.2017.4970) | Supports explicit agents, effects, subjects and conditions and separation of statistical from biological relevance. | Does not define compositional favourability, ingredient ordering or score direction. | New proposed decision-use link; applicability review required. |
| `SRC-EFSA-EKE-2014` | European Food Safety Authority, *Guidance on Expert Knowledge Elicitation in Food and Feed Safety Risk Assessment* (2014) | [DOI 10.2903/j.efsa.2014.3734](https://doi.org/10.2903/j.efsa.2014.3734) | Supports structured elicitation, bias controls, uncertainty and documentation for future reference judgments. | Developed for food/feed risk assessment; WYE goodness is not risk, so only elicitation-process principles may transfer. | New proposed register record and restricted methodological role. |
| `SRC-STEVENS-SCALES-1946` | S. S. Stevens, *On the Theory of Scales of Measurement* (1946) | [PMID 20984256](https://pubmed.ncbi.nlm.nih.gov/20984256/) | Historical measurement-theory basis for distinguishing ordinal, interval and ratio interpretations. | Classic taxonomy is not sufficient validation and does not prove that the WYE scale has interval properties. | New proposed register record; background-only role. |
| `SRC-CODEX-RISK-2007` | FAO/WHO Codex Alimentarius Commission, *Working Principles for Risk Analysis for Food Safety for Application by Governments*, CXG 62-2007 | [Official CXG 62-2007 document](https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXG%2B62-2007%252FCXG_062e.pdf) | Reused internal support for keeping hazard, exposure, risk assessment, management and communication distinct. | Government food-safety framework; not a scoring authority, clinical conclusion or WYE compliance approval. | Reuse only through the governed record already referenced by WYE source-governance artifacts. |

### H.1 Evidence interpretation

`SOURCE FACT`: these sources describe general measurement, composite-indicator,
evidence, uncertainty, elicitation or risk-analysis principles within their own
scope.

`WYE METHODOLOGICAL INFERENCE`: a future ingredient mapping should expose its
construct, normative choices, uncertainty and sensitivity and should initially
avoid interval-like claims.

`WYE PROPOSAL`: Option B is the preferred family for further development. This
proposal is not reported by any source and has no approval authority.

## I. Decision package

### I.1 Questions for accountable roles

Question for the product owner, within product authority only:

> Does the product require a transparent, decomposable and explicitly
> protocol-relative ingredient mapping whose initial interpretation is ordered
> rather than interval-like, while accepting that scientific validation may
> reject or materially change the proposed family?

Question for the internal methodology and validation functions:

> After the state policy, reference judgments and calibration corpus are
> approved, which reviewed candidate mapping validly represents ingredient
> favourability on the bounded WYE scale while preserving monotonicity,
> uncertainty, non-computability and the mandatory semantic separations?

The product-owner candidate-direction answer alone cannot close `PSC-OD-005`.
Closure requires the complete Internal Informational Assurance package,
data/model-steward verification and a separate product-owner acceptance of the
exact candidate under the authority recorded in the decision matrix.

### I.2 Options and principal trade-offs

- **Option A:** maximal lookup transparency, but poor scalability and risk of a
  forced total order.
- **Option B:** strongest decomposability and sensitivity analysis, but high risk
  of hidden normative weights and false precision.
- **Option C:** empirical calibration to judgments, but costly, model-dependent
  and vulnerable to expert-framing bias.
- **Option D:** protects non-compensation and incomparability, but fits a single
  bounded integer only through a potentially lossy extra step.

### I.3 Minimum conditions before a decision

- approved ingredient-state and dimension policy;
- decision-scoped source register and cutoff;
- documented directional and applicability rules;
- governed reference-judgment protocol and reviewer roles;
- representative calibration corpus and internally separated validation set;
- exact candidate formulas/parameters and canonical identity;
- sensitivity, monotonicity, extremes, stability and falsification results;
- explicit dependency handling for `PSC-OD-013` through `PSC-OD-019`;
- communication risk review without approving final UI;
- internal methodology and validation dispositions, data/model-steward check
  and product-owner acceptance; external independent validation is optional for
  the informational MVP.

### I.4 Proposed decision record

```text
decision_id: PSC-OD-005
decision_status: OPEN
proposal_status: PROPOSED, NOT APPROVED
recommended_research_family: Option B — transparent monotone multi-attribute model
decision_owner: Product owner after Internal Informational Assurance
methodology_preparation: Protocol proposer / Codex-assisted workflow
technical_verification: Data/model steward
internal_validation: REQUIRED — NOT COMPLETE
external_validation: FUTURE / OPTIONAL / NOT PRESENT
candidate_direction_date: 2026-09-02
candidate_direction_authority: Product owner
product_owner_candidate_direction: Option B — multi-attribute monotone and decomposable model
candidate_direction_nature: CANDIDATE DESIGN DIRECTION ONLY
approved_state_policy: NOT PRESENT
reference_judgments: NOT PRESENT
calibration_corpus: NOT PRESENT
exact_formula: NOT PROPOSED OR APPROVED
weights_or_thresholds: NOT PROPOSED OR APPROVED
scientific_approval: NOT PRESENT
scientific_validation: NOT CLAIMED
validation_owner_approval: INTERNAL DISPOSITION NOT PRESENT
implementation_authorization: NOT PRESENT
runtime_authority: NONE
release_status: NOT APPROVED
```

The product owner confirms the semantic boundaries of `PSC-OD-005` and selects
Option B — the multi-attribute monotone and decomposable model — exclusively as
the candidate design direction for subsequent scientific development. This
direction is conditional and does not constitute scientific approval or
validation of the mapping. It does not approve formulas, transformations,
weights, thresholds, parameters, caps, floors, overrides, comparability or
numerical outputs, and it does not authorize implementation, publication or
release. `PSC-OD-005` remains `OPEN`.

The internal methodology and validation functions may reject, modify or replace
the candidate direction before product-owner acceptance. Future external
reviewers may also challenge it without being an MVP prerequisite. Option A
remains the transparency baseline and Option D remains the non-compensatory
stress case. Internal validation must still compare the exact candidate with
alternatives and baselines. The direction gives the scale
no interval or ratio properties, approves no comparability across ingredients,
categories or products, and authorizes no `0..100` value for runtime or UI.

### I.5 Exit criteria for this RFC

- the canonical question is preserved;
- approved and candidate inputs are distinguished;
- at least three genuinely different methodological families are reviewable;
- scale semantics and non-claims are explicit;
- missingness, uncertainty, confidence, coverage, hazard, exposure and risk are
  not collapsed into score;
- the recommendation is explicitly provisional;
- sources and methodological inferences are attributable and bounded;
- unresolved prerequisites are visible;
- `PSC-OD-005` remains `OPEN`;
- no implementation or release authority is created.

## J. Acceptance checklist and exit state

- [x] The exact `PSC-OD-005` matrix scope is quoted.
- [x] `PSC-OD-001`, `PSC-OD-002`, `PSC-OD-003`, `PSC-OD-004` and `PSC-OD-021`
  remain the only `DECIDED` decisions.
- [x] `PSC-OD-005` through `PSC-OD-020` and `PSC-OD-022` remain `OPEN`.
- [x] Approved inputs are separated from candidate vocabularies and artifacts.
- [x] The ingredient-level mapping is separated from `PSC-OD-006` product-level
  ingredient aggregation.
- [x] Four alternatives and one provisional recommendation are documented.
- [x] Every candidate formula or parameter family is marked
  `CANDIDATE — NOT APPROVED`.
- [x] No numerical mapping value, weight, threshold, cap, floor or ranking is
  approved.
- [x] `not_computable` has no substitute numeric value.
- [x] Missingness and uncertainty produce no automatic penalty.
- [x] Hazard, exposure, risk, regulatory status, confidence and coverage remain
  separate.
- [x] QPS candidate, golden corpus, publication state, delivery package and
  approval gate are unchanged and separate.
- [x] No API, runtime, database, migration, code, fixture, UI, premium or
  personalization is introduced.
- [x] The document is ready for independent read-only review.

```text
RFC status: DRAFT — SCIENTIFIC/PRODUCT DECISION REQUIRED
PSC-OD-005: OPEN
recommended family: OPTION B — PROPOSED, NOT APPROVED
approved ingredient-state policy: NOT PRESENT
reference judgments: NOT PRESENT
calibration corpus: NOT PRESENT
scientific validation: NOT PERFORMED
runtime authority: NONE
next gate: INDEPENDENT READ-ONLY REVIEW
```
