import os
from pathlib import Path
import unittest
import uuid

from app.db import get_connection
from app.services.product_acquisitions import (
    AcquisitionError,
    ProductAcquisitionService,
    barcode_digest,
)


def _gtin14() -> str:
    body = f"{uuid.uuid4().int % 10**13:013d}"
    total = sum(
        int(digit) * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(body)
    )
    return body + str((10 - total % 10) % 10)


class ProductAcquisitionContractTests(unittest.TestCase):
    def test_barcode_digest_is_fixed_length_and_does_not_expose_barcode(self):
        barcode = "4006381333931"
        digest = barcode_digest(barcode)
        self.assertEqual(len(digest), 64)
        self.assertNotIn(barcode, digest)

    def test_scientific_batch_tables_are_not_reused(self):
        migration = (
            Path(__file__).parents[1]
            / "migrations"
            / "versions"
            / "0025_product_acquisition_jobs.py"
        ).read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE product_acquisition_jobs", migration)
        self.assertNotIn("scientific_batch_work_items", migration)

    def test_migration_defines_all_public_lifecycle_states(self):
        migration = (
            Path(__file__).parents[1]
            / "migrations"
            / "versions"
            / "0025_product_acquisition_jobs.py"
        ).read_text(encoding="utf-8")
        for state in (
            "queued",
            "processing",
            "extracted",
            "needs_review",
            "admin_validated",
            "rejected",
            "correction_required",
            "failed",
        ):
            self.assertIn(f"'{state}'", migration)

    def test_migration_has_bounded_attempts_and_worker_lease(self):
        migration = (
            Path(__file__).parents[1]
            / "migrations"
            / "versions"
            / "0025_product_acquisition_jobs.py"
        ).read_text(encoding="utf-8")
        self.assertIn("max_attempts BETWEEN 1 AND 10", migration)
        self.assertIn("lease_expires_at", migration)
        self.assertIn("FOR UPDATE SKIP LOCKED", Path(
            __file__
        ).parents[1].joinpath("app/services/product_acquisitions.py").read_text(encoding="utf-8"))


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated WYE_TEST_DATABASE")
class ProductAcquisitionDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.service = ProductAcquisitionService()
        self.product_id: int | None = None
        self.storage_ids: list[int] = []
        self.acquisition_ids: list[str] = []
        self.barcode = _gtin14()
        self.documents = []
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO products(
                      barcode,brand_name,product_name,category,product_type,
                      source,verified,status
                    ) VALUES(%s,'Queue test','Queue product','other','food',
                      'photo_submission',FALSE,'needs_review') RETURNING id
                    """,
                    (self.barcode,),
                )
                self.product_id = cursor.fetchone()[0]
                for index, document_type in enumerate(
                    ("product_front", "ingredients", "nutrition"), start=1
                ):
                    checksum = str(index) * 64
                    cursor.execute(
                        """
                        INSERT INTO storage_objects(
                          storage_provider,bucket,object_key,checksum_algorithm,
                          checksum_value,mime_type,byte_size
                        ) VALUES('s3','test',%s,'sha256',%s,'image/jpeg',4)
                        RETURNING id
                        """,
                        (f"acquisition-test/{uuid.uuid4().hex}", checksum),
                    )
                    storage_id = cursor.fetchone()[0]
                    self.storage_ids.append(storage_id)
                    cursor.execute(
                        """
                        INSERT INTO product_images(
                          product_id,image_type,mime_type,byte_size,checksum,
                          source,status,is_current,storage_object_id
                        ) VALUES(%s,%s,'image/jpeg',4,%s,
                          'user_submission','active',TRUE,%s) RETURNING id
                        """,
                        (self.product_id, document_type, checksum, storage_id),
                    )
                    image_id = cursor.fetchone()[0]
                    self.documents.append(
                        {
                            "document_type": document_type,
                            "product_image_id": image_id,
                            "checksum_sha256": checksum,
                            "raw_ocr": "Ingredients: water" if document_type == "ingredients" else None,
                            "source_language": "en" if document_type == "ingredients" else None,
                            "structured_extraction": {
                                "warnings": [],
                                "authoritative": False,
                            },
                        }
                    )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                if self.product_id:
                    cursor.execute(
                        "DELETE FROM product_acquisitions WHERE product_id=%s",
                        (self.product_id,),
                    )
                    cursor.execute("DELETE FROM products WHERE id=%s", (self.product_id,))
                if self.storage_ids:
                    cursor.execute(
                        "DELETE FROM storage_objects WHERE id=ANY(%s)",
                        (self.storage_ids,),
                    )
            connection.commit()
        finally:
            connection.close()

    def _submit(self, key: str):
        row = self.service.submit_public_registration(
            product_id=self.product_id,
            barcode_hash=barcode_digest(self.barcode),
            idempotency_key=key,
            pipeline_version="photo_field_mapper_v3",
            documents=self.documents,
        )
        self.acquisition_ids.append(str(row["id"]))
        return row

    def test_submission_is_queued_and_idempotent(self):
        key = f"test:{uuid.uuid4()}"
        first = self._submit(key)
        second = self.service.submit_public_registration(
            product_id=self.product_id,
            barcode_hash=barcode_digest(self.barcode),
            idempotency_key=key,
            pipeline_version="photo_field_mapper_v3",
            documents=self.documents,
        )
        self.assertEqual(first["status"], "queued")
        self.assertEqual(first["id"], second["id"])

    def test_worker_transitions_to_needs_review_with_audit_events(self):
        row = self._submit(f"test:{uuid.uuid4()}")
        claim = self.service.claim_next()
        self.assertIsNotNone(claim)
        self.assertEqual(claim.acquisition_id, str(row["id"]))
        self.service.complete(claim)
        completed = self.service.get(str(row["id"]))
        self.assertEqual(completed["status"], "needs_review")
        self.assertEqual(completed["job_status"], "succeeded")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT to_status FROM product_acquisition_events WHERE acquisition_id=%s ORDER BY id",
                    (str(row["id"]),),
                )
                self.assertEqual(
                    [item[0] for item in cursor.fetchall()],
                    ["queued", "processing", "extracted", "needs_review"],
                )
        finally:
            connection.close()

    def test_retryable_failure_is_bounded_and_preserves_acquisition(self):
        row = self._submit(f"test:{uuid.uuid4()}")
        claim = self.service.claim_next()
        self.service.fail(
            claim,
            AcquisitionError("temporary_failure", retryable=True),
        )
        failed = self.service.get(str(row["id"]))
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["job_status"], "queued")
        self.assertEqual(failed["attempts"], 1)

    def test_verified_product_cannot_be_silently_overwritten(self):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE products SET verified=TRUE,status='active' WHERE id=%s",
                    (self.product_id,),
                )
            connection.commit()
        finally:
            connection.close()
        with self.assertRaisesRegex(AcquisitionError, "verified_product_is_read_only"):
            self._submit(f"test:{uuid.uuid4()}")

    def test_document_image_type_mismatch_is_rejected(self):
        documents = [dict(item) for item in self.documents]
        documents[0]["product_image_id"] = documents[1]["product_image_id"]
        with self.assertRaisesRegex(AcquisitionError, "document_image_mismatch"):
            self.service.submit_public_registration(
                product_id=self.product_id,
                barcode_hash=barcode_digest(self.barcode),
                idempotency_key=f"test:{uuid.uuid4()}",
                pipeline_version="photo_field_mapper_v3",
                documents=documents,
            )


if __name__ == "__main__":
    unittest.main()
