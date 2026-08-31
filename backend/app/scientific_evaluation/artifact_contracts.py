"""Allowlisted canonical artifact contracts frozen by Phases 7.6.1–B."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from app.scientific_evaluation.canonicalization import (
    CANONICALIZATION_VERSION,
    MEDIA_TYPE,
)
from app.scientific_evaluation.errors import ArtifactContractError


@dataclass(frozen=True)
class ArtifactContract:
    artifact_kind: str
    schema_version: str
    preferred_storage_mode: str


_CONTRACTS = {
    ("protocol_definition", "1"): ArtifactContract(
        "protocol_definition", "1", "inline"
    ),
    ("protocol_review", "1"): ArtifactContract(
        "protocol_review", "1", "inline"
    ),
    ("scientific_evidence_snapshot_query", "1"): ArtifactContract(
        "scientific_evidence_snapshot_query", "1", "inline"
    ),
    ("scientific_evidence_snapshot_member", "1"): ArtifactContract(
        "scientific_evidence_snapshot_member", "1", "object"
    ),
    ("scientific_evidence_snapshot_manifest", "1"): ArtifactContract(
        "scientific_evidence_snapshot_manifest", "1", "object"
    ),
    ("scientific_evaluation_target", "1"): ArtifactContract(
        "scientific_evaluation_target", "1", "inline"
    ),
    ("scientific_mapping_state_member", "1"): ArtifactContract(
        "scientific_mapping_state_member", "1", "object"
    ),
    ("scientific_mapping_state_manifest", "1"): ArtifactContract(
        "scientific_mapping_state_manifest", "1", "object"
    ),
    ("scientific_evaluation_input", "1"): ArtifactContract(
        "scientific_evaluation_input", "1", "inline"
    ),
    ("scientific_evaluation_configuration", "1"): ArtifactContract(
        "scientific_evaluation_configuration", "1", "inline"
    ),
    ("scientific_evaluation_execution_identity", "1"): ArtifactContract(
        "scientific_evaluation_execution_identity", "1", "inline"
    ),
    ("scientific_evaluation_engine_build", "1"): ArtifactContract(
        "scientific_evaluation_engine_build", "1", "inline"
    ),
    ("scientific_evaluation_attempt_error", "1"): ArtifactContract(
        "scientific_evaluation_attempt_error", "1", "inline"
    ),
    ("scientific_evidence_selection_decision", "1"): ArtifactContract(
        "scientific_evidence_selection_decision", "1", "inline"
    ),
    ("scientific_evidence_selection_manifest", "1"): ArtifactContract(
        "scientific_evidence_selection_manifest", "1", "inline"
    ),
    ("scientific_evaluation_result_component", "1"): ArtifactContract(
        "scientific_evaluation_result_component", "1", "inline"
    ),
    ("scientific_evaluation_result", "1"): ArtifactContract(
        "scientific_evaluation_result", "1", "inline"
    ),
    ("scientific_evaluation_trace", "1"): ArtifactContract(
        "scientific_evaluation_trace", "1", "inline"
    ),
    ("scientific_evaluation_publication_bundle", "1"): ArtifactContract(
        "scientific_evaluation_publication_bundle", "1", "inline"
    ),
    ("scientific_evaluation_replay_verification", "1"): ArtifactContract(
        "scientific_evaluation_replay_verification", "1", "inline"
    ),
}

ARTIFACT_CONTRACTS: Mapping[tuple[str, str], ArtifactContract] = MappingProxyType(
    _CONTRACTS
)


def require_artifact_contract(
    artifact_kind: str,
    schema_version: str,
) -> ArtifactContract:
    try:
        return ARTIFACT_CONTRACTS[(artifact_kind, schema_version)]
    except KeyError as exc:
        raise ArtifactContractError(
            f"unsupported scientific artifact contract: {artifact_kind}/{schema_version}"
        ) from exc


def build_artifact_envelope(
    artifact_kind: str,
    schema_version: str,
    payload: dict[str, Any],
    *,
    canonicalization_version: str = CANONICALIZATION_VERSION,
    content_type: str = MEDIA_TYPE,
) -> dict[str, Any]:
    require_artifact_contract(artifact_kind, schema_version)
    if canonicalization_version != CANONICALIZATION_VERSION:
        raise ArtifactContractError(
            f"unsupported canonicalization version: {canonicalization_version}"
        )
    if content_type != MEDIA_TYPE:
        raise ArtifactContractError(f"unsupported canonical media type: {content_type}")
    if type(payload) is not dict:
        raise ArtifactContractError("canonical artifact payload must be a JSON object")
    return {
        "artifact_kind": artifact_kind,
        "canonicalization_version": canonicalization_version,
        "payload": payload,
        "schema_version": schema_version,
    }
