from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import psycopg2.extras
from app.db import get_connection
from app.security import require_image_api_key
from app.services.image_uploads import ImageUploadService, UploadError
from app.storage import StorageSettings, get_storage_adapter

router=APIRouter(prefix="/products/{product_id}/images",tags=["product-images"],dependencies=[Depends(require_image_api_key)])
class InitUpload(BaseModel):
    image_type: str; mime_type: str; byte_size: int=Field(gt=0); sha256: str
def _service():
    try:
        settings=StorageSettings.from_env(); return ImageUploadService(get_storage_adapter(settings),settings)
    except RuntimeError as e: raise HTTPException(503,str(e))
def _call(fn):
    try: return fn()
    except UploadError as e: raise HTTPException(e.status,{"code":e.code,"message":e.message})
@router.post("/uploads",status_code=201)
def initialize_upload(product_id:int,payload:InitUpload): return _call(lambda:_service().initialize(product_id,payload.image_type,payload.mime_type,payload.byte_size,payload.sha256))
@router.post("/uploads/{upload_id}/finalize")
def finalize_upload(product_id:int,upload_id:str): return _call(lambda:_service().finalize(product_id,upload_id))
@router.get("")
def list_images(product_id:int):
    conn=get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT pi.id,pi.image_type,pi.mime_type,pi.byte_size,pi.checksum,pi.status,pi.is_current,pi.created_at,pi.superseded_at,pi.superseded_by_image_id,so.storage_provider FROM product_images pi LEFT JOIN storage_objects so ON so.id=pi.storage_object_id WHERE pi.product_id=%s ORDER BY pi.created_at DESC,pi.id DESC",(product_id,)); return {"images":cur.fetchall()}
    finally: conn.close()
@router.get("/{image_id}/access")
def image_access(product_id:int,image_id:int):
    settings=StorageSettings.from_env(); conn=get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT so.object_key FROM product_images pi JOIN storage_objects so ON so.id=pi.storage_object_id WHERE pi.id=%s AND pi.product_id=%s",(image_id,product_id)); row=cur.fetchone()
            if not row: raise HTTPException(404,"Image not found")
        return {"url":get_storage_adapter(settings).generate_read_url(row["object_key"],settings.read_ttl),"expires_at":datetime.now(timezone.utc)+timedelta(seconds=settings.read_ttl)}
    finally: conn.close()
