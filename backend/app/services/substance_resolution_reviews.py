"""Transactional candidate capture and explicit review decisions."""

from datetime import datetime,timezone
from typing import Callable

import psycopg2
import psycopg2.extras

from app.db import get_connection
from app.repositories.substance_resolution_reviews import PostgresSubstanceResolutionReviewRepository
from app.scientific_ingestion.canonicalization import canonical_sha256


class SubstanceResolutionReviewError(RuntimeError):
    def __init__(self,code,message): self.code=code; super().__init__(message)


class SubstanceResolutionReviewService:
    def __init__(self,repository=None,connection_factory:Callable=get_connection,clock=lambda:datetime.now(timezone.utc)):
        self.repository=repository or PostgresSubstanceResolutionReviewRepository(); self.connection_factory=connection_factory; self.clock=clock

    def record_resolution(self,run_id,record,resolution,provenance=None):
        if resolution.status=="resolved": return ()
        candidates=self._candidate_payloads(record,resolution)
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                persisted=[]
                for candidate in candidates:
                    row=self.repository.get_or_create_candidate(cursor,candidate)
                    occurrence_id,created=self.repository.record_occurrence(cursor,row["id"],run_id,record,resolution,provenance)
                    persisted.append({"candidate_id":row["id"],"candidate_status":row["candidate_status"],"occurrence_id":occurrence_id,"occurrence_created":created})
            connection.commit(); return tuple(persisted)
        except Exception:
            connection.rollback(); raise
        finally: connection.close()

    def decide(self,candidate_id,decision_type,reviewed_by,reason_code,target_substance_id=None,notes=None,provenance=None,preferred_name=None,normalized_name=None,substance_type=None):
        if decision_type not in {"associate_existing","create_new_substance","reject","defer"}: raise SubstanceResolutionReviewError("invalid_decision","Unsupported decision")
        if not reviewed_by or not reviewed_by.strip(): raise SubstanceResolutionReviewError("reviewer_required","reviewed_by is required")
        if not reason_code or not reason_code.strip(): raise SubstanceResolutionReviewError("reason_required","reason_code is required")
        if (decision_type=="associate_existing")!=(target_substance_id is not None): raise SubstanceResolutionReviewError("invalid_target","target substance is required only for association")
        creation_values=(preferred_name,normalized_name,substance_type)
        if decision_type=="create_new_substance":
            if any(not isinstance(value,str) or not value.strip() for value in creation_values): raise SubstanceResolutionReviewError("creation_payload_required","Explicit preferred_name, normalized_name and substance_type are required")
            if len(preferred_name.strip())>255 or len(normalized_name.strip())>255: raise SubstanceResolutionReviewError("creation_payload_invalid","Substance names must not exceed 255 characters")
            if substance_type not in {"additive","chemical_substance","biological_substance","contaminant","nutrient","mixture","unknown"}: raise SubstanceResolutionReviewError("creation_payload_invalid","Unsupported substance_type")
            preferred_name=preferred_name.strip(); normalized_name=normalized_name.strip()
        elif any(value is not None for value in creation_values):
            raise SubstanceResolutionReviewError("creation_payload_invalid","Creation payload is valid only for create_new_substance")
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                candidate=self.repository.get_candidate(cursor,candidate_id,lock=True)
                if candidate is None: raise SubstanceResolutionReviewError("candidate_not_found","Candidate not found")
                if decision_type in {"associate_existing","create_new_substance","reject"} and candidate["candidate_status"]!="pending_review": raise SubstanceResolutionReviewError("candidate_already_terminal","Candidate already has a terminal decision")
                if decision_type=="create_new_substance" and (candidate["candidate_kind"]!="unknown_identifier" or candidate["namespace_id"] is None or not candidate["normalized_value"]): raise SubstanceResolutionReviewError("candidate_not_eligible_for_creation","Create-new requires an unknown identifier in a known namespace")
                if decision_type=="associate_existing":
                    target=self.repository.lock_target_substance(cursor,target_substance_id)
                    if target is None or target["status"]!="active": raise SubstanceResolutionReviewError("target_not_eligible","Target substance must be active")
                try:
                    decision=self.repository.record_decision(cursor,candidate_id,decision_type,target_substance_id,reviewed_by.strip(),self.clock(),reason_code.strip(),notes,provenance,preferred_name,normalized_name,substance_type)
                except psycopg2.IntegrityError as exc:
                    if getattr(exc.diag,"constraint_name",None)=="uq_substance_resolution_terminal_decision": raise SubstanceResolutionReviewError("candidate_already_terminal","Concurrent terminal decision won") from exc
                    raise
                if decision_type in {"associate_existing","create_new_substance","reject"}:
                    status={"associate_existing":"resolved_existing","create_new_substance":"resolved_new","reject":"rejected"}[decision_type]
                    if not self.repository.update_status(cursor,candidate_id,status): raise SubstanceResolutionReviewError("candidate_already_terminal","Candidate state changed concurrently")
            connection.commit(); return dict(decision)
        except Exception:
            connection.rollback(); raise
        finally: connection.close()

    def get(self,candidate_id):
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                candidate=self.repository.get_candidate(cursor,candidate_id); history=self.repository.decision_history(cursor,candidate_id) if candidate else ()
            if candidate is None: raise SubstanceResolutionReviewError("candidate_not_found","Candidate not found")
            return {"candidate":dict(candidate),"decisions":[dict(row) for row in history]}
        finally: connection.close()

    def list_pending(self,limit=100):
        if limit<1 or limit>1000: raise ValueError("limit must be between 1 and 1000")
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor: rows=self.repository.list_pending(cursor,limit)
            return tuple(dict(row) for row in rows)
        finally: connection.close()

    @staticmethod
    def _candidate_payloads(record,resolution):
        diagnostics=tuple(resolution.diagnostics)
        if resolution.status=="ambiguous" and resolution.reason_code=="conflicting_identifier_matches":
            identity={"kind":"identity_conflict","identifiers":sorted((i.namespace_key,i.namespace_version,i.normalized_value) for i in record.substance_identifiers),"substance_ids":sorted(resolution.conflicting_substance_ids)}
            return ({"candidate_key":canonical_sha256(identity),"candidate_kind":"identity_conflict","namespace_id":None,"namespace_key":None,"namespace_version":None,"normalized_value":None,"candidate_name":None},)
        kind="inactive_target" if resolution.reason_code in {"inactive_substance","deprecated_substance"} else "unknown_identifier"
        by_identity={(d.namespace_key,d.namespace_version,d.normalized_value):d for d in diagnostics}
        payloads=[]
        for item in record.substance_identifiers:
            key=(item.namespace_key,item.namespace_version,item.normalized_value)
            if any(existing["namespace_key"]==key[0] and existing["namespace_version"]==key[1] and existing["normalized_value"]==key[2] for existing in payloads): continue
            diagnostic=by_identity.get(key); identity={"kind":kind,"namespace_id":diagnostic.namespace_id if diagnostic else None,"namespace_key":key[0],"namespace_version":key[1],"normalized_value":key[2]}
            payloads.append({"candidate_key":canonical_sha256(identity),"candidate_kind":kind,"namespace_id":diagnostic.namespace_id if diagnostic else None,"namespace_key":key[0],"namespace_version":key[1],"normalized_value":key[2],"candidate_name":None})
        return tuple(payloads)
