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
from app.services.substance_resolution_reviews import (
    SubstanceResolutionReviewError,
    SubstanceResolutionReviewService,
)
import tests.test_scientific_substance_resolution as registry_fixtures


class _StaticParser:
    def __init__(self, result): self.result = result
    def parse(self, manifest): return self.result


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0016")
class ControlledSubstanceCreationTests(unittest.TestCase):
    def fixture(self):
        helper = registry_fixtures.ScientificSubstanceResolutionPostgresTests(
            "test_real_namespace_verified_lookup_executor_and_registry_immutability"
        )
        return helper.fixture()

    @staticmethod
    def unknown(record, namespace_key, value=None):
        value = value or f"new-{uuid.uuid4().hex}"
        item = record.substance_identifiers[0].model_copy(update={
            "namespace_key": namespace_key, "normalized_value": value,
            "raw_value": f" RAW-{value} ",
        })
        return record.model_copy(update={"substance_identifiers": (item,)})

    def reviewed_creation(self, preferred_name="Test Compound", normalized_name=None,
                          substance_type="chemical_substance"):
        prepared, ingestion, result, _, _, namespace_key = self.fixture()
        record = self.unknown(result.records[0], namespace_key)
        resolution = PostgresScientificSubstanceResolver().resolve(record)
        review = SubstanceResolutionReviewService()
        candidate = review.record_resolution(prepared.id, record, resolution)[0]
        normalized_name = normalized_name or f"test compound {uuid.uuid4().hex}"
        decision = review.decide(
            candidate["candidate_id"], "create_new_substance", "reviewer-A",
            "new_canonical_identity", preferred_name=preferred_name,
            normalized_name=normalized_name, substance_type=substance_type,
            provenance={"review": "explicit"},
        )
        return prepared, ingestion, result, namespace_key, record, candidate, decision

    def test_decision_creation_bootstrap_audit_resolver_and_retry(self):
        _, _, _, namespace_key, record, candidate, decision = self.reviewed_creation()
        detail = SubstanceResolutionReviewService().get(candidate["candidate_id"])
        self.assertEqual(detail["candidate"]["candidate_status"], "resolved_new")
        self.assertEqual(decision["proposed_substance_type"], "chemical_substance")
        service = SubstanceRegistryMaterializationService()
        first = service.materialize_decision(decision["id"], "worker-B", {"job": "test"})
        second = service.materialize_decision(decision["id"], "worker-C")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["mutation_type"], "create_new_substance")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT preferred_name,normalized_name,substance_type,status FROM substances WHERE id=%s", (first["target_substance_id"],)); self.assertEqual(cur.fetchone(), (decision["proposed_preferred_name"], decision["proposed_normalized_name"], "chemical_substance", "active"))
                cur.execute("SELECT substance_id,verification_status,is_primary,identifier_value,source_dataset_release_id,ingestion_run_id,provenance FROM substance_identifiers WHERE id=%s", (first["substance_identifier_id"],)); identifier = cur.fetchone()
                self.assertEqual(identifier[:3], (first["target_substance_id"], "verified", True))
                self.assertEqual(identifier[3], record.substance_identifiers[0].raw_value)
                self.assertEqual(identifier[4:6], (None, None)); self.assertEqual(identifier[6]["decision_id"], decision["id"])
                cur.execute("SELECT count(*) FROM substance_resolution_candidates WHERE id=%s", (candidate["candidate_id"],)); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()
        resolved = PostgresScientificSubstanceResolver().resolve(record)
        self.assertEqual((resolved.status, resolved.record.substance_id), ("resolved", first["target_substance_id"]))
        self.assertEqual((decision["reviewed_by"], first["materialized_by"]), ("reviewer-A", "worker-B"))

    def test_same_name_different_scientific_identifiers_create_distinct_substances(self):
        values = []
        for _ in range(2):
            *_, decision = self.reviewed_creation(preferred_name="Same Display", normalized_name="same display")
            values.append(SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker"))
        self.assertNotEqual(values[0]["target_substance_id"], values[1]["target_substance_id"])
        self.assertNotEqual(values[0]["substance_identifier_id"], values[1]["substance_identifier_id"])
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM substances WHERE normalized_name='same display'"); self.assertEqual(cur.fetchone()[0], 2)
        finally: conn.close()

    def test_stale_identifier_collision_rolls_back_substance(self):
        _, _, _, namespace_key, record, _, decision = self.reviewed_creation(normalized_name="stale proposed")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM substance_identifier_namespaces WHERE namespace_key=%s AND namespace_version='1'", (namespace_key,)); namespace_id = cur.fetchone()[0]
                cur.execute("SELECT id FROM substances WHERE status='active' ORDER BY id LIMIT 1"); target = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,'stale','x',%s,'verified')", (target, namespace_id, record.substance_identifiers[0].normalized_value))
            conn.commit()
        finally: conn.close()
        with self.assertRaisesRegex(SubstanceRegistryMaterializationError, "now exists"):
            SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM substances WHERE normalized_name='stale proposed'"); self.assertEqual(cur.fetchone()[0], 0)
                cur.execute("SELECT count(*) FROM substance_registry_materializations WHERE decision_id=%s", (decision["id"],)); self.assertEqual(cur.fetchone()[0], 0)
        finally: conn.close()

    def test_invalid_payload_and_ineligible_candidates_are_rejected(self):
        prepared, _, result, _, _, namespace_key = self.fixture(); review = SubstanceResolutionReviewService()
        record = self.unknown(result.records[0], namespace_key); resolution = PostgresScientificSubstanceResolver().resolve(record)
        candidate = review.record_resolution(prepared.id, record, resolution)[0]
        for payload in ({}, {"preferred_name": "X", "normalized_name": "x", "substance_type": "chemical"}):
            with self.subTest(payload=payload):
                with self.assertRaises(SubstanceResolutionReviewError): review.decide(candidate["candidate_id"], "create_new_substance", "reviewer", "reason", **payload)
        unknown = self.unknown(result.records[0], f"missing_{uuid.uuid4().hex}"); unknown_resolution = PostgresScientificSubstanceResolver().resolve(unknown)
        unknown_candidate = review.record_resolution(prepared.id, unknown, unknown_resolution)[0]
        with self.assertRaises(SubstanceResolutionReviewError): review.decide(unknown_candidate["candidate_id"], "create_new_substance", "reviewer", "reason", preferred_name="X", normalized_name="x", substance_type="unknown")
        conn = get_connection()
        try:
            with conn.cursor() as cur: cur.execute("UPDATE substance_resolution_candidates SET candidate_kind='identity_conflict' WHERE id=%s", (candidate["candidate_id"],))
            conn.commit()
        finally: conn.close()
        with self.assertRaises(SubstanceResolutionReviewError): review.decide(candidate["candidate_id"], "create_new_substance", "reviewer", "reason", preferred_name="X", normalized_name="x", substance_type="unknown")

    def test_concurrent_same_decision_creates_one_complete_registry_identity(self):
        *_, decision = self.reviewed_creation(); barrier = threading.Barrier(2); results = []; errors = []
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
                cur.execute("SELECT count(*) FROM substances WHERE id=%s", (results[0]["target_substance_id"],)); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("SELECT count(*) FROM substance_identifiers WHERE id=%s", (results[0]["substance_identifier_id"],)); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()

    def test_competing_creation_for_same_identifier_has_one_winner(self):
        prepared, _, _, namespace_key, record, candidate, decision1 = self.reviewed_creation()
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT namespace_id,namespace_version,normalized_value FROM substance_resolution_candidates WHERE id=%s", (candidate["candidate_id"],)); namespace_id, version, value = cur.fetchone()
                cur.execute("INSERT INTO substance_resolution_candidates(candidate_key,candidate_kind,namespace_id,namespace_key,namespace_version,normalized_value) VALUES(%s,'unknown_identifier',%s,%s,%s,%s) RETURNING id", ("c"*64, namespace_id, namespace_key, version, value)); second_candidate = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_resolution_candidate_occurrences(candidate_id,ingestion_run_id,source_record_key,resolution_outcome,reason_code,raw_identifiers) SELECT %s,ingestion_run_id,source_record_key||'_competitor',resolution_outcome,reason_code,raw_identifiers FROM substance_resolution_candidate_occurrences WHERE candidate_id=%s LIMIT 1", (second_candidate, candidate["candidate_id"]))
            conn.commit()
        finally: conn.close()
        decision2 = SubstanceResolutionReviewService().decide(second_candidate, "create_new_substance", "reviewer-B", "competing", preferred_name="Competitor", normalized_name="competitor", substance_type="unknown")
        barrier = threading.Barrier(2); wins = []; conflicts = []
        def apply(decision):
            try:
                barrier.wait(); wins.append(SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker"))
            except SubstanceRegistryMaterializationError as exc: conflicts.append(exc.code)
        threads = [threading.Thread(target=apply, args=(decision,)) for decision in (decision1, decision2)]
        [thread.start() for thread in threads]; [thread.join(20) for thread in threads]
        self.assertEqual((len(wins), len(conflicts)), (1, 1)); self.assertIn(conflicts[0], {"identifier_creation_conflict", "identifier_creation_stale"})
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM substance_identifiers WHERE namespace_id=%s AND normalized_value=%s", (namespace_id, value)); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("SELECT count(*) FROM substance_registry_materializations WHERE decision_id IN (%s,%s)", (decision1["id"], decision2["id"])); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()

    def test_full_learning_loop_persists_future_evidence_only(self):
        prepared, ingestion, result, _, _, namespace_key = self.fixture(); record = self.unknown(result.records[0], namespace_key)
        parser_result = result.model_copy(update={"records": (record,)})
        review = SubstanceResolutionReviewService(); executor = ScientificIngestionExecutor(_StaticParser(parser_result), PostgresScientificSubstanceResolver(), ingestion, resolution_review_service=review)
        first = executor.execute(prepared); self.assertEqual((first.records_accepted, first.records_rejected), (0, 1))
        conn = get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT candidate_id FROM substance_resolution_candidate_occurrences WHERE ingestion_run_id=%s", (prepared.id,)); candidate_id = cur.fetchone()[0]
        finally: conn.close()
        decision = review.decide(candidate_id, "create_new_substance", "reviewer", "new identity", preferred_name="Learned Substance", normalized_name=f"learned {uuid.uuid4().hex}", substance_type="unknown")
        materialization = SubstanceRegistryMaterializationService().materialize_decision(decision["id"], "worker")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO scientific_ingestion_runs(release_id,run_key,idempotency_key,importer_name,importer_version,source_adapter_version,acquisition_version,parser_version,normalization_schema_version,artifact_manifest_algorithm,artifact_manifest_fingerprint,run_status) SELECT release_id,%s,%s,importer_name,importer_version,source_adapter_version,acquisition_version,parser_version,normalization_schema_version,artifact_manifest_algorithm,artifact_manifest_fingerprint,'pending' FROM scientific_ingestion_runs WHERE id=%s RETURNING id,run_key""", (str(uuid.uuid4()), f"future-{uuid.uuid4().hex}", prepared.id)); run_id, run_key = cur.fetchone()
                cur.execute("INSERT INTO scientific_ingestion_run_artifacts(ingestion_run_id,release_artifact_id,manifest_position) SELECT %s,release_artifact_id,manifest_position FROM scientific_ingestion_run_artifacts WHERE ingestion_run_id=%s", (run_id, prepared.id))
            conn.commit()
        finally: conn.close()
        future = PreparedScientificIngestionRun(run_id, run_key, "pending", prepared.manifest, False)
        second = ScientificIngestionExecutor(_StaticParser(parser_result), PostgresScientificSubstanceResolver(), ingestion, resolution_review_service=review).execute(future)
        self.assertEqual((second.records_accepted, second.records_rejected, second.assessments_written), (1, 0, 1))
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s AND substance_id=%s", (run_id, materialization["target_substance_id"])); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("SELECT count(*) FROM substance_resolution_candidate_occurrences WHERE ingestion_run_id=%s", (run_id,)); self.assertEqual(cur.fetchone()[0], 0)
        finally: conn.close()


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1", "requires lifecycle PostgreSQL")
class ControlledSubstanceCreationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]
    def alembic(self, *args, success=True):
        result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=self.backend, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr); return result

    def test_safe_and_unsafe_lifecycle_and_name_constraint(self):
        self.alembic("downgrade", "0015_registry_materialization")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM pg_constraint WHERE conrelid='substances'::regclass AND contype='u' AND pg_get_constraintdef(oid)='UNIQUE (normalized_name)'"); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()
        self.alembic("upgrade", "0016_substance_creation")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM pg_constraint WHERE conrelid='substances'::regclass AND contype='u' AND pg_get_constraintdef(oid)='UNIQUE (normalized_name)'"); self.assertEqual(cur.fetchone()[0], 0)
                cur.execute("SELECT count(*) FROM pg_indexes WHERE tablename='substances' AND indexname='idx_substances_normalized_name'"); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()
        self.alembic("downgrade", "0015_registry_materialization"); self.alembic("upgrade", "0016_substance_creation")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                suffix = uuid.uuid4().hex
                cur.execute("INSERT INTO substances(preferred_name,normalized_name) VALUES('A',%s),('B',%s) RETURNING id", (suffix, suffix)); duplicate_ids = [row[0] for row in cur.fetchall()]
            conn.commit()
        finally: conn.close()
        failed = self.alembic("downgrade", "0015_registry_materialization", success=False); self.assertIn("not representable", failed.stdout + failed.stderr)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cur.fetchone()[0], "0016_substance_creation")
                cur.execute("SELECT count(*) FROM substances WHERE id=ANY(%s)", (duplicate_ids,)); self.assertEqual(cur.fetchone()[0], 2)
                cur.execute("DELETE FROM substances WHERE id=ANY(%s)", (duplicate_ids,))
            conn.commit()
        finally: conn.close()
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                suffix = uuid.uuid4().hex
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Lifecycle creation','v1') RETURNING id", (f"creation_{suffix}",)); namespace_id = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_resolution_candidates(candidate_key,candidate_kind,namespace_id,namespace_key,namespace_version,normalized_value,candidate_status) VALUES(%s,'unknown_identifier',%s,%s,'1','new-x','resolved_new') RETURNING id", ("d"*64, namespace_id, f"creation_{suffix}")); candidate_id = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_resolution_decisions(candidate_id,decision_type,reviewed_by,reviewed_at,reason_code,proposed_preferred_name,proposed_normalized_name,proposed_substance_type) VALUES(%s,'create_new_substance','reviewer',NOW(),'approved','New X','new x','unknown') RETURNING id", (candidate_id,)); decision_id = cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        failed = self.alembic("downgrade", "0015_registry_materialization", success=False); self.assertIn("not representable", failed.stdout + failed.stderr)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cur.fetchone()[0], "0016_substance_creation")
                cur.execute("SELECT candidate_status FROM substance_resolution_candidates WHERE id=%s", (candidate_id,)); self.assertEqual(cur.fetchone()[0], "resolved_new")
                cur.execute("SELECT decision_type FROM substance_resolution_decisions WHERE id=%s", (decision_id,)); self.assertEqual(cur.fetchone()[0], "create_new_substance")
        finally: conn.close()



if __name__ == "__main__": unittest.main()
