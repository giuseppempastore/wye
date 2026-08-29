"""Add versioned substance identifier namespaces and integrity constraints.

Revision ID: 0011_substance_identity_registry
Revises: 0010_assessment_finding_identity
"""

from alembic import op


revision = "0011_substance_identity_registry"
down_revision = "0010_assessment_finding_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM substance_identifiers
                WHERE is_primary = TRUE AND verification_status <> 'verified'
            ) THEN
                RAISE EXCEPTION 'Cannot migrate 0011: a non-verified identifier is marked primary';
            END IF;
            IF EXISTS (
                SELECT substance_id, identifier_system
                FROM substance_identifiers
                WHERE is_primary = TRUE AND verification_status = 'verified'
                GROUP BY substance_id, identifier_system
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot migrate 0011: multiple verified primary identifiers exist in one legacy system';
            END IF;
        END $$
        """
    )
    op.execute(
        """
        CREATE TABLE substance_identifier_namespaces (
            id BIGSERIAL PRIMARY KEY,
            namespace_key VARCHAR(100) NOT NULL,
            namespace_version VARCHAR(50) NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            owner_source_id BIGINT REFERENCES sources(id) ON DELETE RESTRICT,
            normalization_rule_version VARCHAR(100) NOT NULL,
            description TEXT,
            provenance JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_substance_identifier_namespaces_key_version
                UNIQUE (namespace_key, namespace_version),
            CONSTRAINT ck_substance_identifier_namespaces_key CHECK (
                namespace_key ~ '^[a-z][a-z0-9]*(_[a-z0-9]+)*$'
            ),
            CONSTRAINT ck_substance_identifier_namespaces_required_text CHECK (
                btrim(namespace_version) <> ''
                AND btrim(display_name) <> ''
                AND btrim(normalization_rule_version) <> ''
            )
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_substance_identifier_namespaces_owner_source "
        "ON substance_identifier_namespaces (owner_source_id) "
        "WHERE owner_source_id IS NOT NULL"
    )
    op.execute(
        """
        INSERT INTO substance_identifier_namespaces (
            namespace_key, namespace_version, display_name,
            normalization_rule_version, provenance
        )
        SELECT
            'legacy_system_' || encode(sha256(convert_to(identifier_system, 'UTF8')), 'hex'),
            'legacy_1',
            identifier_system,
            'legacy_unknown',
            jsonb_build_object(
                'synthetic_legacy_namespace', true,
                'legacy_identifier_system', identifier_system,
                'migration', '0011_substance_identity_hardening'
            )
        FROM substance_identifiers
        GROUP BY identifier_system
        """
    )

    op.execute("ALTER TABLE substance_identifiers ADD COLUMN namespace_id BIGINT")
    op.execute("ALTER TABLE substance_identifiers ADD COLUMN ingestion_run_id BIGINT")
    op.execute(
        """
        UPDATE substance_identifiers i
        SET namespace_id = n.id
        FROM substance_identifier_namespaces n
        WHERE n.namespace_key = 'legacy_system_' ||
            encode(sha256(convert_to(i.identifier_system, 'UTF8')), 'hex')
          AND n.namespace_version = 'legacy_1'
          AND n.provenance ->> 'legacy_identifier_system' = i.identifier_system
        """
    )
    op.execute("ALTER TABLE substance_identifiers ALTER COLUMN namespace_id SET NOT NULL")
    op.execute(
        "ALTER TABLE substance_identifiers ADD CONSTRAINT "
        "fk_substance_identifiers_namespace FOREIGN KEY (namespace_id) "
        "REFERENCES substance_identifier_namespaces(id) ON DELETE RESTRICT"
    )
    op.execute(
        "ALTER TABLE substance_identifiers ADD CONSTRAINT "
        "fk_substance_identifiers_ingestion_run FOREIGN KEY (ingestion_run_id) "
        "REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT"
    )
    op.execute(
        "ALTER TABLE substance_identifiers ADD CONSTRAINT "
        "ck_substance_identifiers_primary_verified CHECK ("
        "is_primary = FALSE OR verification_status = 'verified')"
    )
    op.execute(
        """
        DO $$
        DECLARE constraint_name TEXT;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'substance_identifiers'::regclass
              AND contype = 'u'
              AND pg_get_constraintdef(oid) =
                  'UNIQUE (identifier_system, normalized_value)';
            IF constraint_name IS NULL THEN
                RAISE EXCEPTION 'Legacy substance identifier identity constraint not found';
            END IF;
            EXECUTE format('ALTER TABLE substance_identifiers DROP CONSTRAINT %I', constraint_name);
        END $$
        """
    )
    op.execute(
        "ALTER TABLE substance_identifiers ADD CONSTRAINT "
        "uq_substance_identifiers_namespace_value "
        "UNIQUE (namespace_id, normalized_value)"
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_substance_identifiers_primary_verified
        ON substance_identifiers (substance_id, namespace_id)
        WHERE is_primary = TRUE AND verification_status = 'verified'
        """
    )
    op.execute(
        "CREATE INDEX idx_substance_identifiers_namespace "
        "ON substance_identifiers (namespace_id)"
    )
    op.execute(
        "CREATE INDEX idx_substance_identifiers_ingestion_run "
        "ON substance_identifiers (ingestion_run_id) "
        "WHERE ingestion_run_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM substance_identifier_namespaces n
                WHERE n.namespace_version <> 'legacy_1'
                   OR n.normalization_rule_version <> 'legacy_unknown'
                   OR n.owner_source_id IS NOT NULL
                   OR NOT (n.provenance @> '{"synthetic_legacy_namespace": true}'::jsonb)
                   OR n.namespace_key <> 'legacy_system_' || encode(
                       sha256(convert_to(n.provenance ->> 'legacy_identifier_system', 'UTF8')), 'hex')
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0011: namespace semantics are not representable by identifier_system';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM substance_identifiers i
                JOIN substance_identifier_namespaces n ON n.id = i.namespace_id
                WHERE i.ingestion_run_id IS NOT NULL
                   OR n.provenance ->> 'legacy_identifier_system' IS DISTINCT FROM i.identifier_system
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0011: identifier namespace or ingestion provenance is not representable by 0010';
            END IF;
            IF EXISTS (
                SELECT identifier_system, normalized_value
                FROM substance_identifiers
                GROUP BY identifier_system, normalized_value
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade 0011: identifiers violate the legacy identity constraint';
            END IF;
        END $$
        """
    )
    op.execute("DROP INDEX idx_substance_identifiers_ingestion_run")
    op.execute("DROP INDEX idx_substance_identifiers_namespace")
    op.execute("DROP INDEX uq_substance_identifiers_primary_verified")
    op.execute("ALTER TABLE substance_identifiers DROP CONSTRAINT uq_substance_identifiers_namespace_value")
    op.execute(
        "ALTER TABLE substance_identifiers ADD CONSTRAINT "
        "substance_identifiers_system_normalized_value_key "
        "UNIQUE (identifier_system, normalized_value)"
    )
    op.execute("ALTER TABLE substance_identifiers DROP CONSTRAINT ck_substance_identifiers_primary_verified")
    op.execute("ALTER TABLE substance_identifiers DROP CONSTRAINT fk_substance_identifiers_ingestion_run")
    op.execute("ALTER TABLE substance_identifiers DROP CONSTRAINT fk_substance_identifiers_namespace")
    op.execute("ALTER TABLE substance_identifiers DROP COLUMN ingestion_run_id")
    op.execute("ALTER TABLE substance_identifiers DROP COLUMN namespace_id")
    op.execute("DROP INDEX idx_substance_identifier_namespaces_owner_source")
    op.execute("DROP TABLE substance_identifier_namespaces")
