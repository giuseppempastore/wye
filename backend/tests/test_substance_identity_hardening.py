import hashlib
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


def create_source_release_run(cur, suffix):
    cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id", (f"identity_source_{suffix}", f"Identity source {suffix}")); source_id = cur.fetchone()[0]
    cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,'Identity dataset',%s) RETURNING id", (source_id, f"identity_dataset_{suffix}")); dataset_id = cur.fetchone()[0]
    cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,'Identity release') RETURNING id", (dataset_id, f"identity_release_{suffix}")); release_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO scientific_ingestion_runs(release_id,run_key,importer_name,
        importer_version,source_adapter_version,acquisition_version,parser_version,
        normalization_schema_version,artifact_manifest_algorithm,artifact_manifest_fingerprint)
        VALUES(%s,%s,'test','1','adapter-1','acquisition-1','parser-1','normalization-1',
        'sha256',%s) RETURNING id""", (release_id, str(uuid.uuid4()), "a" * 64)); run_id = cur.fetchone()[0]
    return source_id, dataset_id, release_id, run_id


def create_substance(cur, suffix):
    cur.execute("INSERT INTO substances(preferred_name,normalized_name) VALUES(%s,%s) RETURNING id", (f"Substance {suffix}", f"substance-{suffix}"))
    return cur.fetchone()[0]


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0011")
class SubstanceIdentityHardeningTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(); self.conn.autocommit = False
        self.cur = self.conn.cursor(); self.cur.execute("SAVEPOINT substance_identity_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT substance_identity_test"); self.conn.commit()
        finally: self.cur.close(); self.conn.close()

    def namespace(self, key=None, version="1", owner=None, **overrides):
        values = dict(key=key or f"test_namespace_{uuid.uuid4().hex}", version=version,
                      display="Test namespace", owner=owner, rule="normalization_v1",
                      provenance=Json({"fixture": True}))
        values.update(overrides)
        self.cur.execute("""INSERT INTO substance_identifier_namespaces(
            namespace_key,namespace_version,display_name,owner_source_id,
            normalization_rule_version,provenance)
            VALUES(%(key)s,%(version)s,%(display)s,%(owner)s,%(rule)s,%(provenance)s)
            RETURNING id""", values)
        return self.cur.fetchone()[0]

    def identifier(self, substance_id=None, namespace_id=None, **overrides):
        substance_id = substance_id or create_substance(self.cur, uuid.uuid4().hex)
        namespace_id = namespace_id or self.namespace()
        values = dict(substance=substance_id, namespace=namespace_id, system="test_system",
                      raw=" Raw-123 ", normalized=f"normalized-{uuid.uuid4().hex}",
                      primary=False, status="pending_review", release=None, run=None,
                      provenance=Json({"fixture": "identifier"}))
        values.update(overrides)
        self.cur.execute("""INSERT INTO substance_identifiers(
            substance_id,namespace_id,identifier_system,identifier_value,normalized_value,
            is_primary,verification_status,source_dataset_release_id,ingestion_run_id,provenance)
            VALUES(%(substance)s,%(namespace)s,%(system)s,%(raw)s,%(normalized)s,
            %(primary)s,%(status)s,%(release)s,%(run)s,%(provenance)s) RETURNING id""", values)
        return self.cur.fetchone()[0]

    def reset(self):
        self.cur.execute("ROLLBACK TO SAVEPOINT substance_identity_test")
        self.cur.execute("SAVEPOINT substance_identity_test")

    def test_namespace_identity_versions_owner_and_required_fields(self):
        key = f"namespace_{uuid.uuid4().hex}"; self.namespace(key, "1")
        with self.assertRaises(psycopg2.IntegrityError): self.namespace(key, "1")
        self.reset(); key = f"namespace_{uuid.uuid4().hex}"
        self.namespace(key, "1"); self.namespace(key, "2")
        source_id, _, _, _ = create_source_release_run(self.cur, uuid.uuid4().hex)
        self.namespace(owner=source_id)
        with self.assertRaises(psycopg2.IntegrityError): self.namespace(owner=9223372036854775807)

    def test_namespace_machine_key_and_normalization_rule_are_enforced(self):
        for values in (dict(key="Invalid Key"), dict(key="_leading"), dict(rule="")):
            with self.subTest(values=values):
                with self.assertRaises(psycopg2.IntegrityError): self.namespace(**values)
                self.reset()

    def test_identifier_namespace_identity_raw_provenance_and_foreign_keys(self):
        substance = create_substance(self.cur, uuid.uuid4().hex)
        first_namespace = self.namespace(); second_namespace = self.namespace()
        first = self.identifier(substance, first_namespace, raw="CAS raw", normalized="same-value")
        with self.assertRaises(psycopg2.IntegrityError):
            self.identifier(create_substance(self.cur, uuid.uuid4().hex), first_namespace, normalized="same-value")
        self.reset(); substance = create_substance(self.cur, uuid.uuid4().hex)
        first_namespace = self.namespace(); second_namespace = self.namespace()
        first = self.identifier(substance, first_namespace, raw="CAS raw", normalized="same-value")
        self.identifier(substance, second_namespace, raw="different raw", normalized="same-value")
        self.cur.execute("SELECT identifier_value,normalized_value,provenance FROM substance_identifiers WHERE id=%s", (first,))
        self.assertEqual(self.cur.fetchone(), ("CAS raw", "same-value", {"fixture": "identifier"}))
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("""INSERT INTO substance_identifiers(
                substance_id,identifier_system,identifier_value,normalized_value)
                VALUES(%s,'legacy','raw','missing-namespace')""", (substance,))
        self.reset(); substance = create_substance(self.cur, uuid.uuid4().hex)
        with self.assertRaises(psycopg2.IntegrityError): self.identifier(substance, 9223372036854775807)

    def test_identifier_ingestion_and_release_provenance_are_optional_and_restricted(self):
        source_id, dataset_id, release_id, run_id = create_source_release_run(self.cur, uuid.uuid4().hex)
        namespace = self.namespace(owner=source_id); substance = create_substance(self.cur, uuid.uuid4().hex)
        self.identifier(substance, namespace)
        identifier_id = self.identifier(substance, namespace, normalized="with-provenance", release=release_id, run=run_id)
        self.cur.execute("SELECT source_dataset_release_id,ingestion_run_id FROM substance_identifiers WHERE id=%s", (identifier_id,))
        self.assertEqual(self.cur.fetchone(), (release_id, run_id))
        with self.assertRaises(psycopg2.IntegrityError): self.identifier(substance, namespace, normalized="bad-run", run=9223372036854775807)

    def test_primary_verified_invariants(self):
        substance = create_substance(self.cur, uuid.uuid4().hex); first_namespace = self.namespace(); second_namespace = self.namespace()
        self.identifier(substance, first_namespace, normalized="primary-1", primary=True, status="verified")
        with self.assertRaises(psycopg2.IntegrityError):
            self.identifier(substance, first_namespace, normalized="primary-2", primary=True, status="verified")
        self.reset(); substance = create_substance(self.cur, uuid.uuid4().hex); first_namespace = self.namespace(); second_namespace = self.namespace()
        self.identifier(substance, first_namespace, normalized="primary-1", primary=True, status="verified")
        self.identifier(substance, second_namespace, normalized="primary-2", primary=True, status="verified")
        for status in ("pending_review", "rejected", "deprecated"):
            with self.subTest(status=status):
                with self.assertRaises(psycopg2.IntegrityError):
                    self.identifier(substance, first_namespace, normalized=f"invalid-{status}", primary=True, status=status)
                self.cur.execute("ROLLBACK TO SAVEPOINT substance_identity_test")
                self.cur.execute("SAVEPOINT substance_identity_test")
                substance = create_substance(self.cur, uuid.uuid4().hex); first_namespace = self.namespace()
        self.identifier(substance, first_namespace, normalized="non-primary-1", primary=False)
        self.identifier(substance, first_namespace, normalized="non-primary-2", primary=False)

    def test_concurrent_identifier_collision_has_one_owner(self):
        setup = get_connection(); suffix = uuid.uuid4().hex
        try:
            with setup.cursor() as cur:
                first_substance = create_substance(cur, suffix + "a"); second_substance = create_substance(cur, suffix + "b")
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Race namespace','v1') RETURNING id", (f"race_namespace_{suffix}",)); namespace_id = cur.fetchone()[0]
            setup.commit()
        finally: setup.close()
        barrier = threading.Barrier(2); results = []; unexpected = []
        def worker(substance_id):
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    barrier.wait(timeout=10)
                    cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value) VALUES(%s,%s,'test','X','collision-x')", (substance_id, namespace_id))
                conn.commit(); results.append("committed")
            except psycopg2.IntegrityError: conn.rollback(); results.append("integrity_error")
            except Exception as exc: conn.rollback(); unexpected.append(repr(exc))
            finally: conn.close()
        first = threading.Thread(target=worker, args=(first_substance,)); second = threading.Thread(target=worker, args=(second_substance,))
        first.start(); second.start(); first.join(15); second.join(15)
        self.assertFalse(first.is_alive()); self.assertFalse(second.is_alive()); self.assertEqual(unexpected, [])
        self.assertCountEqual(results, ["committed", "integrity_error"])
        cleanup = get_connection()
        try:
            with cleanup.cursor() as cur:
                cur.execute("SELECT count(*) FROM substance_identifiers WHERE namespace_id=%s AND normalized_value='collision-x'", (namespace_id,)); self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM substance_identifiers WHERE namespace_id=%s", (namespace_id,)); cur.execute("DELETE FROM substance_identifier_namespaces WHERE id=%s", (namespace_id,)); cur.execute("DELETE FROM substances WHERE id IN (%s,%s)", (first_substance, second_substance))
            cleanup.commit()
        finally: cleanup.close()


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1", "requires isolated PostgreSQL")
class SubstanceIdentityMigrationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]
    def alembic(self, *args, expect_success=True):
        result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=self.backend, text=True, capture_output=True, check=False)
        if expect_success: self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else: self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_backfill_and_0010_0011_0010_0011_lifecycle(self):
        suffix = uuid.uuid4().hex; legacy_system = "Legacy System / X"
        self.alembic("downgrade", "0010_assessment_finding_identity")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                source_id, dataset_id, release_id, run_id = create_source_release_run(cur, suffix)
                substance_id = create_substance(cur, suffix)
                cur.execute("""INSERT INTO substance_identifiers(substance_id,identifier_system,
                    identifier_value,normalized_value,is_primary,verification_status,
                    source_dataset_release_id,provenance)
                    VALUES(%s,%s,' Raw Legacy ','legacy-value',TRUE,'verified',%s,%s) RETURNING id""",
                    (substance_id, legacy_system, release_id, Json({"legacy": True}))); identifier_id = cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        expected_key = "legacy_system_" + hashlib.sha256(legacy_system.encode()).hexdigest()
        self.alembic("upgrade", "0011_substance_identity_registry"); self.assert_backfill(identifier_id, substance_id, release_id, expected_key, True)
        self.alembic("downgrade", "0010_assessment_finding_identity"); self.assert_backfill(identifier_id, substance_id, release_id, expected_key, False)
        self.alembic("upgrade", "0011_substance_identity_registry"); self.assert_backfill(identifier_id, substance_id, release_id, expected_key, True)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM substance_identifiers WHERE id=%s", (identifier_id,)); cur.execute("DELETE FROM scientific_ingestion_runs WHERE id=%s", (run_id,)); cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,)); cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,)); cur.execute("DELETE FROM substances WHERE id=%s", (substance_id,)); cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally: conn.close()
        self.alembic("upgrade", "head")

    def assert_backfill(self, identifier_id, substance_id, release_id, key, hardened):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.substance_identifier_namespaces')"); self.assertEqual(cur.fetchone()[0] is not None, hardened)
                if hardened:
                    cur.execute("""SELECT n.namespace_key,n.namespace_version,n.owner_source_id,
                        i.identifier_value,i.normalized_value,i.substance_id,i.verification_status,
                        i.is_primary,i.provenance,i.source_dataset_release_id
                        FROM substance_identifiers i JOIN substance_identifier_namespaces n ON n.id=i.namespace_id
                        WHERE i.id=%s""", (identifier_id,))
                    self.assertEqual(cur.fetchone(), (key,"legacy_1",None," Raw Legacy ","legacy-value",substance_id,"verified",True,{"legacy":True},release_id))
                else:
                    cur.execute("SELECT identifier_value,normalized_value,substance_id,verification_status,is_primary,provenance,source_dataset_release_id FROM substance_identifiers WHERE id=%s", (identifier_id,)); self.assertEqual(cur.fetchone(), (" Raw Legacy ","legacy-value",substance_id,"verified",True,{"legacy":True},release_id))
        finally: conn.close()

    def test_downgrade_refuses_new_namespace_semantics(self):
        conn = get_connection(); key = f"new_namespace_{uuid.uuid4().hex}"
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); starting_revision = cur.fetchone()[0]
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','New namespace','v1') RETURNING id", (key,)); namespace_id = cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        self.alembic("downgrade", "0010_assessment_finding_identity", expect_success=False)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cur.fetchone()[0], starting_revision)
                cur.execute("DELETE FROM substance_identifier_namespaces WHERE id=%s", (namespace_id,))
            conn.commit()
        finally: conn.close()


if __name__ == "__main__": unittest.main()
