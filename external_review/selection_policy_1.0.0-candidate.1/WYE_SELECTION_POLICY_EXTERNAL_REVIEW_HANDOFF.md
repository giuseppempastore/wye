# WYE Phase 7.7.3 — External scientific review handoff

Status:

```text
HANDOFF READY — HUMAN REVIEW REQUIRED
candidate: frozen, not scientifically approved, not published
repository gate: EXTERNAL SCIENTIFIC APPROVAL REQUIRED
```

This document is the human-facing entry point for an independent scientific
review of the first WYE evidence-selection policy candidate. It organizes the
review and provides a declaration form. It does not restate or replace the
canonical policy, golden corpus, or detailed scientific review package, and it
does not itself record an approval.

## 1. Review purpose

Phase 7.7 is preparing a deterministic policy for deciding which findings from
a sealed evidence snapshot may enter a later, separately governed scientific
synthesis. This review asks whether the concrete scientific choices in the
first narrow candidate are appropriate for that declared use.

Software checks have established that the candidate and its test corpus are
stable and internally deterministic. Those checks cannot establish scientific
validity. A scientifically qualified external reviewer must independently
assess the proposed evidence channel, mappings, applicability choices,
contribution roles, claims, and scientific golden-case outcomes.

## 2. Exact controlled review subject

The review applies only to this exact pair of frozen artifacts:

| Item | Controlled identity |
|---|---|
| Candidate key | `efsa_qps_evidence_selection` |
| Candidate version | `1.0.0-candidate.1` |
| Candidate schema | `wye_scientific_evidence_selection_policy / 1` |
| Candidate SHA-256 | `d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615` |
| Golden corpus schema | `wye_selection_golden_corpus_manifest / 1` |
| Golden case count | `28` |
| Golden corpus SHA-256 | `db535148ece59c222eaac2004594ae19a1e00a2e65448c42a4804dd8cefd8b15` |
| Freeze state | Candidate and golden corpus frozen; external scientific approval absent |

Any change to the candidate bytes, a golden expected outcome, or the manifest
creates a different review subject and requires a new version/digest and a new
review. The candidate suffix is intentional: `1.0.0-candidate.1` is not the
published version `1.0.0`.

## 3. Authoritative materials and reading order

The reviewer does not need to read application code, database migrations, or
Git history. Use this reading order:

1. this handoff for scope, questions, procedure, and declaration;
2. `WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md` for the detailed
   decision matrix, scientific review cards, source table, claims, and case
   approval matrix;
3. `WYE_SELECTION_GOLDEN_CASES.md` for the 28 fixtures and expected outcomes;
4. `WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json` to identify the exact corpus;
5. `WYE_SELECTION_POLICY_CANDIDATE_V1.json` as the exact machine-readable
   candidate under review.

`WYE_SELECTION_POLICY_FREEZE.md`, `WYE_EVIDENCE_SELECTION.md`,
`WYE_SCORING_PROTOCOL.md`, and `WYE_SCORING_EXECUTION_MODEL.md` are available
for technical or architectural context. If a summary in this handoff appears
to conflict with the controlled artifacts, the controlled candidate, corpus
manifest, golden cases, and detailed review package govern; the conflict must
be reported rather than resolved informally.

## 4. Scientific scope

The candidate is deliberately narrow. It concerns finding-level EFSA QPS list
evidence for an exact substance target. It proposes that a finding passing all
structural, provenance, lifecycle, temporal, representation, target, and
reviewed applicability gates may enter later scientific synthesis in the
scoped regulatory-status and qualification channel.

The external scientific reviewer is asked to assess:

- admission of the exact EFSA QPS source/dataset for the declared claim;
- the QPS evidence-channel and evidence-type mapping;
- the meaning and allowed use of `qps_status` and `qps_qualification`;
- whether null population, route, and duration are correctly treated as not
  applicable at this QPS taxonomic-unit selection boundary;
- the proposed scientific-date precedence;
- treatment of unknown evidence dependency;
- the proposed scientific contribution role;
- the intended claims and explicit non-claims;
- the scientific appropriateness of the golden expected outcomes.

The candidate does not claim that QPS establishes product safety, that a QPS
qualification is satisfied for a particular product, that selected evidence
proves safety or harm, or that any source has a numerical quality weight.
Scientific conflict interpretation remains a later synthesis responsibility;
selection preserves otherwise eligible conflicting findings.

## 5. Out of scope

This review does not ask the reviewer to approve:

- Python or application implementation quality;
- database or migration architecture;
- UI/UX, DevOps, Git workflow, or deployment practice;
- deterministic hashing or test-framework mechanics;
- a future selector implementation;
- evidence synthesis, ingredient projection, or product assessment runtime;
- product safety, authorization, exposure, or consumer-risk conclusions;
- a future numerical product score;
- formulas, weights, thresholds, or score ranges.

The reviewer may report a technical concern discovered during review, but a
technical concern is not a substitute for the requested scientific decisions.

## 6. Scientific review questions

For every row, select exactly one response:

```text
acceptable | changes_required | unacceptable
```

`acceptable` means the exact current candidate value is scientifically
acceptable for its declared narrow scope. `changes_required` means the current
candidate is not approvable as-is but may become acceptable after a specified
change and a new digest-bound review. `unacceptable` means the proposed choice
should not be used for the declared scope.

| Canonical Category C identity | Question | Response | Rationale/reference |
|---|---|---|---|
| `efsa_qps_channel_admission` | Is admitting `efsa/efsa_qps` appropriate for the candidate's limited later-synthesis claim, without implying product safety or source precedence? | __________ | __________ |
| `qps_evidence_channel_mapping` | Is mapping the QPS recommendation/list evidence to the scoped `regulatory_status_and_qualification` channel and `qps_list_entry` type scientifically appropriate? | __________ | __________ |
| `qps_status_endpoint_mapping` | Does the proposed `qps_status` endpoint preserve the meaning of QPS recommendation status without overstating it? | __________ | __________ |
| `qps_qualification_endpoint_mapping` | Does the proposed `qps_qualification` endpoint preserve qualification as a condition/context without implying that a product satisfies it? | __________ | __________ |
| `population_null_not_applicable_qps_taxonomic_unit` | Is null population correctly interpreted as not applicable for this exact taxonomic-unit QPS question rather than as unresolved? | __________ | __________ |
| `scientific_date_precedence` | Is assessment publication date first, then release date, an appropriate scientific-date precedence for the cutoff decision? | __________ | __________ |
| `route_duration_not_applicable` | Are route and duration correctly not applicable, rather than unknown or optional, for this QPS-only selection question? | __________ | __________ |
| `dependency_unknown_contributing` | May an otherwise eligible finding with unknown dependency remain contributing while its lack of proven independence stays explicit? | __________ | __________ |
| `scientific_contribution_role` | Is the proposed contributing role appropriate for eligible QPS status and qualification findings entering later synthesis? | __________ | __________ |
| `scientific_claims_and_non_claims` | Are the intended claim and explicit non-claims scientifically accurate, sufficiently narrow, and resistant to safety overinterpretation? | __________ | __________ |
| `scientific_golden_oracles` | Are all scientific-review-required golden outcomes appropriate consequences of the candidate policy? | __________ | __________ |

These eleven identities are the closed, canonically ordered Category C set for
this gate. Do not rename, reorder, add, or remove an identity on the review
form. A requested semantic change must instead produce a revised candidate and
new review subject.

## 7. Golden corpus review instructions

The golden corpus is an independently authored set of 28 controlled cases. It
exists to make the candidate's consequences concrete before implementation.
It is not output generated by selector code.

The corpus classifies 18 cases as `TECHNICAL` and 10 as
`SCIENTIFIC-REVIEW-REQUIRED`. No case is currently
`SCIENTIFIC-APPROVED`. The scientific cases are:

1. `GC-ELIGIBLE-QPS`;
2. `GC-RELEASE-VALIDATED`;
3. `GC-RUN-SUCCEEDED`;
4. `GC-ENDPOINT-MAPPED`;
5. `GC-ENDPOINT-UNKNOWN`;
6. `GC-POPULATION-NOT-APPLICABLE`;
7. `GC-POPULATION-UNKNOWN`;
8. `GC-DEPENDENCY-UNKNOWN`;
9. `GC-CONFLICT-RETAINED`;
10. `GC-POLICY-VERSION-SENSITIVE`.

For each scientific case in `WYE_SELECTION_GOLDEN_CASES.md`:

1. read the shared fixture and the case-specific mutation;
2. assess whether the expected included/excluded/deferred decision is
   scientifically appropriate under the exact candidate;
3. assess the primary reason, contribution role, and manifest state;
4. confirm that the rationale respects the intended claims and non-claims;
5. record `acceptable`, `changes_required`, or `unacceptable`, with a precise
   rationale and source reference where useful.

Review the remaining technical cases for any scientific consequence the
classification may have missed, but do not treat passing tests as proof that
an expected outcome is scientifically correct. Do not edit expected outcomes
in place. A requested change must identify the affected case key and proposed
scientific correction so that a new candidate/corpus can be governed.

## 8. Decision semantics

Choose exactly one overall decision after completing the scientific questions
and golden-case review:

- `approved`: the reviewer has assessed the exact candidate and exact golden
  corpus and accepts every mandatory Category C item as written. This is the
  only decision that can make the repository's external scientific approval
  gate valid after a separate conforming approval record is supplied.
- `changes_requested`: the exact review subject is not approved as-is; the
  reviewer identifies specific changes needed. The current candidate stays
  frozen, unapproved, and blocked. Any revision requires new bytes, identity,
  impact analysis, and review.
- `rejected`: the exact review subject is scientifically unacceptable for the
  declared scope. The candidate stays frozen, unapproved, and blocked.

A partial set of acceptable items never equals overall approval. Validation
owner and release approver responsibilities remain separate from the external
scientific-review decision.

## 9. Human reviewer declaration

This section is a human-readable working declaration. Completing it does not
create the production approval JSON and does not unlock the repository gate.

```text
Reviewer full name or stable professional identity:
  __________________________________________________________________________

Professional role and qualification:
  __________________________________________________________________________

Organization or affiliation (if applicable):
  __________________________________________________________________________

Review date/time (UTC preferred):
  __________________________________________________________________________

Review subject confirmed:
  [ ] policy key: efsa_qps_evidence_selection
  [ ] version: 1.0.0-candidate.1
  [ ] candidate SHA-256:
      d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615
  [ ] all eleven Category C questions completed

Golden corpus confirmed:
  [ ] 28 cases reviewed at the appropriate scientific/technical boundary
  [ ] golden corpus SHA-256:
      db535148ece59c222eaac2004594ae19a1e00a2e65448c42a4804dd8cefd8b15

Overall decision — select exactly one:
  [ ] approved
  [ ] changes_requested
  [ ] rejected

Decision rationale / notes, or immutable notes reference:
  __________________________________________________________________________
  __________________________________________________________________________
  __________________________________________________________________________

Signature or governed audit-system reference:
  __________________________________________________________________________
```

The completed review should retain the per-question responses from section 6
and the case-level judgments from section 7 as supporting review evidence.

## 10. Recording the decision

After the human review is complete, an authorized external governance process
must separately encode the decision in:

```text
WYE_SELECTION_POLICY_EXTERNAL_APPROVAL.json
```

The record must follow the closed
`wye_selection_policy_approval_record / 1` shape in
`WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md`, bind the exact candidate
and golden-corpus digests, carry the real reviewer identity and governed audit
reference, and pass the deterministic Phase 7.7.2 validator.

The human-readable declaration alone does not unlock the gate. WYE code,
tests, CI, AI, fixtures, and bootstrap tooling must never fabricate the
reviewer, the decision, or the production JSON record. Until a real conforming
record exists, the derived state remains:

```text
EXTERNAL SCIENTIFIC APPROVAL REQUIRED
```

## 11. Neutrality and current boundary

This handoff does not recommend approval, claim that the policy is correct, or
present golden outcomes as predetermined scientific answers. It distinguishes
technical reproducibility from scientific validation and records no reviewer
judgment.

No candidate promotion, published protocol, selector runtime, scientific
synthesis, numerical score, or production scientific execution is authorized
by this document.
