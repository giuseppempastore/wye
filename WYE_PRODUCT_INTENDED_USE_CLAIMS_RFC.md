# WYE — Product Intended Use and Claims RFC

## Document status

```text
PSC-OD-001 DECIDED — PRODUCT OWNER APPROVED
EXTERNAL WORDING — LEGAL/REGULATORY REVIEW REQUIRED
```

```text
decision_id: PSC-OD-001
decision_status: DECIDED
document_kind: product decision record
decision_owner: Product owner
decision_date: 2026-09-01
source_of_authority: Explicit product-owner approval
approved_option: Option A
approval_scope: intended use and claims boundary for PSC-OD-001 only
runtime authority: none
```

This record documents the product owner's explicit approval of Option A for the
first release of the WYE food-product tri-score and changes `PSC-OD-001` from
`OPEN` to `DECIDED`. It does not approve a scientific or clinical method, grant
legal or regulatory approval, publish a scoring policy or authorize
user-facing release.

The proposed claims and wording in this RFC require scientific, product,
communication and legal/regulatory review before external use. Where legal or
regulatory interpretation is material, the status is explicitly:

```text
REQUIRES LEGAL/REGULATORY REVIEW
```

## Basis and authority boundary

This decision record is bounded by the repository's current contracts and
governance:

- `WYE_PRODUCT_SCORING_CONTRACT.md` defines the draft food tri-score boundary,
  non-claims, evaluability semantics and the 22 governed decisions, of which
  `PSC-OD-001` is now `DECIDED` and 21 remain `OPEN`;
- `Checkpoints/WYE_PHASE_7.md` separates scientific evidence from scoring,
  requires reviewed intended use and claims, and defines the RFC lifecycle;
- `WYE_SCORING_SEMANTICS.md` separates evidence, hazard, exposure, risk,
  confidence and product assessment;
- `WYE_SCORING_PROTOCOL.md` requires every future protocol to publish its exact
  intended use, population, claims, completeness and communication contract;
- `WYE_PRODUCT_ASSESSMENT.md` treats non-computability as a valid epistemic
  result and separates generic from user-specific assessment;
- `WYE_EVIDENCE_SELECTION.md` defines selection as distinct from synthesis,
  product judgment and scoring;
- the QPS candidate, golden corpus, review package, delivery package and
  external approval gate remain separate controlled artifacts;
- `README.md` and `scope/project_documentation.md` describe legacy/MVP product
  ambitions but do not override the Phase 7 scientific contracts.

This RFC introduces no scientific source and makes no claim of legal or
regulatory compliance.

## A. Decisione registrata

`PSC-OD-001` resolves the following coherent decision bundle for the first WYE
product-scoring release:

| Decision dimension | Recorded decision | Boundary of this record |
|---|---|---|
| Initial population | Adults in the general population. | Do not extend the decision to clinical or vulnerable subgroups. |
| Intended users | Ordinary adult consumers consulting packaged foods and beverages without a clinical profile in WYE. | Professional, clinical and personalized uses are excluded. |
| Intended use | General informational interpretation of a packaged food or beverage under versioned WYE methodology. | No personal, clinical, therapeutic or dietary-prescriptive assessment. |
| Allowed claims | Scoped, traceable and non-clinical statements about label facts, WYE method outputs and limitations. | External wording still requires the applicable scientific, communication and legal/regulatory reviews. |
| Forbidden claims | Diagnosis, treatment, individual safety or suitability, recommended intake and universal health or safety conclusions. | A disclaimer cannot authorize an otherwise forbidden claim. |
| UI formulations | Candidate phrases that distinguish facts, WYE assessments and unavailable results. | Exact final wording remains governed by `PSC-OD-020` and release review. |
| Product/clinical boundary | Food information and methodological judgment remain separate from personal or professional advice. | No clinical, therapeutic, dietary-prescriptive or personalized use. |

The decision must distinguish:

```text
food information
!= WYE methodological assessment
!= clinical or personal advice
```

The product owner's explicit approval recorded on `2026-09-01` selects Option A
and changes only `PSC-OD-001` from `OPEN` to `DECIDED`. The approval has no
scientific, clinical, legal/regulatory, formula, runtime or release authority.

## B. Fatti, inferenze e limiti

### B.1 Three levels of statement

| Level | What belongs here | Examples | Required communication boundary |
|---|---|---|---|
| 1. Verifiable product or label facts | Data directly present on, or canonically attributed to, the identified product with provenance. | Declared ingredients; available nutrition values and basis; allergens declared on the label; product identity; data source and version; extraction or verification status. | State source, product identity, basis and limitations. Do not silently turn a declared fact into a health conclusion. |
| 2. WYE methodological assessments | Outputs produced by a future published and validated WYE protocol. | `evaluability_status` (`computable` or `not_computable`); `ingredient_goodness_percent`; `nutrition_goodness_percent`; `overall_goodness_percent`; coverage; confidence; critical flags; limitations; missing inputs. | Label the result as a WYE assessment, identify the scoring version and keep confidence, coverage and criticality separate from goodness. |
| 3. Conclusions WYE cannot draw under this RFC | Clinical, therapeutic, personal-suitability or universal-safety conclusions not supported by the general product contract. | Clinical efficacy; individual safety; suitability for a disease; recommended dose or portion; treatment effect; substitution of a physician, dietitian or nutritionist. | Do not display or imply these conclusions. Route future personal use through separate policy and governance. |

`evaluability_status` is a methodological conclusion produced by the versioned
WYE policy from the available inputs and applicable computability conditions. It
is not an intrinsic fact of the product or data declared on its label;
`not_computable` is one possible state of that WYE methodological assessment.

### B.2 Proposed epistemic rule

WYE may offer an informative, methodological assessment of an identified food
product. WYE cannot guarantee that a food is “sano” or “salutare” for every
person, in every quantity and in every context.

Strong assertions may concern only what can be demonstrated, for example:

- the exact product and label data used;
- the provenance, version and cutoff of governed inputs;
- whether the assessment is `computable` or `not_computable`;
- which limitations and missing inputs were recorded;
- whether the same canonical inputs and published rules were applied
  consistently;
- which WYE rule and scoring version produced a methodological result.

Those assertions do not establish an absolute clinical benefit, absence of
harm, suitability for an individual or scientific certainty about every use.

### B.3 Fact-versus-assessment language

Future communication should use explicit attribution:

| Statement type | Preferred construction | Construction to avoid |
|---|---|---|
| Label fact | “L'etichetta dichiara…” | “WYE certifica che il prodotto contiene soltanto…” |
| Canonical product data | “Dati del prodotto utilizzati per questa valutazione…” | “Composizione reale garantita per ogni lotto…” |
| Methodological output | “Valutazione WYE… secondo la versione indicata” | “Verità scientifica sul prodotto…” |
| Missingness | “Dati insufficienti per una valutazione completa” | “In assenza di dati il prodotto è sicuro/pericoloso” |
| Confidence | “Affidabilità della conclusione WYE: …” | “Probabilità che il prodotto sia sicuro: …” |
| Critical flag | “Segnalazione da interpretare nel contesto indicato” | “La presenza del flag dimostra rischio clinico” |

## C. Opzioni decisionali

### C.1 Comparison

| Criterion | Option A — Product owner approved | Option B — Broader/sensitive population | Option C — Professional or semi-professional orientation |
|---|---|---|---|
| Population | Adults in the general population. | General population plus people with sensitive or specific needs. | Nutrition, food-quality or other professionals and trained operators. |
| Intended users | Adult consumers consulting packaged foods and beverages without a clinical profile or personalization. | Consumers who may expect relevance to allergies, pregnancy, disease, medicines, minors or other individual conditions. | Users expected to understand methodological detail, evidence boundaries and traceability. |
| User value | A clear, general and versioned product assessment with explicit limitations. | Potentially more personally relevant interpretation. | Richer scrutiny, audit and decision support within professional workflows. |
| Possible claims | General WYE ingredient, nutrition and overall assessments; coverage, confidence, flags and limitations; `not_computable`. | General claims plus condition- or subgroup-aware language, only if separately justified. | Methodological and trace-oriented statements; no automatic clinical conclusion. |
| Main risks | Users may still overread “goodness” as personal health advice; communication testing remains necessary. | High risk of implied individual suitability, clinical advice, allergen safety or vulnerable-population assurance. | Risk of appearing to validate professional or clinical decisions without an approved professional-use protocol. |
| Product/governance complexity | Lowest of the three options; still requires claims, scientific, legal/regulatory and communication review. | High: separate population, allergy, clinical, privacy and validation governance. | Medium to high: role definition, training assumptions, professional claims and workflow governance. |
| Product Scoring Contract compatibility | Directly compatible with the user-independent food tri-score boundary. | Not compatible as a first-release extension without separate policies and data. | Potentially compatible only as a distinct professional intended-use profile and communication contract. |
| Decision outcome | **DECIDED — PRODUCT OWNER APPROVED.** | **NOT SELECTED for the first release.** Reconsider only through separate governed work. | **NOT SELECTED.** Defer until a separate use case and claims package exist. |

### C.2 Option A — Product owner approved

Option A offers a general informational assessment to adults consulting foods
and beverages within the Product Scoring Contract. It does not use a health
profile, infer actual intake or claim personal suitability.

This option was recommended because it keeps the intended use aligned with
the available product-level data and with the current separation between a
general product assessment and a future personalized assessment.

### C.3 Option B — Broader or sensitive population

Option B includes people whose interpretation may depend on age, pregnancy,
allergies, disease, medicines, dietary restrictions or other individual
conditions. These contexts require distinct scientific questions, input
contracts, privacy governance and claims. They cannot be inferred from a
general product score.

Option B is not recommended for the first release.

### C.4 Option C — Professional or semi-professional orientation

Option C could prioritize traceability and methodological detail for trained
users. Professional orientation nevertheless changes foreseeable reliance,
claim expectations, validation and governance. The current tri-score contract
does not authorize clinical or professional decision support.

Option C is deferred with reservation pending a separate intended-use proposal.

The comparison is retained as decision history. Approval derives only from the
explicit product-owner decision recorded in sections D and I.

## D. Decisione approvata dal product owner

### D.1 Recorded first-release decision

On `2026-09-01`, the product owner explicitly approved Option A and authorized
the following decision:

> Per la prima release, WYE è uno strumento informativo generale rivolto ad
> adulti della popolazione generale per consultare alimenti e bevande
> confezionati. Non fornisce valutazioni personali, cliniche, terapeutiche o
> dietetiche; non considera condizioni individuali; non fornisce dosi, porzioni,
> frequenze o raccomandazioni personali.

The recorded decision includes these mandatory boundaries:

- adults in the general population;
- packaged foods and beverages within the Product Scoring Contract domain;
- scores that are informative, methodological and versioned rather than
  personal or clinical conclusions;
- no personalization or user health profile;
- no recommended dose, portion or consumption frequency;
- no personal, professional, therapeutic, clinical or dietary-prescriptive
  assessment or advice;
- no suitability assessment for disease, allergy, pregnancy, minors,
  medication use or other individual conditions;
- specifically regulated supplements and non-food domains require a separate
  policy and are outside the supported use;
- numeric scores only when `evaluability_status = computable`;
- `not_computable` as a valid result, not an error and not score zero;
- label facts, WYE assessments and forbidden personal conclusions shown as
  distinct classes of statement;
- external wording remains subject to scientific, communication and
  `REQUIRES LEGAL/REGULATORY REVIEW` gates;
- no bibliography is mandatory in the ordinary UI;
- premium and personalization remain deferred to a separate future Wave.

### D.2 Rationale

- **Clarity:** one narrow audience and purpose reduce ambiguity about what the
  scores mean.
- **User safety:** the selected option avoids suggesting personal suitability or
  clinical benefit from a general product assessment.
- **Methodological consistency:** it matches the food-only, user-independent and
  evaluability-aware Product Scoring Contract.
- **Feasibility:** it does not require clinical profiles, actual-intake data,
  vulnerable-population models or premium personalization.
- **Governance:** it leaves scientific validation, claims review, final UI
  communication and publication as explicit later gates.

This is an approved product-owner decision for `PSC-OD-001`, not scientific,
clinical, legal/regulatory or scoring-formula approval. All external wording
remains `REQUIRES LEGAL/REGULATORY REVIEW`.

## E. Claims taxonomy

The examples below are candidate Italian wording for later review. They do not
authorize current UI use.

| Category | Candidate Italian statement | Conditions or rationale | Review gate |
|---|---|---|---|
| `ALLOWED` | “Ingredienti dichiarati in etichetta: …” | Verifiable label fact; retain product and label provenance. | Product/data QA |
| `ALLOWED` | “Valori nutrizionali dichiarati per la base indicata: …” | Report the exact declared basis and preparation state. | Product/data QA |
| `ALLOWED` | “Stato della valutazione: non computabile.” | Valid methodological state; do not show a numeric placeholder. | Communication review |
| `ALLOWED` | “Dati mancanti per questa valutazione: …” | Name missing inputs without inferring safety or danger. | Communication review |
| `ALLOWED WITH QUALIFIER` | “Valutazione WYE degli ingredienti, basata sui dati disponibili.” | Show scoring version, coverage, confidence and limitations. | Scientific + communication + `REQUIRES LEGAL/REGULATORY REVIEW` |
| `ALLOWED WITH QUALIFIER` | “Valutazione WYE del profilo nutrizionale, quando computabile.” | Identify category/basis and do not imply total-diet or clinical assessment. | Scientific + communication + `REQUIRES LEGAL/REGULATORY REVIEW` |
| `ALLOWED WITH QUALIFIER` | “Punteggio informativo del prodotto: non è un parere medico.” | Use only for a `computable` result and with the complete disclaimer. | Scientific + communication + `REQUIRES LEGAL/REGULATORY REVIEW` |
| `ALLOWED WITH QUALIFIER` | “Dati insufficienti per una valutazione completa.” | Accompany with missing inputs and limitations; do not show zero. | Communication review |
| `ALLOWED WITH QUALIFIER` | “La valutazione non considera le tue condizioni personali.” | Required boundary for the recommended general assessment. | Communication + `REQUIRES LEGAL/REGULATORY REVIEW` |
| `ALLOWED WITH QUALIFIER` | “Segnalazione informativa relativa a un potenziale hazard nel contesto indicato.” | Preserve endpoint/context; do not imply exposure, risk or automatic score effect. | Scientific + communication review |
| `FORBIDDEN` | “Questo prodotto è sano/salutare per te.” | Implies personal and context-independent health suitability. | Prohibited under this intended use |
| `FORBIDDEN` | “Questo prodotto previene, cura o migliora una condizione.” | Therapeutic or clinical efficacy claim. | Prohibited; `REQUIRES LEGAL/REGULATORY REVIEW` if ever proposed elsewhere |
| `FORBIDDEN` | “È adatto alla tua patologia.” | Requires individual clinical suitability assessment. | Prohibited under this intended use |
| `FORBIDDEN` | “Puoi mangiarne questa dose.” | Converts a general product assessment into intake advice. | Prohibited under this intended use |
| `FORBIDDEN` | “WYE sostituisce medico, dietista o nutrizionista.” | Misrepresents the product's role. | Prohibited |
| `FORBIDDEN` | “È sicuro per chiunque.” | Universal safety cannot be established by the tri-score. | Prohibited |
| `FORBIDDEN` | “Il punteggio 100 garantisce salubrità assoluta.” | Misstates a protocol endpoint as absolute health certainty. | Prohibited |
| `FORBIDDEN` | “Il punteggio 0 dimostra pericolosità clinica.” | Misstates a computed lower endpoint as a clinical conclusion. | Prohibited |
| `FORBIDDEN` | “Nessun dato significa nessun rischio.” | Converts missing evidence into safety. | Prohibited |
| `DEFERRED TO PREMIUM / FUTURE WAVE` | “Valutazione personalizzata in base al tuo profilo sanitario.” | Requires separate intended use, policy, validation and privacy governance. | `PSC-OD-022` plus scientific and legal/privacy review |
| `DEFERRED TO PREMIUM / FUTURE WAVE` | “Porzione consigliata per te.” | Requires personal exposure/diet context and appropriate professional governance. | Separate future policy; `REQUIRES LEGAL/REGULATORY REVIEW` |
| `DEFERRED TO PREMIUM / FUTURE WAVE` | “Compatibile con i tuoi obiettivi e le tue restrizioni.” | Personal recommendation is outside the general score. | Separate future policy |
| `REQUIRES SEPARATE POLICY` | “Adatto in gravidanza” or “adatto ai minori”. | Population-specific suitability cannot be inherited from the general population. | Scientific + clinical + `REQUIRES LEGAL/REGULATORY REVIEW` |
| `REQUIRES SEPARATE POLICY` | “Adatto a chi assume il farmaco …” | Requires interaction and individual-context assessment. | Scientific + clinical + `REQUIRES LEGAL/REGULATORY REVIEW` |
| `REQUIRES SEPARATE POLICY` | “Sicuro per la tua allergia.” | Declared allergen facts are distinct from individual allergy safety. | Allergy/clinical policy + `REQUIRES LEGAL/REGULATORY REVIEW` |
| `REQUIRES SEPARATE POLICY` | Claims for cosmetics, medicines, feed or specifically regulated supplements. | These domains are outside the current food tri-score contract. | Separate domain contract and review |

The ordinary UI is not required to display a bibliography. Source identity,
version, cutoff, provenance and rule trace remain mandatory internal governance
and audit capabilities.

## F. Contratto user-facing proposto

This section proposes textual semantics, not layout, API fields, schema or
runtime behavior.

### F.1 Computable result

When `evaluability_status = computable`, the future interface may present all
three scores, always attributed to WYE and to the applicable scoring version:

- `ingredient_goodness_percent`: “Valutazione WYE degli ingredienti: NN%”;
- `nutrition_goodness_percent`: “Valutazione WYE del profilo nutrizionale:
  NN%”;
- `overall_goodness_percent`: “Valutazione complessiva WYE del prodotto: NN%”.

The three values must remain visibly different constructs. The overall result
must not be described as clinical health, personal suitability or proof of
safety.

The result must also communicate:

- coverage as the extent of policy-required inputs that were available and
  usable, not as product goodness;
- confidence as confidence in the exact WYE conclusion, not probability of
  safety;
- critical flags as separately named and contextualized notices, without
  implying an automatic numerical effect unless a future published policy says
  so;
- limitations as boundaries on interpretation;
- missing data as named absences, never favourable or adverse evidence;
- the scoring version as the identity of the applied published methodology.

### F.2 Non-computable result

When `evaluability_status = not_computable`:

- show “Valutazione non disponibile con i dati utilizzabili”;
- show coverage, confidence in the non-computability conclusion where defined,
  missing inputs and limitations separately;
- show no ingredient, nutrition or overall numeric score;
- use no zero, neutral value, placeholder percentage or inferred estimate;
- do not describe the result as an application or database error merely because
  the valid semantic outcome is non-computable.

### F.3 Score zero versus unavailable

```text
score 0
= computed protocol endpoint
!= missing score
!= not_computable
!= automatic clinical danger
```

```text
not_computable
= no complete numeric assessment under the applicable policy
!= score 0
!= evidence of safety or danger
```

### F.4 Proposed disclaimers

For every displayed numeric tri-score, show a disclaimer equivalent to:

> Valutazione WYE generale, informativa e versionata del prodotto, basata sui
> dati utilizzabili. Non è una diagnosi, una prescrizione, un consiglio medico o
> una raccomandazione personale.

For a non-computable result, show a disclaimer equivalent to:

> La valutazione numerica WYE non è disponibile con i dati utilizzabili. Non
> equivale a un punteggio zero e non indica che il prodotto sia sicuro o
> pericoloso per te.

The disclaimer must be present whenever a score, interpretation, critical flag
or non-computability message could otherwise be read as a personal health
conclusion. Exact final wording, comprehension testing and release approval
remain governed by `PSC-OD-020` and are not decided here.

### F.5 When no score is shown

No numeric score is shown when:

- the result is `not_computable`;
- no published and approved product-scoring policy applies;
- the identified product is outside the food tri-score domain;
- an indispensable component is non-computable and no future approved policy
  defines a different treatment;
- execution or product identity cannot produce a valid canonical result.

The exact computability gates remain governed by `PSC-OD-015`, `PSC-OD-016` and
`PSC-OD-017`; this RFC introduces no completeness, coverage or confidence
threshold.

## G. Premium e personalizzazione

The recorded approval of Option A does not enable:

- a health or clinical profile;
- collection or interpretation of clinical data;
- sensitive dietary preferences or restrictions as scoring inputs;
- a recommended dose, portion or consumption frequency;
- personal medical, dietary or therapeutic recommendations;
- a personalized score;
- allergy, disease, pregnancy, minor or medicine-specific suitability.

A future premium Wave would require, at minimum:

- a separate intended use, target population and claims decision;
- a separate scientific protocol for every personalized construct;
- evidence, exposure and validation requirements appropriate to each claim;
- clinical and professional governance where the claim requires it;
- legal, regulatory and privacy review;
- explicit purpose and legal basis, consent where required, data minimization,
  access control, security, retention/deletion and audit;
- a DPIA determination and documented risk controls;
- communication and comprehension validation;
- separation of the personalized result from the immutable general product
  assessment.

These are decision gates, not a premium design. This RFC creates no premium
schema, workflow, feature or implementation.

## H. Decisione chiusa e questioni che restano aperte

### H.1 What `PSC-OD-001` closes

The product-owner decision recorded on `2026-09-01` freezes:

- the first-release population and intended users;
- the first-release informational purpose;
- the boundary between label facts, WYE assessments and clinical advice;
- the allowed, qualified, forbidden and deferred claim classes;
- the required non-personal and non-clinical disclaimers;
- the approved option and its explicit non-claims.

Only `PSC-OD-001` is closed by this record. Exact user-facing wording, legal and
regulatory review, scientific validation, communication approval and release
authorization remain separate gates.

### H.2 Decisions that remain separate

The recorded decision for `PSC-OD-001` does not decide:

- the scientific construct and numerical meaning of goodness (`PSC-OD-002`);
- ingredient state, mapping and aggregation rules (`PSC-OD-003` through
  `PSC-OD-006`);
- nutrition construct, categories, components and mapping (`PSC-OD-007`
  through `PSC-OD-011`);
- overall aggregation, critical effects or override rules (`PSC-OD-012`
  through `PSC-OD-014`);
- coverage, evaluability, missing-data and confidence policies (`PSC-OD-015`
  through `PSC-OD-017`);
- precision, validation corpus and impact analysis (`PSC-OD-018` and
  `PSC-OD-019`);
- final UI language, bands, colors, accessibility and comprehension approval
  (`PSC-OD-020`);
- source-governance mechanics (`PSC-OD-021`);
- premium and personalized-assessment boundaries (`PSC-OD-022`).

No formula, weight, threshold, cap, floor, ranking or rule for an individual
ingredient is selected by this RFC.

### H.3 QPS boundary

The candidate `efsa_qps_evidence_selection/1.0.0-candidate.1` remains a separate
finding-level evidence-selection candidate. This RFC does not modify or approve
its bytes, golden corpus, review package, delivery package, claims or approval
record. The gate remains:

```text
EXTERNAL SCIENTIFIC APPROVAL REQUIRED
```

QPS evidence does not become a general product-health claim through this RFC.

## I. Decision record

| Field | Recorded decision |
|---|---|
| ID | `PSC-OD-001` |
| Current status | `DECIDED` |
| Decided option | Option A — adults in the general population consulting packaged foods and beverages, with a general, non-personalized informational assessment |
| Decision owner | `Product owner` |
| Decision date | `2026-09-01` |
| Source of authority | `Explicit product-owner approval` |
| Authority limits | No scientific, clinical, legal/regulatory, scoring-formula, runtime or release approval |
| Review history | `Fase 7.9.2` review found `RFC-REV-001`; `Fase 7.9.2A` corrected it; repeated `Fase 7.9.2` review returned `READY_FOR_PRODUCT_OWNER_DECISION` |
| Remaining reviews/gates | Scientific review of construct-compatible claims; product communication/QA review; `REQUIRES LEGAL/REGULATORY REVIEW`; later release approval under the applicable publication lifecycle |
| Future documentary impacts | Governed intended-use/claims artifact; Product Scoring Contract decision state synchronized by this record; future protocol declaration; claims/non-claims package; communication package under `PSC-OD-020`; validation and publication records |
| Direct Product Scoring Contract change | `PSC-OD-001` state and decision record only |
| QPS candidate or approval-gate impact | None |

### I.1 Closure evidence and remaining gates

The explicit product-owner approval supplies the authority for the product
decision recorded here. The reviewed RFC identifies the option, population,
intended users, intended use, domain, claims boundary and non-claims. It changes
no scientific construct, numerical rule or other `PSC-OD` decision.

Scientific validation, legal/regulatory review of external wording, final
communication approval under `PSC-OD-020`, publication and release remain
required and are not implied by `DECIDED`.

```text
PSC-OD-001: DECIDED
decided option: OPTION A — PRODUCT OWNER APPROVED
scientific approval: NOT GRANTED
clinical approval: NOT GRANTED
legal/regulatory approval: NOT GRANTED
legal/regulatory review of external wording: REQUIRED
user-facing release authority: NOT GRANTED
```
