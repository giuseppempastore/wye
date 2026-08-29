import os
import subprocess
import sys
import threading
import unittest
import uuid
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

from app.db import get_connection


RUN_SQL = """INSERT INTO scientific_ingestion_runs (
 release_id,run_key,idempotency_key,importer_name,importer_version,
 source_adapter_version,acquisition_version,parser_version,normalization_schema_version,
 artifact_manifest_algorithm,artifact_manifest_fingerprint,
 config_checksum_algorithm,config_checksum_value,
 parser_output_checksum_algorithm,parser_output_checksum_value,
 run_status,started_at,completed_at,records_seen,records_accepted,records_rejected,
 assessments_written,findings_written,warnings_count,error_code,error_summary,provenance)
VALUES (%(release_id)s,%(run_key)s,%(idempotency_key)s,%(importer_name)s,%(importer_version)s,
 %(source_adapter_version)s,%(acquisition_version)s,%(parser_version)s,
 %(normalization_schema_version)s,%(artifact_manifest_algorithm)s,
 %(artifact_manifest_fingerprint)s,%(config_checksum_algorithm)s,%(config_checksum_value)s,
 %(parser_output_checksum_algorithm)s,%(parser_output_checksum_value)s,%(run_status)s,
 %(started_at)s,%(completed_at)s,%(records_seen)s,%(records_accepted)s,
 %(records_rejected)s,%(assessments_written)s,%(findings_written)s,%(warnings_count)s,
 %(error_code)s,%(error_summary)s,%(provenance)s) RETURNING id"""


def create_release(cur, suffix):
    cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id", (f"run_source_{suffix}", f"Run source {suffix}"))
    source_id = cur.fetchone()[0]
    cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,'Run dataset',%s) RETURNING id", (source_id, f"run_dataset_{suffix}"))
    dataset_id = cur.fetchone()[0]
    cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,'Run release') RETURNING id", (dataset_id, f"run_release_{suffix}"))
    return source_id, dataset_id, cur.fetchone()[0]


def run_params(release_id, **overrides):
    values = dict(
        release_id=release_id, run_key=str(uuid.uuid4()), idempotency_key=None,
        importer_name="wye_scientific_ingestion", importer_version="1.0.0",
        source_adapter_version="adapter-1", acquisition_version="acquisition-1",
        parser_version="parser-1", normalization_schema_version="normalization-1",
        artifact_manifest_algorithm="sha256", artifact_manifest_fingerprint="a" * 64,
        config_checksum_algorithm=None, config_checksum_value=None,
        parser_output_checksum_algorithm=None, parser_output_checksum_value=None,
        run_status="pending", started_at=None, completed_at=None,
        records_seen=0, records_accepted=0, records_rejected=0,
        assessments_written=0, findings_written=0, warnings_count=0,
        error_code=None, error_summary=None, provenance=None,
    )
    values.update(overrides)
    return values


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0009")
class ScientificIngestionRunTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(); self.conn.autocommit = False
        self.cur = self.conn.cursor(); self.cur.execute("SAVEPOINT ingestion_run_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT ingestion_run_test"); self.conn.commit()
        finally:
            self.cur.close(); self.conn.close()

    def release(self):
        return create_release(self.cur, uuid.uuid4().hex)[2]

    def insert(self, release_id=None, **overrides):
        self.cur.execute(RUN_SQL, run_params(release_id or self.release(), **overrides))
        return self.cur.fetchone()[0]

    def reset(self):
        self.cur.execute("ROLLBACK TO SAVEPOINT ingestion_run_test")
        self.cur.execute("SAVEPOINT ingestion_run_test")

    def test_valid_run_fk_unique_run_key_and_multiple_runs_per_release(self):
        release_id = self.release(); run_key = str(uuid.uuid4())
        self.insert(release_id, run_key=run_key); self.insert(release_id)
        self.cur.execute("SELECT count(*) FROM scientific_ingestion_runs WHERE release_id=%s", (release_id,))
        self.assertEqual(self.cur.fetchone()[0], 2)
        with self.assertRaises(psycopg2.IntegrityError): self.insert(release_id, run_key=run_key)
        self.reset()
        with self.assertRaises(psycopg2.IntegrityError): self.insert(9223372036854775807)

    def test_status_and_timestamp_invariants(self):
        self.insert(); self.reset()
        invalid = (
            dict(run_status="running"),
            dict(run_status="running", started_at="2026-08-28T10:00:00Z", completed_at="2026-08-28T10:01:00Z"),
            dict(run_status="succeeded"),
            dict(run_status="failed", started_at="2026-08-28T10:00:00Z", completed_at="2026-08-28T10:01:00Z"),
            dict(run_status="succeeded", started_at="2026-08-28T10:00:00Z", completed_at="2026-08-28T09:59:00Z"),
        )
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(psycopg2.IntegrityError): self.insert(**values)
                self.reset()
        self.insert(run_status="cancelled", started_at="2026-08-28T10:00:00Z", completed_at="2026-08-28T10:01:00Z")

    def test_counter_invariants(self):
        for values in (dict(warnings_count=-1), dict(records_seen=2, records_accepted=2, records_rejected=1)):
            with self.subTest(values=values):
                with self.assertRaises(psycopg2.IntegrityError): self.insert(**values)
                self.reset()
        self.insert(records_seen=3, records_accepted=2, records_rejected=1, assessments_written=7, findings_written=12)

    def test_checksum_pairs_and_sha256_formats(self):
        invalid = (
            dict(config_checksum_algorithm="sha256"), dict(config_checksum_value="b" * 64),
            dict(parser_output_checksum_algorithm="sha256"), dict(parser_output_checksum_value="c" * 64),
            dict(config_checksum_algorithm="sha256", config_checksum_value="B" * 64),
            dict(parser_output_checksum_algorithm="sha256", parser_output_checksum_value="c" * 63),
            dict(artifact_manifest_fingerprint="A" * 64),
        )
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(psycopg2.IntegrityError): self.insert(**values)
                self.reset()
        self.insert(artifact_manifest_fingerprint="d" * 64,
                    config_checksum_algorithm="sha256", config_checksum_value="e" * 64,
                    parser_output_checksum_algorithm="sha256", parser_output_checksum_value="f" * 64)

    def test_idempotency_scope(self):
        release_id = self.release(); self.insert(release_id, idempotency_key="request-1")
        with self.assertRaises(psycopg2.IntegrityError): self.insert(release_id, idempotency_key="request-1")
        self.reset(); release_id = self.release()
        self.insert(release_id, idempotency_key="request-1")
        self.insert(release_id, idempotency_key="request-2")
        self.insert(release_id, idempotency_key="request-1", parser_version="parser-2")
        self.insert(release_id, idempotency_key="request-1", normalization_schema_version="normalization-2")
        self.insert(release_id, idempotency_key="request-1", artifact_manifest_fingerprint="b" * 64)
        self.insert(release_id, idempotency_key="request-1", config_checksum_algorithm="sha256", config_checksum_value="c" * 64)
        self.insert(release_id); self.insert(release_id)

    def test_jsonb_provenance(self):
        run_id = self.insert(provenance=Json({"worker": "fixture", "attempt": 1}))
        self.cur.execute("SELECT provenance FROM scientific_ingestion_runs WHERE id=%s", (run_id,))
        self.assertEqual(self.cur.fetchone()[0], {"worker": "fixture", "attempt": 1})

    def test_concurrent_same_logical_run_has_one_commit_one_conflict(self):
        setup = get_connection()
        try:
            with setup.cursor() as cur: source_id, dataset_id, release_id = create_release(cur, uuid.uuid4().hex)
            setup.commit()
        finally: setup.close()
        barrier = threading.Barrier(2); results = []; unexpected = []
        def worker():
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    barrier.wait(timeout=10)
                    cur.execute(RUN_SQL, run_params(release_id, idempotency_key="concurrent-request"))
                conn.commit(); results.append("committed")
            except psycopg2.IntegrityError:
                conn.rollback(); results.append("integrity_error")
            except Exception as exc:
                conn.rollback(); unexpected.append(repr(exc))
            finally: conn.close()
        first = threading.Thread(target=worker); second = threading.Thread(target=worker)
        first.start(); second.start(); first.join(15); second.join(15)
        self.assertFalse(first.is_alive()); self.assertFalse(second.is_alive())
        self.assertEqual(unexpected, []); self.assertCountEqual(results, ["committed", "integrity_error"])
        cleanup = get_connection()
        try:
            with cleanup.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_ingestion_runs WHERE release_id=%s", (release_id,)); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM scientific_ingestion_runs WHERE release_id=%s", (release_id,))
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            cleanup.commit()
        finally: cleanup.close()


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1", "requires isolated PostgreSQL")
class ScientificIngestionRunMigrationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]
    def alembic(self, *args):
        result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=self.backend, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_0008_0009_0008_0009_preserves_release_and_artifact(self):
        suffix = uuid.uuid4().hex; self.alembic("downgrade", "0008_release_artifact_integrity")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                source_id, dataset_id, release_id = create_release(cur, suffix)
                cur.execute("INSERT INTO storage_objects(storage_provider,bucket,object_key,checksum_algorithm,checksum_value) VALUES('test','lifecycle',%s,'sha256',%s) RETURNING id", (f"runs/{suffix}", "a" * 64)); storage_id = cur.fetchone()[0]
                cur.execute("INSERT INTO scientific_release_artifacts(release_id,storage_object_id,artifact_key,artifact_role,raw_checksum_algorithm,raw_checksum_value,acquired_at) VALUES(%s,%s,'primary','primary','sha256',%s,NOW()) RETURNING id", (release_id, storage_id, "a" * 64)); artifact_id = cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        self.alembic("upgrade", "0009_scientific_ingestion_runs"); self.assert_state(release_id, artifact_id, True)
        self.alembic("downgrade", "0008_release_artifact_integrity"); self.assert_state(release_id, artifact_id, False)
        self.alembic("upgrade", "0009_scientific_ingestion_runs"); self.assert_state(release_id, artifact_id, True)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM scientific_release_artifacts WHERE id=%s", (artifact_id,)); cur.execute("DELETE FROM storage_objects WHERE id=%s", (storage_id,)); cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,)); cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,)); cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally: conn.close()
        self.alembic("upgrade", "head")

    def assert_state(self, release_id, artifact_id, exists):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                for name in ("scientific_ingestion_runs", "scientific_ingestion_runs_id_seq", "uq_scientific_ingestion_runs_idempotency"):
                    cur.execute("SELECT to_regclass(%s)", (f"public.{name}",)); self.assertEqual(cur.fetchone()[0] is not None, exists)
                cur.execute("SELECT count(*) FROM source_dataset_releases WHERE id=%s", (release_id,)); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("SELECT count(*) FROM scientific_release_artifacts WHERE id=%s", (artifact_id,)); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()


if __name__ == "__main__": unittest.main()
