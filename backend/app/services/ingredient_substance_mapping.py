"""Controlled proposal, review, acceptance and history for scientific mappings."""

from datetime import date, datetime, timezone
from typing import Callable
from uuid import UUID

import psycopg2
import psycopg2.extras

from app.db import get_connection
from app.repositories.ingredient_substance_mapping import PostgresIngredientSubstanceMappingRepository


class IngredientSubstanceMappingError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class IngredientSubstanceMappingService:
    RELATIONSHIPS = {"represents","contains","derived_from","mixture_component","equivalent_to"}
    METHODS = {"manual_review","dataset","deterministic"}

    def __init__(self, repository=None, connection_factory: Callable = get_connection,
                 clock=lambda: datetime.now(timezone.utc)):
        self.repository = repository or PostgresIngredientSubstanceMappingRepository()
        self.connection_factory = connection_factory
        self.clock = clock

    def propose_mapping(self, *, proposal_key, ingredient_id, substance_id,
                        relationship_type, mapping_method, proposed_by,
                        mapping_confidence=None, release_id=None, run_id=None,
                        provenance=None):
        try: key = str(UUID(str(proposal_key)))
        except (ValueError, TypeError, AttributeError) as exc:
            raise IngredientSubstanceMappingError("invalid_proposal_key", "proposal_key must be a UUID") from exc
        actor = proposed_by.strip() if proposed_by else ""
        if not actor: raise IngredientSubstanceMappingError("proposer_required", "proposed_by is required")
        if relationship_type not in self.RELATIONSHIPS: raise IngredientSubstanceMappingError("invalid_relationship", "Unsupported relationship type")
        if mapping_method not in self.METHODS: raise IngredientSubstanceMappingError("invalid_mapping_method", "Unsupported mapping method")
        if mapping_confidence is not None and not 0 <= mapping_confidence <= 1: raise IngredientSubstanceMappingError("invalid_confidence", "mapping_confidence must be between 0 and 1")
        if mapping_method == "dataset" and release_id is None and run_id is None: raise IngredientSubstanceMappingError("dataset_provenance_required", "Dataset proposals require release or run provenance")
        if mapping_method == "deterministic" and provenance is None: raise IngredientSubstanceMappingError("deterministic_provenance_required", "Deterministic proposals require structured provenance")
        payload={"proposal_key":key,"ingredient_id":ingredient_id,"substance_id":substance_id,
                 "relationship_type":relationship_type,"mapping_method":mapping_method,
                 "mapping_confidence":mapping_confidence,"release_id":release_id,"run_id":run_id,
                 "proposed_by":actor,"provenance":provenance}
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                self._validate_references(cursor, ingredient_id, substance_id, release_id, run_id, require_active=False)
                row=self.repository.create_proposal(cursor,payload)
                if row is None:
                    row=self.repository.get_proposal_by_key(cursor,key)
                    self._assert_compatible_proposal(row,payload)
            connection.commit(); return dict(row)
        except Exception: connection.rollback(); raise
        finally: connection.close()

    def review_proposal(self, proposal_id, decision_type, reviewed_by, reason_code,
                        *, effective_from=None, materialized_by=None, notes=None,
                        provenance=None):
        if decision_type not in {"accept","reject","defer"}: raise IngredientSubstanceMappingError("invalid_decision", "Unsupported decision")
        reviewer=reviewed_by.strip() if reviewed_by else ""
        reason=reason_code.strip() if reason_code else ""
        if not reviewer: raise IngredientSubstanceMappingError("reviewer_required", "reviewed_by is required")
        if not reason: raise IngredientSubstanceMappingError("reason_required", "reason_code is required")
        if decision_type == "accept" and not isinstance(effective_from,date): raise IngredientSubstanceMappingError("effective_from_required", "Accepted mappings require effective_from")
        if decision_type != "accept" and effective_from is not None: raise IngredientSubstanceMappingError("invalid_effective_from", "Only acceptance has effective_from")
        materializer=materialized_by.strip() if materialized_by else ""
        if decision_type == "accept" and not materializer: raise IngredientSubstanceMappingError("materializer_required", "materialized_by is required")
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                proposal=self.repository.get_proposal(cursor,proposal_id,lock=True)
                if proposal is None: raise IngredientSubstanceMappingError("proposal_not_found", "Proposal not found")
                terminal=self.repository.terminal_decision(cursor,proposal_id)
                if terminal is not None:
                    if terminal["decision_type"] != decision_type: raise IngredientSubstanceMappingError("terminal_decision_conflict", "Proposal already has an incompatible terminal decision")
                    if decision_type == "accept":
                        materialization=self.repository.get_materialization(cursor,terminal["id"])
                        if materialization is None: raise IngredientSubstanceMappingError("materialization_missing", "Accepted decision has no materialization")
                        connection.commit(); return {"decision":dict(terminal),"materialization":dict(materialization)}
                    connection.commit(); return {"decision":dict(terminal),"materialization":None}
                if decision_type == "accept":
                    self._validate_references(cursor,proposal["ingredient_id"],proposal["substance_id"],proposal["source_dataset_release_id"],proposal["ingestion_run_id"],require_active=True)
                try:
                    decision=self.repository.create_decision(cursor,proposal_id,decision_type,effective_from,reviewer,self.clock(),reason,notes,provenance)
                except psycopg2.IntegrityError as exc:
                    if getattr(exc.diag,"constraint_name",None)=="uq_ingredient_substance_terminal_decision": raise IngredientSubstanceMappingError("terminal_decision_conflict", "Concurrent terminal decision won") from exc
                    raise
                materialization=None
                if decision_type == "accept":
                    if self.repository.overlapping_closed_mapping(cursor,proposal,effective_from) is not None:
                        raise IngredientSubstanceMappingError("validity_overlap", "Accepted mapping overlaps existing history")
                    mapping=self.repository.current_open_mapping(cursor,proposal,lock=True)
                    status="already_current"
                    if mapping is None:
                        mapping=self.repository.create_accepted_mapping(cursor,proposal,decision)
                        if mapping is None: mapping=self.repository.current_open_mapping(cursor,proposal,lock=True)
                        else: status="applied"
                    materialization=self.repository.create_materialization(cursor,decision["id"],proposal_id,mapping["id"],status,materializer,self.clock(),provenance)
                    new_status="accepted"
                elif decision_type == "reject": new_status="rejected"
                else: new_status=None
                if new_status and self.repository.update_proposal_status(cursor,proposal_id,new_status) is None: raise IngredientSubstanceMappingError("terminal_decision_conflict", "Proposal changed concurrently")
            connection.commit(); return {"decision":dict(decision),"materialization":dict(materialization) if materialization else None}
        except Exception: connection.rollback(); raise
        finally: connection.close()

    def close_mapping(self, mapping_id, valid_to, closed_by, reason_code, provenance=None):
        if not isinstance(valid_to,date): raise IngredientSubstanceMappingError("invalid_valid_to", "valid_to is required")
        actor=closed_by.strip() if closed_by else ""; reason=reason_code.strip() if reason_code else ""
        if not actor or not reason: raise IngredientSubstanceMappingError("closure_metadata_required", "closed_by and reason_code are required")
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                mapping=self.repository.get_mapping(cursor,mapping_id,lock=True)
                if mapping is None: raise IngredientSubstanceMappingError("mapping_not_found", "Mapping not found")
                existing=self.repository.get_closure(cursor,mapping_id)
                if existing:
                    if existing["valid_to"] != valid_to: raise IngredientSubstanceMappingError("closure_conflict", "Mapping was closed with another date")
                    connection.commit(); return dict(existing)
                if mapping["mapping_status"] != "accepted" or mapping["valid_to"] is not None: raise IngredientSubstanceMappingError("mapping_not_current", "Only an open accepted mapping can be closed")
                if mapping["valid_from"] is not None and valid_to < mapping["valid_from"]: raise IngredientSubstanceMappingError("invalid_validity", "valid_to precedes valid_from")
                if self.repository.close_mapping(cursor,mapping_id,valid_to) is None: raise IngredientSubstanceMappingError("closure_conflict", "Mapping changed concurrently")
                closure=self.repository.create_closure(cursor,mapping_id,valid_to,actor,self.clock(),reason,provenance)
            connection.commit(); return dict(closure)
        except Exception: connection.rollback(); raise
        finally: connection.close()

    def current_mappings(self, ingredient_id, as_of=None):
        as_of=as_of or self.clock().date(); connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor: rows=self.repository.current_for_ingredient(cursor,ingredient_id,as_of)
            return tuple(dict(row) for row in rows)
        finally: connection.close()

    def history(self, ingredient_id):
        connection=self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor: rows=self.repository.history_for_ingredient(cursor,ingredient_id)
            return tuple(dict(row) for row in rows)
        finally: connection.close()

    def _validate_references(self,cursor,ingredient_id,substance_id,release_id,run_id,require_active):
        if self.repository.load_ingredient(cursor,ingredient_id) is None: raise IngredientSubstanceMappingError("ingredient_not_found", "Ingredient not found")
        substance=self.repository.load_substance(cursor,substance_id)
        if substance is None: raise IngredientSubstanceMappingError("substance_not_found", "Substance not found")
        if require_active and substance["status"]!="active": raise IngredientSubstanceMappingError("substance_not_eligible", "Accepted mappings require an active substance")
        if release_id is not None and self.repository.load_release(cursor,release_id) is None: raise IngredientSubstanceMappingError("release_not_found", "Release not found")
        run=self.repository.load_run(cursor,run_id) if run_id is not None else None
        if run_id is not None and run is None: raise IngredientSubstanceMappingError("run_not_found", "Ingestion run not found")
        if run is not None and release_id is not None and run["release_id"]!=release_id: raise IngredientSubstanceMappingError("release_run_mismatch", "Ingestion run belongs to another release")

    @staticmethod
    def _assert_compatible_proposal(row,payload):
        fields={"ingredient_id":"ingredient_id","substance_id":"substance_id","relationship_type":"relationship_type","mapping_method":"mapping_method","mapping_confidence":"mapping_confidence","source_dataset_release_id":"release_id","ingestion_run_id":"run_id","proposed_by":"proposed_by","provenance":"provenance"}
        if any(row[column] != payload[key] for column,key in fields.items()): raise IngredientSubstanceMappingError("proposal_identity_conflict", "proposal_key already identifies different content")
