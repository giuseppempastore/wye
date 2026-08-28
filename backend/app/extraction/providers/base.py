from abc import ABC, abstractmethod
from app.extraction.models import ExtractionRequest, ProviderResult


class ProviderError(RuntimeError):
    code = "provider_error"


class ProviderTimeout(ProviderError):
    code = "provider_timeout"


class ExtractionProvider(ABC):
    name: str

    @abstractmethod
    def extract(self, request: ExtractionRequest) -> ProviderResult: ...
