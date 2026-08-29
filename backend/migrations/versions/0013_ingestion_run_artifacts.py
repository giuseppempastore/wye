"""Persist exact artifact membership for scientific ingestion runs."""

from alembic import op

revision = "0013_ingestion_run_artifacts"
down_revision = "0012_ingredient_substance_guard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE scientific_ingestion_run_artifacts (
            ingestion_run_id BIGINT NOT NULL,
            release_artifact_id BIGINT NOT NULL,
            manifest_position INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_scientific_ingestion_run_artifacts PRIMARY KEY (ingestion_run_id, release_artifact_id),
            CONSTRAINT fk_scientific_ingestion_run_artifacts_run FOREIGN KEY (ingestion_run_id) REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT,
            CONSTRAINT fk_scientific_ingestion_run_artifacts_artifact FOREIGN KEY (release_artifact_id) REFERENCES scientific_release_artifacts(id) ON DELETE RESTRICT,
            CONSTRAINT uq_scientific_ingestion_run_artifacts_position UNIQUE (ingestion_run_id, manifest_position),
            CONSTRAINT ck_scientific_ingestion_run_artifacts_position CHECK (manifest_position >= 0)
        )
    """)
    op.execute("CREATE INDEX idx_scientific_ingestion_run_artifacts_artifact ON scientific_ingestion_run_artifacts (release_artifact_id)")


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM scientific_ingestion_run_artifacts) THEN
                RAISE EXCEPTION 'Cannot downgrade 0013: scientific_ingestion_run_artifacts contains non-representable provenance.';
            END IF;
        END $$
    """)
    op.execute("DROP TABLE scientific_ingestion_run_artifacts")
