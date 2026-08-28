from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.extraction.config import ExtractionSettings
from app.extraction.prompts import PROMPT_ID
from app.security import require_image_api_key
from app.services.label_extractions import ExtractionError, LabelExtractionService
from app.storage import StorageSettings, get_storage_adapter

router = APIRouter(prefix="/products/{product_id}/images/{image_id}/extractions", tags=["label-extractions"], dependencies=[Depends(require_image_api_key)])

class ExtractionCreate(BaseModel):
    model: str | None = None
    prompt_version: str = PROMPT_ID

def _service():
    try:
        storage = StorageSettings.from_env(); extraction = ExtractionSettings.from_env()
        return LabelExtractionService(get_storage_adapter(storage), storage, extraction)
    except RuntimeError as exc:
        raise HTTPException(503, {"code": "extraction_not_configured", "message": str(exc)}) from exc

def _call(function):
    try: return function()
    except ExtractionError as exc:
        detail = {"code": exc.code, "message": exc.message}
        if exc.run_id is not None: detail["run_id"] = exc.run_id
        raise HTTPException(exc.status, detail) from exc

@router.post("", status_code=201)
def create_extraction(product_id: int, image_id: int, payload: ExtractionCreate, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    return _call(lambda: _service().create(product_id, image_id, idempotency_key or "", payload.model, payload.prompt_version))

@router.get("")
def list_extractions(product_id: int, image_id: int): return _call(lambda: _service().list(product_id, image_id))

@router.get("/{run_id}")
def get_extraction(product_id: int, image_id: int, run_id: int): return _call(lambda: _service().get(product_id, image_id, run_id))
