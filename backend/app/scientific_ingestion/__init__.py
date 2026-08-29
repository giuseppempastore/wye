"""Source-agnostic contracts for scientific acquisition and parsing."""

from .canonicalization import canonical_json_bytes, canonical_sha256
from .contracts import (
    ScientificAdapterMetadata,
    ScientificArtifactAcquirer,
    ScientificArtifactManifest,
    ScientificArtifactParser,
    ScientificArtifactReference,
    ScientificAssessmentInput,
    ScientificChecksum,
    ScientificFindingInput,
    ScientificIngestionConfiguration,
    ScientificParsedRecord,
    ScientificParserResult,
    ScientificParserWarning,
    ScientificRecordRejection,
    ScientificReleaseIdentity,
    ScientificSourceAdapter,
    SubstanceIdentifierInput,
)
from .errors import (
    ScientificAcquisitionError,
    ScientificIngestionError,
    ScientificParserError,
    ScientificPersistenceConflict,
    ScientificRecordValidationError,
)

__all__ = [
    "ScientificAcquisitionError",
    "ScientificAdapterMetadata",
    "ScientificArtifactAcquirer",
    "ScientificArtifactManifest",
    "ScientificArtifactParser",
    "ScientificArtifactReference",
    "ScientificAssessmentInput",
    "ScientificChecksum",
    "ScientificFindingInput",
    "ScientificIngestionConfiguration",
    "ScientificIngestionError",
    "ScientificParsedRecord",
    "ScientificParserError",
    "ScientificParserResult",
    "ScientificParserWarning",
    "ScientificPersistenceConflict",
    "ScientificRecordRejection",
    "ScientificRecordValidationError",
    "ScientificReleaseIdentity",
    "ScientificSourceAdapter",
    "SubstanceIdentifierInput",
    "canonical_json_bytes",
    "canonical_sha256",
]
