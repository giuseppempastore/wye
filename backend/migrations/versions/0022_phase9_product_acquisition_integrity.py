"""Preserve unknown user ingredient candidates without invented confidence.

Revision ID: 0022_phase9_product_acquisition_integrity
Revises: 0021_scientific_evaluation_publication
"""
from alembic import op


revision = "0022_phase9_product_acquisition_integrity"
down_revision = "0021_scientific_evaluation_publication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE product_ingredients ALTER COLUMN confidence DROP NOT NULL")
    op.execute(
        "ALTER TABLE ingredient_mapping_reviews "
        "DROP CONSTRAINT ingredient_mapping_reviews_product_ingredient_id_fkey"
    )
    op.execute(
        "ALTER TABLE ingredient_mapping_reviews ADD CONSTRAINT "
        "ingredient_mapping_reviews_product_ingredient_id_fkey "
        "FOREIGN KEY (product_ingredient_id) REFERENCES product_ingredients(id) "
        "ON DELETE CASCADE"
    )
    op.execute("ALTER TABLE label_extraction_runs ADD COLUMN provider_invoked BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute("ALTER TABLE label_extraction_runs ALTER COLUMN provider_invoked SET DEFAULT FALSE")
    op.execute("ALTER TABLE label_extraction_runs ADD COLUMN cache_source_run_id BIGINT REFERENCES label_extraction_runs(id) ON DELETE RESTRICT")
    op.execute("CREATE INDEX idx_label_extraction_runs_fingerprint_success ON label_extraction_runs(request_fingerprint, id) WHERE run_status='succeeded'")


def downgrade() -> None:
    op.execute("DROP INDEX idx_label_extraction_runs_fingerprint_success")
    op.execute("ALTER TABLE label_extraction_runs DROP COLUMN cache_source_run_id")
    op.execute("ALTER TABLE label_extraction_runs DROP COLUMN provider_invoked")
    op.execute(
        "ALTER TABLE ingredient_mapping_reviews "
        "DROP CONSTRAINT ingredient_mapping_reviews_product_ingredient_id_fkey"
    )
    op.execute(
        "ALTER TABLE ingredient_mapping_reviews ADD CONSTRAINT "
        "ingredient_mapping_reviews_product_ingredient_id_fkey "
        "FOREIGN KEY (product_ingredient_id) REFERENCES product_ingredients(id) "
        "ON DELETE SET NULL"
    )
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM product_ingredients WHERE confidence IS NULL) THEN
            RAISE EXCEPTION 'Cannot downgrade while product ingredients have unknown confidence';
          END IF;
        END $$
        """
    )
    op.execute("ALTER TABLE product_ingredients ALTER COLUMN confidence SET NOT NULL")
