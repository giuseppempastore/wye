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


def create_context(cur, suffix):
    cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id", (f"assessment_source_{suffix}", f"Assessment source {suffix}"))
    source_id = cur.fetchone()[0]
    cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,'Assessment dataset',%s) RETURNING id", (source_id, f"assessment_dataset_{suffix}"))
    dataset_id = cur.fetchone()[0]
    cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,'Assessment release') RETURNING id", (dataset_id, f"assessment_release_{suffix}"))
    release_id = cur.fetchone()[0]
    cur.execute("INSERT INTO substances(preferred_name,normalized_name) VALUES(%s,%s) RETURNING id", (f"Substance {suffix}", f"substance-{suffix}"))
    substance_id = cur.fetchone()[0]
    return source_id, dataset_id, release_id, substance_id


def create_run(cur, release_id, parser="parser-1"):
    cur.execute("""INSERT INTO scientific_ingestion_runs(
        release_id,run_key,importer_name,importer_version,source_adapter_version,
        acquisition_version,parser_version,normalization_schema_version,
        artifact_manifest_algorithm,artifact_manifest_fingerprint)
        VALUES(%s,%s,'test_importer','1','adapter-1','acquisition-1',%s,
        'normalization-1','sha256',%s) RETURNING id""",
        (release_id, str(uuid.uuid4()), parser, "a" * 64))
    return cur.fetchone()[0]


def assessment_sql():
    return """INSERT INTO scientific_assessments(
        substance_id,source_dataset_release_id,ingestion_run_id,source_record_key,
        assessment_type,assessment_version,external_assessment_id,
        external_assessment_version,raw_record,normalized_checksum_algorithm,
        normalized_checksum_value)
        VALUES(%(substance_id)s,%(release_id)s,%(run_id)s,%(source_record_key)s,
        'hazard','v1',%(external_id)s,%(external_version)s,%(raw_record)s,
        %(checksum_algorithm)s,%(checksum_value)s) RETURNING id"""


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0010")
class AssessmentFindingIdentityTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(); self.conn.autocommit = False
        self.cur = self.conn.cursor(); self.cur.execute("SAVEPOINT assessment_finding_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT assessment_finding_test"); self.conn.commit()
        finally:
            self.cur.close(); self.conn.close()

    def context(self):
        source_id, dataset_id, release_id, substance_id = create_context(self.cur, uuid.uuid4().hex)
        return release_id, substance_id, create_run(self.cur, release_id)

    def assessment(self, release_id=None, substance_id=None, run_id=None, key=None, **overrides):
        if release_id is None:
            release_id, substance_id, run_id = self.context()
        values = dict(substance_id=substance_id, release_id=release_id, run_id=run_id,
                      source_record_key=key or f"assessment_{uuid.uuid4().hex}",
                      external_id=None, external_version=None, raw_record=None,
                      checksum_algorithm=None, checksum_value=None)
        values.update(overrides); self.cur.execute(assessment_sql(), values)
        return self.cur.fetchone()[0]

    def finding(self, assessment_id=None, key=None, **overrides):
        assessment_id = assessment_id or self.assessment()
        values = dict(assessment_id=assessment_id, key=key or f"finding_{uuid.uuid4().hex}",
                      source_finding_key=None, ordinal=None, value_text="finding",
                      conclusion=None, raw_payload=None, algorithm=None, fingerprint=None)
        values.update(overrides)
        self.cur.execute("""INSERT INTO scientific_assessment_findings(
            assessment_id,source_record_key,source_finding_key,source_ordinal,value_text,
            conclusion_text,raw_payload,fingerprint_algorithm,finding_fingerprint)
            VALUES(%(assessment_id)s,%(key)s,%(source_finding_key)s,%(ordinal)s,%(value_text)s,
            %(conclusion)s,%(raw_payload)s,%(algorithm)s,%(fingerprint)s) RETURNING id""", values)
        return self.cur.fetchone()[0]

    def reset(self):
        self.cur.execute("ROLLBACK TO SAVEPOINT assessment_finding_test")
        self.cur.execute("SAVEPOINT assessment_finding_test")

    def test_assessment_run_fk_required_and_raw_record_persisted(self):
        release_id, substance_id, run_id = self.context()
        assessment_id = self.assessment(release_id, substance_id, run_id, "record_1", raw_record=Json({"native": 1}))
        self.cur.execute("SELECT ingestion_run_id,raw_record FROM scientific_assessments WHERE id=%s", (assessment_id,))
        self.assertEqual(self.cur.fetchone(), (run_id, {"native": 1}))
        with self.assertRaises(psycopg2.IntegrityError):
            self.assessment(release_id, substance_id, None, "missing_run")
        self.reset(); release_id, substance_id, _ = self.context()
        with self.assertRaises(psycopg2.IntegrityError):
            self.assessment(release_id, substance_id, 9223372036854775807, "bad_run")

    def test_assessment_identity_is_scoped_to_run_and_allows_reprocessing(self):
        release_id, substance_id, first_run = self.context()
        second_run = create_run(self.cur, release_id, "parser-2")
        self.assessment(release_id, substance_id, first_run, "source_record", external_id="external-1")
        with self.assertRaises(psycopg2.IntegrityError):
            self.assessment(release_id, substance_id, first_run, "source_record")
        self.reset(); release_id, substance_id, first_run = self.context()
        second_run = create_run(self.cur, release_id, "parser-2")
        self.assessment(release_id, substance_id, first_run, "source_record", external_id="external-1")
        self.assessment(release_id, substance_id, second_run, "source_record", external_id="external-1")
        self.cur.execute("SELECT count(*) FROM scientific_assessments WHERE source_dataset_release_id=%s", (release_id,))
        self.assertEqual(self.cur.fetchone()[0], 2)

    def test_normalized_assessment_checksum_pair_and_sha256(self):
        invalid = (("sha256", None), (None, "a" * 64), ("sha256", "A" * 64), ("sha256", "a" * 63))
        for algorithm, value in invalid:
            with self.subTest(algorithm=algorithm, value=value):
                with self.assertRaises(psycopg2.IntegrityError):
                    self.assessment(checksum_algorithm=algorithm, checksum_value=value)
                self.reset()
        self.assessment(checksum_algorithm="sha256", checksum_value="b" * 64)

    def test_finding_identity_is_scoped_to_assessment(self):
        first = self.assessment(); self.finding(first, "finding_record")
        with self.assertRaises(psycopg2.IntegrityError): self.finding(first, "finding_record")
        self.reset(); first = self.assessment(); second = self.assessment()
        self.finding(first, "finding_record"); self.finding(second, "finding_record")

    def test_finding_ordinal_raw_payload_and_minimal_content(self):
        with self.assertRaises(psycopg2.IntegrityError): self.finding(ordinal=-1)
        self.reset()
        finding_id = self.finding(value_text=None, raw_payload=Json({"native": "payload"}), ordinal=0)
        self.cur.execute("SELECT raw_payload,source_ordinal FROM scientific_assessment_findings WHERE id=%s", (finding_id,))
        self.assertEqual(self.cur.fetchone(), ({"native": "payload"}, 0))
        self.finding(value_text=None, conclusion="General conclusion")
        with self.assertRaises(psycopg2.IntegrityError): self.finding(value_text=None)

    def test_finding_fingerprint_pair_and_sha256(self):
        invalid = (("sha256", None), (None, "a" * 64), ("sha256", "A" * 64), ("sha256", "a" * 63))
        for algorithm, value in invalid:
            with self.subTest(algorithm=algorithm, value=value):
                with self.assertRaises(psycopg2.IntegrityError): self.finding(algorithm=algorithm, fingerprint=value)
                self.reset()
        self.finding(algorithm="sha256", fingerprint="c" * 64, source_finding_key="native-finding")

    def test_assessment_and_finding_concurrency(self):
        setup = get_connection()
        try:
            with setup.cursor() as cur:
                source_id, dataset_id, release_id, substance_id = create_context(cur, uuid.uuid4().hex)
                run_id = create_run(cur, release_id)
            setup.commit()
        finally: setup.close()

        assessment_results = self.concurrent_insert(
            assessment_sql(), dict(substance_id=substance_id, release_id=release_id, run_id=run_id,
            source_record_key="race_assessment", external_id=None, external_version=None,
            raw_record=None, checksum_algorithm=None, checksum_value=None))
        self.assertCountEqual(assessment_results, ["committed", "integrity_error"])
        check = get_connection()
        try:
            with check.cursor() as cur:
                cur.execute("SELECT id FROM scientific_assessments WHERE ingestion_run_id=%s AND source_record_key='race_assessment'", (run_id,))
                assessment_id = cur.fetchone()[0]
        finally: check.close()
        finding_query = "INSERT INTO scientific_assessment_findings(assessment_id,source_record_key,value_text) VALUES(%(assessment_id)s,'race_finding','value') RETURNING id"
        finding_results = self.concurrent_insert(finding_query, {"assessment_id": assessment_id})
        self.assertCountEqual(finding_results, ["committed", "integrity_error"])

        cleanup = get_connection()
        try:
            with cleanup.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_assessment_findings WHERE assessment_id=%s", (assessment_id,)); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM scientific_assessments WHERE id=%s", (assessment_id,))
                cur.execute("DELETE FROM scientific_ingestion_runs WHERE id=%s", (run_id,))
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM substances WHERE id=%s", (substance_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            cleanup.commit()
        finally: cleanup.close()

    def concurrent_insert(self, query, params):
        barrier = threading.Barrier(2); results = []; unexpected = []
        def worker():
            conn = get_connection()
            try:
                with conn.cursor() as cur: barrier.wait(timeout=10); cur.execute(query, params)
                conn.commit(); results.append("committed")
            except psycopg2.IntegrityError: conn.rollback(); results.append("integrity_error")
            except Exception as exc: conn.rollback(); unexpected.append(repr(exc))
            finally: conn.close()
        first = threading.Thread(target=worker); second = threading.Thread(target=worker)
        first.start(); second.start(); first.join(15); second.join(15)
        self.assertFalse(first.is_alive()); self.assertFalse(second.is_alive()); self.assertEqual(unexpected, [])
        return results


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1", "requires isolated PostgreSQL")
class AssessmentFindingMigrationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]
    def alembic(self, *args, expect_success=True):
        result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=self.backend, text=True, capture_output=True, check=False)
        if expect_success: self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else: self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_backfill_and_0009_0010_0009_0010_lifecycle(self):
        suffix = uuid.uuid4().hex; self.alembic("downgrade", "0009_scientific_ingestion_runs")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                source_id, dataset_id, release_id, substance_id = create_context(cur, suffix)
                cur.execute("INSERT INTO scientific_assessments(substance_id,source_dataset_release_id,assessment_type,assessment_version) VALUES(%s,%s,'legacy','v1') RETURNING id", (substance_id, release_id)); assessment_id = cur.fetchone()[0]
                cur.execute("INSERT INTO scientific_assessment_findings(assessment_id,value_text) VALUES(%s,'legacy value') RETURNING id", (assessment_id,)); finding_id = cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        self.alembic("upgrade", "0010_assessment_finding_identity"); self.assert_backfill(assessment_id, finding_id, release_id, True)
        self.alembic("downgrade", "0009_scientific_ingestion_runs"); self.assert_backfill(assessment_id, finding_id, release_id, False)
        self.alembic("upgrade", "0010_assessment_finding_identity"); self.assert_backfill(assessment_id, finding_id, release_id, True)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM scientific_assessments WHERE id=%s", (assessment_id,))
                cur.execute("DELETE FROM scientific_ingestion_runs WHERE release_id=%s", (release_id,))
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,)); cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,)); cur.execute("DELETE FROM substances WHERE id=%s", (substance_id,)); cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally: conn.close()
        self.alembic("upgrade", "head")

    def assert_backfill(self, assessment_id, finding_id, release_id, hardened):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='scientific_assessments' AND column_name='ingestion_run_id')"); self.assertEqual(cur.fetchone()[0], hardened)
                if hardened:
                    cur.execute("SELECT source_record_key,r.release_id,r.importer_name FROM scientific_assessments a JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id WHERE a.id=%s", (assessment_id,)); self.assertEqual(cur.fetchone(), (f"legacy_assessment_{assessment_id}", release_id, "legacy_backfill"))
                    cur.execute("SELECT source_record_key FROM scientific_assessment_findings WHERE id=%s", (finding_id,)); self.assertEqual(cur.fetchone()[0], f"legacy_finding_{finding_id}")
                else:
                    cur.execute("SELECT count(*) FROM scientific_assessments WHERE id=%s", (assessment_id,)); self.assertEqual(cur.fetchone()[0], 1)
                    cur.execute("SELECT count(*) FROM scientific_assessment_findings WHERE id=%s", (finding_id,)); self.assertEqual(cur.fetchone()[0], 1)
        finally: conn.close()

    def test_downgrade_refuses_new_identity_data(self):
        conn = get_connection(); suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); starting_revision = cur.fetchone()[0]
                source_id, dataset_id, release_id, substance_id = create_context(cur, suffix); run_id = create_run(cur, release_id)
                cur.execute(assessment_sql(), dict(substance_id=substance_id,release_id=release_id,run_id=run_id,source_record_key="new_record",external_id=None,external_version=None,raw_record=None,checksum_algorithm=None,checksum_value=None)); assessment_id=cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        self.alembic("downgrade", "0009_scientific_ingestion_runs", expect_success=False)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cur.fetchone()[0], starting_revision)
                cur.execute("DELETE FROM scientific_assessments WHERE id=%s", (assessment_id,)); cur.execute("DELETE FROM scientific_ingestion_runs WHERE id=%s", (run_id,)); cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,)); cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,)); cur.execute("DELETE FROM substances WHERE id=%s", (substance_id,)); cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally: conn.close()


if __name__ == "__main__": unittest.main()
