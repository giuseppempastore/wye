"""Add pending substance identity candidates and append-only review decisions."""

from alembic import op

revision = "0014_substance_resolution_review"
down_revision = "0013_ingestion_run_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE substance_resolution_candidates (
            id BIGSERIAL PRIMARY KEY,
            candidate_key VARCHAR(64) NOT NULL UNIQUE,
            candidate_kind VARCHAR(30) NOT NULL,
            namespace_id BIGINT REFERENCES substance_identifier_namespaces(id) ON DELETE RESTRICT,
            namespace_key VARCHAR(100),
            namespace_version VARCHAR(50),
            normalized_value TEXT,
            candidate_name TEXT,
            candidate_status VARCHAR(30) NOT NULL DEFAULT 'pending_review',
            first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_substance_resolution_candidates_key CHECK (candidate_key ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_substance_resolution_candidates_kind CHECK (candidate_kind IN ('unknown_identifier','identity_conflict','inactive_target')),
            CONSTRAINT ck_substance_resolution_candidates_status CHECK (candidate_status IN ('pending_review','resolved_existing','rejected')),
            CONSTRAINT ck_substance_resolution_candidates_identity CHECK (
              candidate_kind='identity_conflict' OR
              (namespace_key IS NOT NULL AND btrim(namespace_key)<>'' AND namespace_version IS NOT NULL AND btrim(namespace_version)<>'' AND normalized_value IS NOT NULL AND btrim(normalized_value)<>'')
            ),
            CONSTRAINT ck_substance_resolution_candidates_seen CHECK (last_seen_at >= first_seen_at)
        )
    """)
    op.execute("CREATE INDEX idx_substance_resolution_candidates_pending ON substance_resolution_candidates(first_seen_at,id) WHERE candidate_status='pending_review'")
    op.execute("CREATE INDEX idx_substance_resolution_candidates_namespace ON substance_resolution_candidates(namespace_id,normalized_value) WHERE namespace_id IS NOT NULL")
    op.execute("""
        CREATE TABLE substance_resolution_candidate_occurrences (
            id BIGSERIAL PRIMARY KEY,
            candidate_id BIGINT NOT NULL REFERENCES substance_resolution_candidates(id) ON DELETE RESTRICT,
            ingestion_run_id BIGINT NOT NULL REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT,
            source_record_key VARCHAR(512) NOT NULL,
            resolution_outcome VARCHAR(30) NOT NULL,
            reason_code VARCHAR(100) NOT NULL,
            raw_identifiers JSONB NOT NULL,
            diagnostics JSONB,
            provenance JSONB,
            observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_substance_resolution_occurrence UNIQUE(candidate_id,ingestion_run_id,source_record_key),
            CONSTRAINT ck_substance_resolution_occurrence_outcome CHECK (resolution_outcome IN ('unresolved','ambiguous','rejected')),
            CONSTRAINT ck_substance_resolution_occurrence_required CHECK (btrim(source_record_key)<>'' AND btrim(reason_code)<>'')
        )
    """)
    op.execute("CREATE INDEX idx_substance_resolution_occurrences_run ON substance_resolution_candidate_occurrences(ingestion_run_id,source_record_key)")
    op.execute("""
        CREATE TABLE substance_resolution_decisions (
            id BIGSERIAL PRIMARY KEY,
            candidate_id BIGINT NOT NULL REFERENCES substance_resolution_candidates(id) ON DELETE RESTRICT,
            decision_type VARCHAR(30) NOT NULL,
            target_substance_id BIGINT REFERENCES substances(id) ON DELETE RESTRICT,
            reviewed_by VARCHAR(255) NOT NULL,
            reviewed_at TIMESTAMPTZ NOT NULL,
            reason_code VARCHAR(100) NOT NULL,
            notes TEXT,
            provenance JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_substance_resolution_decisions_type CHECK (decision_type IN ('associate_existing','reject','defer')),
            CONSTRAINT ck_substance_resolution_decisions_target CHECK ((decision_type='associate_existing')=(target_substance_id IS NOT NULL)),
            CONSTRAINT ck_substance_resolution_decisions_required CHECK (btrim(reviewed_by)<>'' AND btrim(reason_code)<>'')
        )
    """)
    op.execute("CREATE INDEX idx_substance_resolution_decisions_candidate ON substance_resolution_decisions(candidate_id,created_at,id)")
    op.execute("CREATE UNIQUE INDEX uq_substance_resolution_terminal_decision ON substance_resolution_decisions(candidate_id) WHERE decision_type IN ('associate_existing','reject')")


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
          IF EXISTS(SELECT 1 FROM substance_resolution_candidates)
             OR EXISTS(SELECT 1 FROM substance_resolution_candidate_occurrences)
             OR EXISTS(SELECT 1 FROM substance_resolution_decisions) THEN
            RAISE EXCEPTION 'Cannot downgrade 0014: substance resolution review history contains non-representable data.';
          END IF;
        END $$
    """)
    op.execute("DROP TABLE substance_resolution_decisions")
    op.execute("DROP TABLE substance_resolution_candidate_occurrences")
    op.execute("DROP TABLE substance_resolution_candidates")
