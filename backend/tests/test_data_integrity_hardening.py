import os
import subprocess
import sys
import threading
import unittest
import uuid
from pathlib import Path

import psycopg2

from app.db import get_connection


@unittest.skipUnless(
    os.environ.get("WYE_TEST_DATABASE"),
    "requires WYE_TEST_DATABASE pointing to an isolated migrated PostgreSQL database",
)
class DataIntegrityHardeningTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection()
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT data_integrity_hardening_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT data_integrity_hardening_test")
            self.conn.commit()
        finally:
            self.cur.close()
            self.conn.close()

    def product(self, suffix=None):
        suffix = suffix or uuid.uuid4().hex
        self.cur.execute(
            "INSERT INTO products (barcode, product_name, category) VALUES (%s, %s, %s) RETURNING id",
            (f"hardening-{suffix}", "Hardening test", "food"),
        )
        return self.cur.fetchone()[0]

    def image(self, product_id, image_type="product_front", suffix=None, **overrides):
        suffix = suffix or uuid.uuid4().hex
        values = {
            "status": "active",
            "is_current": True,
            "superseded_at": None,
            "superseded_by_image_id": None,
        }
        values.update(overrides)
        self.cur.execute(
            """
            INSERT INTO product_images
                (product_id, image_type, storage_reference, mime_type, checksum, source,
                 status, is_current, superseded_at, superseded_by_image_id)
            VALUES (%s, %s, %s, 'image/jpeg', %s, 'user_submission', %s, %s, %s, %s)
            RETURNING id
            """,
            (
                product_id, image_type, f"legacy/{suffix}", "a" * 64,
                values["status"], values["is_current"], values["superseded_at"],
                values["superseded_by_image_id"],
            ),
        )
        return self.cur.fetchone()[0]

    def product_ingredient_and_review(self, product_id, status="pending"):
        self.cur.execute(
            """
            INSERT INTO product_ingredients (product_id, ingredient_id, raw_name, mapping_status)
            VALUES (%s, NULL, 'Kakaopulver', 'needs_review') RETURNING id
            """,
            (product_id,),
        )
        product_ingredient_id = self.cur.fetchone()[0]
        self.cur.execute(
            """
            INSERT INTO ingredient_mapping_reviews
                (product_ingredient_id, raw_text, review_status, requested_by_method)
            VALUES (%s, 'Kakaopulver', %s, 'manual') RETURNING id
            """,
            (product_ingredient_id, status),
        )
        return product_ingredient_id, self.cur.fetchone()[0]

    def ingredient(self, name=None):
        name = name or f"ingredient-{uuid.uuid4().hex}"
        self.cur.execute("INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id", (name,))
        return self.cur.fetchone()[0]

    def substance(self):
        suffix = uuid.uuid4().hex
        self.cur.execute(
            "INSERT INTO substances (preferred_name, normalized_name) VALUES (%s, %s) RETURNING id",
            (f"substance-{suffix}", f"substance-{suffix}"),
        )
        return self.cur.fetchone()[0]

    def assert_deferred_violation(self):
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.conn.rollback()
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT data_integrity_hardening_test")

    def test_image_derived_document_must_derive_product_from_image(self):
        product_id = self.product()
        image_id = self.image(product_id)
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO product_label_documents (product_id, product_image_id, raw_text, source_type) VALUES (%s, %s, 'x', 'image_derived')",
                (product_id, image_id),
            )
        self.conn.rollback()
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT data_integrity_hardening_test")
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("INSERT INTO product_label_documents (raw_text, source_type) VALUES ('x', 'image_derived')")

    def test_mapping_candidates_are_canonical_ingredients_only(self):
        product_id = self.product()
        _, review_id = self.product_ingredient_and_review(product_id)
        ingredient_id = self.ingredient()
        substance_id = self.substance()
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO ingredient_mapping_review_candidates (review_id, ingredient_id, substance_id, candidate_method) VALUES (%s, %s, %s, 'manual_review')",
                (review_id, ingredient_id, substance_id),
            )
        self.conn.rollback()
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT data_integrity_hardening_test")
        product_id = self.product()
        _, review_id = self.product_ingredient_and_review(product_id)
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("INSERT INTO ingredient_mapping_review_candidates (review_id, candidate_method) VALUES (%s, 'manual_review')", (review_id,))

    def test_accepted_review_requires_exactly_one_selected_candidate(self):
        product_id = self.product()
        _, review_id = self.product_ingredient_and_review(product_id, "accepted")
        self.assert_deferred_violation()

        product_id = self.product()
        _, review_id = self.product_ingredient_and_review(product_id, "accepted")
        first = self.ingredient()
        second = self.ingredient()
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates (review_id, ingredient_id, candidate_method, is_selected) VALUES (%s, %s, 'manual_review', TRUE)",
            (review_id, first),
        )
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO ingredient_mapping_review_candidates (review_id, ingredient_id, candidate_method, is_selected) VALUES (%s, %s, 'manual_review', TRUE)",
                (review_id, second),
            )
        self.conn.rollback()
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT data_integrity_hardening_test")

        product_id = self.product()
        _, review_id = self.product_ingredient_and_review(product_id, "accepted")
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates (review_id, ingredient_id, candidate_method, is_selected) VALUES (%s, %s, 'manual_review', TRUE)",
            (review_id, self.ingredient()),
        )
        self.cur.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_moving_selected_candidate_revalidates_previous_review(self):
        first_product = self.product()
        _, accepted_review = self.product_ingredient_and_review(first_product, "accepted")
        second_product = self.product()
        _, pending_review = self.product_ingredient_and_review(second_product, "pending")
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates "
            "(review_id, ingredient_id, candidate_method, is_selected) "
            "VALUES (%s, %s, 'manual_review', TRUE) RETURNING id",
            (accepted_review, self.ingredient()),
        )
        candidate_id = self.cur.fetchone()[0]
        self.cur.execute(
            "UPDATE ingredient_mapping_review_candidates SET review_id=%s WHERE id=%s",
            (pending_review, candidate_id),
        )
        self.assert_deferred_violation()

    def test_image_supersession_rejects_self_other_product_type_and_cycles(self):
        product_id = self.product()
        image_id = self.image(product_id)
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "UPDATE product_images SET status = 'superseded', is_current = FALSE, superseded_at = NOW(), superseded_by_image_id = id WHERE id = %s",
                (image_id,),
            )
        self.conn.rollback()
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT data_integrity_hardening_test")

        first_product = self.product()
        second_product = self.product()
        first = self.image(first_product)
        second = self.image(second_product)
        self.cur.execute(
            "UPDATE product_images SET status = 'superseded', is_current = FALSE, superseded_at = NOW(), superseded_by_image_id = %s WHERE id = %s",
            (second, first),
        )
        self.assert_deferred_violation()

        product_id = self.product()
        front = self.image(product_id, "product_front")
        nutrition = self.image(product_id, "nutrition")
        self.cur.execute(
            "UPDATE product_images SET status = 'superseded', is_current = FALSE, superseded_at = NOW(), superseded_by_image_id = %s WHERE id = %s",
            (nutrition, front),
        )
        self.assert_deferred_violation()

        product_id = self.product()
        a = self.image(product_id, suffix="cycle-a")
        c = self.image(product_id, suffix="cycle-c", status="rejected", is_current=False)
        # A second current image would violate the partial unique index. The
        # initially rejected successor becomes superseded when closing the cycle.
        self.cur.execute(
            "UPDATE product_images SET status = 'superseded', is_current = FALSE, superseded_at = NOW(), superseded_by_image_id = %s WHERE id = %s",
            (c, a),
        )
        self.cur.execute(
            "UPDATE product_images SET status = 'superseded', is_current = FALSE, superseded_at = NOW(), superseded_by_image_id = %s WHERE id = %s",
            (a, c),
        )
        self.assert_deferred_violation()

    def test_valid_image_document_and_mapping_candidate(self):
        product_id = self.product()
        image_id = self.image(product_id)
        self.cur.execute(
            "INSERT INTO product_label_documents "
            "(product_image_id, raw_text, source_type) VALUES (%s, 'x', 'image_derived')",
            (image_id,),
        )
        _, review_id = self.product_ingredient_and_review(product_id)
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates "
            "(review_id, ingredient_id, candidate_method) VALUES (%s, %s, 'manual_review')",
            (review_id, self.ingredient()),
        )

    def test_image_version_state_and_valid_chain(self):
        invalid_states = (
            ("superseded", True, None, None),
            ("active", True, "now", 1),
            ("rejected", True, None, None),
        )
        for status, is_current, superseded_at, successor in invalid_states:
            product_id = self.product()
            with self.assertRaises(psycopg2.IntegrityError):
                self.cur.execute(
                    """
                    INSERT INTO product_images
                        (product_id, image_type, storage_reference, mime_type, checksum,
                         source, status, is_current, superseded_at, superseded_by_image_id)
                    VALUES (%s, 'product_front', %s, 'image/jpeg', %s,
                            'user_submission', %s, %s,
                            CASE WHEN %s IS NULL THEN NULL ELSE NOW() END, %s)
                    """,
                    (
                        product_id, f"invalid/{uuid.uuid4().hex}", "a" * 64,
                        status, is_current, superseded_at, successor,
                    ),
                )
            self.conn.rollback()
            self.cur = self.conn.cursor()
            self.cur.execute("SAVEPOINT data_integrity_hardening_test")

        product_id = self.product()
        c = self.image(product_id, suffix="valid-c")
        b = self.image(product_id, suffix="valid-b", status="rejected", is_current=False)
        a = self.image(product_id, suffix="valid-a", status="rejected", is_current=False)
        self.cur.execute(
            "UPDATE product_images SET status='superseded', superseded_at=NOW(), "
            "superseded_by_image_id=%s WHERE id=%s",
            (c, b),
        )
        self.cur.execute(
            "UPDATE product_images SET status='superseded', superseded_at=NOW(), "
            "superseded_by_image_id=%s WHERE id=%s",
            (b, a),
        )
        self.cur.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_concurrent_replacements_leave_one_current_image(self):
        setup_conn = get_connection()
        setup_cur = setup_conn.cursor()
        suffix = uuid.uuid4().hex
        setup_cur.execute(
            "INSERT INTO products (barcode, product_name, category) "
            "VALUES (%s, 'Concurrent image test', 'food') RETURNING id",
            (f"hardening-concurrent-{suffix}",),
        )
        product_id = setup_cur.fetchone()[0]
        setup_cur.execute(
            "INSERT INTO product_images "
            "(product_id, image_type, storage_reference, mime_type, checksum, source, status) "
            "VALUES (%s, 'product_front', %s, 'image/jpeg', %s, "
            "'user_submission', 'active') RETURNING id",
            (product_id, f"concurrent/{suffix}/original", "a" * 64),
        )
        original_id = setup_cur.fetchone()[0]
        setup_conn.commit()
        setup_cur.close()
        setup_conn.close()

        first_locked = threading.Event()
        second_ready = threading.Event()
        release_first = threading.Event()
        results = []
        unexpected_errors = []

        def replace_image(label, first_worker):
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                cur.execute(
                    "INSERT INTO product_images "
                    "(product_id, image_type, storage_reference, mime_type, checksum, source, "
                    "status, is_current) VALUES (%s, 'product_front', %s, 'image/jpeg', %s, "
                    "'user_submission', 'rejected', FALSE) RETURNING id",
                    (product_id, f"concurrent/{suffix}/{label}", label * 64),
                )
                replacement_id = cur.fetchone()[0]
                if first_worker:
                    cur.execute(
                        "UPDATE product_images SET status='superseded', is_current=FALSE, "
                        "superseded_at=NOW(), superseded_by_image_id=%s WHERE id=%s",
                        (replacement_id, original_id),
                    )
                    first_locked.set()
                    if not release_first.wait(10):
                        raise RuntimeError("concurrency test timed out")
                else:
                    if not first_locked.wait(10):
                        raise RuntimeError("concurrency test timed out")
                    second_ready.set()
                    cur.execute(
                        "UPDATE product_images SET status='superseded', is_current=FALSE, "
                        "superseded_at=NOW(), superseded_by_image_id=%s WHERE id=%s",
                        (replacement_id, original_id),
                    )
                cur.execute(
                    "UPDATE product_images SET status='active', is_current=TRUE WHERE id=%s",
                    (replacement_id,),
                )
                conn.commit()
                results.append("committed")
            except psycopg2.IntegrityError:
                conn.rollback()
                results.append("integrity_error")
            except Exception as exc:
                conn.rollback()
                unexpected_errors.append(repr(exc))
            finally:
                cur.close()
                conn.close()

        first = threading.Thread(target=replace_image, args=("b", True))
        second = threading.Thread(target=replace_image, args=("c", False))
        first.start()
        self.assertTrue(first_locked.wait(10))
        second.start()
        self.assertTrue(second_ready.wait(10))
        release_first.set()
        first.join(10)
        second.join(10)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(unexpected_errors, [])
        self.assertCountEqual(results, ["committed", "integrity_error"])

        check_conn = get_connection()
        check_cur = check_conn.cursor()
        check_cur.execute(
            "SELECT count(*) FROM product_images WHERE product_id=%s AND image_type='product_front' "
            "AND is_current=TRUE AND status IN ('pending_review', 'active', 'verified')",
            (product_id,),
        )
        self.assertEqual(check_cur.fetchone()[0], 1)
        check_cur.execute(
            "SELECT id FROM product_images WHERE product_id=%s AND is_current=FALSE",
            (product_id,),
        )
        for (image_id,) in check_cur.fetchall():
            check_cur.execute("DELETE FROM product_images WHERE id=%s", (image_id,))
        check_cur.execute("DELETE FROM product_images WHERE product_id=%s", (product_id,))
        check_cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
        check_conn.commit()
        check_cur.close()
        check_conn.close()

    def test_storage_object_identity_and_reuse(self):
        self.cur.execute(
            """
            INSERT INTO storage_objects (storage_provider, bucket, object_key, checksum_algorithm, checksum_value)
            VALUES ('test', 'wye', 'objects/a', 'sha256', %s) RETURNING id
            """,
            ("a" * 64,),
        )
        storage_id = self.cur.fetchone()[0]
        first_product = self.product()
        second_product = self.product()
        self.cur.execute(
            "INSERT INTO product_images (product_id, image_type, storage_object_id, mime_type, checksum, source) VALUES (%s, 'product_front', %s, 'image/jpeg', %s, 'user_submission')",
            (first_product, storage_id, "a" * 64),
        )
        self.cur.execute(
            "INSERT INTO product_images (product_id, image_type, storage_object_id, mime_type, checksum, source) VALUES (%s, 'product_front', %s, 'image/jpeg', %s, 'user_submission')",
            (second_product, storage_id, "a" * 64),
        )
        self.cur.execute(
            "INSERT INTO storage_objects (storage_provider, bucket, object_key, checksum_algorithm, checksum_value) VALUES ('test', 'wye', 'objects/b', 'sha256', %s)",
            ("a" * 64,),
        )
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("INSERT INTO storage_objects (storage_provider, bucket, object_key) VALUES ('test', 'wye', 'objects/a')")

    def test_release_checksum_is_unique_within_dataset_only(self):
        self.cur.execute("INSERT INTO sources (source_name, source_type) VALUES ('source-a', 'regulatory') RETURNING id")
        source_id = self.cur.fetchone()[0]
        self.cur.execute("INSERT INTO source_datasets (source_id, dataset_name, dataset_key) VALUES (%s, 'a', 'a') RETURNING id", (source_id,))
        first_dataset = self.cur.fetchone()[0]
        self.cur.execute("INSERT INTO source_datasets (source_id, dataset_name, dataset_key) VALUES (%s, 'b', 'b') RETURNING id", (source_id,))
        second_dataset = self.cur.fetchone()[0]
        self.cur.execute("INSERT INTO source_dataset_releases (dataset_id, version_label, checksum, checksum_algorithm) VALUES (%s, 'v1', 'same', 'sha256')", (first_dataset,))
        self.cur.execute("INSERT INTO source_dataset_releases (dataset_id, version_label, checksum, checksum_algorithm) VALUES (%s, 'v1', 'same', 'sha256')", (second_dataset,))
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute("INSERT INTO source_dataset_releases (dataset_id, version_label, checksum, checksum_algorithm) VALUES (%s, 'v2', 'same', 'sha256')", (first_dataset,))


@unittest.skipUnless(
    os.environ.get("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "set WYE_RUN_MIGRATION_LIFECYCLE_TESTS=1 only for an isolated PostgreSQL database",
)
class MigrationLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]

    def alembic(self, *args, expect_success=True):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args], cwd=self.backend, text=True,
            capture_output=True, check=False,
        )
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_upgrade_preflight_abort_and_protected_downgrade(self):
        suffix = uuid.uuid4().hex
        self.alembic("downgrade", "0002_scientific_data_model")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO products (barcode, product_name, category) "
                    "VALUES (%s, 'x', 'food') RETURNING id",
                    (f"hardening-preflight-{suffix}",),
                )
                product_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO product_ingredients (product_id, ingredient_id, raw_name) "
                    "VALUES (%s, NULL, 'x') RETURNING id",
                    (product_id,),
                )
                product_ingredient_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO ingredient_mapping_reviews "
                    "(product_ingredient_id, raw_text, requested_by_method) "
                    "VALUES (%s, 'x', 'manual') RETURNING id",
                    (product_ingredient_id,),
                )
                review_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO substances (preferred_name, normalized_name) "
                    "VALUES (%s, %s) RETURNING id",
                    (f"substance-{suffix}", f"substance-{suffix}"),
                )
                substance_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO ingredient_mapping_review_candidates "
                    "(review_id, substance_id, candidate_method) "
                    "VALUES (%s, %s, 'manual_review')",
                    (review_id, substance_id),
                )
            conn.commit()
        finally:
            conn.close()

        self.alembic("upgrade", "head", expect_success=False)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version")
                self.assertEqual(cur.fetchone()[0], "0002_scientific_data_model")
                cur.execute("SELECT to_regclass('public.storage_objects')")
                self.assertIsNone(cur.fetchone()[0])
                cur.execute(
                    "DELETE FROM ingredient_mapping_review_candidates WHERE review_id=%s",
                    (review_id,),
                )
                cur.execute("DELETE FROM ingredient_mapping_reviews WHERE id=%s", (review_id,))
                cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
                cur.execute("DELETE FROM substances WHERE id=%s", (substance_id,))
            conn.commit()
        finally:
            conn.close()

        self.alembic("upgrade", "head")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO products (barcode, product_name, category) "
                    "VALUES (%s, 'x', 'food') RETURNING id",
                    (f"hardening-downgrade-{suffix}",),
                )
                protected_product_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO storage_objects (storage_provider, bucket, object_key) "
                    "VALUES ('test', 'wye', %s) RETURNING id",
                    (f"downgrade/{suffix}",),
                )
                storage_object_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO product_images "
                    "(product_id, image_type, storage_object_id, mime_type, checksum, source, status) "
                    "VALUES (%s, 'other', %s, 'image/jpeg', %s, 'user_submission', 'active')",
                    (protected_product_id, storage_object_id, "a" * 64),
                )
            conn.commit()
        finally:
            conn.close()

        self.alembic("downgrade", "0002_scientific_data_model", expect_success=False)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version")
                self.assertEqual(cur.fetchone()[0], "0003_data_integrity_hardening")
                cur.execute("DELETE FROM product_images WHERE product_id=%s", (protected_product_id,))
                cur.execute("DELETE FROM products WHERE id=%s", (protected_product_id,))
                cur.execute("DELETE FROM storage_objects WHERE id=%s", (storage_object_id,))
            conn.commit()
        finally:
            conn.close()

        self.alembic("downgrade", "0002_scientific_data_model")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.storage_objects')")
                self.assertIsNone(cur.fetchone()[0])
        finally:
            conn.close()
        self.alembic("upgrade", "head")


if __name__ == "__main__":
    unittest.main()
