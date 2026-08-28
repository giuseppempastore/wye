import os
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

import psycopg2

from app.db import get_connection


@unittest.skipUnless(
    os.environ.get("WYE_TEST_DATABASE"),
    "requires WYE_TEST_DATABASE pointing to an isolated database migrated to 0006",
)
class MappingIntegrityHardeningTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection()
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT mapping_integrity_hardening_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT mapping_integrity_hardening_test")
            self.conn.commit()
        finally:
            self.cur.close()
            self.conn.close()

    def reset_after_error(self):
        self.conn.rollback()
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT mapping_integrity_hardening_test")

    def product(self):
        self.cur.execute(
            "INSERT INTO products (barcode, product_name, category) VALUES (%s, 'Phase 5.1', 'food') RETURNING id",
            (f"mapping-hardening-{uuid.uuid4().hex}",),
        )
        return self.cur.fetchone()[0]

    def extraction_item(self):
        self.cur.execute(
            "INSERT INTO product_label_documents (raw_text, source_type, document_type) "
            "VALUES ('cocoa', 'manual_input', 'other') RETURNING id"
        )
        document_id = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO label_extraction_runs "
            "(label_document_id, extraction_method, run_status, completed_at) "
            "VALUES (%s, 'manual', 'succeeded', NOW()) RETURNING id",
            (document_id,),
        )
        run_id = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO label_extraction_items (extraction_run_id, item_type, raw_text) "
            "VALUES (%s, 'ingredient', 'cocoa') RETURNING id",
            (run_id,),
        )
        return self.cur.fetchone()[0]

    def product_ingredient(self, product_id, item_id=None):
        self.cur.execute(
            "INSERT INTO product_ingredients "
            "(product_id, ingredient_id, label_extraction_item_id, raw_name, mapping_status) "
            "VALUES (%s, NULL, %s, 'cocoa', 'needs_review') RETURNING id",
            (product_id, item_id),
        )
        return self.cur.fetchone()[0]

    def review(self, product_ingredient_id, status="pending"):
        self.cur.execute(
            "INSERT INTO ingredient_mapping_reviews "
            "(product_ingredient_id, raw_text, review_status, requested_by_method) "
            "VALUES (%s, 'cocoa', %s, 'manual') RETURNING id",
            (product_ingredient_id, status),
        )
        return self.cur.fetchone()[0]

    def ingredient(self):
        self.cur.execute(
            "INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id",
            (f"ingredient-{uuid.uuid4().hex}",),
        )
        return self.cur.fetchone()[0]

    def test_extraction_item_materializes_at_most_once(self):
        product_id = self.product()
        item_id = self.extraction_item()
        self.product_ingredient(product_id, item_id)
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.product_ingredient(product_id, item_id)

    def test_multiple_legacy_null_extraction_items_are_allowed(self):
        product_id = self.product()
        self.product_ingredient(product_id)
        self.product_ingredient(product_id)

    def test_only_one_pending_review_per_product_ingredient(self):
        product_ingredient_id = self.product_ingredient(self.product())
        self.review(product_ingredient_id)
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.review(product_ingredient_id)

    def test_concluded_review_can_be_followed_by_pending_review(self):
        product_ingredient_id = self.product_ingredient(self.product())
        self.review(product_ingredient_id, "rejected")
        self.review(product_ingredient_id, "pending")

    def test_accepted_review_without_selected_candidate_is_rejected(self):
        self.review(self.product_ingredient(self.product()), "accepted")
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_accepted_review_with_multiple_selected_candidates_is_rejected(self):
        review_id = self.review(self.product_ingredient(self.product()), "accepted")
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates "
            "(review_id, ingredient_id, candidate_method, is_selected) "
            "VALUES (%s, %s, 'manual_review', TRUE)",
            (review_id, self.ingredient()),
        )
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO ingredient_mapping_review_candidates "
                "(review_id, ingredient_id, candidate_method, is_selected) "
                "VALUES (%s, %s, 'manual_review', TRUE)",
                (review_id, self.ingredient()),
            )

    def test_accepted_review_with_one_selected_candidate_is_allowed(self):
        review_id = self.review(self.product_ingredient(self.product()), "accepted")
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates "
            "(review_id, ingredient_id, candidate_method, is_selected) "
            "VALUES (%s, %s, 'manual_review', TRUE)",
            (review_id, self.ingredient()),
        )
        self.cur.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_candidates_reference_canonical_ingredients_not_substances(self):
        review_id = self.review(self.product_ingredient(self.product()), "pending")
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates "
            "(review_id, ingredient_id, candidate_method) VALUES (%s, %s, 'manual_review')",
            (review_id, self.ingredient()),
        )
        self.cur.execute(
            "INSERT INTO substances (preferred_name, normalized_name) VALUES (%s, %s) RETURNING id",
            (f"substance-{uuid.uuid4().hex}", f"substance-{uuid.uuid4().hex}"),
        )
        substance_id = self.cur.fetchone()[0]
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self.cur.execute(
                "INSERT INTO ingredient_mapping_review_candidates "
                "(review_id, substance_id, candidate_method) VALUES (%s, %s, 'manual_review')",
                (review_id, substance_id),
            )


@unittest.skipUnless(
    os.environ.get("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "set WYE_RUN_MIGRATION_LIFECYCLE_TESTS=1 only for an isolated PostgreSQL database",
)
class MappingIntegrityMigrationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]

    def alembic(self, *args):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=self.backend,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_revision_and_indexes(self, revision, indexes_present):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version")
                self.assertEqual(cur.fetchone()[0], revision)
                for index_name in (
                    "uq_product_ingredients_label_extraction_item",
                    "uq_mapping_reviews_pending_product_ingredient",
                ):
                    cur.execute("SELECT to_regclass(%s)", (f"public.{index_name}",))
                    self.assertEqual(cur.fetchone()[0] is not None, indexes_present)
        finally:
            conn.close()

    def test_upgrade_downgrade_reupgrade(self):
        self.alembic("downgrade", "0005_label_extraction_pipeline")
        self.assert_revision_and_indexes("0005_label_extraction_pipeline", False)
        self.alembic("upgrade", "0006_mapping_integrity_hardening")
        self.assert_revision_and_indexes("0006_mapping_integrity_hardening", True)
        self.alembic("downgrade", "0005_label_extraction_pipeline")
        self.assert_revision_and_indexes("0005_label_extraction_pipeline", False)
        self.alembic("upgrade", "0006_mapping_integrity_hardening")
        self.assert_revision_and_indexes("0006_mapping_integrity_hardening", True)


if __name__ == "__main__":
    unittest.main()
