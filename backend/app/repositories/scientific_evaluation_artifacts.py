"""Caller-transaction-owned PostgreSQL access for canonical artifact rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg2.extras import Json


@dataclass(frozen=True)
class ScientificArtifactRow:
    id: int
    artifact_kind: str
    schema_version: str
    canonicalization_version: str
    digest_algorithm: str
    content_digest: bytes
    content_length: int
    content_type: str
    json_payload: dict[str, Any] | None
    verified_at: datetime


@dataclass(frozen=True)
class ScientificArtifactLocationRow:
    id: int
    location_key: UUID
    artifact_id: int
    canonical_bytes: bytes
    location_status: str
    verified_at: datetime | None


_ARTIFACT_COLUMNS = (
    "id,artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
    "content_digest,content_length,content_type,json_payload,verified_at"
)


def _artifact_row(row) -> ScientificArtifactRow | None:
    if row is None:
        return None
    return ScientificArtifactRow(
        id=row[0],
        artifact_kind=row[1],
        schema_version=row[2],
        canonicalization_version=row[3],
        digest_algorithm=row[4],
        content_digest=bytes(row[5]),
        content_length=row[6],
        content_type=row[7],
        json_payload=row[8],
        verified_at=row[9],
    )


def _location_row(row) -> ScientificArtifactLocationRow:
    return ScientificArtifactLocationRow(
        id=row[0],
        location_key=row[1],
        artifact_id=row[2],
        canonical_bytes=bytes(row[3]),
        location_status=row[4],
        verified_at=row[5],
    )


class PostgresScientificArtifactRepository:
    """Perform artifact writes without committing or rolling back the caller."""

    def insert_artifact(
        self,
        cursor,
        *,
        artifact_kind: str,
        schema_version: str,
        canonicalization_version: str,
        digest_algorithm: str,
        content_digest: bytes,
        content_length: int,
        content_type: str,
        json_payload: dict[str, Any] | None,
    ) -> ScientificArtifactRow | None:
        cursor.execute(
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,json_payload,verified_at) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NOW()) "
            "ON CONFLICT(canonicalization_version,digest_algorithm,content_digest) "
            "DO NOTHING RETURNING " + _ARTIFACT_COLUMNS,
            (
                artifact_kind,
                schema_version,
                canonicalization_version,
                digest_algorithm,
                content_digest,
                content_length,
                content_type,
                Json(json_payload) if json_payload is not None else None,
            ),
        )
        return _artifact_row(cursor.fetchone())

    def load_artifact_for_update(
        self,
        cursor,
        *,
        canonicalization_version: str,
        digest_algorithm: str,
        content_digest: bytes,
    ) -> ScientificArtifactRow | None:
        cursor.execute(
            "SELECT " + _ARTIFACT_COLUMNS + " FROM scientific_evaluation_artifacts "
            "WHERE canonicalization_version=%s AND digest_algorithm=%s "
            "AND content_digest=%s FOR UPDATE",
            (canonicalization_version, digest_algorithm, content_digest),
        )
        return _artifact_row(cursor.fetchone())

    def load_inline_locations_for_update(
        self,
        cursor,
        artifact_id: int,
    ) -> tuple[ScientificArtifactLocationRow, ...]:
        cursor.execute(
            "SELECT id,location_key,artifact_id,canonical_bytes,location_status,verified_at "
            "FROM scientific_evaluation_artifact_locations "
            "WHERE artifact_id=%s AND storage_mode='inline' ORDER BY id FOR UPDATE",
            (artifact_id,),
        )
        return tuple(_location_row(row) for row in cursor.fetchall())

    def insert_verified_inline_location(
        self,
        cursor,
        *,
        location_key: UUID,
        artifact_id: int,
        canonical_bytes: bytes,
    ) -> ScientificArtifactLocationRow:
        cursor.execute(
            "INSERT INTO scientific_evaluation_artifact_locations "
            "(location_key,artifact_id,storage_mode,canonical_bytes,location_status,"
            "verified_at) VALUES(%s,%s,'inline',%s,'verified',NOW()) "
            "RETURNING id,location_key,artifact_id,canonical_bytes,location_status,verified_at",
            (str(location_key), artifact_id, canonical_bytes),
        )
        return _location_row(cursor.fetchone())
