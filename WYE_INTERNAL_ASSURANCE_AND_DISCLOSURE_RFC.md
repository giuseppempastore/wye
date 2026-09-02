# WYE Internal Assurance and Disclosure RFC

## Document status

```text
phase: 7.14.13
effective_date: 2026-09-02
status: ADOPTED FOR MVP GOVERNANCE — IMPLEMENTATION GATES OPEN
mvp_assurance: INTERNAL INFORMATIONAL ASSURANCE
product_owner_confirmation_date: 2026-09-02
product_owner_status: CONFIRMED
level_1_completion_status_label: INTERNALLY REVIEWED — NOT INDEPENDENTLY VALIDATED
internal_assurance_package: NOT YET COMPLETE
independent_external_validation: FUTURE / OPTIONAL / NOT PRESENT
certification: FUTURE / OPTIONAL / NOT PRESENT
medical_clinical_regulatory_legal_approval: NOT CLAIMED
runtime_release: NOT YET AUTHORIZED
legal_review: NOT PERFORMED
```

This RFC records the product-owner governance direction for the informational
MVP. It creates no `PSC-OD-*` identifier, closes no existing decision, approves
no formula or numerical result, and authorizes neither runtime nor release.

## 1. Product-owner direction

Effective `2026-09-02`, WYE is directed to provide general, indicative
information about foods. The MVP must not present itself as scientifically,
clinically or regulatorily certified. The documented internal methodology,
traceable sources, deterministic tests, golden cases, proportionate sensitivity
analysis and reviews assisted by Codex/ChatGPT constitute the assurance model
required for the informational MVP.

WYE does not replace physicians, nutritionists, dietitians or other qualified
professionals. It does not provide diagnosis, therapy or personal
recommendations. Independent scientific validation or a genuinely applicable
certification may be considered in the future, but is not a blocking
prerequisite for the informational MVP.

This direction adopts the governance model only. Decisions, methods, formulas,
tests, disclosures and internal artifacts required by this RFC remain open
until separately completed and accepted.

### 1.1 Product-owner confirmation

On `2026-09-02`, the product owner confirmed Internal Informational Assurance
as the MVP governance model. WYE will provide general informational and
indicative indicators only: it will not provide diagnosis or personal advice
and will not guarantee safety or individual suitability. External validation
does not block the MVP, while internal technical, methodological and test gates
remain mandatory. A disclaimer never justifies a false or unsupported claim.

This confirmation does not complete the internal assurance package, close any
`PSC-OD-*` decision, authorize runtime or release, or claim medical, clinical,
regulatory or legal approval.

## 2. Two-tier assurance model

### 2.1 Level 1 — Internal Informational Assurance

Level 1 is mandatory for the informational MVP. Its complete package includes:

- documented, versioned methodology and canonical identity;
- source provenance and immutable decision-use trace;
- deterministic conformance tests and replay;
- consistency and regression review;
- internal golden cases and adversarial cases;
- proportionate sensitivity analysis;
- known-limitations and typed-gap registers;
- a version-impact report;
- explicit separation of zero from missingness;
- a non-numeric `not_computable` outcome;
- separate coverage, confidence and uncertainty;
- data/model steward verification;
- product-owner acceptance for the informational intended use; and
- an auditable record of inputs, review dispositions and acceptance.

Only after this package is complete may an exact methodology candidate use the
status:

```text
INTERNALLY REVIEWED — NOT INDEPENDENTLY VALIDATED
```

That status is not scientific approval, independent validation,
certification, clinical validation or regulatory approval. Codex/ChatGPT may
assist analysis, drafting, consistency checks and review preparation, but is
not an independent reviewer and has no autonomous final authority.

### 2.2 Level 2 — Independent External Validation

Level 2 is future, optional for the informational MVP, not present and not
simulated. Its absence does not block internal drafting, internal decision
closure or an informational MVP release after all applicable Level 1,
technical, data-safety, claim and release gates pass.

Level 2 may become necessary if WYE later pursues stronger clinical or health
claims, declared independent validation, scientific partnerships, genuinely
applicable certification, or professional or regulated uses. This RFC does not
assert that a certifying body applicable to WYE currently exists.

## 3. Canonical gate interpretation

For the MVP, references in earlier canonical documents to a scientific panel
or validation owner denote internal accountable methodology and validation
functions unless the text explicitly describes a historical external-review
artifact. They do not imply an external or independent party.

Historical Phase 7.7 external-review packages, validators, manifests and status
records remain unchanged historical artifacts. They are available for a future
Level 2 process, but their absent approval record is not an MVP blocker.

The following remain blocking for runtime or release as applicable:

- unresolved `PSC-OD-*` decisions required by the exact candidate;
- absent formulas, transformations or canonical numeric execution rules;
- incomplete Level 1 assurance package;
- failed deterministic, regression, golden, adversarial or sensitivity tests;
- incomplete provenance, trace, gap, limitation or impact artifacts;
- unresolved technical reproducibility, data-safety or security gates;
- unaccepted claim and disclosure package;
- missing product-owner acceptance or separate release authorization.

External scientific review is not a blocker for MVP drafting, internal decision
closure or informational release. Runtime and release nevertheless remain
unauthorized today because the internal decisions and artifacts are incomplete.

## 4. Decision mapping and authority

| Decision | Current state | MVP governance effect | Authority boundary |
|---|---|---|---|
| `PSC-OD-001` | `DECIDED` | This RFC applies its general informational intended use and non-personal claims boundary. | Product owner; no reopening. |
| `PSC-OD-005` | `OPEN` | An ingredient mapping may be accepted only after the exact Level 1 package is complete. | Protocol proposer prepares; data/model steward verifies technical reproducibility; product owner accepts MVP use. External review is future/optional. |
| `PSC-OD-019` | `OPEN` | Internal golden, adversarial, sensitivity, robustness and comprehension evidence is mandatory. | Internal validation function plus data/model steward; product owner accepts residual product risk. External independent validation remains optional for MVP. |
| `PSC-OD-020` | `OPEN` | Claims, limitations, disclosure hierarchy and comprehension must be accepted before release. | Product communication review and product owner; separate release authorization remains required. Legal review is not claimed as performed. |
| `PSC-OD-022` | `OPEN` | Personalization and regulated/professional use remain outside the base informational MVP. | Existing privacy, legal and clinical-governance boundary remains applicable to future premium or regulated scope. |

All 22 Product Scoring Contract decisions retain their existing identifiers and
states: `PSC-OD-001`, `002`, `003`, `004` and `021` are `DECIDED`; the other 17
remain `OPEN`. This RFC does not start or close `PSC-OD-006`.

## 5. Claim contract

### 5.1 Permitted candidate claims

- WYE informational and indicative indicator;
- informative assessment based on WYE's internal methodology;
- internal, versioned and traceable score;
- non-personal result;
- disclosed coverage and limitations;
- non-clinical result;
- methodology not independently validated; and
- missing data distinguished from a negative result.

These claims remain candidates until `PSC-OD-020` and release gates are
completed. They must be true for the exact displayed methodology and result.

### 5.2 Prohibited claims

- a food is guaranteed safe or guaranteed dangerous;
- diagnosis, prevention, cure or treatment;
- medical advice or personal dietary recommendation;
- individual suitability or personal risk;
- health guarantee;
- replacement of a physician, nutritionist or dietitian;
- nonexistent certification or independent scientific approval;
- automatic regulatory compliance; or
- personal doses, portions or frequencies.

A disclaimer cannot make a false, misleading or unsupported claim valid.

## 6. Candidate disclaimer contract

These texts are governed candidates, not final UI copy. They have not received
legal review.

### 6.1 Italian — short

> WYE fornisce indicatori informativi e orientativi basati sulla propria
> metodologia interna. Non offre consulenza medica o dietetica personale e non
> garantisce la sicurezza o l'idoneità di un alimento per una persona specifica.

### 6.2 English — short

> WYE provides informational and indicative indicators based on its internal
> methodology. It does not provide personal medical or dietary advice and does
> not guarantee that a food is safe or suitable for a specific person.

### 6.3 Italian — extended

> Le valutazioni WYE sono informative e orientative e derivano da una
> metodologia interna versionata. Fonti, dati o copertura possono essere
> incompleti e la metodologia non è stata validata in modo indipendente. WYE non
> formula diagnosi o terapie e non considera automaticamente allergie,
> intolleranze, patologie, farmaci o altre condizioni individuali. Per decisioni
> personali consulta un medico, nutrizionista, dietista o altro professionista
> qualificato. Verifica sempre l'etichetta e le informazioni aggiornate del
> produttore.

### 6.4 English — extended

> WYE assessments are informational and indicative and are produced using a
> versioned internal methodology. Sources, data or coverage may be incomplete,
> and the methodology has not been independently validated. WYE does not
> provide diagnosis or treatment and does not automatically account for
> allergies, intolerances, medical conditions, medicines or other individual
> circumstances. Consult a physician, nutritionist, dietitian or another
> qualified professional for personal decisions. Always check the label and
> the manufacturer's current information.

### 6.5 Methodology disclosure

Every displayed result must identify the WYE internal score, methodology
version and applicable limitations. Coverage, confidence and uncertainty must
remain separate. `not_computable` is a non-numeric result distinct from zero.
The disclosure must state that independent validation is not present and may be
considered in a future assurance tier.

Candidate placement follows a three-level hierarchy:

1. short disclosure during onboarding and first score display;
2. expanded disclosure in score detail, `not_computable` views, terms and
   allergy/intolerance-sensitive screens; and
3. full methodology disclosure on the Methodology/About page.

Placement does not replace result-specific limitations or source trace.

## 7. Release and change control

Adoption of this RFC does not authorize implementation, runtime, publication or
release. A future release record must bind the exact methodology version,
canonical digest, Level 1 assurance package, open-decision dispositions,
claim/disclosure version, product-owner acceptance, data/model steward check
and release authorization.

Any stronger claim or scope change triggers a new impact analysis and may
activate Level 2, legal, regulatory, privacy or clinical review requirements.

## 8. Current exit state

```text
governance_model: ADOPTED
mvp_assurance_tier: INTERNAL INFORMATIONAL ASSURANCE
internal_assurance_package: NOT YET COMPLETE
external_validation: FUTURE / OPTIONAL / NOT PRESENT
certification: FUTURE / OPTIONAL / NOT PRESENT
legal_review: NOT PERFORMED
runtime: NOT YET AUTHORIZED
release: NOT YET AUTHORIZED
PSC-OD-005: OPEN
product_owner_status: CONFIRMED
Policy_Option_C: PRODUCT-OWNER CANDIDATE DIRECTION — NOT SCIENTIFICALLY OR INDEPENDENTLY VALIDATED
```
