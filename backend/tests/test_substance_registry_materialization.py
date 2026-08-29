import os
import subprocess
import sys
import threading
import unittest
import uuid
from pathlib import Path

from app.db import get_connection
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import PreparedScientificIngestionRun
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver
from app.services.substance_registry_materialization import (
    SubstanceRegistryMaterializationError,
    SubstanceRegistryMaterializationService,
)
from app.services.substance_resolution_reviews import SubstanceResolutionReviewService
import tests.test_scientific_substance_resolution as registry_fixtures


class _StaticParser:
    def __init__(self, result): self.result = result
    def parse(self, manifest): return self.result


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0015")
class SubstanceRegistryMaterializationTests(unittest.TestCase):
    def fixture(self):
        helper = registry_fixtures.ScientificSubstanceResolutionPostgresTests(
            "test_real_namespace_verified_lookup_executor_and_registry_immutability"
        )
        return helper.fixture()

    @staticmethod
    def unknown(record, namespace_key, value=None):
        value = value or f"learn-{uuid.uuid4().hex}"
        item = record.substance_identifiers[0].model_copy(update={
            "namespace_key": namespace_key, "normalized_value": value,
            "raw_value": f" RAW {value} ",
        })
        return record.model_copy(update={"substance_identifiers": (item,)})

    def reviewed_candidate(self, *, candidate_kind="unknown_identifier"):
        prepared, ingestion, result, substances, _, namespace_key = self.fixture()
        record = self.unknown(result.records[0], namespace_key)
        resolver = PostgresScientificSubstanceResolver()
        resolution = resolver.resolve(record)
        review = SubstanceResolutionReviewService()
        persisted = review.record_resolution(prepared.id, record, resolution)[0]
        if candidate_kind != "unknown_identifier":
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE substance_resolution_candidates SET candidate_kind=%s WHERE id=%s", (candidate_kind, persisted["candidate_id"]))
                conn.commit()
            finally: conn.close()
        decision = review.decide(
            persisted["candidate_id"], "associate_existing", "reviewer-A",
            "verified_match", substances[0],
        )
        return prepared, ingestion, result, substances, namespace_key, record, decision

    def identifier(self, namespace_key, normalized_value):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT i.id,i.substance_id,i.identifier_value,i.is_primary,
                           i.verification_status,i.source_dataset_release_id,
                           i.ingestion_run_id,i.provenance
                    FROM substance_identifiers i
                    JOIN substance_identifier_namespaces n ON n.id=i.namespace_id
                    WHERE n.namespace_key=%s AND n.namespace_version='1'
                      AND i.normalized_value=%s
                """, (namespace_key, normalized_value))
                return cur.fetchone()
        finally: conn.close()

    def test_applies_verified_nonprimary_identifier_with_audit_and_retry(self):
        _, _, _, substances, namespace_key, record, decision = self.reviewed_candidate()
        service = SubstanceRegistryMaterializationService()
        first = service.materialize_decision(decision["id"], "worker-B", {"test": True})
        second = service.materialize_decision(decision["id"], "worker-C")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["materialization_status"], "applied")
        row = self.identifier(namespace_key, record.substance_identifiers[0].normalized_value)
        self.assertEqual(row[:7], (first["substance_identifier_id"], substances[0],
            record.substance_identifiers[0].raw_value, False, "verified", None, None))
        self.assertEqual(row[7]["decision_id"], decision["id"])
        self.assertEqual((decision["reviewed_by"], first["materialized_by"]), ("reviewer-A", "worker-B"))

    def test_compatible_existing_reused_and_conflicts_are_atomic(self):
        _, _, _, substances, namespace_key, record, decision = self.reviewed_candidate()
        value = record.substance_identifiers[0].normalized_value
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM substance_identifier_namespaces WHERE namespace_key=%s AND namespace_version='1'", (namespace_key,)); ns = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,'compat','existing',%s,'verified') RETURNING id", (substances[0], ns, value)); existing = cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        materialized = SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker")
        self.assertEqual((materialized["materialization_status"], materialized["substance_identifier_id"]), ("already_present", existing))

        _, _, _, substances2, namespace2, record2, decision2 = self.reviewed_candidate()
        value2 = record2.substance_identifiers[0].normalized_value
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM substance_identifier_namespaces WHERE namespace_key=%s AND namespace_version='1'", (namespace2,)); ns2 = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,'conflict','existing',%s,'verified')", (substances2[1], ns2, value2))
            conn.commit()
        finally: conn.close()
        with self.assertRaisesRegex(SubstanceRegistryMaterializationError, "another substance"):
            SubstanceRegistryMaterializationService().materialize_decision(decision2["id"], "worker")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM substance_registry_materializations WHERE decision_id=%s", (decision2["id"],)); self.assertEqual(cur.fetchone()[0], 0)
        finally: conn.close()

    def test_ineligible_candidate_target_status_and_decision_types(self):
        for kind in ("identity_conflict", "inactive_target"):

            with self.subTest(kind=kind):
                *_, decision = self.reviewed_candidate(candidate_kind=kind)
                with self.assertRaises(SubstanceRegistryMaterializationError):
                    SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker")
        for identifier_status in ("pending_review", "deprecated", "rejected"):
            with self.subTest(identifier_status=identifier_status):
                _, _, _, substances3, namespace3, record3, decision3 = self.reviewed_candidate()
                value3 = record3.substance_identifiers[0].normalized_value
                conn = get_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM substance_identifier_namespaces WHERE namespace_key=%s AND namespace_version='1'", (namespace3,)); ns3 = cur.fetchone()[0]
                        cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,'status_conflict','existing',%s,%s)", (substances3[0], ns3, value3, identifier_status))
                    conn.commit()
                finally: conn.close()
                with self.assertRaisesRegex(SubstanceRegistryMaterializationError, "not verified"):
                    SubstanceRegistryMaterializationService().materialize_decision(decision3["id"], "worker")
        prepared, _, result, substances, _, namespace_key = self.fixture()
        record = self.unknown(result.records[0], "unknown_namespace")
        resolution = PostgresScientificSubstanceResolver().resolve(record)
        review = SubstanceResolutionReviewService(); candidate = review.record_resolution(prepared.id, record, resolution)[0]
        unknown_decision = review.decide(candidate["candidate_id"], "associate_existing", "reviewer", "manual", substances[0])
        with self.assertRaises(SubstanceRegistryMaterializationError):
            SubstanceRegistryMaterializationService().materialize_decision(unknown_decision["id"], "worker")

        for decision_type in ("defer", "reject"):
            prepared2, _, result2, _, _, namespace2 = self.fixture(); record2 = self.unknown(result2.records[0], namespace2)
            resolution2 = PostgresScientificSubstanceResolver().resolve(record2); review2 = SubstanceResolutionReviewService()
            candidate2 = review2.record_resolution(prepared2.id, record2, resolution2)[0]
            decision2 = review2.decide(candidate2["candidate_id"], decision_type, "reviewer", "not_associated")
            with self.assertRaises(SubstanceRegistryMaterializationError):
                SubstanceRegistryMaterializationService().materialize_decision(decision2["id"], "worker")

        *_, substances3, _, _, decision3 = self.reviewed_candidate()
        conn = get_connection()
        try:
            with conn.cursor() as cur: cur.execute("UPDATE substances SET status='deprecated' WHERE id=%s", (substances3[0],))
            conn.commit()
        finally: conn.close()
        with self.assertRaisesRegex(SubstanceRegistryMaterializationError, "active"):
            SubstanceRegistryMaterializationService().materialize_decision(decision3["id"], "worker")
        with self.assertRaises(SubstanceRegistryMaterializationError):
            SubstanceRegistryMaterializationService().materialize_decision(decision3["id"], "")

    def test_concurrent_same_decision_converges(self):
        *_, decision = self.reviewed_candidate(); barrier = threading.Barrier(2); results = []; errors = []
        def apply():
            try:
                barrier.wait(); results.append(SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker"))
            except Exception as exc: errors.append(exc)
        threads = [threading.Thread(target=apply) for _ in range(2)]
        [thread.start() for thread in threads]; [thread.join(20) for thread in threads]
        self.assertFalse(errors); self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], results[1]["id"])
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM substance_registry_materializations WHERE decision_id=%s", (decision["id"],)); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("SELECT count(*) FROM substance_identifiers WHERE id=%s", (results[0]["substance_identifier_id"],)); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()

    def test_resolver_learning_loop_and_future_run_evidence(self):
        prepared, ingestion, result, substances, _, namespace_key = self.fixture()
        record = self.unknown(result.records[0], namespace_key); one = result.model_copy(update={"records": (record,)})
        review = SubstanceResolutionReviewService(); executor = ScientificIngestionExecutor(_StaticParser(one), PostgresScientificSubstanceResolver(), ingestion, resolution_review_service=review)
        first = executor.execute(prepared); self.assertEqual((first.records_accepted, first.records_rejected), (0, 1))
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT candidate_id FROM substance_resolution_candidate_occurrences WHERE ingestion_run_id=%s AND source_record_key=%s", (prepared.id, record.source_record_key)); candidate_id = cur.fetchone()[0]
        finally: conn.close()
        decision = review.decide(candidate_id, "associate_existing", "reviewer", "learned", substances[0])
        SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker")
        self.assertEqual(PostgresScientificSubstanceResolver().resolve(record).record.substance_id, substances[0])

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO scientific_ingestion_runs(
                      release_id,run_key,idempotency_key,importer_name,importer_version,
                      source_adapter_version,acquisition_version,parser_version,
                      normalization_schema_version,artifact_manifest_algorithm,
                      artifact_manifest_fingerprint,run_status)
                    SELECT release_id,%s,%s,importer_name,importer_version,
                      source_adapter_version,acquisition_version,parser_version,
                      normalization_schema_version,artifact_manifest_algorithm,
                      artifact_manifest_fingerprint,'pending'
                    FROM scientific_ingestion_runs WHERE id=%s RETURNING id,run_key
                """, (str(uuid.uuid4()), f"future-{uuid.uuid4().hex}", prepared.id)); run_id, run_key = cur.fetchone()
                cur.execute("INSERT INTO scientific_ingestion_run_artifacts(ingestion_run_id,release_artifact_id,manifest_position) SELECT %s,release_artifact_id,manifest_position FROM scientific_ingestion_run_artifacts WHERE ingestion_run_id=%s", (run_id, prepared.id))
            conn.commit()
        finally: conn.close()
        future = PreparedScientificIngestionRun(run_id, run_key, "pending", prepared.manifest, False)
        second = ScientificIngestionExecutor(_StaticParser(one), PostgresScientificSubstanceResolver(), ingestion, resolution_review_service=review).execute(future)
        self.assertEqual((second.records_accepted, second.records_rejected, second.assessments_written), (1, 0, 1))
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM substance_resolution_candidate_occurrences WHERE ingestion_run_id=%s", (run_id,)); self.assertEqual(cur.fetchone()[0], 0)
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s AND substance_id=%s", (run_id, substances[0])); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1", "requires lifecycle PostgreSQL")
class SubstanceRegistryMaterializationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]
    def alembic(self, *args, success=True):
        result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=self.backend, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr); return result

    def test_safe_and_unsafe_lifecycle(self):
        self.alembic("downgrade", "0014_substance_resolution_review")
        self.alembic("upgrade", "0015_registry_materialization")
        self.alembic("downgrade", "0014_substance_resolution_review")
        self.alembic("upgrade", "0015_registry_materialization")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                suffix = uuid.uuid4().hex
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Lifecycle','v1') RETURNING id", (f"lifecycle_{suffix}",)); ns = cur.fetchone()[0]
                cur.execute("INSERT INTO substances(preferred_name,normalized_name,status) VALUES('Lifecycle',%s,'active') RETURNING id", (f"lifecycle_{suffix}",)); substance = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_resolution_candidates(candidate_key,candidate_kind,namespace_id,namespace_key,namespace_version,normalized_value,candidate_status) VALUES(%s,'unknown_identifier',%s,%s,'1','x','resolved_existing') RETURNING id", ("b"*64, ns, f"lifecycle_{suffix}")); candidate = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_resolution_decisions(candidate_id,decision_type,target_substance_id,reviewed_by,reviewed_at,reason_code) VALUES(%s,'associate_existing',%s,'reviewer',NOW(),'test') RETURNING id", (candidate, substance)); decision = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,'lifecycle','x','x','verified') RETURNING id", (substance, ns)); identifier_id = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_registry_materializations(decision_id,candidate_id,target_substance_id,namespace_id,normalized_value,substance_identifier_id,mutation_type,materialization_status,materialized_by,materialized_at) VALUES(%s,%s,%s,%s,'x',%s,'associate_existing_identifier','applied','worker',NOW()) RETURNING id", (decision, candidate, substance, ns, identifier_id)); materialization = cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        failed = self.alembic("downgrade", "0014_substance_resolution_review", success=False)
        self.assertIn("non-representable data", failed.stdout + failed.stderr)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cur.fetchone()[0], "0015_registry_materialization")
                cur.execute("SELECT count(*) FROM substance_registry_materializations WHERE id=%s", (materialization,)); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()


if __name__ == "__main__": unittest.main()
