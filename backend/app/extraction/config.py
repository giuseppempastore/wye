import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise RuntimeError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class ExtractionSettings:
    provider: str
    openai_api_key: str | None
    model: str
    timeout_seconds: int

    @classmethod
    def from_env(cls):
        provider = os.getenv("WYE_EXTRACTION_PROVIDER", "openai").strip().lower()
        if provider not in {"openai"}:
            raise RuntimeError("WYE_EXTRACTION_PROVIDER must be openai")
        return cls(
            provider=provider,
            openai_api_key=os.getenv("WYE_OPENAI_API_KEY") or None,
            model=os.getenv("WYE_OPENAI_EXTRACTION_MODEL", "gpt-4o-mini").strip(),
            timeout_seconds=_positive_int("WYE_EXTRACTION_TIMEOUT_SECONDS", 90),
        )
