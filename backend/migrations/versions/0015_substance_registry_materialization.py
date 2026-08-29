"""Audit reviewed substance identifier materializations into the registry."""

from alembic import op


revision = "0015_registry_materialization"
down_revision = "0014_substance_resolution_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE substance_registry_materializations (
            id BIGSERIAL PRIMARY KEY,
            decision_id BIGINT NOT NULL REFERENCES substance_resolution_decisions(id) ON DELETE RESTRICT,
            candidate_id BIGINT NOT NULL REFERENCES substance_resolution_candidates(id) ON DELETE RESTRICT,
            target_substance_id BIGINT NOT NULL REFERENCES substances(id) ON DELETE RESTRICT,
            namespace_id BIGINT NOT NULL REFERENCES substance_identifier_namespaces(id) ON DELETE RESTRICT,
            normalized_value VARCHAR(255) NOT NULL,
            substance_identifier_id BIGINT NOT NULL REFERENCES substance_identifiers(id) ON DELETE RESTRICT,
            mutation_type VARCHAR(40) NOT NULL,
            materialization_status VARCHAR(30) NOT NULL,
            materialized_by VARCHAR(255) NOT NULL,
            materialized_at TIMESTAMPTZ NOT NULL,
            provenance JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_substance_registry_materializations_decision UNIQUE (decision_id),
            CONSTRAINT ck_substance_registry_materializations_type CHECK (
                mutation_type = 'associate_existing_identifier'
            ),
            CONSTRAINT ck_substance_registry_materializations_status CHECK (
                materialization_status IN ('applied', 'already_present')
            ),
            CONSTRAINT ck_substance_registry_materializations_required CHECK (
                btrim(normalized_value) <> '' AND btrim(materialized_by) <> ''
            )
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_substance_registry_materializations_identifier "
        "ON substance_registry_materializations(substance_identifier_id)"
    )
    op.execute(
        "CREATE INDEX idx_substance_registry_materializations_candidate "
        "ON substance_registry_materializations(candidate_id, created_at, id)"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM substance_registry_materializations) THEN
            RAISE EXCEPTION 'Cannot downgrade 0015: registry materialization audit contains non-representable data.';
          END IF;
        END $$
        """
    )
    op.execute("DROP TABLE substance_registry_materializations")
