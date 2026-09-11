from typing import Any
from app.extraction.models import (
    ExtractionRequest,
    ProviderResult,
    TextNormalizationProviderRequest,
)
from .base import ExtractionProvider, TextNormalizationProvider


class FakeExtractionProvider(ExtractionProvider):
    name = "fake"

    def __init__(self, output: Any = None, error: Exception | None = None):
        self.output = output
        self.error = error
        self.requests: list[ExtractionRequest] = []

    def extract(self, request: ExtractionRequest) -> ProviderResult:
        self.requests.append(request)
        if self.error:
            raise self.error
        output = self.output
        if output is None:
            output = _local_e2e_output(request.document_type)
        return ProviderResult(
            output=output,
            raw_response={"fake": True},
            model_name=request.model,
        )


def _local_e2e_output(document_type: str) -> dict[str, Any]:
    if document_type == "ingredients":
        return {
            "document_type": "ingredients",
            "raw_text": "Local E2E fixture ingredient",
            "detected_languages": ["und"],
            "ingredient_list_text": "local e2e fixture ingredient",
            "ingredients": [
                {
                    "raw_text": "local e2e fixture ingredient",
                    "quantity": None,
                }
            ],
            "allergens": [],
            "nutrition": [],
        }
    return {
        "document_type": "nutrition",
        "raw_text": "Local E2E nutrition fixture",
        "detected_languages": ["und"],
        "ingredient_list_text": None,
        "ingredients": [],
        "allergens": [],
        "nutrition": [
            {
                "nutrient": "energy",
                "raw_label": "Local E2E fixture energy",
                "value": 0.0,
                "unit": "kJ",
                "basis": {
                    "type": "per_100_g",
                    "quantity": 100.0,
                    "unit": "g",
                    "raw_text": "per 100 g",
                },
            }
        ],
    }


class FakeTextNormalizationProvider(TextNormalizationProvider):
    name = "fake"

    def __init__(self, output: Any = None, error: Exception | None = None):
        self.output = output
        self.error = error
        self.requests: list[TextNormalizationProviderRequest] = []

    def normalize_text(
        self, request: TextNormalizationProviderRequest
    ) -> ProviderResult:
        self.requests.append(request)
        if self.error:
            raise self.error
        output = self.output or _conservative_text_output(request)
        return ProviderResult(
            output=output,
            raw_response={"fake": True},
            model_name=request.model,
        )


def _conservative_text_output(
    request: TextNormalizationProviderRequest,
) -> dict[str, Any]:
    if request.document_type == "ingredients":
        items = [
            value.strip()
            for value in request.raw_text.replace(";", ",").split(",")
            if value.strip()
        ]
        is_english = request.source_language.split("-", 1)[0] == "en"
        return {
            "detected_language": request.source_language,
            "source_segment": request.raw_text,
            "canonical_english_items": [
                {
                    "source_text": value,
                    "english_candidate": value if is_english else None,
                    "normalized_candidate": value.lower() if is_english else None,
                    "confidence": None,
                    "needs_review": True,
                    "correction_reason": None,
                    "allergen_emphasis": False,
                }
                for value in items
            ],
            "nutrition_items": [],
            "nutrition_basis": None,
            "warnings": ["fake_provider_requires_review"],
        }
    return {
        "detected_language": request.source_language,
        "source_segment": request.raw_text,
        "canonical_english_items": [],
        "nutrition_items": [],
        "nutrition_basis": None,
        "warnings": ["fake_provider_requires_review"],
    }
