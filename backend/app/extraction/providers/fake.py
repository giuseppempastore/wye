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
        return ProviderResult(output=self.output, raw_response={"fake": True}, model_name=request.model)
