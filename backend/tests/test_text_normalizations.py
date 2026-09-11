import json
import unittest

from app.extraction.config import ExtractionSettings
from app.extraction.models import TextNormalizationProviderRequest
from app.extraction.prompts.label_text_normalization_v1 import (
    PROMPT_ID,
    SCHEMA_VERSION,
    instructions_for,
    output_schema_for,
)
from app.extraction.providers import (
    FakeTextNormalizationProvider,
    OpenAITextNormalizationProvider,
)
from app.services.text_normalizations import (
    TextNormalizationError,
    TextNormalizationInput,
    TextNormalizationService,
)


def _settings(**overrides):
    values = {
        "provider": "fake",
        "openai_api_key": None,
        "model": "wye-local-e2e-fake-v1",
        "timeout_seconds": 2,
        "runtime_environment": "test",
        "text_fallback_enabled": True,
        "text_max_characters": 12000,
        "text_cache_entries": 8,
    }
    values.update(overrides)
    return ExtractionSettings(**values)


def _payload(raw_text="Ainesosat: vesi, sokeri", **overrides):
    values = {
        "source_language": "fi",
        "document_type": "ingredients",
        "raw_text": raw_text,
        "target_language": "en",
        "schema_version": "2",
        "parser_version": "photo_field_mapper_v3",
    }
    values.update(overrides)
    return TextNormalizationInput(**values)


def _finnish_output(source_segment="provider must not replace this"):
    return {
        "detected_language": "fi",
        "source_segment": source_segment,
        "canonical_english_items": [
            {
                "source_text": "vesi",
                "english_candidate": "water",
                "normalized_candidate": "water",
                "confidence": 0.99,
                "needs_review": False,
                "correction_reason": None,
                "allergen_emphasis": False,
            },
            {
                "source_text": "sokeri",
                "english_candidate": "sugar",
                "normalized_candidate": "sugar",
                "confidence": 0.98,
                "needs_review": False,
                "correction_reason": None,
                "allergen_emphasis": False,
            },
        ],
        "nutrition_items": [],
        "nutrition_basis": None,
        "warnings": [],
    }


class TextNormalizationServiceTests(unittest.TestCase):
    def test_ingredient_and_nutrition_use_distinct_closed_schemas(self):
        ingredient_schema = output_schema_for("ingredients")
        nutrition_schema = output_schema_for("nutrition")
        self.assertEqual(
            ingredient_schema["properties"]["nutrition_items"]["maxItems"], 0
        )
        self.assertEqual(
            nutrition_schema["properties"]["canonical_english_items"][
                "maxItems"
            ],
            0,
        )
        self.assertNotEqual(ingredient_schema, nutrition_schema)

    def test_fake_fallback_preserves_input_and_never_auto_verifies(self):
        raw = "Ainesosat: vesi, sokeri"
        provider = FakeTextNormalizationProvider(_finnish_output())
        result = TextNormalizationService(
            _settings(), provider=provider
        ).normalize(_payload(raw))

        self.assertEqual(result["source_segment"], raw)
        self.assertEqual(result["detected_language"], "fi")
        self.assertTrue(
            all(item["needs_review"] for item in result["canonical_english_items"])
        )
        self.assertTrue(result["provider_invoked"])
        self.assertFalse(result["cache_hit"])
        self.assertEqual(result["provenance"]["provider"], "fake")
        self.assertEqual(len(provider.requests), 1)
        request = provider.requests[0]
        self.assertEqual(request.raw_text, raw)
        self.assertFalse(hasattr(request, "image_bytes"))
        self.assertFalse(hasattr(request, "barcode"))
        self.assertFalse(hasattr(request, "product_id"))

    def test_cache_hit_does_not_invoke_provider_twice(self):
        provider = FakeTextNormalizationProvider(_finnish_output())
        service = TextNormalizationService(_settings(), provider=provider)

        first = service.normalize(_payload())
        second = service.normalize(_payload())

        self.assertFalse(first["cache_hit"])
        self.assertTrue(second["cache_hit"])
        self.assertFalse(second["provider_invoked"])
        self.assertEqual(len(provider.requests), 1)

    def test_fake_provider_does_not_authorize_billable_usage(self):
        provider = FakeTextNormalizationProvider(_finnish_output())
        authorizations = []
        TextNormalizationService(_settings(), provider=provider).normalize(
            _payload(),
            before_billable_call=lambda provider_name, model: authorizations.append(
                (provider_name, model)
            ),
        )
        self.assertEqual(authorizations, [])

    def test_cache_key_includes_language_and_document_type(self):
        provider = FakeTextNormalizationProvider(_finnish_output())
        service = TextNormalizationService(_settings(), provider=provider)
        service.normalize(_payload(source_language="fi"))
        service.normalize(_payload(source_language="sv"))
        self.assertEqual(len(provider.requests), 2)

    def test_disabled_fallback_never_calls_provider(self):
        provider = FakeTextNormalizationProvider(_finnish_output())
        service = TextNormalizationService(
            _settings(text_fallback_enabled=False), provider=provider
        )
        with self.assertRaises(TextNormalizationError) as caught:
            service.normalize(_payload())
        self.assertEqual(caught.exception.code, "text_fallback_disabled")
        self.assertEqual(provider.requests, [])

    def test_configured_text_limit_is_enforced_before_provider(self):
        provider = FakeTextNormalizationProvider(_finnish_output())
        service = TextNormalizationService(
            _settings(text_max_characters=10), provider=provider
        )
        with self.assertRaises(TextNormalizationError) as caught:
            service.normalize(_payload("a" * 11))
        self.assertEqual(caught.exception.code, "text_fallback_text_too_long")
        self.assertEqual(provider.requests, [])

    def test_invalid_mixed_provider_output_is_rejected(self):
        output = _finnish_output()
        output["nutrition_items"] = [
            {
                "canonical_key": "salt_g",
                "source_label": "suolaa",
                "source_value": "0,8",
                "source_unit": "g",
                "normalized_value": 0.8,
                "normalized_unit": "g",
                "confidence": 0.9,
                "needs_review": True,
            }
        ]
        provider = FakeTextNormalizationProvider(output)
        with self.assertRaises(TextNormalizationError) as caught:
            TextNormalizationService(_settings(), provider=provider).normalize(
                _payload()
            )
        self.assertEqual(caught.exception.code, "text_fallback_invalid_output")

    def test_logs_do_not_contain_ocr_text(self):
        raw = "private-ocr-marker mobile-token-marker"
        provider = FakeTextNormalizationProvider(_finnish_output())
        with self.assertLogs(
            "app.services.text_normalizations", level="INFO"
        ) as captured:
            TextNormalizationService(_settings(), provider=provider).normalize(
                _payload(raw)
            )
        logs = "\n".join(captured.output)
        self.assertNotIn(raw, logs)
        self.assertNotIn("mobile-token-marker", logs)


class _Response:
    id = "safe-request-id"
    model = "fake-model"
    output_text = json.dumps(_finnish_output())

    def model_dump(self, mode="json"):
        return {"id": self.id, "model": self.model}


class _Responses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _Response()


class _Client:
    def __init__(self):
        self.responses = _Responses()


class OpenAITextProviderContractTests(unittest.TestCase):
    def test_request_is_text_only_allowlisted_non_stored_and_single_retry_owned(self):
        client = _Client()
        provider = OpenAITextNormalizationProvider("", client=client)
        request = TextNormalizationProviderRequest(
            source_language="fi",
            document_type="ingredients",
            raw_text="Ainesosat: vesi, sokeri",
            target_language="en",
            schema_version=SCHEMA_VERSION,
            parser_version="photo_field_mapper_v3",
            prompt_version=PROMPT_ID,
            model="fake-model",
            instructions=instructions_for("ingredients"),
            output_schema=output_schema_for("ingredients"),
        )

        provider.normalize_text(request)
        self.assertEqual(len(client.responses.calls), 1)
        call = client.responses.calls[0]
        self.assertFalse(call["store"])
        content = call["input"][0]["content"]
        self.assertEqual([part["type"] for part in content], ["input_text"])
        sent = json.loads(content[0]["text"])
        self.assertEqual(
            set(sent),
            {
                "source_language",
                "document_type",
                "raw_text",
                "target_language",
                "schema_version",
                "parser_version",
            },
        )
        serialized = json.dumps(call)
        for forbidden in (
            "input_image",
            "barcode",
            "product_id",
            "access_token",
            "presigned",
            "data:image",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_real_external_provider_authorizes_once_and_cache_hit_is_free(self):
        client = _Client()
        provider = OpenAITextNormalizationProvider("", client=client)
        service = TextNormalizationService(
            _settings(provider="openai"), provider=provider
        )
        authorizations = []
        callback = lambda provider_name, model: authorizations.append(
            (provider_name, model)
        )
        service.normalize(_payload(), before_billable_call=callback)
        service.normalize(_payload(), before_billable_call=callback)
        self.assertEqual(authorizations, [("openai", "wye-local-e2e-fake-v1")])
        self.assertEqual(len(client.responses.calls), 1)


if __name__ == "__main__":
    unittest.main()
