DECIDED — PRODUCT OWNER APPROVED

# WYE — Regulatory Ontology RFC

## Document status and authority

```text
decision_id: PSC-OD-003
decision_status: DECIDED — PRODUCT OWNER APPROVED
decision_owner: Product owner
decision_date: 2026-09-01
authority_source: Explicit product-owner approval
decision: Option B
decision_text: Ontologia WYE domain-scoped, multilivello e source-backed per distinguere categorie regolatorie e metodologiche senza introdurre scoring, formule o autorità operativa.
document_kind: regulatory-ontology decision RFC
source_cutoff: 2026-09-01
scientific_approval: NOT PRESENT
clinical_approval: NOT PRESENT
legal_or_regulatory_approval: NOT PRESENT
operational_source_selection: NOT APPROVED
runtime_authority: NONE
ai_approval_authority: NONE
```

This RFC records the product owner's explicit approval of Option B for the
conceptual regulatory-ontology vocabulary and governance boundary needed by a
future WYE food-product scoring method. It closes only `PSC-OD-003` under that
bounded authority.

The decided boundary depends on the source-governance model in `PSC-OD-021`:
source use is domain-scoped, acquired artifacts are immutable, and provenance
is linked to WYE decisions. Every regulatory assertion proposed here therefore
requires an identified source version, acquired artifact, checksum, cutoff,
scope, applicability assessment and accountable review. This RFC neither
implements that register nor declares the current implementation compliant
with it.

The product owner may decide the product vocabulary and traceability boundary.
That authority cannot turn a WYE category into a legal determination, make a
source authoritative outside its jurisdiction and scope, or approve a
scientific interpretation. Legal or regulatory interpretation requires a
competent regulatory specialist and, where material, legal review.

AI may assist discovery, extraction, comparison and drafting. AI has no
autonomous authority to classify an entity, interpret legal applicability,
resolve conflicts, approve an ontology or create a regulatory conclusion.

The candidate `efsa_qps_evidence_selection/1.0.0-candidate.1`, its golden
corpus, delivery package, publication state and external approval gate remain
separate and unchanged. No source cited here becomes an operational scoring
source, and no bibliography is required in the ordinary WYE user interface.

## A. Decision and perimeter

### A.1 Decided question

The product-owner decision recorded for `PSC-OD-003` answers:

> Which jurisdiction-, date-, category- and condition-aware conceptual
> ontology should WYE use to distinguish label roles, regulatory categories,
> authorization assertions and methodological contexts for ingredients,
> substances and food components, while preserving source provenance and
> avoiding any automatic scoring or safety inference?

The bounded decision concerns vocabulary and semantic separations. It does not
determine the legal status of a specific product, ingredient or use.

### A.2 Approved conceptual scope

Within the approved ontology boundary, this RFC retains the following
conceptual design. Detailed category membership and disposition rules remain
candidate material unless expressly included in the decision record:

- the entity and context to which each assertion attaches;
- candidate regulatory and methodological category families;
- coexistence and overlap rules at a conceptual level;
- jurisdiction, applicable date, product/category and conditions-of-use scope;
- the distinction between issuer facts, extracted facts, WYE classifications
  and unresolved interpretations;
- provenance from the source artifact to the classification assertion and the
  WYE decision that authorizes its vocabulary;
- review roles and downstream gates;
- explicit unknown, ambiguous, conflicting and not-applicable outcomes.

### A.3 Explicit exclusions

This RFC does not select or define:

- an operational source for ingredient scoring or nutrient profiling;
- a formula, weight, multiplier, threshold, score, cap, floor or ranking;
- a numerical mapping for any category or status;
- an ingredient-state resolution or primary-state precedence policy;
- an ingredient aggregation or overall aggregation method;
- a criticality, coverage, confidence, evaluability or missing-data policy;
- a nutrient-profile model or nutrition category system;
- a product-specific legal or regulatory compliance conclusion;
- definitive UI wording, colors, bands or claims;
- premium features or personalization;
- an API, runtime classifier, database schema, migration or application code.

## B. Problem to solve

### B.1 Why a regulatory ontology is needed

Food labels, regulatory instruments and scientific assessments describe
different things. WYE needs a vocabulary capable of distinguishing, among
other concepts:

- ordinary declared ingredients;
- food additives and their technological functions;
- flavourings and food ingredients with flavouring properties;
- food enzymes;
- processing aids;
- substances or products causing allergies or intolerances;
- added nutrients and fortified substances;
- contaminants and residues;
- microbial or other biological agents;
- novel-food or special regulated-food contexts;
- unresolved or unclassified entities.

These classes are not a single ordered scale. Some describe a label role, some
describe a regulated technological use, some identify a product or population
context, and some describe unintended presence. Several may coexist for the
same underlying entity under different assertions and scopes.

Without this separation, WYE could incorrectly treat:

- appearance in an ingredient list as proof of regulatory classification;
- absence from a label as proof that a processing aid, contaminant or residue
  is absent;
- authorization for a specified use as universal safety;
- a hazard record as a legal prohibition or quantified risk;
- an allergen declaration as a general-population score penalty;
- QPS status as product authorization or a complete safety assessment;
- a scientific dataset record as a current legal-status determination;
- an unknown category as evidence of danger or non-compliance.

### B.2 Required epistemic layers

Every future classification must keep these layers distinct:

```text
source and source version
→ immutable acquired artifact
→ extraction or translation
→ bounded source fact
→ applicability assessment
→ WYE ontology assertion
→ reviewed WYE decision use
→ possible future implementation
```

A source fact reports what the source states. An applicability assessment
determines whether that statement can be used for the exact jurisdiction,
date, entity, product/category and conditions. A WYE ontology assertion applies
an approved WYE vocabulary. None of these layers is itself a score.

## C. Alternatives

| Option | Description | Advantages | Risks and limitations | Decisions remaining open | Future implementation impact | Why it is not scoring |
|---|---|---|---|---|---|---|
| A — label-category minimum | Use only categories visible or inferable directly from the packaged-product label, such as declared ingredient, declared allergen and declared additive function. | Small initial vocabulary; close to available label data; limited regulatory interpretation. | Confuses declaration with complete composition; cannot faithfully represent processing aids, contaminants, residues or context-specific authorization; weak temporal and jurisdictional traceability. | All classification, state-resolution, scoring and aggregation decisions remain open. | Small surface but likely requires breaking expansion when non-label contexts are introduced. | It only labels declared roles; it contains no favourable/adverse direction or number. |
| B — domain-scoped, layered and source-backed WYE ontology | Define separate, coexisting assertion dimensions for label role, regulatory category, authorization context and methodological context, each scoped by source, jurisdiction, date, product/category and conditions. | Fits `PSC-OD-021`; preserves ambiguity and overlap; supports reproducible legal/regulatory review; suitable for the bounded first-release food domain. | Requires disciplined stewardship and expert review; category assignment cannot be inferred from names alone; implementation remains future work. | Entity matching, ingredient-state precedence, numerical mapping, aggregation, criticality, evaluability and communication all remain open. | Requires a future reviewed implementation design, fixtures and mappings without predetermining their storage. | It classifies the role and scope of an assertion; no category has an automatic score effect. |
| C — extended multi-jurisdiction, multi-domain ontology | Attempt a broad ontology covering multiple jurisdictions, foods, supplements, medicines, feed, cosmetics and other regulated domains from the outset. | Potential long-term breadth and cross-domain comparison. | Premature complexity; high legal-maintenance burden; false equivalence across mandates and jurisdictions; conflicts with the bounded first release. | Domain-specific intended use, source competence, conflicts, translations and all downstream policies remain open. | Large vocabulary, mapping and update surface before a validated need exists. | Breadth still would not justify a favourable/adverse scale, but creates pressure to misuse status as scoring. |

## D. Selected option — product owner approved

The product owner selected **Option B** on `2026-09-01` through explicit
product-owner approval.

Option B is the smallest proposal that can represent the first-release domain
without treating the ingredient list as a complete regulatory record. It is
bounded to packaged foods and beverages for adults in the general population,
consistent with `PSC-OD-001`, while preserving the protocol-relative goodness
construct decided in `PSC-OD-002`.

The selection remains prudential because it:

- inherits domain-scoped sources and immutable provenance from `PSC-OD-021`;
- treats categories as contextual assertions rather than intrinsic moral or
  safety labels;
- allows multiple classifications to coexist without imposing precedence;
- preserves unknown and not-applicable states without a numerical fallback;
- leaves scientific evidence, hazard, exposure, risk and score relevance in
  separate decision lanes;
- avoids the legal and maintenance scope of a universal multi-jurisdiction
  ontology.

The decision is `DECIDED — PRODUCT OWNER APPROVED` for the conceptual
vocabulary and governance boundary only. It does not authorize any specific
entity classification, operational source, scientific or legal conclusion,
score effect or implementation.

## E. Candidate conceptual model

### E.1 Assertion subject

A future ontology assertion should identify, conceptually:

| Dimension | Question | Boundary |
|---|---|---|
| Entity identity | Which canonical ingredient, substance, biological agent, component or product context is being described? | A name match alone does not prove identity or equivalence. |
| Assertion kind | Is the statement about label declaration, regulatory category, authorization, scientific assessment or WYE methodology? | Assertion kinds must not substitute for one another. |
| Jurisdiction | Which legal or regulatory system is relevant? | No silent transfer to another jurisdiction. |
| Applicable time | At what date or interval is the assertion evaluated? | Publication, effectiveness, acquisition and cutoff dates remain distinct. |
| Product/category scope | To which food, category, preparation or use does the assertion apply? | Entity-wide status must not be inferred from a bounded use. |
| Conditions of use | Which function, level, specification or other condition limits the statement? | Conditions are not optional explanatory text. |
| Source trace | Which source version, artifact, checksum, extraction and reviewer support the assertion? | A URL or issuer name alone is insufficient. |
| Review disposition | Is the WYE assertion proposed, reviewed, accepted, rejected, ambiguous, conflicting or unresolved? | Internal review state is not issuer authorization status. |

These are conceptual fields, not a database schema or API contract.

### E.2 Coexistence and cardinality

The ontology must support multiple assertions for one entity. For example, a
substance may be a declared ingredient in one product, a carrier or component
of an additive preparation in another context, and the subject of a scientific
hazard assessment. Those statements address different questions.

No candidate category is globally exclusive. Any future exclusivity or
precedence rule must be justified for a specific assertion kind and remain
governed by `PSC-OD-004`. Conflicting assertions must be preserved with their
sources and scopes rather than merged by issuer prestige or recency alone.

### E.3 Minimum conceptual dispositions

The RFC proposes qualitative ontology-review dispositions only:

| Disposition | Meaning | Forbidden interpretation |
|---|---|---|
| `proposed` | A source-backed classification candidate awaits the required review. | Already legally valid or usable for scoring. |
| `accepted_for_scope` | Competent review accepts the assertion for the exact recorded scope. | Universal classification or compliance. |
| `rejected_for_scope` | Review rejects the proposed assertion for the recorded scope and retains the reason. | The entity is prohibited, dangerous or invalid. |
| `ambiguous` | More than one classification or identity remains plausible. | Permission to choose the most convenient category. |
| `conflicting` | Comparable, applicable assertions remain materially incompatible. | Permission to average, vote or select by prestige. |
| `unknown_or_unclassified` | Required identity or category cannot yet be established. | Adverse evidence, illegality or score zero. |
| `not_applicable` | The category question does not apply to the recorded context. | A false, low-quality or invalid source. |

These dispositions do not define ingredient assessment states, evaluability or
missing-data outcomes. Their downstream interaction remains open.

## F. Candidate category families

The identifiers below are WYE candidate concepts. They are not claims that the
same English identifier appears in an external legal text, and they are not
operational rules.

| Candidate category | Conceptual meaning | Does not mean | Typical source classes | Main confusion risk | Decisions still open |
|---|---|---|---|---|---|
| `declared_ingredient` | A component identified as an ingredient from a governed label declaration for a specific product and label state. | Complete batch composition, a legal category, exact quantity, safety or score relevance. | Applicable food-information law; verified label artifact and extraction provenance. | Treating every declared ingredient as an additive, or label absence as proof of absence. | Identity acceptance, declaration exceptions, state resolution, scoring relevance. |
| `food_additive` | A substance or preparation asserted to fall within the applicable regulatory definition and use context for a technological purpose. | Inherently adverse, automatically authorized for every food, present at a known level or score-affecting. | Primary additive legislation, applicable Union lists and conditions, competent guidance. | Conflating class membership, technological function, authorization and product compliance. | Exact source/mapping policy, conditions matching, ingredient state and any later score treatment. |
| `flavouring` | A flavouring or relevant flavouring-material assertion under the applicable scope and definitions. | An ordinary ingredient, additive by default, harmlessness, or authorization in every product/category. | Primary flavouring legislation and applicable lists or conditions. | Collapsing diverse flavouring types or inferring status from the label word “flavouring” alone. | Subtype vocabulary, identity/form matching, authorization context and state policy. |
| `enzyme` | A food-enzyme assertion for an entity added for a technological purpose within the applicable legal scope. | Every enzyme, every microbial culture, a processing aid in all contexts, or automatic declaration on the final label. | Primary food-enzyme legislation and applicable authorization material. | Confusing enzyme, enzyme preparation, producing organism and incidental enzyme production. | Entity relationships, use-context matching, declaration and authorization assertions. |
| `processing_aid` | A context-specific assertion that a substance is used during processing under the applicable definition and conditions. | A declared ingredient, an additive, absence from the finished product, or absence of residues. | Applicable primary legislation and competent jurisdiction-specific interpretation. | Treating processing-aid status as an intrinsic property or inferring absence from non-declaration. | Jurisdiction-specific definition, residual-presence evidence, label implications and review procedure. |
| `allergen_or_intolerance_substance` | A substance or product included in an applicable regulated allergy/intolerance declaration context, or a source-backed relationship to it. | General toxicological hazard, personal clinical diagnosis, automatic general-population penalty or exact exposure. | Applicable food-information law and its controlled lists; verified label facts. | Merging regulatory declaration, actual presence, cross-contact, personal allergy and risk. | Relationship types, cross-contact policy, communication, personalization boundary and flag effects. |
| `added_nutrient` | A nutrient asserted to have been added to a food under an applicable nutritional or compositional context. | Nutritional benefit, necessity, permitted form in every product, or positive score. | Primary addition-of-nutrients legislation, product-specific composition sources and label evidence. | Conflating declared nutrient content, added form, fortification purpose and favourability. | Identity/form matching, product category, nutrient model and nutrition scoring. |
| `fortified_substance` | A broader source-backed assertion concerning a vitamin, mineral or other substance added under an applicable fortification regime. | A universal synonym for `added_nutrient`, a health claim or regulatory compliance. | Primary fortification legislation and applicable lists/conditions. | Treating “fortified” marketing language as proof of regulatory classification or benefit. | Exact vocabulary relationship, other-substance treatment, claims and nutrition method. |
| `contaminant_or_residue` | An assertion of unintended or regulated presence considered under a contaminant or residue framework for a stated food and context. | An ingredient, intentional use, proven presence, exceedance, hazard magnitude or product risk. | Applicable contaminant/residue legislation, official monitoring or reviewed analytical evidence. | Inferring contamination from a generic substance record or treating a maximum level as a product measurement. | Separate contaminant/residue subtypes, analytical evidence, applicability, criticality and exposure policy. |
| `microbial_or_biological_agent` | An identity/context assertion for a microorganism or other biological agent relevant to a food use or assessment. | QPS status, authorization, probiotic benefit, absence of hazard or product safety. | Applicable regulated-product law; scoped EFSA biological-agent assessments; verified identity sources. | Conflating organism, strain, taxonomic unit, function, QPS assessment and authorization. | Identity granularity, strain/taxon transfer, QPS separation, use context and evidence policy. |
| `novel_or_special_regulated_food_context` | A product- or use-context overlay indicating possible relevance of novel-food or special-population food rules. | An intrinsic substance class, a final legal determination, inclusion in the first-release target population or a score effect. | Primary novel-food and foods-for-specific-groups legislation; competent regulatory review. | Applying a product-context rule to every ingredient, or silently including clinical/special populations. | Product-category policy, jurisdiction/date determination, exclusions and future separate contracts. |
| `unknown_or_unclassified` | A first-class outcome where the required regulatory or methodological classification cannot be established for the bounded question. | Safety, danger, prohibition, non-compliance, low confidence by definition or score zero. | Recorded source search, identity and review provenance. | Forcing an adverse/favourable category to make the result appear complete. | Resolution workflow, impact on state policy, evaluability, coverage and communication. |

### F.1 Category versus status

A category answers “what regulated or methodological role is asserted here?”
An authorization assertion answers “what use is authorized, not authorized,
restricted, pending, withdrawn or unresolved under which authority and
conditions?” These are independent.

Accordingly:

```text
food_additive
!= authorised use
!= label presence
!= hazard
!= exposure
!= risk
!= WYE score relevance
```

The same separation applies to every category family.

### F.2 Context overlays

`novel_or_special_regulated_food_context` is deliberately an overlay rather
than a peer substance type. Novel-food and foods-for-specific-groups regimes
can attach to a food, ingredient, source, production process, intended
population or use. Future review must identify the exact subject; WYE must not
stamp a substance with a timeless global label.

## G. Mandatory semantic separations

The ontology must preserve the following independently inspectable dimensions:

| Dimension | Represents | Must not imply automatically |
|---|---|---|
| Label declaration | What a governed product label declares under its captured state. | Complete composition, regulatory category, quantity, authorization or safety. |
| Regulatory category | A source-backed legal/regulatory role under bounded applicability. | Current authorization for the exact use, declaration, hazard, risk or score effect. |
| Authorization status | A competent authority's status for an exact entity/use/category/jurisdiction/date and conditions. | Harmlessness at every dose, product compliance, scientific certainty or favourable score. |
| Hazard identification | Potential to cause an adverse effect under some conditions. | Actual product exposure, likelihood of harm, prohibition or score effect. |
| Risk characterization | Scoped combination of compatible hazard and exposure for a defined population and scenario. | Intrinsic property of an ingredient or a legal conclusion. |
| Exposure or dose | Amount/contact under a stated route, frequency, duration and population. | Ingredient-list presence, authorization or hazard by itself. |
| WYE score relevance | A future approved methodological rule about whether and how an assertion contributes. | Anything in this RFC; relevance remains undecided. |
| User-facing communication | A reviewed presentation of bounded facts and WYE conclusions. | Legal advice, clinical advice, final claims or release approval. |

No dimension may be derived solely from another. In particular:

```text
authorised != safe at every dose or use
not_authorised != poisonous
listed on label != quantitatively exposed
not listed != absent
hazard != risk
QPS status != market authorisation
source record != WYE decision
regulatory classification != product compliance
```

## H. Source-governance application

### H.1 Required source trace for a future assertion

Consistent with decided Option B under `PSC-OD-021`, every future ontology
assertion should be able to reference:

- the stable WYE `source_id` and source class;
- issuer and source domain;
- base-act or source-concept identity;
- exact version, release or consolidated text consulted;
- stable identifier and authoritative locator;
- immutable acquired artifact and checksum;
- publication, effective/applicability, acquisition and cutoff dates as
  distinct values;
- jurisdiction and language;
- extracted passage or structured source fact and its provenance;
- entity, category, product/use and conditions addressed;
- transfer limitations and known conflicts;
- `issuer_lifecycle_status`, `artifact_integrity_status` and
  `wye_use_disposition` as separate coexisting axes;
- reviewer role, decision rationale and dependent WYE decision.

This is a conceptual trace requirement, not a storage design.

### H.2 Source precedence and conflicts

There is no universal hierarchy such as “regulation always beats science” or
“newest source always wins.” The competent source depends on the question:

- applicable primary law anchors a bounded legal-category or authorization
  question;
- competent regulatory guidance may support interpretation but does not become
  binding law merely through WYE use;
- scientific authority outputs may support hazard or assessment propositions
  but do not establish legal compliance;
- label artifacts support what was declared, not the complete regulatory truth
  of the product;
- technical datasets support identity and discovery within their documented
  scope, not autonomous classification or scoring.

When sources differ, WYE must first compare question, jurisdiction, date,
entity/form, product/category, conditions and source mandate. Contextual
differences remain separate assertions. A true unresolved conflict remains
explicit and cannot be closed by AI, issuer prestige, row count or recency
alone.

### H.3 Consolidated-text limitation

EUR-Lex consolidated texts are useful documentary views of an act at a stated
date; they do not themselves have legal effect. A future product-specific legal
determination must verify authentic acts, amendments, transitional provisions,
effective dates and jurisdictional applicability with competent review. The
versions cited below are evidence artifacts for this RFC, not live compliance
lookups.

## I. Relationship to existing WYE concepts

| Existing WYE concept | Permitted relationship | Boundary preserved |
|---|---|---|
| Canonical ingredient | Candidate subject derived from governed label mapping. | Ingredient identity is not universal substance or regulatory identity. |
| Canonical substance | Candidate scientific/regulatory identity anchor. | A substance row does not determine category, authorization or score. |
| Ingredient–substance relationship | Traceable bridge such as `represents`, `contains`, `derived_from`, `mixture_component` or `equivalent_to`. | Relationship type does not prove regulatory equivalence, concentration or exposure. |
| Source/dataset/release | Identifies provider, logical collection and bounded release. | Release membership does not establish authority or legal applicability. |
| Release artifact/checksum | Freezes the exact acquired representation. | Byte integrity does not establish legal validity or scientific quality. |
| Ingestion run/adapter | Records transformation and parser provenance. | Successful parsing does not approve the extracted classification. |
| Assessment/finding | Preserves source-derived scientific content. | A hazard finding is not authorization, exposure, risk or regulatory category. |
| Evidence snapshot | Can bind artifacts and records for deterministic review. | Snapshot inclusion does not decide ontology membership or score relevance. |
| Future ontology assertion | Would bind entity, assertion kind, scope, source trace and review disposition. | This RFC does not implement or populate it. |

Phase 6 capabilities provide useful provenance building blocks, but this RFC
does not declare them complete against the future ontology contract. Legacy
ingredient categories, risk fields, hard-coded catalogs and scoring rules are
not authoritative inputs to `PSC-OD-003`.

## J. Dependencies on open decisions

This RFC may enable later work but closes none of it.

| Decision | What an approved ontology could enable | What remains open |
|---|---|---|
| `PSC-OD-004` | A stable set of regulatory and methodological assertion dimensions for ingredient-state reasoning. | State coexistence, primary-state resolution and precedence. |
| `PSC-OD-005` | Traceable non-numeric inputs whose later relevance can be evaluated. | Any mapping to the ingredient scale, calibration and validation. |
| `PSC-OD-006` | Clear separation of entity role, relationship and product context before aggregation. | Multi-ingredient aggregation, quantity treatment and adversarial cases. |
| `PSC-OD-007` | Boundary preventing regulatory ingredient categories from becoming a nutrient-profile model. | Selection and validation of the nutrition construct. |
| `PSC-OD-013` | Vocabulary that can identify the source and context of a future flag candidate. | Flag-effect class, criticality, caps, severity and no-double-counting. |
| `PSC-OD-016` | Explicit unresolved and not-applicable classifications as possible inputs to future evaluability analysis. | Component indispensability, `not_computable` conditions and missing-data policy. |
| `PSC-OD-020` | Traceable facts and limitations for later communication review. | Final UI language, claims, colors, bands, comprehension and legal review. |
| `PSC-OD-022` | Clear boundary between general food classification and special or personal contexts. | Premium/personalized intended use, privacy, legal and clinical governance. |

`PSC-OD-015`, `PSC-OD-017`, `PSC-OD-018` and `PSC-OD-019` also remain open.
This RFC does not define coverage, confidence, numeric execution or validation
acceptance rules.

## K. Internal evidence note

### K.1 Statement classes

Statements in this RFC are classified as:

- `SOURCE FACT`: a bounded statement attributable to an identified source in
  its own scope;
- `WYE INFERENCE`: a transparent methodological inference from source facts and
  existing WYE contracts;
- `WYE PROPOSAL`: a candidate product/governance choice requiring a decision.

The candidate category identifiers, detailed assertion model and dispositions
remain WYE methodological elaborations within the decided Option B boundary.
No cited act mandates the WYE ontology, and the product-owner decision does not
approve operational mappings or classifications.

### K.2 Sources verified and used

| Source ID | Title; issuer; version/year | Locator | Internal WYE role | Transferability limit | Cutoff verification |
|---|---|---|---|---|---|
| `SRC-EU-ADDITIVES-1333-2008` | Regulation (EC) No 1333/2008 on food additives; European Parliament and Council; consolidated `02008R1333-20260818`; base act `CELEX:32008R1333` | [EUR-Lex ELI, 2026-08-18](https://eur-lex.europa.eu/eli/reg/2008/1333/2026-08-18/eng) | `SOURCE FACT`: distinguishes food additives, technological functions, conditions of use and exclusions including processing aids, nutrients, flavourings and enzymes in their respective scopes. | EU food-additive law only; no WYE score direction, product-specific compliance or universal safety conclusion. | Verified as an official EUR-Lex version dated before `2026-09-01`. |
| `SRC-EU-FIC-1169-2011` | Regulation (EU) No 1169/2011 on food information to consumers; European Parliament and Council; consolidated `02011R1169-20250401`; base act `CELEX:32011R1169` | [EUR-Lex ELI, 2025-04-01](https://eur-lex.europa.eu/eli/reg/2011/1169/2025-04-01/eng) | `SOURCE FACT`: supports ingredient-list, declaration and Annex II allergy/intolerance distinctions. | Label-information law does not prove complete composition, personal allergy risk, authorization or scoring relevance. | Verified official identity and consolidated version before cutoff. |
| `SRC-EU-FLAVOURINGS-1334-2008` | Regulation (EC) No 1334/2008 on flavourings and certain food ingredients with flavouring properties; European Parliament and Council; consolidated `02008R1334-20260216`; base act `CELEX:32008R1334` | [EUR-Lex ELI, 2026-02-16](https://eur-lex.europa.eu/eli/reg/2008/1334/2026-02-16/eng) | `SOURCE FACT`: supplies the bounded flavouring domain, category concepts, lists and conditions of use. | Does not classify a product from label wording alone or imply universal authorization, safety or score effect. | Verified official identity and current consolidated date before cutoff. |
| `SRC-EU-ENZYMES-1332-2008` | Regulation (EC) No 1332/2008 on food enzymes; European Parliament and Council; consolidated `02008R1332-20121203`; base act `CELEX:32008R1332` | [EUR-Lex ELI, 2012-12-03](https://eur-lex.europa.eu/eli/reg/2008/1332/2012-12-03/eng) | `SOURCE FACT`: distinguishes food enzymes, enzyme preparations, technological purpose, processing-aid contexts and incidental microbial cultures. | Does not make every enzyme or microorganism a food enzyme or establish WYE scoring relevance. | Verified official identity and consolidated version before cutoff. |
| `SRC-EU-FORTIFICATION-1925-2006` | Regulation (EC) No 1925/2006 on addition of vitamins, minerals and certain other substances to foods; European Parliament and Council; consolidated `02006R1925-20251126`; base act `CELEX:32006R1925` | [EUR-Lex ELI, 2025-11-26](https://eur-lex.europa.eu/eli/reg/2006/1925/2025-11-26/eng) | `SOURCE FACT`: supports separation of added vitamins/minerals, permitted forms and “other substances” within its scope. | Excludes food supplements from its vitamin/mineral provisions and does not establish nutritional benefit, claims compliance or score direction. | Verified official identity and consolidated version before cutoff. |
| `SRC-EU-FSG-609-2013` | Regulation (EU) No 609/2013 on food intended for infants and young children, food for special medical purposes and total diet replacement; European Parliament and Council; consolidated `02013R0609-20250901`; base act `CELEX:32013R0609` | [EUR-Lex ELI, 2025-09-01](https://eur-lex.europa.eu/eli/reg/2013/609/2025-09-01/eng) | `SOURCE FACT`: identifies special regulated product/population contexts that require separation from the first-release general-adult domain. | Used only as a boundary; it does not extend WYE to infants, patients, medical use or personal dietary management. | Verified official identity and version dated exactly at cutoff. |
| `SRC-EU-NOVEL-2283-2015` | Regulation (EU) 2015/2283 on novel foods; European Parliament and Council; consolidated `02015R2283-20210327`; base act `CELEX:32015R2283` | [EUR-Lex ELI, 2021-03-27](https://eur-lex.europa.eu/eli/reg/2015/2283/2021-03-27/eng) | `SOURCE FACT`: supports a distinct novel-food context, including source-, process- and history-dependent categories. | Does not allow WYE to determine novel status from a name, classify every microorganism as novel or infer safety/scoring. | Verified official identity and consolidated version before cutoff. |
| `SRC-EU-CONTAMINANTS-915-2023` | Commission Regulation (EU) 2023/915 on maximum levels for certain contaminants in food; European Commission; consolidated `02023R0915-20251008`; base act `CELEX:32023R0915` | [EUR-Lex ELI, 2025-10-08](https://eur-lex.europa.eu/eli/reg/2023/915/2025-10-08/eng) | `SOURCE FACT`: supports separation of contaminant context, food/category applicability and analytical level from ingredient status. | A listed contaminant or maximum level is not evidence of presence, exceedance, exposure, risk or product non-compliance. | Verified official artifact/version before cutoff; later applicability still requires competent current-law review. |
| `SRC-EU-GFL-178-2002` | Regulation (EC) No 178/2002, General Food Law; European Parliament and Council; consolidated `02002R0178-20260101`; base act `CELEX:32002R0178` | [EUR-Lex ELI, 2026-01-01](https://eur-lex.europa.eu/eli/reg/2002/178/2026-01-01/eng) | `SOURCE FACT`: supports separation of risk assessment, management and communication and bounded general food-law concepts. | General EU food-law context only; not an ingredient ontology, scoring authority or WYE compliance approval. | Verified official consolidated version before cutoff. |
| `SRC-CODEX-RISK-2007` | Working Principles for Risk Analysis for Food Safety for Application by Governments, `CXG 62-2007`; FAO/WHO Codex Alimentarius Commission; 2007 | [Official Codex PDF](https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXG%2B62-2007%252FCXG_062e.pdf) | `SOURCE FACT`: supports transparent separation of hazard identification, hazard characterization, exposure assessment, risk characterization, management and communication. | Government food-safety risk-analysis guidance; not EU law, product classification, a source hierarchy or scoring policy. | Official four-page artifact verified; adopted before cutoff. |
| `SRC-EFSA-QPS-TOPIC-2026` | Qualified Presumption of Safety (QPS); European Food Safety Authority; official topic page reviewed 2026 | [EFSA QPS topic](https://www.efsa.europa.eu/en/topics/topic/qualified-presumption-safety-qps) | `SOURCE FACT`: QPS is a scoped pre-assessment for defined taxonomic units and regulated-product applications; it does not necessarily lead to market authorization. | Used only to distinguish biological-agent identity/assessment from authorization. It does not approve the WYE QPS candidate, individual strains, products or scores. | Official EFSA page and 2026 scope verified before cutoff. |
| `SRC-EFSA-OPENFOODTOX-2026` | Chemical Hazards Database — OpenFoodTox; European Food Safety Authority; official page reviewed 2026 | [EFSA OpenFoodTox](https://www.efsa.europa.eu/en/data-report/chemical-hazards-database-openfoodtox) | `SOURCE FACT`: the dataset provides structured hazard information derived from EFSA assessments and distinguishes data reuse from original scientific outputs. | Hazard data are not suitability for food use, legal authorization, product exposure, risk, regulatory category or WYE score. | Official EFSA page and stated 2026 release context verified before cutoff. |

### K.3 Bounded WYE inference

From the source facts and WYE contracts, this RFC makes the following
`WYE INFERENCE`:

- label declaration, regulatory role and authorization require separate
  assertions because their source scopes and evidentiary bases differ;
- regulatory classes are contextual and may overlap, so a single exclusive
  ingredient type would lose material meaning;
- product-, category-, jurisdiction-, condition- and date-specific scope is
  necessary for reproducible classification;
- scientific hazard sources and regulatory sources must remain in separate
  authority lanes;
- unknown, ambiguous and conflicting classifications must be preserved rather
  than forced into a favourable or adverse outcome;
- a source-backed ontology can make later decisions auditable without deciding
  their scoring relevance.

This inference is an internal methodological proposal. It is not legal advice,
scientific validation or regulatory approval.

## L. Decision record

### L.1 Registered decision

```text
decision_id: PSC-OD-003
decision_status: DECIDED — PRODUCT OWNER APPROVED
decision_owner: Product owner
decision_date: 2026-09-01
authority_source: Explicit product-owner approval
decision: Option B
decision_text: Ontologia WYE domain-scoped, multilivello e source-backed per distinguere categorie regolatorie e metodologiche senza introdurre scoring, formule o autorità operativa.
decision_scope: conceptual regulatory-ontology vocabulary and governance boundary for the decided WYE food domain only
required_contributors: Regulatory specialist; data/model steward; food-science reviewer
required_downstream_review: Regulatory and legal review for legal interpretation; scientific review for hazard/risk interfaces; validation review before implementation
scientific_status: NO SCIENTIFIC VALIDATION PERFORMED OR APPROVED
legal_or_regulatory_status: NO LEGAL DETERMINATION, COMPLIANCE OR APPROVAL IMPLIED
operational_source_selection: NOT APPROVED
implementation_status: NO API, RUNTIME, DATABASE, MIGRATION OR CODE APPROVED
release_status: NOT APPROVED
```

Authorized decision text:

> Ontologia WYE domain-scoped, multilivello e source-backed per distinguere
> categorie regolatorie e metodologiche senza introdurre scoring, formule o
> autorità operativa.

This decision closes only `PSC-OD-003`. It approves Option B as the conceptual
ontology boundary and does not approve scientific content, legal status,
operational classification or implementation.

### L.2 Approved boundary and authority limits

The product-owner decision approves only:

- the vocabulary and governance boundary of the regulatory ontology;
- the already decided WYE food domain;
- a domain-scoped, layered and source-backed model governed by `PSC-OD-021`;
- coexistence of regulatory and methodological category assertions;
- continued separation of label declaration, regulatory category,
  authorization status, hazard identification, risk characterization,
  exposure/dose, WYE score relevance and user-facing communication.

The decision does not approve:

- scoring, formulas, weights, thresholds, caps, floors or ranking;
- an operational source for ingredient scoring or nutrient profiling;
- a runtime classification or any specific entity, product or use
  classification;
- source applicability outside the issuer's mandate;
- scientific hazard, exposure or risk conclusions;
- criticality, coverage, confidence, evaluability or missing-data policy;
- final UI claims, premium features or personalization;
- scientific, clinical, legal or regulatory validation or WYE compliance;
- an API, runtime, database, migration or code;
- implementation, publication or release.

The 12 sources in Section K support construction and review of this conceptual
boundary only. None becomes an operational source or WYE scoring authority.

### L.3 Historical decision questions and disposition

The product-owner decision answers only the bounded Option B questions within
its recorded authority:

- the first-release ontology boundary is domain-scoped and layered;
- regulatory and methodological assertions may coexist;
- assertions remain source-backed under `PSC-OD-021`;
- the mandatory semantic dimensions remain separate.

The detailed category inventory, overlay behavior and review dispositions
remain conceptual candidate material. The decision selects no operational
source, entity classification, legal status, scientific rule or score.

### L.4 Gates retained after the decision

The bounded product decision is recorded, but downstream work still requires:

- regulatory and, where material, legal review of specific legal
  interpretations and classifications;
- data/model stewardship for compatibility with `PSC-OD-021` provenance and
  identity boundaries;
- food-science review wherever ontology assertions interface with hazard,
  exposure or risk;
- separate decisions for state precedence, scoring, criticality, missing data,
  confidence, evaluability and communication;
- validation review before implementation;
- a separately authorized implementation, publication or release decision;
- an independent read-only review of this decision record.

## M. Acceptance checklist

- [x] The document starts as `DECIDED — PRODUCT OWNER APPROVED`.
- [x] `PSC-OD-003` is `DECIDED` through explicit product-owner approval.
- [x] Option B is approved only for the conceptual vocabulary and governance
  boundary.
- [x] Options A, B and C retain advantages, risks and open dependencies.
- [x] The proposal is limited to foods and packaged beverages for the decided
  first-release intended use.
- [x] Label role, regulatory category, authorization, hazard, risk, exposure,
  score relevance and communication are separated.
- [x] Candidate categories are conceptual, source-backed and non-numeric.
- [x] Category coexistence does not decide state precedence under `PSC-OD-004`.
- [x] `PSC-OD-021` source governance is inherited without claiming that a
  source register is implemented.
- [x] Regulatory sources are bounded by jurisdiction, date, category and use.
- [x] Scientific sources do not become legal authority, and legal sources do
  not become scientific validation.
- [x] QPS and OpenFoodTox are not treated as authorization or scoring sources.
- [x] No operational source is selected for ingredient scoring or nutrient
  profiling.
- [x] No formula, weight, threshold, score, cap, floor or ranking is defined.
- [x] No criticality, coverage, confidence, evaluability or missing-data policy
  is defined.
- [x] No UI, premium, personalization, API, runtime, database, migration or code
  is introduced.
- [x] `PSC-OD-001`, `PSC-OD-002`, `PSC-OD-003` and `PSC-OD-021` are the only
  `DECIDED` decisions.
- [x] `PSC-OD-004` through `PSC-OD-020` and `PSC-OD-022` remain `OPEN`.
- [x] The QPS candidate, golden corpus, delivery package, publication state and
  approval gate are unchanged.
- [x] The bounded decision record is ready for independent read-only review.

## N. Exit state

```text
PSC-OD-003: DECIDED — OPTION B — PRODUCT OWNER APPROVED
regulatory ontology: CONCEPTUAL VOCABULARY/GOVERNANCE BOUNDARY ONLY
specific entity classifications: NOT MADE
legal or regulatory compliance: NOT ASSESSED OR APPROVED
scientific validation: NOT PRESENT
ingredient score relevance: NOT DECIDED
formula or numeric policy: NOT PRESENT
operational source selection: NOT APPROVED
source register implementation: NOT CLAIMED
database or migration authority: NONE
runtime or API authority: NONE
QPS candidate effect: NONE
next gate: INDEPENDENT REVIEW OF THE DECISION RECORD
```

`PSC-OD-001`, `PSC-OD-002`, `PSC-OD-003` and `PSC-OD-021` are `DECIDED` under
their recorded, bounded authorities. `PSC-OD-004` through `PSC-OD-020` and
`PSC-OD-022` remain `OPEN`. This RFC closes only `PSC-OD-003` and authorizes no
implementation.
