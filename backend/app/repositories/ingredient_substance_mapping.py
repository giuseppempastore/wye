"""PostgreSQL primitives for controlled ingredient-substance mappings."""

from psycopg2.extras import Json


class PostgresIngredientSubstanceMappingRepository:
    def load_ingredient(self, cursor, ingredient_id):
        cursor.execute("SELECT id FROM ingredients WHERE id=%s FOR SHARE", (ingredient_id,))
        return cursor.fetchone()

    def load_substance(self, cursor, substance_id):
        cursor.execute("SELECT id,status FROM substances WHERE id=%s FOR SHARE", (substance_id,))
        return cursor.fetchone()

    def load_run(self, cursor, run_id):
        cursor.execute("SELECT id,release_id FROM scientific_ingestion_runs WHERE id=%s FOR SHARE", (run_id,))
        return cursor.fetchone()

    def load_release(self, cursor, release_id):
        cursor.execute("SELECT id FROM source_dataset_releases WHERE id=%s FOR SHARE", (release_id,))
        return cursor.fetchone()

    def create_proposal(self, cursor, payload):
        cursor.execute("""
          INSERT INTO ingredient_substance_mapping_proposals(
            proposal_key,ingredient_id,substance_id,relationship_type,mapping_method,
            mapping_confidence,source_dataset_release_id,ingestion_run_id,proposed_by,provenance)
          VALUES(%(proposal_key)s,%(ingredient_id)s,%(substance_id)s,%(relationship_type)s,
            %(mapping_method)s,%(mapping_confidence)s,%(release_id)s,%(run_id)s,%(proposed_by)s,%(provenance)s)
          ON CONFLICT(proposal_key) DO NOTHING RETURNING *
        """, {**payload, "provenance": Json(payload["provenance"]) if payload["provenance"] is not None else None})
        return cursor.fetchone()

    def get_proposal_by_key(self, cursor, proposal_key):
        cursor.execute("SELECT * FROM ingredient_substance_mapping_proposals WHERE proposal_key=%s", (proposal_key,))
        return cursor.fetchone()

    def get_proposal(self, cursor, proposal_id, lock=False):
        cursor.execute("SELECT * FROM ingredient_substance_mapping_proposals WHERE id=%s" + (" FOR UPDATE" if lock else ""), (proposal_id,))
        return cursor.fetchone()

    def terminal_decision(self, cursor, proposal_id):
        cursor.execute("SELECT * FROM ingredient_substance_mapping_decisions WHERE proposal_id=%s AND decision_type IN ('accept','reject')", (proposal_id,))
        return cursor.fetchone()

    def create_decision(self, cursor, proposal_id, decision_type, effective_from,
                        reviewed_by, reviewed_at, reason_code, notes, provenance):
        cursor.execute("""
          INSERT INTO ingredient_substance_mapping_decisions(
            proposal_id,decision_type,effective_from,reviewed_by,reviewed_at,
            reason_code,notes,provenance)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
        """, (proposal_id, decision_type, effective_from, reviewed_by, reviewed_at,
              reason_code, notes, Json(provenance) if provenance is not None else None))
        return cursor.fetchone()

    def update_proposal_status(self, cursor, proposal_id, status):
        cursor.execute("UPDATE ingredient_substance_mapping_proposals SET proposal_status=%s WHERE id=%s AND proposal_status='pending_review' RETURNING id", (status, proposal_id))
        return cursor.fetchone()
    def overlapping_closed_mapping(self, cursor, proposal, effective_from):
        cursor.execute("""
          SELECT id,valid_from,valid_to FROM ingredient_substances
          WHERE ingredient_id=%s AND substance_id=%s AND relationship_type=%s
            AND mapping_status='accepted' AND valid_to IS NOT NULL AND valid_to>=%s
          ORDER BY valid_to DESC,id DESC LIMIT 1 FOR UPDATE
        """, (proposal["ingredient_id"], proposal["substance_id"],
              proposal["relationship_type"], effective_from))
        return cursor.fetchone()


    def current_open_mapping(self, cursor, proposal, lock=False):
        cursor.execute("""
          SELECT * FROM ingredient_substances
          WHERE ingredient_id=%s AND substance_id=%s AND relationship_type=%s
            AND mapping_status='accepted' AND valid_to IS NULL
        """ + (" FOR UPDATE" if lock else ""), (proposal["ingredient_id"], proposal["substance_id"], proposal["relationship_type"]))
        return cursor.fetchone()

    def create_accepted_mapping(self, cursor, proposal, decision):
        cursor.execute("""
          INSERT INTO ingredient_substances(
            ingredient_id,substance_id,relationship_type,mapping_method,mapping_status,
            mapping_confidence,source_dataset_release_id,ingestion_run_id,provenance,
            reviewed_by,reviewed_at,valid_from,valid_to)
          VALUES(%s,%s,%s,%s,'accepted',%s,%s,%s,%s,%s,%s,%s,NULL)
          ON CONFLICT(ingredient_id,substance_id,relationship_type)
            WHERE mapping_status='accepted' AND valid_to IS NULL DO NOTHING
          RETURNING *
        """, (proposal["ingredient_id"], proposal["substance_id"], proposal["relationship_type"],
              proposal["mapping_method"], proposal["mapping_confidence"],
              proposal["source_dataset_release_id"], proposal["ingestion_run_id"],
              Json({"origin":"controlled_mapping_review","proposal_id":proposal["id"],"decision_id":decision["id"],"proposal_provenance":proposal["provenance"]}),
              decision["reviewed_by"], decision["reviewed_at"], decision["effective_from"]))
        return cursor.fetchone()

    def create_materialization(self, cursor, decision_id, proposal_id, mapping_id,
                               status, materialized_by, materialized_at, provenance):
        cursor.execute("""
          INSERT INTO ingredient_substance_mapping_materializations(
            decision_id,proposal_id,ingredient_substance_id,materialization_status,
            materialized_by,materialized_at,provenance)
          VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING *
        """, (decision_id, proposal_id, mapping_id, status, materialized_by,
              materialized_at, Json(provenance) if provenance is not None else None))
        return cursor.fetchone()

    def get_materialization(self, cursor, decision_id):
        cursor.execute("SELECT * FROM ingredient_substance_mapping_materializations WHERE decision_id=%s", (decision_id,))
        return cursor.fetchone()

    def get_mapping(self, cursor, mapping_id, lock=False):
        cursor.execute("SELECT * FROM ingredient_substances WHERE id=%s" + (" FOR UPDATE" if lock else ""), (mapping_id,))
        return cursor.fetchone()

    def close_mapping(self, cursor, mapping_id, valid_to):
        cursor.execute("UPDATE ingredient_substances SET valid_to=%s WHERE id=%s AND mapping_status='accepted' AND valid_to IS NULL RETURNING *", (valid_to, mapping_id))
        return cursor.fetchone()

    def create_closure(self, cursor, mapping_id, valid_to, closed_by, closed_at,
                       reason_code, provenance):
        cursor.execute("""
          INSERT INTO ingredient_substance_mapping_closures(
            ingredient_substance_id,valid_to,closed_by,closed_at,reason_code,provenance)
          VALUES(%s,%s,%s,%s,%s,%s) RETURNING *
        """, (mapping_id, valid_to, closed_by, closed_at, reason_code,
              Json(provenance) if provenance is not None else None))
        return cursor.fetchone()

    def get_closure(self, cursor, mapping_id):
        cursor.execute("SELECT * FROM ingredient_substance_mapping_closures WHERE ingredient_substance_id=%s", (mapping_id,))
        return cursor.fetchone()

    def current_for_ingredient(self, cursor, ingredient_id, as_of):
        cursor.execute("""
          SELECT * FROM ingredient_substances WHERE ingredient_id=%s
            AND mapping_status='accepted' AND valid_from IS NOT NULL AND valid_from<=%s
            AND (valid_to IS NULL OR valid_to>=%s)
          ORDER BY relationship_type,substance_id,id
        """, (ingredient_id, as_of, as_of))
        return cursor.fetchall()

    def history_for_ingredient(self, cursor, ingredient_id):
        cursor.execute("SELECT * FROM ingredient_substances WHERE ingredient_id=%s ORDER BY COALESCE(valid_from,created_at::date),created_at,id", (ingredient_id,))
        return cursor.fetchall()
