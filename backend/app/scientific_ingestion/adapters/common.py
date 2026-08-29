"""Offline acquisition primitives shared by scientific source adapters."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app.scientific_ingestion.contracts import (
    ScientificArtifactManifest,
    ScientificArtifactReference,
    ScientificReleaseIdentity,
)
from app.scientific_ingestion.errors import ScientificAcquisitionError, ScientificParserError


@dataclass(frozen=True)
class LocalFixtureArtifact:
    path: Path
    artifact_key: str
    artifact_role: str
    storage_object_id: int
    content_type: str = "application/json"
    provider_key: str = "scientific_fixture"

    @property
    def source_locator(self) -> str:
        return f"fixture://{self.provider_key}/{self.path.name}"

    def payload(self) -> bytes:
        try:
            return self.path.read_bytes()
        except OSError as exc:
            raise ScientificAcquisitionError(
                f"fixture artifact could not be read: {self.source_locator}"
            ) from exc


class LocalFixtureArtifactAcquirer:
    """Describe immutable local bytes without performing provider transport."""

    def __init__(self, fixture: LocalFixtureArtifact):
        self.fixture = fixture

    def acquire(self, release: ScientificReleaseIdentity) -> ScientificArtifactManifest:
        payload = self.fixture.payload()
        reference = ScientificArtifactReference(
            artifact_key=self.fixture.artifact_key,
            artifact_role=self.fixture.artifact_role,
            storage_object_id=self.fixture.storage_object_id,
            raw_checksum_algorithm="sha256",
            raw_checksum_value=sha256(payload).hexdigest(),
            byte_size=len(payload),
            source_locator=self.fixture.source_locator,
            content_type=self.fixture.content_type,
            acquisition_metadata={
                "mode": "local_fixture",
                "provider_key": self.fixture.provider_key,
                "fixture_name": self.fixture.path.name,
            },
        )
        return ScientificArtifactManifest.build(release, (reference,))


class LocalFixtureArtifactReader:
    """Read and verify fixture bytes selected by a persisted manifest."""

    def __init__(self, fixture: LocalFixtureArtifact):
        self.fixture = fixture

    def read_bytes(self, artifact: ScientificArtifactReference) -> bytes:
        if (
            artifact.artifact_key != self.fixture.artifact_key
            or artifact.storage_object_id != self.fixture.storage_object_id
        ):
            raise ScientificAcquisitionError("manifest selected an unexpected fixture artifact")
        payload = self.fixture.payload()
        if artifact.byte_size is not None and artifact.byte_size != len(payload):
            raise ScientificAcquisitionError("fixture artifact byte size differs from manifest")
        if (
            artifact.raw_checksum_algorithm != "sha256"
            or artifact.raw_checksum_value != sha256(payload).hexdigest()
        ):
            raise ScientificAcquisitionError("fixture artifact checksum differs from manifest")
        return payload


def load_json_object(payload: bytes, provider_key: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScientificParserError(f"{provider_key} artifact is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ScientificParserError(f"{provider_key} artifact root must be an object")
    return value


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def primary_artifact(manifest: ScientificArtifactManifest) -> ScientificArtifactReference:
    selected = tuple(item for item in manifest.artifacts if item.artifact_role == "primary")
    if len(selected) != 1:
        raise ScientificParserError("exactly one primary artifact is required")
    return selected[0]
