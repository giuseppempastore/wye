"""Add a stable machine-readable identity to scientific sources.

Revision ID: 0007_source_identity_hardening
Revises: 0006_mapping_integrity_hardening
"""

from alembic import op

revision = "0007_source_identity_hardening"
down_revision = "0006_mapping_integrity_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE sources ADD COLUMN source_key VARCHAR(100)")
    # Existing rows have no trustworthy machine identity. Their database id is
    # unique and immutable, so it gives a deterministic, collision-safe legacy
    # key without inferring semantics from the mutable name or URL.
    op.execute(
        "UPDATE sources SET source_key = 'legacy_source_' || id::text "
        "WHERE source_key IS NULL"
    )
    op.execute("ALTER TABLE sources ALTER COLUMN source_key SET NOT NULL")
    op.execute(
        "ALTER TABLE sources ADD CONSTRAINT ck_sources_source_key_format "
        "CHECK (source_key ~ '^[a-z][a-z0-9]*(_[a-z0-9]+)*$')"
    )
    op.execute(
        "ALTER TABLE sources ADD CONSTRAINT uq_sources_source_key UNIQUE (source_key)"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM sources
                WHERE source_key <> 'legacy_source_' || id::text
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0007: source_key contains non-legacy identities.';
            END IF;
        END $$
        """
    )
    op.execute("ALTER TABLE sources DROP CONSTRAINT uq_sources_source_key")
    op.execute("ALTER TABLE sources DROP CONSTRAINT ck_sources_source_key_format")
    op.execute("ALTER TABLE sources DROP COLUMN source_key")
