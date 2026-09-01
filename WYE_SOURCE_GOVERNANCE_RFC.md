DECIDED — PRODUCT OWNER APPROVED

# WYE — Source Governance RFC

## Document status and authority

```text
decision_id: PSC-OD-021
decision_status: DECIDED — PRODUCT OWNER APPROVED
decision_owner: Product owner
decision_date: 2026-09-01
authority_source: Explicit product-owner approval
decision: Option B
decision_text: Source register domain-scoped con artefatti immutabili e provenienza collegata alle decisioni WYE.
document_kind: governance decision RFC
source_cutoff: 2026-09-01
governance_authority: PRODUCT OWNER APPROVED — GOVERNANCE MODEL ONLY
scientific_selection_policy: NOT APPROVED
runtime_authority: NONE
ai_approval_authority: NONE
```

This RFC records the product-owner decision on how WYE governs internal sources
used to support future product-scoring decisions. `PSC-OD-021` is `DECIDED`
only for the bounded governance model in Option B. The decision does not
approve a scientific selection policy, choose an operational source, establish
scientific truth or claim implementation readiness.

The product owner may decide product and traceability requirements, including
which explanations WYE must be able to reproduce. Product authority cannot
make a source scientifically or regulatorily authoritative outside the
source's own domain, jurisdiction, date, purpose and stated scope.

AI has no autonomous authority to select, rank, interpret, approve or
supersede sources. AI-assisted work remains reviewable support to accountable
human roles.

The candidate `efsa_qps_evidence_selection/1.0.0-candidate.1`, its golden
corpus, delivery package, publication state and approval gate remain separate
and unchanged. No source, including a public-authority source, automatically
becomes a general truth about product healthiness, universal safety, clinical
risk or regulatory compliance.

The sources cited in this RFC are internal methodological support. They do not
create a bibliography requirement in the WYE user interface.

## A. Decision and perimeter

### A.1 What `PSC-OD-021` decides

The decision approves a conceptual governance contract for:

- the conceptual source-register schema;
- source classes and a domain-sensitive hierarchy;
- minimum identity and locator requirements;
- version, publication date, effective date, acquisition date and cutoff
  semantics;
- artifact acquisition, checksum identity and provenance;
- applicability assessment by question, domain, jurisdiction, population,
  product/category and time;
- update, monitoring, supersession, deprecation and withdrawal handling;
- conflict and uncertainty recording;
- traceability from an acquired source artifact through extraction, synthesis,
  proposal, review and a future WYE decision;
- accountable owners, reviewers and approval gates.

The governance contract requires a future source-dependent decision to be
reproducible as of its
declared cutoff. Reproducibility means that a reviewer can identify the source
version and acquired bytes used, reconstruct the bounded evidence path, see
the limitations and conflicts recorded at the time, and distinguish source
content from WYE interpretation and policy.

### A.2 What remains outside `PSC-OD-021`

This RFC does not decide:

- a specific source for ingredient scoring or nutrition scoring;
- any source-specific admissibility rule for a future scoring method;
- a formula, weight, multiplier, threshold, cap, floor or ranking;
- a nutrient-profiling model or food-category system;
- a regulatory ontology or legal-status mapping;
- an ingredient-state, criticality, coverage, evaluability, missing-data or
  confidence policy;
- a numeric mapping or aggregation method;
- user-interface content or a user-facing claim;
- an API, runtime, database schema, migration or application code;
- premium features or personalization.

The RFC also does not assert that the present WYE implementation already
satisfies the approved conceptual governance contract.

### A.3 Governance question considered

The bounded decision question was:

> Which domain-sensitive, versioned and auditable internal governance contract
> should WYE use to identify, preserve, assess and trace sources supporting
> future product-scoring decisions without conferring authority beyond each
> source's applicable scope?

## B. Approved conceptual governance principles

### B.1 Authority is limited to domain and question

A source has no context-free authority. Its possible role depends on the exact
question, issuer mandate, jurisdiction, effective date, population,
product/category, method and limitations. A legally binding text may answer an
applicable legal-status question but does not establish a clinical conclusion.
A scientific assessment may support a scientific proposition but does not by
itself establish legal compliance.

No universal precedence order may replace a question-specific applicability
assessment. Issuer prestige, document type or recency alone is insufficient.

### B.2 Traceability and immutable acquisition

Every source used in a proposal must lead to an identified acquired artifact.
The acquired bytes, or a verifiable canonical representation where bytes
cannot lawfully be retained, must receive an artifact identity and checksum.
That frozen artifact is never overwritten when the upstream source changes.

URL equality is not content identity. A mutable URL may point to different
versions over time; a checksum proves acquired bytes, not scientific validity.

### B.3 Versioning and reproducibility

WYE must distinguish source identity, source version/release, acquired artifact
identity and WYE register-record revision. A corrected extraction creates a new
reviewed extraction or register revision linked to its predecessor; it does not
rewrite the source artifact or historical decision trace.

A future decision must identify its source cutoff and the exact source
artifacts used. Later discovery, acquisition or publication must not silently
alter that historical decision.

### B.4 Time semantics

The following dates answer different questions and must not substitute for one
another:

| Time concept | Question answered |
|---|---|
| Publication date | When did the issuer publish the source or version? |
| Effective/validity date | When did a legal, regulatory or governed source become applicable, expire or cease to apply? |
| Acquisition date | When did WYE obtain and freeze the artifact? |
| Evidence cutoff | Which scientific or regulatory information may support the bounded WYE proposal or decision? |
| Review/decision date | When did accountable WYE roles assess or decide the bounded use? |

Acquisition time must never silently replace publication or effective time.
When a necessary date is unknown, the unknown is explicit and its effect on
applicability is reviewed; it is not inferred from ingestion metadata.

### B.5 Separation of epistemic layers

WYE must keep these layers distinct and traceable:

```text
source artifact
→ verified identity and metadata
→ human- or tool-assisted extraction/translation
→ bounded source facts
→ evidence synthesis or methodological inference
→ WYE proposal
→ reviewed WYE decision
```

A source fact is attributable to the source. An extraction is a representation
of source content. A synthesis combines governed inputs. A WYE proposal is a
policy candidate. A WYE decision is an accountable governance act. None may be
silently relabelled as another.

### B.6 Limits, uncertainty and conflicts

Limitations, transfer assumptions, missing information and known conflicts are
first-class records. Silence in a source is not evidence of absence, approval,
safety, harm or applicability. Different scoped answers are not automatically
conflicting answers.

### B.7 Auditability and update without historical rewrite

Source registration, applicability review, WYE use, correction, supersession
and deprecation must be attributable to accountable agents and dated events.
Historical artifacts and decisions remain reachable even when no longer
current. A current-state view may be derived; it must not erase history.

### B.8 No unverified AI dependency

No source may enter a decision trace solely through an unverifiable AI output.
An AI-produced citation, translation, extraction or synthesis must be checked
against the identified source artifact and carry the required human review.
Model fluency, agreement among models or repeated generation is not source
verification.

## C. Approved conceptual source taxonomy and contextual hierarchy

### C.1 Taxonomy

| Source class | May support | Must not support by itself | Principal limits | Possible WYE role | Required review |
|---|---|---|---|---|---|
| Primary regulatory source | Binding or formally adopted requirements within the issuing jurisdiction, effective period, product scope and conditions | Clinical truth, universal scientific validity, applicability outside jurisdiction, or a WYE score | Amendments, consolidated versus original text, transitional provisions, definitions and enforcement context | Anchor for a bounded legal/regulatory question | Regulatory specialist; legal review where interpretation or external claims are material |
| Interpretive regulatory guidance | An authority's stated interpretation, procedure or compliance guidance in its declared scope | Binding law when the document is non-binding; scientific proof outside its mandate | Guidance status, jurisdiction, version, audience and possible replacement | Interpretive context beside primary law | Regulatory specialist; legal review when relied on for claims or compliance |
| Public-authority scientific opinion or guidance | The authority's scientific assessment, method or advice for its stated question, population and domain | General product healthiness, legal compliance, or transfer to a different question | Mandate, evidence cutoff, assumptions, uncertainty, population and domain | Scientific benchmark, method reference or scoped evidence contribution | Domain scientific reviewer; regulatory reviewer when regulatory meaning is implicated |
| Curated scientific data | Structured records and source-linked observations within the dataset's coverage and curation rules | A conclusion not present in the data; independence, completeness or causal validity without assessment | Dataset scope, release, curation method, source lineage, duplication and missing fields | Reproducible evidence input or discovery index | Data steward plus domain reviewer for scientific use |
| Systematic review | A structured synthesis for its review question, eligibility criteria, search date and included evidence | Applicability outside the review question; automatic precedence over newer or excluded evidence | Search cutoff, review quality, heterogeneity, publication bias and update status | Evidence synthesis input or benchmark | Domain scientific reviewer with evidence-synthesis competence |
| Primary study | Findings for the studied design, population/model, exposure/intervention, endpoint and analysis | A general policy, universal effect, legal status or independent replication | Study design, bias, power, reporting, transferability and dependency | Atomic evidence input under an approved selection/synthesis policy | Domain scientific reviewer; specialist review as required by method |
| Methodological standard | A method, vocabulary, reporting or provenance convention within its declared purpose | Scientific correctness of content merely conforming to the standard | Version, normative status, implementation profile and domain fit | Register, provenance, reporting or validation design support | Data/model steward and relevant method owner |
| Technical or operational source | Interface, file, adapter, parser, release or operational behavior | Scientific authority, regulatory status or substantive evidence conclusion | Mutable documentation, implementation version and provider availability | Acquisition and transformation provenance only | Technical owner plus data steward |
| Non-admissible source | Discovery leads only when a governed reviewer can locate and verify an admissible primary source | Any direct scientific, regulatory or policy support | Unverifiable identity, absent provenance, fabricated content, commercial promotion, undisclosed synthesis or inaccessible basis | Quarantined lead with reason; never decision support | Data steward or governance reviewer confirms exclusion |

Commercial pages, blogs, promotional material, unattributed summaries,
AI-generated citations without verified originals and sources whose identity or
content cannot be verified are non-admissible as direct decision support.

### C.2 Contextual hierarchy

The recommended hierarchy is a question-specific decision procedure, not a
universal ranking:

1. Define the exact question, domain, intended use, jurisdiction, time,
   population and product/category.
2. Identify which source class is competent to answer that question.
3. Prefer direct, primary and currently applicable authority within that class
   when available, while retaining relevant interpretation and evidence.
4. Verify stable identity, version, artifact, provenance and limitations.
5. Assess transferability and conflicts before use.
6. Record why each source is used, not used, contextual only or unresolved.
7. Route the proposal through the reviewer competent for that source and claim.

Recency does not automatically defeat an older still-effective source. Primary
law does not automatically defeat scientific evidence on a scientific question.
A systematic review does not automatically defeat a primary study when the
questions, cutoffs or populations differ. No provider receives global
precedence.

## D. Approved conceptual source register

### D.1 Register boundary

The source register is a governed metadata and lineage record for sources and
their frozen artifacts. It is not a database design, an evidence-selection
algorithm, a scoring policy or a list of approved scoring sources.

Conceptually mandatory means that every registered source record carries the
field. When the source does not issue a value, the record uses an explicit
reviewed state such as `not_issued`, `not-applicable` or `unknown`, never a
fabricated substitute. Conditional fields are required when the relevant
condition exists or is material to the proposed use.

### D.2 Minimum fields

| Field | Conceptual requirement | Meaning and rule |
|---|---|---|
| `source_id` | Mandatory | Stable WYE identifier for the source concept; it must not encode an unsupported authority ranking. |
| Title | Mandatory | Official title from the identified artifact; translations are separately identified. |
| Issuer/authors | Mandatory | Accountable issuing body or authors as published; absence blocks attribution-dependent use. |
| Source type | Mandatory | One governed taxonomy class plus any reviewed subtype. |
| Domain | Mandatory | Scientific, regulatory, methodological or operational domain in which authority is assessed. |
| Jurisdiction | Conditional | Required for law, regulation, official guidance or any geographically bounded applicability. |
| Stable identifier | Mandatory record | DOI, PMID, CELEX, ISBN, standard/document number, repository identifier or explicit reviewed absence. |
| URL/locator | Mandatory | Direct authoritative locator where available; landing page and acquired-artifact locator may both be retained. |
| Publication date | Mandatory record | Issuer publication date or explicit unknown; never replaced by acquisition date. |
| Effective/validity date | Conditional | Required when effect, expiry or legal/scientific applicability has distinct time semantics. |
| Version or release | Mandatory record | Issued version/release/revision or explicit `not_issued`; mutable living sources require a captured revision identity. |
| Acquisition date | Mandatory | Timestamp when WYE acquired the artifact or verified the retained representation. |
| Checksum/artifact identity | Mandatory for use | Digest, size and artifact identity for the exact acquired representation; absence blocks reproducible decision use. |
| Cutoff | Mandatory for use | The evidence/source cutoff under which the source was considered for the WYE proposal or decision. |
| Scope | Mandatory | Issuer-stated and reviewer-interpreted bounded subject and purpose, kept distinguishable. |
| Population | Conditional | Required when human, animal, model-system or population applicability is material. |
| Product/category | Conditional | Required when source applicability depends on product type, category, preparation or use. |
| Supportable question | Mandatory | Exact question or proposition class the source may support in WYE. |
| Limits and transferability | Mandatory | Known exclusions, assumptions, data gaps and conditions for transferring the source to the WYE question. |
| `issuer_lifecycle_status` | Mandatory | Issuer-, authority- or official-register state of the identified source/version, such as `active`, `superseded`, `withdrawn` or `expired`. |
| `artifact_integrity_status` | Mandatory for an acquired artifact | Integrity state of the exact representation acquired by WYE, such as `verified`, `checksum-mismatch`, `corrupted`, `unavailable` or `integrity-compromised`. |
| `wye_use_disposition` | Mandatory for proposed or historical WYE use | Scoped WYE applicability disposition for a stated question, domain, jurisdiction, date and use case, such as `eligible`, `limited-use`, `not-applicable`, `deprecated-for-use` or `unresolved`. |
| Supersession relation | Conditional | Typed predecessor/successor or replacement relation, issuer evidence and WYE rationale. |
| Known conflicts | Conditional | Links to scoped conflict records; explicit `none_identified_at_review` is not a claim that no conflict exists. |
| Review level | Mandatory | Reviews completed, reviewer roles, dates, disposition and outstanding gates. |
| Dependent WYE decisions | Mandatory | Decision IDs and versions that used the source; may be an explicit empty set before use. |
| Translation/extraction/AI notes | Conditional | Required when translation, extraction, normalization or AI assistance affected the representation or synthesis. |

### D.3 Identity layers

The register must not collapse:

| Identity layer | Example purpose |
|---|---|
| Source concept | Recognize a continuing report, law, dataset or standard family. |
| Version/release | Identify the issuer's bounded published state. |
| Acquired artifact | Identify the exact bytes or retained canonical representation used by WYE. |
| Extraction/translation | Identify a derived representation and its method/reviewer. |
| Register revision | Record a corrected or enriched WYE metadata statement without changing the source. |
| WYE decision use | Bind a reviewed source role to a particular proposal or decision version and cutoff. |

A persistent identifier supports discovery and citation. It does not replace an
artifact checksum, establish applicability, or certify scientific quality.

### D.4 Independent state axes and conceptual use dispositions

The three state axes are independent and may coexist. None substitutes for
another: for example, an issuer-superseded version may retain a verified frozen
artifact and a `wye_use_disposition` that preserves a bounded historical use.
Every state event must retain its effective or recorded date, rationale,
source/provenance and accountable actor or reviewer. State history is
append-only; a later event does not erase the state under which a prior WYE
decision was made.

Discovery and acquisition milestones such as `candidate`, `verified_identity`
and `frozen_artifact` describe progress through the lifecycle. They are not
substitutes for `issuer_lifecycle_status`, `artifact_integrity_status` or
`wye_use_disposition`.

For a bounded question, `wye_use_disposition` may be recorded conceptually as:

- `eligible`: reviewed as usable for that question and scope;
- `limited-use`: usable only within recorded constraints, including contextual
  support that does not establish the decision premise by itself;
- `not-applicable`: credible but outside the specific WYE question, domain,
  jurisdiction, date or use case; it does not mean that the source is false or
  invalid;
- `deprecated-for-use`: WYE stops new use for a governed, attributable reason
  while preserving historical use;
- `unresolved`: identity, applicability, conflict or evidence gaps prevent a
  reviewed use disposition.

These are governance dispositions, not source-quality scores, operational
selection rules or runtime states approved by this RFC.

## E. Lifecycle, update and supersession

### E.1 Approved conceptual lifecycle

```text
discover → verify → acquire → freeze → assess applicability → use in proposal
→ review → publish/decide → monitor → supersede/deprecate
```

| Stage | Required governance outcome |
|---|---|
| Discover | Record a candidate locator and discovery provenance without implying authority. |
| Verify | Check issuer, title, stable identifier, version, dates, official locator and source class. |
| Acquire | Obtain the authoritative artifact lawfully and record acquisition time and method. |
| Freeze | Preserve bytes or the permitted canonical representation; compute and verify artifact identity and checksum. |
| Assess applicability | State the WYE question and assess domain, jurisdiction, time, population, product/category, transferability, uncertainty and conflicts. |
| Use in proposal | Link bounded source facts and extractions to a WYE inference or proposal; record exclusions and contextual-only sources. |
| Review | Obtain the scientific, regulatory, data-governance, legal or product reviews required by the proposed claim. |
| Publish/decide | Bind the approved decision record to the exact source set, cutoff, artifacts, review evidence and limitations. |
| Monitor | Observe issuer changes, corrections, withdrawals and material new evidence through a separately approved process. |
| Supersede/deprecate | Add an attributable state event and successor relation; preserve the prior artifact, use and dependent decisions. |

This lifecycle specifies no scheduler, polling interval, automatic frequency,
network process or runtime implementation.

### E.2 Update behavior

An upstream change creates a new candidate version or artifact. WYE must compare
identity, scope and content, record what changed and assess whether dependent
proposals or decisions require review. “Latest” is not a sufficient adoption
rationale. A changed URL response never overwrites the prior artifact.

The update record preserves:

- the original artifact and its checksum;
- source version/release and publication/effective dates;
- acquisition time and acquisition provenance;
- evidence of the upstream modification or correction;
- historical WYE decisions and extractions dependent on the prior source;
- the successor artifact and typed relation, when known;
- the reason, reviewer and date for WYE supersession or deprecation;
- an impact assessment disposition for each materially dependent decision.

### E.3 Independent lifecycle, integrity and use states

| Axis and example state | Meaning | Historical treatment |
|---|---|---|
| `issuer_lifecycle_status: active` | The issuer or authoritative register presents the identified version as active for its stated scope. | Preserve the issuer evidence and observation date; WYE applicability remains a separate review. |
| `issuer_lifecycle_status: withdrawn` | The issuer formally retracts or withdraws reliance on the source/version. | Retain the artifact and issuer notice; do not infer anything about a different version or artifact. |
| `issuer_lifecycle_status: expired` | A stated validity or effective period ended without necessarily questioning historical correctness. | Retain the historical applicability interval; do not treat the version as current outside it. |
| `issuer_lifecycle_status: superseded` | A successor replaces the source/version for a defined issuer scope. | Retain the predecessor, artifact and dependent decisions for historical reproducibility; link the successor and review impact. |
| `artifact_integrity_status: verified` | The acquired representation matches its recorded artifact identity and integrity evidence. | Preserve the checksum, verification method, date and actor; this does not establish scientific validity or WYE applicability. |
| `artifact_integrity_status: checksum-mismatch` or `corrupted` | The acquired bytes fail their expected identity or cannot be reliably interpreted. | Quarantine the affected artifact and preserve the failed verification evidence. |
| `artifact_integrity_status: unavailable` | The expected artifact cannot currently be retrieved or accessed. | Preserve prior verified artifacts and the failed-access event; do not infer withdrawal or invalidity. |
| `artifact_integrity_status: integrity-compromised` | Artifact identity, provenance or representation cannot be trusted. | Do not use the artifact for new decisions until it is replaced by a verified artifact or its integrity is restored and verified through governed review. |
| `wye_use_disposition: eligible` or `limited-use` | WYE has reviewed applicability for one bounded question, with any constraints recorded. | Bind the disposition and limits to that question, cutoff and review; do not generalize it. |
| `wye_use_disposition: deprecated-for-use` | WYE stops new use because of a governed limitation or replacement even if the issuer has not withdrawn the source. | Preserve attributable WYE rationale and historical replay. |
| `wye_use_disposition: not-applicable` | The source is credible but does not answer the bounded WYE question or context. | Retain the reviewed scope mismatch; do not relabel the source as false, invalid or low quality. |
| `wye_use_disposition: unresolved` | Applicability, conflict or evidence gaps prevent a reviewed WYE use decision. | Preserve the unresolved reason and required review without manufacturing authority. |

These axes can hold states at the same time and must retain separate event
histories. Supersession is scoped: one version can replace another for a
specific issuer purpose without becoming universally preferable or silently
changing artifact integrity or WYE use disposition.

## F. Conflicts, uncertainty and AI

### F.1 Conflict handling

| Situation | Proposed handling |
|---|---|
| Sources have different scopes | Classify as contextually different unless the same bounded proposition is genuinely addressed. Preserve both scopes. |
| Official versions diverge | Identify issuer, version, effect and supersession notices. Do not select by acquisition time or URL order. |
| Regulatory and scientific sources differ | Keep legal/regulatory and scientific propositions in separate lanes. Applicable law governs the legal question; evidence review governs the scientific question. Escalate any product-policy tension. |
| Scientific studies disagree | Verify comparability and dependency before calling conflict; route comparable evidence to the approved synthesis method and domain review. |
| Authority opinions differ | Record mandate, question, jurisdiction, date, evidence base and uncertainty for each; no global provider precedence. |
| Evidence is insufficient | Record the unresolved question and limits. Do not infer safety, harm, approval, zero, a midpoint or confidence. |
| No authoritative source exists | Keep the proposal unresolved or explicitly identify a bounded WYE methodological choice requiring the proper review. Do not manufacture authority. |

Conflict closure requires an attributable rationale and competent human review.
A choice made for one WYE decision does not silently establish a permanent
precedence rule.

### F.2 Translation and extraction

The original authoritative artifact remains the source anchor. A translation
or extraction is a derived artifact with language, method, tool/version,
operator, date, checksum and review status. Where wording is legally or
scientifically material, a competent human reviewer checks it against the
authoritative original. Machine translation never silently becomes the source.

### F.3 Permitted and prohibited AI assistance

AI may assist:

- discovery of candidate sources;
- metadata extraction and normalization;
- comparison of versions;
- translation drafts;
- source-fact extraction drafts;
- conflict inventories and synthesis drafts;
- citation checking and RFC drafting.

AI must not:

- invent a source, identifier, passage, version or review;
- decide that an issuer has authority outside its mandate;
- ignore scope, transferability, uncertainty or conflict;
- treat absence of evidence as evidence of safety or harm;
- close conflicts or convert uncertainty into certainty;
- approve a source, policy, scientific conclusion or legal interpretation;
- become the sole, unverifiable dependency of a WYE decision.

Every material AI-assisted output must retain the identified source artifact,
the assistance note and the human review required for its intended role.

## G. Relationship to the existing WYE system

### G.1 Conceptual mapping

| Existing WYE concept | Relationship to this proposal | Boundary preserved |
|---|---|---|
| Scientific source | Candidate anchor for issuer/provider identity and domain; not automatically equivalent to a governed source-register record. | Existing rows do not prove future `PSC-OD-021` compliance. |
| Dataset | Groups a provider's data product and scope. | Dataset membership does not establish scientific applicability. |
| Release | Supplies a bounded external release identity and released/acquired time anchors. | Release recency does not establish precedence. |
| Release artifact / storage artifact | Provides an artifact-first path, locator, size and checksum for acquired bytes. | Byte identity does not establish authority or validity. |
| Checksum | Supports integrity and replay of an acquired representation. | A checksum is not a scientific-quality judgment. |
| Ingestion run | Records how one release/artifact was parsed and normalized. | Run completion or recency cannot replace publication date or source applicability. |
| Adapter and parser configuration | Provides transformation provenance and version identity. | Adapter output is a representation, not source truth. |
| Assessments and findings | Carry normalized source-derived content and lifecycle context. | Findings remain separate from WYE synthesis and decision. |
| Batch recovery/checkpoint | Preserves operational retry, resume and changed-upstream handling. | Operational success does not approve scientific use. |
| Ingredient mapping | Provides a separately governed bridge from source targets/substances to ingredients. | Mapping does not confer source authority or product-scoring meaning. |
| Evidence snapshot | Can freeze exact source, release, artifact, run, assessment and finding identities for replay. | Snapshot inclusion is not scientific inclusion or scoring authority. |
| Governance event / publication state | Provides append-only lineage, supersession and review-disposition patterns. | Technical publication is not scientific endorsement or UI release. |
| Future source register | Would bind identity, scope, applicability, limitations, reviews and dependent decisions to the artifact graph. | This RFC defines no database or migration. |
| Future product-scoring decision | Would cite exact register records, source artifacts, cutoff, extracts, synthesis and reviews. | The source trace supports verification but does not decide the scoring rule. |

### G.2 Candidate QPS boundary

The current QPS candidate is a narrow evidence-selection candidate with a
digest-bound golden corpus and external approval gate. This RFC neither changes
its source allowlist nor interprets its scientific values. A future source
register may reference its artifacts and decision provenance only after a
separate design and without weakening its existing approval boundary.

No `PSC-OD-021` decision can approve the QPS candidate, its golden cases, a
scientific selection policy or a production selector.

## H. Implications for other open decisions

This RFC supplies provenance prerequisites; it does not supply substantive
scientific or product-scoring answers.

| Decisions | What source governance enables | What remains open |
|---|---|---|
| `PSC-OD-003`–`PSC-OD-006` | Traceable legal, regulatory, scientific and mapping sources with jurisdiction, dates, versions and limits. | Regulatory ontology, ingredient states, numeric mapping and ingredient aggregation. |
| `PSC-OD-007`–`PSC-OD-011` | Reproducible comparison of nutrient-profile sources, releases, populations, categories and applicable guidance. | Base model, category/preparation rules, sugar semantics, nutrient components and numeric mapping. |
| `PSC-OD-013`–`PSC-OD-014` | Auditable source basis for future flag-effect and criticality proposals. | Flag effects, any caps, severity, no-double-counting and zero overrides. |
| `PSC-OD-015`–`PSC-OD-017` | Traceable evidence for input requirements, data availability, uncertainty and confidence proposals. | Coverage, evaluability, missing-data and confidence policies. |
| `PSC-OD-019` | Identified benchmarks, source cutoffs and immutable inputs for a future validation corpus. | Golden corpus, sensitivity, robustness, comprehension and independent validation design. |
| `PSC-OD-020` | Traceable basis and limitations for later user-facing language review. | Claims, bands, colors, accessibility, comprehension and legal review. |
| `PSC-OD-022` | Separately scoped sources and authorities for privacy, legal, clinical and personalization boundaries. | Premium intended use, DPIA, legal/scientific boundary and governance. |

`PSC-OD-012` and `PSC-OD-018` also remain `OPEN`; this RFC does not select an
overall aggregation family or numeric execution profile.

## I. Internal evidence note

### I.1 Evidence statement classes

Statements in this RFC use three classes:

- `SOURCE FACT`: a bounded statement directly supported by an identified
  source within its own scope;
- `WYE INFERENCE`: a transparent methodological inference drawn from one or
  more source facts and existing WYE contracts;
- `WYE PROPOSAL`: a governance choice offered for decision under
  `PSC-OD-021`, not an externally established fact.

The taxonomy, field requirements, lifecycle, dispositions and recommended
option are `WYE PROPOSAL`. They are informed by the sources below but are not
claimed to be mandated by any one source.

### I.2 Sources actually verified and used

| ID | Issuer/authors; year | Type | Verified locator | Internal role | Transferability limits | Cutoff verified |
|---|---|---|---|---|---|---|
| `SRC-EFSA-EVIDENCE-2015` | European Food Safety Authority; 2015 | Public-authority methodological scientific report | [DOI `10.2903/j.efsa.2015.4121`](https://doi.org/10.2903/j.efsa.2015.4121) | `SOURCE FACT`: EFSA describes upfront planning, conduct against plan, verification, documentation and reporting for evidence use. Supports separation of process stages and deviations. | EFSA assessment methodology; it does not define WYE's register schema or choose scoring evidence. | Yes — published before `2026-09-01` |
| `SRC-EFSA-UNCERTAINTY-2018` | EFSA Scientific Committee; 2018 | Public-authority scientific guidance | [DOI `10.2903/j.efsa.2018.5123`](https://doi.org/10.2903/j.efsa.2018.5123) | `SOURCE FACT`: identified uncertainties and their impact should be documented and kept compatible with conclusions. Supports first-class limitations and uncertainty records. | EFSA scientific assessments; it does not prescribe WYE conflict outcomes or product-scoring policy. | Yes — published before `2026-09-01` |
| `SRC-WHO-GUIDELINES-2014` | World Health Organization; 2014 | Official guideline-development handbook | [WHO publication, ISBN `978-92-4-154896-0`](https://www.who.int/publications/i/item/9789241548960) | `SOURCE FACT`: WHO documents staged guideline development, evidence review and update considerations. Supports review roles and explicit update work. | Health-guideline development context; not authority for food scoring, legal status or WYE source precedence. | Yes — published before `2026-09-01` |
| `SRC-CODEX-RISK-2007` | FAO/WHO Codex Alimentarius Commission; 2007 | Primary official food-safety guidance, `CXG 62-2007` | [Codex `CXG 62-2007` — official PDF](https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXG%2B62-2007%252FCXG_062e.pdf) | `SOURCE FACT`: food-safety risk analysis should be open, documented and reviewed in light of new evidence, while risk assessment, management and communication remain distinct. | Government food-safety risk analysis; not a source register, product-favourability method or universal hierarchy. | Yes — adopted before `2026-09-01`; official artifact verified |
| `SRC-EU-GFL-178-2002` | European Parliament and Council; base act 2002; consolidated version consulted `02002R0178-20260101` | Primary EU regulatory source, Regulation (EC) No 178/2002; base-act identifier `CELEX:32002R0178` | [EUR-Lex consolidated version `02002R0178-20260101`](https://eur-lex.europa.eu/eli/reg/2002/178/2026-01-01/eng) | `SOURCE FACT`: EU food-law risk assessment is based on available scientific evidence and conducted independently, objectively and transparently; assessment, management and communication have distinct roles. WYE uses the identified consolidated version only as internal methodological support for transparency, independence and risk-assessment governance. | EU food-law context only; this use does not establish WYE legal or regulatory compliance, approval or current applicability, all of which require competent regulatory/legal review. | Yes — consolidated version dated `2026-01-01`, available before `2026-09-01` |
| `SRC-EU-TRANSPARENCY-2019` | European Parliament and Council; 2019 | Primary EU regulatory source, Regulation (EU) 2019/1381 | [EUR-Lex CELEX `32019R1381`](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R1381) | `SOURCE FACT`: the EU framework strengthens transparency, accessibility, accountability and reliability around food-chain risk assessment. Supports explicit governance and disclosure boundaries. | EU regulatory risk-assessment system; does not mandate WYE's internal fields or approve reuse of confidential material. | Yes — published before `2026-09-01` |
| `SRC-W3C-PROV-O-2013` | W3C Provenance Working Group; 2013 | Recognized provenance standard, W3C Recommendation | [PROV-O Recommendation, 30 April 2013](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | `SOURCE FACT`: provenance can distinguish entities, activities and responsible agents and express use, generation, derivation and attribution. Supports the artifact-to-decision lineage concept. | General web provenance ontology; WYE does not adopt its RDF/OWL implementation through this RFC. It confers no scientific authority. | Yes — recommendation published before `2026-09-01` |
| `SRC-FAIR-2016` | Wilkinson et al.; 2016 | Peer-reviewed methodological principles | [DOI `10.1038/sdata.2016.18`; PMID `26978244`](https://pubmed.ncbi.nlm.nih.gov/26978244/) | `SOURCE FACT`: FAIR emphasizes persistent identifiers, rich metadata, qualified references and detailed provenance for findability and reuse. Supports identifiers and metadata completeness. | High-level data-stewardship principles; FAIRness does not establish scientific quality, applicability or truth. | Yes — published before `2026-09-01`; DOI and PMID verified |
| `SRC-DATACITE-MDS-4.7` | DataCite Metadata Working Group; 2026 | Recognized metadata standard, version 4.7 | [Documentation DOI `10.14454/qdd3-ps68`](https://doi.org/10.14454/qdd3-ps68) | `SOURCE FACT`: DataCite provides versioned metadata for consistent identification, citation and typed relationships among research outputs. Supports stable identifiers, version and relation concepts. | Citation metadata standard; WYE does not adopt the schema wholesale and it does not evaluate scientific authority or applicability. | Yes — version released `2026-03-03`, before cutoff |

### I.3 Bounded methodological inference

From these source facts and the existing WYE artifact contracts, this RFC makes
the following `WYE INFERENCE`:

- reproducible scientific governance needs both epistemic traceability and
  technical artifact identity;
- domain-limited authority and explicit applicability are safer than a global
  prestige ranking;
- historical immutability and append-only supersession allow updates without
  rewriting the basis of past decisions;
- source facts, derived representations, syntheses and WYE policy decisions
  require separate identities and accountable reviews;
- uncertainty and conflict are reportable states, not permission for AI or a
  product owner to manufacture authority.

The inference does not establish that the proposed register is scientifically
validated or legally sufficient.

## J. Decision record

### J.1 Options

| Option | Description | Strengths | Risks | Recommendation |
|---|---|---|---|---|
| A — Lightweight citation catalog | Store citation metadata and links, with review handled informally in each RFC. | Small documentation burden. | Weak replay, artifact identity, conflict history and supersession trace; decisions can become irreproducible. | Not recommended. |
| B — Domain-scoped source register with immutable artifacts and decision-linked provenance | Govern source classes, contextual authority, exact artifacts, time semantics, applicability, limitations, conflicts, reviews and append-only lifecycle; bind each future decision to its source set and cutoff. | Aligns with existing WYE artifact/provenance patterns; supports audit, reproducibility and bounded authority without choosing scientific content. | Requires disciplined stewardship, role ownership and future implementation design. | `DECIDED — PRODUCT OWNER APPROVED`. |
| C — Universal source hierarchy with automatic newest/highest-authority selection | Assign a global precedence order and replace sources automatically. | Superficially simple. | Conflates domains and questions, hides conflicts and transfer limits, and can create unsupported scientific or legal authority. | Not recommended. |

### J.2 Registered decision

```text
decision_id: PSC-OD-021
decision_status: DECIDED — PRODUCT OWNER APPROVED
decision_owner: Product owner
decision_date: 2026-09-01
authority_source: Explicit product-owner approval
decision: Option B
decision_text: Source register domain-scoped con artefatti immutabili e provenienza collegata alle decisioni WYE.
decision_scope: internal source-governance model and product traceability boundary only
scientific_selection_policy: NOT APPROVED
operational_source_selection: NOT APPROVED
scientific_validation_status: NOT PERFORMED OR APPROVED
legal_or_regulatory_status: NO COMPLIANCE OR APPROVAL IMPLIED
implementation_status: NO DATABASE, MIGRATION, API OR RUNTIME APPROVED
release_or_publication_status: NOT APPROVED
```

The decision approves only:

- the domain-scoped source-governance model;
- separation of source, release/version, acquired artifact, acquisition,
  extraction or translation, synthesis, decision use and future implementation;
- immutable acquired artifacts with checksum identity and provenance;
- traceability between bounded source use and WYE decisions;
- independent, coexisting `issuer_lifecycle_status`,
  `artifact_integrity_status` and `wye_use_disposition` axes;
- contextual hierarchy and precedence based on the question, domain,
  jurisdiction, date and applicability rather than a universal ranking.

The decision does not approve:

- external scientific authority or scientific, clinical, legal or regulatory
  validation;
- WYE legal or regulatory compliance;
- operational sources for ingredient scoring or nutrient profiling;
- a universal source hierarchy;
- formulas, weights, thresholds, scoring, caps, floors or rankings;
- criticality, coverage, evaluability, confidence or missing-data policy;
- UI content, premium features or personalization;
- an API, runtime, database, migration or application code;
- a release, publication or user-facing deployment.

Required downstream contributors and reviewers remain:

- domain scientific reviewers for scientific applicability and transfer;
- a regulatory specialist for primary or interpretive regulatory sources;
- the data/model steward for identity, artifact, checksum, version and lineage;
- the validation owner for audit fixtures and reproducibility evidence;
- legal review when licensing, confidentiality, regulatory interpretation or
  external claims are material;
- the product owner for later product scope, traceability needs and acceptable
  product-facing limitations, without scientific or regulatory authority.

### J.3 Decision boundary and retained gates

The explicit product-owner approval closes `PSC-OD-021` only for Option B's
governance-model and product-traceability boundary. The reviewed RFC provides:

- a domain-sensitive, non-universal source hierarchy;
- unambiguous conceptual register fields and independent state axes;
- distinct date, cutoff, version, artifact and provenance semantics;
- lifecycle, correction, supersession, withdrawal and historical-retention
  principles;
- conflict, uncertainty, translation and AI boundaries;
- mapping to current WYE artifacts without claiming implementation compliance.

Scientific applicability, regulatory interpretation, legal sufficiency,
source-class procedures, operational source selection, implementation and
release remain subject to their separately accountable reviews and gates. QPS
separation and every other open product-scoring decision remain intact.

### J.4 Gates after the decision

Following the bounded Option B decision, later work must separately provide:

- an implementation RFC and data-model review, if implementation is proposed;
- source-class-specific scientific and regulatory review procedures;
- source onboarding and audit fixtures;
- access, licensing, confidentiality and retention review where applicable;
- impact-analysis procedures for changed sources;
- decision-specific source selection and evidence review;
- independent approval of any product-scoring candidate and golden corpus;
- a separate release gate before runtime or user-facing use.

## Exit state

```text
PSC-OD-021: DECIDED — OPTION B — PRODUCT OWNER APPROVED
approved scope: DOMAIN-SCOPED SOURCE GOVERNANCE MODEL AND PRODUCT TRACEABILITY BOUNDARY ONLY
scientific selection policy: NOT APPROVED
specific scoring sources: NOT SELECTED
source register implementation: NOT PRESENT
database or migration authority: NONE
runtime authority: NONE
QPS candidate effect: NONE
next gate: READ-ONLY REVIEW OF THE PSC-OD-021 DECISION RECORD
```
