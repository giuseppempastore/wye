"""Harden scientific release identity and raw artifact provenance.

Revision ID: 0008_release_artifact_integrity
Revises: 0007_source_identity_hardening
"""

from alembic import op


revision = "0008_release_artifact_integrity"
down_revision = "0007_source_identity_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE source_dataset_releases "
        "ADD COLUMN external_release_key VARCHAR(255)"
    )
    # Legacy labels, URLs, timestamps, and checksums do not establish a trusted
    # external identity. The existing id supplies a neutral deterministic key.
    op.execute(
        "UPDATE source_dataset_releases "
        "SET external_release_key = 'legacy_release_' || id::text "
        "WHERE external_release_key IS NULL"
    )
    op.execute(
        "ALTER TABLE source_dataset_releases "
        "ALTER COLUMN external_release_key SET NOT NULL"
    )
    op.execute(
        "ALTER TABLE source_dataset_releases "
        "ADD CONSTRAINT ck_source_dataset_releases_external_key_format "
        "CHECK (external_release_key ~ '^[a-z0-9][a-z0-9._:-]*$')"
    )
    op.execute(
        "ALTER TABLE source_dataset_releases "
        "ADD CONSTRAINT uq_source_dataset_releases_external_key "
        "UNIQUE (dataset_id, external_release_key)"
    )

    op.execute(
        """
        CREATE TABLE scientific_release_artifacts (
            id BIGSERIAL PRIMARY KEY,
            release_id BIGINT NOT NULL REFERENCES source_dataset_releases(id) ON DELETE RESTRICT,
            storage_object_id BIGINT NOT NULL REFERENCES storage_objects(id) ON DELETE RESTRICT,
            artifact_key VARCHAR(255) NOT NULL,
            artifact_role VARCHAR(30) NOT NULL,
            format VARCHAR(100),
            media_type VARCHAR(100),
            raw_checksum_algorithm VARCHAR(50) NOT NULL,
            raw_checksum_value VARCHAR(128) NOT NULL,
            byte_size BIGINT,
            acquired_at TIMESTAMPTZ NOT NULL,
            validated_at TIMESTAMPTZ,
            provenance JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_scientific_release_artifacts_key UNIQUE (release_id, artifact_key),
            CONSTRAINT ck_scientific_release_artifacts_key_format
                CHECK (artifact_key ~ '^[a-z][a-z0-9]*(_[a-z0-9]+)*$'),
            CONSTRAINT ck_scientific_release_artifacts_role
                CHECK (artifact_role IN ('primary', 'manifest', 'metadata',
                    'attachment', 'archive', 'other')),
            CONSTRAINT ck_scientific_release_artifacts_checksum_algorithm
                CHECK (raw_checksum_algorithm ~ '^[a-z0-9][a-z0-9_-]*$'),
            CONSTRAINT ck_scientific_release_artifacts_checksum_value
                CHECK (
                    btrim(raw_checksum_value) <> ''
                    AND (
                        raw_checksum_algorithm <> 'sha256'
                        OR raw_checksum_value ~ '^[0-9a-f]{64}$'
                    )
                ),
            CONSTRAINT ck_scientific_release_artifacts_byte_size
                CHECK (byte_size IS NULL OR byte_size >= 0),
            CONSTRAINT ck_scientific_release_artifacts_validation_time
                CHECK (validated_at IS NULL OR validated_at >= acquired_at)
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_scientific_release_artifacts_storage_object "
        "ON scientific_release_artifacts (storage_object_id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_release_artifacts_release_role "
        "ON scientific_release_artifacts (release_id, artifact_role)"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM scientific_release_artifacts) THEN
                RAISE EXCEPTION 'Cannot downgrade 0008: scientific_release_artifacts contains data.';
            END IF;
            IF EXISTS (
                SELECT 1 FROM source_dataset_releases
                WHERE external_release_key <> 'legacy_release_' || id::text
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0008: external_release_key contains non-legacy identities.';
            END IF;
        END $$
        """
    )
    op.execute("DROP TABLE scientific_release_artifacts")
    op.execute(
        "ALTER TABLE source_dataset_releases "
        "DROP CONSTRAINT uq_source_dataset_releases_external_key"
    )
    op.execute(
        "ALTER TABLE source_dataset_releases "
        "DROP CONSTRAINT ck_source_dataset_releases_external_key_format"
    )
    op.execute(
        "ALTER TABLE source_dataset_releases DROP COLUMN external_release_key"
    )
