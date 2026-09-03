import hashlib
import secrets
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, FrozenSet


class MobileSessionError(RuntimeError):
    def __init__(self, code: str, message: str, status: int):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


@dataclass(frozen=True)
class MobileSessionRecord:
    session_id: str
    token_digest: str
    scopes: FrozenSet[str]
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True, repr=False)
class IssuedMobileSession:
    token: str
    record: MobileSessionRecord

    def __repr__(self) -> str:
        return (
            "IssuedMobileSession(token=<redacted>, "
            f"session_id={self.record.session_id!r}, "
            f"expires_at={self.record.expires_at!r})"
        )


class MobileUploadSessionStore:
    """Process-local, dev-only capability store that retains token digests only."""

    SUPPORTED_SCOPES = frozenset({"upload", "extraction"})
    MIN_TTL_SECONDS = 30
    MAX_TTL_SECONDS = 900

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
        token_factory: Callable[[], str] | None = None,
    ):
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._token_factory = token_factory or (
            lambda: f"wye_dev_{secrets.token_urlsafe(32)}"
        )
        self._records: dict[str, MobileSessionRecord] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def issue(self, scopes: set[str], ttl_seconds: int) -> IssuedMobileSession:
        normalized = frozenset(scopes)
        if not normalized or not normalized.issubset(self.SUPPORTED_SCOPES):
            raise MobileSessionError(
                "mobile_session_scope_invalid",
                "At least one supported mobile facade scope is required",
                422,
            )
        if not self.MIN_TTL_SECONDS <= ttl_seconds <= self.MAX_TTL_SECONDS:
            raise MobileSessionError(
                "mobile_session_ttl_invalid",
                "Mobile session TTL must be between 30 and 900 seconds",
                422,
            )

        now = self._clock()
        token = self._token_factory()
        digest = self._digest(token)
        record = MobileSessionRecord(
            session_id=uuid.uuid4().hex,
            token_digest=digest,
            scopes=normalized,
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        with self._lock:
            self._remove_expired(now)
            if digest in self._records:
                raise RuntimeError("Mobile session token collision")
            self._records[digest] = record
        return IssuedMobileSession(token=token, record=record)

    def validate(self, token: str, required_scope: str) -> MobileSessionRecord:
        if not token or len(token) > 512:
            raise MobileSessionError(
                "mobile_session_invalid", "Mobile session is invalid", 401
            )
        now = self._clock()
        digest = self._digest(token)
        with self._lock:
            record = self._records.get(digest)
            if record is None:
                raise MobileSessionError(
                    "mobile_session_invalid", "Mobile session is invalid", 401
                )
            if record.expires_at <= now:
                del self._records[digest]
                raise MobileSessionError(
                    "mobile_session_expired", "Mobile session has expired", 401
                )
            if required_scope not in record.scopes:
                raise MobileSessionError(
                    "mobile_session_scope_denied",
                    "Mobile session does not grant this operation",
                    403,
                )
            return record

    def revoke(self, token: str) -> None:
        if not token or len(token) > 512:
            return
        with self._lock:
            self._records.pop(self._digest(token), None)

    def _remove_expired(self, now: datetime) -> None:
        expired = [
            digest
            for digest, record in self._records.items()
            if record.expires_at <= now
        ]
        for digest in expired:
            del self._records[digest]
