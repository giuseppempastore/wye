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
