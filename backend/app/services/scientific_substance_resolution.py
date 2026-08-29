"""Namespace-aware, read-only resolution against the scientific substance registry."""

from typing import Callable

import psycopg2.extras

from app.db import get_connection
from app.repositories.substance_registry import PostgresSubstanceRegistryRepository
from app.scientific_ingestion.resolution import (
    ScientificSubstanceResolution,
    SubstanceIdentifierResolutionDiagnostic,
)


class PostgresScientificSubstanceResolver:
    """Resolve only verified namespace/value identities; names are never authority."""

    def __init__(self, repository=None, connection_factory: Callable = get_connection):
        self.repository = repository or PostgresSubstanceRegistryRepository()
        self.connection_factory = connection_factory

    def resolve(self, record):
        identifiers = self._deduplicate(record.substance_identifiers)
        connection = self.connection_factory()
        try:
            connection.set_session(readonly=True)
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                lookups = self.repository.lookup_identifiers(cursor, identifiers)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        diagnostics = tuple(self._diagnostic(row) for row in lookups)
        deprecated = {row.substance_id for row in lookups
                      if row.identifier_status == "verified" and row.substance_status == "deprecated"}
        review_pending = {row.substance_id for row in lookups
                          if row.identifier_status == "verified" and row.substance_status == "review_pending"}
        active = {row.substance_id for row in lookups
                  if row.identifier_status == "verified" and row.substance_status == "active"}
        if deprecated:
            return ScientificSubstanceResolution(
                status="rejected", reason_code="deprecated_substance",
                diagnostics=diagnostics,
                conflicting_substance_ids=tuple(sorted(deprecated | review_pending | active)),
            )
        if review_pending:
            return ScientificSubstanceResolution(
                status="ambiguous", reason_code="inactive_substance",
                diagnostics=diagnostics,
                conflicting_substance_ids=tuple(sorted(review_pending | active)),
            )
        if len(active) > 1:
            return ScientificSubstanceResolution(
                status="ambiguous", reason_code="conflicting_identifier_matches",
                diagnostics=diagnostics,
                conflicting_substance_ids=tuple(sorted(active)),
            )
        if len(active) == 1:
            return ScientificSubstanceResolution.resolved(
                record, next(iter(active)), diagnostics=diagnostics
            ).model_copy(update={"reason_code": "verified_match"})
        reason = "unknown_namespace" if lookups and all(
            row.namespace_id is None for row in lookups
        ) else "no_verified_identifier_match"
        return ScientificSubstanceResolution(
            status="unresolved", reason_code=reason, diagnostics=diagnostics
        )

    @staticmethod
    def _deduplicate(identifiers):
        unique = {}
        for identifier in identifiers:
            key = (
                identifier.namespace_key,
                identifier.namespace_version,
                identifier.normalized_value,
            )
            unique.setdefault(key, identifier)
        return tuple(unique.values())

    @staticmethod
    def _diagnostic(row):
        if row.namespace_id is None:
            outcome = "unknown_namespace"
        elif row.identifier_id is None:
            outcome = "unmatched"
        elif row.identifier_status != "verified":
            outcome = "ignored_identifier_status"
        elif row.substance_status == "active":
            outcome = "matched"
        elif row.substance_status == "deprecated":
            outcome = "deprecated_substance"
        else:
            outcome = "inactive_substance"
        return SubstanceIdentifierResolutionDiagnostic(
            namespace_key=row.namespace_key,
            namespace_version=row.namespace_version,
            normalized_value=row.normalized_value,
            outcome=outcome,
            namespace_id=row.namespace_id,
            identifier_id=row.identifier_id,
            identifier_status=row.identifier_status,
            substance_id=row.substance_id,
            substance_status=row.substance_status,
        )
