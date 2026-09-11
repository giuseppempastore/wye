"""Add distinct declared salt storage for photo-first nutrition capture.

Revision ID: 0023_phase9_photo_first_acquisition
Revises: 0022_phase9_product_acquisition_integrity
"""
from alembic import op


revision = "0023_phase9_photo_first_acquisition"
down_revision = "0022_phase9_product_acquisition_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE nutrition_facts ADD COLUMN salt_g NUMERIC(10,2) "
        "CHECK (salt_g IS NULL OR (salt_g >= 0 AND salt_g <= 100))"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM nutrition_facts WHERE salt_g IS NOT NULL) THEN
            RAISE EXCEPTION 'Cannot downgrade while declared salt values exist';
          END IF;
        END $$
        """
    )
    op.execute("ALTER TABLE nutrition_facts DROP COLUMN salt_g")
