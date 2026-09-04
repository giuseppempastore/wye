import os
from dataclasses import dataclass


LOCAL_FAKE_RUNTIME_ENVIRONMENTS = frozenset(
    {"local", "dev", "development", "test", "e2e"}
)
VALID_RUNTIME_ENVIRONMENTS = LOCAL_FAKE_RUNTIME_ENVIRONMENTS | {
    "staging",
    "production",
}


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
    runtime_environment: str = "production"

    @classmethod
    def from_env(cls):
        runtime_environment = os.getenv(
            "WYE_RUNTIME_ENVIRONMENT", "production"
        ).strip().lower()
        if runtime_environment not in VALID_RUNTIME_ENVIRONMENTS:
            raise RuntimeError(
                "WYE_RUNTIME_ENVIRONMENT must be local, dev, development, "
                "test, e2e, staging, or production"
            )
        provider = os.getenv("WYE_EXTRACTION_PROVIDER", "openai").strip().lower()
        if provider not in {"openai", "fake"}:
            raise RuntimeError("WYE_EXTRACTION_PROVIDER must be openai or fake")
        if (
            provider == "fake"
            and runtime_environment not in LOCAL_FAKE_RUNTIME_ENVIRONMENTS
        ):
            raise RuntimeError(
                "Fake extraction is restricted to explicit local/dev/test/e2e "
                "runtime environments"
            )
        return cls(
            provider=provider,
            openai_api_key=(
                os.getenv("WYE_OPENAI_API_KEY") or None
                if provider == "openai"
                else None
            ),
            model=(
                os.getenv("WYE_OPENAI_EXTRACTION_MODEL", "gpt-4o-mini").strip()
                if provider == "openai"
                else "wye-local-e2e-fake-v1"
            ),
            timeout_seconds=_positive_int("WYE_EXTRACTION_TIMEOUT_SECONDS", 90),
            runtime_environment=runtime_environment,
        )
