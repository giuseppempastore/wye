import os
from dataclasses import dataclass


class MobileFacadeConfigError(RuntimeError):
    pass


def _boolean(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise MobileFacadeConfigError(f"{name} must be a boolean")


def _bounded_integer(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise MobileFacadeConfigError(f"{name} must be an integer") from exc
    if value < minimum or value > maximum:
        raise MobileFacadeConfigError(
            f"{name} must be between {minimum} and {maximum}"
        )
    return value


@dataclass(frozen=True)
class MobileFacadeSettings:
    enabled: bool
    session_ttl_seconds: int

    @classmethod
    def from_env(cls) -> "MobileFacadeSettings":
        return cls(
            enabled=_boolean("WYE_MOBILE_UPLOAD_FACADE_ENABLED"),
            session_ttl_seconds=_bounded_integer(
                "WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS",
                default=300,
                minimum=30,
                maximum=900,
            ),
        )
