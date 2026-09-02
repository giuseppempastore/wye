# Nutrition Score Candidate V1 — Internal Assurance Report

## Status

```text
candidate_version: 1.0.0-internal
status: INTERNAL HEURISTIC CANDIDATE — NOT APPROVED FOR RUNTIME OR RELEASE
governance: Internal Informational Assurance
decision_status: PSC-OD-007 through PSC-OD-012 OPEN
runtime_authority: NONE
release_authority: NONE
external_validation: FUTURE / OPTIONAL / NOT PRESENT
certification: FUTURE / OPTIONAL / NOT PRESENT
```

The candidate produces only a future `nutrition_goodness_percent`; it does
not produce ingredient scores or an overall score. It is a broad informational
food-guidance candidate, not medical, clinical, therapeutic, personal dietary,
safety, healthiness, regulatory, certification or individual-suitability advice.

## Digest and corpus checks

Canonical JSON sorts keys recursively, preserves arrays, normalizes strings to
NFC, emits compact UTF-8 without BOM and excludes only the integrity-digest
member.

| Artifact | Canonical SHA-256 |
| --- | --- |
| Candidate | `954b05d9decaf1e94e461a72377175a783224eddefe09d2bfe3e8a2bda7e7aaf` |
| Golden corpus | `49a5df21f0e9e7477edb238b8fe5dfa41cabb2184363122021bb9b1680e470be` |

The corpus contains 30 synthetic cases: 25 `computable`, 4
`not_computable` and 1 `non_applicable`. Every case holds a complete,
standalone `frozen_input` with snapshot, source, cutoff, category, basis,
serving, nutrient, conversion, evidence-state, provenance and gate-trace
fields. No case inherits a base profile or uses an override as its only data.

## Completed remediation assurance

Each case was replayed from its own `frozen_input`. Computable outputs match
the declared exact-integer lookup tables and bounded formula; the corpus
exercises declared salt and an actual exact sodium-to-salt conversion in
`NSGC-014`: 120 mg sodium × 2.5 = 300 mg derived salt. The conversion is an
internal heuristic candidate value only, not externally validated or approved.
The corpus also covers both allowed bases, optional fibre/protein, ambiguous
serving disclosure, low confidence and high uncertainty without score
modifiers, and a valid numeric zero.

The output schema requires an explicit `nutrition_goodness_percent: null` and
a typed `reason_code` for every `not_computable` or `non_applicable` output.
Computable outputs are integer lookup results in 0..100; no rounding step is
performed. A numeric zero remains a valid computed result rather than a
missing-data sentinel. Mandatory missing, conflicting and non-comparable data
fail closed; there is no missing-data imputation or numeric fallback.

Confidence, uncertainty, coverage, missingness and evaluability remain
disclosures or gates separate from the nutrition number. Ingredient-side
signals, including the overlap fixture, are excluded from the nutrition
calculation; no ingredient/nutrition double-counting and no overall score are
introduced.

## Limits and governance

This is Internal Informational Assurance only. The candidate does not authorize
runtime, release, API, UI, database, migration or production behavior. It makes
no external-validation, scientific, regulatory, certification, safety,
healthiness or individual-suitability claim.

WYE gives broad informational food guidance only. It is not a doctor and gives
no diagnosis, treatment, medical, clinical, therapeutic or personal dietary
advice, and no dose, frequency or portion recommendation. External validation
and certification are future, optional and not present.

```text
PSC-OD-005: OPEN
PSC-OD-006: OPEN
PSC-OD-007 through PSC-OD-012: OPEN
PSC-OD-013 through PSC-OD-019: OPEN
PSC-OD-020: OPEN
PSC-OD-022: OPEN
runtime: NOT AUTHORIZED
release: NOT AUTHORIZED
```
