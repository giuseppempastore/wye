import os
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

from app.db import get_connection


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL",
)
class Phase61DowngradeSafetyTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]

    def alembic(self, *args, expect_success=True):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=self.backend,
            text=True,
            capture_output=True,
            check=False,
        )
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def current_revision(self, cur):
        cur.execute("SELECT version_num FROM alembic_version")
        return cur.fetchone()[0]

    def head_revision(self):
        result = self.alembic("heads")
        heads = [
            line.split()[0]
            for line in result.stdout.splitlines()
            if "(head)" in line
        ]
        self.assertEqual(len(heads), 1, result.stdout + result.stderr)
        return heads[0]

    def column_exists(self, cur, table, column):
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s AND column_name=%s)",
            (table, column),
        )
        return cur.fetchone()[0]

    def constraint_exists(self, cur, name):
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_constraint WHERE conname=%s)", (name,))
        return cur.fetchone()[0]

    def source_legacy(self, cur, suffix):
        cur.execute(
            "INSERT INTO sources(source_name,source_type) "
            "VALUES(%s,'scientific') RETURNING id",
            (f"Legacy source {suffix}",),
        )
        return cur.fetchone()[0]

    def source_hardened(self, cur, suffix):
        cur.execute(
            "INSERT INTO sources(source_key,source_name,source_type) "
            "VALUES(%s,%s,'scientific') RETURNING id",
            (f"safety_source_{suffix}", f"Safety source {suffix}"),
        )
        return cur.fetchone()[0]

    def dataset(self, cur, source_id, suffix):
        cur.execute(
            "INSERT INTO source_datasets(source_id,dataset_name,dataset_key) "
            "VALUES(%s,%s,%s) RETURNING id",
            (source_id, f"Safety dataset {suffix}", f"safety_dataset_{suffix}"),
        )
        return cur.fetchone()[0]

    def release_legacy(self, cur, dataset_id, suffix):
        cur.execute(
            "INSERT INTO source_dataset_releases(dataset_id,version_label) "
            "VALUES(%s,%s) RETURNING id",
            (dataset_id, f"Legacy release {suffix}"),
        )
        return cur.fetchone()[0]

    def release_hardened(self, cur, dataset_id, suffix, key=None):
        cur.execute(
            "INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) "
            "VALUES(%s,%s,%s) RETURNING id",
            (dataset_id, key or f"safety_release_{suffix}", f"Safety release {suffix}"),
        )
        return cur.fetchone()[0]

    def cleanup_source_tree(self, revision, source_id, dataset_id=None, release_id=None):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                if release_id is not None:
                    cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                if dataset_id is not None:
                    cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_0007_safe_synthetic_source_downgrade(self):
        self.alembic("downgrade", "0006_mapping_integrity_hardening")
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                source_id = self.source_legacy(cur, suffix)
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "0007_source_identity_hardening")
        self.alembic("downgrade", "0006_mapping_integrity_hardening")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertEqual(self.current_revision(cur), "0006_mapping_integrity_hardening")
                self.assertFalse(self.column_exists(cur, "sources", "source_key"))
                cur.execute("SELECT count(*) FROM sources WHERE id=%s", (source_id,))
                self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def assert_0007_rejected(self, source_key):
        self.alembic("downgrade", "0006_mapping_integrity_hardening")
        self.alembic("upgrade", "0007_source_identity_hardening")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sources(source_key,source_name,source_type) "
                    "VALUES(%s,'Unsafe source','scientific') RETURNING id",
                    (source_key,),
                )
                source_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()
        result = self.alembic("downgrade", "0006_mapping_integrity_hardening", expect_success=False)
        self.assertIn("Cannot downgrade 0007", result.stdout + result.stderr)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertEqual(self.current_revision(cur), "0007_source_identity_hardening")
                self.assertTrue(self.column_exists(cur, "sources", "source_key"))
                self.assertTrue(self.constraint_exists(cur, "uq_sources_source_key"))
                self.assertTrue(self.constraint_exists(cur, "ck_sources_source_key_format"))
                cur.execute("SELECT source_key FROM sources WHERE id=%s", (source_id,))
                self.assertEqual(cur.fetchone()[0], source_key)
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_0007_real_source_identity_rejects_downgrade(self):
        self.assert_0007_rejected("efsa")

    def test_0007_altered_synthetic_identity_rejects_downgrade(self):
        self.assert_0007_rejected("legacy_source_0")

    def test_0008_safe_synthetic_release_without_artifacts(self):
        self.alembic("downgrade", "0007_source_identity_hardening")
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                source_id = self.source_hardened(cur, suffix)
                dataset_id = self.dataset(cur, source_id, suffix)
                release_id = self.release_legacy(cur, dataset_id, suffix)
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "0008_release_artifact_integrity")
        self.alembic("downgrade", "0007_source_identity_hardening")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertFalse(self.column_exists(cur, "source_dataset_releases", "external_release_key"))
                cur.execute("SELECT count(*) FROM source_dataset_releases WHERE id=%s", (release_id,))
                self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_0008_artifact_rejects_downgrade_atomically(self):
        self.alembic("downgrade", "0007_source_identity_hardening")
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                source_id = self.source_hardened(cur, suffix)
                dataset_id = self.dataset(cur, source_id, suffix)
                release_id = self.release_legacy(cur, dataset_id, suffix)
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "0008_release_artifact_integrity")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO storage_objects(storage_provider,bucket,object_key) "
                    "VALUES('test','safety',%s) RETURNING id",
                    (f"artifact/{suffix}",),
                )
                storage_id = cur.fetchone()[0]
                cur.execute(
                    """INSERT INTO scientific_release_artifacts(
                        release_id,storage_object_id,artifact_key,artifact_role,
                        raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at)
                    VALUES(%s,%s,'primary','primary','sha256',%s,1,NOW()) RETURNING id""",
                    (release_id, storage_id, "a" * 64),
                )
                artifact_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()
        result = self.alembic("downgrade", "0007_source_identity_hardening", expect_success=False)
        self.assertIn("scientific_release_artifacts contains data", result.stdout + result.stderr)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertEqual(self.current_revision(cur), "0008_release_artifact_integrity")
                self.assertEqual(cur.execute("SELECT 1"), None)
                self.assertTrue(self.column_exists(cur, "source_dataset_releases", "external_release_key"))
                self.assertTrue(self.constraint_exists(cur, "uq_scientific_release_artifacts_key"))
                cur.execute("SELECT release_id,storage_object_id FROM scientific_release_artifacts WHERE id=%s", (artifact_id,))
                self.assertEqual(cur.fetchone(), (release_id, storage_id))
                cur.execute("SELECT external_release_key FROM source_dataset_releases WHERE id=%s", (release_id,))
                self.assertEqual(cur.fetchone()[0], f"legacy_release_{release_id}")
                cur.execute("SELECT count(*) FROM storage_objects WHERE id=%s", (storage_id,))
                self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM scientific_release_artifacts WHERE id=%s", (artifact_id,))
                cur.execute("DELETE FROM storage_objects WHERE id=%s", (storage_id,))
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_0008_real_release_identity_rejects_downgrade_atomically(self):
        self.alembic("downgrade", "0008_release_artifact_integrity")
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                source_id = self.source_hardened(cur, suffix)
                dataset_id = self.dataset(cur, source_id, suffix)
                release_id = self.release_hardened(cur, dataset_id, suffix, "release_2026_q1")
            conn.commit()
        finally:
            conn.close()
        result = self.alembic("downgrade", "0007_source_identity_hardening", expect_success=False)
        self.assertIn("external_release_key contains non-legacy identities", result.stdout + result.stderr)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertEqual(self.current_revision(cur), "0008_release_artifact_integrity")
                self.assertTrue(self.column_exists(cur, "source_dataset_releases", "external_release_key"))
                self.assertTrue(self.constraint_exists(cur, "uq_source_dataset_releases_external_key"))
                cur.execute("SELECT external_release_key FROM source_dataset_releases WHERE id=%s", (release_id,))
                self.assertEqual(cur.fetchone()[0], "release_2026_q1")
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_0009_safe_empty_run_table_downgrade(self):
        self.alembic("downgrade", "0008_release_artifact_integrity")
        self.alembic("upgrade", "0009_scientific_ingestion_runs")
        self.alembic("downgrade", "0008_release_artifact_integrity")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertEqual(self.current_revision(cur), "0008_release_artifact_integrity")
                cur.execute("SELECT to_regclass('scientific_ingestion_runs')")
                self.assertIsNone(cur.fetchone()[0])
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_0009_populated_run_rejects_downgrade_atomically(self):
        self.alembic("downgrade", "0008_release_artifact_integrity")
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                source_id = self.source_hardened(cur, suffix)
                dataset_id = self.dataset(cur, source_id, suffix)
                release_id = self.release_hardened(cur, dataset_id, suffix)
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "0009_scientific_ingestion_runs")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO scientific_ingestion_runs(
                        release_id,run_key,importer_name,importer_version,source_adapter_version,
                        acquisition_version,parser_version,normalization_schema_version,
                        artifact_manifest_algorithm,artifact_manifest_fingerprint)
                    VALUES(%s,%s,'safety','1','1','1','1','1','sha256',%s) RETURNING id""",
                    (release_id, str(uuid.uuid4()), "b" * 64),
                )
                run_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()
        result = self.alembic("downgrade", "0008_release_artifact_integrity", expect_success=False)
        self.assertIn("scientific_ingestion_runs contains non-representable data", result.stdout + result.stderr)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertEqual(self.current_revision(cur), "0009_scientific_ingestion_runs")
                cur.execute("SELECT to_regclass('scientific_ingestion_runs')")
                self.assertEqual(cur.fetchone()[0], "scientific_ingestion_runs")
                self.assertTrue(self.constraint_exists(cur, "uq_scientific_ingestion_runs_run_key"))
                cur.execute("SELECT release_id FROM scientific_ingestion_runs WHERE id=%s", (run_id,))
                self.assertEqual(cur.fetchone()[0], release_id)
                cur.execute("SELECT count(*) FROM source_dataset_releases WHERE id=%s", (release_id,))
                self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM scientific_ingestion_runs WHERE id=%s", (run_id,))
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_0010_synthetic_run_is_removed_before_0009_downgrade(self):
        self.alembic("downgrade", "0009_scientific_ingestion_runs")
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                source_id = self.source_hardened(cur, suffix)
                dataset_id = self.dataset(cur, source_id, suffix)
                release_id = self.release_hardened(cur, dataset_id, suffix)
                cur.execute(
                    "INSERT INTO substances(preferred_name,normalized_name) VALUES(%s,%s) RETURNING id",
                    (f"Safety substance {suffix}", f"safety-substance-{suffix}"),
                )
                substance_id = cur.fetchone()[0]
                cur.execute(
                    """INSERT INTO scientific_assessments(
                        substance_id,source_dataset_release_id,assessment_type,assessment_version)
                    VALUES(%s,%s,'legacy','1') RETURNING id""",
                    (substance_id, release_id),
                )
                assessment_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "0010_assessment_finding_identity")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_ingestion_runs WHERE release_id=%s", (release_id,))
                self.assertEqual(cur.fetchone()[0], 1)
        finally:
            conn.close()
        self.alembic("downgrade", "0009_scientific_ingestion_runs")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_ingestion_runs")
                self.assertEqual(cur.fetchone()[0], 0)
        finally:
            conn.close()
        self.alembic("downgrade", "0008_release_artifact_integrity")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM scientific_assessments WHERE id=%s", (assessment_id,))
                cur.execute("DELETE FROM substances WHERE id=%s", (substance_id,))
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "head")

    def test_full_empty_phase_61_downgrade_and_reupgrade(self):
        expected_head = self.head_revision()
        self.alembic("downgrade", "0006_mapping_integrity_hardening")
        self.alembic("upgrade", "head")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                self.assertEqual(self.current_revision(cur), expected_head)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
