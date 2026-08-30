"""Caller-transaction-owned PostgreSQL access for scientific evidence snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json
from typing import Any
from uuid import UUID


# PostgreSQL's two-int advisory-lock space gives snapshot sealing an explicit
# WYE-local namespace. The lock only coordinates contenders; the 0020 partial
# UNIQUE index remains the authority for canonical snapshot identity.
_SNAPSHOT_SEAL_LOCK_NAMESPACE = 0x57594553  # ASCII "WYES"


@dataclass(frozen=True)
class ScientificEvidenceSnapshotRow:
    id: int
    snapshot_key: UUID
    snapshot_policy_key: str
    snapshot_policy_version: str
    as_of: datetime
    evidence_cutoff: datetime
    query_definition_artifact_id: int
    query_definition_digest: bytes
    canonicalization_version: str
    digest_algorithm: str
    manifest_artifact_id: int | None
    snapshot_digest: bytes | None
    member_count: int | None
    status: str
    created_by: str
    sealed_by: str | None
    created_at: datetime
    sealed_at: datetime | None


@dataclass(frozen=True)
class ScientificEvidenceSnapshotMemberRow:
    id: int
    snapshot_id: int
    member_kind: str
    finding_id: int | None
    assessment_id: int
    ingestion_run_id: int
    source_dataset_release_id: int
    member_identity_digest: bytes
    member_payload_artifact_id: int
    member_semantic_digest: bytes
    membership_ordinal: int
    status_as_of: str


_SNAPSHOT_COLUMNS = (
    "s.id,s.snapshot_key,s.snapshot_policy_key,s.snapshot_policy_version,"
    "s.as_of,s.evidence_cutoff,s.query_definition_artifact_id,q.content_digest,"
    "s.canonicalization_version,s.digest_algorithm,s.manifest_artifact_id,"
    "s.snapshot_digest,s.member_count,s.status,s.created_by,s.sealed_by,"
    "s.created_at,s.sealed_at"
)
_MEMBER_COLUMNS = (
    "id,snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
    "source_dataset_release_id,member_identity_digest,member_payload_artifact_id,"
    "member_semantic_digest,membership_ordinal,status_as_of"
)


def _snapshot_row(row) -> ScientificEvidenceSnapshotRow | None:
    if row is None:
        return None
    return ScientificEvidenceSnapshotRow(
        id=row[0],
        snapshot_key=row[1],
        snapshot_policy_key=row[2],
        snapshot_policy_version=row[3],
        as_of=row[4],
        evidence_cutoff=row[5],
        query_definition_artifact_id=row[6],
        query_definition_digest=bytes(row[7]),
        canonicalization_version=row[8],
        digest_algorithm=row[9],
        manifest_artifact_id=row[10],
        snapshot_digest=None if row[11] is None else bytes(row[11]),
        member_count=row[12],
        status=row[13],
        created_by=row[14],
        sealed_by=row[15],
        created_at=row[16],
        sealed_at=row[17],
    )


def _member_row(row) -> ScientificEvidenceSnapshotMemberRow:
    return ScientificEvidenceSnapshotMemberRow(
        id=row[0],
        snapshot_id=row[1],
        member_kind=row[2],
        finding_id=row[3],
        assessment_id=row[4],
        ingestion_run_id=row[5],
        source_dataset_release_id=row[6],
        member_identity_digest=bytes(row[7]),
        member_payload_artifact_id=row[8],
        member_semantic_digest=bytes(row[9]),
        membership_ordinal=row[10],
        status_as_of=row[11],
    )


def _record(cursor, row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {column.name: value for column, value in zip(cursor.description, row)}


def _decode_json(value: str | None) -> Any:
    if value is None:
        return None
    return json.loads(value, parse_float=Decimal)


class PostgresScientificEvidenceSnapshotRepository:
    """Persist snapshot state without owning commit or rollback."""

    def insert_building_snapshot(
        self,
        cursor,
        *,
        snapshot_key: UUID,
        snapshot_policy_key: str,
        snapshot_policy_version: str,
        as_of: datetime,
        evidence_cutoff: datetime,
        query_definition_artifact_id: int,
        canonicalization_version: str,
        digest_algorithm: str,
        created_by: str,
    ) -> ScientificEvidenceSnapshotRow:
        cursor.execute(
            "INSERT INTO scientific_evidence_snapshots "
            "(snapshot_key,snapshot_policy_key,snapshot_policy_version,as_of,"
            "evidence_cutoff,query_definition_artifact_id,canonicalization_version,"
            "digest_algorithm,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "RETURNING id",
            (
                str(snapshot_key),
                snapshot_policy_key,
                snapshot_policy_version,
                as_of,
                evidence_cutoff,
                query_definition_artifact_id,
                canonicalization_version,
                digest_algorithm,
                created_by,
            ),
        )
        return self.load_snapshot(cursor, cursor.fetchone()[0])

    def load_snapshot(
        self,
        cursor,
        snapshot_id: int,
        *,
        for_update: bool = False,
    ) -> ScientificEvidenceSnapshotRow | None:
        cursor.execute(
            "SELECT " + _SNAPSHOT_COLUMNS + " FROM scientific_evidence_snapshots s "
            "JOIN scientific_evaluation_artifacts q "
            "ON q.id=s.query_definition_artifact_id WHERE s.id=%s"
            + (" FOR UPDATE OF s" if for_update else ""),
            (snapshot_id,),
        )
        return _snapshot_row(cursor.fetchone())

    def load_sealed_by_digest(
        self,
        cursor,
        *,
        canonicalization_version: str,
        digest_algorithm: str,
        snapshot_digest: bytes,
    ) -> ScientificEvidenceSnapshotRow | None:
        cursor.execute(
            "SELECT " + _SNAPSHOT_COLUMNS + " FROM scientific_evidence_snapshots s "
            "JOIN scientific_evaluation_artifacts q "
            "ON q.id=s.query_definition_artifact_id "
            "WHERE s.status='sealed' AND s.canonicalization_version=%s "
            "AND s.digest_algorithm=%s AND s.snapshot_digest=%s FOR SHARE OF s",
            (canonicalization_version, digest_algorithm, snapshot_digest),
        )
        return _snapshot_row(cursor.fetchone())

    def insert_member(
        self,
        cursor,
        *,
        snapshot_id: int,
        member_kind: str,
        finding_id: int | None,
        assessment_id: int,
        ingestion_run_id: int,
        source_dataset_release_id: int,
        member_identity_digest: bytes,
        member_payload_artifact_id: int,
        member_semantic_digest: bytes,
        membership_ordinal: int,
        status_as_of: str,
    ) -> ScientificEvidenceSnapshotMemberRow:
        cursor.execute(
            "INSERT INTO scientific_evidence_snapshot_members "
            "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
            "source_dataset_release_id,member_identity_digest,"
            "member_payload_artifact_id,member_semantic_digest,membership_ordinal,"
            "status_as_of) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING "
            + _MEMBER_COLUMNS,
            (
                snapshot_id,
                member_kind,
                finding_id,
                assessment_id,
                ingestion_run_id,
                source_dataset_release_id,
                member_identity_digest,
                member_payload_artifact_id,
                member_semantic_digest,
                membership_ordinal,
                status_as_of,
            ),
        )
        return _member_row(cursor.fetchone())

    def load_members(
        self,
        cursor,
        snapshot_id: int,
        *,
        for_update: bool = False,
    ) -> tuple[ScientificEvidenceSnapshotMemberRow, ...]:
        cursor.execute(
            "SELECT " + _MEMBER_COLUMNS + " FROM scientific_evidence_snapshot_members "
            "WHERE snapshot_id=%s ORDER BY member_kind COLLATE \"C\","
            "member_identity_digest,member_semantic_digest"
            + (" FOR UPDATE" if for_update else ""),
            (snapshot_id,),
        )
        return tuple(_member_row(row) for row in cursor.fetchall())

    def set_canonical_ordinals(
        self,
        cursor,
        members: tuple[ScientificEvidenceSnapshotMemberRow, ...],
    ) -> None:
        if all(member.membership_ordinal == index for index, member in enumerate(members)):
            return

        # The ordinal UNIQUE is immediate. Reassign as a permutation using one
        # guaranteed-free slot in [0, member_count], rather than relying on a
        # large offset that could overflow INTEGER or collide transiently.
        target_by_id = {member.id: ordinal for ordinal, member in enumerate(members)}
        current_by_id = {
            member.id: member.membership_ordinal for member in members
        }
        occupant_by_ordinal = {
            member.membership_ordinal: member.id for member in members
        }

        while any(
            current_by_id[member_id] != target
            for member_id, target in target_by_id.items()
        ):
            moved = False
            for member_id, target in target_by_id.items():
                current = current_by_id[member_id]
                if current == target or target in occupant_by_ordinal:
                    continue
                self._set_member_ordinal(cursor, member_id, target)
                del occupant_by_ordinal[current]
                occupant_by_ordinal[target] = member_id
                current_by_id[member_id] = target
                moved = True
            if moved:
                continue

            # Remaining rows form one or more cycles. With N occupied ordinals,
            # at least one value in [0, N] is free and safe for cycle breaking.
            spare = next(
                ordinal
                for ordinal in range(len(members) + 1)
                if ordinal not in occupant_by_ordinal
            )
            member_id = next(
                member_id
                for member_id, target in target_by_id.items()
                if current_by_id[member_id] != target
            )
            current = current_by_id[member_id]
            self._set_member_ordinal(cursor, member_id, spare)
            del occupant_by_ordinal[current]
            occupant_by_ordinal[spare] = member_id
            current_by_id[member_id] = spare

    @staticmethod
    def _set_member_ordinal(cursor, member_id: int, ordinal: int) -> None:
        cursor.execute(
            "UPDATE scientific_evidence_snapshot_members "
            "SET membership_ordinal=%s WHERE id=%s",
            (ordinal, member_id),
        )

    def acquire_digest_lock(self, cursor, snapshot_digest: bytes) -> None:
        digest_key = int.from_bytes(snapshot_digest[:4], "big", signed=True)
        cursor.execute(
            "SELECT pg_advisory_xact_lock(%s,%s)",
            (_SNAPSHOT_SEAL_LOCK_NAMESPACE, digest_key),
        )

    def seal_snapshot(
        self,
        cursor,
        *,
        snapshot_id: int,
        manifest_artifact_id: int,
        snapshot_digest: bytes,
        member_count: int,
        sealed_by: str,
    ) -> ScientificEvidenceSnapshotRow:
        cursor.execute(
            "UPDATE scientific_evidence_snapshots SET manifest_artifact_id=%s,"
            "snapshot_digest=%s,member_count=%s,status='sealed',sealed_by=%s,"
            "sealed_at=NOW() WHERE id=%s AND status='building' RETURNING id",
            (
                manifest_artifact_id,
                snapshot_digest,
                member_count,
                sealed_by,
                snapshot_id,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            return self.load_snapshot(cursor, snapshot_id, for_update=True)
        return self.load_snapshot(cursor, row[0])

    def delete_building_snapshot(self, cursor, snapshot_id: int) -> None:
        cursor.execute(
            "DELETE FROM scientific_evidence_snapshot_members WHERE snapshot_id=%s",
            (snapshot_id,),
        )
        cursor.execute(
            "DELETE FROM scientific_evidence_snapshots "
            "WHERE id=%s AND status='building'",
            (snapshot_id,),
        )

    def resolve_candidate(
        self,
        cursor,
        *,
        assessment_id: int,
        finding_id: int | None,
    ) -> dict[str, Any] | None:
        cursor.execute(
            """
            SELECT
              a.id AS assessment_id, a.substance_id, a.source_dataset_release_id,
              a.ingestion_run_id, a.source_record_key AS assessment_source_record_key,
              a.assessment_type, a.assessment_version, a.external_assessment_id,
              a.external_assessment_version, a.assessment_status, a.published_at,
              a.valid_from, a.valid_to, a.document_reference, a.conclusion_text AS assessment_conclusion,
              a.assessment_data::text AS assessment_data_json, a.checksum AS assessment_checksum,
              a.normalized_checksum_algorithm, a.normalized_checksum_value,
              a.raw_record::text AS assessment_raw_record_json,
              f.id AS finding_id, f.assessment_id AS finding_assessment_id,
              f.source_record_key AS finding_source_record_key,
              f.source_finding_key, f.source_ordinal, f.finding_key, f.endpoint,
              f.value_numeric, f.value_text, f.unit, f.population_context,
              f.evidence_type, f.conclusion_text AS finding_conclusion,
              f.source_locator, f.raw_payload::text AS finding_raw_payload_json,
              f.fingerprint_algorithm, f.finding_fingerprint,
              r.release_id AS run_release_id,
              r.run_key, r.idempotency_key, r.importer_name, r.importer_version,
              r.source_adapter_version, r.acquisition_version, r.parser_version,
              r.normalization_schema_version, r.artifact_manifest_algorithm,
              r.artifact_manifest_fingerprint, r.config_checksum_algorithm,
              r.config_checksum_value, r.parser_output_checksum_algorithm,
              r.parser_output_checksum_value, r.run_status, r.started_at,
              r.completed_at, r.records_seen, r.records_accepted, r.records_rejected,
              r.assessments_written, r.findings_written, r.warnings_count,
              r.provenance::text AS run_provenance_json,
              rel.external_release_key, rel.version_label, rel.released_at,
              rel.acquired_at, rel.source_url AS release_source_url,
              rel.checksum_algorithm AS release_checksum_algorithm,
              rel.checksum AS release_checksum, rel.format AS release_format,
              rel.release_status, rel.license_text,
              d.dataset_key, d.dataset_name, d.description AS dataset_description,
              src.source_key, src.source_name, src.source_type, src.url AS source_url,
              src.authority_level, src.country, src.is_authoritative,
              s.preferred_name, s.normalized_name, s.scientific_name,
              s.substance_type, s.status AS substance_status, s.description AS substance_description
            FROM scientific_assessments a
            JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id
            JOIN source_dataset_releases rel ON rel.id=a.source_dataset_release_id
            JOIN source_datasets d ON d.id=rel.dataset_id
            JOIN sources src ON src.id=d.source_id
            JOIN substances s ON s.id=a.substance_id
            LEFT JOIN scientific_assessment_findings f ON f.id=%s
            WHERE a.id=%s
            """,
            (finding_id, assessment_id),
        )
        row = _record(cursor, cursor.fetchone())
        if row is None:
            return None
        for key in (
            "assessment_data_json",
            "assessment_raw_record_json",
            "finding_raw_payload_json",
            "run_provenance_json",
        ):
            row[key.removesuffix("_json")] = _decode_json(row.pop(key))
        row["identifiers"] = self._load_identifiers(cursor, row["substance_id"])
        row["run_artifacts"] = self._load_run_artifacts(cursor, row["ingestion_run_id"])
        return row

    def _load_identifiers(self, cursor, substance_id: int) -> list[dict[str, Any]]:
        cursor.execute(
            """
            SELECT n.namespace_key,n.namespace_version,n.normalization_rule_version,
                   i.identifier_system,i.identifier_value,i.normalized_value,
                   i.is_primary,i.verification_status,
                   rel.external_release_key AS identifier_release_key,
                   r.run_key AS identifier_run_key,
                   i.provenance::text AS identifier_provenance_json
            FROM substance_identifiers i
            JOIN substance_identifier_namespaces n ON n.id=i.namespace_id
            LEFT JOIN source_dataset_releases rel ON rel.id=i.source_dataset_release_id
            LEFT JOIN scientific_ingestion_runs r ON r.id=i.ingestion_run_id
            WHERE i.substance_id=%s
            ORDER BY n.namespace_key COLLATE "C",n.namespace_version COLLATE "C",
                     i.normalized_value COLLATE "C",i.identifier_value COLLATE "C"
            """,
            (substance_id,),
        )
        records = []
        for result in cursor.fetchall():
            record = _record(cursor, result)
            record["identifier_provenance"] = _decode_json(
                record.pop("identifier_provenance_json")
            )
            if record["identifier_run_key"] is not None:
                record["identifier_run_key"] = str(record["identifier_run_key"])
            records.append(record)
        return records

    def _load_run_artifacts(self, cursor, ingestion_run_id: int) -> list[dict[str, Any]]:
        cursor.execute(
            """
            SELECT j.manifest_position,ra.artifact_key,ra.artifact_role,ra.format,
                   ra.media_type,ra.raw_checksum_algorithm,ra.raw_checksum_value,
                   ra.byte_size,ra.acquired_at,ra.validated_at,
                   so.storage_provider,so.bucket,so.object_key,so.object_version,
                   so.checksum_algorithm AS storage_checksum_algorithm,
                   so.checksum_value AS storage_checksum_value,
                   so.mime_type AS storage_mime_type,
                   so.byte_size AS storage_byte_size,
                   ra.provenance::text AS artifact_provenance_json
            FROM scientific_ingestion_run_artifacts j
            JOIN scientific_release_artifacts ra ON ra.id=j.release_artifact_id
            JOIN storage_objects so ON so.id=ra.storage_object_id
            WHERE j.ingestion_run_id=%s
            ORDER BY j.manifest_position
            """,
            (ingestion_run_id,),
        )
        records = []
        for result in cursor.fetchall():
            record = _record(cursor, result)
            record["artifact_provenance"] = _decode_json(
                record.pop("artifact_provenance_json")
            )
            records.append(record)
        return records
