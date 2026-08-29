"""Concrete fixture-first scientific source adapters."""

from .common import LocalFixtureArtifact, LocalFixtureArtifactAcquirer, LocalFixtureArtifactReader
from .efsa import EfsaAdapter, EfsaArtifactParser
from .openfoodtox import OpenFoodToxAdapter, OpenFoodToxArtifactParser
from .openfoodtox_real import (
    OpenFoodTox3Adapter, OpenFoodToxArtifactParser as OpenFoodTox3ArtifactParser,
    OpenFoodToxIuclidXlsxParser, OpenFoodToxRemoteAcquirer,
)

__all__ = [
    "EfsaAdapter", "EfsaArtifactParser", "LocalFixtureArtifact",
    "LocalFixtureArtifactAcquirer", "LocalFixtureArtifactReader",
    "OpenFoodToxAdapter", "OpenFoodToxArtifactParser",
    "OpenFoodTox3Adapter", "OpenFoodTox3ArtifactParser",
    "OpenFoodToxIuclidXlsxParser", "OpenFoodToxRemoteAcquirer",
]
