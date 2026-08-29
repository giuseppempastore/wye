"""Harden ingredient-to-substance relationship integrity.

Revision ID: 0012_ingredient_substance_guard
Revises: 0011_substance_identity_registry
"""

from alembic import op


revision = "0012_ingredient_substance_guard"
down_revision = "0011_substance_identity_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ingredient_substances ADD COLUMN reviewed_by VARCHAR(255)")
    op.execute("ALTER TABLE ingredient_substances ADD COLUMN reviewed_at TIMESTAMPTZ")
    op.execute("ALTER TABLE ingredient_substances ADD COLUMN ingestion_run_id BIGINT")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM ingredient_substances
                WHERE valid_from IS NOT NULL AND valid_to IS NOT NULL
                  AND valid_to < valid_from
            ) THEN
                RAISE EXCEPTION 'Cannot migrate 0012: an ingredient-substance validity interval is inverted';
            END IF;
            IF EXISTS (
                SELECT 1 FROM ingredient_substances
                WHERE mapping_method = 'manual_review'
                  AND mapping_status IN ('accepted', 'rejected', 'ambiguous')
                  AND reviewed_at IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot migrate 0012: a terminal manual relationship lacks review metadata';
            END IF;
            IF EXISTS (
                SELECT 1 FROM ingredient_substances
                WHERE mapping_method = 'dataset'
                  AND source_dataset_release_id IS NULL
                  AND ingestion_run_id IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot migrate 0012: a dataset relationship lacks structured provenance';
            END IF;
            IF EXISTS (
                SELECT 1 FROM ingredient_substances
                WHERE mapping_method = 'deterministic'
                  AND mapping_status = 'accepted'
                  AND provenance IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot migrate 0012: an accepted deterministic relationship lacks provenance';
            END IF;
        END $$
        """
    )

    op.execute(
        "ALTER TABLE ingredient_substances ADD CONSTRAINT "
        "fk_ingredient_substances_ingestion_run FOREIGN KEY (ingestion_run_id) "
        "REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT"
    )
    op.execute(
        "ALTER TABLE ingredient_substances ADD CONSTRAINT "
        "ck_ingredient_substances_valid_interval CHECK ("
        "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)"
    )
    op.execute(
        """
        ALTER TABLE ingredient_substances ADD CONSTRAINT
        ck_ingredient_substances_review_metadata CHECK (
            (
                mapping_method <> 'manual_review'
                OR mapping_status NOT IN ('accepted', 'rejected', 'ambiguous')
                OR reviewed_at IS NOT NULL
            )
            AND (
                reviewed_by IS NULL
                OR (btrim(reviewed_by) <> '' AND reviewed_at IS NOT NULL)
            )
        )
        """
    )
    op.execute(
        "ALTER TABLE ingredient_substances ADD CONSTRAINT "
        "ck_ingredient_substances_dataset_provenance CHECK ("
        "mapping_method <> 'dataset' "
        "OR source_dataset_release_id IS NOT NULL "
        "OR ingestion_run_id IS NOT NULL)"
    )
    op.execute(
        "ALTER TABLE ingredient_substances ADD CONSTRAINT "
        "ck_ingredient_substances_deterministic_provenance CHECK ("
        "mapping_method <> 'deterministic' "
        "OR mapping_status <> 'accepted' "
        "OR provenance IS NOT NULL)"
    )

    op.execute(
        "CREATE INDEX idx_ingredient_substances_ingredient_status "
        "ON ingredient_substances (ingredient_id, mapping_status)"
    )
    op.execute(
        "CREATE INDEX idx_ingredient_substances_substance_status "
        "ON ingredient_substances (substance_id, mapping_status)"
    )
    op.execute(
        "CREATE INDEX idx_ingredient_substances_ingestion_run "
        "ON ingredient_substances (ingestion_run_id) "
        "WHERE ingestion_run_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM ingredient_substances
                WHERE reviewed_by IS NOT NULL
                   OR reviewed_at IS NOT NULL
                   OR ingestion_run_id IS NOT NULL
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0012: review or ingestion provenance is not representable by 0011';
            END IF;
        END $$
        """
    )
    op.execute("DROP INDEX idx_ingredient_substances_ingestion_run")
    op.execute("DROP INDEX idx_ingredient_substances_substance_status")
    op.execute("DROP INDEX idx_ingredient_substances_ingredient_status")
    op.execute(
        "ALTER TABLE ingredient_substances DROP CONSTRAINT "
        "ck_ingredient_substances_deterministic_provenance"
    )
    op.execute(
        "ALTER TABLE ingredient_substances DROP CONSTRAINT "
        "ck_ingredient_substances_dataset_provenance"
    )
    op.execute(
        "ALTER TABLE ingredient_substances DROP CONSTRAINT "
        "ck_ingredient_substances_review_metadata"
    )
    op.execute(
        "ALTER TABLE ingredient_substances DROP CONSTRAINT "
        "ck_ingredient_substances_valid_interval"
    )
    op.execute(
        "ALTER TABLE ingredient_substances DROP CONSTRAINT "
        "fk_ingredient_substances_ingestion_run"
    )
    op.execute("ALTER TABLE ingredient_substances DROP COLUMN ingestion_run_id")
    op.execute("ALTER TABLE ingredient_substances DROP COLUMN reviewed_at")
    op.execute("ALTER TABLE ingredient_substances DROP COLUMN reviewed_by")
