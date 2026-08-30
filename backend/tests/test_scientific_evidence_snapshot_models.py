from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from app.scientific_evaluation.canonicalization import canonical_sha256, canonicalize_json
from app.scientific_evaluation.errors import (
    DuplicateSnapshotMemberError,
    SnapshotMemberError,
    SnapshotRequestError,
)
from app.repositories.scientific_evidence_snapshots import (
    PostgresScientificEvidenceSnapshotRepository,
)
from app.scientific_evaluation.snapshots import (
    CanonicalMemberDescriptor,
    SnapshotConstructionRequest,
    SnapshotMemberInput,
    build_manifest_payload,
    build_member_identity_payload,
    build_query_payload,
    canonical_decimal,
    canonical_timestamp,
)
from app.services.scientific_evidence_snapshots import ScientificEvidenceSnapshotService


NOW = datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc)


def _request(*members, predicates=()):
    return SnapshotConstructionRequest(
        snapshot_policy_key="phase_7_candidate_universe",
        snapshot_policy_version="1",
        as_of=NOW,
        evidence_cutoff=NOW - timedelta(days=1),
        scope={"substance_key": "substance:example"},
        technical_predicates=tuple(predicates),
        members=tuple(members),
        created_by="unit_test",
        sealed_by="unit_test",
    )


class ScientificEvidenceSnapshotModelTests(unittest.TestCase):
    def test_query_payload_is_independent_of_predicate_input_order(self):
        left = build_query_payload(
            _request(predicates=({"field": "z", "value": 2}, {"field": "a", "value": 1}))
        )
        right = build_query_payload(
            _request(predicates=({"field": "a", "value": 1}, {"field": "z", "value": 2}))
        )
        self.assertEqual(canonicalize_json(left), canonicalize_json(right))

    def test_timestamp_and_decimal_normalization_are_explicit(self):
        shifted = NOW.astimezone(timezone(timedelta(hours=2)))
        self.assertEqual(canonical_timestamp(shifted, "as_of"), "2026-08-30T12:00:00.000000Z")
        self.assertEqual(canonical_decimal(Decimal("+12.3400")), "12.34")
        self.assertEqual(canonical_decimal(Decimal("-0.000")), "0")
        with self.assertRaises(SnapshotRequestError):
            canonical_timestamp(datetime(2026, 8, 30), "as_of")

    def test_member_identity_uses_stable_provenance_keys(self):
        payload = build_member_identity_payload(
            member_kind="finding",
            source_key="source",
            dataset_key="dataset",
            external_release_key="release",
            run_key="00000000-0000-0000-0000-000000000001",
            assessment_source_record_key="assessment",
            finding_identity={"kind": "source_finding_key", "value": "finding"},
        )
        self.assertEqual(
            canonical_sha256(payload).hex(),
            canonical_sha256(dict(reversed(tuple(payload.items())))).hex(),
        )
        self.assertNotIn("assessment_id", payload)
        self.assertNotIn("finding_id", payload)

    def test_manifest_order_is_canonical_and_input_order_independent(self):
        first = CanonicalMemberDescriptor("finding", b"b" * 32, b"a" * 32)
        second = CanonicalMemberDescriptor("assessment", b"z" * 32, b"z" * 32)
        arguments = dict(
            snapshot_policy_key="phase_7_candidate_universe",
            snapshot_policy_version="1",
            as_of=NOW,
            evidence_cutoff=NOW - timedelta(days=1),
            query_definition_digest=b"q" * 32,
        )
        left = build_manifest_payload(**arguments, descriptors=[first, second])
        right = build_manifest_payload(**arguments, descriptors=[second, first])
        self.assertEqual(canonicalize_json(left), canonicalize_json(right))
        self.assertEqual(left["ordered_members"][0]["member_kind"], "assessment")

    def test_member_order_uses_identity_then_semantic_digest(self):
        descriptors = [
            CanonicalMemberDescriptor("finding", b"b" * 32, b"a" * 32),
            CanonicalMemberDescriptor("finding", b"a" * 32, b"z" * 32),
            CanonicalMemberDescriptor("finding", b"a" * 32, b"a" * 32),
        ]
        payload = build_manifest_payload(
            snapshot_policy_key="phase_7_candidate_universe",
            snapshot_policy_version="1",
            as_of=NOW,
            evidence_cutoff=NOW,
            query_definition_digest=b"q" * 32,
            descriptors=descriptors,
        )
        self.assertEqual(
            [
                (
                    member["member_identity_digest"],
                    member["member_semantic_digest"],
                )
                for member in payload["ordered_members"]
            ],
            [("61" * 32, "61" * 32), ("61" * 32, "7a" * 32), ("62" * 32, "61" * 32)],
        )

    def test_zero_member_manifest_is_deterministic(self):
        payload = build_manifest_payload(
            snapshot_policy_key="phase_7_candidate_universe",
            snapshot_policy_version="1",
            as_of=NOW,
            evidence_cutoff=NOW,
            query_definition_digest=b"q" * 32,
            descriptors=[],
        )
        self.assertEqual(payload["member_count"], 0)
        self.assertEqual(payload["ordered_members"], [])
        self.assertEqual(canonicalize_json(payload), canonicalize_json(payload))

    def test_duplicate_structural_member_is_rejected(self):
        member = SnapshotMemberInput("finding", assessment_id=7, finding_id=9)
        with self.assertRaises(DuplicateSnapshotMemberError):
            ScientificEvidenceSnapshotService()._validate_request(_request(member, member))

    def test_assessment_and_finding_for_same_assessment_are_rejected(self):
        with self.assertRaises(SnapshotMemberError):
            ScientificEvidenceSnapshotService()._validate_request(
                _request(
                    SnapshotMemberInput("assessment", assessment_id=7),
                    SnapshotMemberInput("finding", assessment_id=7, finding_id=9),
                )
            )

    def test_request_and_member_shapes_are_typed_and_frozen(self):
        request = _request()
        with self.assertRaises(FrozenInstanceError):
            request.created_by = "changed"
        invalid_members = (
            SnapshotMemberInput("finding", assessment_id=1),
            SnapshotMemberInput("assessment", assessment_id=1, finding_id=2),
            SnapshotMemberInput("unsupported", assessment_id=1),
        )
        for member in invalid_members:
            with self.subTest(member=member), self.assertRaises(SnapshotMemberError):
                ScientificEvidenceSnapshotService()._validate_request(_request(member))

    def test_digest_advisory_lock_has_a_stable_dedicated_namespace(self):
        class RecordingCursor:
            def __init__(self):
                self.calls = []

            def execute(self, statement, parameters):
                self.calls.append((statement, parameters))

        repository = PostgresScientificEvidenceSnapshotRepository()
        cursor = RecordingCursor()
        repository.acquire_digest_lock(cursor, b"a" * 32)
        repository.acquire_digest_lock(cursor, b"b" * 32)
        self.assertEqual(
            [call[0] for call in cursor.calls],
            ["SELECT pg_advisory_xact_lock(%s,%s)"] * 2,
        )
        self.assertEqual(cursor.calls[0][1][0], cursor.calls[1][1][0])
        self.assertNotEqual(cursor.calls[0][1][1], cursor.calls[1][1][1])


if __name__ == "__main__":
    unittest.main()
