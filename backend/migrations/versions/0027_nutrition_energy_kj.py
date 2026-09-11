"""Persist declared nutrition energy in kJ separately from kcal.

Revision ID: 0027_nutrition_energy_kj
Revises: 0026_ai_quota_beta_feedback
"""
from alembic import op


revision = "0027_nutrition_energy_kj"
down_revision = "0026_ai_quota_beta_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE nutrition_facts
          ADD COLUMN IF NOT EXISTS energy_kj NUMERIC(10,2)
          CHECK (energy_kj IS NULL OR (energy_kj >= 0 AND energy_kj <= 4000));
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE nutrition_facts DROP COLUMN IF EXISTS energy_kj;")
