import hashlib
import json
import tempfile
from typing import Any, Callable

import psycopg2.extras
from pydantic import ValidationError

from app.db import get_connection
from app.extraction.config import (
    LOCAL_FAKE_RUNTIME_ENVIRONMENTS,
    ExtractionSettings,
)
from app.extraction.models import ExtractionRequest, LabelExtractionOutput
from app.extraction.prompts.label_extraction_v1 import OUTPUT_SCHEMA, PROMPT_HASH, PROMPT_ID, SCHEMA_VERSION, instructions_for
from app.extraction.providers import (
    FakeExtractionProvider,
    OpenAIExtractionProvider,
    ProviderError,
    ProviderTimeout,
)


class ExtractionError(RuntimeError):
    def __init__(self, code: str, message: str, status: int, run_id: int | None = None):
        self.code, self.message, self.status, self.run_id = code, message, status, run_id


def provider_from_settings(settings: ExtractionSettings):
    if settings.provider == "openai":
        return OpenAIExtractionProvider(settings.openai_api_key or "", settings.timeout_seconds)
    if settings.provider == "fake":
        if settings.runtime_environment not in LOCAL_FAKE_RUNTIME_ENVIRONMENTS:
            raise RuntimeError(
                "Fake extraction is restricted to explicit local/dev/test/e2e "
                "runtime environments"
            )
        return FakeExtractionProvider()
    raise RuntimeError("Unsupported extraction provider")


class LabelExtractionService:
    def __init__(self, adapter, storage_settings, extraction_settings, provider=None, connection_factory: Callable = get_connection):
        self.adapter = adapter
        self.storage_settings = storage_settings
        self.settings = extraction_settings
        self.provider = provider or provider_from_settings(extraction_settings)
        self.connection_factory = connection_factory

    def create(self, product_id: int, image_id: int, idempotency_key: str, model: str | None = None, prompt_version: str = PROMPT_ID) -> dict:
        key = (idempotency_key or "").strip()
        if not key or len(key) > 255:
            raise ExtractionError("invalid_request", "Idempotency-Key is required and must be at most 255 characters", 422)
        if prompt_version != PROMPT_ID:
            raise ExtractionError("invalid_request", "Unsupported prompt version", 422)
        model = (model or self.settings.model).strip()
        if not model:
            raise ExtractionError("invalid_request", "Model must not be empty", 422)

        image = self._get_image(product_id, image_id)
        document_type = image["image_type"]
        if document_type not in {"ingredients", "nutrition"}:
            raise ExtractionError("unsupported_image_type", "Only ingredients and nutrition images are supported", 422)
        fingerprint = hashlib.sha256("\0".join((image["checksum"], document_type, self.provider.name, model, PROMPT_ID, SCHEMA_VERSION)).encode()).hexdigest()
        document_id, existing = self._create_pending_run(image_id, document_type, key, fingerprint, model)
        if existing:
            if existing["request_fingerprint"] != fingerprint:
                raise ExtractionError("idempotency_conflict", "Idempotency-Key was already used for a different request", 409, existing["id"])
            return self.get(product_id, image_id, existing["id"])
        run_id = document_id[1]
        document_id = document_id[0]

        try:
            self._mark_running(run_id)
            with tempfile.SpooledTemporaryFile(max_size=min(self.storage_settings.max_image_bytes, 2 * 1024 * 1024)) as tmp:
                self.adapter.download_to(image["object_key"], tmp)
                size = tmp.tell()
                if size <= 0 or size > self.storage_settings.max_image_bytes:
                    raise ExtractionError("image_storage_unavailable", "Stored image size is invalid", 503, run_id)
                tmp.seek(0)
                image_bytes = tmp.read()
            request = ExtractionRequest(
                image_bytes=image_bytes, mime_type=image["mime_type"], document_type=document_type,
                model=model, prompt_version=PROMPT_ID, schema_version=SCHEMA_VERSION,
                instructions=instructions_for(document_type), output_schema=OUTPUT_SCHEMA,
            )
            result = self.provider.extract(request)
            output = LabelExtractionOutput.model_validate(result.output)
            if output.document_type != document_type:
                raise ValueError("Provider document type does not match source image type")
            self._succeed(run_id, output, result)
            return self.get(product_id, image_id, run_id)
        except ProviderTimeout as exc:
            self._fail(run_id, "provider_timeout", str(exc))
            raise ExtractionError("provider_timeout", "Extraction provider timed out", 504, run_id) from exc
        except ProviderError as exc:
            self._fail(run_id, "provider_error", str(exc))
            raise ExtractionError("provider_error", "Extraction provider failed", 502, run_id) from exc
        except (ValidationError, ValueError) as exc:
            self._fail(run_id, "invalid_provider_output", str(exc))
            raise ExtractionError("invalid_provider_output", "Provider output failed validation", 502, run_id) from exc
        except ExtractionError as exc:
            self._fail(run_id, exc.code, exc.message)
            raise
        except Exception as exc:
            self._fail(run_id, "image_storage_unavailable", type(exc).__name__)
            raise ExtractionError("image_storage_unavailable", "Image could not be read from private storage", 503, run_id) from exc

    def _get_image(self, product_id: int, image_id: int) -> dict:
        conn = self.connection_factory()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""SELECT pi.id,pi.image_type,pi.mime_type,pi.checksum,so.object_key
                    FROM product_images pi JOIN storage_objects so ON so.id=pi.storage_object_id
                    WHERE pi.id=%s AND pi.product_id=%s""", (image_id, product_id))
                row = cur.fetchone()
                if not row:
                    raise ExtractionError("image_not_found", "Image not found for product", 404)
                return dict(row)
        finally:
            conn.close()

    def _create_pending_run(self, image_id, document_type, key, fingerprint, model):
        conn = self.connection_factory()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""INSERT INTO product_label_documents(product_image_id,raw_text,source_type,document_type)
                    VALUES(%s,NULL,'image_derived',%s) ON CONFLICT DO NOTHING RETURNING id""", (image_id, document_type))
                found = cur.fetchone()
                if found: document_id = found["id"]
                else:
                    cur.execute("SELECT id FROM product_label_documents WHERE product_image_id=%s AND document_type=%s AND source_type='image_derived'", (image_id, document_type))
                    document_id = cur.fetchone()["id"]
                cur.execute("SELECT * FROM label_extraction_runs WHERE label_document_id=%s AND idempotency_key=%s", (document_id, key))
                existing = cur.fetchone()
                if existing:
                    conn.commit(); return (document_id, existing["id"]), dict(existing)
                cur.execute("""INSERT INTO label_extraction_runs(label_document_id,extraction_method,provider,model_name,prompt_version,
                    schema_version,prompt_hash,idempotency_key,request_fingerprint,run_status)
                    VALUES(%s,'ai',%s,%s,%s,%s,%s,%s,%s,'pending')
                    ON CONFLICT (label_document_id,idempotency_key) WHERE idempotency_key IS NOT NULL
                    DO NOTHING RETURNING id""",
                    (document_id, self.provider.name, model, PROMPT_ID, SCHEMA_VERSION, PROMPT_HASH, key, fingerprint))
                inserted = cur.fetchone()
                if not inserted:
                    cur.execute("SELECT * FROM label_extraction_runs WHERE label_document_id=%s AND idempotency_key=%s", (document_id, key))
                    existing = dict(cur.fetchone())
                    conn.commit()
                    return (document_id, existing["id"]), existing
                run_id = inserted["id"]
            conn.commit(); return (document_id, run_id), None
        except Exception:
            conn.rollback(); raise
        finally:
            conn.close()

    def _mark_running(self, run_id):
        self._update("UPDATE label_extraction_runs SET run_status='running',started_at=NOW() WHERE id=%s AND run_status='pending'", (run_id,))

    def _fail(self, run_id, code, detail):
        self._update("""UPDATE label_extraction_runs SET run_status='failed',error_code=%s,error_detail=%s,
            completed_at=NOW() WHERE id=%s AND run_status IN ('pending','running')""", (code, detail[:2000], run_id))

    def _update(self, sql, values):
        conn = self.connection_factory()
        try:
            with conn.cursor() as cur: cur.execute(sql, values)
            conn.commit()
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def _succeed(self, run_id, output, result):
        conn = self.connection_factory()
        try:
            with conn.cursor() as cur:
                items = []
                languages = output.detected_languages
                language = languages[0] if len(languages) == 1 else None
                if output.document_type == "ingredients":
                    items.append(("ingredient_list", output.ingredient_list_text, None, {"detected_languages": languages}, None, 0))
                    for pos, item in enumerate(output.ingredients, 1):
                        items.append(("ingredient", item.raw_text, None, {"quantity": item.quantity} if item.quantity else {}, None, pos))
                    for item in output.allergens:
                        items.append(("allergen", item.raw_text, None, {}, None, None))
                else:
                    for pos, item in enumerate(output.nutrition, 1):
                        structured = item.model_dump(mode="json")
                        items.append(("nutrition", item.raw_label, None, structured, item.unit, pos))
                for item_type, raw_text, normalized, structured, unit, position in items:
                    cur.execute("""INSERT INTO label_extraction_items(extraction_run_id,item_type,raw_text,normalized_text,
                        detected_language,structured_value,unit,position_in_document,extraction_status)
                        VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,'detected')""",
                        (run_id,item_type,raw_text,normalized,language,json.dumps(structured),unit,position))
                cur.execute("""UPDATE label_extraction_runs SET run_status='succeeded',extracted_raw_text=%s,
                    raw_response=%s::jsonb,provider_request_id=%s,model_name=%s,model_version=%s,completed_at=NOW()
                    WHERE id=%s AND run_status='running'""",
                    (output.raw_text,json.dumps(result.raw_response) if result.raw_response is not None else None,
                     result.provider_request_id,result.model_name,result.model_version,run_id))
            conn.commit()
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def list(self, product_id: int, image_id: int) -> dict:
        self._get_image(product_id, image_id)
        conn = self.connection_factory()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""SELECT r.* FROM label_extraction_runs r JOIN product_label_documents d ON d.id=r.label_document_id
                    WHERE d.product_image_id=%s ORDER BY r.created_at DESC,r.id DESC""", (image_id,))
                return {"extractions": cur.fetchall()}
        finally: conn.close()

    def get(self, product_id: int, image_id: int, run_id: int) -> dict:
        self._get_image(product_id, image_id)
        conn = self.connection_factory()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""SELECT r.* FROM label_extraction_runs r JOIN product_label_documents d ON d.id=r.label_document_id
                    WHERE r.id=%s AND d.product_image_id=%s""", (run_id, image_id))
                run = cur.fetchone()
                if not run: raise ExtractionError("extraction_not_found", "Extraction run not found", 404)
                cur.execute("SELECT * FROM label_extraction_items WHERE extraction_run_id=%s ORDER BY position_in_document NULLS LAST,id", (run_id,))
                return {"extraction": run, "items": cur.fetchall()}
        finally: conn.close()
