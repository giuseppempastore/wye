import os
import unittest
import uuid

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app


def _gtin14() -> str:
    body = f"{uuid.uuid4().int % 10**13:013d}"
    total = sum(
        int(digit) * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(body)
    )
    return body + str((10 - total % 10) % 10)


@unittest.skipUnless(
    os.getenv("WYE_TEST_DATABASE"),
    "requires isolated WYE_TEST_DATABASE",
)
class ProductAcquisitionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.product_ids: list[int] = []
        self.storage_object_ids: list[int] = []

    def tearDown(self):
        if not self.product_ids:
            return
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE id = ANY(%s)", (self.product_ids,))
                if self.storage_object_ids:
                    cur.execute(
                        "DELETE FROM storage_objects WHERE id = ANY(%s)",
                        (self.storage_object_ids,),
                    )
            conn.commit()
        finally:
            conn.close()

    def test_unknown_ingredient_stays_pending_and_non_authoritative(self):
        barcode = _gtin14()
        response = self.client.post(
            "/products",
            json={
                "barcode": barcode,
                "brand_name": "Test brand",
                "product_name": "Test product",
                "category": "food",
                "product_type": "snack",
                "ingredients": "sciroppo d'agave",
                "nutrition": {"energy_kcal": 120, "sugar_g": 8},
            },
        )
        self.assertEqual(response.status_code, 200)
        product_id = response.json()["product"]["id"]
        self.product_ids.append(product_id)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT verified,status FROM products WHERE id=%s",
                    (product_id,),
                )
                self.assertEqual(cur.fetchone(), (False, "needs_review"))
                cur.execute(
                    """SELECT ingredient_id,raw_name,canonical_name,confidence,
                              is_unknown,mapping_method,mapping_status,mapping_provenance
                       FROM product_ingredients WHERE product_id=%s""",
                    (product_id,),
                )
                ingredient = cur.fetchone()
                self.assertIsNone(ingredient[0])
                self.assertEqual(ingredient[1], "sciroppo d'agave")
                self.assertIsNone(ingredient[2])
                self.assertIsNone(ingredient[3])
                self.assertTrue(ingredient[4])
                self.assertEqual(ingredient[5:7], ("unmapped", "needs_review"))
                self.assertFalse(ingredient[7]["authoritative"])
                cur.execute(
                    """SELECT r.review_status,r.requested_by_method
                       FROM ingredient_mapping_reviews r
                       JOIN product_ingredients pi ON pi.id=r.product_ingredient_id
                       WHERE pi.product_id=%s""",
                    (product_id,),
                )
                self.assertEqual(cur.fetchone(), ("pending", "manual"))
                cur.execute(
                    "SELECT verified FROM nutrition_facts WHERE product_id=%s",
                    (product_id,),
                )
                self.assertEqual(cur.fetchone(), (False,))
                cur.execute(
                    "SELECT review_status FROM product_reviews WHERE product_id=%s",
                    (product_id,),
                )
                self.assertEqual(cur.fetchone(), ("pending",))
                cur.execute(
                    "SELECT count(*) FROM substances WHERE lower(preferred_name)=lower(%s)",
                    ("sciroppo d'agave",),
                )
                self.assertEqual(cur.fetchone()[0], 0)
        finally:
            conn.close()

    def test_duplicate_does_not_overwrite_existing_product(self):
        barcode = _gtin14()
        original = {
            "barcode": barcode,
            "brand_name": "Original brand",
            "product_name": "Original product",
            "category": "food",
            "ingredients": "",
        }
        created = self.client.post("/products", json=original)
        self.assertEqual(created.status_code, 200)
        self.product_ids.append(created.json()["product"]["id"])

        changed = dict(original, product_name="Silent overwrite")
        self.assertEqual(self.client.post("/products", json=changed).status_code, 409)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT product_name FROM products WHERE barcode=%s", (barcode,))
                self.assertEqual(cur.fetchone()[0], "Original product")
        finally:
            conn.close()

    def test_invalid_input_is_rejected_before_persistence(self):
        common = {
            "brand_name": "Test brand",
            "product_name": "Test product",
            "category": "food",
            "ingredients": "",
        }
        self.assertEqual(
            self.client.post("/products", json=dict(common, barcode="https://invalid")).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/products",
                json=dict(common, barcode=_gtin14(), image_url="data:image/jpeg;base64,blocked"),
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/products",
                json=dict(common, barcode=_gtin14(), nutrition={"sugar_g": 101}),
            ).status_code,
            400,
        )

    def test_lookup_returns_canonical_front_image_and_explicit_score_state(self):
        barcode = _gtin14()
        created = self.client.post(
            "/products",
            json={
                "barcode": barcode,
                "brand_name": "Test brand",
                "product_name": "Test product",
                "category": "food",
                "ingredients": "",
            },
        )
        self.assertEqual(created.status_code, 200)
        product_id = created.json()["product"]["id"]
        self.product_ids.append(product_id)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO storage_objects(
                           storage_provider,bucket,object_key,checksum_algorithm,
                           checksum_value,mime_type,byte_size
                       ) VALUES('s3','test',%s,'sha256',%s,'image/jpeg',4)
                       RETURNING id""",
                    (f"phase92b/{uuid.uuid4().hex}", "a" * 64),
                )
                storage_id = cur.fetchone()[0]
                self.storage_object_ids.append(storage_id)
                cur.execute(
                    """INSERT INTO product_images(
                           product_id,image_type,mime_type,byte_size,checksum,
                           source,status,is_current,storage_object_id
                       ) VALUES(%s,'product_front','image/jpeg',4,%s,
                                'user_submission','active',TRUE,%s)
                       RETURNING id""",
                    (product_id, "a" * 64, storage_id),
                )
                image_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        lookup = self.client.get(f"/product/{barcode}")
        self.assertEqual(lookup.status_code, 200)
        body = lookup.json()
        self.assertEqual(body["product_image"]["id"], image_id)
        self.assertEqual(
            body["score_view"]["overall_score"]["availability"],
            "deferred",
        )
        self.assertNotIn("score_value", body["score_view"]["overall_score"])


if __name__ == "__main__":
    unittest.main()
