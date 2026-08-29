"""Add auditable, versioned scientific ingestion runs.

Revision ID: 0009_scientific_ingestion_runs
Revises: 0008_release_artifact_integrity
"""

from alembic import op


revision = "0009_scientific_ingestion_runs"
down_revision = "0008_release_artifact_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE scientific_ingestion_runs (
            id BIGSERIAL PRIMARY KEY,
            release_id BIGINT NOT NULL REFERENCES source_dataset_releases(id) ON DELETE RESTRICT,
            run_key UUID NOT NULL,
            idempotency_key VARCHAR(255),
            importer_name VARCHAR(100) NOT NULL,
            importer_version VARCHAR(100) NOT NULL,
            source_adapter_version VARCHAR(100) NOT NULL,
            acquisition_version VARCHAR(100) NOT NULL,
            parser_version VARCHAR(100) NOT NULL,
            normalization_schema_version VARCHAR(100) NOT NULL,
            artifact_manifest_algorithm VARCHAR(50) NOT NULL,
            artifact_manifest_fingerprint VARCHAR(128) NOT NULL,
            config_checksum_algorithm VARCHAR(50),
            config_checksum_value VARCHAR(128),
            parser_output_checksum_algorithm VARCHAR(50),
            parser_output_checksum_value VARCHAR(128),
            run_status VARCHAR(30) NOT NULL DEFAULT 'pending',
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            records_seen BIGINT NOT NULL DEFAULT 0,
            records_accepted BIGINT NOT NULL DEFAULT 0,
            records_rejected BIGINT NOT NULL DEFAULT 0,
            assessments_written BIGINT NOT NULL DEFAULT 0,
            findings_written BIGINT NOT NULL DEFAULT 0,
            warnings_count BIGINT NOT NULL DEFAULT 0,
            error_code VARCHAR(100),
            error_summary TEXT,
            provenance JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_scientific_ingestion_runs_run_key UNIQUE (run_key),
            CONSTRAINT ck_scientific_ingestion_runs_required_text CHECK (
                btrim(importer_name) <> ''
                AND btrim(importer_version) <> ''
                AND btrim(source_adapter_version) <> ''
                AND btrim(acquisition_version) <> ''
                AND btrim(parser_version) <> ''
                AND btrim(normalization_schema_version) <> ''
                AND (idempotency_key IS NULL OR btrim(idempotency_key) <> '')
            ),
            CONSTRAINT ck_scientific_ingestion_runs_manifest_algorithm CHECK (
                artifact_manifest_algorithm ~ '^[a-z0-9][a-z0-9_-]*$'
            ),
            CONSTRAINT ck_scientific_ingestion_runs_manifest_fingerprint CHECK (
                btrim(artifact_manifest_fingerprint) <> ''
                AND (
                    artifact_manifest_algorithm <> 'sha256'
                    OR artifact_manifest_fingerprint ~ '^[0-9a-f]{64}$'
                )
            ),
            CONSTRAINT ck_scientific_ingestion_runs_config_checksum_pair CHECK (
                (config_checksum_algorithm IS NULL) = (config_checksum_value IS NULL)
            ),
            CONSTRAINT ck_scientific_ingestion_runs_config_checksum CHECK (
                config_checksum_algorithm IS NULL
                OR (
                    config_checksum_algorithm ~ '^[a-z0-9][a-z0-9_-]*$'
                    AND btrim(config_checksum_value) <> ''
                    AND (
                        config_checksum_algorithm <> 'sha256'
                        OR config_checksum_value ~ '^[0-9a-f]{64}$'
                    )
                )
            ),
            CONSTRAINT ck_scientific_ingestion_runs_output_checksum_pair CHECK (
                (parser_output_checksum_algorithm IS NULL)
                = (parser_output_checksum_value IS NULL)
            ),
            CONSTRAINT ck_scientific_ingestion_runs_output_checksum CHECK (
                parser_output_checksum_algorithm IS NULL
                OR (
                    parser_output_checksum_algorithm ~ '^[a-z0-9][a-z0-9_-]*$'
                    AND btrim(parser_output_checksum_value) <> ''
                    AND (
                        parser_output_checksum_algorithm <> 'sha256'
                        OR parser_output_checksum_value ~ '^[0-9a-f]{64}$'
                    )
                )
            ),
            CONSTRAINT ck_scientific_ingestion_runs_status CHECK (
                run_status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')
            ),
            CONSTRAINT ck_scientific_ingestion_runs_status_timestamps CHECK (
                (run_status = 'pending' AND started_at IS NULL AND completed_at IS NULL)
                OR (run_status = 'running' AND started_at IS NOT NULL AND completed_at IS NULL)
                OR (
                    run_status IN ('succeeded', 'failed', 'cancelled')
                    AND started_at IS NOT NULL
                    AND completed_at IS NOT NULL
                    AND completed_at >= started_at
                )
            ),
            CONSTRAINT ck_scientific_ingestion_runs_failed_error CHECK (
                run_status <> 'failed'
                OR (error_code IS NOT NULL AND btrim(error_code) <> '')
            ),
            CONSTRAINT ck_scientific_ingestion_runs_nonnegative_counts CHECK (
                records_seen >= 0
                AND records_accepted >= 0
                AND records_rejected >= 0
                AND assessments_written >= 0
                AND findings_written >= 0
                AND warnings_count >= 0
            ),
            CONSTRAINT ck_scientific_ingestion_runs_record_counts CHECK (
                records_accepted + records_rejected <= records_seen
            )
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_scientific_ingestion_runs_idempotency
        ON scientific_ingestion_runs (
            release_id,
            artifact_manifest_algorithm,
            artifact_manifest_fingerprint,
            importer_name,
            importer_version,
            source_adapter_version,
            acquisition_version,
            parser_version,
            normalization_schema_version,
            COALESCE(config_checksum_algorithm, ''),
            COALESCE(config_checksum_value, ''),
            idempotency_key
        )
        WHERE idempotency_key IS NOT NULL
        """
    )
    op.execute(
        "CREATE INDEX idx_scientific_ingestion_runs_release_created "
        "ON scientific_ingestion_runs (release_id, created_at DESC, id DESC)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_ingestion_runs_status "
        "ON scientific_ingestion_runs (run_status)"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM scientific_ingestion_runs) THEN
                RAISE EXCEPTION 'Cannot downgrade 0009: scientific_ingestion_runs contains non-representable data.';
            END IF;
        END $$
        """
    )
    op.execute("DROP TABLE scientific_ingestion_runs")
