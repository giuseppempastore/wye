# WYE Ingredient Score Candidate V1 — Internal Assurance Report

## Document status

```text
phase: 7.15.2
candidate_id: WYE-INGREDIENT-SCORE-CANDIDATE-V1
candidate_version: 1.0.1-internal
status: INTERNAL HEURISTIC CANDIDATE — NOT INDEPENDENTLY VALIDATED
assurance: INTERNAL INFORMATIONAL ASSURANCE
scientific_approval: NOT CLAIMED
independent_validation: NOT PRESENT
certification: NOT PRESENT
clinical_validity: NOT CLAIMED
regulatory_approval: NOT CLAIMED
runtime_authority: NONE
release_authority: NONE
source_cutoff: 2026-09-02
report_date: 2026-09-02
```

This report records deterministic internal conformance and challenge checks for
the first exact numerical candidate. Passing these checks makes the package
eligible for internal candidate review only. It does not establish scientific
approval, independent validation, certification, clinical validity, regulatory
approval, runtime suitability, or release readiness.

## 1. Executive summary

The candidate uses exactly one score-bearing component:
`DIM-CAND-INGREDIENT-FAVOURABILITY`. A governed internal ordinal conclusion
supplies an integer level from 0 through 4. The exact transform maps those five
levels to `0`, `25`, `50`, `75`, and `100`.

The product owner selected Mapping Option A — reviewed ordinal lookup with
bounded anchors — as the MVP candidate direction. Policy Option C remains the
layered state model that separates upstream data, evidence, support,
informational, criticality, evaluability, and numerical output layers. Mapping
Option B remains a future possible multi-attribute development and is not
claimed by this single-construct candidate.

No second numeric component exists. Confidence, uncertainty, coverage,
missingness, mapping resolution, evidence state, regulatory status, ontology
labels, hazard, exposure, risk, criticality, and nutrition-property information
do not enter the number. Applicability, resolved identity, conclusion validity,
and availability of the ordinal level are explicit eligibility/evaluability
gates; a failed indispensable gate produces a non-numeric outcome.

The local assurance run parsed both JSON artifacts, independently replayed all
30 expected cases, checked ordinal relations, boundaries, monotonicity,
sensitivity, declared non-influence pairs, nutrition double-counting exclusion,
and canonical digests. All executed package checks passed. The package remains
an internal heuristic candidate with material source, judgment, comprehension,
impact, and external-validation gaps.

## 2. Scope and non-claims

### 2.1 Intended scope

- ingredient-level output in the inclusive range `0..100`;
- general, non-personal informational use;
- one exact governed ingredient-favourability question and compatible context;
- version-bound score, disclosure, provenance, and replay identity; and
- Internal Informational Assurance for candidate review.

### 2.2 Explicit non-claims

The score is not:

- a clinical or medical model;
- a safety, healthfulness, efficacy, risk, or individual-suitability guarantee;
- personal, therapeutic, dietary, dose, or portion advice;
- a regulatory conclusion or proof of compliance;
- a confidence, uncertainty, evidence-quality, hazard, exposure, or risk value;
- a nutrition-property score;
- independently validated, certified, scientifically approved, or clinically
  valid; or
- approved for runtime, UI, aggregation, release, or `PSC-OD-006`.

Disclaimers do not supply evidence and must never be used to justify an
unsupported inference.

## 3. Internal assumptions

| Assumption | Candidate treatment | Assurance consequence |
|---|---|---|
| A governed favourability conclusion can be represented by five ordered anchors for the exact question. | Integer level `0..4`. | Requires human methodological review and future evidence-based calibration. |
| Equal visual spacing is useful for a first transparent internal candidate. | Each adjacent level differs by 25 points. | Spacing is heuristic and is not an empirical interval or effect size. |
| Only one score-bearing construct is supported by the selected bundle. | No weights, compensation, or numeric interactions. | Prevents artificial dimensions but limits expressiveness. |
| The MVP lookup is not a multi-attribute Mapping Option B model. | Mapping Option A is the candidate direction; Option B remains future. | Prevents a one-level lookup from being presented as a multi-attribute realization. |
| Resolved identity and a valid conclusion are indispensable. | Failed gate emits `not_computable` without a score. | May suppress outputs where production governance has not resolved inputs. |
| Non-applicability is semantically distinct from missingness. | Emits `non_applicable` without a score. | Comparisons across different perimeters are forbidden. |
| Support and informational layers must remain visible but non-numeric. | Separate disclosures only. | Product presentation must not hide those qualifications. |
| Criticality has no V1 cap, floor, veto, override, or score effect. | Separate candidate warning disclosure. | Any future effect needs a new governed candidate and no-double-counting proof. |

These are internal product-method assumptions, not scientific findings.

## 4. Exact model

### 4.1 Formula

Let `L` be the governed favourability level after every gate passes, with `L` an
integer in the closed interval `[0,4]`.

```text
raw_exact = (100 × L) / 4
bounded   = clip(raw_exact, 0, 100)
score     = round_half_even(bounded, 0 decimal places)
```

Equivalent frozen lookup:

| `L` | Ordinal anchor | Score |
|---:|---|---:|
| 0 | least favourable within the governed reference frame | 0 |
| 1 | less favourable within the governed reference frame | 25 |
| 2 | intermediate favourability within the governed reference frame | 50 |
| 3 | more favourable within the governed reference frame | 75 |
| 4 | most favourable within the governed reference frame | 100 |

All intermediate arithmetic is exact integer/rational arithmetic. Floating
point is forbidden. Clipping is explicit but cannot activate for a schema-valid
level. Terminal round-half-to-even is frozen but has no numerical effect because
all five valid rationals are integers.

### 4.2 Components, weights, and interactions

- Score-bearing components: one.
- Weights: none.
- Compensation: not applicable; there is no second component.
- Numeric interactions: none.
- Support interaction: only ordered applicability and typed validity gates.
- Critical cap, floor, veto, override, and zero override: none.
- Nutrition-property contribution: excluded.

This is a Mapping Option A reviewed ordinal lookup over a single governed
construct. It is not a realization of Mapping Option B's multi-attribute
aggregation family.

The equal 25-point steps are an internal interface convention. The candidate
does not claim that real-world differences between adjacent judgments are equal.

## 5. Inputs, gates, and outputs

### 5.1 Canonical input

The canonical input binds:

- abstract subject, exact question, and general non-personal context keys;
- applicability;
- identity mapping state;
- typed conclusion validity;
- nullable favourability level;
- support disclosures for coverage, confidence, uncertainty, evidence state,
  missingness, mapping resolution, hazard, exposure, risk, and criticality;
- informational regulatory status, multi-label ontology, and nutrition-overlap
  state; and
- source cutoff, source identities, judgment identity, and input version.

Personal, clinical, therapeutic, individual dietary, dose, and portion
information is forbidden.

### 5.2 Gate order

1. `non_applicable` exits with no score.
2. A mapping state other than `resolved` exits as `not_computable`.
3. A conclusion state other than `valid` exits as `not_computable`.
4. A missing, non-integer, or out-of-range level exits as `not_computable`.
5. Only an input passing all prior gates reaches the formula.

Confidence is not an evaluability proxy. Coverage alone is not a gate. Optional
missingness remains a disclosure. An indispensable absence must be represented
by the exact failed gate, never by a numerical penalty or fallback.

### 5.3 Output states

| Evaluability | Score member | Meaning |
|---|---|---|
| `computable` | Required integer `0..100` | Exact V1 formula was evaluated. |
| `not_computable` | Forbidden | A named indispensable gate failed. |
| `non_applicable` | Forbidden | The question is outside the applicable perimeter. |

A computable zero is a genuine level-0 endpoint. It is distinct from both
`not_computable` and `non_applicable`.

## 6. Golden corpus

The corpus contains 30 synthetic or abstract cases and no claims about real
people or specific foods.

Each of the 30 `expected_output` objects is explicitly a formula-and-gate
projection governed by `WYE-INGREDIENT-SCORE-GOLDEN-EXPECTED-PROJECTION-V1`.
It intentionally does not duplicate the full output contract. Three separate
`output_contract_fixtures` cover the complete structural output and disclosure
contract for `computable`, `not_computable`, and `non_applicable` outcomes.

| Partition | Cases | Purpose |
|---|---:|---|
| Calibration | 5 | Freeze the five endpoints and basic monotonic chain. |
| Internal holdout | 4 | Challenge non-applicability and level sensitivity. |
| Golden regression | 2 | Exact duplicate-input replay. |
| Adversarial | 19 | Missingness, proxy leakage, risk separation, criticality, and double counting. |
| **Total** | **30** | Internal candidate assurance only. |

Outcome distribution:

| Outcome | Cases |
|---|---:|
| `computable` | 25 |
| `not_computable` | 4 |
| `non_applicable` | 1 |
| computable score `0` | 1 |

Coverage includes lower and upper bounds, intermediate anchors, monotonicity,
non-applicability, missing indispensable inputs, zero distinction, low coverage,
low confidence, high uncertainty, partial mapping, `history_unavailable`, hazard
without exposure, `risk_not_computable`, candidate criticality, regulatory
status, ontology multi-label, nutrition overlap, double counting, sensitivity,
regression, and deterministic replay.

The `internal_holdout` partition is designated for review separation but was
created in the same consolidated generation as the formula. It is therefore not
claimed to be independently authored, independently sealed, or evidence of
generalization. A reviewer should seal or replace it before any later acceptance
decision.

## 7. Tests executed and results

Tests were local, non-mutative package checks. No application tests, migrations,
network calls, or runtime integrations were executed.

| Check | Result | Evidence summary |
|---|---|---|
| JSON parse | PASS | Candidate and corpus parsed as JSON. |
| Candidate/corpus identity references | PASS | IDs, versions, and embedded candidate digest agree. |
| Case contract | PASS | 30 unique, ordered case IDs; all mandatory case fields and judgment labels present. |
| Golden expected-output projection | PASS | All 30 expected outputs conform to the declared formula-and-gate projection schema. |
| Full output contract fixtures | PASS | Three full structural fixtures cover computable, not-computable, and non-applicable outputs, including required disclosures, provenance, and replay fields. |
| Formula replay | PASS | Recalculated score equals expected score for all 25 computable cases. |
| Non-numeric outcomes | PASS | All 4 `not_computable` and the non-applicable case omit the score member. |
| Zero distinction | PASS | `GC-001` emits computed `0`; `GC-012` is `not_computable` with no score. |
| Range and integer output | PASS | Every emitted score is an integer in `0..100`. |
| Clipping and rounding | PASS | Exact valid inputs remain within bounds and integral; no clipping or rounding change occurs. |
| Ordinal relations | PASS | Every referenced case exists and every declared numeric relation replays. |
| Bounded monotonicity | PASS | Levels `0,1,2,3,4` replay as `0,25,50,75,100`. |
| Component sensitivity | PASS | One-level changes in `GC-022`–`024` produce exact +25 changes. |
| Coverage non-influence | PASS | `GC-006` equals the level-2 baseline. |
| Confidence non-influence | PASS | Low/high confidence pair `GC-007`/`GC-029` remains equal. |
| Uncertainty non-influence | PASS | `GC-008` equals the level-2 baseline. |
| Optional missingness non-influence | PASS | `GC-028` equals the level-3 baseline. |
| Regulatory-status non-influence | PASS | `GC-017` and `GC-018` remain equal. |
| Ontology-label non-influence | PASS | Multi-label `GC-019` equals the level-2 baseline. |
| Hazard non-influence | PASS | Hazard-without-exposure `GC-014` equals the level-3 baseline. |
| Exposure/risk non-influence | PASS | `GC-015` and `GC-030` equal the level-3 baseline. |
| Criticality non-influence | PASS | Candidate warning `GC-016` equals the level-3 baseline. |
| Nutrition double-counting | PASS | `GC-020`/`GC-021` remain equal; overlap metadata contributes nothing. |
| Deterministic duplicate replay | PASS | `GC-025` and `GC-026` have the same canonical input digest and score. |
| Required corpus coverage tags | PASS | Every mandated semantic category is represented. |
| Canonical candidate digest replay | PASS | Recomputed digest equals the embedded candidate digest. |
| Canonical corpus digest replay | PASS | Recomputed digest equals the embedded corpus digest. |

These PASS results demonstrate internal consistency with the frozen candidate.
They do not demonstrate that the ordinal judgments or spacing are scientifically
correct.

## 8. Boundary analysis

- Valid lower boundary: level 0 maps to score 0.
- Valid upper boundary: level 4 maps to score 100.
- Valid interior points: levels 1, 2, and 3 map to 25, 50, and 75.
- Invalid or missing level: no formula execution and no score member.
- Valid-domain clipping: never activates.
- Valid-domain rounding: never changes a value.
- Overflow: specified as an error; silent wrapping or saturation is forbidden.

Endpoint wording is deliberately ordinal and protocol-relative. Neither 0 nor
100 carries a safety, health, risk, clinical, or individual interpretation.

## 9. Monotonicity and sensitivity analysis

The complete valid domain was enumerated. The score sequence is strictly
increasing:

```text
L:      0   1   2   3    4
score:  0  25  50  75  100
delta:     +25 +25 +25 +25
```

Consequently, a one-level increase cannot decrease the score, and the local
sensitivity is exactly 25 score points per level everywhere in the valid domain.
There are no other numeric components to perturb.

This property is bounded to compatible inputs under the same question and
context. It does not authorize universal ordering across questions, versions,
forms, uses, populations, or applicability perimeters. The 25-point sensitivity
is a property of the chosen heuristic transform, not an empirical estimate.

## 10. Support non-influence and double counting

Paired cases hold the sole score-bearing level fixed while varying support or
informational fields. The score remains unchanged for confidence, uncertainty,
coverage, optional missingness, evidence state, regulatory status, ontology
labels, hazard, exposure, risk, criticality, and nutrition-overlap metadata.

Mapping resolution and typed conclusion validity are not numeric components.
They may change evaluability only through named indispensable gates. This gate
effect must never be reported as a score penalty.

The nutrition overlap cases use explicit `excluded` or
`detected_and_excluded` states. No nutrition property, derived nutrition value,
shared-evidence duplicate, or hidden second component enters the formula.

## 11. Determinism, replay, and integrity

Candidate canonical digest:

```text
a0efffbed58a2d5c8c5cc996518e7b155b02d57b29fd5be465418dc1f08fa2f3
```

Golden-corpus canonical digest:

```text
3682fdaf249b25ca3f30862c5cd1ce6347b831b6bee7c17adafa39db4f4c68bc
```

Both use `WYE-CANONICAL-JSON-ASCII-KEYS-V1`: Unicode NFC strings, recursively
sorted object keys, preserved array order, minimal integer serialization, UTF-8
without BOM, no insignificant whitespace, and SHA-256. Each artifact excludes
only its own `integrity.canonical_digest_sha256` member from its digest scope.

The formula uses exact arithmetic and a single terminal rounding locus. The
duplicate replay pair produced equal canonical input identity and equal output.
Historical replay still requires immutable production inputs and artifacts;
none are authorized by this package.

## 12. `not_computable` analysis

The corpus exercises three non-computability causes:

- partial identity mapping;
- mapping history unavailable; and
- missing level or invalid favourability conclusion.

All such cases omit the score member. None emits zero, a midpoint, a null score,
an imputed value, or a missingness penalty. Non-applicability has a separate
outcome and also omits the score member.

Confidence labels do not control computability. A high-confidence but invalid
conclusion remains `not_computable`; a low-confidence but explicitly valid
conclusion remains computable with confidence disclosed separately.

## 13. Limitations and source gaps

- No independent reference judgments or external benchmarks are present.
- The ordinal anchors and equal spacing have not been empirically calibrated.
- The candidate is an Option A lookup and does not validate or represent a future multi-attribute Option B model.
- Synthetic cases do not represent production prevalence, ambiguity, source
  drift, cultural context, language variation, or edge-case frequency.
- The designated holdout was not independently sealed or authored.
- No named human reviewer has yet accepted each reference judgment.
- No disagreement register, inter-reviewer analysis, or adjudication record is
  present beyond the case rationales.
- No user-comprehension study has tested endpoint, `not_computable`, warning, or
  uncertainty interpretation.
- No product-distribution impact, subgroup impact, or production-data bias
  analysis has been performed.
- No external validation, certification, clinical validation, or regulatory
  review is present.
- No runtime schema, database, API, UI, telemetry, aggregation, or release path
  is authorized.
- Source evidence after the `2026-09-02` cutoff is outside this version.

These gaps constrain claims and acceptance. They must not be papered over with
disclaimers.

## 14. Disclosure mapping

| Model concern | Required disclosure |
|---|---|
| Candidate authority | `INTERNAL HEURISTIC CANDIDATE — NOT INDEPENDENTLY VALIDATED` |
| Intended use | General, non-personal, ingredient-level informational indicator. |
| Score meaning | Protocol-relative favourability under the exact versioned WYE question. |
| Non-claims | No clinical, medical, safety, healthfulness, risk, regulatory, or individual-suitability claim. |
| Support state | Coverage, confidence, uncertainty, evidence state, missingness, and mapping resolution shown separately. |
| Risk separation | Hazard, exposure, and risk shown separately and never inferred from the score. |
| Criticality | Separate warning disclosure with no V1 cap, floor, veto, or override. |
| Informational layers | Regulatory statuses and ontology labels identified as informational only. |
| Nutrition overlap | Explicitly excluded to prevent double counting. |
| Non-computability | Named reason code and no score member. |
| Version/provenance | Candidate ID/version/digest, source cutoff, input/output digests, and source/judgment trace. |
| External assurance | Future, optional, and not present. |
| Authority | No runtime or release authorization. |

## 15. Internal assurance checklist

- [x] Exact formula and sole score-bearing component frozen.
- [x] Weights, compensation, interactions, clipping, and rounding declared.
- [x] Canonical input, output, and disclosure contracts defined.
- [x] Zero distinguished from non-computability.
- [x] Support, informational, risk, and criticality layers kept non-numeric.
- [x] Nutrition-property scoring excluded.
- [x] Thirty synthetic/abstract reference cases provided.
- [x] Formula, range, boundaries, monotonicity, sensitivity, and replay checked.
- [x] Declared non-influence and double-counting cases checked.
- [x] Canonical serialization and content digests replayed.
- [x] Known limitations and forbidden interpretations recorded.
- [ ] Human methodology owner review completed.
- [ ] Human review of every AI-assisted reference judgment completed.
- [ ] Independently sealed or replacement internal holdout reviewed.
- [ ] Disagreement and adjudication register completed.
- [ ] Representative production-like impact and bias analysis completed.
- [ ] User-comprehension review completed.
- [ ] Product owner accepts the exact candidate and residual product risk.
- [ ] Runtime authority granted; deliberately not requested here.
- [ ] Release authority granted; deliberately not requested here.

Unchecked items do not negate the executed conformance results. They prevent this
report from being interpreted as final candidate acceptance or release evidence.

## 16. Decision state

```text
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

The product-owner direction selects the bundle as a candidate direction and
authorizes preparation of this exact package. It closes no decision and accepts
neither the numerical candidate nor residual product risk.

For the MVP mapping direction, the product owner selected Option A lookup with
bounded anchors. Policy Option C remains selected for layered-state separation;
Option B remains a future possible multi-attribute development.

## 17. Required work before runtime or release

At minimum, a later governed process must:

1. perform an independent-from-generator read-only candidate review;
2. assign accountable human owners and review every reference judgment;
3. seal or replace the designated holdout before using it as acceptance evidence;
4. complete disagreement, source-gap, robustness, impact, bias, and
   comprehension analysis on representative non-personal data;
5. decide whether the ordinal anchors and equal spacing are acceptable or must
   be revised;
6. resolve or formally accept every still-open decision in the authorized
   governance process;
7. define downstream aggregation only through a future `PSC-OD-006` process;
8. separately design and review any runtime, API, database, UI, monitoring,
   rollback, and version-migration behavior; and
9. obtain distinct runtime and release authority.

External validation remains future and optional for the informational MVP. It
is not present and is not replaced by this internal report.

## 18. Internal assurance conclusion

The exact candidate and corpus are internally consistent, deterministic, and
transparent under their declared heuristic assumptions. All executed local
package checks passed, and no prohibited dimension leaked into the number.

The appropriate status is:

`READY FOR INTERNAL CANDIDATE REVIEW — NOT ACCEPTED FOR RUNTIME OR RELEASE`

This conclusion is Internal Informational Assurance only.
