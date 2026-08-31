"""PostgreSQL lifecycle and integrity tests for migration 0021."""

from hashlib import sha256
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
    _insert_artifact,
    _insert_evidence,
    _insert_member,
    _insert_snapshot,
    _seal_snapshot,
)
from test_scientific_evaluation_foundation import (  # noqa: E402
    _publish_protocol_version,
)


REVISION = "0021_scientific_evaluation_publication"
PARENT_REVISION = "0020_scientific_evidence_snapshots"
TABLES = (
    "scientific_evaluation_executions",
    "scientific_evaluation_execution_attempts",
    "scientific_evidence_selection_decisions",
    "scientific_evaluation_results",
    "scientific_evaluation_result_components",
    "scientific_evaluation_traces",
    "scientific_evaluation_publications",
    "scientific_evaluation_replay_verifications",
    "scientific_evaluation_idempotency_keys",
)


def _artifact(cursor, kind, seed=None, located=True):
    return _insert_artifact(cursor, kind, seed or uuid.uuid4().hex, located=located)


@unittest.skipUnless(
    os.getenv("WYE_RUN_EXECUTION_PERSISTENCE_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvaluationExecutionPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = _create_database("execution_publication")
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

    def tearDown(self):
        try:
            self.connection.rollback()
        finally:
            self.cursor.close()
            self.connection.close()

    def _foundation(self, *, seal=True, member_count=0):
        _, version_id, _, _ = _publish_protocol_version(self.connection)
        self.cursor.execute(
            "SELECT protocol_digest FROM scientific_evaluation_protocol_versions WHERE id=%s",
            (version_id,),
        )
        protocol_digest = self.cursor.fetchone()[0]
        snapshot_id, _ = _insert_snapshot(self.cursor)
        member_ids = []
        for ordinal in range(member_count):
            evidence = _insert_evidence(self.cursor)
            member_ids.append(_insert_member(self.cursor, snapshot_id, evidence, ordinal)[0])
        if seal:
            _, snapshot_digest = _seal_snapshot(self.cursor, snapshot_id, member_count)
        else:
            snapshot_digest = b"x" * 32
        self.cursor.execute(
            "INSERT INTO substances(preferred_name,normalized_name,substance_type,status) "
            "VALUES(%s,%s,'chemical_substance','active') RETURNING id",
            (f"Execution substance {uuid.uuid4().hex}", uuid.uuid4().hex),
        )
        substance_id = self.cursor.fetchone()[0]
        roots = {}
        for key, kind in (
            ("target", "scientific_evaluation_target"),
            ("input", "scientific_evaluation_input"),
            ("configuration", "scientific_evaluation_configuration"),
            ("identity", "scientific_evaluation_execution_identity"),
        ):
            roots[key] = _artifact(self.cursor, kind)
        self.connection.commit()
        self.cursor = self.connection.cursor()
        return {
            "protocol_version_id": version_id,
            "protocol_digest": protocol_digest,
            "snapshot_id": snapshot_id,
            "snapshot_digest": snapshot_digest,
            "substance_id": substance_id,
            "member_ids": member_ids,
            "roots": roots,
        }

    def _execution(self, fixture, *, status="pending", mode="NORMAL", comparison=None):
        started = "NOW()" if status != "pending" else "NULL"
        completed = "NOW()" if status in ("completed", "failed", "cancelled") else "NULL"
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_executions("
            "execution_key,protocol_version_id,evidence_snapshot_id,target_type,substance_id,"
            "target_artifact_id,input_artifact_id,configuration_artifact_id,semantic_identity_artifact_id,"
            "comparison_execution_id,execution_mode,protocol_digest,evidence_snapshot_digest,input_digest,"
            "configuration_digest,semantic_execution_digest,technical_status,requested_by,requested_at,"
            "started_at,completed_at) VALUES(%s,%s,%s,'substance',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
            f"%s,'test_actor',NOW(),{started},{completed}) RETURNING id",
            (
                str(uuid.uuid4()), fixture["protocol_version_id"], fixture["snapshot_id"],
                fixture["substance_id"], fixture["roots"]["target"][0],
                fixture["roots"]["input"][0], fixture["roots"]["configuration"][0],
                fixture["roots"]["identity"][0], comparison, mode,
                fixture["protocol_digest"], fixture["snapshot_digest"],
                fixture["roots"]["input"][1], fixture["roots"]["configuration"][1],
                fixture["roots"]["identity"][1], status,
            ),
        )
        return self.cursor.fetchone()[0]

    def _attempt(self, execution_id, *, build=None):
        build = build or _artifact(self.cursor, "scientific_evaluation_engine_build")
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_execution_attempts("
            "attempt_key,execution_id,attempt_number,engine_build_artifact_id,worker_id,lease_token,"
            "lease_expires_at,heartbeat_at,started_at) "
            "VALUES(%s,%s,1,%s,'worker:test',%s,NOW()+INTERVAL '5 minutes',NOW(),NOW()) RETURNING id",
            (str(uuid.uuid4()), execution_id, build[0], str(uuid.uuid4())),
        )
        return self.cursor.fetchone()[0]

    def _publish_zero_member(self, execution_id, attempt_id):
        result_artifact = _artifact(self.cursor, "scientific_evaluation_result")
        trace_artifact = _artifact(self.cursor, "scientific_evaluation_trace")
        selection_artifact = _artifact(self.cursor, "scientific_evidence_selection_manifest")
        bundle_artifact = _artifact(self.cursor, "scientific_evaluation_publication_bundle")
        self.cursor.execute(
            "SELECT protocol_digest,evidence_snapshot_digest,input_digest FROM scientific_evaluation_executions WHERE id=%s",
            (execution_id,),
        )
        protocol_digest, snapshot_digest, input_digest = self.cursor.fetchone()
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_results(result_key,execution_id,result_kind,result_schema_version,"
            "scientific_status_namespace,scientific_status_version,scientific_status_code,canonical_artifact_id,result_digest) "
            "VALUES(%s,%s,'substance_assessment','1','wye.scientific.status','1','insufficient_evidence',%s,%s) RETURNING id",
            (str(uuid.uuid4()), execution_id, result_artifact[0], result_artifact[1]),
        )
        result_id = self.cursor.fetchone()[0]
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_traces(trace_key,execution_id,result_id,trace_schema_version,"
            "canonical_artifact_id,trace_digest,result_digest,selection_digest,protocol_digest,evidence_snapshot_digest,input_digest) "
            "VALUES(%s,%s,%s,'1',%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (str(uuid.uuid4()), execution_id, result_id, trace_artifact[0], trace_artifact[1],
             result_artifact[1], selection_artifact[1], protocol_digest, snapshot_digest, input_digest),
        )
        trace_id = self.cursor.fetchone()[0]
        self.cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET attempt_status='succeeded',ended_at=NOW(),"
            "lease_token=NULL,lease_expires_at=NULL,heartbeat_at=NULL WHERE id=%s",
            (attempt_id,),
        )
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='completed',completed_at=NOW() WHERE id=%s",
            (execution_id,),
        )
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_publications(publication_key,execution_id,result_id,trace_id,"
            "successful_attempt_id,selection_manifest_artifact_id,bundle_artifact_id,selection_digest,result_digest,"
            "trace_digest,publication_bundle_digest,published_by,published_at) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'publisher:test',NOW()) RETURNING id",
            (str(uuid.uuid4()), execution_id, result_id, trace_id, attempt_id,
             selection_artifact[0], bundle_artifact[0], selection_artifact[1], result_artifact[1],
             trace_artifact[1], bundle_artifact[1]),
        )
        return self.cursor.fetchone()[0], result_id, trace_id

    def _publication_output(self, publication_id):
        self.cursor.execute(
            "SELECT p.publication_bundle_digest,p.selection_manifest_artifact_id,p.selection_digest,"
            "r.canonical_artifact_id,p.result_digest,t.canonical_artifact_id,p.trace_digest "
            "FROM scientific_evaluation_publications p "
            "JOIN scientific_evaluation_results r ON r.id=p.result_id "
            "JOIN scientific_evaluation_traces t ON t.id=p.trace_id WHERE p.id=%s",
            (publication_id,),
        )
        row = self.cursor.fetchone()
        return {
            "bundle_digest": row[0],
            "selection_artifact_id": row[1],
            "selection_digest": row[2],
            "result_artifact_id": row[3],
            "result_digest": row[4],
            "trace_artifact_id": row[5],
            "trace_digest": row[6],
        }

    def _replay_execution(self, fixture, comparison_execution_id):
        replay_fixture = dict(fixture)
        replay_fixture["roots"] = dict(fixture["roots"])
        replay_fixture["roots"]["identity"] = _artifact(
            self.cursor, "scientific_evaluation_execution_identity"
        )
        return self._execution(
            replay_fixture, mode="REPLAY", comparison=comparison_execution_id
        )

    def _start_attempt(self, execution_id):
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='running',"
            "started_at=NOW() WHERE id=%s",
            (execution_id,),
        )
        return self._attempt(execution_id)

    def _insert_replay_verification(
        self,
        execution_id,
        comparison_publication_id,
        attempt_id,
        *,
        status="matched",
        expected=None,
        recomputed=None,
        verification_artifact=None,
    ):
        comparison = self._publication_output(comparison_publication_id)
        expected = expected or comparison
        recomputed = recomputed or comparison
        verification_artifact = verification_artifact or _artifact(
            self.cursor, "scientific_evaluation_replay_verification"
        )
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_replay_verifications(verification_key,execution_id,"
            "comparison_publication_id,successful_attempt_id,verification_artifact_id,verification_digest,"
            "expected_publication_bundle_digest,expected_selection_digest,expected_result_digest,"
            "expected_trace_digest,recomputed_selection_artifact_id,recomputed_result_artifact_id,"
            "recomputed_trace_artifact_id,recomputed_selection_digest,recomputed_result_digest,"
            "recomputed_trace_digest,verification_status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
            "%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (
                str(uuid.uuid4()), execution_id, comparison_publication_id, attempt_id,
                verification_artifact[0], verification_artifact[1], expected["bundle_digest"],
                expected["selection_digest"], expected["result_digest"], expected["trace_digest"],
                recomputed["selection_artifact_id"], recomputed["result_artifact_id"],
                recomputed["trace_artifact_id"], recomputed["selection_digest"],
                recomputed["result_digest"], recomputed["trace_digest"], status,
            ),
        )
        return self.cursor.fetchone()[0]

    def _finish_replay(self, execution_id, attempt_id):
        self.cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET attempt_status='succeeded',ended_at=NOW(),"
            "lease_token=NULL,lease_expires_at=NULL,heartbeat_at=NULL WHERE id=%s",
            (attempt_id,),
        )
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='completed',completed_at=NOW() "
            "WHERE id=%s",
            (execution_id,),
        )

    def _committed_normal_publication(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        attempt_id = self._start_attempt(execution_id)
        publication_id, _, _ = self._publish_zero_member(execution_id, attempt_id)
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.connection.commit()
        self.cursor = self.connection.cursor()
        return fixture, execution_id, attempt_id, publication_id

    def test_schema_has_exact_tables_columns_and_governance_extension(self):
        self.cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=ANY(%s)",
            (list(TABLES),),
        )
        self.assertEqual({row[0] for row in self.cursor.fetchall()}, set(TABLES))
        expected_columns = {
            "scientific_evaluation_executions": {
                "id", "execution_key", "protocol_version_id", "evidence_snapshot_id",
                "target_type", "substance_id", "ingredient_id", "target_artifact_id",
                "mapping_state_artifact_id", "input_artifact_id", "configuration_artifact_id",
                "semantic_identity_artifact_id", "comparison_execution_id", "execution_mode",
                "semantic_execution_digest", "technical_status", "requested_at", "created_at",
            },
            "scientific_evaluation_execution_attempts": {
                "id", "attempt_key", "execution_id", "attempt_number", "attempt_status",
                "engine_build_artifact_id", "lease_token", "lease_expires_at", "heartbeat_at",
                "error_category", "error_code", "error_artifact_id",
            },
            "scientific_evidence_selection_decisions": {
                "id", "execution_id", "snapshot_member_id", "decision", "selection_role",
                "resolution_state", "decision_artifact_id", "decision_digest",
            },
            "scientific_evaluation_results": {
                "id", "result_key", "execution_id", "result_kind", "result_schema_version",
                "scientific_status_code", "canonical_artifact_id", "result_digest",
            },
            "scientific_evaluation_result_components": {
                "id", "result_id", "component_kind", "component_role", "component_artifact_id",
                "component_digest", "component_ordinal",
            },
            "scientific_evaluation_traces": {
                "id", "trace_key", "execution_id", "result_id", "canonical_artifact_id",
                "trace_digest", "selection_digest", "protocol_digest", "input_digest",
            },
            "scientific_evaluation_publications": {
                "id", "publication_key", "execution_id", "result_id", "trace_id",
                "successful_attempt_id", "selection_manifest_artifact_id", "bundle_artifact_id",
                "publication_bundle_digest", "published_at",
            },
            "scientific_evaluation_replay_verifications": {
                "id", "verification_key", "execution_id", "comparison_publication_id",
                "successful_attempt_id", "verification_artifact_id", "verification_digest",
                "expected_publication_bundle_digest", "expected_selection_digest",
                "expected_result_digest", "expected_trace_digest",
                "recomputed_selection_artifact_id", "recomputed_result_artifact_id",
                "recomputed_trace_artifact_id", "recomputed_selection_digest",
                "recomputed_result_digest", "recomputed_trace_digest",
                "verification_status", "created_at",
            },
            "scientific_evaluation_idempotency_keys": {
                "id", "operation_type", "request_scope", "request_key",
                "expected_semantic_digest", "execution_id", "attempt_id", "publication_id",
            },
        }
        for table, required in expected_columns.items():
            self.cursor.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s",
                (table,),
            )
            self.assertTrue(required.issubset({row[0] for row in self.cursor.fetchall()}), table)
        self.cursor.execute(
            "SELECT count(*) FROM pg_constraint c WHERE c.conrelid=ANY(%s::regclass[]) "
            "AND c.contype='f' AND c.confdeltype<>'r'",
            ([f"public.{table}" for table in TABLES],),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)
        self.cursor.execute(
            "SELECT count(*) FROM pg_constraint c JOIN pg_class r ON r.oid=c.confrelid "
            "WHERE c.conrelid=ANY(%s::regclass[]) AND r.relname IN "
            "('product_scores','ingredient_risk_profiles','ingredient_evidence')",
            ([f"public.{table}" for table in TABLES],),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)
        self.cursor.execute(
            "SELECT tgname FROM pg_trigger WHERE tgrelid=ANY(%s::regclass[]) AND NOT tgisinternal",
            ([f"public.{table}" for table in TABLES],),
        )
        trigger_names = {row[0] for row in self.cursor.fetchall()}
        for name in (
            "trg_scientific_evaluation_executions_guard",
            "trg_scientific_evaluation_executions_validate",
            "trg_scientific_evaluation_attempts_guard",
            "trg_scientific_evaluation_attempts_validate",
            "trg_scientific_evaluation_publications_validate",
            "trg_scientific_evaluation_replay_verifications_immutable",
            "trg_scientific_evaluation_replay_verifications_validate",
            "trg_scientific_evaluation_idempotency_guard",
        ):
            self.assertIn(name, trigger_names)
        self.cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename=ANY(%s)",
            (list(TABLES),),
        )
        index_names = {row[0] for row in self.cursor.fetchall()}
        self.assertIn("uq_scientific_evaluation_execution_attempts_running", index_names)
        self.assertIn("idx_scientific_evaluation_publications_time", index_names)
        self.assertIn("idx_scientific_evaluation_replay_verifications_comparison", index_names)
        self.assertIn("idx_scientific_evaluation_replay_verifications_status", index_names)
        for constraint in (
            "uq_scientific_evaluation_results_artifact",
            "uq_scientific_evaluation_traces_artifact",
            "uq_scientific_evaluation_publications_selection_artifact",
        ):
            self.cursor.execute("SELECT 1 FROM pg_constraint WHERE conname=%s", (constraint,))
            self.assertIsNotNone(self.cursor.fetchone(), constraint)
        for column in (
            "recomputed_selection_artifact_id",
            "recomputed_result_artifact_id",
            "recomputed_trace_artifact_id",
        ):
            self.cursor.execute(
                "SELECT 1 FROM pg_constraint c JOIN unnest(c.conkey) AS key(attnum) ON TRUE "
                "JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=key.attnum "
                "WHERE c.conrelid='scientific_evaluation_replay_verifications'::regclass "
                "AND c.contype='u' AND a.attname=%s",
                (column,),
            )
            self.assertIsNone(self.cursor.fetchone(), column)
        self.cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='scientific_evaluation_governance_events' "
            "AND column_name IN ('execution_id','related_execution_id','result_id','related_result_id')"
        )
        self.assertEqual(len(self.cursor.fetchall()), 4)

    def test_valid_pending_execution_and_root_immutability(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute(
                "UPDATE scientific_evaluation_executions SET input_digest=%s WHERE id=%s",
                (b"z" * 32, execution_id),
            )

    def test_building_snapshot_is_rejected(self):
        fixture = self._foundation(seal=False)
        self._execution(fixture)
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_semantic_execution_digest_is_unique(self):
        fixture = self._foundation()
        self._execution(fixture)
        with self.assertRaises(psycopg2.Error):
            self._execution(fixture)

    def test_concurrent_semantic_execution_identity_elects_one(self):
        fixture = self._foundation()
        barrier = threading.Barrier(2)
        outcomes = []

        def worker():
            connection = _connection(self.database)
            try:
                with connection.cursor() as cursor:
                    barrier.wait()
                    cursor.execute(
                        "INSERT INTO scientific_evaluation_executions("
                        "execution_key,protocol_version_id,evidence_snapshot_id,target_type,substance_id,"
                        "target_artifact_id,input_artifact_id,configuration_artifact_id,semantic_identity_artifact_id,"
                        "execution_mode,protocol_digest,evidence_snapshot_digest,input_digest,configuration_digest,"
                        "semantic_execution_digest,requested_by,requested_at) "
                        "VALUES(%s,%s,%s,'substance',%s,%s,%s,%s,%s,'NORMAL',%s,%s,%s,%s,%s,'test',NOW())",
                        (str(uuid.uuid4()), fixture["protocol_version_id"], fixture["snapshot_id"],
                         fixture["substance_id"], fixture["roots"]["target"][0],
                         fixture["roots"]["input"][0], fixture["roots"]["configuration"][0],
                         fixture["roots"]["identity"][0], fixture["protocol_digest"],
                         fixture["snapshot_digest"], fixture["roots"]["input"][1],
                         fixture["roots"]["configuration"][1], fixture["roots"]["identity"][1]),
                    )
                connection.commit()
                outcomes.append("won")
            except psycopg2.Error:
                connection.rollback()
                outcomes.append("conflict")
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(15)
        self.assertEqual(sorted(outcomes), ["conflict", "won"])

    def test_counterfactual_requires_governance_authorization(self):
        fixture = self._foundation()
        comparison_id = self._execution(fixture)
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        fixture["roots"]["configuration"] = _artifact(
            self.cursor, "scientific_evaluation_configuration"
        )
        fixture["roots"]["identity"] = _artifact(
            self.cursor, "scientific_evaluation_execution_identity"
        )
        self._execution(
            fixture, mode="COUNTERFACTUAL", comparison=comparison_id
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_selection_member_must_belong_to_execution_snapshot(self):
        fixture = self._foundation(member_count=1)
        other = self._foundation(member_count=1)
        execution_id = self._execution(fixture)
        decision = _artifact(self.cursor, "scientific_evidence_selection_decision")
        self.cursor.execute(
            "INSERT INTO scientific_evidence_selection_decisions(execution_id,snapshot_member_id,decision,"
            "selection_role,resolution_state,reason_namespace,reason_version,primary_reason_code,"
            "decision_artifact_id,decision_digest) VALUES(%s,%s,'included','contributing','resolved',"
            "'wye.selection','1','included_by_protocol',%s,%s)",
            (execution_id, other["member_ids"][0], decision[0], decision[1]),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_running_attempt_requires_running_execution(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self._attempt(execution_id)
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_one_running_attempt_is_database_authoritative(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='running',started_at=NOW() WHERE id=%s",
            (execution_id,),
        )
        self._attempt(execution_id)
        with self.assertRaises(psycopg2.Error):
            self._attempt(execution_id)

    def test_attempt_terminal_history_is_immutable(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='running',started_at=NOW() WHERE id=%s",
            (execution_id,),
        )
        attempt_id = self._attempt(execution_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET attempt_status='failed',ended_at=NOW(),"
            "lease_token=NULL,lease_expires_at=NULL,heartbeat_at=NULL,error_category='unexpected',"
            "error_code='test_failure',retryable=TRUE WHERE id=%s",
            (attempt_id,),
        )
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='pending' WHERE id=%s",
            (execution_id,),
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute(
                "UPDATE scientific_evaluation_execution_attempts SET error_code='changed' WHERE id=%s",
                (attempt_id,),
            )

    def test_running_to_pending_requires_retryable_failed_or_abandoned_attempt(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='running',started_at=NOW() "
            "WHERE id=%s",
            (execution_id,),
        )
        attempt_id = self._attempt(execution_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET attempt_status='failed',ended_at=NOW(),"
            "lease_token=NULL,lease_expires_at=NULL,heartbeat_at=NULL,error_category='unexpected',"
            "error_code='non_retryable_failure',retryable=FALSE WHERE id=%s",
            (attempt_id,),
        )
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='pending' WHERE id=%s",
            (execution_id,),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_partial_output_without_publication_is_rejected(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        result_artifact = _artifact(self.cursor, "scientific_evaluation_result")
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_results(result_key,execution_id,result_kind,result_schema_version,"
            "scientific_status_namespace,scientific_status_version,scientific_status_code,canonical_artifact_id,result_digest) "
            "VALUES(%s,%s,'test','1','test','1','non_numeric',%s,%s)",
            (str(uuid.uuid4()), execution_id, result_artifact[0], result_artifact[1]),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_atomic_zero_member_publication_and_immutability(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='running',started_at=NOW() WHERE id=%s",
            (execution_id,),
        )
        attempt_id = self._attempt(execution_id)
        publication_id, result_id, _ = self._publish_zero_member(execution_id, attempt_id)
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute(
                "UPDATE scientific_evaluation_results SET result_kind='changed' WHERE id=%s",
                (result_id,),
            )
        self.connection.rollback()
        self.cursor = self.connection.cursor()
        self.cursor.execute("SELECT 1 FROM scientific_evaluation_publications WHERE id=%s", (publication_id,))
        self.assertIsNone(self.cursor.fetchone())

    def test_matching_replay_reuses_global_artifacts_without_scientific_rows(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        expected = self._publication_output(publication_id)
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        verification_id = self._insert_replay_verification(
            replay_id, publication_id, attempt_id
        )
        self._finish_replay(replay_id, attempt_id)
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

        self.cursor.execute(
            "SELECT verification_status,recomputed_selection_artifact_id,"
            "recomputed_result_artifact_id,recomputed_trace_artifact_id "
            "FROM scientific_evaluation_replay_verifications WHERE id=%s",
            (verification_id,),
        )
        status, selection_id, result_id, trace_id = self.cursor.fetchone()
        self.assertEqual(status, "matched")
        self.assertEqual(selection_id, expected["selection_artifact_id"])
        self.assertEqual(result_id, expected["result_artifact_id"])
        self.assertEqual(trace_id, expected["trace_artifact_id"])
        for table in (
            "scientific_evidence_selection_decisions",
            "scientific_evaluation_results",
            "scientific_evaluation_traces",
            "scientific_evaluation_publications",
        ):
            self.cursor.execute(f"SELECT count(*) FROM {table} WHERE execution_id=%s", (replay_id,))
            self.assertEqual(self.cursor.fetchone()[0], 0, table)
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_result_components c "
            "JOIN scientific_evaluation_results r ON r.id=c.result_id WHERE r.execution_id=%s",
            (replay_id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)
        self.cursor.execute(
            "SELECT selection_digest,result_digest,trace_digest,publication_bundle_digest "
            "FROM scientific_evaluation_publications WHERE id=%s",
            (publication_id,),
        )
        self.assertEqual(
            self.cursor.fetchone(),
            (
                expected["selection_digest"], expected["result_digest"],
                expected["trace_digest"], expected["bundle_digest"],
            ),
        )

    def test_mismatched_replay_completes_without_replacement_publication(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        comparison = self._publication_output(publication_id)
        recomputed = dict(comparison)
        recomputed_selection = _artifact(
            self.cursor, "scientific_evidence_selection_manifest"
        )
        recomputed["selection_artifact_id"] = recomputed_selection[0]
        recomputed["selection_digest"] = recomputed_selection[1]
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        verification_id = self._insert_replay_verification(
            replay_id,
            publication_id,
            attempt_id,
            status="mismatch",
            recomputed=recomputed,
        )
        self._finish_replay(replay_id, attempt_id)
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.cursor.execute(
            "SELECT verification_status,expected_selection_digest,recomputed_selection_digest "
            "FROM scientific_evaluation_replay_verifications WHERE id=%s",
            (verification_id,),
        )
        status, expected_digest, recomputed_digest = self.cursor.fetchone()
        self.assertEqual(status, "mismatch")
        self.assertNotEqual(expected_digest, recomputed_digest)
        self.cursor.execute(
            "SELECT technical_status FROM scientific_evaluation_executions WHERE id=%s",
            (replay_id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], "completed")
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_publications WHERE execution_id=%s",
            (replay_id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)
        self.cursor.execute("SELECT count(*) FROM scientific_evaluation_publications WHERE id=%s", (publication_id,))
        self.assertEqual(self.cursor.fetchone()[0], 1)

    def test_replay_runtime_error_is_attempt_history_without_verification(self):
        fixture, comparison_id, _, _ = self._committed_normal_publication()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET attempt_status='failed',ended_at=NOW(),"
            "lease_token=NULL,lease_expires_at=NULL,heartbeat_at=NULL,error_category='unexpected',"
            "error_code='replay_runtime_error',retryable=TRUE WHERE id=%s",
            (attempt_id,),
        )
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='pending' WHERE id=%s",
            (replay_id,),
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.cursor.execute(
            "SELECT attempt_status,retryable FROM scientific_evaluation_execution_attempts WHERE id=%s",
            (attempt_id,),
        )
        self.assertEqual(self.cursor.fetchone(), ("failed", True))
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_replay_verifications WHERE execution_id=%s",
            (replay_id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_publications WHERE execution_id=%s",
            (replay_id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_replay_publication_is_rejected(self):
        fixture, comparison_id, _, _ = self._committed_normal_publication()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        self._publish_zero_member(replay_id, attempt_id)
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_replay_completion_without_verification_is_rejected(self):
        fixture, comparison_id, _, _ = self._committed_normal_publication()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        self._finish_replay(replay_id, attempt_id)
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_replay_verification_rejects_attempt_owned_by_other_execution(self):
        fixture, comparison_id, comparison_attempt_id, publication_id = (
            self._committed_normal_publication()
        )
        replay_id = self._replay_execution(fixture, comparison_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='running',started_at=NOW() WHERE id=%s",
            (replay_id,),
        )
        self._insert_replay_verification(
            replay_id, publication_id, comparison_attempt_id
        )
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='completed',completed_at=NOW() WHERE id=%s",
            (replay_id,),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_replay_verification_rejects_non_succeeded_attempt(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        self._insert_replay_verification(replay_id, publication_id, attempt_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET attempt_status='failed',ended_at=NOW(),"
            "lease_token=NULL,lease_expires_at=NULL,heartbeat_at=NULL,error_category='unexpected',"
            "error_code='not_a_success',retryable=FALSE WHERE id=%s",
            (attempt_id,),
        )
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='completed',completed_at=NOW() WHERE id=%s",
            (replay_id,),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_replay_expected_roots_must_come_from_comparison_publication(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        comparison = self._publication_output(publication_id)
        expected = dict(comparison)
        expected["selection_digest"] = sha256(b"caller-controlled-expected-root").digest()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        self._insert_replay_verification(
            replay_id,
            publication_id,
            attempt_id,
            status="mismatch",
            expected=expected,
        )
        self._finish_replay(replay_id, attempt_id)
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_replay_status_must_match_digest_equality(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        comparison = self._publication_output(publication_id)
        different = dict(comparison)
        selection = _artifact(self.cursor, "scientific_evidence_selection_manifest")
        different["selection_artifact_id"] = selection[0]
        different["selection_digest"] = selection[1]

        self.cursor.execute("SAVEPOINT replay_status_mismatch_equal")
        with self.assertRaises(psycopg2.Error):
            self._insert_replay_verification(
                replay_id, publication_id, attempt_id, status="mismatch"
            )
        self.cursor.execute("ROLLBACK TO SAVEPOINT replay_status_mismatch_equal")

        self.cursor.execute("SAVEPOINT replay_status_matched_different")
        with self.assertRaises(psycopg2.Error):
            self._insert_replay_verification(
                replay_id,
                publication_id,
                attempt_id,
                status="matched",
                recomputed=different,
            )
        self.cursor.execute("ROLLBACK TO SAVEPOINT replay_status_matched_different")

        self.cursor.execute("SAVEPOINT replay_status_valid_mismatch")
        self._insert_replay_verification(
            replay_id,
            publication_id,
            attempt_id,
            status="mismatch",
            recomputed=different,
        )
        self.cursor.execute("ROLLBACK TO SAVEPOINT replay_status_valid_mismatch")

    def test_replay_artifact_roles_are_validated(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        comparison = self._publication_output(publication_id)
        cases = (
            ("verification", "scientific_evaluation_result"),
            ("selection", "scientific_evaluation_trace"),
            ("result", "scientific_evaluation_trace"),
            ("trace", "scientific_evaluation_result"),
        )
        for index, (role, wrong_kind) in enumerate(cases):
            with self.subTest(role=role):
                savepoint = f"wrong_replay_role_{index}"
                self.cursor.execute(f"SAVEPOINT {savepoint}")
                replay_id = self._replay_execution(fixture, comparison_id)
                attempt_id = self._start_attempt(replay_id)
                recomputed = dict(comparison)
                verification_artifact = None
                wrong = _artifact(self.cursor, wrong_kind)
                status = "matched"
                if role == "verification":
                    verification_artifact = wrong
                else:
                    recomputed[f"{role}_artifact_id"] = wrong[0]
                    recomputed[f"{role}_digest"] = wrong[1]
                    status = "mismatch"
                self._insert_replay_verification(
                    replay_id,
                    publication_id,
                    attempt_id,
                    status=status,
                    recomputed=recomputed,
                    verification_artifact=verification_artifact,
                )
                self._finish_replay(replay_id, attempt_id)
                with self.assertRaises(psycopg2.Error):
                    self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                self.cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                self.cursor.execute("SET CONSTRAINTS ALL DEFERRED")

    def test_replay_completion_accepts_final_state_independent_of_statement_order(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        self._finish_replay(replay_id, attempt_id)
        self._insert_replay_verification(replay_id, publication_id, attempt_id)
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_replay_verification_is_insert_only(self):
        fixture, comparison_id, _, publication_id = self._committed_normal_publication()
        replay_id = self._replay_execution(fixture, comparison_id)
        attempt_id = self._start_attempt(replay_id)
        verification_id = self._insert_replay_verification(
            replay_id, publication_id, attempt_id
        )
        self._finish_replay(replay_id, attempt_id)
        self.connection.commit()
        self.cursor = self.connection.cursor()
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute(
                "UPDATE scientific_evaluation_replay_verifications SET verification_status='mismatch' "
                "WHERE id=%s",
                (verification_id,),
            )
        self.connection.rollback()
        self.cursor = self.connection.cursor()
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute(
                "DELETE FROM scientific_evaluation_replay_verifications WHERE id=%s",
                (verification_id,),
            )

    def test_non_replay_modes_still_require_canonical_publication(self):
        fixture, comparison_id, _, _ = self._committed_normal_publication()
        for index, mode in enumerate(("NORMAL", "REFRESH", "COUNTERFACTUAL")):
            with self.subTest(mode=mode):
                savepoint = f"mode_requires_publication_{index}"
                self.cursor.execute(f"SAVEPOINT {savepoint}")
                mode_fixture = dict(fixture)
                mode_fixture["roots"] = dict(fixture["roots"])
                mode_fixture["roots"]["identity"] = _artifact(
                    self.cursor, "scientific_evaluation_execution_identity"
                )
                comparison = None
                if mode == "REFRESH":
                    snapshot_id, _ = _insert_snapshot(self.cursor)
                    _, snapshot_digest = _seal_snapshot(self.cursor, snapshot_id, 0)
                    mode_fixture["snapshot_id"] = snapshot_id
                    mode_fixture["snapshot_digest"] = snapshot_digest
                    comparison = comparison_id
                elif mode == "COUNTERFACTUAL":
                    mode_fixture["roots"]["configuration"] = _artifact(
                        self.cursor, "scientific_evaluation_configuration"
                    )
                    comparison = comparison_id
                execution_id = self._execution(
                    mode_fixture, mode=mode, comparison=comparison
                )
                if mode == "COUNTERFACTUAL":
                    self.cursor.execute(
                        "INSERT INTO scientific_evaluation_governance_events(event_key,entity_type,execution_id,"
                        "event_type,actor_identifier,reason_code,effective_at) "
                        "VALUES(%s,'evaluation_execution',%s,'counterfactual_authorized',"
                        "'reviewer:test','authorized_test',NOW())",
                        (str(uuid.uuid4()), execution_id),
                    )
                self.cursor.execute(
                    "UPDATE scientific_evaluation_executions SET technical_status='running',started_at=NOW() "
                    "WHERE id=%s",
                    (execution_id,),
                )
                self.cursor.execute(
                    "UPDATE scientific_evaluation_executions SET technical_status='completed',completed_at=NOW() "
                    "WHERE id=%s",
                    (execution_id,),
                )
                with self.assertRaises(psycopg2.Error):
                    self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                self.cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                self.cursor.execute("SET CONSTRAINTS ALL DEFERRED")

    def test_canonical_component_cannot_be_appended_after_publication_commit(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute(
            "UPDATE scientific_evaluation_executions SET technical_status='running',started_at=NOW() WHERE id=%s",
            (execution_id,),
        )
        attempt_id = self._attempt(execution_id)
        _, result_id, _ = self._publish_zero_member(execution_id, attempt_id)
        self.connection.commit()
        self.cursor = self.connection.cursor()
        component = _artifact(self.cursor, "scientific_evaluation_result_component")
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_result_components(result_id,component_kind,"
            "component_schema_version,component_role,component_artifact_id,component_digest,component_ordinal) "
            "VALUES(%s,'generic','1','detail',%s,%s,0)",
            (result_id, component[0], component[1]),
        )
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_idempotency_owner_digest_and_expiry_policy(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_idempotency_keys(operation_type,request_scope,request_key,"
            "expected_semantic_digest,execution_id,expires_at) VALUES('create','tenant:test',%s,%s,%s,NOW()+INTERVAL '1 hour') RETURNING id",
            (uuid.uuid4().hex, fixture["roots"]["identity"][1], execution_id),
        )
        key_id = self.cursor.fetchone()[0]
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute("DELETE FROM scientific_evaluation_idempotency_keys WHERE id=%s", (key_id,))

    def test_governance_exact_entity_and_append_only_preserved(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_governance_events(event_key,entity_type,execution_id,event_type,"
            "actor_identifier,reason_code,effective_at) VALUES(%s,'evaluation_execution',%s,'annotation',"
            "'reviewer:test','test_annotation',NOW()) RETURNING id",
            (str(uuid.uuid4()), execution_id),
        )
        event_id = self.cursor.fetchone()[0]
        with self.assertRaises(psycopg2.Error):
            self.cursor.execute(
                "UPDATE scientific_evaluation_governance_events SET reason_code='changed' WHERE id=%s",
                (event_id,),
            )

    def test_concurrent_running_attempts_elect_one(self):
        fixture = self._foundation()
        execution_id = self._execution(fixture)
        build = _artifact(self.cursor, "scientific_evaluation_engine_build")
        self.connection.commit()
        barrier = threading.Barrier(2)
        outcomes = []

        def worker(number):
            connection = _connection(self.database)
            try:
                with connection.cursor() as cursor:
                    barrier.wait()
                    cursor.execute(
                        "UPDATE scientific_evaluation_executions SET technical_status='running',"
                        "started_at=COALESCE(started_at,NOW()) WHERE id=%s",
                        (execution_id,),
                    )
                    cursor.execute(
                        "INSERT INTO scientific_evaluation_execution_attempts(attempt_key,execution_id,attempt_number,"
                        "engine_build_artifact_id,lease_token,lease_expires_at,heartbeat_at,started_at) "
                        "VALUES(%s,%s,%s,%s,%s,NOW()+INTERVAL '5 minutes',NOW(),NOW())",
                        (str(uuid.uuid4()), execution_id, number, build[0], str(uuid.uuid4())),
                    )
                connection.commit()
                outcomes.append("won")
            except psycopg2.Error:
                connection.rollback()
                outcomes.append("conflict")
            finally:
                connection.close()

        threads = [threading.Thread(target=worker, args=(n,)) for n in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(15)
        self.assertEqual(sorted(outcomes), ["conflict", "won"])


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvaluationExecutionMigrationLifecycleTests(unittest.TestCase):
    def test_fresh_chain_and_empty_downgrade(self):
        database = _create_database("execution_fresh")
        try:
            _alembic(database, "upgrade", REVISION)
            with _connection(database) as connection, connection.cursor() as cursor:
                cursor.execute("SELECT version_num FROM alembic_version")
                self.assertEqual(cursor.fetchone()[0], REVISION)
            _alembic(database, "downgrade", PARENT_REVISION)
            with _connection(database) as connection, connection.cursor() as cursor:
                cursor.execute("SELECT version_num FROM alembic_version")
                self.assertEqual(cursor.fetchone()[0], PARENT_REVISION)
                cursor.execute("SELECT to_regclass('scientific_evaluation_executions')")
                self.assertIsNone(cursor.fetchone()[0])
                cursor.execute("SELECT to_regclass('scientific_evaluation_replay_verifications')")
                self.assertIsNone(cursor.fetchone()[0])
        finally:
            _drop_database(database)

    def test_downgrade_refuses_any_history(self):
        database = _create_database("execution_downgrade_guard")
        try:
            _alembic(database, "upgrade", REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO scientific_evaluation_idempotency_keys(operation_type,request_scope,request_key,"
                        "expected_semantic_digest) VALUES('test','scope','key',%s)",
                        (sha256(b"history").digest(),),
                    )
                connection.commit()
            finally:
                connection.close()
            result = _alembic(database, "downgrade", PARENT_REVISION, success=False)
            self.assertIn("contains scientific/operational history", result.stdout + result.stderr)
        finally:
            _drop_database(database)

    def test_preflight_rejects_collision_without_partial_foundation(self):
        database = _create_database("execution_preflight")
        try:
            _alembic(database, "upgrade", PARENT_REVISION)
            with _connection(database) as connection, connection.cursor() as cursor:
                cursor.execute("CREATE TABLE scientific_evaluation_replay_verifications(id BIGINT)")
            result = _alembic(database, "upgrade", REVISION, success=False)
            self.assertIn("already exists", result.stdout + result.stderr)
            with _connection(database) as connection, connection.cursor() as cursor:
                cursor.execute("SELECT to_regclass('scientific_evaluation_executions')")
                self.assertIsNone(cursor.fetchone()[0])
        finally:
            _drop_database(database)

    def test_downgrade_refuses_replay_verification_history(self):
        database = _create_database("execution_replay_downgrade")
        helper = None
        try:
            _alembic(database, "upgrade", REVISION)
            helper = ScientificEvaluationExecutionPersistenceTests(
                "test_matching_replay_reuses_global_artifacts_without_scientific_rows"
            )
            helper.connection = _connection(database)
            helper.connection.autocommit = False
            helper.cursor = helper.connection.cursor()
            fixture, comparison_id, _, publication_id = helper._committed_normal_publication()
            replay_id = helper._replay_execution(fixture, comparison_id)
            attempt_id = helper._start_attempt(replay_id)
            helper._insert_replay_verification(
                replay_id, publication_id, attempt_id
            )
            helper._finish_replay(replay_id, attempt_id)
            helper.connection.commit()
            helper.cursor.close()
            helper.connection.close()
            helper = None
            result = _alembic(database, "downgrade", PARENT_REVISION, success=False)
            self.assertIn("contains scientific/operational history", result.stdout + result.stderr)
        finally:
            if helper is not None:
                helper.connection.rollback()
                helper.cursor.close()
                helper.connection.close()
            _drop_database(database)

    def test_preflight_rejects_replay_object_collisions(self):
        cases = (
            (
                "function",
                (
                    "CREATE FUNCTION scientific_evaluation_validate_replay_verification() "
                    "RETURNS TRIGGER LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$",
                ),
            ),
            (
                "index",
                (
                    "CREATE INDEX idx_scientific_evaluation_replay_verifications_comparison "
                    "ON substances(id)",
                ),
            ),
            (
                "trigger",
                (
                    "CREATE FUNCTION wye_test_replay_trigger() RETURNS TRIGGER LANGUAGE plpgsql "
                    "AS $$ BEGIN RETURN NEW; END $$",
                    "CREATE TRIGGER trg_scientific_evaluation_replay_verifications_validate "
                    "BEFORE UPDATE ON substances FOR EACH ROW EXECUTE FUNCTION wye_test_replay_trigger()",
                ),
            ),
        )
        for kind, statements in cases:
            with self.subTest(kind=kind):
                database = _create_database(f"execution_replay_{kind}_preflight")
                try:
                    _alembic(database, "upgrade", PARENT_REVISION)
                    with _connection(database) as connection, connection.cursor() as cursor:
                        for statement in statements:
                            cursor.execute(statement)
                    result = _alembic(database, "upgrade", REVISION, success=False)
                    self.assertIn("already exists", result.stdout + result.stderr)
                    with _connection(database) as connection, connection.cursor() as cursor:
                        cursor.execute("SELECT to_regclass('scientific_evaluation_executions')")
                        self.assertIsNone(cursor.fetchone()[0])
                finally:
                    _drop_database(database)


if __name__ == "__main__":
    unittest.main()
