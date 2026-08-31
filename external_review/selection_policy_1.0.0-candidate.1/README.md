# WYE external scientific review delivery package

Start with `WYE_SELECTION_POLICY_EXTERNAL_REVIEW_HANDOFF.md`.

## Review subject

This package presents the exact frozen Phase 7.7.1 candidate and golden corpus
for independent scientific review:

```text
candidate: efsa_qps_evidence_selection / 1.0.0-candidate.1
candidate SHA-256:
  d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615
golden corpus SHA-256:
  db535148ece59c222eaac2004594ae19a1e00a2e65448c42a4804dd8cefd8b15
scientific approval: NOT PRESENT
```

The frozen scientific review subject is:

- `WYE_SELECTION_POLICY_CANDIDATE_V1.json` — exact machine-readable candidate;
- `WYE_SELECTION_GOLDEN_CASES.md` — 28 authored expected cases;
- `WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json` — exact corpus identity and
  candidate binding.

Required reviewer guidance is:

- `WYE_SELECTION_POLICY_EXTERNAL_REVIEW_HANDOFF.md` — scope, questions,
  procedure, and human declaration;
- `WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md` — detailed scientific
  decision matrix, review cards, references, and golden-case approval matrix.

Supporting technical context only:

- `WYE_SELECTION_POLICY_FREEZE.md` — deterministic policy contract and the
  boundary between technical mechanics and scientific choices.

`DELIVERY_MANIFEST.json` proves package composition and byte identity. It does
not prove scientific correctness, reviewer competence, reviewer authenticity,
or scientific approval.

## Reviewer instructions

1. Follow the reading order in the handoff.
2. Assess scientific correctness and appropriateness; software tests establish
   deterministic conformance only and are not scientific validation.
3. Do not edit the frozen candidate, golden cases, or corpus manifest in place.
4. Record exactly one outcome: `approved`, `changes_requested`, or `rejected`.
5. If changes are required, identify them precisely. A scientific change must
   produce a new governed candidate/corpus identity and a new review.

Completing the human review form does not unlock the WYE repository gate. A
real decision must later be encoded separately in the governed
`WYE_SELECTION_POLICY_EXTERNAL_APPROVAL.json` record and pass the repository
validator. That approval record is intentionally not part of this package.

This delivery package is neutral: it does not recommend approval, fabricate a
reviewer, promote the candidate, or publish version `1.0.0`.
