"""Typed canonical models for Phase 7.6.4C execution persistence runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Literal, Mapping, TypeAlias
from uuid import UUID

from app.scientific_evaluation.canonicalization import MAX_SIGNED_64, canonicalize_json
from app.scientific_evaluation.errors import ExecutionRequestError


CanonicalJsonValue: TypeAlias = (
    None | bool | int | str | list["CanonicalJsonValue"] | dict[str, "CanonicalJsonValue"]
)
ExecutionMode = Literal["NORMAL", "REPLAY", "COUNTERFACTUAL", "REFRESH"]

EXECUTION_MODES = frozenset({"NORMAL", "REPLAY", "COUNTERFACTUAL", "REFRESH"})
TARGET_TYPES = frozenset({"substance", "ingredient"})
DECISIONS = frozenset({"included", "excluded"})
SELECTION_ROLES = frozenset({"contributing", "context_only", "none"})
RESOLUTION_STATES = frozenset({"resolved", "deferred"})
FAILURE_CATEGORIES = frozenset(
    {
        "validation",
        "artifact_integrity",
        "engine_incompatible",
        "canonicalization",
        "database",
        "resource",
        "cancelled",
        "unexpected",
    }
)
_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_ERROR_KEY_PARTS = (
    "api_key",
    "authorization",
    "cookie",
    "environment",
    "password",
    "prompt",
    "raw_input",
    "secret",
    "stack_locals",
    "token",
)


def _nonblank(value: str, field_name: str, *, max_length: int | None = None) -> str:
    if type(value) is not str or not value.strip():
        raise ExecutionRequestError(f"{field_name} must be a nonblank string")
    if max_length is not None and len(value) > max_length:
        raise ExecutionRequestError(
            f"{field_name} must contain at most {max_length} characters"
        )
    return value


def _positive_id(value: int | None, field_name: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if type(value) is not int or value <= 0 or value > MAX_SIGNED_64:
        raise ExecutionRequestError(f"{field_name} must be a positive signed 64-bit integer")


def _canonical_object(value: dict[str, Any], field_name: str) -> dict[str, CanonicalJsonValue]:
    if type(value) is not dict:
        raise ExecutionRequestError(f"{field_name} must be a canonical JSON object")
    try:
        canonicalize_json(value)
    except Exception as exc:
        raise ExecutionRequestError(f"{field_name} is outside the canonical JSON domain") from exc
    return value


def _digest_hex(value: bytes, field_name: str) -> str:
    if type(value) is not bytes or len(value) != 32:
        raise ExecutionRequestError(f"{field_name} must contain exactly 32 bytes")
    return value.hex()


def _reject_sensitive_error_keys(value: CanonicalJsonValue, path: str = "technical_references") -> None:
    if type(value) is dict:
        for key, item in value.items():
            normalized = key.casefold()
            if any(part in normalized for part in _FORBIDDEN_ERROR_KEY_PARTS):
                raise ExecutionRequestError(f"{path}.{key} is not permitted in sanitized errors")
            _reject_sensitive_error_keys(item, f"{path}.{key}")
    elif type(value) is list:
        for index, item in enumerate(value):
            _reject_sensitive_error_keys(item, f"{path}[{index}]")


@dataclass(frozen=True)
class ExecutionConfiguration:
    engine_key: str
    semantic_compatibility_version: str


@dataclass(frozen=True)
class SemanticExecutionRequest:
    protocol_version_id: int
    evidence_snapshot_id: int
    target_type: str
    target_id: int
    target_artifact_id: int
    target_digest: bytes
    mapping_state_artifact_id: int | None
    input_artifact_id: int
    input_digest: bytes
    execution_mode: ExecutionMode
    configuration: ExecutionConfiguration
    requested_by: str
    comparison_execution_id: int | None = None
    idempotency_scope: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class EngineBuild:
    engine_key: str
    semantic_compatibility_version: str
    source_revision: str
    source_tree_sha256: str
    dependency_lock_sha256: str
    build_sha256: str
    canonicalization_implementation_version: str
    oci_image_digest: str | None = None


@dataclass(frozen=True)
class AttemptStartRequest:
    execution_id: int
    engine_build: EngineBuild
    lease_token: UUID
    heartbeat_at: datetime
    lease_expires_at: datetime
    worker_id: str | None = None


@dataclass(frozen=True)
class AttemptError:
    category: str
    code: str
    retryable: bool
    sanitized_detail: str | None = None
    technical_references: dict[str, CanonicalJsonValue] = field(default_factory=dict)


@dataclass(frozen=True)
class SelectionDecisionInput:
    snapshot_member_id: int
    decision: str
    selection_role: str
    resolution_state: str
    reason_namespace: str
    reason_version: str
    primary_reason_code: str
    content: dict[str, CanonicalJsonValue] = field(default_factory=dict)


@dataclass(frozen=True)
class ResultComponentInput:
    component_kind: str
    component_schema_version: str
    component_role: str
    content: dict[str, CanonicalJsonValue]


@dataclass(frozen=True)
class PublicationOutputInput:
    decisions: tuple[SelectionDecisionInput, ...]
    result_kind: str
    result_schema_version: str
    scientific_status_namespace: str
    scientific_status_version: str
    scientific_status_code: str
    result_content: dict[str, CanonicalJsonValue]
    components: tuple[ResultComponentInput, ...]
    trace_schema_version: str
    trace_content: dict[str, CanonicalJsonValue]
    published_by: str


@dataclass(frozen=True)
class ReplayOutputInput:
    selection_manifest_payload: dict[str, CanonicalJsonValue]
    result_payload: dict[str, CanonicalJsonValue]
    trace_payload: dict[str, CanonicalJsonValue]


def validate_semantic_request(request: SemanticExecutionRequest) -> None:
    if not isinstance(request, SemanticExecutionRequest):
        raise ExecutionRequestError("execution request must use SemanticExecutionRequest")
    for name in (
        "protocol_version_id",
        "evidence_snapshot_id",
        "target_id",
        "target_artifact_id",
        "input_artifact_id",
    ):
        _positive_id(getattr(request, name), name)
    _positive_id(request.mapping_state_artifact_id, "mapping_state_artifact_id", nullable=True)
    _positive_id(request.comparison_execution_id, "comparison_execution_id", nullable=True)
    if request.target_type not in TARGET_TYPES:
        raise ExecutionRequestError("target_type must be substance or ingredient")
    if request.execution_mode not in EXECUTION_MODES:
        raise ExecutionRequestError("unsupported execution_mode")
    if request.execution_mode == "NORMAL" and request.comparison_execution_id is not None:
        raise ExecutionRequestError("NORMAL execution cannot have a comparison")
    if request.execution_mode != "NORMAL" and request.comparison_execution_id is None:
        raise ExecutionRequestError(f"{request.execution_mode} requires comparison_execution_id")
    if request.target_type == "ingredient" and request.mapping_state_artifact_id is None:
        raise ExecutionRequestError("ingredient execution requires mapping_state_artifact_id")
    if request.target_type == "substance" and request.mapping_state_artifact_id is not None:
        raise ExecutionRequestError("substance execution mapping state is not applicable")
    _digest_hex(request.target_digest, "target_digest")
    _digest_hex(request.input_digest, "input_digest")
    _nonblank(request.requested_by, "requested_by", max_length=255)
    validate_configuration(request.configuration)
    if (request.idempotency_scope is None) != (request.idempotency_key is None):
        raise ExecutionRequestError("idempotency_scope and idempotency_key must be supplied together")
    if request.idempotency_scope is not None:
        _nonblank(request.idempotency_scope, "idempotency_scope", max_length=255)
        _nonblank(request.idempotency_key or "", "idempotency_key", max_length=255)


def validate_configuration(configuration: ExecutionConfiguration) -> None:
    if not isinstance(configuration, ExecutionConfiguration):
        raise ExecutionRequestError("configuration must use ExecutionConfiguration")
    _nonblank(configuration.engine_key, "engine_key")
    _nonblank(configuration.semantic_compatibility_version, "semantic_compatibility_version")


def build_configuration_payload(
    configuration: ExecutionConfiguration,
) -> dict[str, CanonicalJsonValue]:
    validate_configuration(configuration)
    return {
        "artifact_type": "scientific_evaluation_configuration",
        "canonicalization_profiles": ["wye-c14n-json-v1"],
        "engine_contract": {
            "engine_key": configuration.engine_key,
            "semantic_compatibility_version": configuration.semantic_compatibility_version,
        },
        "schema_version": "1",
        "semantic_parameters": [],
    }


def build_execution_identity_payload(
    *,
    protocol_digest: bytes,
    evidence_snapshot_digest: bytes,
    input_digest: bytes,
    execution_mode: str,
    configuration_digest: bytes,
    comparison_semantic_execution_digest: bytes | None,
) -> dict[str, CanonicalJsonValue]:
    if execution_mode not in EXECUTION_MODES:
        raise ExecutionRequestError("unsupported execution_mode")
    return {
        "artifact_type": "scientific_evaluation_execution_identity",
        "comparison_semantic_execution_digest": (
            None
            if comparison_semantic_execution_digest is None
            else _digest_hex(
                comparison_semantic_execution_digest,
                "comparison_semantic_execution_digest",
            )
        ),
        "configuration_digest": _digest_hex(configuration_digest, "configuration_digest"),
        "evidence_snapshot_digest": _digest_hex(
            evidence_snapshot_digest, "evidence_snapshot_digest"
        ),
        "execution_mode": execution_mode,
        "input_digest": _digest_hex(input_digest, "input_digest"),
        "protocol_digest": _digest_hex(protocol_digest, "protocol_digest"),
        "schema_version": "1",
    }


def build_engine_build_payload(build: EngineBuild) -> dict[str, CanonicalJsonValue]:
    if not isinstance(build, EngineBuild):
        raise ExecutionRequestError("engine build must use EngineBuild")
    for field_name in (
        "engine_key",
        "semantic_compatibility_version",
        "source_revision",
        "canonicalization_implementation_version",
    ):
        _nonblank(getattr(build, field_name), field_name)
    for field_name in ("source_tree_sha256", "dependency_lock_sha256", "build_sha256"):
        if not _HEX_DIGEST.fullmatch(getattr(build, field_name)):
            raise ExecutionRequestError(f"{field_name} must be 64 lowercase hexadecimal characters")
    if build.oci_image_digest is not None:
        _nonblank(build.oci_image_digest, "oci_image_digest")
    return {
        "artifact_type": "scientific_evaluation_engine_build",
        "build_sha256": build.build_sha256,
        "canonicalization_implementation_version": (
            build.canonicalization_implementation_version
        ),
        "dependency_lock_sha256": build.dependency_lock_sha256,
        "engine_key": build.engine_key,
        "oci_image_digest": build.oci_image_digest,
        "schema_version": "1",
        "semantic_compatibility_version": build.semantic_compatibility_version,
        "source_revision": build.source_revision,
        "source_tree_sha256": build.source_tree_sha256,
    }


def build_attempt_error_payload(error: AttemptError) -> dict[str, CanonicalJsonValue]:
    if not isinstance(error, AttemptError) or error.category not in FAILURE_CATEGORIES:
        raise ExecutionRequestError("unsupported attempt error category")
    _nonblank(error.code, "error.code", max_length=100)
    if type(error.retryable) is not bool:
        raise ExecutionRequestError("error.retryable must be boolean")
    if error.sanitized_detail is not None:
        _nonblank(error.sanitized_detail, "error.sanitized_detail", max_length=4096)
    _canonical_object(error.technical_references, "error.technical_references")
    _reject_sensitive_error_keys(error.technical_references)
    return {
        "artifact_type": "scientific_evaluation_attempt_error",
        "error_category": error.category,
        "error_code": error.code,
        "retryable": error.retryable,
        "sanitized_detail": error.sanitized_detail,
        "schema_version": "1",
        "technical_references": error.technical_references,
    }


def validate_decision(value: SelectionDecisionInput) -> None:
    if not isinstance(value, SelectionDecisionInput):
        raise ExecutionRequestError("selection decision must use SelectionDecisionInput")
    _positive_id(value.snapshot_member_id, "snapshot_member_id")
    if value.decision not in DECISIONS:
        raise ExecutionRequestError("decision must be included or excluded")
    if value.selection_role not in SELECTION_ROLES:
        raise ExecutionRequestError("unsupported selection_role")
    if value.resolution_state not in RESOLUTION_STATES:
        raise ExecutionRequestError("unsupported selection resolution_state")
    if value.decision == "included" and (
        value.selection_role not in {"contributing", "context_only"}
        or value.resolution_state != "resolved"
    ):
        raise ExecutionRequestError("included decision must be resolved and contributing/context_only")
    if value.decision == "excluded" and value.selection_role != "none":
        raise ExecutionRequestError("excluded decision must have selection_role none")
    for name, limit in (
        ("reason_namespace", 100),
        ("reason_version", 50),
        ("primary_reason_code", 100),
    ):
        _nonblank(getattr(value, name), name, max_length=limit)
    _canonical_object(value.content, "decision.content")


def build_selection_decision_payload(
    *,
    execution_digest: bytes,
    member: Mapping[str, Any],
    decision: SelectionDecisionInput,
) -> dict[str, CanonicalJsonValue]:
    validate_decision(decision)
    return {
        "artifact_type": "scientific_evidence_selection_decision",
        "content": decision.content,
        "decision": decision.decision,
        "execution_semantic_digest": _digest_hex(execution_digest, "execution_digest"),
        "member_identity_digest": _digest_hex(
            bytes(member["member_identity_digest"]), "member_identity_digest"
        ),
        "member_semantic_digest": _digest_hex(
            bytes(member["member_semantic_digest"]), "member_semantic_digest"
        ),
        "primary_reason_code": decision.primary_reason_code,
        "reason_namespace": decision.reason_namespace,
        "reason_version": decision.reason_version,
        "resolution_state": decision.resolution_state,
        "schema_version": "1",
        "selection_role": decision.selection_role,
        "snapshot_member_kind": member["member_kind"],
    }


def build_selection_manifest_payload(
    *, execution_digest: bytes, descriptors: list[dict[str, CanonicalJsonValue]]
) -> dict[str, CanonicalJsonValue]:
    ordered = sorted(
        descriptors,
        key=lambda item: (
            bytes.fromhex(str(item["member_identity_digest"])),
            bytes.fromhex(str(item["member_semantic_digest"])),
            bytes.fromhex(str(item["decision_digest"])),
        ),
    )
    return {
        "artifact_type": "scientific_evidence_selection_manifest",
        "decision_count": len(ordered),
        "execution_semantic_digest": _digest_hex(execution_digest, "execution_digest"),
        "ordered_decisions": ordered,
        "schema_version": "1",
    }


def build_component_payload(
    *, execution_digest: bytes, ordinal: int, component: ResultComponentInput
) -> dict[str, CanonicalJsonValue]:
    if not isinstance(component, ResultComponentInput):
        raise ExecutionRequestError("result component must use ResultComponentInput")
    for name, limit in (
        ("component_kind", 100),
        ("component_schema_version", 50),
        ("component_role", 100),
    ):
        _nonblank(getattr(component, name), name, max_length=limit)
    _canonical_object(component.content, "component.content")
    return {
        "artifact_type": "scientific_evaluation_result_component",
        "component_kind": component.component_kind,
        "component_ordinal": ordinal,
        "component_role": component.component_role,
        "component_schema_version": component.component_schema_version,
        "content": component.content,
        "execution_semantic_digest": _digest_hex(execution_digest, "execution_digest"),
        "schema_version": "1",
    }


def build_result_payload(
    *,
    execution_digest: bytes,
    output: PublicationOutputInput,
    component_descriptors: list[dict[str, CanonicalJsonValue]],
) -> dict[str, CanonicalJsonValue]:
    for name, limit in (
        ("result_kind", 100),
        ("result_schema_version", 50),
        ("scientific_status_namespace", 100),
        ("scientific_status_version", 50),
        ("scientific_status_code", 100),
    ):
        _nonblank(getattr(output, name), name, max_length=limit)
    _canonical_object(output.result_content, "result_content")
    return {
        "artifact_type": "scientific_evaluation_result",
        "components": component_descriptors,
        "content": output.result_content,
        "execution_semantic_digest": _digest_hex(execution_digest, "execution_digest"),
        "result_kind": output.result_kind,
        "result_schema_version": output.result_schema_version,
        "schema_version": "1",
        "scientific_status": {
            "code": output.scientific_status_code,
            "namespace": output.scientific_status_namespace,
            "version": output.scientific_status_version,
        },
    }


def build_trace_payload(
    *,
    execution_digest: bytes,
    protocol_digest: bytes,
    snapshot_digest: bytes,
    input_digest: bytes,
    selection_digest: bytes,
    result_digest: bytes,
    trace_schema_version: str,
    content: dict[str, CanonicalJsonValue],
) -> dict[str, CanonicalJsonValue]:
    _nonblank(trace_schema_version, "trace_schema_version", max_length=50)
    _canonical_object(content, "trace_content")
    return {
        "artifact_type": "scientific_evaluation_trace",
        "content": content,
        "evidence_snapshot_digest": _digest_hex(snapshot_digest, "snapshot_digest"),
        "execution_semantic_digest": _digest_hex(execution_digest, "execution_digest"),
        "input_digest": _digest_hex(input_digest, "input_digest"),
        "protocol_digest": _digest_hex(protocol_digest, "protocol_digest"),
        "result_digest": _digest_hex(result_digest, "result_digest"),
        "schema_version": "1",
        "selection_digest": _digest_hex(selection_digest, "selection_digest"),
        "trace_schema_version": trace_schema_version,
    }


def build_publication_bundle_payload(
    *,
    execution_digest: bytes,
    protocol_digest: bytes,
    snapshot_digest: bytes,
    input_digest: bytes,
    configuration_digest: bytes,
    selection_digest: bytes,
    result_digest: bytes,
    trace_digest: bytes,
) -> dict[str, CanonicalJsonValue]:
    return {
        "artifact_type": "scientific_evaluation_publication_bundle",
        "configuration_digest": _digest_hex(configuration_digest, "configuration_digest"),
        "evidence_snapshot_digest": _digest_hex(snapshot_digest, "snapshot_digest"),
        "input_digest": _digest_hex(input_digest, "input_digest"),
        "protocol_digest": _digest_hex(protocol_digest, "protocol_digest"),
        "result_digest": _digest_hex(result_digest, "result_digest"),
        "schema_version": "1",
        "selection_digest": _digest_hex(selection_digest, "selection_digest"),
        "semantic_execution_digest": _digest_hex(execution_digest, "execution_digest"),
        "trace_digest": _digest_hex(trace_digest, "trace_digest"),
    }


def build_replay_verification_payload(
    *,
    replay_execution_digest: bytes,
    comparison_execution_digest: bytes,
    comparison_bundle_digest: bytes,
    expected_selection_digest: bytes,
    expected_result_digest: bytes,
    expected_trace_digest: bytes,
    recomputed_selection_digest: bytes,
    recomputed_result_digest: bytes,
    recomputed_trace_digest: bytes,
) -> tuple[dict[str, CanonicalJsonValue], str]:
    matches = {
        "result": recomputed_result_digest == expected_result_digest,
        "selection": recomputed_selection_digest == expected_selection_digest,
        "trace": recomputed_trace_digest == expected_trace_digest,
    }
    status = "matched" if all(matches.values()) else "mismatch"
    return {
        "artifact_type": "scientific_evaluation_replay_verification",
        "comparison_publication_bundle_digest": _digest_hex(
            comparison_bundle_digest, "comparison_bundle_digest"
        ),
        "comparison_semantic_execution_digest": _digest_hex(
            comparison_execution_digest, "comparison_execution_digest"
        ),
        "expected_roots": {
            "result_digest": _digest_hex(expected_result_digest, "expected_result_digest"),
            "selection_digest": _digest_hex(
                expected_selection_digest, "expected_selection_digest"
            ),
            "trace_digest": _digest_hex(expected_trace_digest, "expected_trace_digest"),
        },
        "recomputed_roots": {
            "result_digest": _digest_hex(
                recomputed_result_digest, "recomputed_result_digest"
            ),
            "selection_digest": _digest_hex(
                recomputed_selection_digest, "recomputed_selection_digest"
            ),
            "trace_digest": _digest_hex(
                recomputed_trace_digest, "recomputed_trace_digest"
            ),
        },
        "replay_semantic_execution_digest": _digest_hex(
            replay_execution_digest, "replay_execution_digest"
        ),
        "root_matches": matches,
        "schema_version": "1",
        "verification_status": status,
    }, status
