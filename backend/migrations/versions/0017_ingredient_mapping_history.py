"""Add controlled ingredient-substance proposal and relationship history."""

from alembic import op


revision = "0017_ingredient_mapping_history"
down_revision = "0016_substance_creation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ DECLARE constraint_name TEXT;
        BEGIN
          SELECT conname INTO constraint_name FROM pg_constraint
          WHERE conrelid='ingredient_substances'::regclass AND contype='u'
            AND pg_get_constraintdef(oid)=
              'UNIQUE (ingredient_id, substance_id, relationship_type)';
          IF constraint_name IS NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0017: legacy ingredient-substance UNIQUE not found';
          END IF;
          EXECUTE format('ALTER TABLE ingredient_substances DROP CONSTRAINT %I',constraint_name);
        END $$
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_ingredient_substances_current_accepted "
        "ON ingredient_substances(ingredient_id,substance_id,relationship_type) "
        "WHERE mapping_status='accepted' AND valid_to IS NULL"
    )
    op.execute(
        "CREATE INDEX idx_ingredient_substances_history "
        "ON ingredient_substances(ingredient_id,created_at,id)"
    )
    op.execute(
        "CREATE INDEX idx_ingredient_substances_current_temporal "
        "ON ingredient_substances(ingredient_id,mapping_status,valid_from,valid_to)"
    )

    op.execute(
        """
        CREATE TABLE ingredient_substance_mapping_proposals (
          id BIGSERIAL PRIMARY KEY,
          proposal_key UUID NOT NULL UNIQUE,
          ingredient_id BIGINT NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
          substance_id BIGINT NOT NULL REFERENCES substances(id) ON DELETE RESTRICT,
          relationship_type VARCHAR(40) NOT NULL,
          mapping_method VARCHAR(30) NOT NULL,
          mapping_confidence NUMERIC(4,3),
          source_dataset_release_id BIGINT REFERENCES source_dataset_releases(id) ON DELETE RESTRICT,
          ingestion_run_id BIGINT REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT,
          proposed_by VARCHAR(255) NOT NULL,
          proposal_status VARCHAR(30) NOT NULL DEFAULT 'pending_review',
          provenance JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_ingredient_substance_proposals_relationship CHECK (
            relationship_type IN ('represents','contains','derived_from','mixture_component','equivalent_to')),
          CONSTRAINT ck_ingredient_substance_proposals_method CHECK (
            mapping_method IN ('manual_review','dataset','deterministic')),
          CONSTRAINT ck_ingredient_substance_proposals_confidence CHECK (
            mapping_confidence IS NULL OR mapping_confidence BETWEEN 0 AND 1),
          CONSTRAINT ck_ingredient_substance_proposals_status CHECK (
            proposal_status IN ('pending_review','accepted','rejected')),
          CONSTRAINT ck_ingredient_substance_proposals_required CHECK (btrim(proposed_by)<>''),
          CONSTRAINT ck_ingredient_substance_proposals_dataset CHECK (
            mapping_method<>'dataset' OR source_dataset_release_id IS NOT NULL OR ingestion_run_id IS NOT NULL),
          CONSTRAINT ck_ingredient_substance_proposals_deterministic CHECK (
            mapping_method<>'deterministic' OR provenance IS NOT NULL)
        )
        """
    )
    op.execute("CREATE INDEX idx_ingredient_substance_proposals_pending ON ingredient_substance_mapping_proposals(created_at,id) WHERE proposal_status='pending_review'")
    op.execute("CREATE INDEX idx_ingredient_substance_proposals_semantic ON ingredient_substance_mapping_proposals(ingredient_id,substance_id,relationship_type,created_at,id)")
    op.execute("CREATE INDEX idx_ingredient_substance_proposals_run ON ingredient_substance_mapping_proposals(ingestion_run_id) WHERE ingestion_run_id IS NOT NULL")

    op.execute(
        """
        CREATE TABLE ingredient_substance_mapping_decisions (
          id BIGSERIAL PRIMARY KEY,
          proposal_id BIGINT NOT NULL REFERENCES ingredient_substance_mapping_proposals(id) ON DELETE RESTRICT,
          decision_type VARCHAR(20) NOT NULL,
          effective_from DATE,
          reviewed_by VARCHAR(255) NOT NULL,
          reviewed_at TIMESTAMPTZ NOT NULL,
          reason_code VARCHAR(100) NOT NULL,
          notes TEXT,
          provenance JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_ingredient_substance_decisions_type CHECK (decision_type IN ('accept','reject','defer')),
          CONSTRAINT ck_ingredient_substance_decisions_effective CHECK (
            (decision_type='accept')=(effective_from IS NOT NULL)),
          CONSTRAINT ck_ingredient_substance_decisions_required CHECK (
            btrim(reviewed_by)<>'' AND btrim(reason_code)<>'')
        )
        """
    )
    op.execute("CREATE INDEX idx_ingredient_substance_decisions_history ON ingredient_substance_mapping_decisions(proposal_id,created_at,id)")
    op.execute("CREATE UNIQUE INDEX uq_ingredient_substance_terminal_decision ON ingredient_substance_mapping_decisions(proposal_id) WHERE decision_type IN ('accept','reject')")

    op.execute(
        """
        CREATE TABLE ingredient_substance_mapping_materializations (
          id BIGSERIAL PRIMARY KEY,
          decision_id BIGINT NOT NULL UNIQUE REFERENCES ingredient_substance_mapping_decisions(id) ON DELETE RESTRICT,
          proposal_id BIGINT NOT NULL REFERENCES ingredient_substance_mapping_proposals(id) ON DELETE RESTRICT,
          ingredient_substance_id BIGINT NOT NULL REFERENCES ingredient_substances(id) ON DELETE RESTRICT,
          materialization_status VARCHAR(30) NOT NULL,
          materialized_by VARCHAR(255) NOT NULL,
          materialized_at TIMESTAMPTZ NOT NULL,
          provenance JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_ingredient_substance_materializations_status CHECK (
            materialization_status IN ('applied','already_current')),
          CONSTRAINT ck_ingredient_substance_materializations_required CHECK (btrim(materialized_by)<>'')
        )
        """
    )
    op.execute("CREATE INDEX idx_ingredient_substance_materializations_mapping ON ingredient_substance_mapping_materializations(ingredient_substance_id)")

    op.execute(
        """
        CREATE TABLE ingredient_substance_mapping_closures (
          id BIGSERIAL PRIMARY KEY,
          ingredient_substance_id BIGINT NOT NULL UNIQUE REFERENCES ingredient_substances(id) ON DELETE RESTRICT,
          valid_to DATE NOT NULL,
          closed_by VARCHAR(255) NOT NULL,
          closed_at TIMESTAMPTZ NOT NULL,
          reason_code VARCHAR(100) NOT NULL,
          provenance JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_ingredient_substance_closures_required CHECK (
            btrim(closed_by)<>'' AND btrim(reason_code)<>'')
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS(SELECT 1 FROM ingredient_substance_mapping_proposals)
             OR EXISTS(SELECT 1 FROM ingredient_substance_mapping_decisions)
             OR EXISTS(SELECT 1 FROM ingredient_substance_mapping_materializations)
             OR EXISTS(SELECT 1 FROM ingredient_substance_mapping_closures)
             OR EXISTS(
               SELECT ingredient_id,substance_id,relationship_type
               FROM ingredient_substances
               GROUP BY ingredient_id,substance_id,relationship_type HAVING count(*)>1
             ) THEN
            RAISE EXCEPTION 'Cannot downgrade 0017: mapping history is not representable by 0016.';
          END IF;
        END $$
        """
    )
    op.execute("DROP TABLE ingredient_substance_mapping_closures")
    op.execute("DROP TABLE ingredient_substance_mapping_materializations")
    op.execute("DROP TABLE ingredient_substance_mapping_decisions")
    op.execute("DROP TABLE ingredient_substance_mapping_proposals")
    op.execute("DROP INDEX idx_ingredient_substances_current_temporal")
    op.execute("DROP INDEX idx_ingredient_substances_history")
    op.execute("DROP INDEX uq_ingredient_substances_current_accepted")
    op.execute(
        "ALTER TABLE ingredient_substances ADD CONSTRAINT "
        "ingredient_substances_ingredient_id_substance_id_relationship_type_key "
        "UNIQUE(ingredient_id,substance_id,relationship_type)"
    )
