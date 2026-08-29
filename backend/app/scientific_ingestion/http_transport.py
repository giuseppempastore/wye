"""Small provider-neutral HTTP boundary for scientific artifact acquisition."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import logging
import random
import time
from typing import Callable, Mapping
from urllib.parse import urljoin, urlsplit

import httpx

from .errors import ScientificAcquisitionError


class HttpPolicyError(ScientificAcquisitionError):
    pass


class HttpResponseError(ScientificAcquisitionError):
    def __init__(self, status_code: int):
        super().__init__(f"remote server returned HTTP {status_code}")
        self.status_code = status_code


class HttpContentError(ScientificAcquisitionError):
    pass


@dataclass(frozen=True)
class HttpTimeouts:
    connect_seconds: float = 10.0
    read_seconds: float = 30.0


@dataclass(frozen=True)
class HttpRetryPolicy:
    max_attempts: int = 3
    base_backoff_seconds: float = 0.5
    max_backoff_seconds: float = 10.0
    jitter_ratio: float = 0.2


@dataclass(frozen=True)
class HttpRequest:
    url: str
    allowed_hosts: frozenset[str]
    headers: Mapping[str, str] = field(default_factory=dict)
    max_bytes: int = 5 * 1024 * 1024
    max_redirects: int = 2


@dataclass(frozen=True)
class HttpResponse:
    url: str
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    attempts: int
    elapsed_seconds: float


@dataclass(frozen=True)
class HttpAttemptResponse:
    url: str
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class HttpxAttemptExecutor:
    """One non-redirecting streaming request; retry policy lives above it."""

    def __call__(self, url, headers, timeouts, max_bytes):
        timeout = httpx.Timeout(
            connect=timeouts.connect_seconds,
            read=timeouts.read_seconds,
            write=timeouts.read_seconds,
            pool=timeouts.connect_seconds,
        )
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            with client.stream("GET", url, headers=dict(headers)) as response:
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > max_bytes:
                        raise HttpContentError("response exceeds configured maximum bytes")
                    chunks.append(chunk)
                body = b"".join(chunks)
                return HttpAttemptResponse(
                    str(response.url), response.status_code,
                    {key.lower(): value for key, value in response.headers.items()}, body,
                )


class ControlledHttpTransport:
    RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
    REDIRECT_STATUSES = frozenset({301, 302, 307, 308})

    def __init__(self, *, executor=None, timeouts=HttpTimeouts(),
                 retry_policy=HttpRetryPolicy(), sleep: Callable[[float], None] = time.sleep,
                 random_value: Callable[[], float] = random.random, logger=None):
        self.executor = executor or HttpxAttemptExecutor()
        self.timeouts = timeouts
        self.retry_policy = retry_policy
        self.sleep = sleep
        self.random_value = random_value
        self.logger = logger or logging.getLogger(__name__)

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.max_bytes <= 0 or self.retry_policy.max_attempts < 1:
            raise HttpPolicyError("invalid transport limits")
        current_url = request.url
        redirects = 0
        attempts = 0
        started = time.monotonic()
        while True:
            self._validate_url(current_url, request.allowed_hosts)
            attempts += 1
            try:
                response = self.executor(
                    current_url, request.headers, self.timeouts, request.max_bytes
                )
                self._validate_body(response, request.max_bytes)
            except HttpContentError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
                if attempts >= self.retry_policy.max_attempts:
                    raise ScientificAcquisitionError("remote connection failed after bounded retries") from exc
                self._sleep_backoff(attempts, None)
                continue
            if response.status_code in self.REDIRECT_STATUSES:
                location = response.headers.get("location")
                if not location or redirects >= request.max_redirects:
                    raise HttpPolicyError("redirect policy rejected response")
                current_url = urljoin(current_url, location)
                self._validate_url(current_url, request.allowed_hosts)
                redirects += 1
                continue
            if response.status_code != 200:
                if (response.status_code in self.RETRYABLE_STATUSES
                        and attempts < self.retry_policy.max_attempts):
                    self._sleep_backoff(attempts, response.headers.get("retry-after"))
                    continue
                raise HttpResponseError(response.status_code)
            elapsed = time.monotonic() - started
            self.logger.info("scientific_http_acquired", extra={
                "provider": "scientific", "attempt_number": attempts,
                "status": response.status_code, "elapsed_seconds": elapsed,
                "bytes": len(response.body), "result": "success",
            })
            return HttpResponse(response.url, response.status_code, response.headers,
                                response.body, attempts, elapsed)

    @staticmethod
    def _validate_url(url, allowed_hosts):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise HttpPolicyError("only credential-free HTTPS locators are allowed")
        host = (parsed.hostname or "").lower()
        if host not in {item.lower() for item in allowed_hosts}:
            raise HttpPolicyError("remote host is not allow-listed")

    @staticmethod
    def _validate_body(response, max_bytes):
        if len(response.body) > max_bytes:
            raise HttpContentError("response exceeds configured maximum bytes")
        value = response.headers.get("content-length")
        if value is not None:
            try:
                expected = int(value)
            except ValueError as exc:
                raise HttpContentError("invalid Content-Length") from exc
            if expected != len(response.body):
                raise HttpContentError("Content-Length does not match acquired bytes")

    def _sleep_backoff(self, attempts, retry_after):
        delay = self._retry_after_seconds(retry_after)
        if delay is None:
            raw = self.retry_policy.base_backoff_seconds * (2 ** (attempts - 1))
            jitter = raw * self.retry_policy.jitter_ratio * self.random_value()
            delay = min(self.retry_policy.max_backoff_seconds, raw + jitter)
        self.sleep(min(delay, self.retry_policy.max_backoff_seconds))

    @staticmethod
    def _retry_after_seconds(value):
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                when = parsedate_to_datetime(value)
                return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None
