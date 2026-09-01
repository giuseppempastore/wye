DECIDED — SEMANTIC/PRODUCT BOUNDARY APPROVED; SCIENTIFIC VALIDATION PENDING

# WYE — Product Goodness Construct RFC

## Document status and authority

```text
decision_id: PSC-OD-002
decision_status: DECIDED
document_kind: methodological decision record
decision_owner: Product owner
decision_date: 2026-09-01
authority_source: Explicit product-owner approval
decision_scope: semantic and product boundary of the construct
research_cutoff: 2026-09-01
scientific_approval: NOT PRESENT
scientific_status: internal evidence-informed methodology; no external scientific validation performed
clinical_approval: NOT PRESENT
legal_or_regulatory_approval: NOT PRESENT
implementation_status: no formulas, scales or runtime approved
runtime_authority: NONE
```

This document records the product owner's explicit approval of the semantic and
product boundary of Alternative B and closes only `PSC-OD-002`. It does not
publish an externally validated scientific method, approve a claim or authorize
calculation or display of a product score.

AI assistance may support research, comparison, drafting and consistency
checks. AI is not a scientific authority and cannot approve this construct.
The product owner has approved the intended product value and product boundary,
but product-owner approval does not turn the construct into external scientific
validation. Future measurement methods and implementation candidates require
proportionate, traceable scientific governance under their declared authorities.

The candidate `efsa_qps_evidence_selection/1.0.0-candidate.1`, its golden
corpus, delivery package, publication state and external approval gate are
separate controlled subjects. This RFC neither uses that candidate as a
product-scoring method nor modifies, approves, promotes or supersedes it.

Normative project context for this decision record is provided by:

- `WYE_PRODUCT_SCORING_CONTRACT.md`;
- `WYE_PRODUCT_INTENDED_USE_CLAIMS_RFC.md`;
- `Checkpoints/WYE_PHASE_7.md`;
- `WYE_SCORING_SEMANTICS.md`;
- `WYE_SCORING_PROTOCOL.md`;
- `WYE_PRODUCT_ASSESSMENT.md`;
- `WYE_EVIDENCE_SELECTION.md`;
- `WYE_EVIDENCE_SYNTHESIS.md`;
- `WYE_INGREDIENT_PROJECTION.md`.

Where legacy MVP documentation conflicts with the Phase 7 contracts, the
Phase 7 contracts govern. Legacy formulas, classifications, product claims and
premium ambitions are not evidence for this construct.

## A. Recorded decision boundary

### A.1 Exact decision boundary

`PSC-OD-002` records the semantic and product boundary of the scientific and
methodological construct represented by WYE “goodness” for the first-release
intended use already recorded in `PSC-OD-001`.

The decision establishes:

- the common semantic core shared by `ingredient_goodness_percent`,
  `nutrition_goodness_percent` and `overall_goodness_percent`;
- the distinction between the ingredient, nutrition and overall dimensions;
- the relationship between a WYE assessment and declared product composition;
- the interpretation limits that prevent a protocol-relative result from being
  presented as an intrinsic fact, a health probability or personal advice;
- the qualitative properties every future model must satisfy;
- the evidence, review and governance that remain necessary after the semantic
  and product boundary becomes `DECIDED`.

The decision concerns meaning before measurement. A future numeric position can
be scientifically evaluated only after the construct, intended use and
non-claims are stable.

### A.2 Explicitly outside this decision

This RFC does not select or define:

- a formula, weight, multiplier, threshold, score band, cap, floor or ranking;
- a nutrient profiling model;
- a regulatory-status ontology;
- ingredient assessment-state resolution or precedence;
- treatment of any individual ingredient or nutrient;
- product category or preparation-state rules;
- ingredient, nutrition or overall aggregation;
- critical-flag effects or override behavior;
- required inputs or coverage aggregation;
- evaluability or missing-data gates;
- confidence derivation;
- precision, rounding or serialization;
- final UI copy, colors or claims;
- premium or personalized assessment;
- runtime, API, database, migration or application code.

Those subjects remain governed by `PSC-OD-003` through `PSC-OD-022` as
applicable. Nothing in this RFC changes their status.

### A.3 Recorded basis and downstream authority

The product-owner decision records:

- a construct definition and explicit non-constructs;
- comparison of credible alternatives;
- a documented link to `PSC-OD-001` and its non-claims;
- evidence that the construct is measurable in principle from the permitted
  product domain without inventing personal exposure or outcomes.

Closure of the semantic and product boundary does not complete scientific
validation. Downstream governance still requires:

- a construct-validation plan proportionate to the claims eventually sought;
- review of the three dimension definitions for scientific coherence;
- communication review for foreseeable over-interpretation;
- a traceable decision by a multidisciplinary scientific review panel.

Legal or regulatory review remains necessary for external claims and wording.
It does not substitute for scientific construct review.

## B. Mandatory epistemic distinction

WYE must preserve four statement classes.

| Class | What belongs in the class | What must remain visible | Forbidden conversion |
|---|---|---|---|
| Product or label facts | Declared ingredients, declared nutrition values and basis, declared serving when available, declared allergens, product identity and packaging information. | Exact product, label source, declaration basis, date/version, extraction or verification status and limitations. | A declared fact must not silently become a conclusion about health, safety, risk or goodness. |
| Source or evidence facts | Source identity, version, date, provenance, scope, method, quality observations and stated limitations. | The exact proposition reported by the source and the context in which it applies. | Source authority, publication count or evidence availability must not become a score or product conclusion by itself. |
| WYE methodological assessments | Goodness dimensions, score outputs when computable, evaluability, coverage, confidence, critical flags, limitations and missing inputs. | WYE protocol identity, applicable construct, inputs, reasons, uncertainty and trace. | A WYE assessment must not be presented as an intrinsic product fact or as a clinical state of the user. |
| Unauthorized conclusions | Personal benefit, personal health, universal safety, clinical risk, prevention or treatment, suitability for a disease, recommended dose, portion or frequency. | These statements remain outside the first-release intended use. | A disclaimer, high score or authoritative source cannot authorize them. |

The controlling separation is:

```text
declared product fact
!= source or evidence fact
!= WYE methodological assessment
!= personal or clinical conclusion
```

“Goodness” is therefore neither physically contained in a product nor directly
observed on its label. It is a WYE methodological judgment produced only under
an applicable, versioned and validated future protocol.

## C. Construct alternatives

The alternatives below are retained as decision history. Alternative B alone was
approved for the semantic and product boundary; no measurement method was
approved.

| Alternative | Proposed meaning | Strengths | Limitations and risks | Disposition |
|---|---|---|---|---|
| A — compositional and methodological quality only | Goodness describes how completely and coherently the declared product composition satisfies a WYE assessment framework, without a population-oriented notion of favourability. | Strong epistemic restraint; easy separation from health, risk and personal advice; compatible with transparent data-quality reporting. | May collapse methodological adequacy and product favourability; may be too weak to explain why ingredient and nutrition outputs have an ordered direction; could be confused with coverage or confidence. | Not selected; retained as decision history. |
| B — compositional and nutritional favourability under declared general-population criteria | Goodness describes protocol-relative favourability of declared ingredient composition and declared nutritional profile for the general-population intended use, while keeping both dimensions separate and preserving limitations. | Fits `PSC-OD-001`; allows distinct ingredient and nutrition constructs; supports transparent comparison only within a future declared protocol; does not require personal data or clinical prediction. | “Favourability” can still be overread as “healthy” or “safe”; criteria, validation and communication must be purpose-specific; this evidence set identifies no authoritative external standard directly equivalent to ingredient goodness, which therefore needs independent construct validation. | `DECIDED — PRODUCT OWNER APPROVED` for the semantic and product boundary only. |
| C — proxy for health benefit, harm or clinical risk | Goodness estimates whether a product improves health, is safe, or changes the probability of a clinical outcome. | Superficially intuitive and commercially strong. | Requires exposure, intake, total diet, population and individual context, validated outcomes and a different claims/governance framework. It conflicts with the general, non-personal and non-clinical first-release boundary. | Not selected; strongly discouraged and incompatible with `PSC-OD-001` for the first release. |

Alternative C is not made acceptable by describing the output as informational.
A probability, risk or benefit proxy remains a clinical or health-related
construct even if accompanied by a disclaimer.

## D. Decided methodological construct

### D.1 Decided construct

The following definition records the product-owner decision:

> WYE goodness is a transparent, versioned methodological assessment of the
> compositional and nutritional favourability of a packaged food or beverage
> against declared and applicable WYE criteria for adults in the general
> population. It does not represent personal health, absolute healthiness,
> universal safety, probability of clinical benefit or harm, exposure, dose,
> clinical risk, regulatory compliance or individual suitability.

This definition is a `WYE DECISION`, not a fact reported by an external source.
Its approval is limited to the semantic and product boundary and is not external
scientific, clinical, legal or regulatory validation.

### D.2 Relationship to `PSC-OD-001`

The decided construct fits the intended use because it:

- concerns packaged foods and beverages within the existing food-only domain;
- addresses adults in the general population without a user health profile;
- treats the output as informational, methodological and versioned;
- uses product-level declared data rather than actual individual intake;
- excludes diagnosis, treatment, dietary prescription, dose, portion,
  frequency and personal recommendation;
- permits `not_computable` to remain a valid result when the future policy's
  requirements are not met.

### D.3 Why three dimensions remain necessary

The common construct is protocol-relative favourability, but its subjects are
different:

- ingredient goodness concerns declared ingredient composition and applicable
  ingredient evidence;
- nutrition goodness concerns the declared nutritional profile on an applicable
  standardized basis;
- overall goodness concerns a future governed synthesis of the two dimensions.

Sharing a semantic direction does not make the dimensions interchangeable.
Evidence used for one dimension cannot silently determine another, and overall
cannot become a synonym for either component.

### D.4 Why the decision remains bounded

The decided construct does not claim that favourable composition predicts a person's
health outcome. Authoritative nutrient profiling sources show that profiling
models are developed for specific purposes and applications, while healthy-diet
guidance concerns the diet as a whole and varies with individual and contextual
factors. Food-safety risk analysis additionally requires hazard and likelihood
or exposure concepts that are absent from this construct.

The decision therefore creates semantic room for future methods without
selecting any of them. It does not decide which facts contribute, how they are
combined, when results are computable or how uncertainty affects presentation.

## E. Semantics of the three future outputs

### E.1 `ingredient_goodness_percent`

Decision-aligned semantic subject:

> The protocol-relative favourability of the product's declared ingredient
> composition under future WYE criteria that preserve ingredient identity,
> source evidence, regulatory context, applicability, uncertainty and product
> limitations as separate traceable dimensions.

It may eventually represent a WYE judgment about the declared ingredient
composition. It cannot, by itself, indicate:

- clinical safety or toxicity of the product;
- personal allergen suitability;
- actual exposure, dose or risk;
- that every ingredient is harmless or beneficial;
- that authorization equals universal safety;
- that “natural” is favourable or “artificial” is unfavourable;
- the fraction of ingredients considered safe;
- regulatory compliance of the product.

No individual ingredient criterion or mapping is proposed here. The construct
must remain compatible with the non-scalar evidence, synthesis and projection
contracts until later governed decisions define an ingredient-scoring method.

### E.2 `nutrition_goodness_percent`

Decision-aligned semantic subject:

> The protocol-relative favourability of the declared nutritional profile of the
> product under a future purpose-specific and applicable WYE nutrient profiling
> method, using the governed basis, category and preparation state required by
> that method.

It may eventually represent a WYE nutritional-quality judgment for the product
under declared criteria. It cannot, by itself, indicate:

- the quality or adequacy of a person's total diet;
- an appropriate personal portion or consumption frequency;
- prevention, treatment or individual health benefit;
- suitability for a disease, pregnancy, childhood or another special context;
- universal nutritional superiority across categories or methods;
- regulatory authorization for a nutrition or health claim;
- ingredient safety or toxicological risk.

This RFC does not select a nutrient profiling model, food category, component,
reference basis or treatment of missing declared nutrition data.

### E.3 `overall_goodness_percent`

Decision-aligned semantic subject:

> A future protocol-relative synthesis of ingredient goodness and nutrition
> goodness, together with only those additional conditions later approved as
> applicable to that synthesis, while preserving the two component meanings and
> their trace.

It cannot, by itself, indicate:

- an implicit arithmetic mean or any other unstated aggregation;
- personal health, safety, clinical risk or dietary suitability;
- that one domain compensates for or dominates the other;
- that a critical flag necessarily changes the result;
- completeness, coverage or confidence;
- regulatory compliance or release approval;
- a ranking across products assessed under different protocols or in
  non-comparable contexts.

Neither compensation nor non-compensation is presumed by the construct. The
ordinary aggregation family, guardrails and any critical effects remain open
decisions.

## F. Required qualitative properties

Every future policy claiming to measure this construct should demonstrate the
following non-numeric properties.

| Property | Required meaning | Failure to avoid |
|---|---|---|
| Construct clarity | The exact question, subject, intended use and forbidden interpretations are published. | A score whose meaning changes with the explanation given after calculation. |
| Transparency | Inputs, rule families, assumptions and limitations are inspectable. | A persuasive number with no auditable basis. |
| Versioning | Observable methodological change creates governed version identity and impact analysis. | Mutable “latest” semantics or silent historical reinterpretation. |
| Traceability | Product facts, sources, evidence judgments and WYE decisions remain traversable and attributable. | Treating source prestige or an AI summary as scientific authority. |
| Reproducibility | The same canonical inputs and governed protocol produce the same semantic result. | Locale-, order-, network-, time- or model-dependent variation. |
| Evidence/decision separation | Evidence facts and product-policy choices remain distinguishable. | Presenting a policy choice as though it were directly reported by a source. |
| Domain separation | Ingredient, nutrition and overall dimensions remain distinct and explainable. | Importing toxicological evidence into nutrition or nutrient profiling into ingredient risk. |
| No presumed compensation | The construct itself neither authorizes nor forbids compensation. | Hiding an aggregation choice inside the word “goodness”. |
| Explicit uncertainty | Material uncertainty and its effect on the exact conclusion are identified. | Converting uncertainty into product badness, safety or an undocumented score adjustment. |
| No inference beyond data | Missing quantity, exposure, serving, ingredient fact or nutrition value is not invented. | A complete-looking assessment created from unsupported assumptions. |
| Missing-data robustness | Missingness cannot silently improve or worsen goodness and must remain distinct from risk. | Zero, a neutral placeholder or a provisional score used for insufficient data. |
| Evaluability explainability | A `not_computable` result names the blocked requirement and remains distinct from a computed result. | Treating non-computability as technical failure, badness or score zero. |
| Communication restraint | User communication preserves protocol relativity and non-claims. | “Healthy”, “safe”, “good for you” or equivalent personal inference. |
| Validation fitness | Validation addresses the construct and intended use actually claimed. | Borrowing validation from a model developed for a different policy purpose. |

These properties are requirements for future policy design and review. They do
not define calculations, gates or acceptance thresholds.

## G. “Is / is not” matrix

| Topic | What the construct is | What it is not | Implication for future scoring | Communication risk to avoid |
|---|---|---|---|---|
| Product and label facts | A methodological assessment built from eligible governed facts. | A restatement of every label fact or an intrinsic product measurement. | Facts must remain traceable inputs, not self-scoring conclusions. | “The label proves the product is good.” |
| Compositional quality | A possible subject of ingredient-specific favourability under explicit WYE criteria. | Proof that every ingredient is safe, beneficial or necessary. | Ingredient criteria require separate scientific definition and validation. | “Good ingredients means safe for everyone.” |
| Nutrient profiling | A possible future method for the nutrition dimension when its intended use fits WYE. | A model selected or validated by this RFC, or the ingredient/overall construct. | `PSC-OD-007` through `PSC-OD-011` remain open. | Relabelling a marketing or claims model as universal product goodness. |
| Personal health | A general-population product assessment with explicit non-claims. | A statement about the user's current or future health. | No personal outcome may be encoded or inferred. | “This score says the product is healthy for you.” |
| Absolute healthiness | Protocol-relative favourability under declared criteria. | “Healthy” or “unhealthy” as an absolute property in every diet and context. | Scale endpoints require bounded protocol semantics. | Treating the top of a scale as perfect healthfulness. |
| Universal safety | Separate from food-safety and clinical-risk conclusions. | Proof of absence of hazards or harm at every dose and use. | Safety requires a distinct question, inputs and governance. | “A favourable score guarantees safety.” |
| Clinical risk | Explicitly outside the construct. | Likelihood or severity of harm for a population or individual under exposure. | Hazard, exposure and risk must remain separate. | Converting a hazard flag or low result into clinical risk. |
| Regulatory compliance | Regulatory facts may be relevant governed context. | A certificate of authorization, legality or claims compliance. | Regulatory ontology and legal interpretation remain separate. | “WYE goodness means legally compliant.” |
| Individual suitability | Excluded from the first-release construct. | Suitability for allergies, disease, pregnancy, medicines, minors or goals. | Requires a separate future policy and governance. | “Recommended for your condition.” |
| Evidence insufficiency | A limitation that may affect evaluability, coverage or confidence. | Negative evidence or inherent product badness. | Missing-data and evaluability policies must preserve non-computability. | “Unknown means dangerous” or “unknown means safe.” |
| Product not computable | A valid future methodological result when applicable conditions are unmet. | A numeric result, a neutral result or a zero result. | No substitute score may be emitted. | Showing a placeholder percentage for unavailable assessment. |
| Overall result | A future governed synthesis that preserves both component constructs. | An implicit mean, health probability or hidden dominance rule. | Aggregation requires its own approved policy. | Presenting one opaque number as the complete truth about the product. |

## H. Implications for decisions that remain open

This RFC records semantic constraints from `PSC-OD-002` only. It does not change
the state or answer of any decision below.

| Decisions | Conceptual implication of the decided construct | What remains undecided |
|---|---|---|
| `PSC-OD-003`–`PSC-OD-006` | The ingredient branch must measure declared-composition favourability without treating regulatory status, hazard, uncertainty or missingness as interchangeable. | Regulatory ontology, ingredient states, numeric mapping and product-level ingredient aggregation. |
| `PSC-OD-007`–`PSC-OD-011` | The nutrition branch must use a purpose-specific model compatible with general-population product assessment and preserve its category, basis and data assumptions. | Base model, category/preparation rules, sugar semantics, components and numeric mapping. |
| `PSC-OD-012` | Overall must preserve the distinct meanings and trace of ingredient and nutrition goodness. | Aggregation family, parameters and behavior. |
| `PSC-OD-013`–`PSC-OD-014` | Criticality remains a separately justified effect layer; hazard alone is not goodness, risk or an automatic score effect. | Flag-effect classes, any caps, severity, no-double-counting and zero overrides. |
| `PSC-OD-015`–`PSC-OD-017` | Coverage, evaluability and confidence support interpretation of the construct and cannot substitute for goodness. | Required inputs, coverage aggregation, computability conditions and confidence derivation. |
| `PSC-OD-018` | Numeric execution semantics can be specified only after measurement policies exist. | Precision, arithmetic, rounding, boundaries and serialization. |
| `PSC-OD-019` | Validation must test the declared construct, protocol purpose, robustness, comprehension and non-misleading interpretation. | Corpus, benchmarks, validation design and approval evidence. |
| `PSC-OD-020` | External language must make protocol relativity and non-claims understandable. | Final copy, bands, colors, accessibility, comprehension and legal review. |
| `PSC-OD-021` | Sources supporting criteria must be governed internally and kept distinct from WYE policy choices. | Register schema, hierarchy, cadence, cutoff and supersession procedure. |
| `PSC-OD-022` | Personalization cannot inherit the general product construct as a personal recommendation or clinical score. | Premium intended use, scientific boundary, privacy, legal and clinical governance. |

## I. Internal evidence note

### I.1 Use and evidence classification

The sources below support internal methodological reasoning only. They do not
create a bibliography requirement for the app and do not approve WYE.

Statements in this RFC use three evidence classes:

- `SOURCE FACT`: a proposition within the cited source's scope;
- `WYE INFERENCE`: a bounded implication drawn by WYE from one or more source
  facts and the existing project contracts;
- `WYE PROPOSAL`: a new construct or governance choice requiring approval;
- `WYE DECISION`: a WYE product or methodological boundary approved by its
  declared authority, with its limits and downstream gates preserved.

The common definition in section D is a `WYE DECISION` limited to the semantic
and product boundary. The dimension-specific semantics in section E preserve
that boundary but do not approve measurement methods. In particular, no
reviewed source establishes a standard “ingredient goodness” or WYE “overall
goodness” construct.

### I.2 Sources actually used

| ID | Authority or authors; year; source type | Verifiable locator | What it supports in this RFC | Transfer limitation and cutoff check |
|---|---|---|---|---|
| `SRC-WHO-NP-2011` | World Health Organization / IASO; 2011; official technical-meeting report | [WHO IRIS, ISBN 978-92-4-150220-7](https://iris.who.int/bitstream/handle/10665/336447/9789241502207-eng.pdf) | `SOURCE FACT`: nutrient profiling classifies foods by nutritional composition; a model must be distinguished from its policy application and purpose. Supports construct-before-method and purpose specificity. | Does not validate WYE, ingredient goodness or an overall product score. Publication predates cutoff; locator and ISBN verified by 2026-09-01. |
| `SRC-WHO-NP-2022` | WHO Regional Office for Europe; 2022; official expert-meeting report | [WHO/EURO:2022-6201-45966-66383](https://www.who.int/europe/publications/i/item/WHO-EURO-2022-6201-45966-66383) | `SOURCE FACT`: nutrient profile models have multiple policy applications and enable nutrition-composition classification and comparison. Supports explicit intended use. | An expert-meeting report does not select a WYE model or justify ingredient/overall goodness. Verified as published before cutoff. |
| `SRC-WHO-EURO-NPM-2023` | WHO Regional Office for Europe; 2023; official nutrient profile model | [WHO-EURO-2023-6894-46660-68492](https://www.who.int/europe/publications/i/item/WHO-EURO-2023-6894-46660-68492) | `SOURCE FACT`: the model is designed for policies restricting marketing of foods to children and uses defined scope and categories. Supports the rule that model validity and meaning are application-specific. | Population and marketing purpose differ from WYE Option A; its classifications and criteria cannot be transferred automatically. Verified before cutoff. |
| `SRC-EFSA-NP-2022` | EFSA NDA Panel; 2022; official scientific opinion | [DOI 10.2903/j.efsa.2022.7259](https://doi.org/10.2903/j.efsa.2022.7259) | `SOURCE FACT`: nutrient profiling is classification based on nutritional composition for specific purposes; relevant nutrients and food groups depend on public-health and design considerations. Supports keeping nutrition construct and application explicit. | Scientific advice for EU front-of-pack labelling and claims profiles, not a complete WYE model and not ingredient or overall scoring. Verified before cutoff. |
| `SRC-CODEX-LABEL-2024` | Codex Alimentarius Commission; current text modified 2024; official guideline `CXG 2-1985` | [Guidelines on Nutrition Labelling](https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXG%2B2-1985%252FCXG_002e.pdf) | `SOURCE FACT`: front-of-pack information is supplementary to the nutrient declaration and should align with relevant dietary guidance or policy. Supports separating declared facts from methodological interpretation. | Does not approve WYE wording, outputs or scoring and does not cover ingredient goodness. Current official text verified before cutoff. |
| `SRC-CODEX-RISK-2007` | FAO/WHO Codex Alimentarius Commission; 2007; official guideline `CXG 62-2007` | [Codex `CXG 62-2007` — primary official document](https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXG%2B62-2007%252FCXG_062e.pdf) | `SOURCE FACT`: food-safety risk analysis separates scientific risk assessment, risk management and risk communication; risk concerns hazards and likelihood of harm. Supports excluding clinical risk and universal safety from goodness. | Government food-safety framework, not a product-favourability scoring method. Verified as an active official Codex reference before cutoff. |
| `SRC-EFSA-UNCERTAINTY-2018` | EFSA Scientific Committee; 2018; official guidance | [DOI 10.2903/j.efsa.2018.5123](https://doi.org/10.2903/j.efsa.2018.5123) | `SOURCE FACT`: scientific assessments should identify uncertainty and characterize its implications for conclusions. Supports explicit uncertainty and bounded communication. | Does not prescribe WYE confidence, coverage or evaluability rules. Verified before cutoff. |
| `SRC-LABONTE-NPM-2018` | Labonté et al.; 2018; peer-reviewed systematic review | [PMID 30462178; DOI 10.1093/advances/nmy045](https://pubmed.ncbi.nlm.nih.gov/30462178/) | `SOURCE FACT`: government-led nutrient profile models vary by policy application, and validation information was absent for many identified models. Supports model-purpose matching and independent validation. | Evidence inventory was bounded by the review's search period and does not validate WYE. Published before cutoff. |
| `SRC-COOPER-VALIDATION-2016` | Cooper, Pelly and Lowe; 2016; peer-reviewed systematic review | [PMID 26850312; DOI 10.1016/j.appet.2016.02.001](https://pubmed.ncbi.nlm.nih.gov/26850312/) | `SOURCE FACT`: construct and criterion validity evidence for nutrient profiling showed methodological limitations and variable evidential quality. Supports an explicit construct-validation gate. | Review concerns nutrition profiling, not ingredient or WYE overall goodness; evidence searched through its stated historical boundary. Published before cutoff. |
| `SRC-WHO-HEALTHY-DIET-2026` | World Health Organization; 2026; official public-health fact sheet | [WHO Healthy diet, 26 January 2026](https://www.who.int/news-room/fact-sheets/detail/healthy-diet) | `SOURCE FACT`: healthy diets concern adequacy, balance, moderation and diversity, and their exact composition varies with individual and contextual factors. Supports the non-claim that one packaged-product assessment is not a person's total diet or health state. | A fact sheet is not a nutrient profiling model or WYE validation source. Published and verified before the 2026-09-01 cutoff. |
| `SRC-EU-CLAIMS-2006` | European Parliament and Council; 2006, consolidated official legal text; Regulation (EC) No 1924/2006 | [EUR-Lex CELEX 32006R1924](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006R1924) | `SOURCE FACT`: nutrition and health claims are governed legal communication categories and food information must not mislead or attribute medicinal properties. Supports keeping goodness separate from legal claims and compliance. | Legal source does not provide scientific validation or authorize WYE external wording; consolidated status and future legal applicability require legal review. Verified before cutoff. |

### I.3 Bounded inference from the sources

The sources jointly support these limited `WYE INFERENCE` statements:

1. A food-profile output needs an explicit construct and policy purpose before
   any model can be selected or validated.
2. A model developed for one population, jurisdiction or policy application
   cannot be renamed WYE goodness without transfer justification.
3. Declared nutrition information, nutrient profiling, food-safety risk and
   health claims are related but non-equivalent concepts.
4. A product-level methodological assessment cannot stand in for a person's
   total diet, exposure, health status or clinical outcome.
5. Uncertainty, missing data and non-computability must remain visible rather
   than being hidden inside apparent goodness.

The sources do not establish external scientific validation of the decided WYE
construct. That status requires the future review and validation described in
this RFC.

## J. Decision record

| Field | Recorded decision |
|---|---|
| Decision ID | `PSC-OD-002` |
| Current status | `DECIDED` |
| Decided methodological option | Alternative B — transparent, versioned compositional and nutritional favourability under declared and applicable WYE criteria for the first-release adult general-population intended use |
| Approval status | `DECIDED — PRODUCT OWNER APPROVED` |
| Decision owner | Product owner |
| Decision date | `2026-09-01` |
| Authority source | Explicit product-owner approval |
| Decision scope | Semantic and product boundary of the construct |
| Scientific status | Internal evidence-informed methodology; no external scientific validation performed |
| Legal/regulatory status | No legal or regulatory approval implied |
| Implementation status | No formulas, scales or runtime approved |
| Independent review | `Fase 7.10.3`; `READY_FOR_PRODUCT_OWNER_DECISION`; no `BLOCKER` or `MAJOR` |
| Review finding disposition | `GCR-REV-001` (`MINOR`) resolved by replacing the indirect FAO reference page with the primary official Codex `CXG 62-2007` document locator |
| Future validation contributors | Nutrition-science reviewer; food-toxicology or ingredient-evidence reviewer; public-health reviewer; regulatory/legal reviewer for boundary and claims; product communication reviewer; validation owner; data/model steward |
| Not authorized by this decision | Scientific certification; clinical interpretation; legal/regulatory compliance; ingredient or nutrition method validity; formula; release; publication; runtime |
| QPS effect | None; the candidate and its approval gate remain separate |

### J.1 Basis recorded for the `DECIDED` state

`PSC-OD-002` moved to `DECIDED` on explicit product-owner authority for the
semantic and product boundary because all of the following are recorded:

- one exact construct wording and its non-claims are selected;
- the product owner confirms product value and perimeter without claiming
  scientific authority;
- Alternative B is selected after preserving the reviewed alternatives and
  internal evidence note;
- the independent review found no `BLOCKER` or `MAJOR`, and its sole `MINOR`
  locator finding `GCR-REV-001` is resolved;
- ingredient, nutrition and overall remain distinct, and `not_computable`
  remains a non-numeric result;
- authority limits and all downstream scientific, validation, communication,
  legal/regulatory and implementation gates are explicit;
- the evidence cutoff remains `2026-09-01`.

### J.2 Gates that remain after the decision

After `PSC-OD-002` is decided, the following remain necessary:

- all applicable `PSC-OD-003` through `PSC-OD-022` decisions;
- selection and validation of ingredient and nutrition methods;
- overall, criticality, missing-data, evaluability and confidence policies;
- independent corpus, robustness and comprehension validation;
- scientific, communication and legal/regulatory review of external claims;
- a separately governed product-scoring candidate, version and digest;
- publication and release approval;
- runtime and persistence authorization through later technical work.

## Exit state

```text
PSC-OD-002: DECIDED — OPTION B — PRODUCT OWNER APPROVED
approved scope: SEMANTIC AND PRODUCT BOUNDARY ONLY
scientific status: INTERNAL EVIDENCE-INFORMED METHODOLOGY; NO EXTERNAL VALIDATION PERFORMED
product-owner product-boundary decision: RECORDED — 2026-09-01
legal/regulatory review of external wording: REQUIRED
product scoring formula: NOT PRESENT
product scoring candidate: NOT PRESENT
numeric runtime authority: NONE
QPS candidate impact: NONE
next gate: REVIEW OF THE PSC-OD-002 DECISION
```
