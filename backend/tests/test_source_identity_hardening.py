import os
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

import psycopg2

from app.db import get_connection


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0007")
class SourceIdentityHardeningTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection()
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT source_identity_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT source_identity_test")
            self.conn.commit()
        finally:
            self.cur.close()
            self.conn.close()

    def insert_source(self, source_key, suffix=None):
        suffix = suffix or uuid.uuid4().hex
        self.cur.execute(
            "INSERT INTO sources (source_key, source_name, source_type, url) "
            "VALUES (%s, %s, 'scientific', %s) RETURNING id",
            (source_key, f"Source {suffix}", f"https://example.invalid/{suffix}"),
        )
        return self.cur.fetchone()[0]

    def test_source_key_is_required(self):
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO sources (source_name, source_type) "
                "VALUES ('Missing key', 'scientific')"
            )

    def test_source_key_has_database_unique_constraint(self):
        self.cur.execute(
            "SELECT count(*) FROM pg_constraint "
            "WHERE conrelid='sources'::regclass "
            "AND conname='uq_sources_source_key' AND contype='u'"
        )
        self.assertEqual(self.cur.fetchone()[0], 1)

    def test_duplicate_source_key_is_rejected(self):
        source_key = f"test_source_{uuid.uuid4().hex}"
        self.insert_source(source_key, "first")
        with self.assertRaises(psycopg2.IntegrityError):
            self.insert_source(source_key, "second")

    def test_source_key_format_is_enforced(self):
        invalid_keys = ("EFSA", "open-foodtox", "has space", "_leading", "trailing_", "")
        for invalid_key in invalid_keys:
            with self.subTest(source_key=invalid_key):
                self.cur.execute("SAVEPOINT invalid_source_key")
                with self.assertRaises(psycopg2.IntegrityError):
                    self.insert_source(invalid_key)
                self.cur.execute("ROLLBACK TO SAVEPOINT invalid_source_key")
        self.insert_source(f"valid_source_{uuid.uuid4().hex}")

    def test_name_and_url_can_change_without_changing_identity(self):
        source_key = f"stable_source_{uuid.uuid4().hex}"
        source_id = self.insert_source(source_key)
        self.cur.execute(
            "UPDATE sources SET source_name='Renamed source', url=%s WHERE id=%s",
            ("https://renamed.example.invalid", source_id),
        )
        self.cur.execute("SELECT source_key FROM sources WHERE id=%s", (source_id,))
        self.assertEqual(self.cur.fetchone()[0], source_key)

    def test_existing_dataset_foreign_key_still_works(self):
        source_id = self.insert_source(f"dataset_source_{uuid.uuid4().hex}")
        self.cur.execute(
            "INSERT INTO source_datasets (source_id, dataset_name, dataset_key) "
            "VALUES (%s, 'Identity test dataset', %s) RETURNING source_id",
            (source_id, f"dataset_{uuid.uuid4().hex}"),
        )
        self.assertEqual(self.cur.fetchone()[0], source_id)


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires an isolated PostgreSQL database for migration lifecycle tests",
)
class SourceIdentityMigrationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]

    def alembic(self, *args):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args], cwd=self.backend,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_0006_0007_0006_0007_lifecycle_and_legacy_backfill(self):
        suffix = uuid.uuid4().hex
        self.alembic("downgrade", "0006_mapping_integrity_hardening")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sources (source_name, source_type, url) "
                    "VALUES (%s, 'scientific', %s) RETURNING id",
                    (f"Legacy source {suffix}", f"https://legacy.invalid/{suffix}"),
                )
                source_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO source_datasets (source_id, dataset_name, dataset_key) "
                    "VALUES (%s, 'Legacy dataset', %s) RETURNING id",
                    (source_id, f"legacy_dataset_{suffix}"),
                )
                dataset_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        expected_key = f"legacy_source_{source_id}"
        self.alembic("upgrade", "0007_source_identity_hardening")
        self.assert_state(source_id, dataset_id, expected_key, True)
        self.alembic("downgrade", "0006_mapping_integrity_hardening")
        self.assert_state(source_id, dataset_id, None, False)
        self.alembic("upgrade", "0007_source_identity_hardening")
        self.assert_state(source_id, dataset_id, expected_key, True)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()

        self.alembic("upgrade", "head")

    def assert_state(self, source_id, dataset_id, expected_key, column_exists):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='sources' "
                    "AND column_name='source_key')"
                )
                self.assertEqual(cur.fetchone()[0], column_exists)
                if column_exists:
                    cur.execute("SELECT source_key FROM sources WHERE id=%s", (source_id,))
                    self.assertEqual(cur.fetchone()[0], expected_key)
                cur.execute("SELECT source_id FROM source_datasets WHERE id=%s", (dataset_id,))
                self.assertEqual(cur.fetchone()[0], source_id)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
