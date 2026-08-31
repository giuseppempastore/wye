"""Unit contract tests for canonical mapping state and evaluation input v1."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest
from uuid import UUID

from app.scientific_evaluation.canonicalization import canonical_sha256, canonicalize_json
from app.scientific_evaluation.errors import (
    MappingInputRequestError,
    UnsupportedEvaluationTargetError,
)
from app.scientific_evaluation.mapping_inputs import (
    CanonicalEvaluationInputRequest,
    MappingMemberDescriptor,
    build_authority_chain_payload,
    build_evaluation_input_payload,
    build_mapping_manifest_payload,
    build_mapping_member_payload,
    build_mapping_member_identity,
    build_non_member_observation,
    build_observation_subject_identity,
    build_target_payload,
    canonical_decimal,
    derive_resolution,
    mapping_day,
    order_authority_chains,
    validate_request,
)


UTC = timezone.utc
AS_OF = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def _proposal(proposal_id=8001, proposal_key="11111111-1111-4111-8111-111111111111"):
    return {
        "id": proposal_id,
        "proposal_key": UUID(proposal_key),
        "ingredient_id": 42,
        "substance_id": 99,
        "relationship_type": "represents",
        "mapping_method": "manual_review",
        "mapping_confidence": Decimal("0.900"),
        "source_dataset_release_id": None,
        "ingestion_run_id": None,
        "proposed_by": "proposer:test",
        "provenance": {"source": "review"},
        "created_at": datetime(2026, 1, 2, 9, 0, tzinfo=UTC),
    }


def _decision(decision_id=9001):
    return {
        "id": decision_id,
        "proposal_id": 8001,
        "decision_type": "accept",
        "effective_from": date(2026, 1, 1),
        "reviewed_by": "reviewer:test",
        "reviewed_at": datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
        "reason_code": "identity_verified",
        "provenance": None,
        "created_at": datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
    }


def _materialization(materialization_id=10001, status="applied", minute=1):
    return {
        "id": materialization_id,
        "decision_id": 9001,
        "proposal_id": 8001,
        "ingredient_substance_id": 7001,
        "materialization_status": status,
        "materialized_by": "worker:test",
        "materialized_at": datetime(2026, 1, 2, 10, minute, tzinfo=UTC),
        "provenance": None,
        "created_at": datetime(2026, 1, 2, 10, minute, tzinfo=UTC),
    }


class ScientificMappingInputModelTests(unittest.TestCase):
    def test_target_vocabulary_and_timezone_validation(self):
        validate_request(CanonicalEvaluationInputRequest("ingredient", 42, AS_OF))
        validate_request(CanonicalEvaluationInputRequest("substance", 99, AS_OF))
        with self.assertRaises(UnsupportedEvaluationTargetError):
            validate_request(CanonicalEvaluationInputRequest("product", 1, AS_OF))
        with self.assertRaises(MappingInputRequestError):
            validate_request(CanonicalEvaluationInputRequest("ingredient", 42, AS_OF.replace(tzinfo=None)))
        with self.assertRaises(MappingInputRequestError):
            validate_request(CanonicalEvaluationInputRequest("ingredient", 2**63, AS_OF))

    def test_mapping_day_is_utc_and_boundaries_are_stable(self):
        rome_like = timezone(timedelta(hours=2))
        self.assertEqual(
            mapping_day(datetime(2026, 8, 31, 1, 30, tzinfo=rome_like)),
            date(2026, 8, 30),
        )
        self.assertEqual(mapping_day(datetime(2026, 8, 31, 0, 0, tzinfo=UTC)), date(2026, 8, 31))

    def test_ingredient_target_golden_vector(self):
        payload = build_target_payload(
            target_type="ingredient",
            row={
                "id": 42,
                "canonical_name": "citric acid",
                "common_name": None,
                "ingredient_group": "acidulant",
                "status": "active",
                "cas_number": "77-92-9",
                "einecs_number": None,
                "created_at": datetime(2026, 1, 1, tzinfo=UTC),
                "updated_at": datetime(2026, 8, 1, 9, 30, tzinfo=UTC),
            },
            as_of=AS_OF,
        )
        expected = (
            b'{"artifact_type":"scientific_evaluation_target","entity_id":42,'
            b'"identity_as_of":"2026-08-30T12:00:00.000000Z",'
            b'"identity_namespace":"wye_internal_id_v1",'
            b'"identity_recorded_at":"2026-08-01T09:30:00.000000Z",'
            b'"identity_resolution_state":"resolved","identity_state":'
            b'{"canonical_name":"citric acid","common_name":null,'
            b'"declared_identifiers":[{"identifier_system":"cas","value":"77-92-9"}],'
            b'"ingredient_group":"acidulant","status":"active"},'
            b'"schema_version":"1","target_type":"ingredient"}'
        )
        self.assertEqual(canonicalize_json(payload), expected)
        self.assertEqual(
            canonical_sha256(payload).hex(),
            "c9554fe283730ea18e403bf7fd4383d6f6a06f1cb66e5646ab4ac6a60fc01a9f",
        )

    def test_substance_target_shape_excludes_identifier_projection(self):
        payload = build_target_payload(
            target_type="substance",
            row={
                "id": 99,
                "preferred_name": "Citric acid",
                "normalized_name": "citric acid",
                "scientific_name": None,
                "substance_type": "chemical_substance",
                "status": "active",
                "created_at": datetime(2026, 1, 1, tzinfo=UTC),
                "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
            },
            as_of=AS_OF,
        )
        self.assertNotIn("identifiers", payload["identity_state"])
        self.assertEqual(payload["target_type"], "substance")

    def test_authority_chain_identity_payload_and_decimal(self):
        payload, digest = build_authority_chain_payload(
            bridge_id=7001,
            proposal=_proposal(),
            decision=_decision(),
            materialization=_materialization(),
        )
        self.assertEqual(payload["proposal"]["mapping_confidence"], "0.9")
        self.assertEqual(payload["authority_chain_identity_digest"], digest.hex())
        self.assertEqual(canonical_decimal(Decimal("-0.000")), "0")

    def test_authority_chain_order_uses_timestamp_then_digest(self):
        first = build_authority_chain_payload(
            bridge_id=7001,
            proposal=_proposal(),
            decision=_decision(),
            materialization=_materialization(10001, "applied", 2),
        )
        second_proposal = _proposal(8002, "22222222-2222-4222-8222-222222222222")
        second_decision = _decision(9002)
        second_decision["proposal_id"] = 8002
        second_materialization = _materialization(10002, "already_current", 1)
        second_materialization["proposal_id"] = 8002
        second_materialization["decision_id"] = 9002
        second = build_authority_chain_payload(
            bridge_id=7001,
            proposal=second_proposal,
            decision=second_decision,
            materialization=second_materialization,
        )
        ordered = order_authority_chains([first, second])
        self.assertEqual(ordered[0]["materialization"]["materialization_id"], 10002)
        self.assertEqual(len(ordered), 2)

    def test_mapping_member_identity_is_bridge_oriented(self):
        bridge = {
            "id": 7001,
            "ingredient_id": 42,
            "substance_id": 99,
            "relationship_type": "contains",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        }
        before = canonical_sha256(build_mapping_member_identity(bridge))
        bridge["valid_to"] = date(2026, 12, 31)
        self.assertEqual(before, canonical_sha256(build_mapping_member_identity(bridge)))
        bridge["relationship_type"] = "represents"
        self.assertNotEqual(before, canonical_sha256(build_mapping_member_identity(bridge)))

    def _observation(self, reason_code="pending_proposal"):
        identity = build_observation_subject_identity(
            observation_kind="proposal", proposal_id=8100
        )
        return build_non_member_observation(
            observation_kind="proposal",
            reason_code=reason_code,
            subject_identity=identity,
            ingredient_id=42,
            substance_id=100,
            relationship_type="contains",
            recorded_at=datetime(2026, 8, 1, 8, 0, tzinfo=UTC),
        )

    def test_observation_identity_digest_and_closed_reason_vocabulary(self):
        observation = self._observation()
        self.assertEqual(observation.resolution_impact, "extends_set")
        self.assertEqual(
            observation.payload()["subject_identity_digest"],
            observation.subject_identity_digest.hex(),
        )
        with self.assertRaises(MappingInputRequestError):
            self._observation("invented_reason")

    def test_resolution_decision_table(self):
        extending = [self._observation()]
        invalidating = [self._observation("history_incomplete")]
        self.assertEqual(derive_resolution(member_count=1, observations=[], visible_history=True)[0], "resolved")
        self.assertEqual(derive_resolution(member_count=0, observations=[], visible_history=False)[0], "empty")
        self.assertEqual(derive_resolution(member_count=1, observations=extending, visible_history=True)[0], "partially_resolved")
        self.assertEqual(derive_resolution(member_count=0, observations=extending, visible_history=True)[0], "history_unavailable")
        self.assertEqual(derive_resolution(member_count=2, observations=invalidating, visible_history=True)[0], "history_unavailable")

    def test_manifest_is_input_order_independent_and_counts_exactly(self):
        members = [
            MappingMemberDescriptor("contains", b"b" * 32, b"c" * 32, b"d" * 32),
            MappingMemberDescriptor("represents", b"a" * 32, b"e" * 32, b"f" * 32),
        ]
        first, state = build_mapping_manifest_payload(
            as_of=AS_OF,
            day=AS_OF.date(),
            ingredient_target_digest=b"i" * 32,
            members=members,
            observations=[self._observation()],
            visible_history=True,
        )
        second, _ = build_mapping_manifest_payload(
            as_of=AS_OF,
            day=AS_OF.date(),
            ingredient_target_digest=b"i" * 32,
            members=list(reversed(members)),
            observations=[self._observation()],
            visible_history=True,
        )
        self.assertEqual(canonicalize_json(first), canonicalize_json(second))
        self.assertEqual((state, first["member_count"], first["observation_count"]), ("partially_resolved", 2, 1))

    def test_evaluation_input_root_excludes_snapshot_protocol_and_mode(self):
        request = CanonicalEvaluationInputRequest("ingredient", 42, AS_OF)
        payload = build_evaluation_input_payload(
            request=request,
            target_artifact_digest=b"t" * 32,
            mapping_resolution_state="resolved",
            mapping_manifest_digest=b"m" * 32,
        )
        encoded = canonicalize_json(payload)
        for forbidden in (b"snapshot", b"protocol", b"NORMAL", b"mode"):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(payload["domain_inputs"], [])

    def test_substance_input_has_explicit_not_applicable_mapping(self):
        payload = build_evaluation_input_payload(
            request=CanonicalEvaluationInputRequest("substance", 99, AS_OF),
            target_artifact_digest=b"t" * 32,
            mapping_resolution_state="not_applicable",
            mapping_manifest_digest=None,
        )
        self.assertEqual(
            payload["mapping_state"],
            {
                "applicability": "not_applicable",
                "manifest_digest": None,
                "resolution_state": "not_applicable",
            },
        )

    def test_nine_stable_canonical_golden_roots(self):
        ingredient_target = build_target_payload(
            target_type="ingredient",
            row={
                "id": 42,
                "canonical_name": "citric acid",
                "common_name": None,
                "ingredient_group": "acidulant",
                "status": "active",
                "cas_number": "77-92-9",
                "einecs_number": None,
                "created_at": datetime(2026, 1, 1, tzinfo=UTC),
                "updated_at": datetime(2026, 8, 1, 9, 30, tzinfo=UTC),
            },
            as_of=AS_OF,
        )
        substance_target = build_target_payload(
            target_type="substance",
            row={
                "id": 99,
                "preferred_name": "Citric acid",
                "normalized_name": "citric acid",
                "scientific_name": None,
                "substance_type": "chemical_substance",
                "status": "active",
                "created_at": datetime(2026, 1, 1, tzinfo=UTC),
                "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
            },
            as_of=AS_OF,
        )
        bridge = {
            "id": 7001,
            "ingredient_id": 42,
            "substance_id": 99,
            "relationship_type": "represents",
            "mapping_method": "manual_review",
            "source_dataset_release_id": None,
            "ingestion_run_id": None,
            "valid_from": date(2026, 1, 1),
        }
        first_chain = build_authority_chain_payload(
            bridge_id=7001,
            proposal=_proposal(),
            decision=_decision(),
            materialization=_materialization(),
        )
        second_proposal = _proposal(8002, "22222222-2222-4222-8222-222222222222")
        second_decision = _decision(9002)
        second_decision["proposal_id"] = 8002
        second_materialization = _materialization(10002, "already_current", 2)
        second_materialization["proposal_id"] = 8002
        second_materialization["decision_id"] = 9002
        second_chain = build_authority_chain_payload(
            bridge_id=7001,
            proposal=second_proposal,
            decision=second_decision,
            materialization=second_materialization,
        )
        identity_digest = canonical_sha256(build_mapping_member_identity(bridge))
        ingredient_digest = canonical_sha256(ingredient_target)
        substance_digest = canonical_sha256(substance_target)
        member_one = build_mapping_member_payload(
            bridge=bridge,
            member_identity_digest=identity_digest,
            ingredient_target_digest=ingredient_digest,
            substance_target_digest=substance_digest,
            as_of=AS_OF,
            day=AS_OF.date(),
            effective_valid_to=None,
            closure=None,
            authority_chains=order_authority_chains([first_chain]),
        )
        member_two = build_mapping_member_payload(
            bridge=bridge,
            member_identity_digest=identity_digest,
            ingredient_target_digest=ingredient_digest,
            substance_target_digest=substance_digest,
            as_of=AS_OF,
            day=AS_OF.date(),
            effective_valid_to=None,
            closure=None,
            authority_chains=order_authority_chains([second_chain, first_chain]),
        )
        observation = self._observation()
        descriptor = MappingMemberDescriptor(
            "represents",
            substance_digest,
            identity_digest,
            canonical_sha256(member_one),
        )
        resolved, _ = build_mapping_manifest_payload(
            as_of=AS_OF,
            day=AS_OF.date(),
            ingredient_target_digest=ingredient_digest,
            members=[descriptor],
            observations=[],
            visible_history=True,
        )
        partial, _ = build_mapping_manifest_payload(
            as_of=AS_OF,
            day=AS_OF.date(),
            ingredient_target_digest=ingredient_digest,
            members=[descriptor],
            observations=[observation],
            visible_history=True,
        )
        unavailable, _ = build_mapping_manifest_payload(
            as_of=AS_OF,
            day=AS_OF.date(),
            ingredient_target_digest=ingredient_digest,
            members=[],
            observations=[observation],
            visible_history=True,
        )
        evaluation_input = build_evaluation_input_payload(
            request=CanonicalEvaluationInputRequest("ingredient", 42, AS_OF),
            target_artifact_digest=ingredient_digest,
            mapping_resolution_state="resolved",
            mapping_manifest_digest=canonical_sha256(resolved),
        )
        vectors = {
            "ingredient_target": ingredient_target,
            "substance_target": substance_target,
            "mapping_member_one_authority": member_one,
            "mapping_member_two_authorities": member_two,
            "non_member_observation": observation.payload(),
            "resolved_manifest": resolved,
            "partially_resolved_manifest": partial,
            "history_unavailable_manifest": unavailable,
            "scientific_evaluation_input": evaluation_input,
        }
        actual = {
            name: (len(canonicalize_json(value)), canonical_sha256(value).hex())
            for name, value in vectors.items()
        }
        expected = {
            "ingredient_target": (
                481,
                "c9554fe283730ea18e403bf7fd4383d6f6a06f1cb66e5646ab4ac6a60fc01a9f",
            ),
            "substance_target": (
                452,
                "26bb04ea5d1db5689b6be2b7a294fbea292f7ab7c401d79cc4d2710d0ea02030",
            ),
            "mapping_member_one_authority": (
                1743,
                "d4715b3f80d445e12bb4941ed1ad52d0b557ae44e317d72faf6ec1328e6493dc",
            ),
            "mapping_member_two_authorities": (
                2712,
                "d19b3777f45e4a90d6e77680d77e659fcdacd948eb0028612b3ffdc6994ebebf",
            ),
            "non_member_observation": (
                790,
                "4113fd689fefc0c4226f7cacc2f1211e6bb0279520dae7738b08b5d67d686f4f",
            ),
            "resolved_manifest": (
                817,
                "8245afbd3f25bbdc90e253254a48d8855ddff4e3f8032fa458de42b723da0a58",
            ),
            "partially_resolved_manifest": (
                1638,
                "a4ffb490d891958d9d9952379d694a507a662c024c73fd61e7a44520b1b123c0",
            ),
            "history_unavailable_manifest": (
                1332,
                "080bbcc2fbfd271e4767b5b5da40ba715998fad2f2f540a64a265d5f13ece2ca",
            ),
            "scientific_evaluation_input": (
                421,
                "06dc2a258982f96cef039e2dfa077163d400377e845d2d2cbbb56f1d2a08e6bb",
            ),
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
