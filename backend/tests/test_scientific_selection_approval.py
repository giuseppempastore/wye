"""Governance-only tests for the Phase 7.7.2 external approval gate."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from app.scientific_evaluation.selection_approval import (
    APPROVAL_ARTIFACT_FILENAME,
    APPROVAL_REJECTED,
    APPROVAL_REQUIRED,
    APPROVAL_SCHEMA,
    APPROVAL_SCHEMA_VERSION,
    APPROVAL_VALID,
    CHANGES_REQUESTED,
    FROZEN_GOLDEN_CORPUS_DIGEST,
    FROZEN_POLICY_DIGEST,
    FROZEN_POLICY_VERSION,
    GOLDEN_CORPUS_SCHEMA_REFERENCE,
    MANDATORY_CATEGORY_C_ITEMS,
    REQUIRED_SCOPE,
    compute_approval_record_digest,
    evaluate_repository_approval_gate,
    load_frozen_selection_package,
    validate_external_scientific_approval,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_FILES = (
    "WYE_SELECTION_POLICY_CANDIDATE_V1.json",
    "WYE_SELECTION_GOLDEN_CASES.md",
    "WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json",
)


def _copy_frozen_package(destination: Path) -> None:
    for filename in PACKAGE_FILES:
        shutil.copy2(REPOSITORY_ROOT / filename, destination / filename)


def _approval_record(**changes):
    # This is intentionally synthetic test data and is never written to the
    # repository approval path or represented as real scientific authority.
    record = {
        "approval_schema": APPROVAL_SCHEMA,
        "approval_schema_version": APPROVAL_SCHEMA_VERSION,
        "approval_key": "approval:external-review:001",
        "policy_key": "efsa_qps_evidence_selection",
        "policy_version": FROZEN_POLICY_VERSION,
        "selection_policy_digest": FROZEN_POLICY_DIGEST,
        "role": "scientific_reviewer",
        "reviewer_identity": "reviewer:external-domain-reviewer-001",
        "decision": "approved",
        "reviewed_at": "2026-08-31T12:00:00Z",
        "scope": list(REQUIRED_SCOPE),
        "approved_category_C_items": list(MANDATORY_CATEGORY_C_ITEMS),
        "candidate_review_confirmed": True,
        "golden_corpus_review_confirmed": True,
        "golden_case_set_reference": {
            "schema": GOLDEN_CORPUS_SCHEMA_REFERENCE,
            "digest": FROZEN_GOLDEN_CORPUS_DIGEST,
        },
        "notes_reference": None,
        "governed_audit_reference": "governed-audit:external-review/record-001",
    }
    record.update(changes)
    record["approval_record_digest"] = compute_approval_record_digest(record)
    return record


def _changed(record, **changes):
    value = deepcopy(record)
    value.update(changes)
    value["approval_record_digest"] = compute_approval_record_digest(value)
    return value


class ScientificSelectionApprovalGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = load_frozen_selection_package(REPOSITORY_ROOT)

    def test_frozen_package_matches_exact_review_subject(self):
        self.assertEqual(self.frozen.policy_version, FROZEN_POLICY_VERSION)
        self.assertEqual(self.frozen.policy_canonical_bytes, 16284)
        self.assertEqual(self.frozen.policy_digest, FROZEN_POLICY_DIGEST)
        self.assertEqual(self.frozen.golden_document_bytes, 17040)
        self.assertEqual(self.frozen.golden_case_count, 28)
        self.assertEqual(self.frozen.golden_corpus_digest, FROZEN_GOLDEN_CORPUS_DIGEST)

    def test_no_approval_artifact_is_blocked_and_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _copy_frozen_package(root)
            approval_path = root / APPROVAL_ARTIFACT_FILENAME
            self.assertFalse(approval_path.exists())
            validation = evaluate_repository_approval_gate(root)
            self.assertEqual(validation.gate_status, APPROVAL_REQUIRED)
            self.assertEqual(validation.errors, ("approval_artifact_missing",))
            self.assertFalse(validation.unlocks_next_gate)
            self.assertFalse(approval_path.exists())

    def test_exact_synthetic_record_is_mechanically_valid_only(self):
        validation = validate_external_scientific_approval(
            _approval_record(), self.frozen
        )
        self.assertTrue(validation.mechanically_valid)
        self.assertTrue(validation.unlocks_next_gate)
        self.assertEqual(validation.gate_status, APPROVAL_VALID)

    def test_wrong_candidate_digest_is_invalid(self):
        record = _changed(
            _approval_record(), selection_policy_digest="0" * 64
        )
        validation = validate_external_scientific_approval(record, self.frozen)
        self.assertIn("selection_policy_digest_mismatch", validation.errors)
        self.assertFalse(validation.unlocks_next_gate)

    def test_wrong_golden_corpus_digest_is_invalid(self):
        record = _approval_record()
        record["golden_case_set_reference"]["digest"] = "0" * 64
        record["approval_record_digest"] = compute_approval_record_digest(record)
        validation = validate_external_scientific_approval(record, self.frozen)
        self.assertIn("golden_corpus_digest_mismatch", validation.errors)

    def test_wrong_candidate_version_is_invalid(self):
        record = _changed(_approval_record(), policy_version="1.0.0")
        validation = validate_external_scientific_approval(record, self.frozen)
        self.assertIn("policy_version_mismatch", validation.errors)

    def test_required_scalar_fields_fail_closed_when_missing(self):
        expected = {
            "reviewer_identity": "missing_field:reviewer_identity",
            "reviewed_at": "missing_field:reviewed_at",
            "decision": "missing_field:decision",
        }
        for field, error in expected.items():
            with self.subTest(field=field):
                record = _approval_record()
                record.pop(field)
                record["approval_record_digest"] = compute_approval_record_digest(record)
                validation = validate_external_scientific_approval(record, self.frozen)
                self.assertIn(error, validation.errors)
                self.assertFalse(validation.unlocks_next_gate)

    def test_both_review_confirmations_are_required(self):
        for field, error in (
            ("candidate_review_confirmed", "candidate_review_not_confirmed"),
            ("golden_corpus_review_confirmed", "golden_corpus_review_not_confirmed"),
        ):
            with self.subTest(field=field):
                validation = validate_external_scientific_approval(
                    _changed(_approval_record(), **{field: False}), self.frozen
                )
                self.assertIn(error, validation.errors)

    def test_changes_requested_is_valid_but_never_unlocks(self):
        record = _changed(
            _approval_record(),
            decision="changes_requested",
            approved_category_C_items=[],
        )
        validation = validate_external_scientific_approval(record, self.frozen)
        self.assertTrue(validation.mechanically_valid)
        self.assertEqual(validation.gate_status, CHANGES_REQUESTED)
        self.assertFalse(validation.unlocks_next_gate)

    def test_rejected_is_valid_but_never_unlocks(self):
        record = _changed(
            _approval_record(), decision="rejected", approved_category_C_items=[]
        )
        validation = validate_external_scientific_approval(record, self.frozen)
        self.assertTrue(validation.mechanically_valid)
        self.assertEqual(validation.gate_status, APPROVAL_REJECTED)
        self.assertFalse(validation.unlocks_next_gate)

    def test_malformed_artifact_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _copy_frozen_package(root)
            approval_path = root / APPROVAL_ARTIFACT_FILENAME
            approval_path.write_text('{"decision":', encoding="utf-8")
            validation = evaluate_repository_approval_gate(root)
            self.assertEqual(validation.gate_status, APPROVAL_REQUIRED)
            self.assertTrue(validation.errors[0].startswith("malformed_approval_artifact:"))

    def test_candidate_changed_after_approval_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _copy_frozen_package(root)
            approval_path = root / APPROVAL_ARTIFACT_FILENAME
            approval_path.write_text(json.dumps(_approval_record()), encoding="utf-8")
            candidate_path = root / "WYE_SELECTION_POLICY_CANDIDATE_V1.json"
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["post_review_change"] = True
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            validation = evaluate_repository_approval_gate(root)
            self.assertEqual(validation.gate_status, APPROVAL_REQUIRED)
            self.assertIn("candidate canonical", validation.errors[0])

    def test_golden_corpus_changed_after_approval_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _copy_frozen_package(root)
            approval_path = root / APPROVAL_ARTIFACT_FILENAME
            approval_path.write_text(json.dumps(_approval_record()), encoding="utf-8")
            golden_path = root / "WYE_SELECTION_GOLDEN_CASES.md"
            golden_path.write_text(
                golden_path.read_text(encoding="utf-8") + "\nchanged after review\n",
                encoding="utf-8",
            )
            validation = evaluate_repository_approval_gate(root)
            self.assertEqual(validation.gate_status, APPROVAL_REQUIRED)
            self.assertIn("golden document", validation.errors[0])

    def test_missing_or_partial_category_C_approval_never_unlocks(self):
        partial = list(MANDATORY_CATEGORY_C_ITEMS[:-1])
        validation = validate_external_scientific_approval(
            _changed(_approval_record(), approved_category_C_items=partial), self.frozen
        )
        self.assertIn("mandatory_category_C_items_not_fully_approved", validation.errors)
        self.assertFalse(validation.unlocks_next_gate)

    def test_non_scientific_or_ai_identity_never_unlocks(self):
        for changes, expected in (
            ({"role": "validation_owner"}, "scientific_reviewer_role_required"),
            ({"reviewer_identity": "OpenAI Codex"}, "non_external_reviewer_identity"),
            ({"reviewer_identity": "CI automation bot"}, "non_external_reviewer_identity"),
        ):
            with self.subTest(changes=changes):
                validation = validate_external_scientific_approval(
                    _changed(_approval_record(), **changes), self.frozen
                )
                self.assertIn(expected, validation.errors)
                self.assertFalse(validation.unlocks_next_gate)

    def test_missing_audit_provenance_never_unlocks(self):
        validation = validate_external_scientific_approval(
            _changed(_approval_record(), governed_audit_reference=None), self.frozen
        )
        self.assertIn("governed_audit_reference_required", validation.errors)

    def test_record_digest_and_closed_schema_are_enforced(self):
        bad_digest = _approval_record()
        bad_digest["approval_record_digest"] = "0" * 64
        validation = validate_external_scientific_approval(bad_digest, self.frozen)
        self.assertIn("approval_record_digest_mismatch", validation.errors)

        extra = _approval_record(extra_approval_flag=True)
        validation = validate_external_scientific_approval(extra, self.frozen)
        self.assertIn("unknown_field:extra_approval_flag", validation.errors)


if __name__ == "__main__":
    unittest.main()
