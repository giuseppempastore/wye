"""Versioned canonical JSON helpers used only for semantic fingerprints."""

import hashlib
import json
from typing import Any, Iterable


ARTIFACT_MANIFEST_CANONICALIZATION_VERSION = "scientific_artifact_manifest_v1"
INGESTION_CONFIG_CANONICALIZATION_VERSION = "scientific_ingestion_config_v1"


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON-compatible data deterministically as UTF-8.

    Keys are sorted, insignificant whitespace is omitted, Unicode is preserved,
    and non-JSON numeric values such as NaN are rejected.
    """

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return lowercase SHA-256 for a canonical JSON value."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def artifact_manifest_payload(release: Any, artifacts: Iterable[Any], version: str) -> dict[str, Any]:
    """Build the explicit, order-independent artifact-manifest payload.

    ``storage_object_id`` remains available on each reference for traversal but
    is deliberately excluded from the semantic fingerprint: moving identical
    immutable bytes between infrastructure objects must not change raw input
    identity. Exact database membership still requires a future run/artifact
    junction.
    """

    canonical_artifacts = [
        {
            "artifact_key": artifact.artifact_key,
            "artifact_role": artifact.artifact_role,
            "byte_size": artifact.byte_size,
            "raw_checksum_algorithm": artifact.raw_checksum_algorithm,
            "raw_checksum_value": artifact.raw_checksum_value,
        }
        for artifact in sorted(artifacts, key=lambda item: item.artifact_key)
    ]
    return {
        "artifacts": canonical_artifacts,
        "canonicalization_version": version,
        "release": {
            "dataset_key": release.dataset_key,
            "external_release_key": release.external_release_key,
            "source_key": release.source_key,
        },
    }


def artifact_manifest_fingerprint(release: Any, artifacts: Iterable[Any], version: str) -> str:
    return canonical_sha256(artifact_manifest_payload(release, artifacts, version))
