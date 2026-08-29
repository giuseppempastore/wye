"""Idempotent PostgreSQL persistence for normalized scientific materializations."""

from dataclasses import dataclass

from psycopg2.extras import Json

from app.scientific_ingestion.checksums import assessment_checksum, finding_checksum
from app.scientific_ingestion.errors import ScientificPersistenceConflict


@dataclass(frozen=True)
class PersistedScientificRecord:
    assessment_id: int
    finding_ids: tuple[int, ...]
    assessment_created: bool
    findings_created: int


class PostgresScientificPersistenceRepository:
    """Persist one resolved record atomically through a caller-owned transaction."""

    def load_run_context(self, cursor, run_id):
        cursor.execute("""
            SELECT id,release_id,run_key,run_status,parser_version,
              normalization_schema_version,parser_output_checksum_algorithm,
              parser_output_checksum_value,artifact_manifest_algorithm,
              artifact_manifest_fingerprint,records_seen,records_accepted,
              records_rejected,assessments_written,findings_written,warnings_count
            FROM scientific_ingestion_runs WHERE id=%s FOR SHARE
        """, (run_id,))
        return cursor.fetchone()

    def persist_record(self, cursor, run_id, release_id, resolved):
        record = resolved.parsed_record
        if resolved.source_record_key != record.source_record_key:
            raise ScientificPersistenceConflict("resolved and parsed source record keys differ")
        expected_checksum = assessment_checksum(record.assessment)
        supplied = record.assessment.normalized_checksum
        if supplied is not None and (supplied.algorithm != "sha256" or supplied.value != expected_checksum):
            raise ScientificPersistenceConflict("supplied normalized assessment checksum differs")
        cursor.execute("""
            INSERT INTO scientific_assessments (
              substance_id,source_dataset_release_id,ingestion_run_id,source_record_key,
              assessment_type,assessment_version,external_assessment_id,
              external_assessment_version,assessment_status,published_at,
              document_reference,conclusion_text,assessment_data,raw_record,
              normalized_checksum_algorithm,normalized_checksum_value)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'sha256',%s)
            ON CONFLICT (ingestion_run_id,source_record_key) DO NOTHING
            RETURNING id
        """, (
            resolved.substance_id, release_id, run_id, record.source_record_key,
            record.assessment.assessment_type, record.assessment.assessment_version,
            record.assessment.external_assessment_id,
            record.assessment.external_assessment_version,
            record.assessment.assessment_status, record.assessment.published_at,
            record.assessment.document_reference, record.assessment.conclusion_text,
            Json(record.assessment.assessment_data) if record.assessment.assessment_data is not None else None,
            Json(record.assessment.raw_record) if record.assessment.raw_record is not None else None,
            expected_checksum,
        ))
        inserted = cursor.fetchone()
        created = inserted is not None
        if created:
            assessment_id = inserted["id"]
        else:
            cursor.execute("""
                SELECT id,substance_id,source_dataset_release_id,normalized_checksum_algorithm,
                       normalized_checksum_value
                FROM scientific_assessments
                WHERE ingestion_run_id=%s AND source_record_key=%s FOR SHARE
            """, (run_id, record.source_record_key))
            existing = cursor.fetchone()
            if existing is None or (
                existing["substance_id"] != resolved.substance_id
                or existing["source_dataset_release_id"] != release_id
                or existing["normalized_checksum_algorithm"] != "sha256"
                or existing["normalized_checksum_value"] != expected_checksum
            ):
                raise ScientificPersistenceConflict("assessment identity has conflicting content")
            assessment_id = existing["id"]

        finding_ids = []
        findings_created = 0
        for finding in record.findings:
            finding_id, finding_created = self._persist_finding(cursor, assessment_id, finding)
            finding_ids.append(finding_id)
            findings_created += int(finding_created)
        return PersistedScientificRecord(
            assessment_id, tuple(finding_ids), created, findings_created
        )

    def _persist_finding(self, cursor, assessment_id, finding):
        expected = finding_checksum(finding)
        supplied = finding.fingerprint
        if supplied is not None and (supplied.algorithm != "sha256" or supplied.value != expected):
            raise ScientificPersistenceConflict("supplied finding fingerprint differs")
        cursor.execute("""
            INSERT INTO scientific_assessment_findings (
              assessment_id,source_record_key,source_finding_key,source_ordinal,
              finding_key,endpoint,value_numeric,value_text,unit,population_context,
              evidence_type,conclusion_text,source_locator,raw_payload,
              fingerprint_algorithm,finding_fingerprint)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'sha256',%s)
            ON CONFLICT (assessment_id,source_record_key) DO NOTHING RETURNING id
        """, (
            assessment_id,finding.source_record_key,finding.source_finding_key,
            finding.source_ordinal,finding.finding_key,finding.endpoint,
            finding.value_numeric,finding.value_text,finding.unit,
            finding.population_context,finding.evidence_type,finding.conclusion_text,
            finding.source_locator,
            Json(finding.raw_payload) if finding.raw_payload is not None else None,
            expected,
        ))
        inserted = cursor.fetchone()
        if inserted is not None:
            return inserted["id"], True
        cursor.execute("""
            SELECT id,fingerprint_algorithm,finding_fingerprint
            FROM scientific_assessment_findings
            WHERE assessment_id=%s AND source_record_key=%s FOR SHARE
        """, (assessment_id,finding.source_record_key))
        existing = cursor.fetchone()
        if existing is None or existing["fingerprint_algorithm"] != "sha256" or existing["finding_fingerprint"] != expected:
            raise ScientificPersistenceConflict("finding identity has conflicting content")
        return existing["id"], False

    def finalize_succeeded(self, cursor, run_id, checksum, counters):
        cursor.execute("""
            UPDATE scientific_ingestion_runs SET run_status='succeeded',completed_at=NOW(),
              parser_output_checksum_algorithm='sha256',parser_output_checksum_value=%s,
              records_seen=%s,records_accepted=%s,records_rejected=%s,
              assessments_written=%s,findings_written=%s,warnings_count=%s
            WHERE id=%s AND run_status='running'
            RETURNING id
        """, (checksum,counters["records_seen"],counters["records_accepted"],
              counters["records_rejected"],counters["assessments_written"],
              counters["findings_written"],counters["warnings_count"],run_id))
        return cursor.fetchone() is not None
