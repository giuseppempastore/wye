import hashlib
import logging
import threading
from collections.abc import Callable
from collections import OrderedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.extraction.config import (
    LOCAL_FAKE_RUNTIME_ENVIRONMENTS,
    ExtractionSettings,
)
from app.extraction.models import (
    IngredientTextNormalizationOutput,
    NutritionTextNormalizationOutput,
    TextNormalizationOutput,
    TextNormalizationProviderRequest,
)
from app.extraction.prompts.label_text_normalization_v1 import (
    PROMPT_HASH,
    PROMPT_ID,
    SCHEMA_VERSION,
    instructions_for,
    output_schema_for,
)
from app.extraction.providers import (
    FakeTextNormalizationProvider,
    OpenAITextNormalizationProvider,
    ProviderError,
    ProviderTimeout,
)


logger = logging.getLogger(__name__)


class TextNormalizationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_language: str = Field(
        max_length=10,
        pattern=r"^(?:und|[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)$"
    )
    document_type: str = Field(pattern=r"^(?:ingredients|nutrition)$")
    raw_text: str = Field(min_length=1, max_length=12000)
    target_language: str = Field(default="en", pattern=r"^en$")
    schema_version: str = Field(default=SCHEMA_VERSION, pattern=r"^2$")
    parser_version: str = Field(pattern=r"^[a-z0-9_.-]{1,80}$")


class TextNormalizationError(RuntimeError):
    def __init__(self, code: str, message: str, status: int):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


def text_provider_from_settings(settings: ExtractionSettings):
    if settings.provider == "openai":
        return OpenAITextNormalizationProvider(
            settings.openai_api_key or "", settings.timeout_seconds
        )
    if settings.provider == "fake":
        if settings.runtime_environment not in LOCAL_FAKE_RUNTIME_ENVIRONMENTS:
            raise RuntimeError(
                "Fake text normalization is restricted to local/dev/test/e2e"
            )
        return FakeTextNormalizationProvider()
    raise RuntimeError("Unsupported text normalization provider")


class TextNormalizationService:
    def __init__(self, settings: ExtractionSettings, provider=None):
        if settings.text_max_characters > 12000:
            raise RuntimeError(
                "WYE_TEXT_NORMALIZATION_MAX_CHARACTERS must not exceed 12000"
            )
        if settings.text_cache_entries > 4096:
            raise RuntimeError(
                "WYE_TEXT_NORMALIZATION_CACHE_ENTRIES must not exceed 4096"
            )
        self.settings = settings
        self.provider = provider
        if self.provider is None and settings.text_fallback_enabled:
            self.provider = text_provider_from_settings(settings)
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._lock = threading.Lock()

    def normalize(
        self,
        payload: TextNormalizationInput,
        before_billable_call: Callable[[str, str], None] | None = None,
    ) -> dict:
        if not self.settings.text_fallback_enabled:
            logger.info("text_normalization outcome=disabled")
            raise TextNormalizationError(
                "text_fallback_disabled",
                "Text normalization fallback is disabled",
                503,
            )
        if len(payload.raw_text) > self.settings.text_max_characters:
            logger.info("text_normalization outcome=reject reason=text_too_long")
            raise TextNormalizationError(
                "text_fallback_text_too_long",
                "OCR segment exceeds the configured text limit",
                413,
            )
        if self.provider is None:
            raise TextNormalizationError(
                "text_fallback_unavailable",
                "Text normalization fallback is unavailable",
                503,
            )

        fingerprint = self._fingerprint(payload)
        with self._lock:
            cached = self._cache.get(fingerprint)
            if cached is not None:
                self._cache.move_to_end(fingerprint)
                logger.info("text_normalization outcome=cache_hit")
                return {**cached, "cache_hit": True, "provider_invoked": False}

        if (
            self.provider.billable_external
            and before_billable_call is not None
        ):
            before_billable_call(self.provider.name, self.settings.model)

        request = TextNormalizationProviderRequest(
            source_language=payload.source_language,
            document_type=payload.document_type,
            raw_text=payload.raw_text,
            target_language=payload.target_language,
            schema_version=payload.schema_version,
            parser_version=payload.parser_version,
            prompt_version=PROMPT_ID,
            model=self.settings.model,
            instructions=instructions_for(payload.document_type),
            output_schema=output_schema_for(payload.document_type),
        )
        try:
            logger.info(
                "text_normalization outcome=provider_request provider=%s",
                self.provider.name,
            )
            result = self.provider.normalize_text(request)
            output_model = (
                IngredientTextNormalizationOutput
                if payload.document_type == "ingredients"
                else NutritionTextNormalizationOutput
            )
            output: TextNormalizationOutput = output_model.model_validate(
                result.output
            )
        except ProviderTimeout as exc:
            raise TextNormalizationError(
                "text_fallback_timeout", "Text normalization timed out", 504
            ) from exc
        except ProviderError as exc:
            raise TextNormalizationError(
                "text_fallback_provider_error",
                "Text normalization provider failed",
                502,
            ) from exc
        except (ValidationError, ValueError) as exc:
            raise TextNormalizationError(
                "text_fallback_invalid_output",
                "Text normalization output failed validation",
                502,
            ) from exc

        detected_language = (
            payload.source_language
            if payload.source_language != "und"
            else output.detected_language
        )
        safe_output = output.model_copy(
            update={
                "detected_language": detected_language,
                "source_segment": payload.raw_text,
                "canonical_english_items": [
                    item.model_copy(update={"needs_review": True})
                    for item in output.canonical_english_items
                ],
                "nutrition_items": [
                    item.model_copy(update={"needs_review": True})
                    for item in output.nutrition_items
                ],
            }
        ).model_dump(mode="json")
        safe_result = {
            **safe_output,
            "provenance": {
                "provider": self.provider.name,
                "model_name": result.model_name,
                "model_version": result.model_version,
                "prompt_version": PROMPT_ID,
                "schema_version": payload.schema_version,
                "parser_version": payload.parser_version,
            },
        }
        with self._lock:
            self._cache[fingerprint] = safe_result
            self._cache.move_to_end(fingerprint)
            while len(self._cache) > self.settings.text_cache_entries:
                self._cache.popitem(last=False)
        return {**safe_result, "cache_hit": False, "provider_invoked": True}

    def _fingerprint(self, payload: TextNormalizationInput) -> str:
        segment_hash = hashlib.sha256(payload.raw_text.encode("utf-8")).hexdigest()
        values = (
            segment_hash,
            payload.source_language,
            payload.document_type,
            payload.target_language,
            payload.schema_version,
            payload.parser_version,
            PROMPT_ID,
            PROMPT_HASH,
            self.provider.name,
            self.settings.model,
        )
        return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()
