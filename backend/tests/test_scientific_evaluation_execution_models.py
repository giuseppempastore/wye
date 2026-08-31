"""Pure deterministic contract tests for the Phase 7.6.4C runtime."""

from dataclasses import replace
from datetime import datetime, timezone
import unittest

from app.scientific_evaluation.artifact_contracts import build_artifact_envelope
from app.scientific_evaluation.canonicalization import canonical_sha256, canonicalize_json
from app.scientific_evaluation.errors import ExecutionRequestError
from app.scientific_evaluation.execution import (
    AttemptError,
    EngineBuild,
    ExecutionConfiguration,
    PublicationOutputInput,
    ResultComponentInput,
    SelectionDecisionInput,
    SemanticExecutionRequest,
    build_component_payload,
    build_attempt_error_payload,
    build_configuration_payload,
    build_engine_build_payload,
    build_execution_identity_payload,
    build_publication_bundle_payload,
    build_replay_verification_payload,
    build_result_payload,
    build_selection_decision_payload,
    build_selection_manifest_payload,
    build_trace_payload,
    validate_semantic_request,
)


DIGEST_A = b"a" * 32
DIGEST_B = b"b" * 32
DIGEST_C = b"c" * 32
DIGEST_D = b"d" * 32


def _request(**changes):
    value = SemanticExecutionRequest(
        protocol_version_id=1,
        evidence_snapshot_id=2,
        target_type="substance",
        target_id=3,
        target_artifact_id=4,
        target_digest=DIGEST_A,
        mapping_state_artifact_id=None,
        input_artifact_id=5,
        input_digest=DIGEST_B,
        execution_mode="NORMAL",
        configuration=ExecutionConfiguration("wye-scientific", "2026.1"),
        requested_by="test:caller",
    )
    return replace(value, **changes)


class ScientificEvaluationExecutionModelTests(unittest.TestCase):
    def test_semantic_request_target_and_comparison_shapes(self):
        validate_semantic_request(_request())
        validate_semantic_request(
            _request(
                target_type="ingredient",
                mapping_state_artifact_id=6,
                execution_mode="REFRESH",
                comparison_execution_id=7,
            )
        )
        for request in (
            _request(target_type="product"),
            _request(mapping_state_artifact_id=6),
            _request(execution_mode="REPLAY"),
            _request(idempotency_scope="scope"),
        ):
            with self.subTest(request=request), self.assertRaises(ExecutionRequestError):
                validate_semantic_request(request)

    def test_configuration_payload_has_no_semantic_knobs(self):
        self.assertEqual(
            build_configuration_payload(ExecutionConfiguration("wye-scientific", "2026.1")),
            {
                "artifact_type": "scientific_evaluation_configuration",
                "canonicalization_profiles": ["wye-c14n-json-v1"],
                "engine_contract": {
                    "engine_key": "wye-scientific",
                    "semantic_compatibility_version": "2026.1",
                },
                "schema_version": "1",
                "semantic_parameters": [],
            },
        )

    def test_execution_identity_binds_only_frozen_semantic_roots(self):
        normal = build_execution_identity_payload(
            protocol_digest=DIGEST_A,
            evidence_snapshot_digest=DIGEST_B,
            input_digest=DIGEST_C,
            execution_mode="NORMAL",
            configuration_digest=DIGEST_D,
            comparison_semantic_execution_digest=None,
        )
        replay = build_execution_identity_payload(
            protocol_digest=DIGEST_A,
            evidence_snapshot_digest=DIGEST_B,
            input_digest=DIGEST_C,
            execution_mode="REPLAY",
            configuration_digest=DIGEST_D,
            comparison_semantic_execution_digest=DIGEST_A,
        )
        self.assertNotEqual(canonical_sha256(normal), canonical_sha256(replay))
        self.assertNotIn("worker", normal)
        self.assertNotIn("requested_at", normal)
        self.assertNotIn("attempt", normal)

    def test_engine_build_is_operational_and_strict(self):
        build = EngineBuild(
            "wye-scientific",
            "2026.1",
            "source-r1",
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "python-c14n-1",
            "sha256:" + "4" * 64,
        )
        payload = build_engine_build_payload(build)
        self.assertEqual(payload["engine_key"], "wye-scientific")
        self.assertNotIn("worker_id", payload)
        with self.assertRaises(ExecutionRequestError):
            build_engine_build_payload(replace(build, build_sha256="ABC"))

    def test_attempt_error_rejects_secret_bearing_technical_references(self):
        with self.assertRaises(ExecutionRequestError):
            build_attempt_error_payload(
                AttemptError(
                    "unexpected",
                    "fixture_error",
                    False,
                    technical_references={"nested": {"api_key": "must-not-persist"}},
                )
            )

    def test_selection_manifest_order_is_input_independent(self):
        first = {
            "decision": "included",
            "decision_digest": (b"z" * 32).hex(),
            "member_identity_digest": DIGEST_B.hex(),
            "member_semantic_digest": DIGEST_A.hex(),
            "primary_reason_code": "fixture",
            "resolution_state": "resolved",
            "selection_role": "contributing",
        }
        second = dict(first)
        second.update(
            decision_digest=(b"y" * 32).hex(),
            member_identity_digest=DIGEST_A.hex(),
        )
        left = build_selection_manifest_payload(
            execution_digest=DIGEST_C, descriptors=[first, second]
        )
        right = build_selection_manifest_payload(
            execution_digest=DIGEST_C, descriptors=[second, first]
        )
        self.assertEqual(canonicalize_json(left), canonicalize_json(right))
        self.assertEqual(
            left["ordered_decisions"][0]["member_identity_digest"], DIGEST_A.hex()
        )

    def test_component_order_is_explicit_result_semantics(self):
        component = ResultComponentInput("generic_state", "1", "primary", {"state": "unknown"})
        first = build_component_payload(
            execution_digest=DIGEST_A, ordinal=0, component=component
        )
        second = build_component_payload(
            execution_digest=DIGEST_A, ordinal=1, component=component
        )
        self.assertNotEqual(canonical_sha256(first), canonical_sha256(second))

    def test_result_payload_is_generic_and_non_numeric(self):
        output = PublicationOutputInput(
            decisions=(),
            result_kind="substance_assessment",
            result_schema_version="1",
            scientific_status_namespace="wye.scientific.status",
            scientific_status_version="1",
            scientific_status_code="insufficient_evidence",
            result_content={"state": "not_computable"},
            components=(),
            trace_schema_version="1",
            trace_content={"nodes": []},
            published_by="test:publisher",
        )
        payload = build_result_payload(
            execution_digest=DIGEST_A, output=output, component_descriptors=[]
        )
        self.assertEqual(payload["scientific_status"]["code"], "insufficient_evidence")
        self.assertNotIn("score", payload)

    def test_publication_bundle_excludes_operational_metadata(self):
        payload = build_publication_bundle_payload(
            execution_digest=DIGEST_A,
            protocol_digest=DIGEST_B,
            snapshot_digest=DIGEST_C,
            input_digest=DIGEST_D,
            configuration_digest=DIGEST_A,
            selection_digest=DIGEST_B,
            result_digest=DIGEST_C,
            trace_digest=DIGEST_D,
        )
        self.assertEqual(payload["semantic_execution_digest"], DIGEST_A.hex())
        for field in ("attempt_id", "worker_id", "engine_build", "published_at"):
            self.assertNotIn(field, payload)

    def test_replay_verification_derives_matched_and_mismatch(self):
        matched, matched_status = build_replay_verification_payload(
            replay_execution_digest=DIGEST_A,
            comparison_execution_digest=DIGEST_B,
            comparison_bundle_digest=DIGEST_C,
            expected_selection_digest=DIGEST_A,
            expected_result_digest=DIGEST_B,
            expected_trace_digest=DIGEST_C,
            recomputed_selection_digest=DIGEST_A,
            recomputed_result_digest=DIGEST_B,
            recomputed_trace_digest=DIGEST_C,
        )
        mismatch, mismatch_status = build_replay_verification_payload(
            replay_execution_digest=DIGEST_A,
            comparison_execution_digest=DIGEST_B,
            comparison_bundle_digest=DIGEST_C,
            expected_selection_digest=DIGEST_A,
            expected_result_digest=DIGEST_B,
            expected_trace_digest=DIGEST_C,
            recomputed_selection_digest=DIGEST_D,
            recomputed_result_digest=DIGEST_B,
            recomputed_trace_digest=DIGEST_C,
        )
        self.assertEqual((matched_status, matched["root_matches"]), (
            "matched", {"result": True, "selection": True, "trace": True}
        ))
        self.assertEqual(mismatch_status, "mismatch")
        self.assertFalse(mismatch["root_matches"]["selection"])

    def test_golden_canonical_artifact_vectors(self):
        build = EngineBuild(
            "wye-scientific",
            "2026.1",
            "source-r1",
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "python-c14n-1",
            None,
        )
        decision = SelectionDecisionInput(
            7,
            "included",
            "contributing",
            "resolved",
            "wye.fixture.selection",
            "1",
            "fixture_included",
            {"state": "fixture"},
        )
        member = {
            "member_kind": "finding",
            "member_identity_digest": DIGEST_A,
            "member_semantic_digest": DIGEST_B,
        }
        decision_descriptor = {
            "decision": "included",
            "decision_digest": DIGEST_C.hex(),
            "member_identity_digest": DIGEST_A.hex(),
            "member_semantic_digest": DIGEST_B.hex(),
            "primary_reason_code": "fixture_included",
            "resolution_state": "resolved",
            "selection_role": "contributing",
        }
        component = ResultComponentInput(
            "generic_scientific_state", "1", "primary", {"state": "unknown"}
        )
        output = PublicationOutputInput(
            decisions=(decision,),
            result_kind="substance_assessment",
            result_schema_version="1",
            scientific_status_namespace="wye.scientific.status",
            scientific_status_version="1",
            scientific_status_code="insufficient_evidence",
            result_content={"state": "not_computable"},
            components=(component,),
            trace_schema_version="1",
            trace_content={"edges": [], "nodes": []},
            published_by="test:publisher",
        )
        component_descriptor = {
            "component_digest": DIGEST_D.hex(),
            "component_kind": component.component_kind,
            "component_ordinal": 0,
            "component_role": component.component_role,
            "component_schema_version": component.component_schema_version,
        }
        replay_payload, _ = build_replay_verification_payload(
            replay_execution_digest=DIGEST_A,
            comparison_execution_digest=DIGEST_B,
            comparison_bundle_digest=DIGEST_C,
            expected_selection_digest=DIGEST_A,
            expected_result_digest=DIGEST_B,
            expected_trace_digest=DIGEST_C,
            recomputed_selection_digest=DIGEST_A,
            recomputed_result_digest=DIGEST_B,
            recomputed_trace_digest=DIGEST_C,
        )
        vectors = {
            "configuration": (
                "scientific_evaluation_configuration",
                build_configuration_payload(ExecutionConfiguration("wye-scientific", "2026.1")),
                375,
                "6a0169c24c35c783a293644bc99bb96d8d064dafdb7f56e04ee3ed34d9110ab5",
            ),
            "execution_identity": (
                "scientific_evaluation_execution_identity",
                build_execution_identity_payload(
                    protocol_digest=DIGEST_A,
                    evidence_snapshot_digest=DIGEST_B,
                    input_digest=DIGEST_C,
                    execution_mode="NORMAL",
                    configuration_digest=DIGEST_D,
                    comparison_semantic_execution_digest=None,
                ),
                640,
                "f037a3ac81fe51e8491765a541cf1ffe3b3e100af352273701a24fcfbe38899c",
            ),
            "engine_build": (
                "scientific_evaluation_engine_build",
                build_engine_build_payload(build),
                653,
                "325f995a936b9a9f95122a15f8e33c5126540bc93ed80c937070baa167283c40",
            ),
            "attempt_error": (
                "scientific_evaluation_attempt_error",
                build_attempt_error_payload(
                    AttemptError("resource", "fixture_capacity", True, "safe fixture")
                ),
                346,
                "4bc698bbee5ec119fd46d1b7c305e7878762a5da8481ba5e34c89565d67e6cc8",
            ),
            "selection_decision": (
                "scientific_evidence_selection_decision",
                build_selection_decision_payload(
                    execution_digest=DIGEST_C, member=member, decision=decision
                ),
                746,
                "b22aa2df245f7d16efad94d51d2f49cd91ba7502161434f618e7c5ff28a80c86",
            ),
            "selection_manifest": (
                "scientific_evidence_selection_manifest",
                build_selection_manifest_payload(
                    execution_digest=DIGEST_C, descriptors=[decision_descriptor]
                ),
                747,
                "208b9d05c8d9f8c98466980e4fa0d7c6cceabe150be3e33ddab7c093ab618ba0",
            ),
            "result_component": (
                "scientific_evaluation_result_component",
                build_component_payload(
                    execution_digest=DIGEST_A, ordinal=0, component=component
                ),
                464,
                "f737bfda2b2e645055d97c96a9d49907b8b70baf3cc73ede2781fb22213d8333",
            ),
            "result": (
                "scientific_evaluation_result",
                build_result_payload(
                    execution_digest=DIGEST_A,
                    output=output,
                    component_descriptors=[component_descriptor],
                ),
                722,
                "9e3f3b033c5042457affa385adc27d4e5ee26752c188fa05a08f31dfba147e61",
            ),
            "trace": (
                "scientific_evaluation_trace",
                build_trace_payload(
                    execution_digest=DIGEST_A,
                    protocol_digest=DIGEST_B,
                    snapshot_digest=DIGEST_C,
                    input_digest=DIGEST_D,
                    selection_digest=DIGEST_A,
                    result_digest=DIGEST_B,
                    trace_schema_version="1",
                    content={"edges": [], "nodes": []},
                ),
                779,
                "4c4638abf9092cb0601e5a64ff4d8dfacc59156d9fa6c7b0ce90c020d4e6cf96",
            ),
            "publication_bundle": (
                "scientific_evaluation_publication_bundle",
                build_publication_bundle_payload(
                    execution_digest=DIGEST_A,
                    protocol_digest=DIGEST_B,
                    snapshot_digest=DIGEST_C,
                    input_digest=DIGEST_D,
                    configuration_digest=DIGEST_A,
                    selection_digest=DIGEST_B,
                    result_digest=DIGEST_C,
                    trace_digest=DIGEST_D,
                ),
                916,
                "72abbe6cd028c8179719a25d3f79dce2720947f097b8f1338cbea9febaf57862",
            ),
            "replay_verification": (
                "scientific_evaluation_replay_verification",
                replay_payload,
                1170,
                "50857133773b245511679f110d908665f3ae0761dbafe2afef248e54fa20e6cd",
            ),
        }
        for name, (kind, payload, expected_length, expected_digest) in vectors.items():
            canonical = canonicalize_json(build_artifact_envelope(kind, "1", payload))
            with self.subTest(vector=name):
                self.assertEqual(len(canonical), expected_length)
                self.assertEqual(canonical_sha256(build_artifact_envelope(kind, "1", payload)).hex(), expected_digest)


if __name__ == "__main__":
    unittest.main()
