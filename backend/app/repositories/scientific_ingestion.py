"""PostgreSQL persistence for source-agnostic scientific run orchestration."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg2.extras import Json, execute_values


@dataclass(frozen=True)
class ReleaseRow:
    id: int
    source_key: str
    dataset_key: str
    external_release_key: str


@dataclass(frozen=True)
class ArtifactRow:
    id: int
    release_id: int
    storage_object_id: int
    artifact_key: str
    artifact_role: str
    raw_checksum_algorithm: str
    raw_checksum_value: str
    byte_size: int | None
    storage_checksum_algorithm: str | None
    storage_checksum_value: str | None
    storage_byte_size: int | None


@dataclass(frozen=True)
class RunRow:
    id: int
    release_id: int
    run_key: UUID
    run_status: str
    started_at: datetime | None
    completed_at: datetime | None


class PostgresScientificIngestionRepository:
    IDEMPOTENCY_CONSTRAINT = "uq_scientific_ingestion_runs_idempotency"

    def resolve_release(self, cursor, source_key, dataset_key, external_release_key):
        cursor.execute("""
            SELECT r.id, s.source_key, d.dataset_key, r.external_release_key
            FROM sources s JOIN source_datasets d ON d.source_id=s.id
            JOIN source_dataset_releases r ON r.dataset_id=d.id
            WHERE s.source_key=%s AND d.dataset_key=%s AND r.external_release_key=%s
            FOR SHARE OF s, d, r
        """, (source_key, dataset_key, external_release_key))
        row = cursor.fetchone()
        return ReleaseRow(**row) if row else None

    def load_artifacts(self, cursor, release_id, artifact_keys):
        cursor.execute("""
            SELECT a.id,a.release_id,a.storage_object_id,a.artifact_key,a.artifact_role,
              a.raw_checksum_algorithm,a.raw_checksum_value,a.byte_size,
              o.checksum_algorithm storage_checksum_algorithm,o.checksum_value storage_checksum_value,
              o.byte_size storage_byte_size
            FROM scientific_release_artifacts a JOIN storage_objects o ON o.id=a.storage_object_id
            WHERE a.release_id=%s AND a.artifact_key=ANY(%s)
            ORDER BY a.artifact_key FOR SHARE OF a, o
        """, (release_id, list(artifact_keys)))
        return tuple(ArtifactRow(**row) for row in cursor.fetchall())

    def create_run(self, cursor, values):
        cursor.execute("""
            INSERT INTO scientific_ingestion_runs (
              release_id,run_key,idempotency_key,importer_name,importer_version,
              source_adapter_version,acquisition_version,parser_version,normalization_schema_version,
              artifact_manifest_algorithm,artifact_manifest_fingerprint,
              config_checksum_algorithm,config_checksum_value,run_status,provenance)
            VALUES (%(release_id)s,%(run_key)s,%(idempotency_key)s,%(importer_name)s,%(importer_version)s,
              %(source_adapter_version)s,%(acquisition_version)s,%(parser_version)s,%(normalization_schema_version)s,
              %(artifact_manifest_algorithm)s,%(artifact_manifest_fingerprint)s,
              %(config_checksum_algorithm)s,%(config_checksum_value)s,'pending',%(provenance)s)
            RETURNING id,release_id,run_key,run_status,started_at,completed_at
        """, {**values, "provenance": Json(values["provenance"])})
        return RunRow(**cursor.fetchone())

    def find_idempotent_run(self, cursor, v):
        cursor.execute("""
            SELECT id,release_id,run_key,run_status,started_at,completed_at FROM scientific_ingestion_runs
            WHERE release_id=%(release_id)s AND artifact_manifest_algorithm=%(artifact_manifest_algorithm)s
              AND artifact_manifest_fingerprint=%(artifact_manifest_fingerprint)s
              AND importer_name=%(importer_name)s AND importer_version=%(importer_version)s
              AND source_adapter_version=%(source_adapter_version)s AND acquisition_version=%(acquisition_version)s
              AND parser_version=%(parser_version)s AND normalization_schema_version=%(normalization_schema_version)s
              AND COALESCE(config_checksum_algorithm,'')=COALESCE(%(config_checksum_algorithm)s,'')
              AND COALESCE(config_checksum_value,'')=COALESCE(%(config_checksum_value)s,'')
              AND idempotency_key=%(idempotency_key)s
        """, v)
        row = cursor.fetchone()
        return RunRow(**row) if row else None

    def persist_membership(self, cursor, run_id, artifacts):
        execute_values(cursor, """INSERT INTO scientific_ingestion_run_artifacts
          (ingestion_run_id,release_artifact_id,manifest_position) VALUES %s
          ON CONFLICT (ingestion_run_id,release_artifact_id) DO NOTHING""",
          [(run_id, artifact.id, pos) for pos, artifact in enumerate(artifacts)])

    def membership_ids(self, cursor, run_id):
        cursor.execute("SELECT release_artifact_id FROM scientific_ingestion_run_artifacts WHERE ingestion_run_id=%s ORDER BY manifest_position", (run_id,))
        return tuple(row["release_artifact_id"] for row in cursor.fetchall())

    def get_run_by_key(self, cursor, run_key):
        cursor.execute("SELECT id,release_id,run_key,run_status,started_at,completed_at FROM scientific_ingestion_runs WHERE run_key=%s", (str(run_key),))
        row = cursor.fetchone()
        return RunRow(**row) if row else None

    def transition_run(self, cursor, run_id, from_statuses, to_status, values):
        sql = {
          "running": "run_status='running',started_at=%(at)s,completed_at=NULL",
          "succeeded": "run_status='succeeded',completed_at=%(at)s,records_seen=%(records_seen)s,records_accepted=%(records_accepted)s,records_rejected=%(records_rejected)s,assessments_written=%(assessments_written)s,findings_written=%(findings_written)s,warnings_count=%(warnings_count)s",
          "failed": "run_status='failed',completed_at=%(at)s,error_code=%(error_code)s,error_summary=%(error_summary)s",
          "cancelled": "run_status='cancelled',started_at=COALESCE(started_at,%(at)s),completed_at=%(at)s",
        }[to_status]
        cursor.execute(f"UPDATE scientific_ingestion_runs SET {sql} WHERE id=%(id)s AND run_status=ANY(%(states)s) RETURNING id,release_id,run_key,run_status,started_at,completed_at", {**values,"id":run_id,"states":list(from_statuses)})
        row = cursor.fetchone()
        return RunRow(**row) if row else None
