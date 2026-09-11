import base64
import json
from typing import Any

from app.extraction.models import (
    ExtractionRequest,
    ProviderResult,
    TextNormalizationProviderRequest,
)
from .base import (
    ExtractionProvider,
    ProviderError,
    ProviderTimeout,
    TextNormalizationProvider,
)


class OpenAIExtractionProvider(ExtractionProvider):
    name = "openai"

    def __init__(self, api_key: str, timeout_seconds: int = 90, client: Any = None):
        if not api_key and client is None:
            raise RuntimeError("WYE_OPENAI_API_KEY is required")
        if client is None:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=1)
        self.client = client

    def extract(self, request: ExtractionRequest) -> ProviderResult:
        image = base64.b64encode(request.image_bytes).decode("ascii")
        try:
            response = self.client.responses.create(
                model=request.model,
                instructions=request.instructions,
                input=[{"role": "user", "content": [
                    {"type": "input_text", "text": "Extract the requested label data from this image."},
                    {"type": "input_image", "image_url": f"data:{request.mime_type};base64,{image}", "detail": "high"},
                ]}],
                text={"format": {"type": "json_schema", "name": "wye_label_extraction", "strict": True, "schema": request.output_schema}},
                store=False,
            )
        except Exception as exc:
            try:
                from openai import APITimeoutError
                if isinstance(exc, APITimeoutError):
                    raise ProviderTimeout("OpenAI request timed out") from exc
            except ImportError:
                pass
            raise ProviderError("OpenAI extraction request failed") from exc

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise ProviderError("OpenAI returned no structured output")
        try:
            output = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderError("OpenAI returned invalid JSON") from exc
        raw = response.model_dump(mode="json") if hasattr(response, "model_dump") else {"id": getattr(response, "id", None)}
        return ProviderResult(
            output=output,
            raw_response=raw,
            provider_request_id=getattr(response, "id", None),
            model_name=getattr(response, "model", None) or request.model,
        )


class OpenAITextNormalizationProvider(TextNormalizationProvider):
    billable_external = True
    name = "openai"

    def __init__(self, api_key: str, timeout_seconds: int = 90, client: Any = None):
        if not api_key and client is None:
            raise RuntimeError("WYE_OPENAI_API_KEY is required")
        if client is None:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                timeout=timeout_seconds,
                max_retries=1,
            )
        self.client = client

    def normalize_text(
        self, request: TextNormalizationProviderRequest
    ) -> ProviderResult:
        # The allowlisted request cannot carry images, product identifiers,
        # mobile capabilities, signed URLs, or application logs.
        input_payload = {
            "source_language": request.source_language,
            "document_type": request.document_type,
            "raw_text": request.raw_text,
            "target_language": request.target_language,
            "schema_version": request.schema_version,
            "parser_version": request.parser_version,
        }
        try:
            response = self.client.responses.create(
                model=request.model,
                instructions=request.instructions,
                input=[{
                    "role": "user",
                    "content": [{
                        "type": "input_text",
                        "text": json.dumps(input_payload, ensure_ascii=False),
                    }],
                }],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "wye_text_normalization",
                        "strict": True,
                        "schema": request.output_schema,
                    }
                },
                store=False,
            )
        except Exception as exc:
            try:
                from openai import APITimeoutError
                if isinstance(exc, APITimeoutError):
                    raise ProviderTimeout("OpenAI request timed out") from exc
            except ImportError:
                pass
            raise ProviderError("OpenAI text normalization failed") from exc

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise ProviderError("OpenAI returned no structured output")
        try:
            output = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderError("OpenAI returned invalid JSON") from exc
        raw = (
            response.model_dump(mode="json")
            if hasattr(response, "model_dump")
            else {"id": getattr(response, "id", None)}
        )
        return ProviderResult(
            output=output,
            raw_response=raw,
            provider_request_id=getattr(response, "id", None),
            model_name=getattr(response, "model", None) or request.model,
        )
