"""Allow reviewed creation of identifier-backed canonical substances."""

from alembic import op


revision = "0016_substance_creation"
down_revision = "0015_registry_materialization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE constraint_name TEXT;
        BEGIN
          SELECT conname INTO constraint_name
          FROM pg_constraint
          WHERE conrelid='substances'::regclass
            AND contype='u'
            AND pg_get_constraintdef(oid)='UNIQUE (normalized_name)';
          IF constraint_name IS NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0016: normalized_name UNIQUE constraint not found';
          END IF;
          EXECUTE format('ALTER TABLE substances DROP CONSTRAINT %I',constraint_name);
        END $$
        """
    )
    op.execute("CREATE INDEX idx_substances_normalized_name ON substances(normalized_name)")

    op.execute("ALTER TABLE substance_resolution_candidates DROP CONSTRAINT ck_substance_resolution_candidates_status")
    op.execute(
        "ALTER TABLE substance_resolution_candidates ADD CONSTRAINT "
        "ck_substance_resolution_candidates_status CHECK "
        "(candidate_status IN ('pending_review','resolved_existing','resolved_new','rejected'))"
    )

    op.execute("ALTER TABLE substance_resolution_decisions ADD COLUMN proposed_preferred_name VARCHAR(255)")
    op.execute("ALTER TABLE substance_resolution_decisions ADD COLUMN proposed_normalized_name VARCHAR(255)")
    op.execute("ALTER TABLE substance_resolution_decisions ADD COLUMN proposed_substance_type VARCHAR(50)")
    op.execute("DROP INDEX uq_substance_resolution_terminal_decision")
    op.execute("ALTER TABLE substance_resolution_decisions DROP CONSTRAINT ck_substance_resolution_decisions_type")
    op.execute("ALTER TABLE substance_resolution_decisions DROP CONSTRAINT ck_substance_resolution_decisions_target")
    op.execute(
        "ALTER TABLE substance_resolution_decisions ADD CONSTRAINT "
        "ck_substance_resolution_decisions_type CHECK "
        "(decision_type IN ('associate_existing','create_new_substance','reject','defer'))"
    )
    op.execute(
        "ALTER TABLE substance_resolution_decisions ADD CONSTRAINT "
        "ck_substance_resolution_decisions_target CHECK "
        "((decision_type='associate_existing')=(target_substance_id IS NOT NULL))"
    )
    op.execute(
        """
        ALTER TABLE substance_resolution_decisions ADD CONSTRAINT
        ck_substance_resolution_decisions_creation_payload CHECK (
          (decision_type='create_new_substance'
           AND proposed_preferred_name IS NOT NULL AND btrim(proposed_preferred_name)<>''
           AND proposed_normalized_name IS NOT NULL AND btrim(proposed_normalized_name)<>''
           AND proposed_substance_type IN ('additive','chemical_substance','biological_substance',
             'contaminant','nutrient','mixture','unknown'))
          OR
          (decision_type<>'create_new_substance'
           AND proposed_preferred_name IS NULL
           AND proposed_normalized_name IS NULL
           AND proposed_substance_type IS NULL)
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_substance_resolution_terminal_decision "
        "ON substance_resolution_decisions(candidate_id) "
        "WHERE decision_type IN ('associate_existing','create_new_substance','reject')"
    )

    op.execute("ALTER TABLE substance_registry_materializations DROP CONSTRAINT ck_substance_registry_materializations_type")
    op.execute(
        "ALTER TABLE substance_registry_materializations ADD CONSTRAINT "
        "ck_substance_registry_materializations_type CHECK "
        "(mutation_type IN ('associate_existing_identifier','create_new_substance'))"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM substances GROUP BY normalized_name HAVING count(*)>1)
             OR EXISTS (SELECT 1 FROM substance_resolution_decisions WHERE decision_type='create_new_substance')
             OR EXISTS (SELECT 1 FROM substance_resolution_candidates WHERE candidate_status='resolved_new')
             OR EXISTS (SELECT 1 FROM substance_registry_materializations WHERE mutation_type='create_new_substance') THEN
            RAISE EXCEPTION 'Cannot downgrade 0016: substance creation data is not representable by 0015.';
          END IF;
        END $$
        """
    )
    op.execute("ALTER TABLE substance_registry_materializations DROP CONSTRAINT ck_substance_registry_materializations_type")
    op.execute(
        "ALTER TABLE substance_registry_materializations ADD CONSTRAINT "
        "ck_substance_registry_materializations_type CHECK "
        "(mutation_type='associate_existing_identifier')"
    )
    op.execute("DROP INDEX uq_substance_resolution_terminal_decision")
    op.execute("ALTER TABLE substance_resolution_decisions DROP CONSTRAINT ck_substance_resolution_decisions_creation_payload")
    op.execute("ALTER TABLE substance_resolution_decisions DROP CONSTRAINT ck_substance_resolution_decisions_target")
    op.execute("ALTER TABLE substance_resolution_decisions DROP CONSTRAINT ck_substance_resolution_decisions_type")
    op.execute(
        "ALTER TABLE substance_resolution_decisions ADD CONSTRAINT "
        "ck_substance_resolution_decisions_type CHECK "
        "(decision_type IN ('associate_existing','reject','defer'))"
    )
    op.execute(
        "ALTER TABLE substance_resolution_decisions ADD CONSTRAINT "
        "ck_substance_resolution_decisions_target CHECK "
        "((decision_type='associate_existing')=(target_substance_id IS NOT NULL))"
    )
    op.execute("ALTER TABLE substance_resolution_decisions DROP COLUMN proposed_substance_type")
    op.execute("ALTER TABLE substance_resolution_decisions DROP COLUMN proposed_normalized_name")
    op.execute("ALTER TABLE substance_resolution_decisions DROP COLUMN proposed_preferred_name")
    op.execute(
        "CREATE UNIQUE INDEX uq_substance_resolution_terminal_decision "
        "ON substance_resolution_decisions(candidate_id) "
        "WHERE decision_type IN ('associate_existing','reject')"
    )
    op.execute("ALTER TABLE substance_resolution_candidates DROP CONSTRAINT ck_substance_resolution_candidates_status")
    op.execute(
        "ALTER TABLE substance_resolution_candidates ADD CONSTRAINT "
        "ck_substance_resolution_candidates_status CHECK "
        "(candidate_status IN ('pending_review','resolved_existing','rejected'))"
    )
    op.execute("DROP INDEX idx_substances_normalized_name")
    op.execute(
        "ALTER TABLE substances ADD CONSTRAINT substances_normalized_name_key UNIQUE(normalized_name)"
    )
