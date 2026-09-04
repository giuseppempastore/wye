from typing import Any
from app.extraction.models import ExtractionRequest, ProviderResult
from .base import ExtractionProvider


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
