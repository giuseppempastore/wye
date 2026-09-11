from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import psycopg2.extras
from psycopg2.extras import Json

from app.db import get_connection


PUBLIC_DOCUMENT_TYPES = frozenset({"product_front", "ingredients", "nutrition"})


class AcquisitionError(Exception):
    def __init__(self, code: str, *, retryable: bool = False):
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class ClaimedAcquisition:
    acquisition_id: str
    job_id: str
    lease_token: str
    attempts: int
    max_attempts: int


def barcode_digest(barcode: str) -> str:
    return hashlib.sha256(barcode.encode("ascii")).hexdigest()


class ProductAcquisitionService:
    """Persistent public-registration queue, separate from scientific batches."""

    def submit_public_registration(
        self,
        *,
        product_id: int,
        barcode_hash: str,
        idempotency_key: str,
        pipeline_version: str,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if set(item.get("document_type") for item in documents) != PUBLIC_DOCUMENT_TYPES:
            raise AcquisitionError("all_public_registration_photos_required")
        if len(documents) != len(PUBLIC_DOCUMENT_TYPES):
            raise AcquisitionError("duplicate_document_type")

        connection = get_connection()
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                "SELECT * FROM product_acquisitions WHERE idempotency_key=%s",
                (idempotency_key,),
            )
            existing = cursor.fetchone()
            if existing:
                connection.rollback()
                return dict(existing)

            cursor.execute(
                "SELECT id,barcode,verified,status FROM products WHERE id=%s FOR SHARE",
                (product_id,),
            )
            product = cursor.fetchone()
            if not product:
                raise AcquisitionError("product_not_found")
            if product["verified"]:
                raise AcquisitionError("verified_product_is_read_only")
            if barcode_digest(product["barcode"]) != barcode_hash:
                raise AcquisitionError("product_identity_mismatch")

            image_ids = [item["product_image_id"] for item in documents]
            cursor.execute(
                """
                SELECT id,image_type,checksum FROM product_images
                WHERE product_id=%s AND id=ANY(%s) AND status='active'
                """,
                (product_id, image_ids),
            )
            images = {row["id"]: row for row in cursor.fetchall()}
            for document in documents:
                image = images.get(document["product_image_id"])
                if image is None or image["image_type"] != document["document_type"]:
                    raise AcquisitionError("document_image_mismatch")
                if image["checksum"].lower() != document["checksum_sha256"].lower():
                    raise AcquisitionError("document_checksum_mismatch")

            acquisition_id = str(uuid.uuid4())
            job_id = str(uuid.uuid4())
            provenance = {
                "source": "mobile_public_registration",
                "authoritative": False,
                "image_ai_invoked": False,
            }
            cursor.execute(
                """
                INSERT INTO product_acquisitions(
                  id,product_id,acquisition_kind,status,barcode_hash,
                  idempotency_key,pipeline_version,provenance
                ) VALUES(%s,%s,'public_registration','queued',%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    acquisition_id,
                    product_id,
                    barcode_hash,
                    idempotency_key,
                    pipeline_version,
                    Json(provenance),
                ),
            )
            acquisition = dict(cursor.fetchone())
            for document in documents:
                extraction = document.get("structured_extraction") or {}
                warnings = extraction.get("warnings") or []
                cursor.execute(
                    """
                    INSERT INTO product_acquisition_documents(
                      acquisition_id,product_image_id,document_type,
                      checksum_sha256,raw_ocr,source_language,
                      structured_extraction,extraction_warnings
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        acquisition_id,
                        document["product_image_id"],
                        document["document_type"],
                        document["checksum_sha256"].lower(),
                        document.get("raw_ocr"),
                        document.get("source_language"),
                        Json(extraction),
                        Json(warnings),
                    ),
                )
            cursor.execute(
                """
                INSERT INTO product_acquisition_jobs(id,acquisition_id)
                VALUES(%s,%s)
                """,
                (job_id, acquisition_id),
            )
            cursor.execute(
                """
                INSERT INTO product_acquisition_events(
                  acquisition_id,from_status,to_status,actor_type,safe_metadata
                ) VALUES(%s,NULL,'queued','mobile_client',%s)
                """,
                (acquisition_id, Json({"document_count": len(documents)})),
            )
            connection.commit()
            return acquisition
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(self, acquisition_id: str) -> dict[str, Any] | None:
        connection = get_connection()
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """
                SELECT a.*,j.job_status,j.attempts,j.max_attempts,j.last_error_code
                FROM product_acquisitions a
                JOIN product_acquisition_jobs j ON j.acquisition_id=a.id
                WHERE a.id=%s
                """,
                (acquisition_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def claim_next(self, *, lease_seconds: int = 120) -> ClaimedAcquisition | None:
        connection = get_connection()
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM product_acquisition_jobs
                WHERE ((
                  job_status='queued' AND available_at <= NOW()
                ) OR (
                  job_status='processing' AND lease_expires_at < NOW()
                )) AND attempts < max_attempts
                ORDER BY available_at,created_at
                FOR UPDATE SKIP LOCKED LIMIT 1
                """
            )
            job = cursor.fetchone()
            if not job:
                connection.rollback()
                return None
            lease_token = str(uuid.uuid4())
            cursor.execute(
                """
                UPDATE product_acquisition_jobs
                SET job_status='processing',attempts=attempts+1,lease_token=%s,
                    lease_expires_at=NOW()+(%s * INTERVAL '1 second'),
                    updated_at=NOW()
                WHERE id=%s
                RETURNING attempts,max_attempts
                """,
                (lease_token, lease_seconds, job["id"]),
            )
            claimed = cursor.fetchone()
            attempts = claimed["attempts"]
            max_attempts = claimed["max_attempts"]
            cursor.execute(
                """
                UPDATE product_acquisitions SET status='processing',updated_at=NOW(),
                  recoverable_error_code=NULL WHERE id=%s
                """,
                (job["acquisition_id"],),
            )
            cursor.execute(
                """
                INSERT INTO product_acquisition_events(
                  acquisition_id,from_status,to_status,actor_type,safe_metadata
                ) VALUES(%s,%s,'processing','worker',%s)
                """,
                (
                    job["acquisition_id"],
                    "failed" if job["last_error_code"] else "queued",
                    Json({"attempt": attempts}),
                ),
            )
            connection.commit()
            return ClaimedAcquisition(
                acquisition_id=str(job["acquisition_id"]),
                job_id=str(job["id"]),
                lease_token=lease_token,
                attempts=attempts,
                max_attempts=max_attempts,
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def complete(self, claim: ClaimedAcquisition) -> None:
        connection = get_connection()
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """
                SELECT a.product_id,p.verified,count(d.id) AS document_count
                FROM product_acquisitions a
                JOIN products p ON p.id=a.product_id
                LEFT JOIN product_acquisition_documents d ON d.acquisition_id=a.id
                WHERE a.id=%s GROUP BY a.product_id,p.verified
                """,
                (claim.acquisition_id,),
            )
            row = cursor.fetchone()
            if not row or row["verified"]:
                raise AcquisitionError("product_became_read_only")
            if row["document_count"] != 3:
                raise AcquisitionError("acquisition_documents_incomplete", retryable=True)
            cursor.execute(
                """
                UPDATE product_acquisitions SET status='extracted',updated_at=NOW()
                WHERE id=%s
                """,
                (claim.acquisition_id,),
            )
            cursor.execute(
                """
                INSERT INTO product_acquisition_events(
                  acquisition_id,from_status,to_status,actor_type
                ) VALUES(%s,'processing','extracted','worker')
                """,
                (claim.acquisition_id,),
            )
            cursor.execute(
                """
                UPDATE product_acquisitions
                SET status='needs_review',updated_at=NOW(),completed_at=NOW()
                WHERE id=%s
                """,
                (claim.acquisition_id,),
            )
            cursor.execute(
                """
                INSERT INTO product_acquisition_events(
                  acquisition_id,from_status,to_status,actor_type,
                  safe_metadata
                ) VALUES(%s,'extracted','needs_review','worker',%s)
                """,
                (
                    claim.acquisition_id,
                    Json({"authoritative": False, "admin_review_required": True}),
                ),
            )
            cursor.execute(
                """
                UPDATE product_acquisition_jobs
                SET job_status='succeeded',lease_token=NULL,lease_expires_at=NULL,
                    completed_at=NOW(),updated_at=NOW()
                WHERE id=%s AND lease_token=%s
                """,
                (claim.job_id, claim.lease_token),
            )
            if cursor.rowcount != 1:
                raise AcquisitionError("worker_lease_lost", retryable=True)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def fail(self, claim: ClaimedAcquisition, error: AcquisitionError) -> None:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            retry = error.retryable and claim.attempts < claim.max_attempts
            cursor.execute(
                """
                UPDATE product_acquisition_jobs
                SET job_status=%s,lease_token=NULL,lease_expires_at=NULL,
                    last_error_code=%s,available_at=NOW()+(%s * INTERVAL '1 second'),
                    completed_at=CASE WHEN %s THEN NULL ELSE NOW() END,
                    updated_at=NOW()
                WHERE id=%s AND lease_token=%s
                """,
                (
                    "queued" if retry else "failed",
                    error.code,
                    min(60, 2 ** claim.attempts),
                    retry,
                    claim.job_id,
                    claim.lease_token,
                ),
            )
            cursor.execute(
                """
                UPDATE product_acquisitions
                SET status='failed',recoverable_error_code=%s,updated_at=NOW()
                WHERE id=%s
                """,
                (error.code, claim.acquisition_id),
            )
            cursor.execute(
                """
                INSERT INTO product_acquisition_events(
                  acquisition_id,from_status,to_status,actor_type,safe_metadata
                ) VALUES(%s,'processing','failed','worker',%s)
                """,
                (claim.acquisition_id, Json({"retry_scheduled": retry})),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def process_one(self) -> bool:
        claim = self.claim_next()
        if claim is None:
            return False
        try:
            self.complete(claim)
        except AcquisitionError as error:
            self.fail(claim, error)
        except Exception:
            self.fail(claim, AcquisitionError("worker_internal_error", retryable=True))
        return True
