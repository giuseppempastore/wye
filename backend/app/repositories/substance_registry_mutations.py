"""PostgreSQL primitives for audited substance registry mutations."""

from psycopg2.extras import Json


class PostgresSubstanceRegistryMutationRepository:
    def load_decision_candidate_for_update(self, cursor, decision_id):
        cursor.execute(
            """
            SELECT d.id AS decision_id,d.decision_type,d.target_substance_id,
                   d.reviewed_by,d.reviewed_at,c.id AS candidate_id,
                   d.proposed_preferred_name,d.proposed_normalized_name,
                   d.proposed_substance_type,
                   c.candidate_kind,c.candidate_status,c.namespace_id,
                   c.namespace_key,c.namespace_version,c.normalized_value
            FROM substance_resolution_decisions d
            JOIN substance_resolution_candidates c ON c.id=d.candidate_id
            WHERE d.id=%s
            FOR UPDATE OF d,c
            """,
            (decision_id,),
        )
        return cursor.fetchone()

    def get_materialization(self, cursor, decision_id):
        cursor.execute(
            "SELECT * FROM substance_registry_materializations WHERE decision_id=%s",
            (decision_id,),
        )
        return cursor.fetchone()

    def load_active_target(self, cursor, substance_id):
        cursor.execute(
            "SELECT id,status FROM substances WHERE id=%s FOR SHARE", (substance_id,)
        )
        return cursor.fetchone()

    def load_namespace(self, cursor, namespace_id):
        cursor.execute(
            "SELECT id,namespace_key,namespace_version FROM substance_identifier_namespaces "
            "WHERE id=%s FOR SHARE",
            (namespace_id,),
        )
        return cursor.fetchone()

    def observed_raw_value(self, cursor, candidate_id, namespace_key, namespace_version, normalized_value):
        cursor.execute(
            """
            SELECT item->>'raw_value' AS raw_value
            FROM substance_resolution_candidate_occurrences o
            CROSS JOIN LATERAL jsonb_array_elements(o.raw_identifiers) item
            WHERE o.candidate_id=%s
              AND item->>'namespace_key'=%s
              AND item->>'namespace_version'=%s
              AND item->>'normalized_value'=%s
              AND btrim(COALESCE(item->>'raw_value',''))<>''
            ORDER BY o.observed_at,o.id
            LIMIT 1
            """,
            (candidate_id, namespace_key, namespace_version, normalized_value),
        )
        return cursor.fetchone()

    def lookup_identifier(self, cursor, namespace_id, normalized_value):
        cursor.execute(
            "SELECT * FROM substance_identifiers WHERE namespace_id=%s AND normalized_value=%s",
            (namespace_id, normalized_value),
        )
        return cursor.fetchone()

    def create_verified_identifier(self, cursor, *, substance_id, namespace_id,
                                   identifier_system, raw_value, normalized_value,
                                   provenance, is_primary=False):
        cursor.execute(
            """
            INSERT INTO substance_identifiers(
              substance_id,namespace_id,identifier_system,identifier_value,
              normalized_value,is_primary,verification_status,
              source_dataset_release_id,ingestion_run_id,provenance)
            VALUES(%s,%s,%s,%s,%s,%s,'verified',NULL,NULL,%s)
            ON CONFLICT(namespace_id,normalized_value) DO NOTHING
            RETURNING *
            """,
            (substance_id, namespace_id, identifier_system, raw_value,
             normalized_value, is_primary, Json(provenance)),
        )
        return cursor.fetchone()

    def create_substance(self, cursor, preferred_name, normalized_name, substance_type):
        cursor.execute(
            """INSERT INTO substances(preferred_name,normalized_name,substance_type,status)
               VALUES(%s,%s,%s,'active') RETURNING *""",
            (preferred_name, normalized_name, substance_type),
        )
        return cursor.fetchone()

    def create_materialization(self, cursor, *, decision, target_substance_id,
                               identifier_id, mutation_type, status,
                               materialized_by, materialized_at, provenance):
        cursor.execute(
            """
            INSERT INTO substance_registry_materializations(
              decision_id,candidate_id,target_substance_id,namespace_id,
              normalized_value,substance_identifier_id,mutation_type,
              materialization_status,materialized_by,materialized_at,provenance)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
            """,
            (decision["decision_id"], decision["candidate_id"],
             target_substance_id, decision["namespace_id"], decision["normalized_value"],
             identifier_id, mutation_type, status, materialized_by, materialized_at,
             Json(provenance) if provenance is not None else None),
        )
        return cursor.fetchone()
