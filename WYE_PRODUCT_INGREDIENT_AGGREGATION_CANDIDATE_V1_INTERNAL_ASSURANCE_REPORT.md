# WYE Product Ingredient Aggregation Candidate V1 — Internal Assurance Report

## Status and boundary

```text
candidate_id: WYE-PRODUCT-INGREDIENT-AGGREGATION-CANDIDATE-V1
candidate_version: 1.0.1-internal
candidate_status: INTERNAL HEURISTIC CANDIDATE — NOT APPROVED FOR RUNTIME OR RELEASE
governance: INTERNAL INFORMATIONAL ASSURANCE
decision_id: PSC-OD-006
decision_status: OPEN
runtime_authority: NONE
release_authority: NONE
external_validation: FUTURE / OPTIONAL / NOT PRESENT
certification: FUTURE / OPTIONAL / NOT PRESENT
```

This is an internal assurance record, not independent validation, scientific
approval, certification, release authorization or runtime authority. The
candidate is a broad informational food-guidance artifact. WYE is not a doctor
and provides no diagnosis, treatment, medical, clinical, personal dietary,
dose, frequency, portion, safety, regulatory-compliance or individual-
suitability advice or guarantee.

## Artifact integrity

The canonical profile sorts object keys recursively, preserves array order,
normalizes strings to NFC, emits compact UTF-8 JSON without BOM, excludes only
`integrity.canonical_digest_sha256`, and hashes those bytes with SHA-256.

| Artifact | Canonical SHA-256 | Replay result |
|---|---|---|
| Candidate | `b131292e09f9c79f9761bfca51efe631c4608ae1b1517335f4c2af73a2280884` | PASS |
| Golden corpus | `68da5fdb6e3d6211bd65505809b0d0054803d5b8d11df720fb49292029be431a` | PASS |

The golden corpus binds the candidate digest and contains 26 synthetic,
abstract cases. AGG-CAND-REV-002 is remediated: every case now carries a
structured `frozen_input`, including a product snapshot, gate trace, duplicate
proxy state, and composition entries with all required replay fields.
Identical canonical input, candidate version and source cutoff have
deterministic status, result and replay identity.

## Candidate algorithm assurance

The candidate is Option E — Evidence-gated staged MVP. It first separates
non-applicable entries, then blocks a numeric output for unavailable product
history, any applicable `not_computable` ingredient, unresolved relationship,
or duplicate/proxy contribution. Only after every applicable entry is
computable, resolved and unique does it calculate:

```text
ingredient_goodness_percent = round_half_even(sum(ingredient_score) / count(applicable entries))
```

The sum is an exact integer and the denominator an exact positive integer;
floating point is forbidden. Rounding occurs once at terminal serialization.
The arithmetic denominator is an eligible-entry count, not a quantity
denominator. Quantity, QUID and list order are disclosure/provenance only: no
missing quantity is converted to zero, absence, equal physical quantity or a
reliable quantity denominator.

AGG-CAND-REV-001 is remediated in version `1.0.1-internal`: equal arithmetic
contribution is an explicit internal per-entry heuristic policy, not an
assumption of equal mass, exposure, risk, nutritional importance or scientific
importance. It is acceptable only for Internal Informational Assurance while
`PSC-OD-006` remains `OPEN`; runtime and release remain unauthorized.

This is a quantity-blind, order-blind and duplicate-sensitive internal
heuristic. It is not externally validated. Any future quantity, order,
deduplication-resolution or final aggregation method needs a separate artifact
and review while `PSC-OD-006` remains `OPEN`.

## Golden corpus recalculation

All 26 cases parse as JSON and can be replayed against the declared gates from
their structured case data and exact rational algorithm: 17 `computable`, 8
`not_computable`, and 1 `non_applicable`. Every composition entry retains
identity, relationship, quantity, support, informational and provenance fields
needed for that internal gate replay.

| Computable cases | Exact numerator / entry count | Expected integer |
|---|---:|---:|
| PAGC-001, 010, 019, 025 | 75 / 1 | 75 |
| PAGC-002, 012, 017, 021–024 | 50 / 1 or 100 / 2 | 50 |
| PAGC-003, 013, 014 | 150 / 3 or 100 / 2 | 50 |
| PAGC-004 | 0 / 1 | 0 |
| PAGC-011 | 25 / 1 | 25 |
| PAGC-026 | 25 / 2 = 12.5 | 12 (half-even) |

`PAGC-004` proves that numeric zero is a valid computable endpoint. Cases
`PAGC-005`, `006`, `008`, `009`, `015`, `016`, `018` and `020` contain no
score member and prove that `not_computable` is neither zero nor an imputed
mean. `PAGC-007` proves that `non_applicable` is separately typed and contains
no score member.

## Separation and adversarial controls

- Coverage and evaluability remain separate from the numeric output. Missing
  quantity is disclosed in `PAGC-005` and `010`, while QUID and order are
  disclosed but unused in `PAGC-011` through `014`.
- Confidence and uncertainty have no numeric effect (`PAGC-021`, `022`).
- Criticality has no hidden veto, cap, floor or override (`PAGC-023`).
- Regulatory status is informational, not goodness (`PAGC-024`).
- Nutrition overlap is excluded from the candidate number (`PAGC-025`); no
  nutrition or overall score is defined.
- Duplicate aliases, shared substance proxies and unresolved parent/child
  relationships are blocked, not double-counted (`PAGC-015`, `016`, `018`).

Hazard, exposure, risk, criticality, confidence, uncertainty, coverage,
missingness, regulatory status, ontology labels and informational flags are
structurally disclosed and have numeric effect `NONE`.

## Mechanical and governance checks

- Candidate and corpus JSON: valid.
- AGG-CAND-REV-001 remains remediated; per-entry contribution is an internal
  heuristic policy, not physical equal weighting.
- AGG-CAND-REV-002 remediated; all 26 cases have structured frozen inputs and
  all composition entries have required replay fields.
- Canonical digest replay: PASS for both artifacts.
- Candidate status and corpus status: internal only; no runtime or release
  authority.
- Disclaimers and non-claims: present.
- `PSC-OD-005`, `PSC-OD-006` and `PSC-OD-013` through `PSC-OD-019`: `OPEN`.
- No decision is closed by this candidate package.
- External validation and certification: future, optional and not present.

## Conclusion

The package is ready only for a subsequent internal candidate review. It does
not decide `PSC-OD-006`, authorize a final aggregation method, start nutrition
or overall scoring, or authorize implementation, API, UI, database, runtime,
release, commit or push.
