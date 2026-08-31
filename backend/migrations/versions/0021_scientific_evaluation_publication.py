"""Add scientific evaluation execution and canonical publication persistence.

Revision ID: 0021_scientific_evaluation_publication
Revises: 0020_scientific_evidence_snapshots
"""

from alembic import op


revision = "0021_scientific_evaluation_publication"
down_revision = "0020_scientific_evidence_snapshots"
branch_labels = None
depends_on = None


NEW_TABLES = (
    "scientific_evaluation_executions",
    "scientific_evaluation_execution_attempts",
    "scientific_evidence_selection_decisions",
    "scientific_evaluation_results",
    "scientific_evaluation_result_components",
    "scientific_evaluation_traces",
    "scientific_evaluation_publications",
    "scientific_evaluation_replay_verifications",
    "scientific_evaluation_idempotency_keys",
)


def _governance_lineage_function(include_execution: bool) -> str:
    execution_owner = (
        "WHEN 'evaluation_execution' THEN 'evaluation_execution:' || NEW.execution_id "
        "WHEN 'evaluation_result' THEN 'evaluation_result:' || NEW.result_id"
        if include_execution
        else ""
    )
    execution_related = (
        "WHEN 'evaluation_execution' THEN 'evaluation_execution:' || NEW.related_execution_id "
        "WHEN 'evaluation_result' THEN 'evaluation_result:' || NEW.related_result_id"
        if include_execution
        else ""
    )
    row_execution_owner = (
        "WHEN 'evaluation_execution' THEN 'evaluation_execution:' || execution_id "
        "WHEN 'evaluation_result' THEN 'evaluation_result:' || result_id"
        if include_execution
        else ""
    )
    row_execution_related = (
        "WHEN 'evaluation_execution' THEN 'evaluation_execution:' || related_execution_id "
        "WHEN 'evaluation_result' THEN 'evaluation_result:' || related_result_id"
        if include_execution
        else ""
    )
    return f"""
        CREATE OR REPLACE FUNCTION scientific_evaluation_validate_governance_lineage()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
          new_owner_key TEXT;
          new_related_key TEXT;
          has_cycle BOOLEAN;
        BEGIN
          IF NEW.predecessor_event_id IS NOT NULL THEN
            WITH RECURSIVE predecessor_chain(id, path) AS (
              SELECT NEW.predecessor_event_id, ARRAY[NEW.predecessor_event_id]
              UNION ALL
              SELECT e.predecessor_event_id, c.path || e.predecessor_event_id
              FROM predecessor_chain c
              JOIN public.scientific_evaluation_governance_events e ON e.id = c.id
              WHERE e.predecessor_event_id IS NOT NULL
                AND NOT e.predecessor_event_id = ANY(c.path)
            )
            SELECT EXISTS (SELECT 1 FROM predecessor_chain WHERE id = NEW.id)
            INTO has_cycle;
            IF has_cycle THEN
              RAISE EXCEPTION 'governance predecessor lineage must be acyclic'
                USING ERRCODE = '23514';
            END IF;
          END IF;

          IF NEW.event_type = 'supersedes' THEN
            new_owner_key := CASE NEW.entity_type
              WHEN 'protocol' THEN 'protocol:' || NEW.protocol_id
              WHEN 'protocol_version' THEN 'protocol_version:' || NEW.protocol_version_id
              WHEN 'artifact' THEN 'artifact:' || NEW.artifact_id
              WHEN 'artifact_location' THEN 'artifact_location:' || NEW.artifact_location_id
              WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || NEW.snapshot_id
              {execution_owner}
            END;
            new_related_key := CASE NEW.entity_type
              WHEN 'protocol' THEN 'protocol:' || NEW.related_protocol_id
              WHEN 'protocol_version' THEN 'protocol_version:' || NEW.related_protocol_version_id
              WHEN 'artifact' THEN 'artifact:' || NEW.related_artifact_id
              WHEN 'artifact_location' THEN 'artifact_location:' || NEW.related_artifact_location_id
              WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || NEW.related_snapshot_id
              {execution_related}
            END;

            WITH RECURSIVE supersession_edges(owner_key, related_key) AS (
              SELECT
                CASE entity_type
                  WHEN 'protocol' THEN 'protocol:' || protocol_id
                  WHEN 'protocol_version' THEN 'protocol_version:' || protocol_version_id
                  WHEN 'artifact' THEN 'artifact:' || artifact_id
                  WHEN 'artifact_location' THEN 'artifact_location:' || artifact_location_id
                  WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || snapshot_id
                  {row_execution_owner}
                END,
                CASE entity_type
                  WHEN 'protocol' THEN 'protocol:' || related_protocol_id
                  WHEN 'protocol_version' THEN 'protocol_version:' || related_protocol_version_id
                  WHEN 'artifact' THEN 'artifact:' || related_artifact_id
                  WHEN 'artifact_location' THEN 'artifact_location:' || related_artifact_location_id
                  WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || related_snapshot_id
                  {row_execution_related}
                END
              FROM public.scientific_evaluation_governance_events
              WHERE event_type = 'supersedes' AND id <> NEW.id
            ), walk(node, path) AS (
              SELECT new_related_key, ARRAY[new_related_key]
              UNION ALL
              SELECT e.related_key, w.path || e.related_key
              FROM walk w
              JOIN supersession_edges e ON e.owner_key = w.node
              WHERE NOT e.related_key = ANY(w.path)
            )
            SELECT EXISTS (SELECT 1 FROM walk WHERE node = new_owner_key)
            INTO has_cycle;
            IF has_cycle THEN
              RAISE EXCEPTION 'governance supersession lineage must be acyclic'
                USING ERRCODE = '23514';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$
    """


def _preflight() -> None:
    tables = ", ".join(f"'{name}'" for name in NEW_TABLES)
    op.execute(
        f"""
        DO $$
        DECLARE collision TEXT;
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public' AND table_name='alembic_version'
              AND column_name='version_num' AND character_maximum_length>=64
          ) THEN
            RAISE EXCEPTION 'Cannot migrate 0021: Alembic version column is not VARCHAR(64).';
          END IF;
          IF to_regclass('scientific_evaluation_artifacts') IS NULL
             OR to_regclass('scientific_evaluation_artifact_locations') IS NULL
             OR to_regclass('scientific_evaluation_protocol_versions') IS NULL
             OR to_regclass('scientific_evaluation_governance_events') IS NULL
             OR to_regclass('scientific_evidence_snapshots') IS NULL
             OR to_regclass('scientific_evidence_snapshot_members') IS NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0021: expected 0019/0020 foundation is missing.';
          END IF;

          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='scientific_evaluation_governance_events'
              AND column_name='snapshot_id'
          ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname='ck_scientific_evaluation_governance_entity_reference'
              AND conrelid='scientific_evaluation_governance_events'::regclass
          ) OR to_regprocedure('scientific_evaluation_validate_governance_lineage()') IS NULL
             OR to_regprocedure('scientific_evaluation_reject_governance_mutation()') IS NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0021: expected 0020 governance shape is missing.';
          END IF;

          SELECT c.relname INTO collision
          FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE n.nspname='public' AND c.relname IN ({tables})
          LIMIT 1;
          IF collision IS NOT NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0021: object % already exists.', collision;
          END IF;

          SELECT c.relname INTO collision
          FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE n.nspname='public' AND c.relname IN (
            'uq_scientific_evaluation_execution_attempts_running',
            'idx_scientific_evaluation_executions_target',
            'idx_scientific_evaluation_executions_protocol_status',
            'idx_scientific_evaluation_executions_snapshot',
            'idx_scientific_evaluation_executions_comparison',
            'idx_scientific_evaluation_attempts_execution',
            'idx_scientific_evaluation_attempts_lease',
            'idx_scientific_evidence_selection_execution',
            'idx_scientific_evidence_selection_member',
            'idx_scientific_evaluation_components_result',
            'idx_scientific_evaluation_publications_time',
            'idx_scientific_evaluation_replay_verifications_comparison',
            'idx_scientific_evaluation_replay_verifications_status',
            'idx_scientific_evaluation_idempotency_expiry',
            'idx_scientific_evaluation_governance_execution',
            'idx_scientific_evaluation_governance_related_execution',
            'idx_scientific_evaluation_governance_result',
            'idx_scientific_evaluation_governance_related_result'
          ) LIMIT 1;
          IF collision IS NOT NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0021: index % already exists.', collision;
          END IF;

          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='scientific_evaluation_governance_events'
              AND column_name IN (
                'execution_id','related_execution_id','result_id','related_result_id'
              )
          ) THEN
            RAISE EXCEPTION 'Cannot migrate 0021: governance execution/result columns already exist.';
          END IF;

          SELECT p.proname INTO collision
          FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
          WHERE n.nspname='public' AND p.proname IN (
            'scientific_evaluation_guard_execution',
            'scientific_evaluation_validate_execution',
            'scientific_evaluation_guard_attempt',
            'scientific_evaluation_validate_attempt_consistency',
            'scientific_evaluation_reject_canonical_output_mutation',
            'scientific_evaluation_validate_selection',
            'scientific_evaluation_require_publication',
            'scientific_evaluation_validate_publication',
            'scientific_evaluation_validate_replay_verification',
            'scientific_evaluation_guard_idempotency'
          ) LIMIT 1;
          IF collision IS NOT NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0021: function % already exists.', collision;
          END IF;

          SELECT t.tgname INTO collision
          FROM pg_trigger t
          WHERE NOT t.tgisinternal AND t.tgname IN (
            'trg_scientific_evaluation_replay_verifications_immutable',
            'trg_scientific_evaluation_replay_verifications_validate'
          ) LIMIT 1;
          IF collision IS NOT NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0021: trigger % already exists.', collision;
          END IF;
        END $$
        """
    )


def upgrade() -> None:
    _preflight()

    op.execute(
        """
        CREATE TABLE scientific_evaluation_executions (
          id BIGSERIAL,
          execution_key UUID NOT NULL,
          protocol_version_id BIGINT NOT NULL,
          evidence_snapshot_id BIGINT NOT NULL,
          target_type VARCHAR(20) NOT NULL,
          substance_id BIGINT,
          ingredient_id BIGINT,
          target_artifact_id BIGINT NOT NULL,
          mapping_state_artifact_id BIGINT,
          input_artifact_id BIGINT NOT NULL,
          configuration_artifact_id BIGINT NOT NULL,
          semantic_identity_artifact_id BIGINT NOT NULL,
          comparison_execution_id BIGINT,
          execution_mode VARCHAR(20) NOT NULL,
          protocol_digest BYTEA NOT NULL,
          evidence_snapshot_digest BYTEA NOT NULL,
          input_digest BYTEA NOT NULL,
          configuration_digest BYTEA NOT NULL,
          semantic_execution_digest BYTEA NOT NULL,
          technical_status VARCHAR(20) NOT NULL DEFAULT 'pending',
          requested_by VARCHAR(255) NOT NULL,
          requested_at TIMESTAMPTZ NOT NULL,
          started_at TIMESTAMPTZ,
          completed_at TIMESTAMPTZ,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_executions PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_executions_key UNIQUE (execution_key),
          CONSTRAINT uq_scientific_evaluation_executions_semantic UNIQUE (semantic_execution_digest),
          CONSTRAINT uq_scientific_evaluation_executions_identity_artifact UNIQUE (semantic_identity_artifact_id),
          CONSTRAINT fk_scientific_evaluation_executions_protocol_version FOREIGN KEY (protocol_version_id)
            REFERENCES scientific_evaluation_protocol_versions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_snapshot FOREIGN KEY (evidence_snapshot_id)
            REFERENCES scientific_evidence_snapshots(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_substance FOREIGN KEY (substance_id)
            REFERENCES substances(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_ingredient FOREIGN KEY (ingredient_id)
            REFERENCES ingredients(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_target_artifact FOREIGN KEY (target_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_mapping_artifact FOREIGN KEY (mapping_state_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_input_artifact FOREIGN KEY (input_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_configuration_artifact FOREIGN KEY (configuration_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_identity_artifact FOREIGN KEY (semantic_identity_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_executions_comparison FOREIGN KEY (comparison_execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_executions_target_type CHECK (target_type IN ('substance','ingredient')),
          CONSTRAINT ck_scientific_evaluation_executions_target_shape CHECK (
            (target_type='substance' AND substance_id IS NOT NULL AND ingredient_id IS NULL AND mapping_state_artifact_id IS NULL)
            OR (target_type='ingredient' AND ingredient_id IS NOT NULL AND substance_id IS NULL AND mapping_state_artifact_id IS NOT NULL)
          ),
          CONSTRAINT ck_scientific_evaluation_executions_mode CHECK (
            execution_mode IN ('NORMAL','REPLAY','COUNTERFACTUAL','REFRESH')
          ),
          CONSTRAINT ck_scientific_evaluation_executions_comparison_shape CHECK (
            (execution_mode='NORMAL' AND comparison_execution_id IS NULL)
            OR (execution_mode<>'NORMAL' AND comparison_execution_id IS NOT NULL)
          ),
          CONSTRAINT ck_scientific_evaluation_executions_digest_length CHECK (
            octet_length(protocol_digest)=32 AND octet_length(evidence_snapshot_digest)=32
            AND octet_length(input_digest)=32 AND octet_length(configuration_digest)=32
            AND octet_length(semantic_execution_digest)=32
          ),
          CONSTRAINT ck_scientific_evaluation_executions_status CHECK (
            technical_status IN ('pending','running','completed','failed','cancelled')
          ),
          CONSTRAINT ck_scientific_evaluation_executions_actor CHECK (btrim(requested_by)<>''),
          CONSTRAINT ck_scientific_evaluation_executions_time CHECK (
            requested_at<=created_at AND (started_at IS NULL OR started_at>=requested_at)
            AND (completed_at IS NULL OR (started_at IS NOT NULL AND completed_at>=started_at))
          ),
          CONSTRAINT ck_scientific_evaluation_executions_state CHECK (
            (technical_status='pending' AND completed_at IS NULL)
            OR (technical_status='running' AND started_at IS NOT NULL AND completed_at IS NULL)
            OR (technical_status IN ('completed','failed') AND started_at IS NOT NULL AND completed_at IS NOT NULL)
            OR (technical_status='cancelled' AND completed_at IS NOT NULL)
          )
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_execution_attempts (
          id BIGSERIAL,
          attempt_key UUID NOT NULL,
          execution_id BIGINT NOT NULL,
          attempt_number INTEGER NOT NULL,
          attempt_status VARCHAR(20) NOT NULL DEFAULT 'running',
          engine_build_artifact_id BIGINT NOT NULL,
          worker_id VARCHAR(255),
          lease_token UUID,
          lease_expires_at TIMESTAMPTZ,
          heartbeat_at TIMESTAMPTZ,
          started_at TIMESTAMPTZ NOT NULL,
          ended_at TIMESTAMPTZ,
          error_category VARCHAR(30),
          error_code VARCHAR(100),
          retryable BOOLEAN,
          error_artifact_id BIGINT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_execution_attempts PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_execution_attempts_key UNIQUE (attempt_key),
          CONSTRAINT uq_scientific_evaluation_execution_attempts_number UNIQUE (execution_id,attempt_number),
          CONSTRAINT fk_scientific_evaluation_execution_attempts_execution FOREIGN KEY (execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_execution_attempts_build FOREIGN KEY (engine_build_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_execution_attempts_error FOREIGN KEY (error_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_execution_attempts_number CHECK (attempt_number>0),
          CONSTRAINT ck_scientific_evaluation_execution_attempts_status CHECK (
            attempt_status IN ('running','succeeded','failed','cancelled','abandoned')
          ),
          CONSTRAINT ck_scientific_evaluation_execution_attempts_error_category CHECK (
            error_category IS NULL OR error_category IN (
              'validation','artifact_integrity','engine_incompatible','canonicalization',
              'database','resource','cancelled','unexpected'
            )
          ),
          CONSTRAINT ck_scientific_evaluation_execution_attempts_worker CHECK (
            worker_id IS NULL OR btrim(worker_id)<>''
          ),
          CONSTRAINT ck_scientific_evaluation_execution_attempts_time CHECK (
            started_at>=created_at AND (ended_at IS NULL OR ended_at>=started_at)
          ),
          CONSTRAINT ck_scientific_evaluation_execution_attempts_state CHECK (
            (attempt_status='running' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL
              AND heartbeat_at IS NOT NULL AND lease_expires_at>heartbeat_at AND ended_at IS NULL
              AND error_category IS NULL AND error_code IS NULL AND retryable IS NULL AND error_artifact_id IS NULL)
            OR (attempt_status='succeeded' AND ended_at IS NOT NULL
              AND error_category IS NULL AND error_code IS NULL AND retryable IS NULL AND error_artifact_id IS NULL)
            OR (attempt_status IN ('failed','abandoned') AND ended_at IS NOT NULL
              AND error_category IS NOT NULL AND btrim(error_code)<>'' AND retryable IS NOT NULL)
            OR (attempt_status='cancelled' AND ended_at IS NOT NULL
              AND (error_category IS NULL OR error_category='cancelled'))
          )
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_scientific_evaluation_execution_attempts_running "
        "ON scientific_evaluation_execution_attempts(execution_id) WHERE attempt_status='running'"
    )

    op.execute(
        """
        CREATE TABLE scientific_evidence_selection_decisions (
          id BIGSERIAL,
          execution_id BIGINT NOT NULL,
          snapshot_member_id BIGINT NOT NULL,
          decision VARCHAR(20) NOT NULL,
          selection_role VARCHAR(20) NOT NULL,
          resolution_state VARCHAR(20) NOT NULL,
          reason_namespace VARCHAR(100) NOT NULL,
          reason_version VARCHAR(50) NOT NULL,
          primary_reason_code VARCHAR(100) NOT NULL,
          decision_artifact_id BIGINT NOT NULL,
          decision_digest BYTEA NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evidence_selection_decisions PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evidence_selection_decisions_member UNIQUE (execution_id,snapshot_member_id),
          CONSTRAINT fk_scientific_evidence_selection_decisions_execution FOREIGN KEY (execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_selection_decisions_member FOREIGN KEY (snapshot_member_id)
            REFERENCES scientific_evidence_snapshot_members(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_selection_decisions_artifact FOREIGN KEY (decision_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evidence_selection_decisions_decision CHECK (decision IN ('included','excluded')),
          CONSTRAINT ck_scientific_evidence_selection_decisions_role CHECK (
            selection_role IN ('contributing','context_only','none')
          ),
          CONSTRAINT ck_scientific_evidence_selection_decisions_resolution CHECK (
            resolution_state IN ('resolved','deferred')
          ),
          CONSTRAINT ck_scientific_evidence_selection_decisions_required CHECK (
            btrim(reason_namespace)<>'' AND btrim(reason_version)<>'' AND btrim(primary_reason_code)<>''
          ),
          CONSTRAINT ck_scientific_evidence_selection_decisions_digest CHECK (octet_length(decision_digest)=32),
          CONSTRAINT ck_scientific_evidence_selection_decisions_semantics CHECK (
            (decision='included' AND selection_role IN ('contributing','context_only') AND resolution_state='resolved')
            OR (decision='excluded' AND selection_role='none')
          )
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_results (
          id BIGSERIAL,
          result_key UUID NOT NULL,
          execution_id BIGINT NOT NULL,
          result_kind VARCHAR(100) NOT NULL,
          result_schema_version VARCHAR(50) NOT NULL,
          scientific_status_namespace VARCHAR(100) NOT NULL,
          scientific_status_version VARCHAR(50) NOT NULL,
          scientific_status_code VARCHAR(100) NOT NULL,
          canonical_artifact_id BIGINT NOT NULL,
          result_digest BYTEA NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_results PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_results_key UNIQUE (result_key),
          CONSTRAINT uq_scientific_evaluation_results_execution UNIQUE (execution_id),
          CONSTRAINT uq_scientific_evaluation_results_artifact UNIQUE (canonical_artifact_id),
          CONSTRAINT fk_scientific_evaluation_results_execution FOREIGN KEY (execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_results_artifact FOREIGN KEY (canonical_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_results_required CHECK (
            btrim(result_kind)<>'' AND btrim(result_schema_version)<>''
            AND btrim(scientific_status_namespace)<>'' AND btrim(scientific_status_version)<>''
            AND btrim(scientific_status_code)<>''
          ),
          CONSTRAINT ck_scientific_evaluation_results_digest CHECK (octet_length(result_digest)=32)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_result_components (
          id BIGSERIAL,
          result_id BIGINT NOT NULL,
          component_kind VARCHAR(100) NOT NULL,
          component_schema_version VARCHAR(50) NOT NULL,
          component_role VARCHAR(100) NOT NULL,
          component_artifact_id BIGINT NOT NULL,
          component_digest BYTEA NOT NULL,
          component_ordinal INTEGER NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_result_components PRIMARY KEY (id),
          CONSTRAINT fk_scientific_evaluation_result_components_result FOREIGN KEY (result_id)
            REFERENCES scientific_evaluation_results(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_result_components_artifact FOREIGN KEY (component_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT uq_scientific_evaluation_result_components_ordinal UNIQUE (result_id,component_ordinal),
          CONSTRAINT uq_scientific_evaluation_result_components_identity
            UNIQUE (result_id,component_role,component_kind,component_digest),
          CONSTRAINT ck_scientific_evaluation_result_components_required CHECK (
            btrim(component_kind)<>'' AND btrim(component_schema_version)<>'' AND btrim(component_role)<>''
          ),
          CONSTRAINT ck_scientific_evaluation_result_components_digest CHECK (octet_length(component_digest)=32),
          CONSTRAINT ck_scientific_evaluation_result_components_ordinal CHECK (component_ordinal>=0)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_traces (
          id BIGSERIAL,
          trace_key UUID NOT NULL,
          execution_id BIGINT NOT NULL,
          result_id BIGINT NOT NULL,
          trace_schema_version VARCHAR(50) NOT NULL,
          canonical_artifact_id BIGINT NOT NULL,
          trace_digest BYTEA NOT NULL,
          result_digest BYTEA NOT NULL,
          selection_digest BYTEA NOT NULL,
          protocol_digest BYTEA NOT NULL,
          evidence_snapshot_digest BYTEA NOT NULL,
          input_digest BYTEA NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_traces PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_traces_key UNIQUE (trace_key),
          CONSTRAINT uq_scientific_evaluation_traces_execution UNIQUE (execution_id),
          CONSTRAINT uq_scientific_evaluation_traces_result UNIQUE (result_id),
          CONSTRAINT uq_scientific_evaluation_traces_artifact UNIQUE (canonical_artifact_id),
          CONSTRAINT fk_scientific_evaluation_traces_execution FOREIGN KEY (execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_traces_result FOREIGN KEY (result_id)
            REFERENCES scientific_evaluation_results(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_traces_artifact FOREIGN KEY (canonical_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_traces_version CHECK (btrim(trace_schema_version)<>''),
          CONSTRAINT ck_scientific_evaluation_traces_digest CHECK (
            octet_length(trace_digest)=32 AND octet_length(result_digest)=32
            AND octet_length(selection_digest)=32 AND octet_length(protocol_digest)=32
            AND octet_length(evidence_snapshot_digest)=32 AND octet_length(input_digest)=32
          )
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_publications (
          id BIGSERIAL,
          publication_key UUID NOT NULL,
          execution_id BIGINT NOT NULL,
          result_id BIGINT NOT NULL,
          trace_id BIGINT NOT NULL,
          successful_attempt_id BIGINT NOT NULL,
          selection_manifest_artifact_id BIGINT NOT NULL,
          bundle_artifact_id BIGINT NOT NULL,
          selection_digest BYTEA NOT NULL,
          result_digest BYTEA NOT NULL,
          trace_digest BYTEA NOT NULL,
          publication_bundle_digest BYTEA NOT NULL,
          published_by VARCHAR(255) NOT NULL,
          published_at TIMESTAMPTZ NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_publications PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_publications_key UNIQUE (publication_key),
          CONSTRAINT uq_scientific_evaluation_publications_execution UNIQUE (execution_id),
          CONSTRAINT uq_scientific_evaluation_publications_result UNIQUE (result_id),
          CONSTRAINT uq_scientific_evaluation_publications_trace UNIQUE (trace_id),
          CONSTRAINT uq_scientific_evaluation_publications_attempt UNIQUE (successful_attempt_id),
          CONSTRAINT uq_scientific_evaluation_publications_selection_artifact UNIQUE (selection_manifest_artifact_id),
          CONSTRAINT uq_scientific_evaluation_publications_bundle_artifact UNIQUE (bundle_artifact_id),
          CONSTRAINT uq_scientific_evaluation_publications_bundle_digest UNIQUE (publication_bundle_digest),
          CONSTRAINT fk_scientific_evaluation_publications_execution FOREIGN KEY (execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_publications_result FOREIGN KEY (result_id)
            REFERENCES scientific_evaluation_results(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_publications_trace FOREIGN KEY (trace_id)
            REFERENCES scientific_evaluation_traces(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_publications_attempt FOREIGN KEY (successful_attempt_id)
            REFERENCES scientific_evaluation_execution_attempts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_publications_selection FOREIGN KEY (selection_manifest_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_publications_bundle FOREIGN KEY (bundle_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_publications_digest CHECK (
            octet_length(selection_digest)=32 AND octet_length(result_digest)=32
            AND octet_length(trace_digest)=32 AND octet_length(publication_bundle_digest)=32
          ),
          CONSTRAINT ck_scientific_evaluation_publications_actor CHECK (btrim(published_by)<>''),
          CONSTRAINT ck_scientific_evaluation_publications_time CHECK (published_at>=created_at)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_replay_verifications (
          id BIGSERIAL,
          verification_key UUID NOT NULL,
          execution_id BIGINT NOT NULL,
          comparison_publication_id BIGINT NOT NULL,
          successful_attempt_id BIGINT NOT NULL,
          verification_artifact_id BIGINT NOT NULL,
          verification_digest BYTEA NOT NULL,
          expected_publication_bundle_digest BYTEA NOT NULL,
          expected_selection_digest BYTEA NOT NULL,
          expected_result_digest BYTEA NOT NULL,
          expected_trace_digest BYTEA NOT NULL,
          recomputed_selection_artifact_id BIGINT NOT NULL,
          recomputed_result_artifact_id BIGINT NOT NULL,
          recomputed_trace_artifact_id BIGINT NOT NULL,
          recomputed_selection_digest BYTEA NOT NULL,
          recomputed_result_digest BYTEA NOT NULL,
          recomputed_trace_digest BYTEA NOT NULL,
          verification_status VARCHAR(20) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_replay_verifications PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_replay_verifications_key UNIQUE (verification_key),
          CONSTRAINT uq_scientific_evaluation_replay_verifications_execution UNIQUE (execution_id),
          CONSTRAINT uq_scientific_evaluation_replay_verifications_attempt UNIQUE (successful_attempt_id),
          CONSTRAINT uq_scientific_evaluation_replay_verifications_artifact UNIQUE (verification_artifact_id),
          CONSTRAINT fk_scientific_evaluation_replay_verifications_execution FOREIGN KEY (execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_replay_verifications_comparison FOREIGN KEY (comparison_publication_id)
            REFERENCES scientific_evaluation_publications(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_replay_verifications_attempt FOREIGN KEY (successful_attempt_id)
            REFERENCES scientific_evaluation_execution_attempts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_replay_verifications_artifact FOREIGN KEY (verification_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_replay_verifications_selection FOREIGN KEY (recomputed_selection_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_replay_verifications_result FOREIGN KEY (recomputed_result_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_replay_verifications_trace FOREIGN KEY (recomputed_trace_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_replay_verifications_status CHECK (
            verification_status IN ('matched','mismatch')
          ),
          CONSTRAINT ck_scientific_evaluation_replay_verifications_digest CHECK (
            octet_length(verification_digest)=32
            AND octet_length(expected_publication_bundle_digest)=32
            AND octet_length(expected_selection_digest)=32
            AND octet_length(expected_result_digest)=32
            AND octet_length(expected_trace_digest)=32
            AND octet_length(recomputed_selection_digest)=32
            AND octet_length(recomputed_result_digest)=32
            AND octet_length(recomputed_trace_digest)=32
          ),
          CONSTRAINT ck_scientific_evaluation_replay_verifications_equality CHECK (
            (verification_status='matched'
              AND recomputed_selection_digest=expected_selection_digest
              AND recomputed_result_digest=expected_result_digest
              AND recomputed_trace_digest=expected_trace_digest)
            OR (verification_status='mismatch' AND (
              recomputed_selection_digest<>expected_selection_digest
              OR recomputed_result_digest<>expected_result_digest
              OR recomputed_trace_digest<>expected_trace_digest
            ))
          )
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_idempotency_keys (
          id BIGSERIAL,
          operation_type VARCHAR(100) NOT NULL,
          request_scope VARCHAR(255) NOT NULL,
          request_key VARCHAR(255) NOT NULL,
          expected_semantic_digest BYTEA NOT NULL,
          execution_id BIGINT,
          attempt_id BIGINT,
          publication_id BIGINT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          expires_at TIMESTAMPTZ,
          CONSTRAINT pk_scientific_evaluation_idempotency_keys PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_idempotency_keys_scope UNIQUE (operation_type,request_scope,request_key),
          CONSTRAINT fk_scientific_evaluation_idempotency_keys_execution FOREIGN KEY (execution_id)
            REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_idempotency_keys_attempt FOREIGN KEY (attempt_id)
            REFERENCES scientific_evaluation_execution_attempts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_idempotency_keys_publication FOREIGN KEY (publication_id)
            REFERENCES scientific_evaluation_publications(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_idempotency_keys_required CHECK (
            btrim(operation_type)<>'' AND btrim(request_scope)<>'' AND btrim(request_key)<>''
          ),
          CONSTRAINT ck_scientific_evaluation_idempotency_keys_digest CHECK (octet_length(expected_semantic_digest)=32),
          CONSTRAINT ck_scientific_evaluation_idempotency_keys_owner CHECK (
            num_nonnulls(execution_id,attempt_id,publication_id)<=1
          ),
          CONSTRAINT ck_scientific_evaluation_idempotency_keys_time CHECK (
            expires_at IS NULL OR expires_at>created_at
          )
        )
        """
    )

    for sql in (
        "CREATE INDEX idx_scientific_evaluation_executions_target ON scientific_evaluation_executions(target_type,substance_id,ingredient_id,requested_at DESC,id)",
        "CREATE INDEX idx_scientific_evaluation_executions_protocol_status ON scientific_evaluation_executions(protocol_version_id,technical_status,created_at)",
        "CREATE INDEX idx_scientific_evaluation_executions_snapshot ON scientific_evaluation_executions(evidence_snapshot_id)",
        "CREATE INDEX idx_scientific_evaluation_executions_comparison ON scientific_evaluation_executions(comparison_execution_id) WHERE comparison_execution_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_attempts_execution ON scientific_evaluation_execution_attempts(execution_id,attempt_number DESC)",
        "CREATE INDEX idx_scientific_evaluation_attempts_lease ON scientific_evaluation_execution_attempts(lease_expires_at,execution_id) WHERE attempt_status='running'",
        "CREATE INDEX idx_scientific_evidence_selection_execution ON scientific_evidence_selection_decisions(execution_id,decision,resolution_state,primary_reason_code)",
        "CREATE INDEX idx_scientific_evidence_selection_member ON scientific_evidence_selection_decisions(snapshot_member_id)",
        "CREATE INDEX idx_scientific_evaluation_components_result ON scientific_evaluation_result_components(result_id,component_kind,component_ordinal)",
        "CREATE INDEX idx_scientific_evaluation_publications_time ON scientific_evaluation_publications(published_at DESC,id DESC)",
        "CREATE INDEX idx_scientific_evaluation_replay_verifications_comparison ON scientific_evaluation_replay_verifications(comparison_publication_id)",
        "CREATE INDEX idx_scientific_evaluation_replay_verifications_status ON scientific_evaluation_replay_verifications(verification_status,created_at DESC,id DESC)",
        "CREATE INDEX idx_scientific_evaluation_idempotency_expiry ON scientific_evaluation_idempotency_keys(expires_at) WHERE expires_at IS NOT NULL",
    ):
        op.execute(sql)

    op.execute(
        "ALTER TABLE scientific_evaluation_governance_events "
        "ADD COLUMN execution_id BIGINT, ADD COLUMN related_execution_id BIGINT, "
        "ADD COLUMN result_id BIGINT, ADD COLUMN related_result_id BIGINT"
    )
    for sql in (
        "ALTER TABLE scientific_evaluation_governance_events ADD CONSTRAINT fk_scientific_evaluation_governance_execution FOREIGN KEY (execution_id) REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT",
        "ALTER TABLE scientific_evaluation_governance_events ADD CONSTRAINT fk_scientific_evaluation_governance_related_execution FOREIGN KEY (related_execution_id) REFERENCES scientific_evaluation_executions(id) ON DELETE RESTRICT",
        "ALTER TABLE scientific_evaluation_governance_events ADD CONSTRAINT fk_scientific_evaluation_governance_result FOREIGN KEY (result_id) REFERENCES scientific_evaluation_results(id) ON DELETE RESTRICT",
        "ALTER TABLE scientific_evaluation_governance_events ADD CONSTRAINT fk_scientific_evaluation_governance_related_result FOREIGN KEY (related_result_id) REFERENCES scientific_evaluation_results(id) ON DELETE RESTRICT",
    ):
        op.execute(sql)

    for name in (
        "ck_scientific_evaluation_governance_entity_type",
        "ck_scientific_evaluation_governance_event_type",
        "ck_scientific_evaluation_governance_entity_reference",
        "ck_scientific_evaluation_governance_related_reference",
        "ck_scientific_evaluation_governance_not_self",
    ):
        op.execute(f"ALTER TABLE scientific_evaluation_governance_events DROP CONSTRAINT {name}")

    op.execute(
        """
        ALTER TABLE scientific_evaluation_governance_events
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_type CHECK (
          entity_type IN (
            'protocol','protocol_version','artifact','artifact_location','evidence_snapshot',
            'evaluation_execution','evaluation_result'
          )
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_event_type CHECK (
          event_type IN (
            'submitted_for_review','approved','published','deprecated','retired',
            'supersedes','retracts','integrity_compromised','annotation',
            'review_disposition','counterfactual_authorized'
          )
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_reference CHECK (
          num_nonnulls(protocol_id,protocol_version_id,artifact_id,artifact_location_id,
            snapshot_id,execution_id,result_id)=1
          AND (entity_type='protocol')=(protocol_id IS NOT NULL)
          AND (entity_type='protocol_version')=(protocol_version_id IS NOT NULL)
          AND (entity_type='artifact')=(artifact_id IS NOT NULL)
          AND (entity_type='artifact_location')=(artifact_location_id IS NOT NULL)
          AND (entity_type='evidence_snapshot')=(snapshot_id IS NOT NULL)
          AND (entity_type='evaluation_execution')=(execution_id IS NOT NULL)
          AND (entity_type='evaluation_result')=(result_id IS NOT NULL)
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_related_reference CHECK (
          num_nonnulls(related_protocol_id,related_protocol_version_id,related_artifact_id,
            related_artifact_location_id,related_snapshot_id,related_execution_id,related_result_id)<=1
          AND (
            num_nonnulls(related_protocol_id,related_protocol_version_id,related_artifact_id,
              related_artifact_location_id,related_snapshot_id,related_execution_id,related_result_id)=0
            OR (entity_type='protocol' AND related_protocol_id IS NOT NULL)
            OR (entity_type='protocol_version' AND related_protocol_version_id IS NOT NULL)
            OR (entity_type='artifact' AND related_artifact_id IS NOT NULL)
            OR (entity_type='artifact_location' AND related_artifact_location_id IS NOT NULL)
            OR (entity_type='evidence_snapshot' AND related_snapshot_id IS NOT NULL)
            OR (entity_type='evaluation_execution' AND related_execution_id IS NOT NULL)
            OR (entity_type='evaluation_result' AND related_result_id IS NOT NULL)
          )
          AND (
            event_type<>'supersedes'
            OR num_nonnulls(related_protocol_id,related_protocol_version_id,related_artifact_id,
              related_artifact_location_id,related_snapshot_id,related_execution_id,related_result_id)=1
          )
          AND (event_type<>'counterfactual_authorized' OR entity_type='evaluation_execution')
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_not_self CHECK (
          (protocol_id IS NULL OR related_protocol_id IS NULL OR protocol_id<>related_protocol_id)
          AND (protocol_version_id IS NULL OR related_protocol_version_id IS NULL OR protocol_version_id<>related_protocol_version_id)
          AND (artifact_id IS NULL OR related_artifact_id IS NULL OR artifact_id<>related_artifact_id)
          AND (artifact_location_id IS NULL OR related_artifact_location_id IS NULL OR artifact_location_id<>related_artifact_location_id)
          AND (snapshot_id IS NULL OR related_snapshot_id IS NULL OR snapshot_id<>related_snapshot_id)
          AND (execution_id IS NULL OR related_execution_id IS NULL OR execution_id<>related_execution_id)
          AND (result_id IS NULL OR related_result_id IS NULL OR result_id<>related_result_id)
          AND (predecessor_event_id IS NULL OR predecessor_event_id<>id)
        )
        """
    )
    for sql in (
        "CREATE INDEX idx_scientific_evaluation_governance_execution ON scientific_evaluation_governance_events(execution_id,effective_at,id) WHERE execution_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_related_execution ON scientific_evaluation_governance_events(related_execution_id) WHERE related_execution_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_result ON scientific_evaluation_governance_events(result_id,effective_at,id) WHERE result_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_related_result ON scientific_evaluation_governance_events(related_result_id) WHERE related_result_id IS NOT NULL",
    ):
        op.execute(sql)
    op.execute(_governance_lineage_function(include_execution=True))

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_execution()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        BEGIN
          IF TG_OP='INSERT' THEN
            IF NEW.technical_status<>'pending' THEN
              RAISE EXCEPTION 'scientific evaluation execution must start pending'
                USING ERRCODE='23514';
            END IF;
            RETURN NEW;
          END IF;
          IF TG_OP='DELETE' THEN
            RAISE EXCEPTION 'scientific evaluation executions are historical and cannot be deleted'
              USING ERRCODE='23514';
          END IF;
          IF NEW.execution_key IS DISTINCT FROM OLD.execution_key
             OR NEW.protocol_version_id IS DISTINCT FROM OLD.protocol_version_id
             OR NEW.evidence_snapshot_id IS DISTINCT FROM OLD.evidence_snapshot_id
             OR NEW.target_type IS DISTINCT FROM OLD.target_type
             OR NEW.substance_id IS DISTINCT FROM OLD.substance_id
             OR NEW.ingredient_id IS DISTINCT FROM OLD.ingredient_id
             OR NEW.target_artifact_id IS DISTINCT FROM OLD.target_artifact_id
             OR NEW.mapping_state_artifact_id IS DISTINCT FROM OLD.mapping_state_artifact_id
             OR NEW.input_artifact_id IS DISTINCT FROM OLD.input_artifact_id
             OR NEW.configuration_artifact_id IS DISTINCT FROM OLD.configuration_artifact_id
             OR NEW.semantic_identity_artifact_id IS DISTINCT FROM OLD.semantic_identity_artifact_id
             OR NEW.comparison_execution_id IS DISTINCT FROM OLD.comparison_execution_id
             OR NEW.execution_mode IS DISTINCT FROM OLD.execution_mode
             OR NEW.protocol_digest IS DISTINCT FROM OLD.protocol_digest
             OR NEW.evidence_snapshot_digest IS DISTINCT FROM OLD.evidence_snapshot_digest
             OR NEW.input_digest IS DISTINCT FROM OLD.input_digest
             OR NEW.configuration_digest IS DISTINCT FROM OLD.configuration_digest
             OR NEW.semantic_execution_digest IS DISTINCT FROM OLD.semantic_execution_digest
             OR NEW.requested_by IS DISTINCT FROM OLD.requested_by
             OR NEW.requested_at IS DISTINCT FROM OLD.requested_at
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'scientific evaluation execution semantic identity is immutable'
              USING ERRCODE='23514';
          END IF;
          IF OLD.technical_status IN ('completed','cancelled') AND NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'terminal scientific evaluation execution is immutable'
              USING ERRCODE='23514';
          END IF;
          IF NEW.technical_status IS DISTINCT FROM OLD.technical_status AND NOT (
            (OLD.technical_status='pending' AND NEW.technical_status IN ('running','cancelled'))
            OR (OLD.technical_status='running' AND NEW.technical_status IN ('pending','completed','failed','cancelled'))
            OR (OLD.technical_status='failed' AND NEW.technical_status='running')
          ) THEN
            RAISE EXCEPTION 'invalid scientific execution transition: % -> %',
              OLD.technical_status,NEW.technical_status USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER trg_scientific_evaluation_executions_guard "
        "BEFORE INSERT OR UPDATE OR DELETE ON scientific_evaluation_executions "
        "FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_execution()"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_execution()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        DECLARE
          current_row public.scientific_evaluation_executions%ROWTYPE;
          protocol_row RECORD;
          snapshot_row RECORD;
          target_row RECORD;
          mapping_row RECORD;
          input_row RECORD;
          config_row RECORD;
          identity_row RECORD;
          comparison_row RECORD;
          running_count INTEGER;
          latest_attempt_status TEXT;
          latest_attempt_retryable BOOLEAN;
        BEGIN
          SELECT * INTO current_row FROM public.scientific_evaluation_executions WHERE id=NEW.id;
          IF NOT FOUND THEN
            RETURN NEW;
          END IF;
          NEW:=current_row;
          SELECT lifecycle_status,published_at,protocol_digest INTO protocol_row
          FROM public.scientific_evaluation_protocol_versions WHERE id=NEW.protocol_version_id;
          IF protocol_row.protocol_digest IS DISTINCT FROM NEW.protocol_digest THEN
            RAISE EXCEPTION 'execution protocol digest mismatch' USING ERRCODE='23514';
          END IF;
          IF NEW.execution_mode IN ('NORMAL','REFRESH') AND protocol_row.lifecycle_status<>'published' THEN
            RAISE EXCEPTION 'execution mode requires published protocol' USING ERRCODE='23514';
          END IF;
          IF NEW.execution_mode IN ('REPLAY','COUNTERFACTUAL')
             AND (protocol_row.lifecycle_status NOT IN ('published','deprecated','retired')
                  OR protocol_row.published_at IS NULL) THEN
            RAISE EXCEPTION 'historical execution mode requires historically published protocol'
              USING ERRCODE='23514';
          END IF;

          SELECT status,snapshot_digest INTO snapshot_row
          FROM public.scientific_evidence_snapshots WHERE id=NEW.evidence_snapshot_id;
          IF snapshot_row.status<>'sealed' OR snapshot_row.snapshot_digest IS DISTINCT FROM NEW.evidence_snapshot_digest THEN
            RAISE EXCEPTION 'execution requires matching sealed evidence snapshot' USING ERRCODE='23514';
          END IF;

          SELECT * INTO target_row FROM public.scientific_evaluation_artifacts WHERE id=NEW.target_artifact_id;
          SELECT * INTO input_row FROM public.scientific_evaluation_artifacts WHERE id=NEW.input_artifact_id;
          SELECT * INTO config_row FROM public.scientific_evaluation_artifacts WHERE id=NEW.configuration_artifact_id;
          SELECT * INTO identity_row FROM public.scientific_evaluation_artifacts WHERE id=NEW.semantic_identity_artifact_id;
          IF target_row.artifact_kind<>'scientific_evaluation_target' OR target_row.schema_version<>'1'
             OR target_row.canonicalization_version<>'wye-c14n-json-v1' THEN
            RAISE EXCEPTION 'invalid execution target artifact role' USING ERRCODE='23514';
          END IF;
          IF input_row.artifact_kind<>'scientific_evaluation_input' OR input_row.schema_version<>'1'
             OR input_row.canonicalization_version<>'wye-c14n-json-v1'
             OR input_row.content_digest IS DISTINCT FROM NEW.input_digest THEN
            RAISE EXCEPTION 'invalid execution input artifact role or digest' USING ERRCODE='23514';
          END IF;
          IF config_row.artifact_kind<>'scientific_evaluation_configuration' OR config_row.schema_version<>'1'
             OR config_row.canonicalization_version<>'wye-c14n-json-v1'
             OR config_row.content_digest IS DISTINCT FROM NEW.configuration_digest THEN
            RAISE EXCEPTION 'invalid execution configuration artifact role or digest' USING ERRCODE='23514';
          END IF;
          IF identity_row.artifact_kind<>'scientific_evaluation_execution_identity' OR identity_row.schema_version<>'1'
             OR identity_row.canonicalization_version<>'wye-c14n-json-v1'
             OR identity_row.content_digest IS DISTINCT FROM NEW.semantic_execution_digest THEN
            RAISE EXCEPTION 'invalid execution identity artifact role or digest' USING ERRCODE='23514';
          END IF;
          IF NEW.mapping_state_artifact_id IS NOT NULL THEN
            SELECT * INTO mapping_row FROM public.scientific_evaluation_artifacts WHERE id=NEW.mapping_state_artifact_id;
            IF mapping_row.artifact_kind<>'scientific_mapping_state_manifest'
               OR mapping_row.schema_version<>'1'
               OR mapping_row.canonicalization_version<>'wye-c14n-json-v1' THEN
              RAISE EXCEPTION 'invalid mapping-state artifact role' USING ERRCODE='23514';
            END IF;
          END IF;

          IF EXISTS (
            SELECT 1 FROM (VALUES
              (NEW.target_artifact_id),(NEW.input_artifact_id),(NEW.configuration_artifact_id),
              (NEW.semantic_identity_artifact_id),(NEW.mapping_state_artifact_id)
            ) AS roots(id)
            WHERE id IS NOT NULL AND NOT EXISTS (
              SELECT 1 FROM public.scientific_evaluation_artifact_locations l
              WHERE l.artifact_id=roots.id AND l.location_status='verified' AND l.verified_at IS NOT NULL
            )
          ) THEN
            RAISE EXCEPTION 'execution root artifact lacks verified location' USING ERRCODE='23514';
          END IF;

          IF NEW.comparison_execution_id IS NOT NULL THEN
            SELECT * INTO comparison_row FROM public.scientific_evaluation_executions
            WHERE id=NEW.comparison_execution_id;
            IF comparison_row.id IS NULL THEN
              RAISE EXCEPTION 'comparison execution missing' USING ERRCODE='23514';
            END IF;
            IF NEW.execution_mode='REPLAY' AND NOT (
              NEW.protocol_version_id=comparison_row.protocol_version_id
              AND NEW.evidence_snapshot_id=comparison_row.evidence_snapshot_id
              AND NEW.input_artifact_id=comparison_row.input_artifact_id
              AND NEW.configuration_artifact_id=comparison_row.configuration_artifact_id
            ) THEN
              RAISE EXCEPTION 'REPLAY must preserve protocol, snapshot, input and configuration'
                USING ERRCODE='23514';
            END IF;
            IF NEW.execution_mode='COUNTERFACTUAL' AND NOT (
              NEW.evidence_snapshot_id=comparison_row.evidence_snapshot_id
              AND NEW.input_artifact_id=comparison_row.input_artifact_id
              AND (NEW.protocol_version_id<>comparison_row.protocol_version_id
                   OR NEW.configuration_artifact_id<>comparison_row.configuration_artifact_id)
            ) THEN
              RAISE EXCEPTION 'COUNTERFACTUAL root relationship invalid' USING ERRCODE='23514';
            END IF;
            IF NEW.execution_mode='REFRESH' AND NOT (
              NEW.target_type=comparison_row.target_type
              AND NEW.substance_id IS NOT DISTINCT FROM comparison_row.substance_id
              AND NEW.ingredient_id IS NOT DISTINCT FROM comparison_row.ingredient_id
              AND (NEW.evidence_snapshot_id<>comparison_row.evidence_snapshot_id
                   OR NEW.input_artifact_id<>comparison_row.input_artifact_id)
            ) THEN
              RAISE EXCEPTION 'REFRESH root relationship invalid' USING ERRCODE='23514';
            END IF;
          END IF;

          IF NEW.execution_mode='COUNTERFACTUAL' AND NOT EXISTS (
            SELECT 1 FROM public.scientific_evaluation_governance_events g
            WHERE g.entity_type='evaluation_execution' AND g.execution_id=NEW.id
              AND g.event_type='counterfactual_authorized'
          ) THEN
            RAISE EXCEPTION 'COUNTERFACTUAL execution requires governance authorization'
              USING ERRCODE='23514';
          END IF;

          SELECT count(*) INTO running_count FROM public.scientific_evaluation_execution_attempts
          WHERE execution_id=NEW.id AND attempt_status='running';
          IF NEW.technical_status='running' AND running_count<>1 THEN
            RAISE EXCEPTION 'running execution requires exactly one running attempt' USING ERRCODE='23514';
          END IF;
          IF NEW.technical_status<>'running' AND running_count<>0 THEN
            RAISE EXCEPTION 'non-running execution cannot retain a running attempt' USING ERRCODE='23514';
          END IF;
          IF NEW.technical_status='pending' AND EXISTS (
            SELECT 1 FROM public.scientific_evaluation_execution_attempts
            WHERE execution_id=NEW.id
          ) THEN
            SELECT attempt_status,retryable
            INTO latest_attempt_status,latest_attempt_retryable
            FROM public.scientific_evaluation_execution_attempts
            WHERE execution_id=NEW.id
            ORDER BY attempt_number DESC
            LIMIT 1;
            IF latest_attempt_status NOT IN ('failed','abandoned')
               OR latest_attempt_retryable IS DISTINCT FROM TRUE THEN
              RAISE EXCEPTION 'pending retry requires latest failed or abandoned retryable attempt'
                USING ERRCODE='23514';
            END IF;
          END IF;
          IF NEW.technical_status='completed' THEN
            IF NEW.execution_mode='REPLAY' AND (
              NOT EXISTS (
                SELECT 1 FROM public.scientific_evaluation_replay_verifications v
                WHERE v.execution_id=NEW.id
              ) OR EXISTS (
                SELECT 1 FROM public.scientific_evaluation_publications p
                WHERE p.execution_id=NEW.id
              )
            ) THEN
              RAISE EXCEPTION 'completed REPLAY requires verification and forbids publication'
                USING ERRCODE='23514';
            ELSIF NEW.execution_mode<>'REPLAY' AND (
              NOT EXISTS (
                SELECT 1 FROM public.scientific_evaluation_publications p
                WHERE p.execution_id=NEW.id
              ) OR EXISTS (
                SELECT 1 FROM public.scientific_evaluation_replay_verifications v
                WHERE v.execution_id=NEW.id
              )
            ) THEN
              RAISE EXCEPTION 'completed canonical execution requires publication and forbids replay verification'
                USING ERRCODE='23514';
            END IF;
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_executions_validate "
        "AFTER INSERT OR UPDATE ON scientific_evaluation_executions DEFERRABLE INITIALLY DEFERRED "
        "FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_validate_execution()"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_attempt()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        BEGIN
          IF TG_OP='INSERT' THEN
            IF NEW.attempt_status<>'running' THEN
              RAISE EXCEPTION 'scientific evaluation attempt must start running'
                USING ERRCODE='23514';
            END IF;
            RETURN NEW;
          END IF;
          IF TG_OP='DELETE' THEN
            RAISE EXCEPTION 'scientific evaluation attempts are append-only history'
              USING ERRCODE='23514';
          END IF;
          IF NEW.attempt_key IS DISTINCT FROM OLD.attempt_key
             OR NEW.execution_id IS DISTINCT FROM OLD.execution_id
             OR NEW.attempt_number IS DISTINCT FROM OLD.attempt_number
             OR NEW.engine_build_artifact_id IS DISTINCT FROM OLD.engine_build_artifact_id
             OR NEW.worker_id IS DISTINCT FROM OLD.worker_id
             OR NEW.started_at IS DISTINCT FROM OLD.started_at
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'scientific evaluation attempt identity is immutable'
              USING ERRCODE='23514';
          END IF;
          IF OLD.attempt_status<>'running' AND NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'terminal scientific evaluation attempt is immutable'
              USING ERRCODE='23514';
          END IF;
          IF OLD.attempt_status='running'
             AND NEW.attempt_status NOT IN ('running','succeeded','failed','cancelled','abandoned') THEN
            RAISE EXCEPTION 'invalid scientific evaluation attempt transition'
              USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER trg_scientific_evaluation_attempts_guard "
        "BEFORE INSERT OR UPDATE OR DELETE ON scientific_evaluation_execution_attempts "
        "FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_attempt()"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_attempt_consistency()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        DECLARE
          current_row public.scientific_evaluation_execution_attempts%ROWTYPE;
          execution_status TEXT;
          execution_mode TEXT;
          build_row RECORD;
          error_row RECORD;
        BEGIN
          SELECT * INTO current_row FROM public.scientific_evaluation_execution_attempts WHERE id=NEW.id;
          IF NOT FOUND THEN
            RETURN NEW;
          END IF;
          NEW:=current_row;
          SELECT e.technical_status,e.execution_mode INTO execution_status,execution_mode
          FROM public.scientific_evaluation_executions e WHERE e.id=NEW.execution_id;
          SELECT * INTO build_row FROM public.scientific_evaluation_artifacts
          WHERE id=NEW.engine_build_artifact_id;
          IF build_row.artifact_kind<>'scientific_evaluation_engine_build'
             OR build_row.schema_version<>'1'
             OR build_row.canonicalization_version<>'wye-c14n-json-v1'
             OR NOT EXISTS (
               SELECT 1 FROM public.scientific_evaluation_artifact_locations l
               WHERE l.artifact_id=build_row.id AND l.location_status='verified'
                 AND l.verified_at IS NOT NULL
             ) THEN
            RAISE EXCEPTION 'invalid or unverified engine build artifact' USING ERRCODE='23514';
          END IF;
          IF NEW.error_artifact_id IS NOT NULL THEN
            SELECT * INTO error_row FROM public.scientific_evaluation_artifacts
            WHERE id=NEW.error_artifact_id;
            IF error_row.artifact_kind<>'scientific_evaluation_attempt_error'
               OR error_row.schema_version<>'1'
               OR error_row.canonicalization_version<>'wye-c14n-json-v1'
               OR NOT EXISTS (
                 SELECT 1 FROM public.scientific_evaluation_artifact_locations l
                 WHERE l.artifact_id=error_row.id AND l.location_status='verified'
                   AND l.verified_at IS NOT NULL
               ) THEN
              RAISE EXCEPTION 'invalid or unverified attempt error artifact' USING ERRCODE='23514';
            END IF;
          END IF;
          IF NEW.attempt_status='running' AND execution_status<>'running' THEN
            RAISE EXCEPTION 'running attempt requires running execution' USING ERRCODE='23514';
          END IF;
          IF NEW.attempt_status='succeeded' THEN
            IF execution_status<>'completed' THEN
              RAISE EXCEPTION 'succeeded attempt requires completed execution'
                USING ERRCODE='23514';
            ELSIF execution_mode='REPLAY' AND NOT EXISTS (
              SELECT 1 FROM public.scientific_evaluation_replay_verifications v
              WHERE v.execution_id=NEW.execution_id AND v.successful_attempt_id=NEW.id
            ) THEN
              RAISE EXCEPTION 'succeeded REPLAY attempt requires its replay verification'
                USING ERRCODE='23514';
            ELSIF execution_mode<>'REPLAY' AND NOT EXISTS (
              SELECT 1 FROM public.scientific_evaluation_publications p
              WHERE p.execution_id=NEW.execution_id AND p.successful_attempt_id=NEW.id
            ) THEN
              RAISE EXCEPTION 'succeeded attempt requires its completed canonical publication'
                USING ERRCODE='23514';
            END IF;
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_attempts_validate "
        "AFTER INSERT OR UPDATE ON scientific_evaluation_execution_attempts "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION scientific_evaluation_validate_attempt_consistency()"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_reject_canonical_output_mutation()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        BEGIN
          RAISE EXCEPTION '% rows are immutable canonical history',TG_TABLE_NAME
            USING ERRCODE='23514';
        END $$
        """
    )
    for table in (
        "scientific_evidence_selection_decisions",
        "scientific_evaluation_results",
        "scientific_evaluation_result_components",
        "scientific_evaluation_traces",
        "scientific_evaluation_publications",
        "scientific_evaluation_replay_verifications",
    ):
        op.execute(
            f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_reject_canonical_output_mutation()"
        )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_selection()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        DECLARE
          expected_snapshot BIGINT;
          actual_snapshot BIGINT;
          artifact_row RECORD;
        BEGIN
          SELECT evidence_snapshot_id INTO expected_snapshot
          FROM public.scientific_evaluation_executions WHERE id=NEW.execution_id;
          SELECT snapshot_id INTO actual_snapshot
          FROM public.scientific_evidence_snapshot_members WHERE id=NEW.snapshot_member_id;
          IF expected_snapshot IS DISTINCT FROM actual_snapshot THEN
            RAISE EXCEPTION 'selection member does not belong to execution evidence snapshot'
              USING ERRCODE='23514';
          END IF;
          SELECT * INTO artifact_row FROM public.scientific_evaluation_artifacts
          WHERE id=NEW.decision_artifact_id;
          IF artifact_row.artifact_kind<>'scientific_evidence_selection_decision'
             OR artifact_row.schema_version<>'1'
             OR artifact_row.canonicalization_version<>'wye-c14n-json-v1'
             OR artifact_row.content_digest IS DISTINCT FROM NEW.decision_digest
             OR NOT EXISTS (
               SELECT 1 FROM public.scientific_evaluation_artifact_locations l
               WHERE l.artifact_id=artifact_row.id AND l.location_status='verified'
                 AND l.verified_at IS NOT NULL
             ) THEN
            RAISE EXCEPTION 'invalid or unverified selection decision artifact'
              USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER trg_scientific_evidence_selection_validate "
        "AFTER INSERT ON scientific_evidence_selection_decisions "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION scientific_evaluation_validate_selection()"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_require_publication()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        DECLARE
          owner_execution BIGINT;
          output_xmin TEXT;
          publication_xmin TEXT;
        BEGIN
          IF TG_TABLE_NAME='scientific_evidence_selection_decisions' THEN
            owner_execution:=NEW.execution_id;
            SELECT xmin::TEXT INTO output_xmin
            FROM public.scientific_evidence_selection_decisions WHERE id=NEW.id;
          ELSIF TG_TABLE_NAME='scientific_evaluation_results' THEN
            owner_execution:=NEW.execution_id;
            SELECT xmin::TEXT INTO output_xmin
            FROM public.scientific_evaluation_results WHERE id=NEW.id;
          ELSIF TG_TABLE_NAME='scientific_evaluation_result_components' THEN
            SELECT execution_id INTO owner_execution FROM public.scientific_evaluation_results
            WHERE id=NEW.result_id;
            SELECT xmin::TEXT INTO output_xmin
            FROM public.scientific_evaluation_result_components WHERE id=NEW.id;
          ELSE
            owner_execution:=NEW.execution_id;
            SELECT xmin::TEXT INTO output_xmin
            FROM public.scientific_evaluation_traces WHERE id=NEW.id;
          END IF;
          SELECT xmin::TEXT INTO publication_xmin
          FROM public.scientific_evaluation_publications WHERE execution_id=owner_execution;
          IF publication_xmin IS NULL OR publication_xmin<>output_xmin THEN
            RAISE EXCEPTION 'canonical output requires atomic publication'
              USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    for table in (
        "scientific_evidence_selection_decisions",
        "scientific_evaluation_results",
        "scientific_evaluation_result_components",
        "scientific_evaluation_traces",
    ):
        op.execute(
            f"CREATE CONSTRAINT TRIGGER trg_{table}_require_publication "
            f"AFTER INSERT ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            "EXECUTE FUNCTION scientific_evaluation_require_publication()"
        )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_publication()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        DECLARE
          execution_row RECORD;
          attempt_row RECORD;
          result_row RECORD;
          trace_row RECORD;
          selection_row RECORD;
          bundle_row RECORD;
          expected_members INTEGER;
          actual_decisions INTEGER;
          invalid_artifacts INTEGER;
        BEGIN
          SELECT * INTO execution_row FROM public.scientific_evaluation_executions
          WHERE id=NEW.execution_id;
          SELECT * INTO attempt_row FROM public.scientific_evaluation_execution_attempts
          WHERE id=NEW.successful_attempt_id;
          SELECT * INTO result_row FROM public.scientific_evaluation_results WHERE id=NEW.result_id;
          SELECT * INTO trace_row FROM public.scientific_evaluation_traces WHERE id=NEW.trace_id;
          SELECT * INTO selection_row FROM public.scientific_evaluation_artifacts
          WHERE id=NEW.selection_manifest_artifact_id;
          SELECT * INTO bundle_row FROM public.scientific_evaluation_artifacts
          WHERE id=NEW.bundle_artifact_id;

          IF execution_row.execution_mode='REPLAY' THEN
            RAISE EXCEPTION 'REPLAY execution cannot own canonical scientific publication'
              USING ERRCODE='23514';
          END IF;
          IF execution_row.technical_status<>'completed'
             OR attempt_row.execution_id<>NEW.execution_id OR attempt_row.attempt_status<>'succeeded'
             OR result_row.execution_id<>NEW.execution_id
             OR trace_row.execution_id<>NEW.execution_id OR trace_row.result_id<>NEW.result_id
             OR NEW.published_at<attempt_row.started_at THEN
            RAISE EXCEPTION 'publication execution/result/trace/attempt relationship invalid'
              USING ERRCODE='23514';
          END IF;
          IF result_row.result_digest IS DISTINCT FROM NEW.result_digest
             OR trace_row.trace_digest IS DISTINCT FROM NEW.trace_digest
             OR trace_row.result_digest IS DISTINCT FROM NEW.result_digest
             OR trace_row.selection_digest IS DISTINCT FROM NEW.selection_digest
             OR trace_row.protocol_digest IS DISTINCT FROM execution_row.protocol_digest
             OR trace_row.evidence_snapshot_digest IS DISTINCT FROM execution_row.evidence_snapshot_digest
             OR trace_row.input_digest IS DISTINCT FROM execution_row.input_digest THEN
            RAISE EXCEPTION 'publication digest roots are inconsistent' USING ERRCODE='23514';
          END IF;
          IF selection_row.artifact_kind<>'scientific_evidence_selection_manifest'
             OR selection_row.schema_version<>'1'
             OR selection_row.content_digest IS DISTINCT FROM NEW.selection_digest
             OR bundle_row.artifact_kind<>'scientific_evaluation_publication_bundle'
             OR bundle_row.schema_version<>'1'
             OR bundle_row.content_digest IS DISTINCT FROM NEW.publication_bundle_digest THEN
            RAISE EXCEPTION 'publication manifest/bundle artifact role or digest invalid'
              USING ERRCODE='23514';
          END IF;
          SELECT member_count INTO expected_members FROM public.scientific_evidence_snapshots
          WHERE id=execution_row.evidence_snapshot_id;
          SELECT count(*) INTO actual_decisions FROM public.scientific_evidence_selection_decisions
          WHERE execution_id=NEW.execution_id;
          IF actual_decisions<>expected_members OR EXISTS (
            SELECT 1 FROM public.scientific_evidence_snapshot_members m
            WHERE m.snapshot_id=execution_row.evidence_snapshot_id AND NOT EXISTS (
              SELECT 1 FROM public.scientific_evidence_selection_decisions d
              WHERE d.execution_id=NEW.execution_id AND d.snapshot_member_id=m.id
            )
          ) THEN
            RAISE EXCEPTION 'publication requires exact evidence-selection coverage'
              USING ERRCODE='23514';
          END IF;

          SELECT count(*) INTO invalid_artifacts FROM (
            SELECT result_row.canonical_artifact_id AS id,'scientific_evaluation_result' AS kind,result_row.result_digest AS digest
            UNION ALL SELECT trace_row.canonical_artifact_id,'scientific_evaluation_trace',trace_row.trace_digest
            UNION ALL SELECT NEW.selection_manifest_artifact_id,'scientific_evidence_selection_manifest',NEW.selection_digest
            UNION ALL SELECT NEW.bundle_artifact_id,'scientific_evaluation_publication_bundle',NEW.publication_bundle_digest
            UNION ALL
            SELECT c.component_artifact_id,'scientific_evaluation_result_component',c.component_digest
            FROM public.scientific_evaluation_result_components c WHERE c.result_id=NEW.result_id
          ) roots
          JOIN public.scientific_evaluation_artifacts a ON a.id=roots.id
          WHERE a.artifact_kind<>roots.kind OR a.schema_version<>'1'
             OR a.canonicalization_version<>'wye-c14n-json-v1'
             OR a.content_digest IS DISTINCT FROM roots.digest
             OR NOT EXISTS (
               SELECT 1 FROM public.scientific_evaluation_artifact_locations l
               WHERE l.artifact_id=a.id AND l.location_status='verified' AND l.verified_at IS NOT NULL
             );
          IF invalid_artifacts<>0 THEN
            RAISE EXCEPTION 'publication contains invalid or unverified canonical artifacts'
              USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_publications_validate "
        "AFTER INSERT ON scientific_evaluation_publications DEFERRABLE INITIALLY DEFERRED "
        "FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_validate_publication()"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_replay_verification()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        DECLARE
          current_row public.scientific_evaluation_replay_verifications%ROWTYPE;
          execution_row RECORD;
          attempt_row RECORD;
          comparison_row RECORD;
          invalid_artifacts INTEGER;
        BEGIN
          SELECT * INTO current_row
          FROM public.scientific_evaluation_replay_verifications WHERE id=NEW.id;
          IF NOT FOUND THEN
            RETURN NEW;
          END IF;

          SELECT * INTO execution_row FROM public.scientific_evaluation_executions
          WHERE id=current_row.execution_id;
          SELECT * INTO attempt_row FROM public.scientific_evaluation_execution_attempts
          WHERE id=current_row.successful_attempt_id;
          SELECT * INTO comparison_row FROM public.scientific_evaluation_publications
          WHERE id=current_row.comparison_publication_id;

          IF execution_row.execution_mode<>'REPLAY'
             OR execution_row.technical_status<>'completed'
             OR execution_row.comparison_execution_id IS NULL THEN
            RAISE EXCEPTION 'replay verification requires completed REPLAY execution with comparison'
              USING ERRCODE='23514';
          END IF;
          IF comparison_row.id IS NULL
             OR comparison_row.execution_id IS DISTINCT FROM execution_row.comparison_execution_id THEN
            RAISE EXCEPTION 'replay verification comparison publication is not authoritative'
              USING ERRCODE='23514';
          END IF;
          IF attempt_row.id IS NULL
             OR attempt_row.execution_id IS DISTINCT FROM current_row.execution_id
             OR attempt_row.attempt_status<>'succeeded' THEN
            RAISE EXCEPTION 'replay verification requires succeeded attempt owned by REPLAY execution'
              USING ERRCODE='23514';
          END IF;
          IF EXISTS (
            SELECT 1 FROM public.scientific_evaluation_publications p
            WHERE p.execution_id=current_row.execution_id
          ) THEN
            RAISE EXCEPTION 'REPLAY verification forbids owned scientific publication'
              USING ERRCODE='23514';
          END IF;
          IF current_row.expected_publication_bundle_digest
                IS DISTINCT FROM comparison_row.publication_bundle_digest
             OR current_row.expected_selection_digest
                IS DISTINCT FROM comparison_row.selection_digest
             OR current_row.expected_result_digest
                IS DISTINCT FROM comparison_row.result_digest
             OR current_row.expected_trace_digest
                IS DISTINCT FROM comparison_row.trace_digest THEN
            RAISE EXCEPTION 'replay verification expected roots differ from comparison publication'
              USING ERRCODE='23514';
          END IF;

          SELECT count(*) INTO invalid_artifacts FROM (VALUES
            (current_row.verification_artifact_id,
              'scientific_evaluation_replay_verification',current_row.verification_digest),
            (current_row.recomputed_selection_artifact_id,
              'scientific_evidence_selection_manifest',current_row.recomputed_selection_digest),
            (current_row.recomputed_result_artifact_id,
              'scientific_evaluation_result',current_row.recomputed_result_digest),
            (current_row.recomputed_trace_artifact_id,
              'scientific_evaluation_trace',current_row.recomputed_trace_digest)
          ) roots(id,kind,digest)
          LEFT JOIN public.scientific_evaluation_artifacts a ON a.id=roots.id
          WHERE a.id IS NULL OR a.artifact_kind<>roots.kind OR a.schema_version<>'1'
             OR a.canonicalization_version<>'wye-c14n-json-v1'
             OR a.digest_algorithm<>'sha256'
             OR a.content_digest IS DISTINCT FROM roots.digest
             OR NOT EXISTS (
               SELECT 1 FROM public.scientific_evaluation_artifact_locations l
               WHERE l.artifact_id=a.id AND l.location_status='verified'
                 AND l.verified_at IS NOT NULL
             );
          IF invalid_artifacts<>0 THEN
            RAISE EXCEPTION 'replay verification contains invalid or unverified canonical artifacts'
              USING ERRCODE='23514';
          END IF;

          IF (current_row.verification_status='matched') IS DISTINCT FROM (
            current_row.recomputed_selection_digest=current_row.expected_selection_digest
            AND current_row.recomputed_result_digest=current_row.expected_result_digest
            AND current_row.recomputed_trace_digest=current_row.expected_trace_digest
          ) THEN
            RAISE EXCEPTION 'replay verification status does not match root equality'
              USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_replay_verifications_validate "
        "AFTER INSERT ON scientific_evaluation_replay_verifications "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION scientific_evaluation_validate_replay_verification()"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_idempotency()
        RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public AS $$
        DECLARE owner_digest BYTEA;
        BEGIN
          IF TG_OP='DELETE' THEN
            IF OLD.expires_at IS NULL OR OLD.expires_at>NOW() THEN
              RAISE EXCEPTION 'unexpired idempotency key cannot be deleted' USING ERRCODE='23514';
            END IF;
            RETURN OLD;
          END IF;
          IF TG_OP='UPDATE' AND (
            NEW.operation_type IS DISTINCT FROM OLD.operation_type
            OR NEW.request_scope IS DISTINCT FROM OLD.request_scope
            OR NEW.request_key IS DISTINCT FROM OLD.request_key
            OR NEW.expected_semantic_digest IS DISTINCT FROM OLD.expected_semantic_digest
            OR NEW.created_at IS DISTINCT FROM OLD.created_at
            OR (OLD.execution_id IS NOT NULL AND NEW.execution_id IS DISTINCT FROM OLD.execution_id)
            OR (OLD.attempt_id IS NOT NULL AND NEW.attempt_id IS DISTINCT FROM OLD.attempt_id)
            OR (OLD.publication_id IS NOT NULL AND NEW.publication_id IS DISTINCT FROM OLD.publication_id)
          ) THEN
            RAISE EXCEPTION 'established idempotency identity/owner is immutable'
              USING ERRCODE='23514';
          END IF;
          IF NEW.execution_id IS NOT NULL THEN
            SELECT semantic_execution_digest INTO owner_digest
            FROM public.scientific_evaluation_executions WHERE id=NEW.execution_id;
          ELSIF NEW.attempt_id IS NOT NULL THEN
            SELECT e.semantic_execution_digest INTO owner_digest
            FROM public.scientific_evaluation_execution_attempts a
            JOIN public.scientific_evaluation_executions e ON e.id=a.execution_id
            WHERE a.id=NEW.attempt_id;
          ELSIF NEW.publication_id IS NOT NULL THEN
            SELECT e.semantic_execution_digest INTO owner_digest
            FROM public.scientific_evaluation_publications p
            JOIN public.scientific_evaluation_executions e ON e.id=p.execution_id
            WHERE p.id=NEW.publication_id;
          END IF;
          IF owner_digest IS NOT NULL AND owner_digest IS DISTINCT FROM NEW.expected_semantic_digest THEN
            RAISE EXCEPTION 'idempotency owner semantic digest mismatch' USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER trg_scientific_evaluation_idempotency_guard "
        "BEFORE INSERT OR UPDATE OR DELETE ON scientific_evaluation_idempotency_keys "
        "FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_idempotency()"
    )


def downgrade() -> None:
    tables = ", ".join(f"'{name}'" for name in NEW_TABLES)
    op.execute(
        f"""
        DO $$
        DECLARE table_name TEXT;
        DECLARE row_found BOOLEAN;
        BEGIN
          FOREACH table_name IN ARRAY ARRAY[{tables}] LOOP
            EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I)',table_name) INTO row_found;
            IF row_found THEN
              RAISE EXCEPTION 'Cannot downgrade 0021: % contains scientific/operational history.',table_name;
            END IF;
          END LOOP;
          IF EXISTS (
            SELECT 1 FROM scientific_evaluation_governance_events
            WHERE execution_id IS NOT NULL OR related_execution_id IS NOT NULL
               OR result_id IS NOT NULL OR related_result_id IS NOT NULL
          ) THEN
            RAISE EXCEPTION 'Cannot downgrade 0021: governance references execution/result history.';
          END IF;
        END $$
        """
    )

    for name in (
        "idx_scientific_evaluation_governance_execution",
        "idx_scientific_evaluation_governance_related_execution",
        "idx_scientific_evaluation_governance_result",
        "idx_scientific_evaluation_governance_related_result",
    ):
        op.execute(f"DROP INDEX {name}")
    for name in (
        "ck_scientific_evaluation_governance_entity_type",
        "ck_scientific_evaluation_governance_event_type",
        "ck_scientific_evaluation_governance_entity_reference",
        "ck_scientific_evaluation_governance_related_reference",
        "ck_scientific_evaluation_governance_not_self",
        "fk_scientific_evaluation_governance_execution",
        "fk_scientific_evaluation_governance_related_execution",
        "fk_scientific_evaluation_governance_result",
        "fk_scientific_evaluation_governance_related_result",
    ):
        op.execute(f"ALTER TABLE scientific_evaluation_governance_events DROP CONSTRAINT {name}")
    op.execute(
        "ALTER TABLE scientific_evaluation_governance_events "
        "DROP COLUMN execution_id,DROP COLUMN related_execution_id,"
        "DROP COLUMN result_id,DROP COLUMN related_result_id"
    )
    op.execute(
        """
        ALTER TABLE scientific_evaluation_governance_events
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_type CHECK (
          entity_type IN ('protocol','protocol_version','artifact','artifact_location','evidence_snapshot')
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_event_type CHECK (
          event_type IN ('submitted_for_review','approved','published','deprecated','retired',
            'supersedes','retracts','integrity_compromised','annotation','review_disposition')
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_reference CHECK (
          num_nonnulls(protocol_id,protocol_version_id,artifact_id,artifact_location_id,snapshot_id)=1
          AND (entity_type='protocol')=(protocol_id IS NOT NULL)
          AND (entity_type='protocol_version')=(protocol_version_id IS NOT NULL)
          AND (entity_type='artifact')=(artifact_id IS NOT NULL)
          AND (entity_type='artifact_location')=(artifact_location_id IS NOT NULL)
          AND (entity_type='evidence_snapshot')=(snapshot_id IS NOT NULL)
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_related_reference CHECK (
          num_nonnulls(related_protocol_id,related_protocol_version_id,related_artifact_id,
            related_artifact_location_id,related_snapshot_id)<=1
          AND (
            num_nonnulls(related_protocol_id,related_protocol_version_id,related_artifact_id,
              related_artifact_location_id,related_snapshot_id)=0
            OR (entity_type='protocol' AND related_protocol_id IS NOT NULL)
            OR (entity_type='protocol_version' AND related_protocol_version_id IS NOT NULL)
            OR (entity_type='artifact' AND related_artifact_id IS NOT NULL)
            OR (entity_type='artifact_location' AND related_artifact_location_id IS NOT NULL)
            OR (entity_type='evidence_snapshot' AND related_snapshot_id IS NOT NULL)
          )
          AND (event_type<>'supersedes' OR num_nonnulls(related_protocol_id,
            related_protocol_version_id,related_artifact_id,related_artifact_location_id,
            related_snapshot_id)=1)
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_not_self CHECK (
          (protocol_id IS NULL OR related_protocol_id IS NULL OR protocol_id<>related_protocol_id)
          AND (protocol_version_id IS NULL OR related_protocol_version_id IS NULL OR protocol_version_id<>related_protocol_version_id)
          AND (artifact_id IS NULL OR related_artifact_id IS NULL OR artifact_id<>related_artifact_id)
          AND (artifact_location_id IS NULL OR related_artifact_location_id IS NULL OR artifact_location_id<>related_artifact_location_id)
          AND (snapshot_id IS NULL OR related_snapshot_id IS NULL OR snapshot_id<>related_snapshot_id)
          AND (predecessor_event_id IS NULL OR predecessor_event_id<>id)
        )
        """
    )
    op.execute(_governance_lineage_function(include_execution=False))

    for function in (
        "scientific_evaluation_guard_idempotency",
        "scientific_evaluation_validate_replay_verification",
        "scientific_evaluation_validate_publication",
        "scientific_evaluation_require_publication",
        "scientific_evaluation_validate_selection",
        "scientific_evaluation_reject_canonical_output_mutation",
        "scientific_evaluation_validate_attempt_consistency",
        "scientific_evaluation_guard_attempt",
        "scientific_evaluation_validate_execution",
        "scientific_evaluation_guard_execution",
    ):
        op.execute(f"DROP FUNCTION {function}() CASCADE")

    for table in reversed(NEW_TABLES):
        op.execute(f"DROP TABLE {table}")
