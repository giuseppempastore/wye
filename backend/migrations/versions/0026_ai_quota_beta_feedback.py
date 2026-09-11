"""Add external AI usage accounting and sanitized beta feedback.

Revision ID: 0026_ai_quota_beta_feedback
Revises: 0025_product_acquisition_jobs
"""
from alembic import op


revision = "0026_ai_quota_beta_feedback"
down_revision = "0025_product_acquisition_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ai_usage_events (
          id BIGSERIAL PRIMARY KEY,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          local_day DATE NOT NULL,
          actor_hash CHAR(64) NOT NULL CHECK (actor_hash ~ '^[0-9a-f]{64}$'),
          plan VARCHAR(30) NOT NULL CHECK (
            plan IN ('base','premium_light','premium_pro','internal')
          ),
          operation VARCHAR(80) NOT NULL CHECK (operation ~ '^[a-z0-9_.-]+$'),
          provider VARCHAR(80) NOT NULL CHECK (provider ~ '^[a-z0-9_.-]+$'),
          model VARCHAR(120),
          cost_units INTEGER NOT NULL DEFAULT 1 CHECK (cost_units BETWEEN 0 AND 1000),
          cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
          status VARCHAR(30) NOT NULL CHECK (
            status IN ('consumed','not_billable','quota_rejected','failed')
          ),
          sanitized_error_code VARCHAR(100)
        );
        CREATE INDEX idx_ai_usage_actor_day
          ON ai_usage_events(actor_hash,local_day,status);

        CREATE TABLE beta_feedback (
          id BIGSERIAL PRIMARY KEY,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          feedback_type VARCHAR(40) NOT NULL CHECK (feedback_type IN (
            'bug','ux_ui','ocr','barcode','result_score','performance',
            'suggestion','other'
          )),
          severity VARCHAR(20) NOT NULL CHECK (
            severity IN ('low','medium','high','blocking')
          ),
          message TEXT NOT NULL CHECK (char_length(message) BETWEEN 5 AND 4000),
          expected_behavior TEXT CHECK (
            expected_behavior IS NULL OR char_length(expected_behavior) <= 2000
          ),
          actual_behavior TEXT CHECK (
            actual_behavior IS NULL OR char_length(actual_behavior) <= 2000
          ),
          app_version VARCHAR(80),
          platform VARCHAR(40),
          device_class VARCHAR(80),
          route VARCHAR(120),
          sanitized_context_json JSONB,
          status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (
            status IN ('new','triaged','in_progress','resolved','closed')
          )
        );
        CREATE INDEX idx_beta_feedback_status_created
          ON beta_feedback(status,created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE beta_feedback;
        DROP TABLE ai_usage_events;
        """
    )
