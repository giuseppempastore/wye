"""Real PostgreSQL integration tests for the Phase 7.6.3B snapshot runtime."""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import threading
import time
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
    _insert_finding,
)

from app.repositories.scientific_evidence_snapshots import (  # noqa: E402
    PostgresScientificEvidenceSnapshotRepository,
)
from app.scientific_evaluation.errors import (  # noqa: E402
    DuplicateSnapshotMemberError,
    SnapshotMemberError,
    SnapshotProvenanceError,
)
from app.scientific_evaluation.snapshots import (  # noqa: E402
    SnapshotConstructionRequest,
    SnapshotMemberInput,
)
from app.services.scientific_evidence_snapshots import (  # noqa: E402
    ScientificEvidenceSnapshotService,
)


NOW = datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc)


def _request(*members, scope_key="runtime", created_by="snapshot_runtime_test"):
    return SnapshotConstructionRequest(
        snapshot_policy_key="phase_7_candidate_universe",
        snapshot_policy_version="1",
        as_of=NOW,
        evidence_cutoff=NOW - timedelta(days=1),
        scope={"target_identity": scope_key},
        technical_predicates=(
            {"field": "candidate_ids", "operator": "explicit_membership"},
        ),
        members=tuple(members),
        created_by=created_by,
        sealed_by=created_by,
    )


@unittest.skipUnless(
    os.getenv("WYE_RUN_SNAPSHOT_RUNTIME_POSTGRES_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvidenceSnapshotRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = _create_database("runtime")
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
        self.service = ScientificEvidenceSnapshotService()

    def tearDown(self):
        try:
            self.connection.rollback()
        finally:
            self.cursor.close()
            self.connection.close()

    def _finding_member(self, evidence):
        return SnapshotMemberInput(
            "finding", evidence["assessment_id"], evidence["finding_id"]
        )

    def test_finding_snapshot_persists_query_member_manifest_and_seals(self):
        evidence = _insert_evidence(self.cursor)
        result = self.service.build_and_seal(
            self.cursor, _request(self._finding_member(evidence))
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(result.snapshot.status, "sealed")
        self.assertEqual(result.snapshot.member_count, 1)
        self.assertEqual(result.snapshot.snapshot_digest, self._manifest_digest(result.snapshot.id))
        repeated_finalize = self.service.finalize(
            self.cursor, result.snapshot.id, sealed_by="snapshot_runtime_test"
        )
        self.assertTrue(repeated_finalize.canonical_winner_reused)
        self.assertEqual(repeated_finalize.snapshot.snapshot_digest, result.snapshot.snapshot_digest)
        self.cursor.execute(
            "SELECT json_payload->'payload' FROM scientific_evaluation_artifacts "
            "WHERE id=%s",
            (result.snapshot.query_definition_artifact_id,),
        )
        query_payload = self.cursor.fetchone()[0]
        self.assertEqual(query_payload["snapshot_policy_key"], "phase_7_candidate_universe")
        for forbidden in ("mapping_state", "selection", "score", "result"):
            self.assertNotIn(forbidden, query_payload)
        self.cursor.execute(
            "SELECT a.artifact_kind,m.status_as_of,m.membership_ordinal,a.json_payload "
            "FROM scientific_evidence_snapshot_members m "
            "JOIN scientific_evaluation_artifacts a ON a.id=m.member_payload_artifact_id "
            "WHERE m.snapshot_id=%s",
            (result.snapshot.id,),
        )
        kind, status, ordinal, member_envelope = self.cursor.fetchone()
        self.assertEqual((kind, status, ordinal), (
            "scientific_evidence_snapshot_member", "published", 0
        ))
        self.assertEqual(
            member_envelope["payload"]["provenance"]["ingestion_run"]["parser_version"],
            "1",
        )
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_artifacts WHERE artifact_kind IN "
            "('scientific_evidence_snapshot_query','scientific_evidence_snapshot_member',"
            "'scientific_evidence_snapshot_manifest')"
        )
        self.assertEqual(self.cursor.fetchone()[0], 3)

    def test_member_artifact_freezes_ordered_storage_provenance(self):
        evidence = _insert_evidence(self.cursor)
        for position, suffix in ((1, "second"), (0, "first")):
            checksum = ("a" if position == 0 else "b") * 64
            self.cursor.execute(
                "INSERT INTO storage_objects "
                "(storage_provider,bucket,object_key,object_version,checksum_algorithm,"
                "checksum_value,mime_type,byte_size) "
                "VALUES('local','snapshot-test',%s,'v1','sha256',%s,'application/json',10) "
                "RETURNING id",
                (f"phase763b/{suffix}.json", checksum),
            )
            storage_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                "INSERT INTO scientific_release_artifacts "
                "(release_id,storage_object_id,artifact_key,artifact_role,format,media_type,"
                "raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at,validated_at) "
                "VALUES(%s,%s,%s,'primary','json','application/json','sha256',%s,10,NOW(),NOW()) "
                "RETURNING id",
                (evidence["release_id"], storage_id, suffix, checksum),
            )
            artifact_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                "INSERT INTO scientific_ingestion_run_artifacts "
                "(ingestion_run_id,release_artifact_id,manifest_position) VALUES(%s,%s,%s)",
                (evidence["ingestion_run_id"], artifact_id, position),
            )

        result = self.service.build_and_seal(
            self.cursor,
            _request(self._finding_member(evidence), scope_key="storage_provenance"),
        )
        self.cursor.execute(
            "SELECT a.json_payload->'payload'->'provenance'->'run_artifacts' "
            "FROM scientific_evidence_snapshot_members m "
            "JOIN scientific_evaluation_artifacts a ON a.id=m.member_payload_artifact_id "
            "WHERE m.snapshot_id=%s",
            (result.snapshot.id,),
        )
        artifacts = self.cursor.fetchone()[0]
        self.assertEqual([item["manifest_position"] for item in artifacts], [0, 1])
        self.assertEqual(artifacts[0]["object_key"], "phase763b/first.json")
        self.assertEqual(artifacts[0]["storage_checksum_algorithm"], "sha256")
        self.assertEqual(artifacts[0]["storage_checksum_value"], "a" * 64)
        self.assertEqual(artifacts[0]["storage_byte_size"], 10)

    def test_assessment_member_and_zero_member_snapshots_are_supported(self):
        evidence = _insert_evidence(self.cursor)
        assessment = self.service.build_and_seal(
            self.cursor,
            _request(
                SnapshotMemberInput("assessment", evidence["assessment_id"]),
                scope_key="assessment",
            ),
        )
        empty = self.service.build_and_seal(
            self.cursor, _request(scope_key="empty")
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(assessment.snapshot.member_count, 1)
        self.assertEqual(empty.snapshot.member_count, 0)
        self.cursor.execute(
            "SELECT json_payload->'payload'->>'member_count' "
            "FROM scientific_evaluation_artifacts WHERE id=%s",
            (empty.snapshot.manifest_artifact_id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], "0")

    def test_invalid_shapes_duplicates_and_provenance_mismatch_are_rejected(self):
        first = _insert_evidence(self.cursor)
        second = _insert_evidence(self.cursor)
        member = self._finding_member(first)
        with self.assertRaises(DuplicateSnapshotMemberError):
            self.service.build_and_seal(self.cursor, _request(member, member))
        with self.assertRaises(SnapshotMemberError):
            self.service.build_and_seal(
                self.cursor,
                _request(
                    SnapshotMemberInput("assessment", first["assessment_id"]),
                    member,
                ),
            )
        with self.assertRaises(SnapshotProvenanceError):
            self.service.build_and_seal(
                self.cursor,
                _request(
                    SnapshotMemberInput(
                        "finding", first["assessment_id"], second["finding_id"]
                    )
                ),
            )

    def test_input_order_and_retry_converge_on_one_canonical_snapshot(self):
        first = _insert_evidence(self.cursor)
        second = _insert_evidence(self.cursor)
        first_member = self._finding_member(first)
        second_member = self._finding_member(second)
        winner = self.service.build_and_seal(
            self.cursor, _request(first_member, second_member, scope_key="converge")
        )
        self.connection.commit()

        retried = self.service.build_and_seal(
            self.cursor, _request(second_member, first_member, scope_key="converge")
        )
        self.assertTrue(retried.canonical_winner_reused)
        self.assertEqual(retried.snapshot.id, winner.snapshot.id)
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evidence_snapshots WHERE status='sealed' "
            "AND snapshot_digest=%s",
            (winner.snapshot.snapshot_digest,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evidence_snapshots WHERE status='building'"
        )
        self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_finalizer_repairs_a_nontrivial_ordinal_permutation(self):
        first = _insert_evidence(self.cursor)
        second = _insert_evidence(self.cursor)
        snapshot = self.service.create_building(
            self.cursor,
            _request(
                self._finding_member(first),
                self._finding_member(second),
                scope_key="ordinal_permutation",
            ),
        )
        self.cursor.execute(
            "UPDATE scientific_evidence_snapshot_members "
            "SET membership_ordinal=membership_ordinal+10 WHERE snapshot_id=%s",
            (snapshot.id,),
        )
        self.cursor.execute(
            "UPDATE scientific_evidence_snapshot_members SET membership_ordinal="
            "CASE membership_ordinal WHEN 10 THEN 1 WHEN 11 THEN 0 END "
            "WHERE snapshot_id=%s",
            (snapshot.id,),
        )
        result = self.service.finalize(
            self.cursor, snapshot.id, sealed_by="snapshot_runtime_test"
        )
        self.cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.cursor.execute(
            "SELECT membership_ordinal FROM scientific_evidence_snapshot_members "
            "WHERE snapshot_id=%s ORDER BY member_kind COLLATE \"C\","
            "member_identity_digest,member_semantic_digest",
            (result.snapshot.id,),
        )
        self.assertEqual([row[0] for row in self.cursor.fetchall()], [0, 1])

    def test_distinct_findings_with_same_observed_value_remain_distinct_members(self):
        evidence = _insert_evidence(self.cursor)
        second_finding = _insert_finding(self.cursor, evidence["assessment_id"])
        result = self.service.build_and_seal(
            self.cursor,
            _request(
                self._finding_member(evidence),
                SnapshotMemberInput(
                    "finding", evidence["assessment_id"], second_finding
                ),
                scope_key="same_value",
            ),
        )
        self.assertEqual(result.snapshot.member_count, 2)
        self.cursor.execute(
            "SELECT count(DISTINCT member_identity_digest),count(*) "
            "FROM scientific_evidence_snapshot_members WHERE snapshot_id=%s",
            (result.snapshot.id,),
        )
        self.assertEqual(self.cursor.fetchone(), (2, 2))

    def test_caller_transaction_rollback_removes_entire_build(self):
        evidence = _insert_evidence(self.cursor)
        result = self.service.build_and_seal(
            self.cursor, _request(self._finding_member(evidence), scope_key="rollback")
        )
        snapshot_key = result.snapshot.snapshot_key
        self.connection.rollback()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM scientific_evidence_snapshots WHERE snapshot_key=%s",
                (str(snapshot_key),),
            )
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_sealed_status_as_of_and_member_artifact_remain_historical(self):
        evidence = _insert_evidence(self.cursor)
        result = self.service.build_and_seal(
            self.cursor, _request(self._finding_member(evidence), scope_key="history")
        )
        self.cursor.execute(
            "SELECT m.status_as_of,a.content_digest FROM scientific_evidence_snapshot_members m "
            "JOIN scientific_evaluation_artifacts a ON a.id=m.member_payload_artifact_id "
            "WHERE m.snapshot_id=%s",
            (result.snapshot.id,),
        )
        before = self.cursor.fetchone()
        snapshot_digest = result.snapshot.snapshot_digest
        manifest_artifact_id = result.snapshot.manifest_artifact_id
        self.cursor.execute(
            "UPDATE scientific_assessments SET assessment_status='superseded' WHERE id=%s",
            (evidence["assessment_id"],),
        )
        self.cursor.execute(
            "SELECT m.status_as_of,a.content_digest FROM scientific_evidence_snapshot_members m "
            "JOIN scientific_evaluation_artifacts a ON a.id=m.member_payload_artifact_id "
            "WHERE m.snapshot_id=%s",
            (result.snapshot.id,),
        )
        self.assertEqual(self.cursor.fetchone(), before)
        self.cursor.execute(
            "SELECT snapshot_digest,manifest_artifact_id FROM scientific_evidence_snapshots "
            "WHERE id=%s",
            (result.snapshot.id,),
        )
        persisted_digest, persisted_manifest = self.cursor.fetchone()
        self.assertEqual(bytes(persisted_digest), snapshot_digest)
        self.assertEqual(persisted_manifest, manifest_artifact_id)

    def test_identical_concurrent_builders_converge(self):
        evidence = _insert_evidence(self.cursor)
        self.connection.commit()
        request = _request(self._finding_member(evidence), scope_key="concurrent")
        barrier = threading.Barrier(2)
        results = []
        failures = []

        def worker():
            connection = _connection(self.database)
            connection.autocommit = False
            try:
                with connection.cursor() as cursor:
                    barrier.wait(timeout=10)
                    built = ScientificEvidenceSnapshotService().build_and_seal(
                        cursor, request
                    )
                connection.commit()
                results.append(built.snapshot.id)
            except Exception as exc:  # pragma: no cover - reported by assertion
                connection.rollback()
                failures.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(len(set(results)), 1)
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evidence_snapshots WHERE status='sealed'"
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)

    def test_mutation_first_is_included_by_waiting_finalizer(self):
        evidence = _insert_evidence(self.cursor)
        snapshot = self.service.create_building(
            self.cursor, _request(scope_key="mutation_first")
        )
        self.connection.commit()

        mutation = _connection(self.database)
        finalizer = _connection(self.database)
        done = threading.Event()
        started = threading.Event()
        failures = []
        result_ids = []
        try:
            with mutation.cursor() as cursor:
                service = ScientificEvidenceSnapshotService()
                prepared = service._prepare_member(cursor, self._finding_member(evidence))
                service.repository.insert_member(
                    cursor,
                    snapshot_id=snapshot.id,
                    member_kind="finding",
                    finding_id=prepared.finding_id,
                    assessment_id=prepared.assessment_id,
                    ingestion_run_id=prepared.ingestion_run_id,
                    source_dataset_release_id=prepared.source_dataset_release_id,
                    member_identity_digest=prepared.identity_digest,
                    member_payload_artifact_id=prepared.artifact.artifact.id,
                    member_semantic_digest=prepared.artifact.artifact.content_digest,
                    membership_ordinal=0,
                    status_as_of=prepared.status_as_of,
                )

            def seal_worker():
                try:
                    with finalizer.cursor() as cursor:
                        started.set()
                        result = ScientificEvidenceSnapshotService().finalize(
                            cursor, snapshot.id, sealed_by="snapshot_runtime_test"
                        )
                    finalizer.commit()
                    result_ids.append(result.snapshot.id)
                except Exception as exc:  # pragma: no cover - assertion reports it
                    finalizer.rollback()
                    failures.append(exc)
                finally:
                    done.set()

            thread = threading.Thread(target=seal_worker)
            thread.start()
            self.assertTrue(started.wait(timeout=5))
            self._assert_backend_waiting_on_lock(finalizer.get_backend_pid())
            self.assertFalse(done.is_set())
            mutation.commit()
            thread.join(timeout=30)
            self.assertEqual(failures, [])
            self.assertEqual(result_ids, [snapshot.id])
            self.cursor.execute(
                "SELECT member_count FROM scientific_evidence_snapshots WHERE id=%s",
                (snapshot.id,),
            )
            self.assertEqual(self.cursor.fetchone()[0], 1)
        finally:
            mutation.rollback()
            finalizer.rollback()
            mutation.close()
            finalizer.close()

    def test_seal_first_blocks_then_rejects_member_insert(self):
        evidence = _insert_evidence(self.cursor)
        snapshot = self.service.create_building(
            self.cursor, _request(scope_key="seal_first")
        )
        prepared = self.service._prepare_member(self.cursor, self._finding_member(evidence))
        self.connection.commit()

        sealing = _connection(self.database)
        mutation = _connection(self.database)
        done = threading.Event()
        started = threading.Event()
        failures = []
        try:
            with sealing.cursor() as cursor:
                ScientificEvidenceSnapshotService().finalize(
                    cursor, snapshot.id, sealed_by="snapshot_runtime_test"
                )

            def mutate_worker():
                try:
                    with mutation.cursor() as cursor:
                        started.set()
                        PostgresScientificEvidenceSnapshotRepository().insert_member(
                            cursor,
                            snapshot_id=snapshot.id,
                            member_kind="finding",
                            finding_id=prepared.finding_id,
                            assessment_id=prepared.assessment_id,
                            ingestion_run_id=prepared.ingestion_run_id,
                            source_dataset_release_id=prepared.source_dataset_release_id,
                            member_identity_digest=prepared.identity_digest,
                            member_payload_artifact_id=prepared.artifact.artifact.id,
                            member_semantic_digest=prepared.artifact.artifact.content_digest,
                            membership_ordinal=0,
                            status_as_of=prepared.status_as_of,
                        )
                    mutation.commit()
                except Exception as exc:
                    mutation.rollback()
                    failures.append(exc)
                finally:
                    done.set()

            thread = threading.Thread(target=mutate_worker)
            thread.start()
            self.assertTrue(started.wait(timeout=5))
            self._assert_backend_waiting_on_lock(mutation.get_backend_pid())
            self.assertFalse(done.is_set())
            sealing.commit()
            thread.join(timeout=30)
            self.assertEqual(len(failures), 1)
            self.assertIsInstance(failures[0], psycopg2.Error)
            self.assertEqual(failures[0].pgcode, "55000")
        finally:
            sealing.rollback()
            mutation.rollback()
            sealing.close()
            mutation.close()

    def _manifest_digest(self, snapshot_id):
        self.cursor.execute(
            "SELECT a.content_digest FROM scientific_evidence_snapshots s "
            "JOIN scientific_evaluation_artifacts a ON a.id=s.manifest_artifact_id "
            "WHERE s.id=%s",
            (snapshot_id,),
        )
        return bytes(self.cursor.fetchone()[0])

    def _assert_backend_waiting_on_lock(self, backend_pid):
        for _ in range(100):
            self.cursor.execute(
                "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s",
                (backend_pid,),
            )
            row = self.cursor.fetchone()
            if row is not None and row[0] == "Lock":
                return
            time.sleep(0.05)
        self.fail(f"backend {backend_pid} did not enter a PostgreSQL lock wait")


if __name__ == "__main__":
    unittest.main()
