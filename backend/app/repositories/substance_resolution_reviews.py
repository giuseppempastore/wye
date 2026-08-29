"""PostgreSQL persistence for substance resolution candidates and decisions."""

from psycopg2.extras import Json


class PostgresSubstanceResolutionReviewRepository:
    def get_or_create_candidate(self,cursor,candidate):
        cursor.execute("""
          INSERT INTO substance_resolution_candidates(
            candidate_key,candidate_kind,namespace_id,namespace_key,namespace_version,
            normalized_value,candidate_name,first_seen_at,last_seen_at)
          VALUES(%(candidate_key)s,%(candidate_kind)s,%(namespace_id)s,%(namespace_key)s,
            %(namespace_version)s,%(normalized_value)s,%(candidate_name)s,NOW(),NOW())
          ON CONFLICT(candidate_key) DO UPDATE SET last_seen_at=GREATEST(
            substance_resolution_candidates.last_seen_at,EXCLUDED.last_seen_at)
          RETURNING id,candidate_status
        """,candidate)
        return cursor.fetchone()

    def record_occurrence(self,cursor,candidate_id,run_id,record,resolution,provenance):
        cursor.execute("""
          INSERT INTO substance_resolution_candidate_occurrences(
            candidate_id,ingestion_run_id,source_record_key,resolution_outcome,
            reason_code,raw_identifiers,diagnostics,provenance)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
          ON CONFLICT(candidate_id,ingestion_run_id,source_record_key) DO NOTHING
          RETURNING id
        """,(candidate_id,run_id,record.source_record_key,resolution.status,
          resolution.reason_code or f"substance_{resolution.status}",
          Json([item.model_dump(mode="json") for item in record.substance_identifiers]),
          Json([item.model_dump(mode="json") for item in resolution.diagnostics]),
          Json(provenance) if provenance is not None else None))
        row=cursor.fetchone()
        if row: return row["id"],True
        cursor.execute("SELECT id FROM substance_resolution_candidate_occurrences WHERE candidate_id=%s AND ingestion_run_id=%s AND source_record_key=%s",(candidate_id,run_id,record.source_record_key))
        return cursor.fetchone()["id"],False

    def get_candidate(self,cursor,candidate_id,lock=False):
        cursor.execute("SELECT * FROM substance_resolution_candidates WHERE id=%s"+(" FOR UPDATE" if lock else ""),(candidate_id,))
        return cursor.fetchone()

    def list_pending(self,cursor,limit):
        cursor.execute("SELECT * FROM substance_resolution_candidates WHERE candidate_status='pending_review' ORDER BY first_seen_at,id LIMIT %s",(limit,))
        return cursor.fetchall()

    def lock_target_substance(self,cursor,substance_id):
        cursor.execute("SELECT id,status FROM substances WHERE id=%s FOR SHARE",(substance_id,)); return cursor.fetchone()

    def record_decision(self,cursor,candidate_id,decision_type,target_substance_id,reviewed_by,reviewed_at,reason_code,notes,provenance,preferred_name=None,normalized_name=None,substance_type=None):
        cursor.execute("""
          INSERT INTO substance_resolution_decisions(candidate_id,decision_type,
            target_substance_id,reviewed_by,reviewed_at,reason_code,notes,provenance,
            proposed_preferred_name,proposed_normalized_name,proposed_substance_type)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
        """,(candidate_id,decision_type,target_substance_id,reviewed_by,reviewed_at,
          reason_code,notes,Json(provenance) if provenance is not None else None,
          preferred_name,normalized_name,substance_type))
        return cursor.fetchone()

    def update_status(self,cursor,candidate_id,status):
        cursor.execute("UPDATE substance_resolution_candidates SET candidate_status=%s WHERE id=%s AND candidate_status='pending_review' RETURNING id",(status,candidate_id))
        return cursor.fetchone() is not None

    def decision_history(self,cursor,candidate_id):
        cursor.execute("SELECT * FROM substance_resolution_decisions WHERE candidate_id=%s ORDER BY created_at,id",(candidate_id,)); return cursor.fetchall()
