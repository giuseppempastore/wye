"""Immutable boundary contracts between source adapters and WYE ingestion.

Source-specific acquisition and parsing end at this module. The future core
receives only these source-agnostic envelopes and remains unaware of external
JSON, CSV, URLs, APIs, or provider-specific schemas.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated

from .canonicalization import (
    ARTIFACT_MANIFEST_CANONICALIZATION_VERSION,
    INGESTION_CONFIG_CANONICALIZATION_VERSION,
    artifact_manifest_fingerprint,
    canonical_sha256,
)


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
MachineKey = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"),
]
Algorithm = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9][a-z0-9_-]*$"),
]


class FrozenContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ScientificChecksum(FrozenContract):
    """Checksum metadata whose value always describes explicitly named bytes."""

    algorithm: Algorithm
    value: NonEmptyText

    @model_validator(mode="after")
    def validate_algorithm_value(self):
        if self.algorithm == "sha256" and (
            len(self.value) != 64 or any(char not in "0123456789abcdef" for char in self.value)
        ):
            raise ValueError("sha256 value must be 64 lowercase hexadecimal characters")
        return self


class ScientificAdapterMetadata(FrozenContract):
    source_key: MachineKey
    dataset_key: MachineKey
    adapter_version: NonEmptyText
    acquisition_version: NonEmptyText
    parser_version: NonEmptyText
    normalization_schema_version: NonEmptyText


class ScientificReleaseIdentity(FrozenContract):
    source_key: MachineKey
    dataset_key: MachineKey
    external_release_key: NonEmptyText


ArtifactRole = Literal["primary", "manifest", "metadata", "attachment", "archive", "other"]


class ScientificArtifactReference(FrozenContract):
    """One immutable raw artifact selected for an ingestion run."""

    artifact_key: MachineKey
    artifact_role: ArtifactRole
    storage_object_id: int = Field(gt=0)
    raw_checksum_algorithm: Algorithm
    raw_checksum_value: NonEmptyText
    byte_size: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_raw_checksum(self):
        ScientificChecksum(
            algorithm=self.raw_checksum_algorithm,
            value=self.raw_checksum_value,
        )
        return self


class ScientificArtifactManifest(FrozenContract):
    """Exact application-level artifact selection for one logical release."""

    release: ScientificReleaseIdentity
    artifacts: tuple[ScientificArtifactReference, ...] = Field(min_length=1)
    canonicalization_version: Literal["scientific_artifact_manifest_v1"] = (
        ARTIFACT_MANIFEST_CANONICALIZATION_VERSION
    )
    fingerprint_algorithm: Literal["sha256"] = "sha256"
    fingerprint: NonEmptyText

    @classmethod
    def build(
        cls,
        release: ScientificReleaseIdentity,
        artifacts: tuple[ScientificArtifactReference, ...],
    ) -> "ScientificArtifactManifest":
        fingerprint = artifact_manifest_fingerprint(
            release,
            artifacts,
            ARTIFACT_MANIFEST_CANONICALIZATION_VERSION,
        )
        return cls(release=release, artifacts=artifacts, fingerprint=fingerprint)

    @model_validator(mode="after")
    def validate_identity_and_fingerprint(self):
        keys = [artifact.artifact_key for artifact in self.artifacts]
        if len(keys) != len(set(keys)):
            raise ValueError("artifact_key must be unique within a manifest")
        expected = artifact_manifest_fingerprint(
            self.release,
            self.artifacts,
            self.canonicalization_version,
        )
        if self.fingerprint != expected:
            raise ValueError("manifest fingerprint does not match canonical artifact content")
        return self


class ScientificIngestionConfiguration(FrozenContract):
    """Semantic versions and source-agnostic configuration used for one run."""

    adapter: ScientificAdapterMetadata
    semantic_configuration: dict[str, Any] = Field(default_factory=dict)
    canonicalization_version: Literal["scientific_ingestion_config_v1"] = (
        INGESTION_CONFIG_CANONICALIZATION_VERSION
    )

    @property
    def fingerprint_algorithm(self) -> str:
        return "sha256"

    @property
    def fingerprint(self) -> str:
        return canonical_sha256(
            {
                "adapter_version": self.adapter.adapter_version,
                "acquisition_version": self.adapter.acquisition_version,
                "canonicalization_version": self.canonicalization_version,
                "normalization_schema_version": self.adapter.normalization_schema_version,
                "parser_version": self.adapter.parser_version,
                "semantic_configuration": self.semantic_configuration,
                "source_key": self.adapter.source_key,
                "dataset_key": self.adapter.dataset_key,
            }
        )


class SubstanceIdentifierInput(FrozenContract):
    namespace_key: MachineKey
    namespace_version: NonEmptyText
    raw_value: str = Field(min_length=1)
    normalized_value: NonEmptyText
    is_primary: bool = False
    source_record_locator: NonEmptyText | None = None
    provenance: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_raw_value(self):
        if not self.raw_value.strip():
            raise ValueError("raw_value must not be blank")
        return self


AssessmentStatus = Literal["pending_review", "published", "superseded", "withdrawn", "rejected"]


class ScientificAssessmentInput(FrozenContract):
    source_record_key: NonEmptyText
    external_assessment_id: NonEmptyText | None = None
    external_assessment_version: NonEmptyText | None = None
    assessment_type: NonEmptyText
    assessment_version: NonEmptyText
    assessment_status: AssessmentStatus = "pending_review"
    published_at: date | None = None
    document_reference: NonEmptyText | None = None
    conclusion_text: str | None = None
    assessment_data: dict[str, Any] | None = None
    raw_record: dict[str, Any] | None = None
    normalized_checksum: ScientificChecksum | None = None


class ScientificFindingInput(FrozenContract):
    source_record_key: NonEmptyText
    source_finding_key: NonEmptyText | None = None
    source_ordinal: int | None = Field(default=None, ge=0)
    finding_key: NonEmptyText | None = None
    endpoint: NonEmptyText | None = None
    value_numeric: Decimal | None = None
    value_text: str | None = None
    unit: NonEmptyText | None = None
    population_context: str | None = None
    evidence_type: NonEmptyText | None = None
    conclusion_text: str | None = None
    source_locator: NonEmptyText | None = None
    raw_payload: dict[str, Any] | None = None
    fingerprint: ScientificChecksum | None = None

    @model_validator(mode="after")
    def validate_minimal_content(self):
        if all(
            value is None
            for value in (
                self.value_numeric,
                self.value_text,
                self.conclusion_text,
                self.raw_payload,
            )
        ):
            raise ValueError("finding requires numeric, text, conclusion, or raw content")
        return self


class ScientificParsedRecord(FrozenContract):
    """Minimal parser envelope; source order is preserved by parser results."""

    source_record_key: NonEmptyText
    source_record_locator: NonEmptyText | None = None
    raw_record: dict[str, Any]
    substance_identifiers: tuple[SubstanceIdentifierInput, ...] = Field(min_length=1)
    assessment: ScientificAssessmentInput
    findings: tuple[ScientificFindingInput, ...] = Field(default_factory=tuple)


class ScientificParserWarning(FrozenContract):
    code: MachineKey
    message: NonEmptyText
    source_record_locator: NonEmptyText | None = None


class ScientificRecordRejection(FrozenContract):
    source_record_key: NonEmptyText
    error_code: MachineKey
    error_summary: NonEmptyText
    raw_record: dict[str, Any] | None = None


class ScientificParserResult(FrozenContract):
    """Database-independent parser output and run-counter inputs."""

    records: tuple[ScientificParsedRecord, ...] = Field(default_factory=tuple)
    rejected_records: tuple[ScientificRecordRejection, ...] = Field(default_factory=tuple)
    warnings: tuple[ScientificParserWarning, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parser_version: NonEmptyText
    normalization_schema_version: NonEmptyText

    @property
    def records_seen(self) -> int:
        return len(self.records) + len(self.rejected_records)

    @property
    def records_accepted(self) -> int:
        return len(self.records)

    @property
    def records_rejected(self) -> int:
        return len(self.rejected_records)

    @property
    def warnings_count(self) -> int:
        return len(self.warnings)


@runtime_checkable
class ScientificSourceAdapter(Protocol):
    """Discover logical source releases; no acquisition or parsing concerns."""

    @property
    def metadata(self) -> ScientificAdapterMetadata: ...

    def discover_release(self) -> ScientificReleaseIdentity: ...


@runtime_checkable
class ScientificArtifactAcquirer(Protocol):
    """Acquire one release and return its exact immutable artifact manifest."""

    def acquire(self, release: ScientificReleaseIdentity) -> ScientificArtifactManifest: ...


@runtime_checkable
class ScientificArtifactParser(Protocol):
    """Transform acquired artifacts into source-agnostic record envelopes."""

    def parse(self, manifest: ScientificArtifactManifest) -> ScientificParserResult: ...
