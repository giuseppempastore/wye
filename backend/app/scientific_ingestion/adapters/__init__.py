"""Concrete fixture-first scientific source adapters."""

from .common import LocalFixtureArtifact, LocalFixtureArtifactAcquirer, LocalFixtureArtifactReader
from .efsa import EfsaAdapter, EfsaArtifactParser
from .openfoodtox import OpenFoodToxAdapter, OpenFoodToxArtifactParser

__all__ = [
    "EfsaAdapter", "EfsaArtifactParser", "LocalFixtureArtifact",
    "LocalFixtureArtifactAcquirer", "LocalFixtureArtifactReader",
    "OpenFoodToxAdapter", "OpenFoodToxArtifactParser",
]
