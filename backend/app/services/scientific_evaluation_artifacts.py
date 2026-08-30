"""Deterministic writer for canonical scientific evaluation artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any
from uuid import uuid4

from app.repositories.scientific_evaluation_artifacts import (
    PostgresScientificArtifactRepository,
    ScientificArtifactLocationRow,
    ScientificArtifactRow,
)
from app.scientific_evaluation.artifact_contracts import build_artifact_envelope
from app.scientific_evaluation.canonicalization import (
    CANONICALIZATION_VERSION,
    DIGEST_ALGORITHM,
    MEDIA_TYPE,
    canonicalize_json,
)
from app.scientific_evaluation.errors import (
    ArtifactBytesUnavailableError,
    ArtifactIntegrityError,
    IncompatibleArtifactError,
    InvalidArtifactLocationError,
)


@dataclass(frozen=True)
class ScientificArtifactWriteRequest:
    artifact_kind: str
    schema_version: str
    payload: dict[str, Any]
    canonicalization_version: str = CANONICALIZATION_VERSION
    content_type: str = MEDIA_TYPE


@dataclass(frozen=True)
class PersistedScientificArtifact:
    artifact: ScientificArtifactRow
    location: ScientificArtifactLocationRow
    canonical_bytes: bytes
    artifact_reused: bool
    location_reused: bool


class ScientificArtifactWriter:
    """Write/reuse one canonical artifact inside a caller-owned transaction.

    The method never commits or rolls back. Inline placement is the deliberately
    small Phase 7.6.3A runtime substrate; remote object upload remains deferred.
    """

    def __init__(self, repository: PostgresScientificArtifactRepository | None = None):
        self.repository = repository or PostgresScientificArtifactRepository()

    def write_verified_inline(
        self,
        cursor,
        request: ScientificArtifactWriteRequest,
    ) -> PersistedScientificArtifact:
        envelope = build_artifact_envelope(
            request.artifact_kind,
            request.schema_version,
            request.payload,
            canonicalization_version=request.canonicalization_version,
            content_type=request.content_type,
        )
        canonical_bytes = canonicalize_json(envelope)
        content_digest = sha256(canonical_bytes).digest()
        canonical_cache = json.loads(canonical_bytes.decode("utf-8"))
        jsonb_cache = (
            None if self._contains_null_character(canonical_cache) else canonical_cache
        )

        artifact = self.repository.insert_artifact(
            cursor,
            artifact_kind=request.artifact_kind,
            schema_version=request.schema_version,
            canonicalization_version=request.canonicalization_version,
            digest_algorithm=DIGEST_ALGORITHM,
            content_digest=content_digest,
            content_length=len(canonical_bytes),
            content_type=request.content_type,
            json_payload=jsonb_cache,
        )
        artifact_reused = artifact is None
        if artifact_reused:
            artifact = self.repository.load_artifact_for_update(
                cursor,
                canonicalization_version=request.canonicalization_version,
                digest_algorithm=DIGEST_ALGORITHM,
                content_digest=content_digest,
            )
            if artifact is None:
                raise ArtifactIntegrityError(
                    "canonical artifact conflict resolved without an artifact row"
                )

        self._verify_artifact(
            artifact,
            request=request,
            canonical_cache=canonical_cache,
            canonical_bytes=canonical_bytes,
            content_digest=content_digest,
        )

        locations = self.repository.load_inline_locations_for_update(cursor, artifact.id)
        if artifact_reused:
            location = self._verify_reusable_inline_location(
                locations,
                canonical_bytes=canonical_bytes,
                content_digest=content_digest,
            )
            location_reused = True
        else:
            if locations:
                raise ArtifactIntegrityError(
                    "new canonical artifact unexpectedly already has an inline location"
                )
            location = self.repository.insert_verified_inline_location(
                cursor,
                location_key=uuid4(),
                artifact_id=artifact.id,
                canonical_bytes=canonical_bytes,
            )
            location_reused = False

        return PersistedScientificArtifact(
            artifact=artifact,
            location=location,
            canonical_bytes=canonical_bytes,
            artifact_reused=artifact_reused,
            location_reused=location_reused,
        )

    @staticmethod
    def _contains_null_character(value: Any) -> bool:
        """Return whether a canonical value cannot be represented by JSONB.

        PostgreSQL rejects U+0000 in JSONB strings and object keys. The registry
        cache is optional, so exact verified canonical bytes remain authoritative
        while the cache is omitted for this otherwise valid canonical document.
        """

        value_type = type(value)
        if value_type is str:
            return "\x00" in value
        if value_type is list:
            return any(
                ScientificArtifactWriter._contains_null_character(item)
                for item in value
            )
        if value_type is dict:
            return any(
                "\x00" in key
                or ScientificArtifactWriter._contains_null_character(item)
                for key, item in value.items()
            )
        return False

    @staticmethod
    def _verify_artifact(
        artifact: ScientificArtifactRow,
        *,
        request: ScientificArtifactWriteRequest,
        canonical_cache: dict[str, Any],
        canonical_bytes: bytes,
        content_digest: bytes,
    ) -> None:
        expected = (
            request.artifact_kind,
            request.schema_version,
            request.canonicalization_version,
            DIGEST_ALGORITHM,
            content_digest,
            len(canonical_bytes),
            request.content_type,
        )
        actual = (
            artifact.artifact_kind,
            artifact.schema_version,
            artifact.canonicalization_version,
            artifact.digest_algorithm,
            artifact.content_digest,
            artifact.content_length,
            artifact.content_type,
        )
        if actual != expected:
            raise IncompatibleArtifactError(
                "existing canonical artifact has incompatible semantic metadata"
            )
        if artifact.json_payload is not None and artifact.json_payload != canonical_cache:
            raise IncompatibleArtifactError(
                "existing canonical artifact JSONB cache disagrees with canonical payload"
            )

    @staticmethod
    def _verify_reusable_inline_location(
        locations: tuple[ScientificArtifactLocationRow, ...],
        *,
        canonical_bytes: bytes,
        content_digest: bytes,
    ) -> ScientificArtifactLocationRow:
        if not locations:
            raise ArtifactBytesUnavailableError(
                "existing canonical identity has no inline bytes for collision-safe reuse"
            )
        verified = [
            location
            for location in locations
            if location.location_status == "verified" and location.verified_at is not None
        ]
        if not verified:
            raise InvalidArtifactLocationError(
                "existing inline locations are not in verified state"
            )
        for location in verified:
            if sha256(location.canonical_bytes).digest() != content_digest:
                raise ArtifactIntegrityError(
                    "verified inline bytes do not hash to the artifact identity"
                )
            if location.canonical_bytes != canonical_bytes:
                raise ArtifactIntegrityError(
                    "SHA-256 identity collision: authoritative canonical bytes differ"
                )
        return verified[0]
