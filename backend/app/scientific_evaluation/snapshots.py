"""Typed deterministic inputs and canonical payload helpers for evidence snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Mapping, TypeAlias

from app.scientific_evaluation.canonicalization import (
    CANONICALIZATION_VERSION,
    canonicalize_json,
)
from app.scientific_evaluation.errors import SnapshotRequestError


CanonicalJsonValue: TypeAlias = (
    None | bool | int | str | list["CanonicalJsonValue"] | dict[str, "CanonicalJsonValue"]
)
SnapshotMemberKind = Literal["finding", "assessment"]


@dataclass(frozen=True)
class SnapshotMemberInput:
    member_kind: SnapshotMemberKind
    assessment_id: int
    finding_id: int | None = None

    def structural_key(self) -> tuple[str, int, int | None]:
        return self.member_kind, self.assessment_id, self.finding_id


@dataclass(frozen=True)
class SnapshotConstructionRequest:
    snapshot_policy_key: str
    snapshot_policy_version: str
    as_of: datetime
    evidence_cutoff: datetime
    scope: Mapping[str, CanonicalJsonValue]
    technical_predicates: tuple[Mapping[str, CanonicalJsonValue], ...]
    members: tuple[SnapshotMemberInput, ...]
    created_by: str
    sealed_by: str


@dataclass(frozen=True)
class CanonicalMemberDescriptor:
    member_kind: SnapshotMemberKind
    member_identity_digest: bytes
    member_semantic_digest: bytes

    def payload(self) -> dict[str, CanonicalJsonValue]:
        return {
            "member_identity_digest": self.member_identity_digest.hex(),
            "member_kind": self.member_kind,
            "member_semantic_digest": self.member_semantic_digest.hex(),
        }

    def order_key(self) -> tuple[bytes, bytes, bytes]:
        return (
            self.member_kind.encode("ascii"),
            self.member_identity_digest,
            self.member_semantic_digest,
        )


def canonical_timestamp(value: datetime, field: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise SnapshotRequestError(f"{field} must be a timezone-aware datetime")
    try:
        utc = value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise SnapshotRequestError(f"{field} cannot be normalized to UTC") from exc
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def canonical_date(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def canonical_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if not value.is_finite():
        raise SnapshotRequestError("scientific decimal must be finite")
    if value.is_zero():
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text.startswith("+"):
        text = text[1:]
    return text


def normalize_database_json(value: Any) -> CanonicalJsonValue:
    """Normalize parsed PostgreSQL JSON into the canonical v1 value domain."""

    value_type = type(value)
    if value is None or value_type in (bool, int, str):
        return value
    if value_type is Decimal:
        return canonical_decimal(value)
    if value_type is list:
        return [normalize_database_json(item) for item in value]
    if value_type is dict:
        if any(type(key) is not str for key in value):
            raise SnapshotRequestError("database JSON object keys must be strings")
        return {
            key: normalize_database_json(item)
            for key, item in value.items()
        }
    raise SnapshotRequestError(
        f"unsupported database JSON value type: {value_type.__name__}"
    )


def build_query_payload(
    request: SnapshotConstructionRequest,
) -> dict[str, CanonicalJsonValue]:
    scope = normalize_database_json(dict(request.scope))
    predicates = [normalize_database_json(dict(item)) for item in request.technical_predicates]
    predicates.sort(key=canonicalize_json)
    return {
        "artifact_type": "scientific_evidence_snapshot_query",
        "as_of": canonical_timestamp(request.as_of, "as_of"),
        "canonicalization_version": CANONICALIZATION_VERSION,
        "evidence_cutoff": canonical_timestamp(
            request.evidence_cutoff, "evidence_cutoff"
        ),
        "schema_version": "1",
        "scope": scope,
        "snapshot_policy_key": request.snapshot_policy_key,
        "snapshot_policy_version": request.snapshot_policy_version,
        "technical_predicates": predicates,
    }


def build_member_identity_payload(
    *,
    member_kind: SnapshotMemberKind,
    source_key: str,
    dataset_key: str,
    external_release_key: str,
    run_key: str,
    assessment_source_record_key: str,
    finding_identity: dict[str, CanonicalJsonValue] | None,
) -> dict[str, CanonicalJsonValue]:
    return {
        "assessment_source_record_key": assessment_source_record_key,
        "dataset_key": dataset_key,
        "external_release_key": external_release_key,
        "finding_identity": finding_identity,
        "identity_schema_version": "1",
        "member_kind": member_kind,
        "run_key": run_key,
        "source_key": source_key,
    }


def canonical_member_descriptors(
    descriptors: list[CanonicalMemberDescriptor],
) -> list[CanonicalMemberDescriptor]:
    return sorted(descriptors, key=CanonicalMemberDescriptor.order_key)


def build_manifest_payload(
    *,
    snapshot_policy_key: str,
    snapshot_policy_version: str,
    as_of: datetime,
    evidence_cutoff: datetime,
    query_definition_digest: bytes,
    descriptors: list[CanonicalMemberDescriptor],
) -> dict[str, CanonicalJsonValue]:
    ordered = canonical_member_descriptors(descriptors)
    return {
        "artifact_type": "scientific_evidence_snapshot_manifest",
        "as_of": canonical_timestamp(as_of, "as_of"),
        "evidence_cutoff": canonical_timestamp(evidence_cutoff, "evidence_cutoff"),
        "member_count": len(ordered),
        "ordered_members": [descriptor.payload() for descriptor in ordered],
        "query_definition_digest": query_definition_digest.hex(),
        "schema_version": "1",
        "snapshot_policy_key": snapshot_policy_key,
        "snapshot_policy_version": snapshot_policy_version,
    }
