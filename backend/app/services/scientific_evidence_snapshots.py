"""Deterministic builder/finalizer for protocol-independent evidence snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any
from uuid import UUID, uuid4

from app.repositories.scientific_evidence_snapshots import (
    PostgresScientificEvidenceSnapshotRepository,
    ScientificEvidenceSnapshotMemberRow,
    ScientificEvidenceSnapshotRow,
)
from app.scientific_evaluation.canonicalization import (
    CANONICALIZATION_VERSION,
    DIGEST_ALGORITHM,
    canonical_sha256,
)
from app.scientific_evaluation.errors import (
    DuplicateSnapshotMemberError,
    IncompatibleCanonicalSnapshotError,
    SnapshotAlreadySealedError,
    SnapshotFinalizationError,
    SnapshotMemberError,
    SnapshotProvenanceError,
    SnapshotRequestError,
)
from app.scientific_evaluation.snapshots import (
    CanonicalJsonValue,
    CanonicalMemberDescriptor,
    SnapshotConstructionRequest,
    SnapshotMemberInput,
    build_manifest_payload,
    build_member_identity_payload,
    build_query_payload,
    canonical_date,
    canonical_decimal,
    canonical_member_descriptors,
    canonical_timestamp,
    normalize_database_json,
)
from app.services.scientific_evaluation_artifacts import (
    PersistedScientificArtifact,
    ScientificArtifactWriteRequest,
    ScientificArtifactWriter,
)


_POLICY_KEY = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


@dataclass(frozen=True)
class ScientificEvidenceSnapshotBuildResult:
    snapshot: ScientificEvidenceSnapshotRow
    canonical_winner_reused: bool


@dataclass(frozen=True)
class _PreparedMember:
    requested: SnapshotMemberInput
    assessment_id: int
    finding_id: int | None
    ingestion_run_id: int
    source_dataset_release_id: int
    status_as_of: str
    identity_digest: bytes
    artifact: PersistedScientificArtifact

    @property
    def descriptor(self) -> CanonicalMemberDescriptor:
        return CanonicalMemberDescriptor(
            member_kind=self.requested.member_kind,
            member_identity_digest=self.identity_digest,
            member_semantic_digest=self.artifact.artifact.content_digest,
        )


def _canonical_field(value: Any, field: str) -> CanonicalJsonValue:
    value_type = type(value)
    if value is None or value_type in (bool, int, str):
        return value
    if value_type is Decimal:
        return canonical_decimal(value)
    if value_type is datetime:
        return canonical_timestamp(value, field)
    if value_type is date:
        return canonical_date(value)
    if value_type is UUID:
        return str(value)
    if value_type in (list, dict):
        return normalize_database_json(value)
    raise SnapshotProvenanceError(
        f"{field} has unsupported provenance value type {value_type.__name__}"
    )


def _canonical_object(values: dict[str, Any], prefix: str) -> dict[str, CanonicalJsonValue]:
    return {
        key: _canonical_field(value, f"{prefix}.{key}")
        for key, value in values.items()
    }


class ScientificEvidenceSnapshotService:
    """Construct and seal one snapshot inside a caller-owned transaction."""

    def __init__(
        self,
        repository: PostgresScientificEvidenceSnapshotRepository | None = None,
        artifact_writer: ScientificArtifactWriter | None = None,
    ):
        self.repository = repository or PostgresScientificEvidenceSnapshotRepository()
        self.artifact_writer = artifact_writer or ScientificArtifactWriter()

    def build_and_seal(
        self,
        cursor,
        request: SnapshotConstructionRequest,
    ) -> ScientificEvidenceSnapshotBuildResult:
        snapshot = self.create_building(cursor, request)
        return self.finalize(cursor, snapshot.id, sealed_by=request.sealed_by)

    def create_building(
        self,
        cursor,
        request: SnapshotConstructionRequest,
    ) -> ScientificEvidenceSnapshotRow:
        """Persist one complete building snapshot in the caller transaction."""

        self._validate_request(request)
        query_payload = build_query_payload(request)
        query_artifact = self.artifact_writer.write_verified_inline(
            cursor,
            ScientificArtifactWriteRequest(
                "scientific_evidence_snapshot_query", "1", query_payload
            ),
        )
        snapshot = self.repository.insert_building_snapshot(
            cursor,
            snapshot_key=uuid4(),
            snapshot_policy_key=request.snapshot_policy_key,
            snapshot_policy_version=request.snapshot_policy_version,
            as_of=request.as_of,
            evidence_cutoff=request.evidence_cutoff,
            query_definition_artifact_id=query_artifact.artifact.id,
            canonicalization_version=CANONICALIZATION_VERSION,
            digest_algorithm=DIGEST_ALGORITHM,
            created_by=request.created_by,
        )
        prepared = [
            self._prepare_member(cursor, member)
            for member in request.members
        ]
        prepared.sort(key=lambda member: member.descriptor.order_key())
        for ordinal, member in enumerate(prepared):
            self.repository.insert_member(
                cursor,
                snapshot_id=snapshot.id,
                member_kind=member.requested.member_kind,
                finding_id=member.finding_id,
                assessment_id=member.assessment_id,
                ingestion_run_id=member.ingestion_run_id,
                source_dataset_release_id=member.source_dataset_release_id,
                member_identity_digest=member.identity_digest,
                member_payload_artifact_id=member.artifact.artifact.id,
                member_semantic_digest=member.artifact.artifact.content_digest,
                membership_ordinal=ordinal,
                status_as_of=member.status_as_of,
            )
        return snapshot

    def finalize(
        self,
        cursor,
        snapshot_id: int,
        *,
        sealed_by: str,
    ) -> ScientificEvidenceSnapshotBuildResult:
        if not isinstance(snapshot_id, int) or snapshot_id <= 0:
            raise SnapshotRequestError("snapshot_id must be a positive integer")
        if not isinstance(sealed_by, str) or not sealed_by.strip():
            raise SnapshotRequestError("sealed_by must be nonblank")
        snapshot = self.repository.load_snapshot(cursor, snapshot_id, for_update=True)
        if snapshot is None:
            raise SnapshotRequestError("snapshot does not exist")
        if snapshot.status == "sealed":
            return ScientificEvidenceSnapshotBuildResult(snapshot, True)
        if snapshot.status != "building":
            raise SnapshotAlreadySealedError(
                f"unsupported snapshot lifecycle state: {snapshot.status}"
            )

        stored_members = self.repository.load_members(
            cursor, snapshot.id, for_update=True
        )
        revalidated: list[tuple[ScientificEvidenceSnapshotMemberRow, _PreparedMember]] = []
        for stored in stored_members:
            prepared = self._prepare_member(
                cursor,
                SnapshotMemberInput(
                    member_kind=stored.member_kind,
                    assessment_id=stored.assessment_id,
                    finding_id=stored.finding_id,
                ),
            )
            if (
                prepared.identity_digest != stored.member_identity_digest
                or prepared.artifact.artifact.id != stored.member_payload_artifact_id
                or prepared.artifact.artifact.content_digest
                != stored.member_semantic_digest
                or prepared.status_as_of != stored.status_as_of
                or prepared.ingestion_run_id != stored.ingestion_run_id
                or prepared.source_dataset_release_id
                != stored.source_dataset_release_id
            ):
                raise SnapshotFinalizationError(
                    f"stored member {stored.id} no longer matches frozen provenance"
                )
            revalidated.append((stored, prepared))

        revalidated.sort(key=lambda item: item[1].descriptor.order_key())
        ordered_rows = tuple(item[0] for item in revalidated)
        self.repository.set_canonical_ordinals(cursor, ordered_rows)
        descriptors = [item[1].descriptor for item in revalidated]
        manifest_payload = build_manifest_payload(
            snapshot_policy_key=snapshot.snapshot_policy_key,
            snapshot_policy_version=snapshot.snapshot_policy_version,
            as_of=snapshot.as_of,
            evidence_cutoff=snapshot.evidence_cutoff,
            query_definition_digest=snapshot.query_definition_digest,
            descriptors=descriptors,
        )
        manifest_artifact = self.artifact_writer.write_verified_inline(
            cursor,
            ScientificArtifactWriteRequest(
                "scientific_evidence_snapshot_manifest", "1", manifest_payload
            ),
        )
        snapshot_digest = manifest_artifact.artifact.content_digest
        self.repository.acquire_digest_lock(cursor, snapshot_digest)
        winner = self.repository.load_sealed_by_digest(
            cursor,
            canonicalization_version=CANONICALIZATION_VERSION,
            digest_algorithm=DIGEST_ALGORITHM,
            snapshot_digest=snapshot_digest,
        )
        if winner is not None and winner.id != snapshot.id:
            self._verify_canonical_winner(
                cursor,
                winner=winner,
                building=snapshot,
                manifest_artifact_id=manifest_artifact.artifact.id,
                descriptors=descriptors,
            )
            self.repository.delete_building_snapshot(cursor, snapshot.id)
            return ScientificEvidenceSnapshotBuildResult(winner, True)

        sealed = self.repository.seal_snapshot(
            cursor,
            snapshot_id=snapshot.id,
            manifest_artifact_id=manifest_artifact.artifact.id,
            snapshot_digest=snapshot_digest,
            member_count=len(descriptors),
            sealed_by=sealed_by,
        )
        if sealed is None or sealed.status != "sealed":
            raise SnapshotFinalizationError("snapshot did not enter sealed state")
        return ScientificEvidenceSnapshotBuildResult(sealed, False)

    def _validate_request(self, request: SnapshotConstructionRequest) -> None:
        if not isinstance(request, SnapshotConstructionRequest):
            raise SnapshotRequestError("snapshot request must use the typed internal model")
        if not _POLICY_KEY.fullmatch(request.snapshot_policy_key):
            raise SnapshotRequestError("snapshot_policy_key is not canonical snake-case")
        for field, value in (
            ("snapshot_policy_version", request.snapshot_policy_version),
            ("created_by", request.created_by),
            ("sealed_by", request.sealed_by),
        ):
            if not isinstance(value, str) or not value.strip():
                raise SnapshotRequestError(f"{field} must be nonblank")
        canonical_timestamp(request.as_of, "as_of")
        canonical_timestamp(request.evidence_cutoff, "evidence_cutoff")
        if request.evidence_cutoff > request.as_of:
            raise SnapshotRequestError("evidence_cutoff cannot exceed as_of")
        build_query_payload(request)

        structural_keys: set[tuple[str, int, int | None]] = set()
        assessment_roles: dict[int, set[str]] = {}
        for member in request.members:
            self._validate_member_shape(member)
            key = member.structural_key()
            if key in structural_keys:
                raise DuplicateSnapshotMemberError(
                    f"duplicate structural snapshot member: {key}"
                )
            structural_keys.add(key)
            roles = assessment_roles.setdefault(member.assessment_id, set())
            roles.add(member.member_kind)
            if roles == {"assessment", "finding"}:
                raise SnapshotMemberError(
                    "assessment-only and finding members cannot coexist under policy v1"
                )

    @staticmethod
    def _validate_member_shape(member: SnapshotMemberInput) -> None:
        if not isinstance(member, SnapshotMemberInput):
            raise SnapshotMemberError("members must use SnapshotMemberInput")
        if member.member_kind not in ("finding", "assessment"):
            raise SnapshotMemberError("member_kind must be finding or assessment")
        if not isinstance(member.assessment_id, int) or member.assessment_id <= 0:
            raise SnapshotMemberError("assessment_id must be a positive integer")
        if member.member_kind == "finding":
            if not isinstance(member.finding_id, int) or member.finding_id <= 0:
                raise SnapshotMemberError("finding member requires a positive finding_id")
        elif member.finding_id is not None:
            raise SnapshotMemberError("assessment member cannot reference a finding")

    def _prepare_member(self, cursor, member: SnapshotMemberInput) -> _PreparedMember:
        self._validate_member_shape(member)
        resolved = self.repository.resolve_candidate(
            cursor,
            assessment_id=member.assessment_id,
            finding_id=member.finding_id,
        )
        if resolved is None:
            raise SnapshotProvenanceError(
                f"assessment {member.assessment_id} does not exist"
            )
        if resolved["run_release_id"] != resolved["source_dataset_release_id"]:
            raise SnapshotProvenanceError("assessment and ingestion release disagree")
        if member.member_kind == "finding":
            if resolved["finding_id"] is None:
                raise SnapshotProvenanceError(
                    f"finding {member.finding_id} does not exist"
                )
            if resolved["finding_assessment_id"] != member.assessment_id:
                raise SnapshotProvenanceError(
                    "finding does not belong to the requested assessment"
                )

        finding_content = self._finding_content(resolved) if member.finding_id else None
        finding_identity = self._finding_identity(resolved, finding_content)
        identity_payload = build_member_identity_payload(
            member_kind=member.member_kind,
            source_key=resolved["source_key"],
            dataset_key=resolved["dataset_key"],
            external_release_key=resolved["external_release_key"],
            run_key=str(resolved["run_key"]),
            assessment_source_record_key=resolved["assessment_source_record_key"],
            finding_identity=finding_identity,
        )
        identity_digest = canonical_sha256(identity_payload)
        member_payload: dict[str, CanonicalJsonValue] = {
            "artifact_type": "scientific_evidence_snapshot_member",
            "assessment_context": self._assessment_context(resolved),
            "candidate_identity": identity_payload,
            "evidence_linked_substance_identity": self._substance_identity(resolved),
            "finding_content": finding_content,
            "member_kind": member.member_kind,
            "provenance": self._provenance(resolved),
            "schema_version": "1",
            "status_as_of": resolved["assessment_status"],
        }
        artifact = self.artifact_writer.write_verified_inline(
            cursor,
            ScientificArtifactWriteRequest(
                "scientific_evidence_snapshot_member", "1", member_payload
            ),
        )
        return _PreparedMember(
            requested=member,
            assessment_id=member.assessment_id,
            finding_id=member.finding_id,
            ingestion_run_id=resolved["ingestion_run_id"],
            source_dataset_release_id=resolved["source_dataset_release_id"],
            status_as_of=resolved["assessment_status"],
            identity_digest=identity_digest,
            artifact=artifact,
        )

    @staticmethod
    def _finding_identity(
        resolved: dict[str, Any],
        finding_content: dict[str, CanonicalJsonValue] | None,
    ) -> dict[str, CanonicalJsonValue] | None:
        if finding_content is None:
            return None
        if resolved["source_finding_key"] is not None:
            return {"kind": "source_finding_key", "value": resolved["source_finding_key"]}
        if resolved["source_ordinal"] is not None:
            return {"kind": "source_ordinal", "value": resolved["source_ordinal"]}
        if resolved["finding_fingerprint"] is not None:
            return {
                "algorithm": resolved["fingerprint_algorithm"],
                "kind": "verified_finding_fingerprint",
                "value": resolved["finding_fingerprint"],
            }
        return {
            "kind": "frozen_finding_payload_digest",
            "value": canonical_sha256(finding_content).hex(),
        }

    @staticmethod
    def _assessment_context(resolved: dict[str, Any]) -> dict[str, CanonicalJsonValue]:
        return _canonical_object(
            {
                "assessment_data": resolved["assessment_data"],
                "assessment_status": resolved["assessment_status"],
                "assessment_type": resolved["assessment_type"],
                "assessment_version": resolved["assessment_version"],
                "checksum": resolved["assessment_checksum"],
                "conclusion_text": resolved["assessment_conclusion"],
                "document_reference": resolved["document_reference"],
                "external_assessment_id": resolved["external_assessment_id"],
                "external_assessment_version": resolved["external_assessment_version"],
                "normalized_checksum_algorithm": resolved["normalized_checksum_algorithm"],
                "normalized_checksum_value": resolved["normalized_checksum_value"],
                "published_at": resolved["published_at"],
                "raw_record": resolved["assessment_raw_record"],
                "source_record_key": resolved["assessment_source_record_key"],
                "valid_from": resolved["valid_from"],
                "valid_to": resolved["valid_to"],
            },
            "assessment_context",
        )

    @staticmethod
    def _finding_content(resolved: dict[str, Any]) -> dict[str, CanonicalJsonValue]:
        return _canonical_object(
            {
                "conclusion_text": resolved["finding_conclusion"],
                "endpoint": resolved["endpoint"],
                "evidence_type": resolved["evidence_type"],
                "finding_fingerprint": resolved["finding_fingerprint"],
                "finding_key": resolved["finding_key"],
                "fingerprint_algorithm": resolved["fingerprint_algorithm"],
                "population_context": resolved["population_context"],
                "raw_payload": resolved["finding_raw_payload"],
                "source_finding_key": resolved["source_finding_key"],
                "source_locator": resolved["source_locator"],
                "source_ordinal": resolved["source_ordinal"],
                "source_record_key": resolved["finding_source_record_key"],
                "unit": resolved["unit"],
                "value_numeric": resolved["value_numeric"],
                "value_text": resolved["value_text"],
            },
            "finding_content",
        )

    @staticmethod
    def _substance_identity(resolved: dict[str, Any]) -> dict[str, CanonicalJsonValue]:
        identifiers = [
            _canonical_object(identifier, "substance.identifier")
            for identifier in resolved["identifiers"]
        ]
        return {
            "description": resolved["substance_description"],
            "identifiers": identifiers,
            "normalized_name": resolved["normalized_name"],
            "preferred_name": resolved["preferred_name"],
            "scientific_name": resolved["scientific_name"],
            "status": resolved["substance_status"],
            "substance_type": resolved["substance_type"],
        }

    @staticmethod
    def _provenance(resolved: dict[str, Any]) -> dict[str, CanonicalJsonValue]:
        run_artifacts = [
            _canonical_object(artifact, "provenance.run_artifact")
            for artifact in resolved["run_artifacts"]
        ]
        return {
            "dataset": _canonical_object(
                {
                    "dataset_description": resolved["dataset_description"],
                    "dataset_key": resolved["dataset_key"],
                    "dataset_name": resolved["dataset_name"],
                },
                "provenance.dataset",
            ),
            "ingestion_run": _canonical_object(
                {
                    "acquisition_version": resolved["acquisition_version"],
                    "artifact_manifest_algorithm": resolved["artifact_manifest_algorithm"],
                    "artifact_manifest_fingerprint": resolved["artifact_manifest_fingerprint"],
                    "assessments_written": resolved["assessments_written"],
                    "completed_at": resolved["completed_at"],
                    "config_checksum_algorithm": resolved["config_checksum_algorithm"],
                    "config_checksum_value": resolved["config_checksum_value"],
                    "findings_written": resolved["findings_written"],
                    "idempotency_key": resolved["idempotency_key"],
                    "importer_name": resolved["importer_name"],
                    "importer_version": resolved["importer_version"],
                    "normalization_schema_version": resolved["normalization_schema_version"],
                    "parser_output_checksum_algorithm": resolved["parser_output_checksum_algorithm"],
                    "parser_output_checksum_value": resolved["parser_output_checksum_value"],
                    "parser_version": resolved["parser_version"],
                    "provenance": resolved["run_provenance"],
                    "records_accepted": resolved["records_accepted"],
                    "records_rejected": resolved["records_rejected"],
                    "records_seen": resolved["records_seen"],
                    "run_key": resolved["run_key"],
                    "run_status": resolved["run_status"],
                    "source_adapter_version": resolved["source_adapter_version"],
                    "started_at": resolved["started_at"],
                    "warnings_count": resolved["warnings_count"],
                },
                "provenance.ingestion_run",
            ),
            "release": _canonical_object(
                {
                    "acquired_at": resolved["acquired_at"],
                    "checksum": resolved["release_checksum"],
                    "checksum_algorithm": resolved["release_checksum_algorithm"],
                    "evidence_status_as_of": resolved["release_status"],
                    "external_release_key": resolved["external_release_key"],
                    "format": resolved["release_format"],
                    "license_text": resolved["license_text"],
                    "released_at": resolved["released_at"],
                    "source_url": resolved["release_source_url"],
                    "version_label": resolved["version_label"],
                },
                "provenance.release",
            ),
            "run_artifacts": run_artifacts,
            "source": _canonical_object(
                {
                    "authority_level": resolved["authority_level"],
                    "country": resolved["country"],
                    "is_authoritative": resolved["is_authoritative"],
                    "source_key": resolved["source_key"],
                    "source_name": resolved["source_name"],
                    "source_type": resolved["source_type"],
                    "url": resolved["source_url"],
                },
                "provenance.source",
            ),
        }

    def _verify_canonical_winner(
        self,
        cursor,
        *,
        winner: ScientificEvidenceSnapshotRow,
        building: ScientificEvidenceSnapshotRow,
        manifest_artifact_id: int,
        descriptors: list[CanonicalMemberDescriptor],
    ) -> None:
        expected_header = (
            building.snapshot_policy_key,
            building.snapshot_policy_version,
            building.as_of,
            building.evidence_cutoff,
            building.query_definition_artifact_id,
            manifest_artifact_id,
            len(descriptors),
        )
        actual_header = (
            winner.snapshot_policy_key,
            winner.snapshot_policy_version,
            winner.as_of,
            winner.evidence_cutoff,
            winner.query_definition_artifact_id,
            winner.manifest_artifact_id,
            winner.member_count,
        )
        if actual_header != expected_header:
            raise IncompatibleCanonicalSnapshotError(
                "sealed canonical winner has incompatible snapshot roots"
            )
        winner_members = self.repository.load_members(cursor, winner.id)
        actual_descriptors = canonical_member_descriptors(
            [
                CanonicalMemberDescriptor(
                    member_kind=member.member_kind,
                    member_identity_digest=member.member_identity_digest,
                    member_semantic_digest=member.member_semantic_digest,
                )
                for member in winner_members
            ]
        )
        expected_descriptors = canonical_member_descriptors(descriptors)
        if actual_descriptors != expected_descriptors:
            raise IncompatibleCanonicalSnapshotError(
                "sealed canonical winner has incompatible member roots"
            )
