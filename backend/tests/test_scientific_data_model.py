import os
import unittest

import psycopg2

from app.db import get_connection


@unittest.skipUnless(
    os.environ.get("WYE_TEST_DATABASE"),
    "requires WYE_TEST_DATABASE pointing to an isolated migrated PostgreSQL database",
)
class ScientificDataModelConstraintsTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection()
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        self.cur.execute("SAVEPOINT scientific_data_model_test")

    def tearDown(self):
        try:
            self.cur.execute("ROLLBACK TO SAVEPOINT scientific_data_model_test")
            self.conn.commit()
        finally:
            self.cur.close()
            self.conn.close()

    def create_product(self, barcode: str) -> int:
        self.cur.execute(
            "INSERT INTO products (barcode, product_name, category) VALUES (%s, %s, %s) RETURNING id",
            (barcode, "Migration constraint test", "food"),
        )
        return self.cur.fetchone()[0]

    def test_product_images_store_reference_not_bytea_and_enforce_one_current_type(self):
        self.cur.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'product_images' AND column_name = 'storage_reference'"
        )
        self.assertEqual(self.cur.fetchone()[0], "text")

        product_id = self.create_product("phase2-image-constraint")
        values = (product_id, "product_front", "objects/sha256/a", "image/jpeg", "a" * 64, "user_submission")
        self.cur.execute(
            "INSERT INTO product_images "
            "(product_id, image_type, storage_reference, mime_type, checksum, source) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            values,
        )
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO product_images "
                "(product_id, image_type, storage_reference, mime_type, checksum, source) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (product_id, "product_front", "objects/sha256/b", "image/jpeg", "b" * 64, "user_submission"),
            )

    def test_image_derived_label_document_requires_original_image(self):
        product_id = self.create_product("phase2-label-constraint")
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO product_label_documents (product_id, raw_text, source_type) VALUES (%s, %s, %s)",
                (product_id, "Ingredients: cocoa powder", "image_derived"),
            )

    def test_mapping_candidate_requires_identity_and_only_one_selected_candidate(self):
        product_id = self.create_product("phase2-mapping-constraint")
        self.cur.execute(
            "INSERT INTO product_ingredients (product_id, ingredient_id, raw_name, mapping_status) "
            "VALUES (%s, NULL, %s, %s) RETURNING id",
            (product_id, "Kakaopulver", "needs_review"),
        )
        product_ingredient_id = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO ingredient_mapping_reviews "
            "(product_ingredient_id, raw_text, review_status, requested_by_method) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (product_ingredient_id, "Kakaopulver", "ambiguous", "ai"),
        )
        review_id = self.cur.fetchone()[0]

        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO ingredient_mapping_review_candidates (review_id, candidate_method) VALUES (%s, %s)",
                (review_id, "ai"),
            )
        self.cur.execute("ROLLBACK TO SAVEPOINT scientific_data_model_test")
        self.cur.execute("SAVEPOINT scientific_data_model_test")

        product_id = self.create_product("phase2-mapping-selected")
        self.cur.execute(
            "INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id",
            ("cocoa powder test",),
        )
        ingredient_one = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id",
            ("cocoa butter test",),
        )
        ingredient_two = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO product_ingredients (product_id, ingredient_id, raw_name, mapping_status) "
            "VALUES (%s, NULL, %s, %s) RETURNING id",
            (product_id, "cocoa", "needs_review"),
        )
        product_ingredient_id = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO ingredient_mapping_reviews "
            "(product_ingredient_id, raw_text, review_status, requested_by_method) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (product_ingredient_id, "cocoa", "ambiguous", "ai"),
        )
        review_id = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO ingredient_mapping_review_candidates "
            "(review_id, ingredient_id, candidate_method, is_selected) VALUES (%s, %s, %s, TRUE)",
            (review_id, ingredient_one, "ai"),
        )
        with self.assertRaises(psycopg2.IntegrityError):
            self.cur.execute(
                "INSERT INTO ingredient_mapping_review_candidates "
                "(review_id, ingredient_id, candidate_method, is_selected) VALUES (%s, %s, %s, TRUE)",
                (review_id, ingredient_two, "ai"),
            )


if __name__ == "__main__":
    unittest.main()

