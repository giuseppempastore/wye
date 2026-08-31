"""Frozen canonical models for Phase 7.6.4A target, mapping and input roots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Mapping, TypeAlias

from app.scientific_evaluation.canonicalization import (
    MAX_SIGNED_64,
    canonical_sha256,
    canonicalize_json,
)
from app.scientific_evaluation.errors import (
    MappingInputRequestError,
    UnsupportedEvaluationTargetError,
)


CanonicalJsonValue: TypeAlias = (
    None | bool | int | str | list["CanonicalJsonValue"] | dict[str, "CanonicalJsonValue"]
)
TargetType = Literal["substance", "ingredient"]
ResolutionState = Literal[
    "resolved", "empty", "partially_resolved", "history_unavailable"
]

IDENTITY_NAMESPACE = "wye_internal_id_v1"
MAPPING_POLICY_KEY = "ingredient_substance_authoritative_state"
MAPPING_POLICY_VERSION = "1"
TARGET_TYPES = frozenset({"substance", "ingredient"})
RELATIONSHIP_TYPES = frozenset(
    {"represents", "contains", "derived_from", "mixture_component", "equivalent_to"}
)
OBSERVATION_KINDS = frozenset(
    {"bridge", "proposal", "decision", "materialization", "closure", "authority_chain"}
)
REASON_IMPACTS: Mapping[str, str] = {
    "pending_proposal": "extends_set",
    "pending_review_bridge": "extends_set",
    "ambiguous_bridge": "extends_set",
    "rejected_decision": "none",
    "rejected_bridge": "none",
    "deferred_decision": "extends_set",
    "accepted_not_materialized_as_of": "extends_set",
    "accepted_authority_not_effective": "none",
    "materialization_inconsistent": "invalidates_reconstruction",
    "legacy_unreviewed_bridge": "extends_set",
    "uncontrolled_accepted_bridge": "extends_set",
    "history_incomplete": "invalidates_reconstruction",
    "closure_history_inconsistent": "invalidates_reconstruction",
    "out_of_effective_range": "none",
}
EXECUTION_TYPES = frozenset({"NORMAL", "REPLAY", "COUNTERFACTUAL", "REFRESH"})


@dataclass(frozen=True)
class CanonicalEvaluationInputRequest:
    target_type: TargetType
    target_id: int
    as_of: datetime


@dataclass(frozen=True)
class MappingMemberDescriptor:
    relationship_type: str
    substance_target_digest: bytes
    member_identity_digest: bytes
    member_semantic_digest: bytes

    def order_key(self) -> tuple[bytes, bytes, bytes, bytes]:
        return (
            self.relationship_type.encode("utf-8"),
            self.substance_target_digest,
            self.member_identity_digest,
            self.member_semantic_digest,
        )

    def payload(self) -> dict[str, CanonicalJsonValue]:
        return {
            "member_identity_digest": self.member_identity_digest.hex(),
            "member_semantic_digest": self.member_semantic_digest.hex(),
            "relationship_type": self.relationship_type,
            "substance_target_digest": self.substance_target_digest.hex(),
        }


@dataclass(frozen=True)
class NonMemberObservation:
    payload_value: dict[str, CanonicalJsonValue]
    subject_identity_digest: bytes
    semantic_digest: bytes

    @property
    def reason_code(self) -> str:
        return str(self.payload_value["reason_code"])

    @property
    def observation_kind(self) -> str:
        return str(self.payload_value["observation_kind"])

    @property
    def resolution_impact(self) -> str:
        return str(self.payload_value["resolution_impact"])

    def order_key(self) -> tuple[bytes, bytes, bytes, bytes]:
        return (
            self.reason_code.encode("utf-8"),
            self.observation_kind.encode("utf-8"),
            self.subject_identity_digest,
            self.semantic_digest,
        )

    def payload(self) -> dict[str, CanonicalJsonValue]:
        return self.payload_value


def validate_request(request: CanonicalEvaluationInputRequest) -> None:
    if not isinstance(request, CanonicalEvaluationInputRequest):
        raise MappingInputRequestError("canonical input request must use the typed model")
    if request.target_type not in TARGET_TYPES:
        raise UnsupportedEvaluationTargetError(
            f"unsupported evaluation target: {request.target_type}"
        )
    if (
        type(request.target_id) is not int
        or request.target_id <= 0
        or request.target_id > MAX_SIGNED_64
    ):
        raise MappingInputRequestError("target_id must be a positive signed 64-bit integer")
    canonical_timestamp(request.as_of, "as_of")


def canonical_timestamp(value: datetime, field: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise MappingInputRequestError(f"{field} must be a timezone-aware datetime")
    try:
        normalized = value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise MappingInputRequestError(f"{field} cannot be normalized to UTC") from exc
    return normalized.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def mapping_day(value: datetime) -> date:
    canonical_timestamp(value, "as_of")
    return value.astimezone(timezone.utc).date()


def canonical_date(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def canonical_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, Decimal) or not value.is_finite():
        raise MappingInputRequestError("mapping_confidence must be a finite Decimal")
    if value.is_zero():
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text[1:] if text.startswith("+") else text


def normalize_database_json(value: Any) -> CanonicalJsonValue:
    value_type = type(value)
    if value is None or value_type in (bool, int, str):
        return value
    if value_type is Decimal:
        return canonical_decimal(value)
    if value_type is list:
        return [normalize_database_json(item) for item in value]
    if value_type is dict:
        if any(type(key) is not str for key in value):
            raise MappingInputRequestError("database JSON object keys must be strings")
        return {key: normalize_database_json(item) for key, item in value.items()}
    raise MappingInputRequestError(
        f"unsupported database JSON value type: {value_type.__name__}"
    )


def build_target_payload(
    *, target_type: TargetType, row: Mapping[str, Any], as_of: datetime
) -> dict[str, CanonicalJsonValue]:
    if target_type not in TARGET_TYPES:
        raise UnsupportedEvaluationTargetError(f"unsupported evaluation target: {target_type}")
    identifiers: list[dict[str, CanonicalJsonValue]] = []
    if target_type == "ingredient":
        for system, column in (("cas", "cas_number"), ("einecs", "einecs_number")):
            value = row.get(column)
            if value is not None:
                identifiers.append({"identifier_system": system, "value": value})
        identifiers.sort(key=canonicalize_json)
        state: dict[str, CanonicalJsonValue] = {
            "canonical_name": row["canonical_name"],
            "common_name": row.get("common_name"),
            "declared_identifiers": identifiers,
            "ingredient_group": row.get("ingredient_group"),
            "status": row["status"],
        }
    else:
        state = {
            "normalized_name": row["normalized_name"],
            "preferred_name": row["preferred_name"],
            "scientific_name": row.get("scientific_name"),
            "status": row["status"],
            "substance_type": row["substance_type"],
        }
    return {
        "artifact_type": "scientific_evaluation_target",
        "entity_id": row["id"],
        "identity_as_of": canonical_timestamp(as_of, "as_of"),
        "identity_namespace": IDENTITY_NAMESPACE,
        "identity_recorded_at": canonical_timestamp(row["updated_at"], "updated_at"),
        "identity_resolution_state": "resolved",
        "identity_state": state,
        "schema_version": "1",
        "target_type": target_type,
    }


def build_authority_chain_identity(
    *, bridge_id: int, proposal: Mapping[str, Any], decision: Mapping[str, Any], materialization: Mapping[str, Any]
) -> dict[str, CanonicalJsonValue]:
    return {
        "bridge_id": bridge_id,
        "decision_id": decision["id"],
        "identity_namespace": IDENTITY_NAMESPACE,
        "identity_type": "ingredient_substance_mapping_authority_chain",
        "identity_version": "1",
        "materialization_id": materialization["id"],
        "proposal_id": proposal["id"],
        "proposal_key": str(proposal["proposal_key"]),
    }


def build_authority_chain_payload(
    *, bridge_id: int, proposal: Mapping[str, Any], decision: Mapping[str, Any], materialization: Mapping[str, Any]
) -> tuple[dict[str, CanonicalJsonValue], bytes]:
    identity = build_authority_chain_identity(
        bridge_id=bridge_id,
        proposal=proposal,
        decision=decision,
        materialization=materialization,
    )
    identity_digest = canonical_sha256(identity)
    payload: dict[str, CanonicalJsonValue] = {
        "authority_chain_identity_digest": identity_digest.hex(),
        "decision": {
            "created_at": canonical_timestamp(decision["created_at"], "decision.created_at"),
            "decision_id": decision["id"],
            "decision_type": decision["decision_type"],
            "effective_from": canonical_date(decision.get("effective_from")),
            "provenance": normalize_database_json(decision.get("provenance")),
            "reason_code": decision["reason_code"],
            "reviewed_at": canonical_timestamp(decision["reviewed_at"], "decision.reviewed_at"),
            "reviewed_by": decision["reviewed_by"],
        },
        "materialization": {
            "created_at": canonical_timestamp(materialization["created_at"], "materialization.created_at"),
            "materialization_id": materialization["id"],
            "materialization_status": materialization["materialization_status"],
            "materialized_at": canonical_timestamp(materialization["materialized_at"], "materialization.materialized_at"),
            "materialized_by": materialization["materialized_by"],
            "provenance": normalize_database_json(materialization.get("provenance")),
        },
        "proposal": {
            "created_at": canonical_timestamp(proposal["created_at"], "proposal.created_at"),
            "ingredient_id": proposal["ingredient_id"],
            "ingestion_run_id": proposal.get("ingestion_run_id"),
            "mapping_confidence": canonical_decimal(proposal.get("mapping_confidence")),
            "mapping_method": proposal["mapping_method"],
            "proposal_id": proposal["id"],
            "proposal_key": str(proposal["proposal_key"]),
            "proposed_by": proposal["proposed_by"],
            "provenance": normalize_database_json(proposal.get("provenance")),
            "relationship_type": proposal["relationship_type"],
            "source_dataset_release_id": proposal.get("source_dataset_release_id"),
            "substance_id": proposal["substance_id"],
        },
    }
    return payload, identity_digest


def order_authority_chains(
    chains: list[tuple[dict[str, CanonicalJsonValue], bytes]],
) -> list[dict[str, CanonicalJsonValue]]:
    return [
        payload
        for payload, _ in sorted(
            chains,
            key=lambda item: (
                str(item[0]["materialization"]["materialized_at"]).encode("utf-8"),
                item[1],
            ),
        )
    ]


def build_mapping_member_identity(bridge: Mapping[str, Any]) -> dict[str, CanonicalJsonValue]:
    return {
        "identity_namespace": IDENTITY_NAMESPACE,
        "identity_type": "ingredient_substance_mapping",
        "identity_version": "1",
        "ingredient_id": bridge["ingredient_id"],
        "mapping_row_id": bridge["id"],
        "relationship_type": bridge["relationship_type"],
        "substance_id": bridge["substance_id"],
    }


def build_mapping_member_payload(
    *,
    bridge: Mapping[str, Any],
    member_identity_digest: bytes,
    ingredient_target_digest: bytes,
    substance_target_digest: bytes,
    as_of: datetime,
    day: date,
    effective_valid_to: date | None,
    closure: Mapping[str, Any] | None,
    authority_chains: list[dict[str, CanonicalJsonValue]],
) -> dict[str, CanonicalJsonValue]:
    closure_payload: dict[str, CanonicalJsonValue] | None = None
    if closure is not None:
        closure_payload = {
            "closed_at": canonical_timestamp(closure["closed_at"], "closure.closed_at"),
            "closed_by": closure["closed_by"],
            "closure_id": closure["id"],
            "created_at": canonical_timestamp(closure["created_at"], "closure.created_at"),
            "provenance": normalize_database_json(closure.get("provenance")),
            "reason_code": closure["reason_code"],
            "valid_to": canonical_date(closure["valid_to"]),
        }
    return {
        "artifact_type": "scientific_mapping_state_member",
        "authority_chains": authority_chains,
        "effective_state": {
            "closure": closure_payload,
            "mapping_day": day.isoformat(),
            "mapping_status": "accepted",
            "recorded_as_of": canonical_timestamp(as_of, "as_of"),
            "valid_from": canonical_date(bridge.get("valid_from")),
            "valid_to": canonical_date(effective_valid_to),
        },
        "ingredient_target_digest": ingredient_target_digest.hex(),
        "mapping_policy_key": MAPPING_POLICY_KEY,
        "mapping_policy_version": MAPPING_POLICY_VERSION,
        "member_identity_digest": member_identity_digest.hex(),
        "provenance": {
            "ingestion_run_id": bridge.get("ingestion_run_id"),
            "mapping_method": bridge["mapping_method"],
            "source_dataset_release_id": bridge.get("source_dataset_release_id"),
        },
        "relationship_type": bridge["relationship_type"],
        "schema_version": "1",
        "substance_target_digest": substance_target_digest.hex(),
    }


def build_observation_subject_identity(
    *,
    observation_kind: str,
    bridge_id: int | None = None,
    proposal_id: int | None = None,
    decision_id: int | None = None,
    materialization_id: int | None = None,
    closure_id: int | None = None,
) -> dict[str, CanonicalJsonValue]:
    if observation_kind not in OBSERVATION_KINDS:
        raise MappingInputRequestError(f"unsupported observation_kind: {observation_kind}")
    if all(
        value is None
        for value in (bridge_id, proposal_id, decision_id, materialization_id, closure_id)
    ):
        raise MappingInputRequestError("observation subject requires a historical id")
    return {
        "bridge_id": bridge_id,
        "closure_id": closure_id,
        "decision_id": decision_id,
        "identity_namespace": IDENTITY_NAMESPACE,
        "identity_type": "mapping_non_member_observation_subject",
        "identity_version": "1",
        "materialization_id": materialization_id,
        "observation_kind": observation_kind,
        "proposal_id": proposal_id,
    }


def build_non_member_observation(
    *,
    observation_kind: str,
    reason_code: str,
    subject_identity: dict[str, CanonicalJsonValue],
    ingredient_id: int,
    recorded_at: datetime,
    bridge_id: int | None = None,
    substance_id: int | None = None,
    relationship_type: str | None = None,
    authority_chain_identity_digest: bytes | None = None,
    effective_from: date | None = None,
    effective_to: date | None = None,
) -> NonMemberObservation:
    if reason_code not in REASON_IMPACTS:
        raise MappingInputRequestError(f"unsupported mapping observation reason: {reason_code}")
    subject_digest = canonical_sha256(subject_identity)
    body: dict[str, CanonicalJsonValue] = {
        "authority_chain_identity_digest": (
            None if authority_chain_identity_digest is None else authority_chain_identity_digest.hex()
        ),
        "bridge_context": {
            "bridge_id": bridge_id,
            "ingredient_id": ingredient_id,
            "relationship_type": relationship_type,
            "substance_id": substance_id,
        },
        "effective_from": canonical_date(effective_from),
        "effective_to": canonical_date(effective_to),
        "observation_kind": observation_kind,
        "reason_code": reason_code,
        "recorded_at": canonical_timestamp(recorded_at, "observation.recorded_at"),
        "resolution_impact": REASON_IMPACTS[reason_code],
        "subject_identity": subject_identity,
        "subject_identity_digest": subject_digest.hex(),
    }
    semantic_digest = canonical_sha256(body)
    payload = dict(body)
    payload["observation_semantic_digest"] = semantic_digest.hex()
    return NonMemberObservation(payload, subject_digest, semantic_digest)


def canonical_member_descriptors(
    descriptors: list[MappingMemberDescriptor],
) -> list[MappingMemberDescriptor]:
    return sorted(descriptors, key=MappingMemberDescriptor.order_key)


def canonical_observations(
    observations: list[NonMemberObservation],
) -> list[NonMemberObservation]:
    unique: dict[bytes, NonMemberObservation] = {}
    for observation in observations:
        unique.setdefault(canonicalize_json(observation.payload()), observation)
    return sorted(unique.values(), key=NonMemberObservation.order_key)


def derive_resolution(
    *, member_count: int, observations: list[NonMemberObservation], visible_history: bool
) -> tuple[ResolutionState, list[str]]:
    invalidating = any(
        observation.resolution_impact == "invalidates_reconstruction"
        for observation in observations
    )
    extending = any(
        observation.resolution_impact == "extends_set" for observation in observations
    )
    if invalidating:
        state: ResolutionState = "history_unavailable"
        primary = "historical_reconstruction_incomplete"
    elif extending and member_count > 0:
        state = "partially_resolved"
        primary = "additional_candidates_unresolved"
    elif extending:
        state = "history_unavailable"
        primary = "historical_reconstruction_incomplete"
    elif member_count > 0:
        state = "resolved"
        primary = "authoritative_mapping_complete"
    else:
        state = "empty"
        primary = "no_authoritative_effective_mapping" if visible_history else "no_mapping_records"
    blocking_codes = sorted(
        {
            observation.reason_code
            for observation in observations
            if observation.resolution_impact != "none"
        },
        key=lambda value: value.encode("utf-8"),
    )
    return state, [primary, *blocking_codes]


def build_mapping_manifest_payload(
    *,
    as_of: datetime,
    day: date,
    ingredient_target_digest: bytes,
    members: list[MappingMemberDescriptor],
    observations: list[NonMemberObservation],
    visible_history: bool,
) -> tuple[dict[str, CanonicalJsonValue], ResolutionState]:
    ordered_members = canonical_member_descriptors(members)
    ordered_observations = canonical_observations(observations)
    state, reason_codes = derive_resolution(
        member_count=len(ordered_members),
        observations=ordered_observations,
        visible_history=visible_history,
    )
    return {
        "artifact_type": "scientific_mapping_state_manifest",
        "as_of": canonical_timestamp(as_of, "as_of"),
        "ingredient_target_digest": ingredient_target_digest.hex(),
        "mapping_day": day.isoformat(),
        "mapping_policy_key": MAPPING_POLICY_KEY,
        "mapping_policy_version": MAPPING_POLICY_VERSION,
        "member_count": len(ordered_members),
        "non_member_observations": [item.payload() for item in ordered_observations],
        "observation_count": len(ordered_observations),
        "ordered_members": [item.payload() for item in ordered_members],
        "resolution_reason_codes": reason_codes,
        "resolution_state": state,
        "schema_version": "1",
    }, state


def build_evaluation_input_payload(
    *,
    request: CanonicalEvaluationInputRequest,
    target_artifact_digest: bytes,
    mapping_resolution_state: str,
    mapping_manifest_digest: bytes | None,
) -> dict[str, CanonicalJsonValue]:
    if request.target_type == "ingredient":
        if mapping_manifest_digest is None or mapping_resolution_state not in {
            "resolved", "empty", "partially_resolved", "history_unavailable"
        }:
            raise MappingInputRequestError("ingredient input requires a canonical mapping manifest")
        applicability = "required"
    else:
        if mapping_manifest_digest is not None or mapping_resolution_state != "not_applicable":
            raise MappingInputRequestError("substance input mapping state must be not_applicable")
        applicability = "not_applicable"
    return {
        "artifact_type": "scientific_evaluation_input",
        "domain_inputs": [],
        "input_as_of": canonical_timestamp(request.as_of, "as_of"),
        "mapping_state": {
            "applicability": applicability,
            "manifest_digest": (
                None if mapping_manifest_digest is None else mapping_manifest_digest.hex()
            ),
            "resolution_state": mapping_resolution_state,
        },
        "schema_version": "1",
        "target": {
            "target_artifact_digest": target_artifact_digest.hex(),
            "target_type": request.target_type,
        },
    }
