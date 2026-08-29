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


def create_ingredient(cur, suffix):
    cur.execute(
        "INSERT INTO ingredients(canonical_name) VALUES(%s) RETURNING id",
        (f"Scientific ingredient {suffix}",),
    )
    return cur.fetchone()[0]


def create_substance(cur, suffix):
    cur.execute(
        "INSERT INTO substances(preferred_name,normalized_name) VALUES(%s,%s) RETURNING id",
        (f"Scientific substance {suffix}", f"scientific-substance-{suffix}"),
    )
    return cur.fetchone()[0]


def create_scientific_context(cur, suffix):
    cur.execute(
        "INSERT INTO sources(source_key,source_name,source_type) "
        "VALUES(%s,%s,'scientific') RETURNING id",
        (f"bridge_source_{suffix}", f"Bridge source {suffix}"),
    )
    source_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO source_datasets(source_id,dataset_name,dataset_key) "
        "VALUES(%s,'Bridge dataset',%s) RETURNING id",
        (source_id, f"bridge_dataset_{suffix}"),
    )
    dataset_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) "
        "VALUES(%s,%s,'Bridge release') RETURNING id",
        (dataset_id, f"bridge_release_{suffix}"),
    )
    release_id = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO scientific_ingestion_runs(
            release_id,run_key,importer_name,importer_version,source_adapter_version,
            acquisition_version,parser_version,normalization_schema_version,
            artifact_manifest_algorithm,artifact_manifest_fingerprint)
        VALUES(%s,%s,'test','1','adapter-1','acquisition-1','parser-1',
            'normalization-1','sha256',%s) RETURNING id""",
        (release_id, str(uuid.uuid4()), "a" * 64),
    )
    run_id = cur.fetchone()[0]
    return source_id, dataset_id, release_id, run_id


def insert_relationship(
    cur,
    ingredient_id,
    substance_id,
    relationship_type="represents",
    mapping_method="legacy",
    mapping_status="legacy_unreviewed",
    confidence=None,
    release_id=None,
    run_id=None,
    provenance=None,
    valid_from=None,
    valid_to=None,
    reviewed_by=None,
    reviewed_at=None,
):
    cur.execute(
        """INSERT INTO ingredient_substances(
            ingredient_id,substance_id,relationship_type,mapping_method,mapping_status,
            mapping_confidence,source_dataset_release_id,ingestion_run_id,provenance,
            valid_from,valid_to,reviewed_by,reviewed_at)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (
            ingredient_id,
            substance_id,
            relationship_type,
            mapping_method,
            mapping_status,
            confidence,
            release_id,
            run_id,
            Json(provenance) if provenance is not None else None,
            valid_from,
            valid_to,
            reviewed_by,
            reviewed_at,
        ),
    )
    return cur.fetchone()[0]


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0012")
class IngredientSubstanceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection()
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT ingredient_substance_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT ingredient_substance_test")
            self.conn.commit()
        finally:
            self.cur.close()
            self.conn.close()

    def reset(self):
        self.cur.execute("ROLLBACK TO SAVEPOINT ingredient_substance_test")
        self.cur.execute("SAVEPOINT ingredient_substance_test")

    def pair(self):
        suffix = uuid.uuid4().hex
        return create_ingredient(self.cur, suffix), create_substance(self.cur, suffix)

    def test_temporal_integrity(self):
        ingredient, substance = self.pair()
        insert_relationship(self.cur, ingredient, substance)
        ingredient, substance = self.pair()
        insert_relationship(self.cur, ingredient, substance, valid_from="2024-01-01", valid_to="2024-02-01")
        ingredient, substance = self.pair()
        insert_relationship(self.cur, ingredient, substance, valid_from="2024-01-01", valid_to="2024-01-01")
        ingredient, substance = self.pair()
        with self.assertRaises(psycopg2.IntegrityError):
            insert_relationship(self.cur, ingredient, substance, valid_from="2024-02-01", valid_to="2024-01-01")

    def test_manual_review_and_status_invariants(self):
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="manual_review",
            mapping_status="accepted", reviewed_by="reviewer:test", reviewed_at="2025-01-01T00:00:00Z",
        )
        for status in ("accepted", "rejected", "ambiguous"):
            with self.subTest(status=status):
                ingredient, substance = self.pair()
                with self.assertRaises(psycopg2.IntegrityError):
                    insert_relationship(
                        self.cur, ingredient, substance, mapping_method="manual_review", mapping_status=status,
                    )
                self.reset()
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="manual_review", mapping_status="rejected",
            reviewed_at="2025-01-01T00:00:00Z", provenance={"decision": "rejected"},
        )
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="manual_review", mapping_status="ambiguous",
            reviewed_at="2025-01-01T00:00:00Z", provenance={"decision": "ambiguous"},
        )
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="manual_review", mapping_status="pending_review",
        )
        ingredient, substance = self.pair()
        insert_relationship(self.cur, ingredient, substance)

    def test_deterministic_and_dataset_provenance(self):
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="deterministic", mapping_status="accepted",
            provenance={"rule": "fixture_rule_v1"},
        )
        ingredient, substance = self.pair()
        with self.assertRaises(psycopg2.IntegrityError):
            insert_relationship(
                self.cur, ingredient, substance, mapping_method="deterministic", mapping_status="accepted",
            )
        self.reset()
        _, _, release_id, run_id = create_scientific_context(self.cur, uuid.uuid4().hex)
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="dataset", mapping_status="accepted",
            release_id=release_id,
        )
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="dataset", mapping_status="accepted",
            run_id=run_id,
        )
        ingredient, substance = self.pair()
        relationship_id = insert_relationship(
            self.cur, ingredient, substance, mapping_method="dataset", mapping_status="accepted",
            release_id=release_id, run_id=run_id, provenance={"fixture": True},
        )
        self.cur.execute(
            "SELECT source_dataset_release_id,ingestion_run_id,provenance "
            "FROM ingredient_substances WHERE id=%s", (relationship_id,),
        )
        release, run, provenance = self.cur.fetchone()
        self.assertEqual((release, run), (release_id, run_id))
        self.assertEqual(provenance, {"fixture": True})
        ingredient, substance = self.pair()
        with self.assertRaises(psycopg2.IntegrityError):
            insert_relationship(
                self.cur, ingredient, substance, mapping_method="dataset", mapping_status="accepted",
            )

    def test_ingestion_run_fk_and_delete_are_restricted(self):
        _, _, release_id, run_id = create_scientific_context(self.cur, uuid.uuid4().hex)
        ingredient, substance = self.pair()
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="dataset", mapping_status="accepted",
            release_id=release_id, run_id=run_id,
        )
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("DELETE FROM scientific_ingestion_runs WHERE id=%s", (run_id,))
        self.reset()
        ingredient, substance = self.pair()
        with self.assertRaises(psycopg2.IntegrityError):
            insert_relationship(
                self.cur, ingredient, substance, mapping_method="dataset", mapping_status="accepted",
                run_id=9223372036854775807,
            )

    def test_many_to_many_and_relationship_vocabulary(self):
        suffix = uuid.uuid4().hex
        ingredient_one = create_ingredient(self.cur, suffix + "a")
        ingredient_two = create_ingredient(self.cur, suffix + "b")
        substance_one = create_substance(self.cur, suffix + "a")
        substance_two = create_substance(self.cur, suffix + "b")
        insert_relationship(self.cur, ingredient_one, substance_one, "represents")
        insert_relationship(self.cur, ingredient_one, substance_two, "contains")
        insert_relationship(self.cur, ingredient_two, substance_one, "contains")
        for relationship_type in ("derived_from", "mixture_component", "equivalent_to"):
            insert_relationship(self.cur, ingredient_two, substance_two, relationship_type)
        self.cur.execute(
            "SELECT count(DISTINCT substance_id) FROM ingredient_substances WHERE ingredient_id=%s",
            (ingredient_one,),
        )
        self.assertEqual(self.cur.fetchone()[0], 2)
        self.cur.execute(
            "SELECT count(DISTINCT ingredient_id) FROM ingredient_substances WHERE substance_id=%s",
            (substance_one,),
        )
        self.assertEqual(self.cur.fetchone()[0], 2)

    def test_current_unique_rejects_duplicate_relationship(self):
        setup = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with setup.cursor() as cur:
                ingredient = create_ingredient(cur, suffix)
                substance = create_substance(cur, suffix)
            setup.commit()
        finally:
            setup.close()
        barrier = threading.Barrier(2)
        results = []
        unexpected = []

        def worker():
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    barrier.wait(timeout=10)
                    insert_relationship(
                        cur, ingredient, substance, mapping_method="deterministic",
                        mapping_status="accepted", provenance={"rule": "concurrency_fixture_v1"},
                        valid_from="2025-01-01",
                    )
                conn.commit()
                results.append("committed")
            except psycopg2.IntegrityError:
                conn.rollback()
                results.append("integrity_error")
            except Exception as exc:
                conn.rollback()
                unexpected.append(repr(exc))
            finally:
                conn.close()

        first = threading.Thread(target=worker)
        second = threading.Thread(target=worker)
        first.start()
        second.start()
        first.join(15)
        second.join(15)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(unexpected, [])
        self.assertCountEqual(results, ["committed", "integrity_error"])
        cleanup = get_connection()
        try:
            with cleanup.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FROM ingredient_substances WHERE ingredient_id=%s AND substance_id=%s",
                    (ingredient, substance),
                )
                self.assertEqual(cur.fetchone()[0], 1)
                cur.execute("DELETE FROM ingredient_substances WHERE ingredient_id=%s", (ingredient,))
                cur.execute("DELETE FROM ingredients WHERE id=%s", (ingredient,))
                cur.execute("DELETE FROM substances WHERE id=%s", (substance,))
            cleanup.commit()
        finally:
            cleanup.close()

    def test_full_scientific_provenance_query_path(self):
        suffix = uuid.uuid4().hex
        source_id, _, release_id, run_id = create_scientific_context(self.cur, suffix)
        ingredient = create_ingredient(self.cur, suffix)
        substance = create_substance(self.cur, suffix)
        insert_relationship(
            self.cur, ingredient, substance, mapping_method="dataset", mapping_status="accepted",
            release_id=release_id, run_id=run_id, provenance={"fixture": "query_path"},
        )
        self.cur.execute(
            """INSERT INTO scientific_assessments(
                substance_id,source_dataset_release_id,ingestion_run_id,source_record_key,
                assessment_type,assessment_version)
            VALUES(%s,%s,%s,'query-path-assessment','generic','1') RETURNING id""",
            (substance, release_id, run_id),
        )
        assessment_id = self.cur.fetchone()[0]
        self.cur.execute(
            """SELECT i.id,s.id,a.id,r.id,rel.id,d.id,src.id,src.source_key
            FROM ingredients i
            JOIN ingredient_substances bridge ON bridge.ingredient_id=i.id
                AND bridge.mapping_status='accepted'
            JOIN substances s ON s.id=bridge.substance_id
            JOIN scientific_assessments a ON a.substance_id=s.id
            JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id
            JOIN source_dataset_releases rel ON rel.id=r.release_id
            JOIN source_datasets d ON d.id=rel.dataset_id
            JOIN sources src ON src.id=d.source_id
            WHERE i.id=%s AND a.id=%s""",
            (ingredient, assessment_id),
        )
        row = self.cur.fetchone()
        self.assertEqual(row[:7], (ingredient, substance, assessment_id, run_id, release_id, row[5], source_id))
        self.assertEqual(row[7], f"bridge_source_{suffix}")


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL",
)
class IngredientSubstanceMigrationLifecycleTests(unittest.TestCase):
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

    def test_downgrade_refuses_unrepresentable_audit_data(self):
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version")
                starting_revision = cur.fetchone()[0]
                ingredient = create_ingredient(cur, suffix)
                substance = create_substance(cur, suffix)
                relationship = insert_relationship(
                    cur, ingredient, substance, mapping_method="manual_review", mapping_status="accepted",
                    reviewed_at="2025-01-01T00:00:00Z",
                )
            conn.commit()
        finally:
            conn.close()
        self.alembic("downgrade", "0011_substance_identity_registry", expect_success=False)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version")
                self.assertEqual(cur.fetchone()[0], starting_revision)
                cur.execute("DELETE FROM ingredient_substances WHERE id=%s", (relationship,))
                cur.execute("DELETE FROM ingredients WHERE id=%s", (ingredient,))
                cur.execute("DELETE FROM substances WHERE id=%s", (substance,))
            conn.commit()
        finally:
            conn.close()

    def test_legacy_relationship_and_0011_0012_0011_0012_lifecycle(self):
        self.alembic("downgrade", "0011_substance_identity_registry")
        conn = get_connection()
        suffix = uuid.uuid4().hex
        try:
            with conn.cursor() as cur:
                ingredient = create_ingredient(cur, suffix)
                substance = create_substance(cur, suffix)
                cur.execute(
                    """INSERT INTO ingredient_substances(
                        ingredient_id,substance_id,relationship_type,mapping_method,mapping_status,
                        provenance,valid_from,valid_to)
                    VALUES(%s,%s,'represents','legacy','legacy_unreviewed',%s,'2020-01-01',NULL)
                    RETURNING id""",
                    (ingredient, substance, Json({"legacy": True})),
                )
                relationship = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()
        self.alembic("upgrade", "0012_ingredient_substance_guard")
        self.assert_legacy(relationship, True)
        self.alembic("downgrade", "0011_substance_identity_registry")
        self.assert_legacy(relationship, False)
        self.alembic("upgrade", "0012_ingredient_substance_guard")
        self.assert_legacy(relationship, True)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ingredient_substances WHERE id=%s", (relationship,))
                cur.execute("DELETE FROM ingredients WHERE id=%s", (ingredient,))
                cur.execute("DELETE FROM substances WHERE id=%s", (substance,))
            conn.commit()
        finally:
            conn.close()

    def assert_legacy(self, relationship, hardened):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
                    "WHERE table_name='ingredient_substances' AND column_name='ingestion_run_id')"
                )
                self.assertEqual(cur.fetchone()[0], hardened)
                if hardened:
                    cur.execute(
                        "SELECT indexname FROM pg_indexes WHERE tablename='ingredient_substances'"
                    )
                    indexes = {row[0] for row in cur.fetchall()}
                    self.assertTrue({
                        "idx_ingredient_substances_ingredient_status",
                        "idx_ingredient_substances_substance_status",
                        "idx_ingredient_substances_ingestion_run",
                    }.issubset(indexes))
                    cur.execute(
                        "SELECT mapping_method,mapping_status,reviewed_by,reviewed_at,ingestion_run_id,provenance "
                        "FROM ingredient_substances WHERE id=%s", (relationship,),
                    )
                    self.assertEqual(
                        cur.fetchone(),
                        ("legacy", "legacy_unreviewed", None, None, None, {"legacy": True}),
                    )
                else:
                    cur.execute("SELECT count(*) FROM ingredient_substances WHERE id=%s", (relationship,))
                    self.assertEqual(cur.fetchone()[0], 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
