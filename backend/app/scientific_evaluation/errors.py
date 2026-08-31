"""Small internal error model for canonical scientific artifacts."""


class ScientificArtifactError(Exception):
    """Base error for canonicalization and scientific artifact persistence."""


class CanonicalizationError(ScientificArtifactError, ValueError):
    """The supplied value is outside the frozen canonical JSON domain."""


class UnsupportedCanonicalValueError(CanonicalizationError, TypeError):
    """A Python-specific or otherwise unsupported value was supplied."""


class CanonicalStringError(CanonicalizationError):
    """A string is not a valid Unicode scalar sequence."""


class CanonicalObjectKeyError(CanonicalizationError):
    """An object key is invalid or collides after normalization."""


class CanonicalNumberError(CanonicalizationError):
    """A numeric input cannot be represented by wye-c14n-json-v1."""


class ArtifactContractError(ScientificArtifactError, ValueError):
    """Artifact kind, schema or envelope configuration is unsupported."""


class ArtifactIntegrityError(ScientificArtifactError):
    """Stored canonical identity cannot be proven compatible with supplied bytes."""


class IncompatibleArtifactError(ArtifactIntegrityError):
    """An existing digest identity has incompatible semantic metadata."""


class ArtifactBytesUnavailableError(ArtifactIntegrityError):
    """Authoritative stored bytes are unavailable for collision-safe reuse."""


class InvalidArtifactLocationError(ArtifactIntegrityError):
    """An existing artifact location is incompatible with verified inline reuse."""


class SnapshotRuntimeError(ScientificArtifactError):
    """Base error for deterministic scientific evidence snapshot construction."""


class SnapshotRequestError(SnapshotRuntimeError, ValueError):
    """A snapshot request is structurally invalid or noncanonical."""


class SnapshotMemberError(SnapshotRuntimeError, ValueError):
    """A requested evidence member has an invalid shape or identity."""


class DuplicateSnapshotMemberError(SnapshotMemberError):
    """The request repeats the same structural evidence candidate."""


class SnapshotProvenanceError(SnapshotMemberError):
    """The requested candidate cannot resolve the frozen provenance chain."""


class SnapshotAlreadySealedError(SnapshotRuntimeError):
    """A mutation or finalization operation targeted a sealed snapshot."""


class CanonicalSnapshotConflictError(SnapshotRuntimeError):
    """A canonical sealed snapshot identity already exists."""


class IncompatibleCanonicalSnapshotError(CanonicalSnapshotConflictError):
    """A sealed digest winner does not have the expected canonical roots."""


class SnapshotFinalizationError(SnapshotRuntimeError):
    """Stored building state cannot be finalized as the requested snapshot."""


class MappingInputRuntimeError(ScientificArtifactError):
    """Base error for canonical target, mapping-state and input construction."""


class MappingInputRequestError(MappingInputRuntimeError, ValueError):
    """A target or canonical input request is structurally invalid."""


class UnsupportedEvaluationTargetError(MappingInputRequestError):
    """The requested evaluation target is outside the frozen v1 vocabulary."""


class EvaluationTargetNotFoundError(MappingInputRuntimeError):
    """The requested target does not exist in the authoritative registry."""


class HistoricalTargetStateUnavailableError(MappingInputRuntimeError):
    """The target row cannot truthfully represent the requested historical view."""


class MappingStateInconsistentError(MappingInputRuntimeError):
    """Stored mapping history violates the frozen structural contract."""


class MappingHistoryUnavailableError(MappingInputRuntimeError):
    """Mapping history cannot provide the required canonical reconstruction."""


class AuthorityChainInconsistentError(MappingStateInconsistentError):
    """A proposal/decision/materialization chain is structurally inconsistent."""


class TargetMappingMismatchError(MappingStateInconsistentError):
    """Mapping state contains a relationship outside the requested target."""


class UnsealedEvidenceSnapshotError(MappingInputRuntimeError):
    """An execution prerequisite references a non-sealed evidence snapshot."""


class InvalidProtocolLifecycleError(MappingInputRuntimeError):
    """The protocol lifecycle is not executable for the requested mode."""


class CounterfactualAuthorizationUnavailableError(MappingInputRuntimeError):
    """Governed counterfactual authorization cannot be proven by current runtime."""


class CanonicalInputIntegrityError(MappingInputRuntimeError):
    """Canonical target, mapping or input roots are internally inconsistent."""
