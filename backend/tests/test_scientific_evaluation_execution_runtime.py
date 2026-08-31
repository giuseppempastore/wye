"""Real PostgreSQL integration tests for the Phase 7.6.4C runtime."""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import threading
import unittest
import uuid

import psycopg2


TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_scientific_evidence_snapshots import (  # noqa: E402
    _alembic,
    _connection,
    _create_database,
    _drop_database,
    _insert_evidence,
    _insert_member,
    _insert_snapshot,
    _seal_snapshot,
)
from test_scientific_evaluation_foundation import _publish_protocol_version  # noqa: E402

from app.scientific_evaluation.errors import (  # noqa: E402
    ActiveExecutionAttemptError,
    ExecutionIdempotencyConflictError,
    ExecutionPublicationConflictError,
    IncompleteSelectionCoverageError,
    IncompatibleCanonicalOutputError,
    InvalidExecutionAttemptTransitionError,
    NonRetryableExecutionError,
    ReplayComparisonUnavailableError,
    UnsealedEvidenceSnapshotError,
)
from app.scientific_evaluation.execution import (  # noqa: E402
    AttemptError,
    AttemptStartRequest,
    EngineBuild,
    ExecutionConfiguration,
    PublicationOutputInput,
    ReplayOutputInput,
    ResultComponentInput,
    SelectionDecisionInput,
    SemanticExecutionRequest,
)
from app.scientific_evaluation.mapping_inputs import CanonicalEvaluationInputRequest  # noqa: E402
from app.services.scientific_evaluation_executions import (  # noqa: E402
    ScientificEvaluationExecutionService,
)
from app.services.scientific_mapping_state import ScientificMappingStateService  # noqa: E402


@unittest.skipUnless(
    os.getenv("WYE_RUN_EXECUTION_RUNTIME_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvaluationExecutionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = _create_database("execution_runtime")
        try:
            _alembic(cls.database, "upgrade", "head")
        except Exception:
            _drop_database(cls.database)
            raise

    @classmethod
    def tearDownClass(cls):
        _drop_database(cls.database)

    def setUp(self):
        self.connection = _connection(self.database)
        self.connection.autocommit = False
        self.cursor = self.connection.cursor()
        self.service = ScientificEvaluationExecutionService()

    def tearDown(self):
        try:
            self.connection.rollback()
        finally:
            self.cursor.close()
            self.connection.close()

    def _fixture(self, member_count=0, *, sealed=True):
        _, protocol_id, _, _ = _publish_protocol_version(self.connection)
        self.cursor.execute(
            "SELECT protocol_digest FROM scientific_evaluation_protocol_versions WHERE id=%s",
            (protocol_id,),
        )
        protocol_digest = bytes(self.cursor.fetchone()[0])
        snapshot_id, _ = _insert_snapshot(self.cursor)
        members = []
        for ordinal in range(member_count):
            evidence = _insert_evidence(self.cursor)
            members.append(_insert_member(self.cursor, snapshot_id, evidence, ordinal)[0])
        snapshot_digest = None
        if sealed:
            _, snapshot_digest = _seal_snapshot(self.cursor, snapshot_id, member_count)
        suffix = uuid.uuid4().hex
        self.cursor.execute(
            "INSERT INTO substances(preferred_name,normalized_name,substance_type,status) "
            "VALUES(%s,%s,'chemical_substance','active') RETURNING id",
            (f"Runtime substance {suffix}", f"runtime_substance_{suffix}"),
        )
        substance_id = self.cursor.fetchone()[0]
        as_of = datetime.now(timezone.utc) + timedelta(seconds=2)
        canonical_input = ScientificMappingStateService().build_evaluation_input(
            self.cursor,
            CanonicalEvaluationInputRequest("substance", substance_id, as_of),
        )
        return {
            "protocol_id": protocol_id,
            "protocol_digest": protocol_digest,
            "snapshot_id": snapshot_id,
            "snapshot_digest": None if snapshot_digest is None else bytes(snapshot_digest),
            "members": tuple(members),
            "substance_id": substance_id,
            "canonical_input": canonical_input,
        }

    def _request(
        self,
        fixture,
        *,
        mode="NORMAL",
        comparison=None,
        configuration=None,
        scope=None,
        key=None,
        snapshot_id=None,
    ):
        target = fixture["canonical_input"].target.artifact.artifact
        input_artifact = fixture["canonical_input"].input_artifact.artifact
        return SemanticExecutionRequest(
            protocol_version_id=fixture["protocol_id"],
            evidence_snapshot_id=snapshot_id or fixture["snapshot_id"],
            target_type="substance",
            target_id=fixture["substance_id"],
            target_artifact_id=target.id,
            target_digest=target.content_digest,
            mapping_state_artifact_id=None,
            input_artifact_id=input_artifact.id,
            input_digest=input_artifact.content_digest,
            execution_mode=mode,
            configuration=configuration or ExecutionConfiguration("wye-scientific", "2026.1"),
            requested_by="test:runtime",
            comparison_execution_id=comparison,
            idempotency_scope=scope,
            idempotency_key=key,
        )

    @staticmethod
    def _build(semantic_compatibility_version="2026.1"):
        return EngineBuild(
            "wye-scientific",
            semantic_compatibility_version,
            "runtime-fixture-r1",
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "python-c14n-1",
        )

    def _start(self, execution_id, *, build=None):
        now = datetime.now(timezone.utc)
        return self.service.start_attempt(
            self.cursor,
            AttemptStartRequest(
                execution_id,
                build or self._build(),
                uuid.uuid4(),
                now,
                now + timedelta(minutes=5),
                "test:worker",
            ),
        )

    def _output(self, members=(), *, marker="canonical"):
        decisions = tuple(
            SelectionDecisionInput(
                member,
                "included",
                "contributing",
                "resolved",
                "wye.fixture.selection",
                "1",
                "fixture_included",
                {"marker": marker},
            )
            for member in members
        )
        return PublicationOutputInput(
            decisions=decisions,
            result_kind="substance_assessment",
            result_schema_version="1",
            scientific_status_namespace="wye.scientific.status",
            scientific_status_version="1",
            scientific_status_code="insufficient_evidence",
            result_content={"state": "not_computable", "marker": marker},
            components=(
                ResultComponentInput(
                    "generic_scientific_state", "1", "primary", {"state": "unknown"}
                ),
            ),
            trace_schema_version="1",
            trace_content={"edges": [], "nodes": [], "marker": marker},
            published_by="test:publisher",
        )

    def _publish(self, fixture, *, marker="canonical"):
        execution = self.service.create_or_reuse_execution(
            self.cursor, self._request(fixture)
        )
        attempt = self._start(execution.execution["id"])
        publication = self.service.publish(
            self.cursor,
            execution_id=execution.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=self._output(fixture["members"], marker=marker),
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        return execution, attempt, publication

    def _artifact_payload(self, artifact_id):
        self.cursor.execute(
            "SELECT json_payload FROM scientific_evaluation_artifacts WHERE id=%s",
            (artifact_id,),
        )
        return self.cursor.fetchone()[0]["payload"]

    def _replay_output(self, publication):
        return ReplayOutputInput(
            self._artifact_payload(publication.selection_artifact.artifact.id),
            self._artifact_payload(publication.result_artifact.artifact.id),
            self._artifact_payload(publication.trace_artifact.artifact.id),
        )

    def test_normal_creation_reuse_and_root_verification(self):
        fixture = self._fixture()
        request = self._request(fixture)
        first = self.service.create_or_reuse_execution(self.cursor, request)
        second = self.service.create_or_reuse_execution(self.cursor, request)
        self.assertFalse(first.execution_reused)
        self.assertTrue(second.execution_reused)
        self.assertEqual(first.execution["id"], second.execution["id"])
        self.assertEqual(
            bytes(first.execution["semantic_execution_digest"]),
            first.identity_artifact.artifact.content_digest,
        )

    def test_building_snapshot_is_rejected(self):
        fixture = self._fixture(sealed=False)
        with self.assertRaises(UnsealedEvidenceSnapshotError):
            self.service.create_or_reuse_execution(self.cursor, self._request(fixture))

    def test_idempotency_reuse_and_conflict(self):
        fixture = self._fixture()
        first = self.service.create_or_reuse_execution(
            self.cursor, self._request(fixture, scope="api", key="request-1")
        )
        second = self.service.create_or_reuse_execution(
            self.cursor, self._request(fixture, scope="api", key="request-1")
        )
        self.assertEqual(first.execution["id"], second.execution["id"])
        self.assertTrue(second.idempotency_reused)
        with self.assertRaises(ExecutionIdempotencyConflictError):
            self.service.create_or_reuse_execution(
                self.cursor,
                self._request(
                    fixture,
                    configuration=ExecutionConfiguration("wye-scientific", "2026.2"),
                    scope="api",
                    key="request-1",
                ),
            )

    def test_attempt_start_heartbeat_and_success_requires_atomic_output(self):
        fixture = self._fixture()
        execution = self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
        attempt = self._start(execution.execution["id"])
        now = datetime.now(timezone.utc) + timedelta(seconds=1)
        heartbeat = self.service.heartbeat_attempt(
            self.cursor,
            attempt_id=attempt.attempt["id"],
            lease_token=uuid.UUID(str(attempt.attempt["lease_token"])),
            heartbeat_at=now,
            lease_expires_at=now + timedelta(minutes=7),
        )
        self.assertEqual(heartbeat["attempt_status"], "running")
        self.service.mark_attempt_succeeded(self.cursor, attempt.attempt["id"])
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_heartbeat_cannot_move_backwards(self):
        fixture = self._fixture()
        execution = self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
        attempt = self._start(execution.execution["id"])
        old = attempt.attempt["heartbeat_at"] - timedelta(seconds=1)
        with self.assertRaises(InvalidExecutionAttemptTransitionError):
            self.service.heartbeat_attempt(
                self.cursor,
                attempt_id=attempt.attempt["id"],
                lease_token=uuid.UUID(str(attempt.attempt["lease_token"])),
                heartbeat_at=old,
                lease_expires_at=attempt.attempt["lease_expires_at"],
            )

    def test_retryable_failure_preserves_attempt_and_allows_retry(self):
        fixture = self._fixture()
        execution = self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
        first = self._start(execution.execution["id"])
        closed = self.service.fail_attempt(
            self.cursor,
            first.attempt["id"],
            AttemptError("resource", "temporary_capacity", True, "bounded fixture"),
        )
        second = self._start(execution.execution["id"])
        self.assertEqual(closed["attempt_status"], "failed")
        self.assertEqual(second.attempt["attempt_number"], 2)

    def test_nonretryable_failure_blocks_new_attempt(self):
        fixture = self._fixture()
        execution = self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
        attempt = self._start(execution.execution["id"])
        self.service.fail_attempt(
            self.cursor,
            attempt.attempt["id"],
            AttemptError("validation", "invalid_canonical_output", False),
        )
        with self.assertRaises(NonRetryableExecutionError):
            self._start(execution.execution["id"])

    def test_atomic_publication_persists_selection_result_components_and_trace(self):
        fixture = self._fixture(member_count=1)
        execution, _, publication = self._publish(fixture)
        self.assertFalse(publication.publication_reused)
        for table, expected in (
            ("scientific_evidence_selection_decisions", 1),
            ("scientific_evaluation_results", 1),
            ("scientific_evaluation_result_components", 1),
            ("scientific_evaluation_traces", 1),
            ("scientific_evaluation_publications", 1),
        ):
            self.cursor.execute(
                f"SELECT count(*) FROM {table} WHERE execution_id=%s"
                if table != "scientific_evaluation_result_components"
                else "SELECT count(*) FROM scientific_evaluation_result_components c "
                "JOIN scientific_evaluation_results r ON r.id=c.result_id WHERE r.execution_id=%s",
                (execution.execution["id"],),
            )
            self.assertEqual(self.cursor.fetchone()[0], expected)

    def test_zero_member_publication_and_identical_retry(self):
        fixture = self._fixture()
        execution, attempt, first = self._publish(fixture)
        second = self.service.publish(
            self.cursor,
            execution_id=execution.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=self._output(),
        )
        self.assertTrue(second.publication_reused)
        self.assertEqual(first.publication["id"], second.publication["id"])

    def test_incomplete_selection_coverage_fails_before_relational_output(self):
        fixture = self._fixture(member_count=1)
        execution = self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
        attempt = self._start(execution.execution["id"])
        with self.assertRaises(IncompleteSelectionCoverageError):
            self.service.publish(
                self.cursor,
                execution_id=execution.execution["id"],
                attempt_id=attempt.attempt["id"],
                output=self._output(()),
            )
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_results WHERE execution_id=%s",
            (execution.execution["id"],),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_post_publication_component_mutation_is_rejected(self):
        fixture = self._fixture()
        execution, _, publication = self._publish(fixture)
        self.connection.commit()
        self.cursor.close()
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            "SELECT id FROM scientific_evaluation_results WHERE execution_id=%s",
            (execution.execution["id"],),
        )
        result_id = self.cursor.fetchone()[0]
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_result_components(result_id,component_kind,"
            "component_schema_version,component_role,component_artifact_id,component_digest,component_ordinal) "
            "VALUES(%s,'late','1','late',%s,%s,99)",
            (
                result_id,
                publication.result_artifact.artifact.id,
                publication.result_artifact.artifact.content_digest,
            ),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_replay_matched_reuses_global_artifacts_without_scientific_rows(self):
        fixture = self._fixture()
        normal, _, publication = self._publish(fixture)
        replay = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(fixture, mode="REPLAY", comparison=normal.execution["id"]),
        )
        attempt = self._start(replay.execution["id"])
        verification = self.service.verify_replay(
            self.cursor,
            execution_id=replay.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=self._replay_output(publication),
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(verification.verification["verification_status"], "matched")
        self.assertEqual(
            verification.result_artifact.artifact.id, publication.result_artifact.artifact.id
        )
        for table in (
            "scientific_evidence_selection_decisions",
            "scientific_evaluation_results",
            "scientific_evaluation_traces",
            "scientific_evaluation_publications",
        ):
            self.cursor.execute(
                f"SELECT count(*) FROM {table} WHERE execution_id=%s",
                (replay.execution["id"],),
            )
            self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_replay_mismatch_completes_without_replacing_publication(self):
        fixture = self._fixture()
        normal, _, publication = self._publish(fixture)
        replay = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(fixture, mode="REPLAY", comparison=normal.execution["id"]),
        )
        attempt = self._start(replay.execution["id"])
        output = self._replay_output(publication)
        changed_trace = dict(output.trace_payload)
        changed_trace["content"] = {
            "edges": [],
            "nodes": [],
            "marker": "different_non_numeric_trace",
        }
        verification = self.service.verify_replay(
            self.cursor,
            execution_id=replay.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=ReplayOutputInput(
                output.selection_manifest_payload, output.result_payload, changed_trace
            ),
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(verification.verification["verification_status"], "mismatch")
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_publications WHERE execution_id=%s",
            (normal.execution["id"],),
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)

    def test_replay_verification_retry_reuses_one_canonical_row(self):
        fixture = self._fixture()
        normal, _, publication = self._publish(fixture)
        replay = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(fixture, mode="REPLAY", comparison=normal.execution["id"]),
        )
        attempt = self._start(replay.execution["id"])
        output = self._replay_output(publication)
        first = self.service.verify_replay(
            self.cursor,
            execution_id=replay.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=output,
        )
        second = self.service.verify_replay(
            self.cursor,
            execution_id=replay.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=output,
        )
        self.assertFalse(first.verification_reused)
        self.assertTrue(second.verification_reused)
        self.assertEqual(first.verification["id"], second.verification["id"])

    def test_replay_rejects_wrong_output_artifact_contract(self):
        fixture = self._fixture()
        normal, _, publication = self._publish(fixture)
        replay = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(fixture, mode="REPLAY", comparison=normal.execution["id"]),
        )
        attempt = self._start(replay.execution["id"])
        output = self._replay_output(publication)
        wrong = dict(output.result_payload)
        wrong["artifact_type"] = "scientific_evaluation_trace"
        with self.assertRaises(IncompatibleCanonicalOutputError):
            self.service.verify_replay(
                self.cursor,
                execution_id=replay.execution["id"],
                attempt_id=attempt.attempt["id"],
                output=ReplayOutputInput(
                    output.selection_manifest_payload, wrong, output.trace_payload
                ),
            )

    def test_replay_failure_has_no_verification_and_can_retry(self):
        fixture = self._fixture()
        normal, _, _ = self._publish(fixture)
        replay = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(fixture, mode="REPLAY", comparison=normal.execution["id"]),
        )
        attempt = self._start(replay.execution["id"])
        self.service.fail_attempt(
            self.cursor,
            attempt.attempt["id"],
            AttemptError("resource", "transient_failure", True),
        )
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_replay_verifications WHERE execution_id=%s",
            (replay.execution["id"],),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)
        self.assertEqual(self._start(replay.execution["id"]).attempt["attempt_number"], 2)

    def test_replay_requires_comparison_publication_and_same_configuration(self):
        fixture = self._fixture()
        comparison = self.service.create_or_reuse_execution(
            self.cursor, self._request(fixture)
        )
        with self.assertRaises(ReplayComparisonUnavailableError):
            self.service.create_or_reuse_execution(
                self.cursor,
                self._request(
                    fixture, mode="REPLAY", comparison=comparison.execution["id"]
                ),
            )
        self.connection.rollback()

    def test_refresh_creation_requires_same_target_and_changed_root(self):
        fixture = self._fixture()
        normal, _, _ = self._publish(fixture)
        refreshed_snapshot, _ = _insert_snapshot(self.cursor)
        _seal_snapshot(self.cursor, refreshed_snapshot, 0)
        refresh = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(
                fixture,
                mode="REFRESH",
                comparison=normal.execution["id"],
                snapshot_id=refreshed_snapshot,
            ),
        )
        self.assertEqual(refresh.execution["execution_mode"], "REFRESH")
        self.assertEqual(refresh.execution["evidence_snapshot_id"], refreshed_snapshot)
        attempt = self._start(refresh.execution["id"])
        publication = self.service.publish(
            self.cursor,
            execution_id=refresh.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=self._output(),
        )
        self.assertEqual(publication.publication["execution_id"], refresh.execution["id"])

    def test_incompatible_publication_retry_is_rejected(self):
        fixture = self._fixture()
        execution, attempt, _ = self._publish(fixture)
        with self.assertRaises(ExecutionPublicationConflictError):
            self.service.publish(
                self.cursor,
                execution_id=execution.execution["id"],
                attempt_id=attempt.attempt["id"],
                output=self._output(marker="incompatible-retry"),
            )

    def test_counterfactual_requires_governance_but_service_does_not_create_it(self):
        fixture = self._fixture()
        normal, _, _ = self._publish(fixture)
        counterfactual = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(
                fixture,
                mode="COUNTERFACTUAL",
                comparison=normal.execution["id"],
                configuration=ExecutionConfiguration("wye-scientific", "2026.2"),
            ),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.connection.rollback()

        fixture = self._fixture()
        normal, _, _ = self._publish(fixture)
        counterfactual = self.service.create_or_reuse_execution(
            self.cursor,
            self._request(
                fixture,
                mode="COUNTERFACTUAL",
                comparison=normal.execution["id"],
                configuration=ExecutionConfiguration("wye-scientific", "2026.2"),
            ),
        )
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_governance_events(event_key,entity_type,execution_id,"
            "event_type,actor_identifier,reason_code,effective_at) "
            "VALUES(%s,'evaluation_execution',%s,'counterfactual_authorized',"
            "'reviewer:test','authorized_test',NOW())",
            (str(uuid.uuid4()), counterfactual.execution["id"]),
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        attempt = self._start(counterfactual.execution["id"], build=self._build("2026.2"))
        publication = self.service.publish(
            self.cursor,
            execution_id=counterfactual.execution["id"],
            attempt_id=attempt.attempt["id"],
            output=self._output(),
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(
            publication.publication["execution_id"], counterfactual.execution["id"]
        )

    def test_transaction_rollback_removes_execution_and_artifacts(self):
        fixture = self._fixture()
        self.connection.commit()
        self.cursor.close()
        self.cursor = self.connection.cursor()
        created = self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
        digest = bytes(created.execution["semantic_execution_digest"])
        self.connection.rollback()
        self.cursor.close()
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_executions WHERE semantic_execution_digest=%s",
            (digest,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_concurrent_identical_creation_converges(self):
        fixture = self._fixture()
        request = self._request(fixture)
        self.connection.commit()
        barrier = threading.Barrier(2)
        results = []
        failures = []

        def worker():
            connection = _connection(self.database)
            connection.autocommit = False
            try:
                with connection.cursor() as cursor:
                    barrier.wait(timeout=10)
                    result = ScientificEvaluationExecutionService().create_or_reuse_execution(
                        cursor, request
                    )
                    connection.commit()
                    results.append(result.execution["id"])
            except Exception as exc:  # pragma: no cover - surfaced by assertion
                connection.rollback()
                failures.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(len(set(results)), 1)

    def test_concurrent_attempt_start_allows_one_active_attempt(self):
        fixture = self._fixture()
        execution = self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
        execution_id = execution.execution["id"]
        self.connection.commit()
        barrier = threading.Barrier(2)
        successes = []
        failures = []

        def worker():
            connection = _connection(self.database)
            connection.autocommit = False
            now = datetime.now(timezone.utc)
            try:
                with connection.cursor() as cursor:
                    barrier.wait(timeout=10)
                    result = ScientificEvaluationExecutionService().start_attempt(
                        cursor,
                        AttemptStartRequest(
                            execution_id,
                            self._build(),
                            uuid.uuid4(),
                            now,
                            now + timedelta(minutes=5),
                            "test:concurrent-worker",
                        ),
                    )
                    connection.commit()
                    successes.append(result.attempt["id"])
            except Exception as exc:
                connection.rollback()
                failures.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], ActiveExecutionAttemptError)

    def test_legacy_scoring_tables_are_not_touched(self):
        fixture = self._fixture()
        for table in ("product_scores", "ingredient_risk_profiles", "ingredient_evidence"):
            self.cursor.execute(f"SELECT count(*) FROM {table}")
            before = self.cursor.fetchone()[0]
            self.service.create_or_reuse_execution(self.cursor, self._request(fixture))
            self.cursor.execute(f"SELECT count(*) FROM {table}")
            self.assertEqual(self.cursor.fetchone()[0], before)


if __name__ == "__main__":
    unittest.main()
