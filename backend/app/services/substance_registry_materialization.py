"""Explicit, idempotent materialization of approved registry decisions."""

from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable

import psycopg2.extras

from app.db import get_connection
from app.repositories.substance_registry_mutations import (
    PostgresSubstanceRegistryMutationRepository,
)


class SubstanceRegistryMaterializationError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class SubstanceRegistryMaterializationService:
    """Apply only reviewed unknown identifiers to an existing active substance."""

    def __init__(self, repository=None, connection_factory: Callable = get_connection,
                 clock=lambda: datetime.now(timezone.utc)):
        self.repository = repository or PostgresSubstanceRegistryMutationRepository()
        self.connection_factory = connection_factory
        self.clock = clock

    def materialize_decision(self, decision_id, materialized_by, provenance=None):
        actor = materialized_by.strip() if materialized_by else ""
        if not actor:
            raise SubstanceRegistryMaterializationError(
                "materializer_required", "materialized_by is required"
            )
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                decision = self.repository.load_decision_candidate_for_update(cursor, decision_id)
                if decision is None:
                    raise SubstanceRegistryMaterializationError(
                        "decision_not_found", "Decision not found"
                    )
                existing_materialization = self.repository.get_materialization(cursor, decision_id)
                if existing_materialization is not None:
                    connection.commit()
                    return dict(existing_materialization)
                namespace,observed=self._validate_common(cursor,decision)
                if decision["decision_type"]=="associate_existing":
                    materialization=self._materialize_existing(cursor,decision,namespace,observed,actor,provenance)
                elif decision["decision_type"]=="create_new_substance":
                    materialization=self._materialize_new(cursor,decision,namespace,observed,actor,provenance)
                else:
                    raise SubstanceRegistryMaterializationError("decision_not_materializable","Decision type is not materializable")
            connection.commit()
            return dict(materialization)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _validate_common(self,cursor,decision):
        if decision["candidate_kind"] != "unknown_identifier":
            raise SubstanceRegistryMaterializationError("candidate_kind_not_materializable","Only unknown_identifier candidates are supported")
        if decision["namespace_id"] is None or not decision["normalized_value"]:
            raise SubstanceRegistryMaterializationError("candidate_identity_incomplete","Known namespace and normalized value are required")
        if len(decision["normalized_value"])>255:
            raise SubstanceRegistryMaterializationError("candidate_identity_invalid","Normalized identifier exceeds registry limit")
        namespace=self.repository.load_namespace(cursor,decision["namespace_id"])
        if namespace is None or namespace["namespace_key"]!=decision["namespace_key"] or namespace["namespace_version"]!=decision["namespace_version"]:
            raise SubstanceRegistryMaterializationError("namespace_not_eligible","Candidate namespace is missing or inconsistent")
        observed=self.repository.observed_raw_value(cursor,decision["candidate_id"],decision["namespace_key"],decision["namespace_version"],decision["normalized_value"])
        if observed is None or len(observed["raw_value"])>255:
            raise SubstanceRegistryMaterializationError("raw_value_unavailable","A valid matching raw identifier is required")
        return namespace,observed

    def _materialize_existing(self,cursor,decision,namespace,observed,actor,provenance):
        if decision["candidate_status"]!="resolved_existing":
            raise SubstanceRegistryMaterializationError("candidate_not_materializable","Candidate is not resolved_existing")
        target=self.repository.load_active_target(cursor,decision["target_substance_id"])
        if target is None or target["status"]!="active":
            raise SubstanceRegistryMaterializationError("target_not_eligible","Target substance must exist and be active")
        identifier=self.repository.lookup_identifier(cursor,decision["namespace_id"],decision["normalized_value"])
        status="already_present"
        if identifier is None:
            identifier=self.repository.create_verified_identifier(
                cursor,substance_id=decision["target_substance_id"],namespace_id=decision["namespace_id"],
                identifier_system=self._legacy_system(namespace),raw_value=observed["raw_value"],
                normalized_value=decision["normalized_value"],provenance=self._identifier_provenance(decision,namespace,"associate_existing"))
            if identifier is None: identifier=self.repository.lookup_identifier(cursor,decision["namespace_id"],decision["normalized_value"])
            else: status="applied"
        self._validate_compatible_identifier(identifier,decision["target_substance_id"])
        return self.repository.create_materialization(
            cursor,decision=decision,target_substance_id=decision["target_substance_id"],identifier_id=identifier["id"],
            mutation_type="associate_existing_identifier",status=status,materialized_by=actor,
            materialized_at=self.clock(),provenance=provenance)

    def _materialize_new(self,cursor,decision,namespace,observed,actor,provenance):
        if decision["candidate_status"]!="resolved_new":
            raise SubstanceRegistryMaterializationError("candidate_not_materializable","Candidate is not resolved_new")
        if any(not decision[key] for key in ("proposed_preferred_name","proposed_normalized_name","proposed_substance_type")):
            raise SubstanceRegistryMaterializationError("creation_payload_invalid","Reviewed creation payload is incomplete")
        if self.repository.lookup_identifier(cursor,decision["namespace_id"],decision["normalized_value"]) is not None:
            raise SubstanceRegistryMaterializationError("identifier_creation_stale","Scientific identifier now exists; decision requires new review")
        substance=self.repository.create_substance(cursor,decision["proposed_preferred_name"],decision["proposed_normalized_name"],decision["proposed_substance_type"])
        identifier=self.repository.create_verified_identifier(
            cursor,substance_id=substance["id"],namespace_id=decision["namespace_id"],
            identifier_system=self._legacy_system(namespace),raw_value=observed["raw_value"],
            normalized_value=decision["normalized_value"],is_primary=True,
            provenance=self._identifier_provenance(decision,namespace,"create_new_substance"))
        if identifier is None:
            raise SubstanceRegistryMaterializationError("identifier_creation_conflict","Scientific identifier was concurrently claimed")
        return self.repository.create_materialization(
            cursor,decision=decision,target_substance_id=substance["id"],identifier_id=identifier["id"],
            mutation_type="create_new_substance",status="applied",materialized_by=actor,
            materialized_at=self.clock(),provenance=provenance)

    @staticmethod
    def _validate_compatible_identifier(identifier, target_substance_id):
        if identifier is None:
            raise SubstanceRegistryMaterializationError("identifier_creation_conflict","Identifier could not be created or reloaded")
        if identifier["substance_id"] != target_substance_id:
            raise SubstanceRegistryMaterializationError("identifier_owner_conflict","Identifier belongs to another substance")
        if identifier["verification_status"] != "verified":
            raise SubstanceRegistryMaterializationError("identifier_status_conflict","Existing identifier is not verified")

    @staticmethod
    def _identifier_provenance(decision,namespace,mutation_type):
        return {"origin":"substance_resolution_materialization","mutation_type":mutation_type,
                "candidate_id":decision["candidate_id"],"decision_id":decision["decision_id"],
                "namespace_key":namespace["namespace_key"],"namespace_version":namespace["namespace_version"]}

    @staticmethod
    def _legacy_system(namespace):
        semantic = f'{namespace["namespace_key"]}:{namespace["namespace_version"]}'
        return "namespace_" + sha256(semantic.encode("utf-8")).hexdigest()[:40]
