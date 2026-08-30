"""Add the scientific evaluation persistence foundation.

Revision ID: 0019_scientific_evaluation_foundation
Revises: 0018_scientific_batch_recovery
"""

from alembic import op


revision = "0019_scientific_evaluation_foundation"
down_revision = "0018_scientific_batch_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic's default revision column is VARCHAR(32), while the frozen,
    # descriptive revision identifier is longer. Widening is metadata-only and
    # must happen inside this transactional migration before Alembic records it.
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")
    op.execute(
        """
        DO $$
        DECLARE collision TEXT;
        BEGIN
          SELECT string_agg(kind || ':' || name, ', ' ORDER BY kind, name)
          INTO collision
          FROM (
            SELECT 'relation' AS kind, c.relname AS name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema()
              AND c.relname = ANY (ARRAY[
                'scientific_evaluation_artifacts',
                'scientific_evaluation_artifact_locations',
                'scientific_evaluation_protocols',
                'scientific_evaluation_protocol_versions',
                'scientific_evaluation_governance_events',
                'uq_scientific_evaluation_artifact_object_location',
                'uq_scientific_evaluation_protocol_version_digest',
                'idx_scientific_evaluation_artifacts_kind_created',
                'idx_scientific_evaluation_artifact_locations_artifact_status',
                'idx_scientific_evaluation_artifact_locations_storage_object',
                'idx_scientific_evaluation_protocol_versions_lifecycle',
                'idx_scientific_evaluation_governance_protocol',
                'idx_scientific_evaluation_governance_protocol_version',
                'idx_scientific_evaluation_governance_artifact',
                'idx_scientific_evaluation_governance_artifact_location',
                'idx_scientific_evaluation_governance_predecessor',
                'idx_scientific_evaluation_governance_related_protocol',
                'idx_scientific_evaluation_governance_related_protocol_version',
                'idx_scientific_evaluation_governance_related_artifact',
                'idx_scientific_evaluation_governance_related_artifact_location'
              ])
            UNION ALL
            SELECT 'constraint', con.conname
            FROM pg_constraint con
            JOIN pg_class c ON c.oid = con.conrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema()
              AND con.conname = ANY (ARRAY[
                'pk_scientific_evaluation_artifacts',
                'uq_scientific_evaluation_artifacts_identity',
                'ck_scientific_evaluation_artifacts_kind',
                'ck_scientific_evaluation_artifacts_schema_version',
                'ck_scientific_evaluation_artifacts_canonicalization',
                'ck_scientific_evaluation_artifacts_digest_algorithm',
                'ck_scientific_evaluation_artifacts_digest_length',
                'ck_scientific_evaluation_artifacts_content_length',
                'ck_scientific_evaluation_artifacts_content_type',
                'ck_scientific_evaluation_artifacts_json_payload',
                'pk_scientific_evaluation_artifact_locations',
                'uq_scientific_evaluation_artifact_locations_key',
                'fk_scientific_evaluation_artifact_locations_artifact',
                'fk_scientific_evaluation_artifact_locations_storage_object',
                'ck_scientific_evaluation_artifact_locations_mode',
                'ck_scientific_evaluation_artifact_locations_status',
                'ck_scientific_evaluation_artifact_locations_storage',
                'ck_scientific_evaluation_artifact_locations_verified',
                'pk_scientific_evaluation_protocols',
                'uq_scientific_evaluation_protocols_key',
                'ck_scientific_evaluation_protocols_key',
                'ck_scientific_evaluation_protocols_required',
                'pk_scientific_evaluation_protocol_versions',
                'fk_scientific_evaluation_protocol_versions_protocol',
                'fk_scientific_evaluation_protocol_versions_artifact',
                'fk_scientific_evaluation_protocol_versions_review_artifact',
                'uq_scientific_evaluation_protocol_versions_semver',
                'ck_scientific_evaluation_protocol_versions_semver',
                'ck_scientific_evaluation_protocol_versions_status',
                'ck_scientific_evaluation_protocol_versions_digest_length',
                'ck_scientific_evaluation_protocol_versions_artifact_digest',
                'ck_scientific_evaluation_protocol_versions_approval',
                'ck_scientific_evaluation_protocol_versions_publication',
                'ck_scientific_evaluation_protocol_versions_retirement',
                'ck_scientific_evaluation_protocol_versions_created_by',
                'pk_scientific_evaluation_governance_events',
                'uq_scientific_evaluation_governance_events_key',
                'fk_scientific_evaluation_governance_protocol',
                'fk_scientific_evaluation_governance_protocol_version',
                'fk_scientific_evaluation_governance_artifact',
                'fk_scientific_evaluation_governance_artifact_location',
                'fk_scientific_evaluation_governance_predecessor',
                'fk_scientific_evaluation_governance_related_protocol',
                'fk_scientific_evaluation_governance_related_protocol_version',
                'fk_scientific_evaluation_governance_related_artifact',
                'fk_scientific_evaluation_governance_related_artifact_location',
                'fk_scientific_evaluation_governance_rationale_artifact',
                'ck_scientific_evaluation_governance_entity_type',
                'ck_scientific_evaluation_governance_event_type',
                'ck_scientific_evaluation_governance_entity_reference',
                'ck_scientific_evaluation_governance_related_reference',
                'ck_scientific_evaluation_governance_not_self',
                'ck_scientific_evaluation_governance_required',
                'ck_scientific_evaluation_governance_metadata'
              ])
            UNION ALL
            SELECT 'function', p.proname
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = current_schema()
              AND p.proname = ANY (ARRAY[
                'scientific_evaluation_reject_artifact_mutation',
                'scientific_evaluation_guard_artifact_location',
                 'scientific_evaluation_require_location_event',
                 'scientific_evaluation_guard_protocol',
                 'scientific_evaluation_require_protocol_event',
                 'scientific_evaluation_guard_protocol_version',
                'scientific_evaluation_validate_protocol_version',
                'scientific_evaluation_require_lifecycle_event',
                'scientific_evaluation_reject_governance_mutation',
                'scientific_evaluation_validate_governance_lineage'
              ])
            UNION ALL
            SELECT 'trigger', t.tgname
            FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema()
              AND NOT t.tgisinternal
              AND t.tgname = ANY (ARRAY[
                'trg_scientific_evaluation_artifacts_immutable',
                'trg_scientific_evaluation_artifact_locations_guard',
                 'trg_scientific_evaluation_artifact_locations_event',
                 'trg_scientific_evaluation_protocols_guard',
                 'trg_scientific_evaluation_protocols_event',
                 'trg_scientific_evaluation_protocol_versions_guard',
                'trg_scientific_evaluation_protocol_versions_validate',
                'trg_scientific_evaluation_protocol_versions_event',
                'trg_scientific_evaluation_governance_immutable',
                'trg_scientific_evaluation_governance_lineage'
              ])
          ) collisions;

          IF collision IS NOT NULL THEN
            RAISE EXCEPTION 'Cannot migrate 0019: incompatible foundation object collision(s): %', collision;
          END IF;
        END $$
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_artifacts (
          id BIGSERIAL,
          artifact_kind VARCHAR(80) NOT NULL,
          schema_version VARCHAR(50) NOT NULL,
          canonicalization_version VARCHAR(50) NOT NULL,
          digest_algorithm VARCHAR(20) NOT NULL,
          content_digest BYTEA NOT NULL,
          content_length BIGINT NOT NULL,
          content_type VARCHAR(100) NOT NULL,
          json_payload JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          verified_at TIMESTAMPTZ NOT NULL,
          CONSTRAINT pk_scientific_evaluation_artifacts PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_artifacts_identity UNIQUE (
            canonicalization_version, digest_algorithm, content_digest
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_kind CHECK (
            artifact_kind ~ '^[a-z][a-z0-9]*(_[a-z0-9]+)*$'
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_schema_version CHECK (
            btrim(schema_version) <> ''
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_canonicalization CHECK (
            canonicalization_version = 'wye-c14n-json-v1'
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_digest_algorithm CHECK (
            digest_algorithm = 'sha256'
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_digest_length CHECK (
            octet_length(content_digest) = 32
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_content_length CHECK (
            content_length >= 0
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_content_type CHECK (
            content_type = 'application/vnd.wye.scientific+json'
          ),
          CONSTRAINT ck_scientific_evaluation_artifacts_json_payload CHECK (
            json_payload IS NULL OR jsonb_typeof(json_payload) = 'object'
          )
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_scientific_evaluation_artifacts_kind_created "
        "ON scientific_evaluation_artifacts (artifact_kind, created_at)"
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_artifact_locations (
          id BIGSERIAL,
          location_key UUID NOT NULL,
          artifact_id BIGINT NOT NULL,
          storage_mode VARCHAR(20) NOT NULL,
          canonical_bytes BYTEA,
          storage_object_id BIGINT,
          location_status VARCHAR(30) NOT NULL DEFAULT 'verified',
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          verified_at TIMESTAMPTZ,
          CONSTRAINT pk_scientific_evaluation_artifact_locations PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_artifact_locations_key UNIQUE (location_key),
          CONSTRAINT fk_scientific_evaluation_artifact_locations_artifact
            FOREIGN KEY (artifact_id) REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_artifact_locations_storage_object
            FOREIGN KEY (storage_object_id) REFERENCES storage_objects(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_artifact_locations_mode CHECK (
            storage_mode IN ('inline', 'object')
          ),
          CONSTRAINT ck_scientific_evaluation_artifact_locations_status CHECK (
            location_status IN ('verified', 'quarantined', 'unavailable', 'retired')
          ),
          CONSTRAINT ck_scientific_evaluation_artifact_locations_storage CHECK (
            (storage_mode = 'inline' AND canonical_bytes IS NOT NULL AND storage_object_id IS NULL)
            OR
            (storage_mode = 'object' AND canonical_bytes IS NULL AND storage_object_id IS NOT NULL)
          ),
          CONSTRAINT ck_scientific_evaluation_artifact_locations_verified CHECK (
            (location_status = 'verified' AND verified_at IS NOT NULL)
            OR location_status <> 'verified'
          )
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_scientific_evaluation_artifact_object_location "
        "ON scientific_evaluation_artifact_locations (artifact_id, storage_object_id) "
        "WHERE storage_object_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evaluation_artifact_locations_artifact_status "
        "ON scientific_evaluation_artifact_locations (artifact_id, location_status)"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evaluation_artifact_locations_storage_object "
        "ON scientific_evaluation_artifact_locations (storage_object_id) "
        "WHERE storage_object_id IS NOT NULL"
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_protocols (
          id BIGSERIAL,
          protocol_key VARCHAR(100) NOT NULL,
          domain_key VARCHAR(100) NOT NULL,
          target_entity_type VARCHAR(30) NOT NULL,
          governance_owner VARCHAR(255) NOT NULL,
          created_by VARCHAR(255) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_protocols PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_protocols_key UNIQUE (protocol_key),
          CONSTRAINT ck_scientific_evaluation_protocols_key CHECK (
            protocol_key ~ '^[a-z][a-z0-9]*(_[a-z0-9]+)*$'
          ),
          CONSTRAINT ck_scientific_evaluation_protocols_required CHECK (
            btrim(domain_key) <> ''
            AND btrim(target_entity_type) <> ''
            AND btrim(governance_owner) <> ''
            AND btrim(created_by) <> ''
          )
        )
        """
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_protocol_versions (
          id BIGSERIAL,
          protocol_id BIGINT NOT NULL,
          semantic_version VARCHAR(50) NOT NULL,
          lifecycle_status VARCHAR(30) NOT NULL DEFAULT 'draft',
          canonical_artifact_id BIGINT,
          protocol_digest BYTEA,
          review_artifact_id BIGINT,
          effective_from DATE,
          created_by VARCHAR(255) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          published_at TIMESTAMPTZ,
          retired_at TIMESTAMPTZ,
          CONSTRAINT pk_scientific_evaluation_protocol_versions PRIMARY KEY (id),
          CONSTRAINT fk_scientific_evaluation_protocol_versions_protocol
            FOREIGN KEY (protocol_id) REFERENCES scientific_evaluation_protocols(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_protocol_versions_artifact
            FOREIGN KEY (canonical_artifact_id) REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_protocol_versions_review_artifact
            FOREIGN KEY (review_artifact_id) REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT uq_scientific_evaluation_protocol_versions_semver
            UNIQUE (protocol_id, semantic_version),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_semver CHECK (
            semantic_version ~
              '^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(-[0-9A-Za-z-]+(\\.[0-9A-Za-z-]+)*)?(\\+[0-9A-Za-z-]+(\\.[0-9A-Za-z-]+)*)?$'
          ),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_status CHECK (
            lifecycle_status IN (
              'draft', 'scientific_review', 'approved',
              'published', 'deprecated', 'retired'
            )
          ),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_digest_length CHECK (
            protocol_digest IS NULL OR octet_length(protocol_digest) = 32
          ),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_artifact_digest CHECK (
            (canonical_artifact_id IS NULL) = (protocol_digest IS NULL)
          ),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_approval CHECK (
            lifecycle_status NOT IN ('approved', 'published', 'deprecated', 'retired')
            OR (
              canonical_artifact_id IS NOT NULL
              AND protocol_digest IS NOT NULL
              AND review_artifact_id IS NOT NULL
            )
          ),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_publication CHECK (
            lifecycle_status NOT IN ('published', 'deprecated', 'retired')
            OR published_at IS NOT NULL
          ),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_retirement CHECK (
            (lifecycle_status = 'retired') = (retired_at IS NOT NULL)
          ),
          CONSTRAINT ck_scientific_evaluation_protocol_versions_created_by CHECK (
            btrim(created_by) <> ''
          )
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_scientific_evaluation_protocol_version_digest "
        "ON scientific_evaluation_protocol_versions (protocol_id, protocol_digest) "
        "WHERE protocol_digest IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_scientific_evaluation_protocol_versions_lifecycle "
        "ON scientific_evaluation_protocol_versions "
        "(protocol_id, lifecycle_status, semantic_version)"
    )

    op.execute(
        """
        CREATE TABLE scientific_evaluation_governance_events (
          id BIGSERIAL,
          event_key UUID NOT NULL,
          entity_type VARCHAR(30) NOT NULL,
          protocol_id BIGINT,
          protocol_version_id BIGINT,
          artifact_id BIGINT,
          artifact_location_id BIGINT,
          event_type VARCHAR(40) NOT NULL,
          predecessor_event_id BIGINT,
          related_protocol_id BIGINT,
          related_protocol_version_id BIGINT,
          related_artifact_id BIGINT,
          related_artifact_location_id BIGINT,
          actor_identifier VARCHAR(255) NOT NULL,
          reason_code VARCHAR(100) NOT NULL,
          rationale_artifact_id BIGINT,
          metadata JSONB,
          effective_at TIMESTAMPTZ NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          CONSTRAINT pk_scientific_evaluation_governance_events PRIMARY KEY (id),
          CONSTRAINT uq_scientific_evaluation_governance_events_key UNIQUE (event_key),
          CONSTRAINT fk_scientific_evaluation_governance_protocol
            FOREIGN KEY (protocol_id) REFERENCES scientific_evaluation_protocols(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_protocol_version
            FOREIGN KEY (protocol_version_id) REFERENCES scientific_evaluation_protocol_versions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_artifact
            FOREIGN KEY (artifact_id) REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_artifact_location
            FOREIGN KEY (artifact_location_id) REFERENCES scientific_evaluation_artifact_locations(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_predecessor
            FOREIGN KEY (predecessor_event_id) REFERENCES scientific_evaluation_governance_events(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_related_protocol
            FOREIGN KEY (related_protocol_id) REFERENCES scientific_evaluation_protocols(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_related_protocol_version
            FOREIGN KEY (related_protocol_version_id) REFERENCES scientific_evaluation_protocol_versions(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_related_artifact
            FOREIGN KEY (related_artifact_id) REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_related_artifact_location
            FOREIGN KEY (related_artifact_location_id) REFERENCES scientific_evaluation_artifact_locations(id) ON DELETE RESTRICT,
          CONSTRAINT fk_scientific_evaluation_governance_rationale_artifact
            FOREIGN KEY (rationale_artifact_id) REFERENCES scientific_evaluation_artifacts(id) ON DELETE RESTRICT,
          CONSTRAINT ck_scientific_evaluation_governance_entity_type CHECK (
            entity_type IN ('protocol', 'protocol_version', 'artifact', 'artifact_location')
          ),
          CONSTRAINT ck_scientific_evaluation_governance_event_type CHECK (
            event_type IN (
              'submitted_for_review', 'approved', 'published', 'deprecated',
              'retired', 'supersedes', 'retracts', 'integrity_compromised',
              'annotation', 'review_disposition'
            )
          ),
          CONSTRAINT ck_scientific_evaluation_governance_entity_reference CHECK (
            num_nonnulls(protocol_id, protocol_version_id, artifact_id, artifact_location_id) = 1
            AND (entity_type = 'protocol') = (protocol_id IS NOT NULL)
            AND (entity_type = 'protocol_version') = (protocol_version_id IS NOT NULL)
            AND (entity_type = 'artifact') = (artifact_id IS NOT NULL)
            AND (entity_type = 'artifact_location') = (artifact_location_id IS NOT NULL)
          ),
          CONSTRAINT ck_scientific_evaluation_governance_related_reference CHECK (
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
          CONSTRAINT ck_scientific_evaluation_governance_not_self CHECK (
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
          ),
          CONSTRAINT ck_scientific_evaluation_governance_required CHECK (
            btrim(actor_identifier) <> '' AND btrim(reason_code) <> ''
          ),
          CONSTRAINT ck_scientific_evaluation_governance_metadata CHECK (
            metadata IS NULL OR jsonb_typeof(metadata) = 'object'
          )
        )
        """
    )

    for sql in (
        "CREATE INDEX idx_scientific_evaluation_governance_protocol "
        "ON scientific_evaluation_governance_events (protocol_id, effective_at, id) "
        "WHERE protocol_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_protocol_version "
        "ON scientific_evaluation_governance_events (protocol_version_id, effective_at, id) "
        "WHERE protocol_version_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_artifact "
        "ON scientific_evaluation_governance_events (artifact_id, effective_at, id) "
        "WHERE artifact_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_artifact_location "
        "ON scientific_evaluation_governance_events (artifact_location_id, effective_at, id) "
        "WHERE artifact_location_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_predecessor "
        "ON scientific_evaluation_governance_events (predecessor_event_id) "
        "WHERE predecessor_event_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_related_protocol "
        "ON scientific_evaluation_governance_events (related_protocol_id) "
        "WHERE related_protocol_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_related_protocol_version "
        "ON scientific_evaluation_governance_events (related_protocol_version_id) "
        "WHERE related_protocol_version_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_related_artifact "
        "ON scientific_evaluation_governance_events (related_artifact_id) "
        "WHERE related_artifact_id IS NOT NULL",
        "CREATE INDEX idx_scientific_evaluation_governance_related_artifact_location "
        "ON scientific_evaluation_governance_events (related_artifact_location_id) "
        "WHERE related_artifact_location_id IS NOT NULL",
    ):
        op.execute(sql)

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_reject_artifact_mutation()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          RAISE EXCEPTION 'scientific evaluation artifact identity is immutable'
            USING ERRCODE = '55000';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_scientific_evaluation_artifacts_immutable
        BEFORE UPDATE OR DELETE ON scientific_evaluation_artifacts
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_reject_artifact_mutation()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_artifact_location()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE expected_length BIGINT;
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'scientific evaluation artifact locations are historically preserved'
              USING ERRCODE = '55000';
          END IF;

          IF TG_OP = 'UPDATE' AND ROW(
            NEW.location_key, NEW.artifact_id, NEW.storage_mode,
            NEW.canonical_bytes, NEW.storage_object_id,
            NEW.created_at, NEW.verified_at
          ) IS DISTINCT FROM ROW(
            OLD.location_key, OLD.artifact_id, OLD.storage_mode,
            OLD.canonical_bytes, OLD.storage_object_id,
            OLD.created_at, OLD.verified_at
          ) THEN
            RAISE EXCEPTION 'artifact locator and canonical content fields are immutable'
              USING ERRCODE = '55000';
          END IF;

          IF TG_OP = 'UPDATE' AND NEW.location_status IS DISTINCT FROM OLD.location_status
             AND NOT (
               (OLD.location_status = 'verified' AND NEW.location_status IN ('quarantined', 'unavailable', 'retired'))
               OR (OLD.location_status = 'quarantined' AND NEW.location_status IN ('unavailable', 'retired'))
               OR (OLD.location_status = 'unavailable' AND NEW.location_status = 'retired')
             ) THEN
            RAISE EXCEPTION 'invalid one-way artifact location status transition: % -> %',
              OLD.location_status, NEW.location_status USING ERRCODE = '23514';
          END IF;

          IF NEW.storage_mode = 'inline' THEN
            SELECT content_length INTO expected_length
            FROM public.scientific_evaluation_artifacts
            WHERE id = NEW.artifact_id;
            IF expected_length IS NOT NULL
               AND octet_length(NEW.canonical_bytes) <> expected_length THEN
              RAISE EXCEPTION 'inline canonical byte length does not match artifact content_length'
                USING ERRCODE = '23514';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_scientific_evaluation_artifact_locations_guard
        BEFORE INSERT OR UPDATE OR DELETE ON scientific_evaluation_artifact_locations
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_artifact_location()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_protocol()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          IF TG_OP = 'UPDATE'
             AND ROW(NEW.protocol_key, NEW.domain_key, NEW.target_entity_type, NEW.created_by, NEW.created_at)
                 IS DISTINCT FROM
                 ROW(OLD.protocol_key, OLD.domain_key, OLD.target_entity_type, OLD.created_by, OLD.created_at)
             AND EXISTS (
               SELECT 1 FROM public.scientific_evaluation_protocol_versions v
               WHERE v.protocol_id = OLD.id
                 AND v.lifecycle_status IN ('published', 'deprecated', 'retired')
             ) THEN
            RAISE EXCEPTION 'published protocol family identity is immutable'
              USING ERRCODE = '55000';
          END IF;
          RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_scientific_evaluation_protocols_guard
        BEFORE UPDATE OR DELETE ON scientific_evaluation_protocols
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_protocol()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_require_protocol_event()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          IF NEW.governance_owner IS NOT DISTINCT FROM OLD.governance_owner THEN
            RETURN NEW;
          END IF;
          IF NOT EXISTS (
            SELECT 1
            FROM public.scientific_evaluation_governance_events e
            WHERE e.entity_type = 'protocol'
              AND e.protocol_id = NEW.id
              AND e.xmin = txid_current()::text::xid
          ) THEN
            RAISE EXCEPTION 'protocol governance-owner transition requires a same-transaction governance event'
              USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_protocols_event
        AFTER UPDATE ON scientific_evaluation_protocols
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_require_protocol_event()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_guard_protocol_version()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            IF OLD.lifecycle_status IN ('approved', 'published', 'deprecated', 'retired') THEN
              RAISE EXCEPTION 'approved or published protocol version is historically immutable'
                USING ERRCODE = '55000';
            END IF;
            RETURN OLD;
          END IF;

          IF NEW.lifecycle_status IS DISTINCT FROM OLD.lifecycle_status
             AND NOT (
               (OLD.lifecycle_status = 'draft' AND NEW.lifecycle_status = 'scientific_review')
               OR (OLD.lifecycle_status = 'scientific_review' AND NEW.lifecycle_status IN ('draft', 'approved'))
               OR (OLD.lifecycle_status = 'approved' AND NEW.lifecycle_status IN ('draft', 'published'))
               OR (OLD.lifecycle_status = 'published' AND NEW.lifecycle_status IN ('deprecated', 'retired'))
               OR (OLD.lifecycle_status = 'deprecated' AND NEW.lifecycle_status = 'retired')
             ) THEN
            RAISE EXCEPTION 'invalid protocol lifecycle transition: % -> %',
              OLD.lifecycle_status, NEW.lifecycle_status USING ERRCODE = '23514';
          END IF;

          IF OLD.lifecycle_status IN ('published', 'deprecated', 'retired')
             AND ROW(
               NEW.protocol_id, NEW.semantic_version, NEW.canonical_artifact_id,
               NEW.protocol_digest, NEW.review_artifact_id, NEW.effective_from,
               NEW.created_by, NEW.created_at, NEW.published_at
             ) IS DISTINCT FROM ROW(
               OLD.protocol_id, OLD.semantic_version, OLD.canonical_artifact_id,
               OLD.protocol_digest, OLD.review_artifact_id, OLD.effective_from,
               OLD.created_by, OLD.created_at, OLD.published_at
             ) THEN
            RAISE EXCEPTION 'published protocol semantic content is immutable'
              USING ERRCODE = '55000';
          END IF;

          IF OLD.lifecycle_status = 'retired' AND NEW IS DISTINCT FROM OLD THEN
            RAISE EXCEPTION 'retired protocol version is immutable'
              USING ERRCODE = '55000';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_scientific_evaluation_protocol_versions_guard
        BEFORE UPDATE OR DELETE ON scientific_evaluation_protocol_versions
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_guard_protocol_version()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_protocol_version()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE artifact_digest BYTEA;
        BEGIN
          IF NEW.canonical_artifact_id IS NOT NULL THEN
            SELECT content_digest INTO artifact_digest
            FROM public.scientific_evaluation_artifacts
            WHERE id = NEW.canonical_artifact_id;
            IF artifact_digest IS DISTINCT FROM NEW.protocol_digest THEN
              RAISE EXCEPTION 'protocol_digest must equal canonical artifact content_digest'
                USING ERRCODE = '23514';
            END IF;
          END IF;

          IF NEW.lifecycle_status IN ('approved', 'published', 'deprecated', 'retired') THEN
            IF NOT EXISTS (
              SELECT 1 FROM public.scientific_evaluation_artifact_locations l
              WHERE l.artifact_id = NEW.canonical_artifact_id
                AND l.location_status = 'verified'
                AND l.verified_at IS NOT NULL
            ) OR NOT EXISTS (
              SELECT 1 FROM public.scientific_evaluation_artifact_locations l
              WHERE l.artifact_id = NEW.review_artifact_id
                AND l.location_status = 'verified'
                AND l.verified_at IS NOT NULL
            ) THEN
              RAISE EXCEPTION 'approved protocol versions require verified canonical and review artifact locations'
                USING ERRCODE = '23514';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_protocol_versions_validate
        AFTER INSERT OR UPDATE ON scientific_evaluation_protocol_versions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_validate_protocol_version()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_reject_governance_mutation()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          RAISE EXCEPTION 'scientific evaluation governance events are append-only'
            USING ERRCODE = '55000';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_scientific_evaluation_governance_immutable
        BEFORE UPDATE OR DELETE ON scientific_evaluation_governance_events
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_reject_governance_mutation()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_validate_governance_lineage()
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
            END;
            new_related_key := CASE NEW.entity_type
              WHEN 'protocol' THEN 'protocol:' || NEW.related_protocol_id
              WHEN 'protocol_version' THEN 'protocol_version:' || NEW.related_protocol_version_id
              WHEN 'artifact' THEN 'artifact:' || NEW.related_artifact_id
              WHEN 'artifact_location' THEN 'artifact_location:' || NEW.related_artifact_location_id
            END;

            WITH RECURSIVE supersession_edges(owner_key, related_key) AS (
              SELECT
                CASE entity_type
                  WHEN 'protocol' THEN 'protocol:' || protocol_id
                  WHEN 'protocol_version' THEN 'protocol_version:' || protocol_version_id
                  WHEN 'artifact' THEN 'artifact:' || artifact_id
                  WHEN 'artifact_location' THEN 'artifact_location:' || artifact_location_id
                END,
                CASE entity_type
                  WHEN 'protocol' THEN 'protocol:' || related_protocol_id
                  WHEN 'protocol_version' THEN 'protocol_version:' || related_protocol_version_id
                  WHEN 'artifact' THEN 'artifact:' || related_artifact_id
                  WHEN 'artifact_location' THEN 'artifact_location:' || related_artifact_location_id
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
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_governance_lineage
        AFTER INSERT ON scientific_evaluation_governance_events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_validate_governance_lineage()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_require_lifecycle_event()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE required_event_type TEXT;
        BEGIN
          IF TG_OP = 'UPDATE' AND NEW.lifecycle_status IS NOT DISTINCT FROM OLD.lifecycle_status THEN
            RETURN NEW;
          END IF;
          IF TG_OP = 'INSERT' AND NEW.lifecycle_status = 'draft' THEN
            RETURN NEW;
          END IF;

          required_event_type := CASE NEW.lifecycle_status
            WHEN 'draft' THEN 'review_disposition'
            WHEN 'scientific_review' THEN 'submitted_for_review'
            WHEN 'approved' THEN 'approved'
            WHEN 'published' THEN 'published'
            WHEN 'deprecated' THEN 'deprecated'
            WHEN 'retired' THEN 'retired'
          END;

          IF NOT EXISTS (
            SELECT 1
            FROM public.scientific_evaluation_governance_events e
            WHERE e.entity_type = 'protocol_version'
              AND e.protocol_version_id = NEW.id
              AND e.event_type = required_event_type
              AND e.xmin = txid_current()::text::xid
          ) THEN
            RAISE EXCEPTION 'protocol lifecycle transition to % requires a same-transaction governance event',
              NEW.lifecycle_status USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_protocol_versions_event
        AFTER INSERT OR UPDATE ON scientific_evaluation_protocol_versions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_require_lifecycle_event()
        """
    )

    op.execute(
        """
        CREATE FUNCTION scientific_evaluation_require_location_event()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          IF NEW.location_status IS NOT DISTINCT FROM OLD.location_status THEN
            RETURN NEW;
          END IF;
          IF NOT EXISTS (
            SELECT 1
            FROM public.scientific_evaluation_governance_events e
            WHERE e.entity_type = 'artifact_location'
              AND e.artifact_location_id = NEW.id
              AND e.xmin = txid_current()::text::xid
          ) THEN
            RAISE EXCEPTION 'artifact location status transition requires a same-transaction governance event'
              USING ERRCODE = '23514';
          END IF;
          IF OLD.location_status = 'verified'
             AND NEW.location_status <> 'verified'
             AND EXISTS (
               SELECT 1
               FROM public.scientific_evaluation_protocol_versions v
               WHERE v.lifecycle_status IN ('approved', 'published', 'deprecated', 'retired')
                 AND (v.canonical_artifact_id = NEW.artifact_id OR v.review_artifact_id = NEW.artifact_id)
             )
             AND NOT EXISTS (
               SELECT 1
               FROM public.scientific_evaluation_artifact_locations other_location
               WHERE other_location.artifact_id = NEW.artifact_id
                 AND other_location.location_status = 'verified'
                 AND other_location.id <> NEW.id
             ) THEN
            RAISE EXCEPTION 'cannot remove the last verified location of a governed protocol artifact'
              USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_scientific_evaluation_artifact_locations_event
        AFTER UPDATE ON scientific_evaluation_artifact_locations
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION scientific_evaluation_require_location_event()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM scientific_evaluation_governance_events)
             OR EXISTS (SELECT 1 FROM scientific_evaluation_protocol_versions)
             OR EXISTS (SELECT 1 FROM scientific_evaluation_protocols)
             OR EXISTS (SELECT 1 FROM scientific_evaluation_artifact_locations)
             OR EXISTS (SELECT 1 FROM scientific_evaluation_artifacts) THEN
            RAISE EXCEPTION 'Cannot downgrade 0019: scientific evaluation canonical history is not representable at 0018.';
          END IF;
        END $$
        """
    )

    op.execute("DROP TABLE scientific_evaluation_governance_events")
    op.execute("DROP TABLE scientific_evaluation_protocol_versions")
    op.execute("DROP TABLE scientific_evaluation_protocols")
    op.execute("DROP TABLE scientific_evaluation_artifact_locations")
    op.execute("DROP TABLE scientific_evaluation_artifacts")

    op.execute("DROP FUNCTION scientific_evaluation_require_location_event()")
    op.execute("DROP FUNCTION scientific_evaluation_require_lifecycle_event()")
    op.execute("DROP FUNCTION scientific_evaluation_validate_governance_lineage()")
    op.execute("DROP FUNCTION scientific_evaluation_reject_governance_mutation()")
    op.execute("DROP FUNCTION scientific_evaluation_validate_protocol_version()")
    op.execute("DROP FUNCTION scientific_evaluation_guard_protocol_version()")
    op.execute("DROP FUNCTION scientific_evaluation_require_protocol_event()")
    op.execute("DROP FUNCTION scientific_evaluation_guard_protocol()")
    op.execute("DROP FUNCTION scientific_evaluation_guard_artifact_location()")
    op.execute("DROP FUNCTION scientific_evaluation_reject_artifact_mutation()")
