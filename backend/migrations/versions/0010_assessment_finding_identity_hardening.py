"""Harden assessment and finding identity, reprocessing, and provenance.

Revision ID: 0010_assessment_finding_identity
Revises: 0009_scientific_ingestion_runs
"""

from alembic import op


revision = "0010_assessment_finding_identity"
down_revision = "0009_scientific_ingestion_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE scientific_assessments ADD COLUMN ingestion_run_id BIGINT")
    op.execute("ALTER TABLE scientific_assessments ADD COLUMN source_record_key VARCHAR(512)")
    op.execute("ALTER TABLE scientific_assessments ADD COLUMN external_assessment_version VARCHAR(255)")
    op.execute("ALTER TABLE scientific_assessments ADD COLUMN normalized_checksum_algorithm VARCHAR(50)")
    op.execute("ALTER TABLE scientific_assessments ADD COLUMN normalized_checksum_value VARCHAR(128)")
    op.execute("ALTER TABLE scientific_assessments ADD COLUMN raw_record JSONB")

    # A deterministic synthetic run per release preserves legacy assessment
    # provenance without claiming knowledge of the original parser or artifacts.
    op.execute(
        """
        INSERT INTO scientific_ingestion_runs (
            release_id, run_key, idempotency_key, importer_name, importer_version,
            source_adapter_version, acquisition_version, parser_version,
            normalization_schema_version, artifact_manifest_algorithm,
            artifact_manifest_fingerprint, run_status, started_at, completed_at,
            records_seen, records_accepted, assessments_written, provenance
        )
        SELECT
            a.source_dataset_release_id,
            (
                substr(md5('wye_legacy_assessment_run:' || a.source_dataset_release_id::text), 1, 8)
                || '-' || substr(md5('wye_legacy_assessment_run:' || a.source_dataset_release_id::text), 9, 4)
                || '-' || substr(md5('wye_legacy_assessment_run:' || a.source_dataset_release_id::text), 13, 4)
                || '-' || substr(md5('wye_legacy_assessment_run:' || a.source_dataset_release_id::text), 17, 4)
                || '-' || substr(md5('wye_legacy_assessment_run:' || a.source_dataset_release_id::text), 21, 12)
            )::uuid,
            'legacy_assessment_backfill',
            'legacy_backfill', 'legacy_unknown', 'legacy_unknown', 'legacy_unknown',
            'legacy_unknown', 'legacy_unknown', 'legacy_unknown',
            'legacy_release_' || a.source_dataset_release_id::text,
            'succeeded', MIN(a.created_at), MIN(a.created_at),
            count(*), count(*), count(*),
            jsonb_build_object(
                'synthetic_legacy_backfill', true,
                'migration', '0010_assessment_finding_identity_hardening'
            )
        FROM scientific_assessments a
        GROUP BY a.source_dataset_release_id
        """
    )
    op.execute(
        """
        UPDATE scientific_assessments a
        SET ingestion_run_id = r.id,
            source_record_key = 'legacy_assessment_' || a.id::text
        FROM scientific_ingestion_runs r
        WHERE r.release_id = a.source_dataset_release_id
          AND r.importer_name = 'legacy_backfill'
          AND r.idempotency_key = 'legacy_assessment_backfill'
          AND r.provenance @> '{"synthetic_legacy_backfill": true}'::jsonb
        """
    )
    op.execute("ALTER TABLE scientific_assessments ALTER COLUMN ingestion_run_id SET NOT NULL")
    op.execute("ALTER TABLE scientific_assessments ALTER COLUMN source_record_key SET NOT NULL")
    op.execute(
        "ALTER TABLE scientific_assessments ADD CONSTRAINT "
        "fk_scientific_assessments_ingestion_run FOREIGN KEY (ingestion_run_id) "
        "REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT"
    )
    op.execute(
        "ALTER TABLE scientific_assessments ADD CONSTRAINT "
        "uq_scientific_assessments_run_source_record "
        "UNIQUE (ingestion_run_id, source_record_key)"
    )
    op.execute(
        "ALTER TABLE scientific_assessments ADD CONSTRAINT "
        "ck_scientific_assessments_source_record_key "
        "CHECK (btrim(source_record_key) <> '')"
    )
    op.execute(
        "ALTER TABLE scientific_assessments ADD CONSTRAINT "
        "ck_scientific_assessments_normalized_checksum_pair CHECK ("
        "(normalized_checksum_algorithm IS NULL) = (normalized_checksum_value IS NULL))"
    )
    op.execute(
        "ALTER TABLE scientific_assessments ADD CONSTRAINT "
        "ck_scientific_assessments_normalized_checksum CHECK ("
        "normalized_checksum_algorithm IS NULL OR ("
        "normalized_checksum_algorithm ~ '^[a-z0-9][a-z0-9_-]*$' "
        "AND btrim(normalized_checksum_value) <> '' AND ("
        "normalized_checksum_algorithm <> 'sha256' "
        "OR normalized_checksum_value ~ '^[0-9a-f]{64}$')))"
    )
    op.execute(
        """
        DO $$
        DECLARE constraint_name TEXT;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'scientific_assessments'::regclass
              AND contype = 'u'
              AND pg_get_constraintdef(oid) =
                  'UNIQUE (substance_id, source_dataset_release_id, assessment_type, assessment_version)';
            IF constraint_name IS NULL THEN
                RAISE EXCEPTION 'Legacy scientific assessment identity constraint not found';
            END IF;
            EXECUTE format('ALTER TABLE scientific_assessments DROP CONSTRAINT %I', constraint_name);
        END $$
        """
    )
    op.execute(
        "CREATE INDEX idx_scientific_assessments_release_external_id "
        "ON scientific_assessments (source_dataset_release_id, external_assessment_id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_assessments_ingestion_run "
        "ON scientific_assessments (ingestion_run_id)"
    )

    op.execute("ALTER TABLE scientific_assessment_findings ADD COLUMN source_record_key VARCHAR(512)")
    op.execute("ALTER TABLE scientific_assessment_findings ADD COLUMN source_finding_key VARCHAR(255)")
    op.execute("ALTER TABLE scientific_assessment_findings ADD COLUMN source_ordinal INTEGER")
    op.execute("ALTER TABLE scientific_assessment_findings ADD COLUMN raw_payload JSONB")
    op.execute("ALTER TABLE scientific_assessment_findings ADD COLUMN fingerprint_algorithm VARCHAR(50)")
    op.execute("ALTER TABLE scientific_assessment_findings ADD COLUMN finding_fingerprint VARCHAR(128)")
    op.execute(
        "UPDATE scientific_assessment_findings "
        "SET source_record_key = 'legacy_finding_' || id::text"
    )
    op.execute("ALTER TABLE scientific_assessment_findings ALTER COLUMN source_record_key SET NOT NULL")
    op.execute(
        "ALTER TABLE scientific_assessment_findings ADD CONSTRAINT "
        "uq_scientific_assessment_findings_source_record "
        "UNIQUE (assessment_id, source_record_key)"
    )
    op.execute(
        "ALTER TABLE scientific_assessment_findings ADD CONSTRAINT "
        "ck_scientific_assessment_findings_source_record_key "
        "CHECK (btrim(source_record_key) <> '')"
    )
    op.execute(
        "ALTER TABLE scientific_assessment_findings ADD CONSTRAINT "
        "ck_scientific_assessment_findings_source_ordinal "
        "CHECK (source_ordinal IS NULL OR source_ordinal >= 0)"
    )
    op.execute(
        "ALTER TABLE scientific_assessment_findings ADD CONSTRAINT "
        "ck_scientific_assessment_findings_fingerprint_pair CHECK ("
        "(fingerprint_algorithm IS NULL) = (finding_fingerprint IS NULL))"
    )
    op.execute(
        "ALTER TABLE scientific_assessment_findings ADD CONSTRAINT "
        "ck_scientific_assessment_findings_fingerprint CHECK ("
        "fingerprint_algorithm IS NULL OR ("
        "fingerprint_algorithm ~ '^[a-z0-9][a-z0-9_-]*$' "
        "AND btrim(finding_fingerprint) <> '' AND ("
        "fingerprint_algorithm <> 'sha256' "
        "OR finding_fingerprint ~ '^[0-9a-f]{64}$')))"
    )
    op.execute(
        "ALTER TABLE scientific_assessment_findings ADD CONSTRAINT "
        "ck_scientific_assessment_findings_minimal_content CHECK ("
        "value_numeric IS NOT NULL OR value_text IS NOT NULL "
        "OR conclusion_text IS NOT NULL OR raw_payload IS NOT NULL "
        "OR finding_key IS NOT NULL OR endpoint IS NOT NULL "
        "OR source_locator IS NOT NULL)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_assessment_findings_assessment_source_key "
        "ON scientific_assessment_findings (assessment_id, source_finding_key) "
        "WHERE source_finding_key IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_scientific_assessment_findings_fingerprint "
        "ON scientific_assessment_findings (fingerprint_algorithm, finding_fingerprint) "
        "WHERE finding_fingerprint IS NOT NULL"
    )


def downgrade() -> None:
    # The legacy schema cannot represent new run-scoped identities or raw/checksum
    # metadata. Refuse downgrade instead of silently discarding those semantics.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM scientific_assessments a
                JOIN scientific_ingestion_runs r ON r.id = a.ingestion_run_id
                WHERE a.source_record_key <> 'legacy_assessment_' || a.id::text
                   OR a.external_assessment_version IS NOT NULL
                   OR a.normalized_checksum_algorithm IS NOT NULL
                   OR a.normalized_checksum_value IS NOT NULL
                   OR a.raw_record IS NOT NULL
                   OR r.release_id <> a.source_dataset_release_id
                   OR r.importer_name <> 'legacy_backfill'
                   OR r.idempotency_key IS DISTINCT FROM 'legacy_assessment_backfill'
                   OR NOT (r.provenance @> '{"synthetic_legacy_backfill": true}'::jsonb)
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0010: assessment identity or provenance is not representable by 0009';
            END IF;
            IF EXISTS (
                SELECT 1 FROM scientific_assessment_findings f
                WHERE f.source_record_key <> 'legacy_finding_' || f.id::text
                   OR f.source_finding_key IS NOT NULL
                   OR f.source_ordinal IS NOT NULL
                   OR f.raw_payload IS NOT NULL
                   OR f.fingerprint_algorithm IS NOT NULL
                   OR f.finding_fingerprint IS NOT NULL
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0010: finding identity or provenance is not representable by 0009';
            END IF;
            IF EXISTS (
                SELECT substance_id, source_dataset_release_id, assessment_type, assessment_version
                FROM scientific_assessments
                GROUP BY substance_id, source_dataset_release_id, assessment_type, assessment_version
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0010: assessments violate the legacy identity constraint';
            END IF;
        END $$
        """
    )

    op.execute("DROP INDEX idx_scientific_assessment_findings_fingerprint")
    op.execute("DROP INDEX idx_scientific_assessment_findings_assessment_source_key")
    op.execute("ALTER TABLE scientific_assessment_findings DROP CONSTRAINT ck_scientific_assessment_findings_minimal_content")
    op.execute("ALTER TABLE scientific_assessment_findings DROP CONSTRAINT ck_scientific_assessment_findings_fingerprint")
    op.execute("ALTER TABLE scientific_assessment_findings DROP CONSTRAINT ck_scientific_assessment_findings_fingerprint_pair")
    op.execute("ALTER TABLE scientific_assessment_findings DROP CONSTRAINT ck_scientific_assessment_findings_source_ordinal")
    op.execute("ALTER TABLE scientific_assessment_findings DROP CONSTRAINT ck_scientific_assessment_findings_source_record_key")
    op.execute("ALTER TABLE scientific_assessment_findings DROP CONSTRAINT uq_scientific_assessment_findings_source_record")
    op.execute("ALTER TABLE scientific_assessment_findings DROP COLUMN finding_fingerprint")
    op.execute("ALTER TABLE scientific_assessment_findings DROP COLUMN fingerprint_algorithm")
    op.execute("ALTER TABLE scientific_assessment_findings DROP COLUMN raw_payload")
    op.execute("ALTER TABLE scientific_assessment_findings DROP COLUMN source_ordinal")
    op.execute("ALTER TABLE scientific_assessment_findings DROP COLUMN source_finding_key")
    op.execute("ALTER TABLE scientific_assessment_findings DROP COLUMN source_record_key")

    op.execute("DROP INDEX idx_scientific_assessments_ingestion_run")
    op.execute("DROP INDEX idx_scientific_assessments_release_external_id")
    op.execute(
        "ALTER TABLE scientific_assessments ADD CONSTRAINT "
        "scientific_assessments_substance_release_type_version_key "
        "UNIQUE (substance_id, source_dataset_release_id, assessment_type, assessment_version)"
    )
    op.execute("ALTER TABLE scientific_assessments DROP CONSTRAINT ck_scientific_assessments_normalized_checksum")
    op.execute("ALTER TABLE scientific_assessments DROP CONSTRAINT ck_scientific_assessments_normalized_checksum_pair")
    op.execute("ALTER TABLE scientific_assessments DROP CONSTRAINT ck_scientific_assessments_source_record_key")
    op.execute("ALTER TABLE scientific_assessments DROP CONSTRAINT uq_scientific_assessments_run_source_record")
    op.execute("ALTER TABLE scientific_assessments DROP CONSTRAINT fk_scientific_assessments_ingestion_run")
    op.execute("ALTER TABLE scientific_assessments DROP COLUMN raw_record")
    op.execute("ALTER TABLE scientific_assessments DROP COLUMN normalized_checksum_value")
    op.execute("ALTER TABLE scientific_assessments DROP COLUMN normalized_checksum_algorithm")
    op.execute("ALTER TABLE scientific_assessments DROP COLUMN external_assessment_version")
    op.execute("ALTER TABLE scientific_assessments DROP COLUMN source_record_key")
    op.execute("ALTER TABLE scientific_assessments DROP COLUMN ingestion_run_id")
    op.execute(
        "DELETE FROM scientific_ingestion_runs r "
        "WHERE r.importer_name = 'legacy_backfill' "
        "AND r.idempotency_key = 'legacy_assessment_backfill' "
        "AND r.provenance @> '{\"synthetic_legacy_backfill\": true}'::jsonb"
    )
