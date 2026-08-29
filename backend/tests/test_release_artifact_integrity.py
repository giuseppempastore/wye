import os
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

from app.db import get_connection


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0008")
class ReleaseArtifactIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection()
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT release_artifact_test")
        self.suffix = uuid.uuid4().hex

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT release_artifact_test")
            self.conn.commit()
        finally:
            self.cur.close()
            self.conn.close()

    def source(self):
        self.cur.execute(
            "INSERT INTO sources (source_key, source_name, source_type) "
            "VALUES (%s, %s, 'scientific') RETURNING id",
            (f"source_{self.suffix}", f"Source {self.suffix}"),
        )
        return self.cur.fetchone()[0]

    def dataset(self, source_id=None, key=None):
        source_id = source_id or self.source()
        key = key or f"dataset_{uuid.uuid4().hex}"
        self.cur.execute(
            "INSERT INTO source_datasets (source_id, dataset_name, dataset_key) "
            "VALUES (%s, %s, %s) RETURNING id",
            (source_id, f"Dataset {key}", key),
        )
        return self.cur.fetchone()[0]

    def release(self, dataset_id=None, external_key=None, version_label=None):
        dataset_id = dataset_id or self.dataset()
        external_key = external_key or f"release_{uuid.uuid4().hex}"
        version_label = version_label or f"Version {uuid.uuid4().hex}"
        self.cur.execute(
            "INSERT INTO source_dataset_releases "
            "(dataset_id, external_release_key, version_label) "
            "VALUES (%s, %s, %s) RETURNING id",
            (dataset_id, external_key, version_label),
        )
        return self.cur.fetchone()[0]

    def storage_object(self, checksum=None):
        checksum = checksum or uuid.uuid4().hex * 2
        self.cur.execute(
            "INSERT INTO storage_objects "
            "(storage_provider, bucket, object_key, checksum_algorithm, checksum_value) "
            "VALUES ('test', 'scientific', %s, 'sha256', %s) RETURNING id",
            (f"objects/{uuid.uuid4().hex}", checksum),
        )
        return self.cur.fetchone()[0]

    def artifact(self, release_id=None, storage_id=None, key="primary", **overrides):
        release_id = release_id or self.release()
        storage_id = storage_id or self.storage_object()
        values = {
            "role": "primary",
            "algorithm": "sha256",
            "checksum": "a" * 64,
            "byte_size": 42,
            "acquired_at": "2026-08-28T10:00:00+00:00",
            "validated_at": "2026-08-28T10:01:00+00:00",
            "provenance": Json({"transport": "test_fixture"}),
        }
        values.update(overrides)
        self.cur.execute(
            "INSERT INTO scientific_release_artifacts "
            "(release_id, storage_object_id, artifact_key, artifact_role, format, media_type, "
            "raw_checksum_algorithm, raw_checksum_value, byte_size, acquired_at, validated_at, provenance) "
            "VALUES (%s, %s, %s, %s, 'json', 'application/json', %s, %s, %s, %s, %s, %s) "
            "RETURNING id",
            (release_id, storage_id, key, values["role"], values["algorithm"],
             values["checksum"], values["byte_size"], values["acquired_at"],
             values["validated_at"], values["provenance"]),
        )
        return self.cur.fetchone()[0]

    def rollback_case(self):
        self.cur.execute("ROLLBACK TO SAVEPOINT release_artifact_test")
        self.cur.execute("SAVEPOINT release_artifact_test")

    def test_external_release_key_is_required_and_can_differ_from_label(self):
        dataset_id = self.dataset()
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO source_dataset_releases (dataset_id, version_label) VALUES (%s, 'v1')",
                (dataset_id,),
            )
        self.rollback_case()
        dataset_id = self.dataset()
        release_id = self.release(dataset_id, "machine_release_1", "Human Version 2026")
        self.cur.execute(
            "SELECT external_release_key, version_label, dataset_id "
            "FROM source_dataset_releases WHERE id=%s", (release_id,)
        )
        self.assertEqual(self.cur.fetchone(), ("machine_release_1", "Human Version 2026", dataset_id))

    def test_external_key_unique_within_dataset_but_reusable_across_datasets(self):
        source_id = self.source()
        first_dataset = self.dataset(source_id)
        second_dataset = self.dataset(source_id)
        self.release(first_dataset, "shared_release", "v1")
        with self.assertRaises(psycopg2.IntegrityError):
            self.release(first_dataset, "shared_release", "v2")
        self.rollback_case()
        source_id = self.source()
        first_dataset = self.dataset(source_id)
        second_dataset = self.dataset(source_id)
        self.release(first_dataset, "shared_release", "v1")
        self.release(second_dataset, "shared_release", "v1")

    def test_release_accepts_one_or_multiple_artifacts(self):
        release_id = self.release()
        first_storage = self.storage_object()
        second_storage = self.storage_object()
        self.artifact(release_id, first_storage, "primary")
        self.artifact(release_id, second_storage, "manifest", role="manifest")
        self.cur.execute(
            "SELECT count(DISTINCT storage_object_id) FROM scientific_release_artifacts "
            "WHERE release_id=%s", (release_id,)
        )
        self.assertEqual(self.cur.fetchone()[0], 2)

    def test_artifact_key_unique_within_release_but_reusable_across_releases(self):
        dataset_id = self.dataset()
        first_release = self.release(dataset_id, "release_one", "v1")
        second_release = self.release(dataset_id, "release_two", "v2")
        self.artifact(first_release, key="primary")
        with self.assertRaises(psycopg2.IntegrityError):
            self.artifact(first_release, key="primary")
        self.rollback_case()
        dataset_id = self.dataset()
        first_release = self.release(dataset_id, "release_one", "v1")
        second_release = self.release(dataset_id, "release_two", "v2")
        self.artifact(first_release, key="primary")
        self.artifact(second_release, key="primary")

    def test_release_and_storage_foreign_keys_are_enforced(self):
        storage_id = self.storage_object()
        with self.assertRaises(psycopg2.IntegrityError):
            self.artifact(9223372036854775807, storage_id)
        self.rollback_case()
        release_id = self.release()
        with self.assertRaises(psycopg2.IntegrityError):
            self.artifact(release_id, 9223372036854775807)

    def test_referenced_storage_object_delete_is_restricted(self):
        release_id = self.release()
        storage_id = self.storage_object()
        self.artifact(release_id, storage_id)
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("DELETE FROM storage_objects WHERE id=%s", (storage_id,))

    def test_byte_size_and_validation_time_are_checked(self):
        with self.assertRaises(psycopg2.IntegrityError):
            self.artifact(byte_size=-1)
        self.rollback_case()
        with self.assertRaises(psycopg2.IntegrityError):
            self.artifact(
                acquired_at="2026-08-28T10:00:00+00:00",
                validated_at="2026-08-28T09:59:59+00:00",
            )

    def test_raw_checksum_is_required_and_sha256_is_lowercase_hex(self):
        invalid_checksums = (
            (None, None),
            (None, "a" * 64),
            ("sha256", None),
            ("sha256", "A" * 64),
            ("sha256", "a" * 63),
        )
        for algorithm, checksum in invalid_checksums:
            with self.subTest(algorithm=algorithm, checksum=checksum):
                with self.assertRaises(psycopg2.IntegrityError):
                    self.artifact(algorithm=algorithm, checksum=checksum)
                self.rollback_case()
        self.artifact(algorithm="sha256", checksum="f" * 64)

    def test_artifact_key_and_role_use_the_generic_vocabulary(self):
        with self.assertRaises(psycopg2.IntegrityError):
            self.artifact(key="Invalid key")
        self.rollback_case()
        with self.assertRaises(psycopg2.IntegrityError):
            self.artifact(role="source_specific_role")
        self.rollback_case()
        roles = ("primary", "manifest", "metadata", "attachment", "archive", "other")
        release_id = self.release()
        for role in roles:
            self.artifact(release_id=release_id, key=f"role_{role}", role=role)

    def test_provenance_jsonb_is_persisted(self):
        artifact_id = self.artifact(provenance=Json({"request_id": "fixture-1", "attempt": 1}))
        self.cur.execute(
            "SELECT provenance FROM scientific_release_artifacts WHERE id=%s", (artifact_id,)
        )
        self.assertEqual(self.cur.fetchone()[0], {"request_id": "fixture-1", "attempt": 1})

    def test_same_raw_checksum_does_not_define_release_identity(self):
        dataset_id = self.dataset()
        first_release = self.release(dataset_id, "logical_release_a", "A")
        second_release = self.release(dataset_id, "logical_release_b", "B")
        checksum = "c" * 64
        self.artifact(first_release, self.storage_object(checksum), checksum=checksum)
        self.artifact(second_release, self.storage_object(checksum), checksum=checksum)
        self.cur.execute(
            "SELECT count(DISTINCT release_id) FROM scientific_release_artifacts "
            "WHERE raw_checksum_value=%s", (checksum,)
        )
        self.assertEqual(self.cur.fetchone()[0], 2)


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL for migration lifecycle tests",
)
class ReleaseArtifactMigrationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]

    def alembic(self, *args):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args], cwd=self.backend,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_0007_0008_0007_0008_lifecycle_and_release_backfill(self):
        suffix = uuid.uuid4().hex
        self.alembic("downgrade", "0007_source_identity_hardening")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sources (source_key, source_name, source_type) "
                    "VALUES (%s, 'Legacy release source', 'scientific') RETURNING id",
                    (f"legacy_release_source_{suffix}",),
                )
                source_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO source_datasets (source_id, dataset_name, dataset_key) "
                    "VALUES (%s, 'Legacy release dataset', %s) RETURNING id",
                    (source_id, f"legacy_release_dataset_{suffix}"),
                )
                dataset_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO source_dataset_releases (dataset_id, version_label) "
                    "VALUES (%s, 'Legacy label') RETURNING id", (dataset_id,)
                )
                release_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        expected_key = f"legacy_release_{release_id}"
        self.alembic("upgrade", "0008_release_artifact_integrity")
        self.assert_state(release_id, dataset_id, expected_key, True)
        self.alembic("downgrade", "0007_source_identity_hardening")
        self.assert_state(release_id, dataset_id, None, False)
        self.alembic("upgrade", "0008_release_artifact_integrity")
        self.assert_state(release_id, dataset_id, expected_key, True)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s", (release_id,))
                cur.execute("DELETE FROM source_datasets WHERE id=%s", (dataset_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()

        self.alembic("upgrade", "head")

    def assert_state(self, release_id, dataset_id, expected_key, artifact_table_exists):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.scientific_release_artifacts')")
                self.assertEqual(cur.fetchone()[0] is not None, artifact_table_exists)
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    "WHERE table_name='source_dataset_releases' "
                    "AND column_name='external_release_key')"
                )
                self.assertEqual(cur.fetchone()[0], artifact_table_exists)
                if artifact_table_exists:
                    cur.execute(
                        "SELECT external_release_key FROM source_dataset_releases WHERE id=%s",
                        (release_id,),
                    )
                    self.assertEqual(cur.fetchone()[0], expected_key)
                cur.execute(
                    "SELECT dataset_id FROM source_dataset_releases WHERE id=%s", (release_id,)
                )
                self.assertEqual(cur.fetchone()[0], dataset_id)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
