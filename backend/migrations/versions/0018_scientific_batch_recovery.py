"""Add persistent scientific batch recovery checkpoints.

Revision ID: 0018_scientific_batch_recovery
Revises: 0017_ingredient_mapping_history
"""

from alembic import op


revision = "0018_scientific_batch_recovery"
down_revision = "0017_ingredient_mapping_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE scientific_batch_plans (
            id BIGSERIAL PRIMARY KEY,
            plan_key VARCHAR(64) NOT NULL,
            definition_checksum_algorithm VARCHAR(50) NOT NULL DEFAULT 'sha256',
            definition_checksum_value VARCHAR(64) NOT NULL,
            plan_definition JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_scientific_batch_plans_key UNIQUE (plan_key),
            CONSTRAINT ck_scientific_batch_plans_key CHECK (plan_key ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_scientific_batch_plans_checksum CHECK (
                definition_checksum_algorithm = 'sha256'
                AND definition_checksum_value ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT ck_scientific_batch_plans_definition CHECK (
                jsonb_typeof(plan_definition) = 'object'
            )
        )
    """)
    op.execute("""
        CREATE TABLE scientific_batch_work_items (
            id BIGSERIAL PRIMARY KEY,
            batch_plan_id BIGINT NOT NULL REFERENCES scientific_batch_plans(id) ON DELETE RESTRICT,
            work_key VARCHAR(64) NOT NULL,
            source_key VARCHAR(100) NOT NULL,
            dataset_key VARCHAR(100) NOT NULL,
            external_release_key VARCHAR(255) NOT NULL,
            artifact_keys JSONB NOT NULL,
            source_adapter_version VARCHAR(100) NOT NULL,
            acquisition_version VARCHAR(100) NOT NULL,
            parser_version VARCHAR(100) NOT NULL,
            normalization_schema_version VARCHAR(100) NOT NULL,
            config_fingerprint VARCHAR(64) NOT NULL,
            work_identity JSONB NOT NULL,
            work_status VARCHAR(30) NOT NULL DEFAULT 'pending',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL,
            lease_token UUID,
            lease_expires_at TIMESTAMPTZ,
            artifact_manifest_fingerprint VARCHAR(64),
            ingestion_run_id BIGINT REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT,
            artifact_created BOOLEAN,
            records_processed BIGINT NOT NULL DEFAULT 0,
            assessments_written BIGINT NOT NULL DEFAULT 0,
            assessments_reused BIGINT NOT NULL DEFAULT 0,
            findings_written BIGINT NOT NULL DEFAULT 0,
            findings_reused BIGINT NOT NULL DEFAULT 0,
            error_class VARCHAR(100),
            error_detail TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_scientific_batch_work_plan_key UNIQUE (batch_plan_id, work_key),
            CONSTRAINT ck_scientific_batch_work_key CHECK (work_key ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_scientific_batch_work_config CHECK (
                config_fingerprint ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT ck_scientific_batch_work_identity CHECK (
                jsonb_typeof(work_identity) = 'object'
            ),
            CONSTRAINT ck_scientific_batch_work_artifacts CHECK (
                jsonb_typeof(artifact_keys) = 'array'
                AND jsonb_array_length(artifact_keys) > 0
            ),
            CONSTRAINT ck_scientific_batch_work_status CHECK (
                work_status IN ('pending','running','succeeded','failed','retryable','conflict')
            ),
            CONSTRAINT ck_scientific_batch_work_attempts CHECK (
                attempt_count >= 0 AND max_attempts > 0 AND attempt_count <= max_attempts
            ),
            CONSTRAINT ck_scientific_batch_work_counts CHECK (
                records_processed >= 0 AND assessments_written >= 0
                AND assessments_reused >= 0 AND findings_written >= 0
                AND findings_reused >= 0
            ),
            CONSTRAINT ck_scientific_batch_work_lease CHECK (
                (work_status = 'running' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL)
                OR (work_status <> 'running' AND lease_token IS NULL AND lease_expires_at IS NULL)
            )
        )
    """)
    op.execute("""
        CREATE INDEX idx_scientific_batch_work_status
        ON scientific_batch_work_items (work_status, lease_expires_at)
    """)
    op.execute("""
        CREATE INDEX idx_scientific_batch_work_ingestion_run
        ON scientific_batch_work_items (ingestion_run_id)
        WHERE ingestion_run_id IS NOT NULL
    """)
    op.execute("""
        CREATE TABLE scientific_batch_work_attempts (
            id BIGSERIAL PRIMARY KEY,
            work_item_id BIGINT NOT NULL REFERENCES scientific_batch_work_items(id) ON DELETE RESTRICT,
            attempt_number INTEGER NOT NULL,
            execution_key UUID NOT NULL,
            attempt_status VARCHAR(30) NOT NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            artifact_manifest_fingerprint VARCHAR(64),
            ingestion_run_id BIGINT REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT,
            artifact_created BOOLEAN,
            records_processed BIGINT NOT NULL DEFAULT 0,
            assessments_written BIGINT NOT NULL DEFAULT 0,
            assessments_reused BIGINT NOT NULL DEFAULT 0,
            findings_written BIGINT NOT NULL DEFAULT 0,
            findings_reused BIGINT NOT NULL DEFAULT 0,
            error_class VARCHAR(100),
            error_detail TEXT,
            result_summary JSONB,
            CONSTRAINT uq_scientific_batch_attempt_number UNIQUE (work_item_id, attempt_number),
            CONSTRAINT uq_scientific_batch_attempt_execution UNIQUE (execution_key),
            CONSTRAINT ck_scientific_batch_attempt_number CHECK (attempt_number > 0),
            CONSTRAINT ck_scientific_batch_attempt_status CHECK (
                attempt_status IN ('running','completed','failed','retryable','conflict','abandoned')
            ),
            CONSTRAINT ck_scientific_batch_attempt_counts CHECK (
                records_processed >= 0 AND assessments_written >= 0
                AND assessments_reused >= 0 AND findings_written >= 0
                AND findings_reused >= 0
            ),
            CONSTRAINT ck_scientific_batch_attempt_summary CHECK (
                result_summary IS NULL OR jsonb_typeof(result_summary) = 'object'
            )
        )
    """)
    op.execute("""
        CREATE INDEX idx_scientific_batch_attempt_work
        ON scientific_batch_work_attempts (work_item_id, attempt_number DESC)
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM scientific_batch_plans) THEN
                RAISE EXCEPTION 'Cannot downgrade 0018: scientific batch recovery history is not representable at 0017.';
            END IF;
        END $$
    """)
    op.execute("DROP TABLE scientific_batch_work_attempts")
    op.execute("DROP TABLE scientific_batch_work_items")
    op.execute("DROP TABLE scientific_batch_plans")
