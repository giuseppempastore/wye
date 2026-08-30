"""Add immutable scientific evidence snapshots.

Revision ID: 0020_scientific_evidence_snapshots
Revises: 0019_scientific_evaluation_foundation
"""

from alembic import op


revision = "0020_scientific_evidence_snapshots"
down_revision = "0019_scientific_evaluation_foundation"
branch_labels = None
depends_on = None


def _governance_lineage_function(include_snapshots: bool) -> str:
    snapshot_owner = (
        "WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || NEW.snapshot_id"
        if include_snapshots
        else ""
    )
    snapshot_related = (
        "WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || NEW.related_snapshot_id"
        if include_snapshots
        else ""
    )
    row_snapshot_owner = (
        "WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || snapshot_id"
        if include_snapshots
        else ""
    )
    row_snapshot_related = (
        "WHEN 'evidence_snapshot' THEN 'evidence_snapshot:' || related_snapshot_id"
        if include_snapshots
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
              {snapshot_owner}
            END;
            new_related_key := CASE NEW.entity_type
              WHEN 'protocol' THEN 'protocol:' || NEW.related_protocol_id
              WHEN 'protocol_version' THEN 'protocol_version:' || NEW.related_protocol_version_id
              WHEN 'artifact' THEN 'artifact:' || NEW.related_artifact_id
              WHEN 'artifact_location' THEN 'artifact_location:' || NEW.related_artifact_location_id
              {snapshot_related}
            END;

            WITH RECURSIVE supersession_edges(owner_key, related_key) AS (
              SELECT
                CASE entity_type
                  WHEN 'protocol' THEN 'protocol:' || protocol_id
                  WHEN 'protocol_version' THEN 'protocol_version:' || protocol_version_id
                  WHEN 'artifact' THEN 'artifact:' || artifact_id
                  WHEN 'artifact_location' THEN 'artifact_location:' || artifact_location_id
                  {row_snapshot_owner}
                END,
                CASE entity_type
                  WHEN 'protocol' THEN 'protocol:' || related_protocol_id
                  WHEN 'protocol_version' THEN 'protocol_version:' || related_protocol_version_id
                  WHEN 'artifact' THEN 'artifact:' || related_artifact_id
                  WHEN 'artifact_location' THEN 'artifact_location:' || related_artifact_location_id
                  {row_snapshot_related}
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


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE collision TEXT;
        BEGIN
          IF to_regclass('scientific_evaluation_artifacts') IS NULL
             OR to_regclass('scientific_evaluation_artifact_locations') IS NULL
             OR to_regclass('scientific_evaluation_governance_events') IS NULL
             OR to_regclass('scientific_assessments') IS NULL
             OR to_regclass('scientific_assessment_findings') IS NULL
             OR to_regclass('scientific_ingestion_runs') IS NULL
             OR to_regclass('source_dataset_releases') IS NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0020: expected 0019/Phase 6 parent schema is incomplete.';
          END IF;

          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'scientific_evaluation_governance_events'
              AND column_name IN ('snapshot_id', 'related_snapshot_id')
          ) THEN
            RAISE EXCEPTION 'Cannot migrate 0020: governance snapshot columns already exist.';
          END IF;

          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_scientific_evaluation_governance_entity_type'
              AND conrelid = 'scientific_evaluation_governance_events'::regclass
          ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_scientific_evaluation_governance_entity_reference'
              AND conrelid = 'scientific_evaluation_governance_events'::regclass
          ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_scientific_evaluation_governance_related_reference'
              AND conrelid = 'scientific_evaluation_governance_events'::regclass
          ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_scientific_evaluation_governance_not_self'
              AND conrelid = 'scientific_evaluation_governance_events'::regclass
          ) OR to_regprocedure('scientific_evaluation_reject_governance_mutation()') IS NULL
            OR to_regprocedure('scientific_evaluation_validate_governance_lineage()') IS NULL
            OR NOT EXISTS (
              SELECT 1 FROM pg_trigger
              WHERE tgrelid = 'scientific_evaluation_governance_events'::regclass
                AND tgname = 'trg_scientific_evaluation_governance_immutable'
                AND NOT tgisinternal
            ) OR NOT EXISTS (
              SELECT 1 FROM pg_trigger
              WHERE tgrelid = 'scientific_evaluation_governance_events'::regclass
                AND tgname = 'trg_scientific_evaluation_governance_lineage'
                AND NOT tgisinternal
            ) THEN
            RAISE EXCEPTION 'Cannot migrate 0020: expected 0019 governance shape is missing.';
          END IF;

          SELECT string_agg(kind || ':' || name, ', ' ORDER BY kind, name)
          INTO collision
          FROM (
            SELECT 'relation' AS kind, c.relname AS name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema()
              AND c.relname = ANY (ARRAY[
                'scientific_evidence_snapshots',
                'scientific_evidence_snapshot_members',
                'uq_scientific_evidence_snapshots_identity',
                'idx_scientific_evidence_snapshots_status_cutoff',
                'idx_scientific_evidence_snapshots_query_artifact',
                'idx_scientific_evidence_snapshots_manifest_artifact',
                'uq_scientific_evidence_snapshot_members_finding',
                'uq_scientific_evidence_snapshot_members_assessment',
                'idx_scientific_evidence_snapshot_members_assessment',
                'idx_scientific_evidence_snapshot_members_ingestion',
                'idx_scientific_evidence_snapshot_members_release',
                'idx_scientific_evidence_snapshot_members_payload',
                'idx_scientific_evidence_snapshot_members_order',
                'idx_scientific_evaluation_governance_snapshot',
                'idx_scientific_evaluation_governance_related_snapshot'
              ])
            UNION ALL
            SELECT 'constraint', con.conname
            FROM pg_constraint con
            JOIN pg_class c ON c.oid = con.conrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema()
              AND con.conname = ANY (ARRAY[
                'pk_scientific_evidence_snapshots',
                'uq_scientific_evidence_snapshots_key',
                'fk_scientific_evidence_snapshots_query_artifact',
                'fk_scientific_evidence_snapshots_manifest_artifact',
                'ck_scientific_evidence_snapshots_policy_key',
                'ck_scientific_evidence_snapshots_policy_version',
                'ck_scientific_evidence_snapshots_time',
                'ck_scientific_evidence_snapshots_canonicalization',
                'ck_scientific_evidence_snapshots_digest_algorithm',
                'ck_scientific_evidence_snapshots_digest_length',
                'ck_scientific_evidence_snapshots_member_count',
                'ck_scientific_evidence_snapshots_status',
                'ck_scientific_evidence_snapshots_state',
                'ck_scientific_evidence_snapshots_actors',
                'pk_scientific_evidence_snapshot_members',
                'fk_scientific_evidence_snapshot_members_snapshot',
                'fk_scientific_evidence_snapshot_members_finding',
                'fk_scientific_evidence_snapshot_members_assessment',
                'fk_scientific_evidence_snapshot_members_ingestion',
                'fk_scientific_evidence_snapshot_members_release',
                'fk_scientific_evidence_snapshot_members_payload',
                'uq_scientific_evidence_snapshot_members_ordinal',
                'uq_scientific_evidence_snapshot_members_identity',
                'ck_scientific_evidence_snapshot_members_kind',
                'ck_scientific_evidence_snapshot_members_shape',
                'ck_scientific_evidence_snapshot_members_identity_digest',
                'ck_scientific_evidence_snapshot_members_semantic_digest',
                'ck_scientific_evidence_snapshot_members_ordinal',
                'ck_scientific_evidence_snapshot_members_status',
                'fk_scientific_evaluation_governance_snapshot',
                'fk_scientific_evaluation_governance_related_snapshot'
              ])
            UNION ALL
            SELECT 'function', p.proname
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = current_schema()
              AND p.proname = ANY (ARRAY[
                'scientific_evaluation_guard_snapshot',
                'scientific_evaluation_validate_snapshot',
                'scientific_evaluation_guard_snapshot_member',
                'scientific_evaluation_validate_snapshot_member'
              ])
            UNION ALL
            SELECT 'trigger', t.tgname
            FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema()
              AND NOT t.tgisinternal
              AND t.tgname = ANY (ARRAY[
                'trg_scientific_evidence_snapshots_guard',
                'trg_scientific_evidence_snapshots_validate',
                'trg_scientific_evidence_snapshot_members_guard',
                'trg_scientific_evidence_snapshot_members_validate'
              ])
          ) collisions;

          IF collision IS NOT NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0020: incompatible snapshot object collision(s): %', collision;
          END IF;
        END $$
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evidence_snapshots (
          id BIGSERIAL,
          snapshot_key UUID NOT NULL,
          snapshot_policy_key VARCHAR(100) NOT NULL,
          snapshot_policy_version VARCHAR(50) NOT NULL,
          as_of TIMESTAMPTZ NOT NULL,
          evidence_cutoff TIMESTAMPTZ NOT NULL,
          query_definition_artifact_id BIGINT NOT NULL,
          canonicalization_version VARCHAR(50) NOT NULL,
          digest_algorithm VARCHAR(20) NOT NULL,
          manifest_artifact_id BIGINT,
          snapshot_digest BYTEA,
          member_count BIGINT,
          status VARCHAR(20) NOT NULL DEFAULT 'building',
          created_by VARCHAR(255) NOT NULL,
          sealed_by VARCHAR(255),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          sealed_at TIMESTAMPTZ,
          CONSTRAINT pk_scientific_evidence_snapshots PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evidence_snapshots_key UNIQUE (snapshot_key),
          CONSTRAINT fk_scientific_evidence_snapshots_query_artifact
            FOREIGN KEY (query_definition_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_snapshots_manifest_artifact
            FOREIGN KEY (manifest_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evidence_snapshots_policy_key CHECK (
            snapshot_policy_key ~ '^[a-z][a-z0-9]*(_[a-z0-9]+)*$'
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_policy_version CHECK (
            btrim(snapshot_policy_version) <> ''
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_time CHECK (
            evidence_cutoff <= as_of
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_canonicalization CHECK (
            canonicalization_version = 'wye-c14n-json-v1'
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_digest_algorithm CHECK (
            digest_algorithm = 'sha256'
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_digest_length CHECK (
            snapshot_digest IS NULL OR octet_length(snapshot_digest) = 32
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_member_count CHECK (
            member_count IS NULL OR member_count >= 0
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_status CHECK (
            status IN ('building', 'sealed')
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_state CHECK (
            (
              status = 'building'
              AND manifest_artifact_id IS NULL
              AND snapshot_digest IS NULL
              AND member_count IS NULL
              AND sealed_by IS NULL
              AND sealed_at IS NULL
            ) OR (
              status = 'sealed'
              AND manifest_artifact_id IS NOT NULL
              AND snapshot_digest IS NOT NULL
              AND member_count IS NOT NULL
              AND sealed_by IS NOT NULL
              AND sealed_at IS NOT NULL
              AND sealed_at >= created_at
            )
          ),
          CONSTRAINT ck_scientific_evidence_snapshots_actors CHECK (
            btrim(created_by) <> '' AND (sealed_by IS NULL OR btrim(sealed_by) <> '')
          )
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_scientific_evidence_snapshots_identity "
        "ON scientific_evidence_snapshots "
        "(canonicalization_version, digest_algorithm, snapshot_digest) "
        "WHERE status='sealed'"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshots_status_cutoff "
        "ON scientific_evidence_snapshots (status, as_of, evidence_cutoff, id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshots_query_artifact "
        "ON scientific_evidence_snapshots (query_definition_artifact_id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshots_manifest_artifact "
        "ON scientific_evidence_snapshots (manifest_artifact_id) "
        "WHERE manifest_artifact_id IS NOT NULL"
    )

    op.execute(
        """
        CREATE TABLE scientific_evidence_snapshot_members (
          id BIGSERIAL,
          snapshot_id BIGINT NOT NULL,
          member_kind VARCHAR(20) NOT NULL,
          finding_id BIGINT,
          assessment_id BIGINT NOT NULL,
          ingestion_run_id BIGINT NOT NULL,
          source_dataset_release_id BIGINT NOT NULL,
          member_identity_digest BYTEA NOT NULL,
          member_payload_artifact_id BIGINT NOT NULL,
          member_semantic_digest BYTEA NOT NULL,
          membership_ordinal INTEGER NOT NULL,
          status_as_of VARCHAR(30) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evidence_snapshot_members PRIMARY KEY (id),
          CONSTRAINT fk_scientific_evidence_snapshot_members_snapshot
            FOREIGN KEY (snapshot_id) REFERENCES scientific_evidence_snapshots(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_snapshot_members_finding
            FOREIGN KEY (finding_id) REFERENCES scientific_assessment_findings(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_snapshot_members_assessment
            FOREIGN KEY (assessment_id) REFERENCES scientific_assessments(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_snapshot_members_ingestion
            FOREIGN KEY (ingestion_run_id) REFERENCES scientific_ingestion_runs(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_snapshot_members_release
            FOREIGN KEY (source_dataset_release_id) REFERENCES source_dataset_releases(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evidence_snapshot_members_payload
            FOREIGN KEY (member_payload_artifact_id)
            REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT uq_scientific_evidence_snapshot_members_ordinal
            UNIQUE (snapshot_id, membership_ordinal),
          CONSTRAINT uq_scientific_evidence_snapshot_members_identity
            UNIQUE (snapshot_id, member_identity_digest),
          CONSTRAINT ck_scientific_evidence_snapshot_members_kind CHECK (
            member_kind IN ('finding', 'assessment')
          ),
          CONSTRAINT ck_scientific_evidence_snapshot_members_shape CHECK (
            (member_kind = 'finding' AND finding_id IS NOT NULL)
            OR (member_kind = 'assessment' AND finding_id IS NULL)
          ),
          CONSTRAINT ck_scientific_evidence_snapshot_members_identity_digest CHECK (
            octet_length(member_identity_digest) = 32
          ),
          CONSTRAINT ck_scientific_evidence_snapshot_members_semantic_digest CHECK (
            octet_length(member_semantic_digest) = 32
          ),
          CONSTRAINT ck_scientific_evidence_snapshot_members_ordinal CHECK (
            membership_ordinal >= 0
          ),
          CONSTRAINT ck_scientific_evidence_snapshot_members_status CHECK (
            btrim(status_as_of) <> ''
          )
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_scientific_evidence_snapshot_members_finding "
        "ON scientific_evidence_snapshot_members (snapshot_id, finding_id) "
        "WHERE finding_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_scientific_evidence_snapshot_members_assessment "
        "ON scientific_evidence_snapshot_members (snapshot_id, assessment_id) "
        "WHERE member_kind='assessment'"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshot_members_assessment "
        "ON scientific_evidence_snapshot_members (assessment_id, snapshot_id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshot_members_ingestion "
        "ON scientific_evidence_snapshot_members (ingestion_run_id, snapshot_id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshot_members_release "
        "ON scientific_evidence_snapshot_members (source_dataset_release_id, snapshot_id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshot_members_payload "
        "ON scientific_evidence_snapshot_members (member_payload_artifact_id)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evidence_snapshot_members_order "
        "ON scientific_evidence_snapshot_members "
        "(snapshot_id, member_kind, member_identity_digest, member_semantic_digest)"
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_snapshot()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            IF OLD.status = 'sealed' THEN
              RAISE EXCEPTION 'sealed scientific evidence snapshots are historically immutable'
                USING ERRCODE = '55000';
            END IF;
            RETURN OLD;
          END IF;

          IF ROW(
            NEW.snapshot_key, NEW.snapshot_policy_key, NEW.snapshot_policy_version,
            NEW.as_of, NEW.evidence_cutoff, NEW.query_definition_artifact_id,
            NEW.canonicalization_version, NEW.digest_algorithm,
            NEW.created_by, NEW.created_at
          ) IS DISTINCT FROM ROW(
            OLD.snapshot_key, OLD.snapshot_policy_key, OLD.snapshot_policy_version,
            OLD.as_of, OLD.evidence_cutoff, OLD.query_definition_artifact_id,
            OLD.canonicalization_version, OLD.digest_algorithm,
            OLD.created_by, OLD.created_at
          ) THEN
            RAISE EXCEPTION 'scientific evidence snapshot construction identity is immutable'
              USING ERRCODE = '55000';
          END IF;

          IF OLD.status = 'sealed' AND NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'sealed scientific evidence snapshots are historically immutable'
              USING ERRCODE = '55000';
          END IF;

          IF NEW.status IS DISTINCT FROM OLD.status
             AND NOT (OLD.status = 'building' AND NEW.status = 'sealed') THEN
            RAISE EXCEPTION 'invalid scientific evidence snapshot transition: % -> %',
              OLD.status, NEW.status USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_scientific_evidence_snapshots_guard
        BEFORE UPDATE OR DELETE ON scientific_evidence_snapshots
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_snapshot()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_snapshot_member()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE parent_id BIGINT;
        DECLARE parent_status TEXT;
        BEGIN
          parent_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.snapshot_id ELSE NEW.snapshot_id END;
          IF TG_OP = 'UPDATE' AND NEW.snapshot_id IS DISTINCT FROM OLD.snapshot_id THEN
            RAISE EXCEPTION 'snapshot membership cannot move between snapshots'
              USING ERRCODE = '55000';
          END IF;

          SELECT status INTO parent_status
          FROM public.scientific_evidence_snapshots
          WHERE id = parent_id
          FOR SHARE;
          IF parent_status IS NULL THEN
            RAISE EXCEPTION 'snapshot membership parent does not exist'
              USING ERRCODE = '23503';
          END IF;
          IF parent_status <> 'building' THEN
            RAISE EXCEPTION 'sealed scientific evidence snapshot membership is immutable'
              USING ERRCODE = '55000';
          END IF;
          RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_scientific_evidence_snapshot_members_guard
        BEFORE INSERT OR UPDATE OR DELETE ON scientific_evidence_snapshot_members
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_snapshot_member()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_snapshot_member()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE artifact_row RECORD;
        DECLARE assessment_row RECORD;
        DECLARE run_release_id BIGINT;
        DECLARE finding_assessment_id BIGINT;
        BEGIN
          SELECT artifact_kind, schema_version, canonicalization_version,
                 digest_algorithm, content_digest
          INTO artifact_row
          FROM public.scientific_evaluation_artifacts
          WHERE id = NEW.member_payload_artifact_id;
          IF NOT FOUND
             OR artifact_row.artifact_kind <> 'scientific_evidence_snapshot_member'
             OR artifact_row.schema_version <> '1'
             OR artifact_row.canonicalization_version <> 'wye-c14n-json-v1'
             OR artifact_row.digest_algorithm <> 'sha256'
             OR artifact_row.content_digest IS DISTINCT FROM NEW.member_semantic_digest THEN
            RAISE EXCEPTION 'snapshot member payload artifact identity is incompatible'
              USING ERRCODE = '23514';
          END IF;

          SELECT ingestion_run_id, source_dataset_release_id
          INTO assessment_row
          FROM public.scientific_assessments
          WHERE id = NEW.assessment_id;
          IF NOT FOUND
             OR assessment_row.ingestion_run_id IS DISTINCT FROM NEW.ingestion_run_id
             OR assessment_row.source_dataset_release_id IS DISTINCT FROM NEW.source_dataset_release_id THEN
            RAISE EXCEPTION 'snapshot member assessment provenance is inconsistent'
              USING ERRCODE = '23514';
          END IF;

          SELECT release_id INTO run_release_id
          FROM public.scientific_ingestion_runs
          WHERE id = NEW.ingestion_run_id;
          IF run_release_id IS DISTINCT FROM NEW.source_dataset_release_id THEN
            RAISE EXCEPTION 'snapshot member ingestion release is inconsistent'
              USING ERRCODE = '23514';
          END IF;

          IF NEW.member_kind = 'finding' THEN
            SELECT assessment_id INTO finding_assessment_id
            FROM public.scientific_assessment_findings
            WHERE id = NEW.finding_id;
            IF finding_assessment_id IS DISTINCT FROM NEW.assessment_id THEN
              RAISE EXCEPTION 'snapshot finding does not belong to its assessment context'
                USING ERRCODE = '23514';
            END IF;
          END IF;

          IF NEW.member_kind = 'assessment' AND EXISTS (
            SELECT 1 FROM public.scientific_evidence_snapshot_members m
            WHERE m.snapshot_id = NEW.snapshot_id
              AND m.assessment_id = NEW.assessment_id
              AND m.member_kind = 'finding'
              AND m.id <> NEW.id
          ) THEN
            RAISE EXCEPTION 'assessment-only and finding members cannot coexist in snapshot policy v1'
              USING ERRCODE = '23514';
          END IF;
          IF NEW.member_kind = 'finding' AND EXISTS (
            SELECT 1 FROM public.scientific_evidence_snapshot_members m
            WHERE m.snapshot_id = NEW.snapshot_id
              AND m.assessment_id = NEW.assessment_id
              AND m.member_kind = 'assessment'
              AND m.id <> NEW.id
          ) THEN
            RAISE EXCEPTION 'assessment-only and finding members cannot coexist in snapshot policy v1'
              USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_scientific_evidence_snapshot_members_validate
        AFTER INSERT OR UPDATE ON scientific_evidence_snapshot_members
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_validate_snapshot_member()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_snapshot()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE query_row RECORD;
        DECLARE manifest_row RECORD;
        DECLARE actual_count BIGINT;
        DECLARE invalid_order_count BIGINT;
        BEGIN
          SELECT artifact_kind, schema_version, canonicalization_version,
                 digest_algorithm, content_digest
          INTO query_row
          FROM public.scientific_evaluation_artifacts
          WHERE id = NEW.query_definition_artifact_id;
          IF NOT FOUND
             OR query_row.artifact_kind <> 'scientific_evidence_snapshot_query'
             OR query_row.schema_version <> '1'
             OR query_row.canonicalization_version <> NEW.canonicalization_version
             OR query_row.digest_algorithm <> NEW.digest_algorithm THEN
            RAISE EXCEPTION 'snapshot query artifact identity is incompatible'
              USING ERRCODE = '23514';
          END IF;

          IF NEW.status = 'building' THEN
            RETURN NEW;
          END IF;

          SELECT artifact_kind, schema_version, canonicalization_version,
                 digest_algorithm, content_digest
          INTO manifest_row
          FROM public.scientific_evaluation_artifacts
          WHERE id = NEW.manifest_artifact_id;
          IF NOT FOUND
             OR manifest_row.artifact_kind <> 'scientific_evidence_snapshot_manifest'
             OR manifest_row.schema_version <> '1'
             OR manifest_row.canonicalization_version <> NEW.canonicalization_version
             OR manifest_row.digest_algorithm <> NEW.digest_algorithm
             OR manifest_row.content_digest IS DISTINCT FROM NEW.snapshot_digest THEN
            RAISE EXCEPTION 'sealed snapshot manifest identity is incompatible'
              USING ERRCODE = '23514';
          END IF;

          IF NOT EXISTS (
            SELECT 1 FROM public.scientific_evaluation_artifact_locations l
            WHERE l.artifact_id = NEW.query_definition_artifact_id
              AND l.location_status = 'verified' AND l.verified_at IS NOT NULL
          ) OR NOT EXISTS (
            SELECT 1 FROM public.scientific_evaluation_artifact_locations l
            WHERE l.artifact_id = NEW.manifest_artifact_id
              AND l.location_status = 'verified' AND l.verified_at IS NOT NULL
          ) THEN
            RAISE EXCEPTION 'sealed snapshot query and manifest require verified locations'
              USING ERRCODE = '23514';
          END IF;

          SELECT count(*) INTO actual_count
          FROM public.scientific_evidence_snapshot_members m
          WHERE m.snapshot_id = NEW.id;
          IF actual_count IS DISTINCT FROM NEW.member_count THEN
            RAISE EXCEPTION 'sealed snapshot member_count does not match membership'
              USING ERRCODE = '23514';
          END IF;

          IF EXISTS (
            SELECT 1
            FROM public.scientific_evidence_snapshot_members m
            WHERE m.snapshot_id = NEW.id
              AND NOT EXISTS (
                SELECT 1 FROM public.scientific_evaluation_artifact_locations l
                WHERE l.artifact_id = m.member_payload_artifact_id
                  AND l.location_status = 'verified' AND l.verified_at IS NOT NULL
              )
          ) THEN
            RAISE EXCEPTION 'sealed snapshot members require verified artifact locations'
              USING ERRCODE = '23514';
          END IF;

          SELECT count(*) INTO invalid_order_count
          FROM (
            SELECT membership_ordinal,
                   row_number() OVER (
                     ORDER BY member_kind COLLATE "C",
                              member_identity_digest,
                              member_semantic_digest
                   ) - 1 AS expected_ordinal
            FROM public.scientific_evidence_snapshot_members
            WHERE snapshot_id = NEW.id
          ) ordered_members
          WHERE membership_ordinal <> expected_ordinal;
          IF invalid_order_count <> 0 THEN
            RAISE EXCEPTION 'sealed snapshot membership ordinal is not canonical'
              USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_scientific_evidence_snapshots_validate
        AFTER INSERT OR UPDATE ON scientific_evidence_snapshots
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_validate_snapshot()
        """
    )

    op.execute(
        "ALTER TABLE scientific_evaluation_governance_events "
        "ADD COLUMN snapshot_id BIGINT, ADD COLUMN related_snapshot_id BIGINT"
    )
    op.execute(
        "ALTER TABLE scientific_evaluation_governance_events ADD CONSTRAINT "
        "fk_scientific_evaluation_governance_snapshot FOREIGN KEY (snapshot_id) "
        "REFERENCES scientific_evidence_snapshots(id) ON DELETE RESTRICT"
    )
    op.execute(
        "ALTER TABLE scientific_evaluation_governance_events ADD CONSTRAINT "
        "fk_scientific_evaluation_governance_related_snapshot "
        "FOREIGN KEY (related_snapshot_id) REFERENCES scientific_evidence_snapshots(id) "
        "ON DELETE RESTRICT"
    )
    for constraint in (
        "ck_scientific_evaluation_governance_entity_type",
        "ck_scientific_evaluation_governance_entity_reference",
        "ck_scientific_evaluation_governance_related_reference",
        "ck_scientific_evaluation_governance_not_self",
    ):
        op.execute(
            f"ALTER TABLE scientific_evaluation_governance_events DROP CONSTRAINT {constraint}"
        )
    op.execute(
        """
        ALTER TABLE scientific_evaluation_governance_events
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_type CHECK (
          entity_type IN (
            'protocol', 'protocol_version', 'artifact', 'artifact_location',
            'evidence_snapshot'
          )
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_reference CHECK (
          num_nonnulls(
            protocol_id, protocol_version_id, artifact_id, artifact_location_id, snapshot_id
          ) = 1
          AND (entity_type = 'protocol') = (protocol_id IS NOT NULL)
          AND (entity_type = 'protocol_version') = (protocol_version_id IS NOT NULL)
          AND (entity_type = 'artifact') = (artifact_id IS NOT NULL)
          AND (entity_type = 'artifact_location') = (artifact_location_id IS NOT NULL)
          AND (entity_type = 'evidence_snapshot') = (snapshot_id IS NOT NULL)
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_related_reference CHECK (
          num_nonnulls(
            related_protocol_id, related_protocol_version_id,
            related_artifact_id, related_artifact_location_id, related_snapshot_id
          ) <= 1
          AND (
            num_nonnulls(
              related_protocol_id, related_protocol_version_id,
              related_artifact_id, related_artifact_location_id, related_snapshot_id
            ) = 0
            OR (entity_type = 'protocol' AND related_protocol_id IS NOT NULL)
            OR (entity_type = 'protocol_version' AND related_protocol_version_id IS NOT NULL)
            OR (entity_type = 'artifact' AND related_artifact_id IS NOT NULL)
            OR (entity_type = 'artifact_location' AND related_artifact_location_id IS NOT NULL)
            OR (entity_type = 'evidence_snapshot' AND related_snapshot_id IS NOT NULL)
          )
          AND (
            event_type <> 'supersedes'
            OR num_nonnulls(
              related_protocol_id, related_protocol_version_id,
              related_artifact_id, related_artifact_location_id, related_snapshot_id
            ) = 1
          )
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_not_self CHECK (
          (protocol_id IS NULL OR related_protocol_id IS NULL OR protocol_id <> related_protocol_id)
          AND (
            protocol_version_id IS NULL OR related_protocol_version_id IS NULL
            OR protocol_version_id <> related_protocol_version_id
          )
          AND (artifact_id IS NULL OR related_artifact_id IS NULL OR artifact_id <> related_artifact_id)
          AND (
            artifact_location_id IS NULL OR related_artifact_location_id IS NULL
            OR artifact_location_id <> related_artifact_location_id
          )
          AND (snapshot_id IS NULL OR related_snapshot_id IS NULL OR snapshot_id <> related_snapshot_id)
          AND (predecessor_event_id IS NULL OR predecessor_event_id <> id)
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_scientific_evaluation_governance_snapshot "
        "ON scientific_evaluation_governance_events (snapshot_id, effective_at, id) "
        "WHERE snapshot_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evaluation_governance_related_snapshot "
        "ON scientific_evaluation_governance_events (related_snapshot_id) "
        "WHERE related_snapshot_id IS NOT NULL"
    )
    op.execute(_governance_lineage_function(include_snapshots=True))


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM scientific_evidence_snapshot_members)
             OR EXISTS (SELECT 1 FROM scientific_evidence_snapshots)
             OR EXISTS (
               SELECT 1 FROM scientific_evaluation_governance_events
               WHERE snapshot_id IS NOT NULL OR related_snapshot_id IS NOT NULL
             ) THEN
            RAISE EXCEPTION 'Cannot downgrade 0020: scientific evidence snapshot history is not representable at 0019.';
          END IF;
        END $$
        """
    )

    op.execute("DROP INDEX idx_scientific_evaluation_governance_related_snapshot")
    op.execute("DROP INDEX idx_scientific_evaluation_governance_snapshot")
    for constraint in (
        "ck_scientific_evaluation_governance_entity_type",
        "ck_scientific_evaluation_governance_entity_reference",
        "ck_scientific_evaluation_governance_related_reference",
        "ck_scientific_evaluation_governance_not_self",
        "fk_scientific_evaluation_governance_related_snapshot",
        "fk_scientific_evaluation_governance_snapshot",
    ):
        op.execute(
            f"ALTER TABLE scientific_evaluation_governance_events DROP CONSTRAINT {constraint}"
        )
    op.execute(
        """
        ALTER TABLE scientific_evaluation_governance_events
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_type CHECK (
          entity_type IN ('protocol', 'protocol_version', 'artifact', 'artifact_location')
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_entity_reference CHECK (
          num_nonnulls(protocol_id, protocol_version_id, artifact_id, artifact_location_id) = 1
          AND (entity_type = 'protocol') = (protocol_id IS NOT NULL)
          AND (entity_type = 'protocol_version') = (protocol_version_id IS NOT NULL)
          AND (entity_type = 'artifact') = (artifact_id IS NOT NULL)
          AND (entity_type = 'artifact_location') = (artifact_location_id IS NOT NULL)
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_related_reference CHECK (
          num_nonnulls(
            related_protocol_id, related_protocol_version_id,
            related_artifact_id, related_artifact_location_id
          ) <= 1
          AND (
            num_nonnulls(
              related_protocol_id, related_protocol_version_id,
              related_artifact_id, related_artifact_location_id
            ) = 0
            OR (entity_type = 'protocol' AND related_protocol_id IS NOT NULL)
            OR (entity_type = 'protocol_version' AND related_protocol_version_id IS NOT NULL)
            OR (entity_type = 'artifact' AND related_artifact_id IS NOT NULL)
            OR (entity_type = 'artifact_location' AND related_artifact_location_id IS NOT NULL)
          )
          AND (
            event_type <> 'supersedes'
            OR num_nonnulls(
              related_protocol_id, related_protocol_version_id,
              related_artifact_id, related_artifact_location_id
            ) = 1
          )
        ),
        ADD CONSTRAINT ck_scientific_evaluation_governance_not_self CHECK (
          (protocol_id IS NULL OR related_protocol_id IS NULL OR protocol_id <> related_protocol_id)
          AND (
            protocol_version_id IS NULL OR related_protocol_version_id IS NULL
            OR protocol_version_id <> related_protocol_version_id
          )
          AND (artifact_id IS NULL OR related_artifact_id IS NULL OR artifact_id <> related_artifact_id)
          AND (
            artifact_location_id IS NULL OR related_artifact_location_id IS NULL
            OR artifact_location_id <> related_artifact_location_id
          )
          AND (predecessor_event_id IS NULL OR predecessor_event_id <> id)
        )
        """
    )
    op.execute(
        "ALTER TABLE scientific_evaluation_governance_events "
        "DROP COLUMN related_snapshot_id, DROP COLUMN snapshot_id"
    )
    op.execute(_governance_lineage_function(include_snapshots=False))

    op.execute("DROP TABLE scientific_evidence_snapshot_members")
    op.execute("DROP TABLE scientific_evidence_snapshots")
    op.execute("DROP FUNCTION scientific_evaluation_validate_snapshot_member()")
    op.execute("DROP FUNCTION scientific_evaluation_guard_snapshot_member()")
    op.execute("DROP FUNCTION scientific_evaluation_validate_snapshot()")
    op.execute("DROP FUNCTION scientific_evaluation_guard_snapshot()")
