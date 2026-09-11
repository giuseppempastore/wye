from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.barcodes import validate_product_barcode
from app.routes.mobile_upload import require_extraction_session
from app.services.mobile_upload_sessions import MobileSessionRecord
from app.services.product_acquisitions import (
    AcquisitionError,
    ProductAcquisitionService,
    barcode_digest,
)


router = APIRouter(
    prefix="/mobile/dev/v1/capture/product-acquisitions",
    tags=["mobile-product-acquisitions"],
)


class AcquisitionDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: Literal["product_front", "ingredients", "nutrition"]
    product_image_id: int = Field(gt=0)
    checksum_sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    raw_ocr: str | None = Field(default=None, max_length=20000)
    source_language: str | None = Field(
        default=None,
        max_length=10,
        pattern=r"^(?:und|[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)$",
    )
    structured_extraction: dict[str, Any] = Field(default_factory=dict)


class PublicRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)
    barcode: str
    draft_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,128}$")
    pipeline_version: str = Field(pattern=r"^[a-z0-9_.-]{1,80}$")
    documents: list[AcquisitionDocumentRequest] = Field(min_length=3, max_length=3)


class AcquisitionResponse(BaseModel):
    acquisition_id: str
    product_id: int | None
    status: str
    job_status: str | None = None
    attempts: int | None = None
    max_attempts: int | None = None
    recoverable_error_code: str | None = None
    submitted_at: datetime | None = None
    updated_at: datetime | None = None


def _response(row: dict[str, Any]) -> AcquisitionResponse:
    return AcquisitionResponse(
        acquisition_id=str(row["id"]),
        product_id=row.get("product_id"),
        status=row["status"],
        job_status=row.get("job_status"),
        attempts=row.get("attempts"),
        max_attempts=row.get("max_attempts"),
        recoverable_error_code=row.get("recoverable_error_code"),
        submitted_at=row.get("submitted_at"),
        updated_at=row.get("updated_at"),
    )


@router.post("", response_model=AcquisitionResponse, status_code=202)
def submit_public_registration(
    payload: PublicRegistrationRequest,
    _session: MobileSessionRecord = Depends(require_extraction_session),
) -> AcquisitionResponse:
    barcode = validate_product_barcode(payload.barcode)
    if not barcode.valid:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_product_barcode", "reason": barcode.reason},
        )
    try:
        row = ProductAcquisitionService().submit_public_registration(
            product_id=payload.product_id,
            barcode_hash=barcode_digest(barcode.value),
            idempotency_key=f"public-registration:{payload.draft_id}",
            pipeline_version=payload.pipeline_version,
            documents=[item.model_dump() for item in payload.documents],
        )
        return _response(row)
    except AcquisitionError as error:
        status = 409 if error.code in {
            "verified_product_is_read_only",
            "product_identity_mismatch",
        } else 422
        raise HTTPException(status_code=status, detail={"code": error.code}) from error


@router.get("/{acquisition_id}", response_model=AcquisitionResponse)
def get_acquisition(
    acquisition_id: str,
    _session: MobileSessionRecord = Depends(require_extraction_session),
) -> AcquisitionResponse:
    try:
        normalized_id = str(uuid.UUID(acquisition_id))
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": "invalid_acquisition_id"}) from error
    row = ProductAcquisitionService().get(normalized_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "acquisition_not_found"})
    return _response(row)
