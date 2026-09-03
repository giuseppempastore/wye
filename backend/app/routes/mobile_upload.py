import logging
import re
import time
import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.extraction.config import ExtractionSettings
from app.extraction.prompts import PROMPT_ID
from app.mobile_facade_config import MobileFacadeConfigError, MobileFacadeSettings
from app.security import require_image_api_key
from app.services.image_uploads import ImageUploadService, UploadError
from app.services.label_extractions import ExtractionError, LabelExtractionService
from app.services.mobile_upload_sessions import (
    MobileSessionError,
    MobileSessionRecord,
    MobileUploadSessionStore,
)
from app.storage import StorageSettings, get_storage_adapter


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mobile/dev/v1/capture", tags=["mobile-dev-capture"])
_session_store = MobileUploadSessionStore()
_safe_request_id_pattern = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


class MobileSessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scopes: list[Literal["upload", "extraction"]] = Field(
        default_factory=lambda: ["upload", "extraction"],
        min_length=1,
        max_length=2,
    )


class MobileSessionCreateResponse(BaseModel):
    session_id: str
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    scopes: list[Literal["upload", "extraction"]]
    expires_at: datetime


class MobileUploadInitializeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_type: Literal["product_front", "ingredients", "nutrition", "other"]
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    byte_size: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")


class MobileUploadInitializeResponse(BaseModel):
    upload_id: str
    upload_url: str
    method: Literal["PUT"]
    headers: dict[str, str]
    expires_at: datetime


class MobileUploadFinalizeResponse(BaseModel):
    upload_id: str
    status: Literal["finalized"]
    storage_object_id: int = Field(gt=0)
    product_image_id: int = Field(gt=0)


class MobileExtractionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = Field(default=None, max_length=255)
    prompt_version: str = Field(default=PROMPT_ID, max_length=255)


class MobileExtractionRun(BaseModel):
    id: int = Field(gt=0)
    label_document_id: int | None = Field(default=None, gt=0)
    run_status: Literal["pending", "running", "succeeded", "failed", "superseded"]
    error_code: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class MobileExtractionItem(BaseModel):
    id: int = Field(gt=0)
    item_type: Literal[
        "ingredient",
        "ingredient_list",
        "nutrition",
        "allergen",
        "quantity",
        "unit",
        "other",
    ]
    raw_text: str
    normalized_text: str | None = None
    detected_language: str | None = None
    structured_value: dict[str, Any] | None = None
    unit: str | None = None
    position_in_document: int | None = None
    extraction_confidence: float | None = Field(default=None, ge=0, le=1)
    extraction_status: Literal["detected", "validated", "rejected"] = "detected"


class MobileExtractionResponse(BaseModel):
    extraction: MobileExtractionRun
    items: list[MobileExtractionItem]


class MobileExtractionListResponse(BaseModel):
    extractions: list[MobileExtractionRun]


def _safe_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _safe_upload_initialize_result(result: dict[str, Any]) -> dict[str, Any]:
    headers = result.get("headers")
    forbidden = {
        "authorization",
        "cookie",
        "proxy-authorization",
        "set-cookie",
        "x-wye-image-key",
    }
    invalid_headers = not isinstance(headers, dict) or any(
        str(name).lower() in forbidden for name in (headers or {})
    )
    try:
        validated = MobileUploadInitializeResponse.model_validate(result)
    except ValidationError as exc:
        raise _safe_error(
            500,
            "mobile_upload_contract_invalid",
            "Mobile upload capability response is invalid",
        ) from exc
    if invalid_headers:
        raise _safe_error(
            500,
            "mobile_upload_contract_invalid",
            "Mobile upload capability response is invalid",
        )
    return validated.model_dump()


def _request_id(value: str | None) -> str:
    if value and _safe_request_id_pattern.fullmatch(value):
        return value
    return uuid.uuid4().hex


_extraction_run_fields = {
    "id",
    "label_document_id",
    "run_status",
    "error_code",
    "created_at",
    "started_at",
    "completed_at",
}
_extraction_item_fields = {
    "id",
    "item_type",
    "raw_text",
    "normalized_text",
    "detected_language",
    "structured_value",
    "unit",
    "position_in_document",
    "extraction_confidence",
    "extraction_status",
}


def _project_extraction_run(run: dict[str, Any]) -> dict[str, Any]:
    return {key: run[key] for key in _extraction_run_fields if key in run}


def _project_extraction_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "extraction": _project_extraction_run(result.get("extraction") or {}),
        "items": [
            {key: item[key] for key in _extraction_item_fields if key in item}
            for item in (result.get("items") or [])
        ],
    }


def _log_transition(
    event: str,
    request_id: str,
    status: str,
    started_at: float,
    session: MobileSessionRecord | None = None,
    product_id: int | None = None,
    image_type: str | None = None,
    product_image_id: int | None = None,
    storage_object_id: int | None = None,
    extraction_run_id: int | None = None,
) -> None:
    logger.info(
        "mobile_facade event=%s request_id=%s session_id=%s product_id=%s "
        "image_type=%s status=%s latency_ms=%s product_image_id=%s "
        "storage_object_id=%s extraction_run_id=%s",
        event,
        request_id,
        session.session_id if session else None,
        product_id,
        image_type,
        status,
        max(0, int((time.perf_counter() - started_at) * 1000)),
        product_image_id,
        storage_object_id,
        extraction_run_id,
    )


def require_mobile_facade_enabled() -> MobileFacadeSettings:
    try:
        settings = MobileFacadeSettings.from_env()
    except MobileFacadeConfigError as exc:
        raise _safe_error(
            503,
            "mobile_facade_unavailable",
            "Mobile upload facade configuration is invalid",
        ) from exc
    if not settings.enabled:
        raise _safe_error(
            503,
            "mobile_facade_disabled",
            "Mobile upload facade is disabled",
        )
    return settings


def require_mobile_facade_operator(
    settings: MobileFacadeSettings = Depends(require_mobile_facade_enabled),
    x_wye_image_key: str | None = Header(default=None, alias="X-WYE-Image-Key"),
) -> MobileFacadeSettings:
    try:
        require_image_api_key(x_wye_image_key)
    except HTTPException as exc:
        if exc.status_code == 503:
            raise _safe_error(
                503,
                "mobile_facade_operator_auth_unavailable",
                "Mobile facade operator authorization is unavailable",
            ) from exc
        raise _safe_error(
            401,
            "mobile_facade_operator_auth_invalid",
            "Mobile facade operator authorization is invalid",
        ) from exc
    return settings


def get_mobile_session_store() -> MobileUploadSessionStore:
    return _session_store


def _validate_mobile_session(
    required_scope: str,
    authorization: str | None,
    x_wye_image_key: str | None,
    store: MobileUploadSessionStore,
) -> MobileSessionRecord:
    if x_wye_image_key is not None:
        raise _safe_error(
            400,
            "mobile_server_secret_header_forbidden",
            "Mobile facade operations do not accept X-WYE-Image-Key",
        )
    if not authorization:
        raise _safe_error(
            401, "mobile_session_missing", "Mobile session is required"
        )
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise _safe_error(
            401, "mobile_session_invalid", "Mobile session is invalid"
        )
    try:
        return store.validate(token.strip(), required_scope)
    except MobileSessionError as exc:
        raise _safe_error(exc.status, exc.code, exc.message) from exc


def require_upload_session(
    _settings: MobileFacadeSettings = Depends(require_mobile_facade_enabled),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_wye_image_key: str | None = Header(default=None, alias="X-WYE-Image-Key"),
    store: MobileUploadSessionStore = Depends(get_mobile_session_store),
) -> MobileSessionRecord:
    return _validate_mobile_session(
        "upload", authorization, x_wye_image_key, store
    )


def require_extraction_session(
    _settings: MobileFacadeSettings = Depends(require_mobile_facade_enabled),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_wye_image_key: str | None = Header(default=None, alias="X-WYE-Image-Key"),
    store: MobileUploadSessionStore = Depends(get_mobile_session_store),
) -> MobileSessionRecord:
    return _validate_mobile_session(
        "extraction", authorization, x_wye_image_key, store
    )


def get_image_upload_service() -> ImageUploadService:
    try:
        settings = StorageSettings.from_env()
        return ImageUploadService(get_storage_adapter(settings), settings)
    except RuntimeError as exc:
        raise _safe_error(
            503,
            "mobile_upload_unavailable",
            "Mobile image upload is unavailable",
        ) from exc


def get_label_extraction_service() -> LabelExtractionService:
    try:
        storage = StorageSettings.from_env()
        extraction = ExtractionSettings.from_env()
        return LabelExtractionService(
            get_storage_adapter(storage), storage, extraction
        )
    except RuntimeError as exc:
        raise _safe_error(
            503,
            "mobile_extraction_unavailable",
            "Mobile label extraction is unavailable",
        ) from exc


@router.post(
    "/sessions",
    response_model=MobileSessionCreateResponse,
    status_code=201,
)
def create_mobile_session(
    payload: MobileSessionCreateRequest,
    response: Response,
    settings: MobileFacadeSettings = Depends(require_mobile_facade_operator),
    store: MobileUploadSessionStore = Depends(get_mobile_session_store),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    started_at = time.perf_counter()
    request_id = _request_id(x_request_id)
    try:
        issued = store.issue(set(payload.scopes), settings.session_ttl_seconds)
    except MobileSessionError as exc:
        _log_transition("session_create", request_id, exc.code, started_at)
        raise _safe_error(exc.status, exc.code, exc.message) from exc
    except RuntimeError as exc:
        _log_transition(
            "session_create", request_id, "mobile_session_unavailable", started_at
        )
        raise _safe_error(
            503,
            "mobile_session_unavailable",
            "Mobile session could not be issued",
        ) from exc
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Request-ID"] = request_id
    _log_transition(
        "session_create", request_id, "created", started_at, issued.record
    )
    return {
        "session_id": issued.record.session_id,
        "access_token": issued.token,
        "scopes": sorted(issued.record.scopes),
        "expires_at": issued.record.expires_at,
    }


@router.post(
    "/products/{product_id}/images/uploads",
    response_model=MobileUploadInitializeResponse,
    status_code=201,
)
def initialize_mobile_upload(
    payload: MobileUploadInitializeRequest,
    response: Response,
    product_id: int = Path(gt=0),
    session: MobileSessionRecord = Depends(require_upload_session),
    service: ImageUploadService = Depends(get_image_upload_service),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    started_at = time.perf_counter()
    request_id = _request_id(x_request_id)
    try:
        result = service.initialize(
            product_id,
            payload.image_type,
            payload.mime_type,
            payload.byte_size,
            payload.sha256.lower(),
        )
    except UploadError as exc:
        _log_transition(
            "upload_initialize",
            request_id,
            exc.code,
            started_at,
            session,
            product_id,
            payload.image_type,
        )
        raise _safe_error(exc.status, exc.code, exc.message) from exc
    except Exception:
        _log_transition(
            "upload_initialize",
            request_id,
            "mobile_upload_failed",
            started_at,
            session,
            product_id,
            payload.image_type,
        )
        raise _safe_error(
            503, "mobile_upload_failed", "Mobile image upload failed"
        ) from None
    try:
        safe_result = _safe_upload_initialize_result(result)
    except HTTPException:
        _log_transition(
            "upload_initialize",
            request_id,
            "mobile_upload_contract_invalid",
            started_at,
            session,
            product_id,
            payload.image_type,
        )
        raise
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Request-ID"] = request_id
    _log_transition(
        "upload_initialize",
        request_id,
        "created",
        started_at,
        session,
        product_id,
        payload.image_type,
    )
    return safe_result


@router.post(
    "/products/{product_id}/images/uploads/{upload_id}/finalize",
    response_model=MobileUploadFinalizeResponse,
)
def finalize_mobile_upload(
    response: Response,
    product_id: int = Path(gt=0),
    upload_id: uuid.UUID = Path(),
    session: MobileSessionRecord = Depends(require_upload_session),
    service: ImageUploadService = Depends(get_image_upload_service),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    started_at = time.perf_counter()
    request_id = _request_id(x_request_id)
    try:
        result = service.finalize(product_id, str(upload_id))
    except UploadError as exc:
        _log_transition(
            "upload_finalize",
            request_id,
            exc.code,
            started_at,
            session,
            product_id,
        )
        raise _safe_error(exc.status, exc.code, exc.message) from exc
    except Exception:
        _log_transition(
            "upload_finalize",
            request_id,
            "mobile_finalize_failed",
            started_at,
            session,
            product_id,
        )
        raise _safe_error(
            503, "mobile_finalize_failed", "Mobile upload finalization failed"
        ) from None
    response.headers["X-Request-ID"] = request_id
    _log_transition(
        "upload_finalize",
        request_id,
        "finalized",
        started_at,
        session,
        product_id,
        product_image_id=result.get("product_image_id"),
        storage_object_id=result.get("storage_object_id"),
    )
    return result


@router.post(
    "/products/{product_id}/images/{image_id}/extractions",
    response_model=MobileExtractionResponse,
    status_code=201,
)
def create_mobile_extraction(
    payload: MobileExtractionCreateRequest,
    response: Response,
    product_id: int = Path(gt=0),
    image_id: int = Path(gt=0),
    session: MobileSessionRecord = Depends(require_extraction_session),
    service: LabelExtractionService = Depends(get_label_extraction_service),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    started_at = time.perf_counter()
    request_id = _request_id(x_request_id)
    try:
        result = service.create(
            product_id,
            image_id,
            idempotency_key or "",
            payload.model,
            payload.prompt_version,
        )
    except ExtractionError as exc:
        _log_transition(
            "extraction_create",
            request_id,
            exc.code,
            started_at,
            session,
            product_id,
            product_image_id=image_id,
            extraction_run_id=exc.run_id,
        )
        raise _safe_error(exc.status, exc.code, exc.message) from exc
    except Exception:
        _log_transition(
            "extraction_create",
            request_id,
            "mobile_extraction_failed",
            started_at,
            session,
            product_id,
            product_image_id=image_id,
        )
        raise _safe_error(
            503, "mobile_extraction_failed", "Mobile label extraction failed"
        ) from None
    response.headers["X-Request-ID"] = request_id
    run_id = (result.get("extraction") or {}).get("id")
    _log_transition(
        "extraction_create",
        request_id,
        "completed",
        started_at,
        session,
        product_id,
        product_image_id=image_id,
        extraction_run_id=run_id,
    )
    return _project_extraction_result(result)


@router.get(
    "/products/{product_id}/images/{image_id}/extractions",
    response_model=MobileExtractionListResponse,
)
def list_mobile_extractions(
    response: Response,
    product_id: int = Path(gt=0),
    image_id: int = Path(gt=0),
    session: MobileSessionRecord = Depends(require_extraction_session),
    service: LabelExtractionService = Depends(get_label_extraction_service),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    started_at = time.perf_counter()
    request_id = _request_id(x_request_id)
    try:
        result = service.list(product_id, image_id)
    except ExtractionError as exc:
        _log_transition(
            "extraction_list",
            request_id,
            exc.code,
            started_at,
            session,
            product_id,
            product_image_id=image_id,
            extraction_run_id=exc.run_id,
        )
        raise _safe_error(exc.status, exc.code, exc.message) from exc
    except Exception:
        _log_transition(
            "extraction_list",
            request_id,
            "mobile_extraction_failed",
            started_at,
            session,
            product_id,
            product_image_id=image_id,
        )
        raise _safe_error(
            503, "mobile_extraction_failed", "Mobile label extraction failed"
        ) from None
    response.headers["X-Request-ID"] = request_id
    _log_transition(
        "extraction_list",
        request_id,
        "completed",
        started_at,
        session,
        product_id,
        product_image_id=image_id,
    )
    return {
        "extractions": [
            _project_extraction_run(run)
            for run in (result.get("extractions") or [])
        ]
    }


@router.get(
    "/products/{product_id}/images/{image_id}/extractions/{run_id}",
    response_model=MobileExtractionResponse,
)
def get_mobile_extraction(
    response: Response,
    product_id: int = Path(gt=0),
    image_id: int = Path(gt=0),
    run_id: int = Path(gt=0),
    session: MobileSessionRecord = Depends(require_extraction_session),
    service: LabelExtractionService = Depends(get_label_extraction_service),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    started_at = time.perf_counter()
    request_id = _request_id(x_request_id)
    try:
        result = service.get(product_id, image_id, run_id)
    except ExtractionError as exc:
        _log_transition(
            "extraction_get",
            request_id,
            exc.code,
            started_at,
            session,
            product_id,
            product_image_id=image_id,
            extraction_run_id=exc.run_id or run_id,
        )
        raise _safe_error(exc.status, exc.code, exc.message) from exc
    except Exception:
        _log_transition(
            "extraction_get",
            request_id,
            "mobile_extraction_failed",
            started_at,
            session,
            product_id,
            product_image_id=image_id,
            extraction_run_id=run_id,
        )
        raise _safe_error(
            503, "mobile_extraction_failed", "Mobile label extraction failed"
        ) from None
    response.headers["X-Request-ID"] = request_id
    _log_transition(
        "extraction_get",
        request_id,
        "completed",
        started_at,
        session,
        product_id,
        product_image_id=image_id,
        extraction_run_id=run_id,
    )
    return _project_extraction_result(result)
