DECIDED — PRODUCT OWNER APPROVED

# WYE — Category Coexistence and Precedence RFC

## Document status and authority

```text
decision_id: PSC-OD-004
decision_status: DECIDED — PRODUCT OWNER APPROVED
document_kind: methodological decision record
decision_owner: Product owner
decision_date: 2026-09-01
authority_source: Explicit product-owner approval
decision: Option B
source_cutoff: 2026-09-01
scientific_approval: NOT PRESENT
clinical_approval: NOT PRESENT
legal_or_regulatory_approval: NOT PRESENT
runtime_authority: NONE
ai_approval_authority: NONE
```

This RFC records the product owner's explicit approval of Option B as the
conceptual policy for coexistence, contextual precedence and conflict among
categories in the WYE regulatory ontology. It closes only `PSC-OD-004` and
authorizes no classification or implementation.

The decided boundary depends on four bounded decisions already recorded by WYE:

- `PSC-OD-001`: first-release intended use and claims boundary;
- `PSC-OD-002`: protocol-relative goodness construct;
- `PSC-OD-003`: domain-scoped, layered and source-backed regulatory ontology;
- `PSC-OD-021`: domain-scoped source governance, immutable acquired artifacts
  and provenance linked to WYE decisions.

The product owner may decide the product vocabulary and conceptual governance
boundary. Product authority cannot establish a legal classification, a
scientific conclusion, a source's authority outside its scope or an operational
rule. Regulatory, legal, scientific, data/model, validation and release reviews
remain separate gates.

AI may assist comparison, drafting and consistency checks. AI cannot assign a
category autonomously, choose contextual precedence, resolve a conflict or
interpret legal applicability. AI supplied no approval authority for this
decision.

The candidate `efsa_qps_evidence_selection/1.0.0-candidate.1`, its golden
corpus, delivery package, publication state and approval gate remain separate
and unchanged. Sources remain internal provenance; this RFC creates no
user-facing bibliography requirement.

## A. Decision and perimeter

### A.1 Decision question

`PSC-OD-004` must decide:

> How should WYE preserve multiple source-backed category assertions for the
> same entity or label context, identify which assertion is relevant to a
> bounded question, and represent genuine conflicts without creating a
> universal primary category or an automatic scoring consequence?

The decision concerns non-numeric category-state interpretation only. It does
not determine whether a specific product, ingredient, substance or use is
legally classified, authorized, safe, harmful or favourable.

### A.2 Proposed scope

The candidate policy covers:

- coexistence of category assertions about the same canonical entity or label
  context;
- preservation of assertion kind, subject, source, jurisdiction, date,
  product/category, conditions and review disposition;
- contextual relevance or precedence for one explicitly recorded question;
- distinction between compatible coexistence, ambiguity and genuine conflict;
- retention of all secondary assertions and reasons when one assertion is more
  relevant to a bounded view;
- escalation and review boundaries;
- provenance from source artifacts and ontology assertions to the later WYE
  decision that uses them.

### A.3 Definitions used by this RFC

| Term | Conceptual meaning | Boundary |
|---|---|---|
| Category assignment | A source-backed assertion that a subject has a regulatory or methodological role in a stated context. | It is not precedence, authorization, safety, risk or score relevance. |
| Coexistence | Two or more assertions can simultaneously remain valid because they address compatible roles, assertion kinds or scopes. | It does not mean that the assertions are interchangeable. |
| Contextual precedence | For one recorded question, one applicable assertion may be more directly relevant than another. | It is not a global rank, destructive override or intrinsic primary category. |
| Ambiguity | Available information supports more than one plausible identity, scope or category interpretation. | It is not permission to choose the most convenient result. |
| Conflict | Applicable assertions addressing the same bounded proposition are materially incompatible. | Different questions or scopes are not automatically conflicts. |
| Primary-category projection | A future view may present one contextually preferred category while retaining every underlying assertion. | It is not canonical truth and is not approved by this RFC as a runtime output. |

## B. Problem to solve

The ontology decided under `PSC-OD-003` deliberately permits categories to
coexist. This is necessary because food information, regulatory instruments and
scientific assessments describe different aspects of an entity:

- a label entry may be both a `declared_ingredient` assertion and, under the
  applicable function and conditions, a `food_additive` assertion;
- a substance may be an `added_nutrient` and participate in a broader
  `fortified_substance` context;
- an entity may be a declared ingredient and also have a source-backed
  `allergen_or_intolerance_substance` relationship;
- a category can answer a regulatory question without having any approved WYE
  scoring relevance;
- a contaminant or residue context is not ingredient use, while a hazard record
  is not exposure and neither is a risk characterization;
- label absence does not establish absence from the product, and label presence
  does not establish quantity or exposure.

Without a bounded coexistence and precedence policy, future consumers of the
ontology could silently select the first category, overwrite secondary roles,
confuse source recency with authority, treat ambiguity as conflict or promote a
regulatory category into an unsupported score effect or claim.

The policy must therefore answer a question such as “which assertion is most
relevant to this exact task?” rather than “which category is universally best
or most important?”.

## C. Alternatives

| Option | Description | Advantages | Risks and limitations | Decisions remaining open | Future implementation impact | Why it is not scoring |
|---|---|---|---|---|---|---|
| A — one primary category with descriptive secondaries | Require one canonical primary category for each entity and retain other categories as annotations. | Simple display and filtering; small conceptual surface. | Forces unlike dimensions into one slot; primary choice becomes unstable across questions; risks information loss and implied universal hierarchy. | Identity, primary-selection basis, conflict handling, every numeric and communication decision. | A future implementation would need a global primary field and governed transition rules when context changes. | The chosen label would still contain no favourable/adverse direction, but users could easily overread it as one. |
| B — multi-label with contextual precedence and no universal primary | Preserve all source-backed category assertions; determine relevance only for an explicit question and fully scoped context; retain ambiguity and conflict. | Aligns with `PSC-OD-003` and `PSC-OD-021`; avoids destructive collapse; supports audit, different views and bounded expert review. | Requires explicit question and scope; consumers must handle multiple assertions and unresolved results; careless projection could still appear global. | Exact classification mappings, ingredient states, scoring, aggregation, criticality, evaluability and communication remain open. | A future implementation would need reviewed contextual projections and provenance, without requiring one canonical primary category. | It selects no favourable/adverse effect and defines no number, penalty, cap, floor or claim. |
| C — extended typed graph with future reasoning | Represent entities, roles, uses, sources, conditions and conflicts in a richer graph intended for rule-based reasoning across domains and jurisdictions. | Maximum expressiveness; explicit relationships; possible long-term extensibility. | Premature scope, complex validation, high legal-maintenance burden and pressure to automate reasoning before its authority is governed. | Graph vocabulary, inference rules, jurisdiction transfer, conflict closure and all scoring/product decisions. | Would require a separately reviewed model and execution contract beyond the first release. | Typed relationships do not themselves define goodness, risk or score, but automated inference could obscure that boundary. |

## D. Selected option — product owner approved

The product owner selected **Option B** on `2026-09-01` under explicit product
authority for the conceptual coexistence and contextual-precedence boundary.

Option B is the smallest policy that preserves the layered ontology already
decided under `PSC-OD-003`. It permits multiple assertions without forcing a
universal hierarchy and uses the question-, domain-, jurisdiction-, date- and
use-sensitive governance decided under `PSC-OD-021`.

Under the decided boundary:

- categories may coexist;
- precedence is contextual and attributable;
- an assertion may be central to one question and irrelevant to another;
- no category automatically produces a score, penalty, cap, floor, ranking or
  user-facing claim;
- conflict and ambiguity remain explicit and traceable;
- no assertion is discarded merely because a bounded view prefers another;
- AI, source prestige, row order and recency cannot close a conflict.

The selection is `DECIDED — PRODUCT OWNER APPROVED`. It approves only the
conceptual model described here and authorizes no entity classification,
scientific conclusion, legal determination, scoring effect or implementation.

## E. Candidate conceptual rules

The following rules are WYE proposals, not external source facts or executable
requirements.

| Candidate rule | Meaning | Does not mean | Non-operative example | Risk mitigated | Decisions still open |
|---|---|---|---|---|---|
| `multi_label_allowed` | More than one source-backed category assertion may attach to the same subject when assertion kinds and scopes are preserved. | Every proposed label is accepted or applicable. | One label entry can retain declared-ingredient and additive-role assertions. | Loss of valid secondary roles. | Identity acceptance, exact mappings and implementation. |
| `no_universal_primary_category` | WYE stores no context-free claim that one category is intrinsically primary for an entity. | A bounded view can never emphasize the assertion relevant to its question. | A nutrient-focused review and an additive-use review may foreground different assertions. | False universal hierarchy. | Projection vocabulary and presentation review. |
| `contextual_precedence_required` | Any preference records the question, subject, assertion kind, jurisdiction, date, product/use scope, conditions and rationale. | Newest or legally binding always wins every question. | Applicable food-information law may be central to a declaration question but not to a hazard question. | Undocumented or cross-domain precedence. | Exact review procedure and accountable roles. |
| `conflict_state_allowed` | Comparable, applicable and materially incompatible assertions can remain in an explicit conflict state. | Different scopes are conflicts, or conflicts may be averaged. | Two interpretations of the same bounded category assertion remain unresolved pending competent review. | Silent conflict closure and cherry-picking. | Conflict reason vocabulary and resolution gate. |
| `source_scope_controls_applicability` | A source assertion can participate only within its issuer mandate, domain, jurisdiction, time, product/use and stated limits. | Source class or prestige establishes universal authority. | A label source supports declaration; a scientific assessment supports its scoped scientific proposition. | Transfer outside source competence. | Operational applicability assessment remains unapproved. |
| `authorization_does_not_imply_goodness` | Regulatory authorization and WYE methodological favourability remain different dimensions. | Authorization is irrelevant to a regulatory question. | An authorized use may be recorded without assigning favourable points. | Regulatory status becoming an automatic benefit or penalty. | `PSC-OD-005`, `PSC-OD-013` and validation. |
| `hazard_does_not_imply_risk` | Hazard identification cannot substitute for compatible exposure and risk characterization. | Hazard information must be discarded when exposure is absent. | A scoped hazard assertion remains visible while risk remains unavailable. | Clinical or product-risk overclaim. | Criticality, exposure and evaluability policies. |
| `label_presence_does_not_imply_exposure` | A declared entry supports label presence within its provenance, not amount, intake or dose. | Label facts are unusable. | Ingredient-list presence remains qualitative when no governed quantity exists. | Invented exposure and false precision. | Quantity semantics, aggregation and missing-data policy. |
| `category_does_not_imply_score` | No category assignment or contextual preference has an automatic numerical or directional effect. | Categories can never become inputs to a separately approved future method. | `food_additive` remains a role assertion with no default penalty. | Hidden scoring policy and category moralization. | `PSC-OD-005`, `PSC-OD-013` and validation. |
| `user_facing_copy_requires_separate_decision` | External wording about a category or conflict requires the communication and claims gate. | Internal traceability must wait for UI design. | A reviewed internal conflict does not automatically generate a warning label. | Misleading claims and accidental release authority. | `PSC-OD-020` and applicable legal review. |

### E.1 Candidate precedence assessment

A future reviewed application of Option B would consider, without assigning
numeric weights or a universal order:

1. the exact question being answered;
2. identity of the assertion subject;
3. assertion kind and category family;
4. jurisdiction and applicable interval;
5. product/category, function, use and conditions;
6. source mandate, version, artifact and `wye_use_disposition`;
7. review status, limitations, ambiguity and conflicts;
8. the downstream decision that is allowed to consume the assertion.

An assertion that is most directly applicable to one bounded question may be
recorded as contextually preferred for that question only. The other assertions
remain visible with their scopes and provenance. This list is conceptual and
does not define an algorithm, sort order or runtime resolver.

### E.2 Coexistence, difference and conflict

Candidate interpretation distinguishes:

| Situation | Candidate disposition | Required preservation |
|---|---|---|
| Assertions address different kinds or compatible roles | `coexisting` | All assertions, scopes, sources and relationships. |
| One assertion answers the bounded question more directly | `contextually_preferred` for that question | Preferred rationale plus all non-preferred assertions. |
| Identity or applicability is not established | `ambiguous` or `unresolved` | Candidate interpretations, missing facts and required review. |
| Same bounded proposition has materially incompatible assertions | `conflicting` | Both assertions, comparison basis and escalation record. |
| Assertion does not answer the bounded question | `not_applicable` for that question | Credible source assertion and reviewed scope mismatch. |

These are conceptual review dispositions. They are not ingredient assessment
states, source lifecycle states, evaluability outcomes or runtime values.

## F. Non-operative examples

Each example is hypothetical and requires governed identity, source,
jurisdiction, date, product/use and conditions before any real classification.

| Example | Possible coexisting assertions | Contextual question | Mandatory boundary |
|---|---|---|---|
| Ascorbic acid | If supported for the exact context: `declared_ingredient`, `food_additive`, `added_nutrient` or `fortified_substance`. | Declaration, technological function and nutrient addition are separate questions. | Not scoring; not a health claim; not a definitive legal determination. |
| Soy lecithin | If supported: declared ingredient, additive/emulsifier context and a distinct allergen-related relationship to soy. | Additive role does not answer personal allergy risk; exact identity and applicable declaration rules remain necessary. | Not scoring; not a health claim; not a definitive legal determination. |
| Natural flavouring declaration | Label declaration may coexist with a separately sourced `flavouring` category assertion. | Label wording alone does not establish subtype, authorization conditions or complete composition. | Not scoring; not a health claim; not a definitive legal determination. |
| Lactose | A declared-ingredient assertion may coexist with an applicable allergy/intolerance declaration context. | General label classification remains separate from individual intolerance and exposure. | Not scoring; not a health claim; not a definitive legal determination. |
| Nitrates or nitrites | If exact identity, function, food category and conditions support it, an additive assertion may coexist with label and scientific assertions. | Authorization for a specified use does not establish dose, exposure, risk or score effect. | Not scoring; not a health claim; not a definitive legal determination. |
| Regulated contaminant | A regulatory contaminant-category assertion can exist without any assertion that the contaminant is present in a specific product. | A maximum level or generic source record is not a product measurement. | Not scoring; not a health claim; not a definitive legal determination. |

The examples do not classify any marketed product and must not be converted into
lookup rules, ingredient penalties or user-facing warnings.

## G. Mandatory separations

| Dimension | Question | Must not imply automatically |
|---|---|---|
| Category assignment | Which role is asserted for which subject and scope? | Primary category, precedence, authorization or score effect. |
| Category precedence | Which applicable assertion is more directly relevant to one bounded question? | Global rank, deletion of other assertions or scientific truth. |
| Source applicability | Can the bounded source assertion support this exact question? | Category acceptance outside source scope. |
| Regulatory authorization | What exact use/status is recorded by a competent authority for the context? | Universal safety, goodness, product compliance or clinical conclusion. |
| Hazard identification | What potential adverse effect is supported under stated conditions? | Exposure, likelihood of harm, risk or penalty. |
| Exposure/risk assessment | What compatible amount, scenario, population and evidence support a risk characterization? | Derivation from label presence or category alone. |
| WYE scoring relevance | Does a separately approved method use the assertion, and how? | Any effect authorized by this RFC. |
| User-facing communication | What reviewed wording may present a bounded fact or WYE result? | Automatic claim, warning, diagnosis or release. |

No dimension can be used as an undocumented proxy for another. In compact
form:

```text
category assignment != category precedence
contextual precedence != universal primary category
regulatory authorization != goodness or universal safety
hazard != exposure != risk
label presence != quantity or dose
category != score
internal assertion != user-facing claim
```

## H. Dependencies on open decisions

This RFC can enable later work but closes none of it.

| Decision | What an approved Option B could enable | What remains open |
|---|---|---|
| `PSC-OD-005` | Preserved, contextual non-numeric ingredient inputs. | Any mapping to the ingredient scale, direction, calibration and validation. |
| `PSC-OD-006` | Distinct roles and relationships before multi-ingredient aggregation. | Quantity treatment, aggregation family, adversarial cases and validation. |
| `PSC-OD-007` | Boundary preventing ingredient categories from becoming a nutrient-profile model. | Nutrition construct and source/model selection. |
| `PSC-OD-013` | Traceable category context for a future flag candidate. | Flag effects, criticality, caps, severity and no-double-counting. |
| `PSC-OD-016` | Explicit ambiguity, conflict and non-applicability as possible inputs to later evaluability analysis. | Indispensability, `not_computable` conditions and missing-data behavior. |
| `PSC-OD-020` | Reviewable assertions and limitations for later communication design. | Final copy, claims, bands, colors, comprehension and legal review. |
| `PSC-OD-022` | Separation of general food categories from personal or special-population contexts. | Premium intended use, privacy and clinical/legal governance. |

`PSC-OD-008` through `PSC-OD-012` and `PSC-OD-014` through `PSC-OD-019` also
remain under their existing authorities and states. This RFC does not decide
any of them.

## I. Explicit boundaries and internal evidence note

### I.1 Excluded decisions and implementation

This RFC introduces no:

- formula, weight, multiplier, threshold, score, cap, floor or ranking;
- category-to-score or state-to-score mapping;
- ingredient or overall aggregation;
- criticality or flag-effect policy;
- coverage, confidence, evaluability or missing-data policy;
- definitive UI content, color, band, warning or claim;
- premium feature or personalization;
- operational source selection;
- API, runtime resolver, database schema, migration or application code;
- scientific, clinical, legal or regulatory approval;
- compliance determination, publication or release authority.

### I.2 Statement classes

- `SOURCE FACT`: bounded content attributable to an identified source in its
  scope;
- `WYE INFERENCE`: a transparent interpretation of source facts and decided WYE
  contracts;
- `WYE DECISION`: the bounded Option B product/governance choice recorded for
  `PSC-OD-004`;
- `WYE PROPOSAL`: candidate detail that remains subject to its competent future
  review and decision.

Option B and its explicit authority limits are a `WYE DECISION`. The detailed
candidate rules, examples and dispositions remain methodological elaborations
and do not become executable requirements through this decision. No cited
source mandates the WYE policy or supplies product-owner authority.

### I.3 Sources reused from the Regulatory Ontology source register

No new external source is introduced. The following already verified source
records are reused at the same `2026-09-01` cutoff. Their artifacts, versions
and transferability limits remain governed by `PSC-OD-021`.

| Source ID | Title; issuer; version/year | Locator | Internal WYE role | Transferability limit | Cutoff verification |
|---|---|---|---|---|---|
| `SRC-EU-ADDITIVES-1333-2008` | Regulation (EC) No 1333/2008 on food additives; European Parliament and Council; consolidated `02008R1333-20260818` | [EUR-Lex ELI, 2026-08-18](https://eur-lex.europa.eu/eli/reg/2008/1333/2026-08-18/eng) | Supports distinction among additive role, function, conditions and other category contexts. | EU additive law only; no product-specific classification, universal safety or WYE score direction. | Reused from the verified `PSC-OD-003` source register; version before cutoff. |
| `SRC-EU-FIC-1169-2011` | Regulation (EU) No 1169/2011 on food information to consumers; European Parliament and Council; consolidated `02011R1169-20250401` | [EUR-Lex ELI, 2025-04-01](https://eur-lex.europa.eu/eli/reg/2011/1169/2025-04-01/eng) | Supports separation of label declaration and allergy/intolerance declaration contexts. | Label law does not prove complete composition, personal risk, authorization or scoring relevance. | Reused from the verified `PSC-OD-003` source register; version before cutoff. |
| `SRC-EU-FLAVOURINGS-1334-2008` | Regulation (EC) No 1334/2008 on flavourings and certain food ingredients with flavouring properties; European Parliament and Council; consolidated `02008R1334-20260216` | [EUR-Lex ELI, 2026-02-16](https://eur-lex.europa.eu/eli/reg/2008/1334/2026-02-16/eng) | Supports a flavouring context distinct from the raw label wording. | Does not classify a product from wording alone or imply authorization, safety or score effect. | Reused from the verified `PSC-OD-003` source register; version before cutoff. |
| `SRC-EU-FORTIFICATION-1925-2006` | Regulation (EC) No 1925/2006 on addition of vitamins, minerals and certain other substances to foods; European Parliament and Council; consolidated `02006R1925-20251126` | [EUR-Lex ELI, 2025-11-26](https://eur-lex.europa.eu/eli/reg/2006/1925/2025-11-26/eng) | Supports separation of added-nutrient and broader fortification contexts. | Does not establish benefit, permitted status for every product, claim compliance or score direction. | Reused from the verified `PSC-OD-003` source register; version before cutoff. |
| `SRC-EU-CONTAMINANTS-915-2023` | Commission Regulation (EU) 2023/915 on maximum levels for certain contaminants in food; European Commission; consolidated `02023R0915-20251008` | [EUR-Lex ELI, 2025-10-08](https://eur-lex.europa.eu/eli/reg/2023/915/2025-10-08/eng) | Supports separation of contaminant category, food/category scope and analytical presence. | A listing or maximum level is not evidence of product presence, exceedance, exposure, risk or non-compliance. | Reused as a bounded artifact verified before cutoff; current-law use still requires competent review. |
| `SRC-EU-GFL-178-2002` | Regulation (EC) No 178/2002, General Food Law; European Parliament and Council; consolidated `02002R0178-20260101` | [EUR-Lex ELI, 2026-01-01](https://eur-lex.europa.eu/eli/reg/2002/178/2026-01-01/eng) | Supports bounded separation of risk assessment, management and communication. | General EU food-law context only; not a category-precedence or scoring authority. | Reused from the verified `PSC-OD-003` source register; version before cutoff. |
| `SRC-CODEX-RISK-2007` | Working Principles for Risk Analysis for Food Safety for Application by Governments, `CXG 62-2007`; FAO/WHO Codex Alimentarius Commission; 2007 | [Official Codex PDF](https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXG%2B62-2007%252FCXG_062e.pdf) | Supports separation of hazard, exposure, risk characterization, management and communication. | Government risk-analysis guidance; not EU law, product classification, source hierarchy or scoring policy. | Official artifact previously verified and adopted before cutoff. |

Source facts support the need to keep questions and authority lanes separate.
Option B is a bounded WYE governance decision, not a conclusion stated or
approved by any external source.

## J. Decision record

### J.1 Registered decision

```text
decision_id: PSC-OD-004
decision_status: DECIDED — PRODUCT OWNER APPROVED
decision_owner: Product owner
decision_date: 2026-09-01
authority_source: Explicit product-owner approval
decision: Option B
decision_text: Modello multi-label con precedence contestuale e nessuna categoria primaria universale, senza introdurre scoring, penalità, cap/floor, ranking o claim UI.
decision_scope: conceptual category-coexistence and contextual-precedence boundary only
required_downstream_review: Scientific, regulatory, legal, data/model, validation, communication and implementation review as applicable
scientific_status: NO SCIENTIFIC VALIDATION PERFORMED OR APPROVED
clinical_status: NO CLINICAL VALIDATION PERFORMED OR APPROVED
legal_or_regulatory_status: NO LEGAL DETERMINATION, COMPLIANCE OR APPROVAL IMPLIED
operational_source_selection: NOT APPROVED
implementation_status: NO API, RUNTIME, DATABASE, MIGRATION OR CODE APPROVED
release_status: NOT APPROVED
```

The product owner explicitly authorized this decision text:

> Modello multi-label con precedence contestuale e nessuna categoria primaria
> universale, senza introdurre scoring, penalità, cap/floor, ranking o claim UI.

This decision closes only `PSC-OD-004`.

### J.2 Approved conceptual boundary

The decision approves only:

- Option B as the conceptual multi-label coexistence model;
- coexistence of regulatory and methodological category assertions;
- contextual precedence and no universal primary category;
- preservation of secondary assertions and their provenance;
- explicit ambiguity, conflict and non-applicability;
- recording the question, scope, source, domain, jurisdiction, date,
  applicability and rationale for every future contextual-precedence decision;
- the principle that source prestige, recency, row order and AI cannot
  automatically select precedence or resolve conflicts.

The detailed category assignments, candidate rules, examples and dispositions
remain non-operative and require their applicable downstream reviews.

### J.3 Authority limits

The decision does not approve:

- any specific entity, category assignment, authorization or legal conclusion;
- scoring, penalties, formulas, weights, thresholds, caps, floors or ranking;
- an operational source for ingredient scoring or nutrient profiling;
- a runtime classification or applicability resolver;
- scientific hazard, exposure or risk conclusions;
- criticality, coverage, confidence, evaluability or missing-data policy;
- final UI claims, premium features or personalization;
- scientific, clinical, legal or regulatory validation or WYE compliance;
- an API, runtime, database, migration or code;
- publication or release.

### J.4 Historical questions and retained gates

The reviewed questions in the proposal history are resolved only at the
conceptual product/governance level: Option B is selected, all applicable
assertions remain preserved, a context-free primary category is prohibited,
contextual precedence requires attributable scope and rationale, and ambiguity
or conflict remains explicit until competent review of the bounded proposition.

The decision basis retains:

- the alternatives and internal source note reviewed in `Fase 7.13.2`;
- the independent read-only verdict `READY_FOR_PRODUCT_OWNER_DECISION`;
- regulatory review for legal classification or jurisdictional applicability;
- data/model stewardship for compatibility with `PSC-OD-003` assertions and
  `PSC-OD-021` provenance;
- food-science or toxicology review wherever category assertions interface with
  hazard, exposure or risk;
- separate decisions for scoring, criticality, coverage, confidence,
  evaluability, missing data and communication;
- separately authorized implementation, publication and release gates.

## K. Acceptance checklist and exit state

### K.1 Acceptance checklist

- [x] The document starts as `DECIDED — PRODUCT OWNER APPROVED`.
- [x] `PSC-OD-004` is `DECIDED` through explicit product-owner approval.
- [x] Option B is approved only as the conceptual coexistence and
  contextual-precedence boundary.
- [x] Options A, B and C retain advantages, risks and open dependencies.
- [x] Category assignment, coexistence, precedence, ambiguity and conflict are
  distinct.
- [x] The decision defines no universal primary category.
- [x] Contextual precedence preserves all secondary assertions and provenance.
- [x] `PSC-OD-003` ontology and `PSC-OD-021` source governance are inherited
  without claiming implementation.
- [x] Category, authorization, hazard, exposure, risk, score relevance and
  communication remain separate.
- [x] All examples are non-operative, non-scoring, non-clinical and not final
  legal determinations.
- [x] No operational source is selected.
- [x] No formula, weight, threshold, score, cap, floor or ranking is defined.
- [x] No criticality, coverage, confidence, evaluability or missing-data policy
  is defined.
- [x] No UI, premium, personalization, API, runtime, database, migration or code
  is introduced.
- [x] `PSC-OD-001`, `PSC-OD-002`, `PSC-OD-003`, `PSC-OD-004` and `PSC-OD-021`
  are the only `DECIDED` decisions.
- [x] `PSC-OD-005` through `PSC-OD-020` and `PSC-OD-022` remain `OPEN`.
- [x] The QPS candidate, golden corpus, delivery package, publication state and
  approval gate are unchanged.
- [x] The bounded decision record is ready for independent read-only review.

### K.2 Exit state

```text
PSC-OD-004: DECIDED — OPTION B — PRODUCT OWNER APPROVED
approved scope: CONCEPTUAL COEXISTENCE AND CONTEXTUAL-PRECEDENCE BOUNDARY ONLY
category coexistence: MULTI-LABEL MODEL APPROVED
universal primary category: PROHIBITED BY THE DECIDED CONCEPTUAL MODEL
contextual precedence: APPROVED AS A CONCEPTUAL, ATTRIBUTABLE BOUNDARY
specific category assignments: NOT MADE
conflict resolutions: NOT MADE
scoring or numeric policy: NOT PRESENT
operational source selection: NOT PRESENT
scientific validation: NOT PRESENT
legal or regulatory approval: NOT PRESENT
database or migration authority: NONE
runtime or API authority: NONE
QPS candidate effect: NONE
next gate: INDEPENDENT REVIEW OF THE PSC-OD-004 DECISION RECORD
```

`PSC-OD-001`, `PSC-OD-002`, `PSC-OD-003`, `PSC-OD-004` and `PSC-OD-021` are
`DECIDED` under their recorded, bounded authorities. `PSC-OD-005` through
`PSC-OD-020` and `PSC-OD-022` remain `OPEN`. This RFC closes only `PSC-OD-004`
and authorizes no implementation.
