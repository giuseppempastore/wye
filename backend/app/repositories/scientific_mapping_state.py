"""Caller-owned PostgreSQL access for canonical target and mapping-state runtime."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True)
class MappingHistoryRows:
    bridges: tuple[dict[str, Any], ...]
    proposals: tuple[dict[str, Any], ...]
    decisions: tuple[dict[str, Any], ...]
    materializations: tuple[dict[str, Any], ...]
    closures: tuple[dict[str, Any], ...]


def _record(cursor, row) -> dict[str, Any] | None:
    if row is None:
        return None
    value = {column.name: item for column, item in zip(cursor.description, row)}
    for key in tuple(value):
        if key.endswith("_json"):
            target = key[:-5]
            value[target] = (
                None
                if value[key] is None
                else json.loads(value[key], parse_float=Decimal)
            )
            del value[key]
    return value


def _records(cursor) -> tuple[dict[str, Any], ...]:
    return tuple(_record(cursor, row) for row in cursor.fetchall())


class PostgresScientificMappingStateRepository:
    """Load frozen inputs without committing or rolling back the caller."""

    def load_target(self, cursor, target_type: str, target_id: int) -> dict[str, Any] | None:
        if target_type == "ingredient":
            cursor.execute(
                "SELECT id,canonical_name,common_name,ingredient_group,status,"
                "cas_number,einecs_number,created_at,updated_at FROM ingredients "
                "WHERE id=%s FOR SHARE",
                (target_id,),
            )
        elif target_type == "substance":
            cursor.execute(
                "SELECT id,preferred_name,normalized_name,scientific_name,"
                "substance_type,status,created_at,updated_at FROM substances "
                "WHERE id=%s FOR SHARE",
                (target_id,),
            )
        else:
            return None
        return _record(cursor, cursor.fetchone())

    def lock_mapping_history(self, cursor) -> None:
        # SHARE conflicts with Phase 6 RowExclusive writes. It produces one
        # stable recorded-time view while still allowing concurrent readers and
        # content-addressed artifact writers.
        cursor.execute(
            "LOCK TABLE ingredient_substances,"
            "ingredient_substance_mapping_proposals,"
            "ingredient_substance_mapping_decisions,"
            "ingredient_substance_mapping_materializations,"
            "ingredient_substance_mapping_closures IN SHARE MODE"
        )

    def load_mapping_history(self, cursor, ingredient_id: int) -> MappingHistoryRows:
        cursor.execute(
            "SELECT id,ingredient_id,substance_id,relationship_type,mapping_method,"
            "mapping_status,mapping_confidence,source_dataset_release_id,"
            "ingestion_run_id,provenance::text AS provenance_json,reviewed_by,"
            "reviewed_at,valid_from,valid_to,created_at FROM ingredient_substances "
            "WHERE ingredient_id=%s ORDER BY id",
            (ingredient_id,),
        )
        bridges = _records(cursor)

        cursor.execute(
            "SELECT id,proposal_key,ingredient_id,substance_id,relationship_type,"
            "mapping_method,mapping_confidence,source_dataset_release_id,"
            "ingestion_run_id,proposed_by,proposal_status,"
            "provenance::text AS provenance_json,created_at "
            "FROM ingredient_substance_mapping_proposals WHERE ingredient_id=%s "
            "ORDER BY id",
            (ingredient_id,),
        )
        proposals = _records(cursor)

        cursor.execute(
            "SELECT d.id,d.proposal_id,d.decision_type,d.effective_from,"
            "d.reviewed_by,d.reviewed_at,d.reason_code,"
            "d.provenance::text AS provenance_json,d.created_at "
            "FROM ingredient_substance_mapping_decisions d "
            "JOIN ingredient_substance_mapping_proposals p ON p.id=d.proposal_id "
            "WHERE p.ingredient_id=%s ORDER BY d.id",
            (ingredient_id,),
        )
        decisions = _records(cursor)

        cursor.execute(
            "SELECT DISTINCT m.id,m.decision_id,m.proposal_id,"
            "m.ingredient_substance_id,m.materialization_status,m.materialized_by,"
            "m.materialized_at,m.provenance::text AS provenance_json,m.created_at "
            "FROM ingredient_substance_mapping_materializations m "
            "JOIN ingredient_substance_mapping_proposals p ON p.id=m.proposal_id "
            "JOIN ingredient_substances b ON b.id=m.ingredient_substance_id "
            "LEFT JOIN ingredient_substance_mapping_decisions d ON d.id=m.decision_id "
            "LEFT JOIN ingredient_substance_mapping_proposals dp ON dp.id=d.proposal_id "
            "WHERE p.ingredient_id=%s OR b.ingredient_id=%s OR dp.ingredient_id=%s "
            "ORDER BY m.id",
            (ingredient_id, ingredient_id, ingredient_id),
        )
        materializations = _records(cursor)

        cursor.execute(
            "SELECT c.id,c.ingredient_substance_id,c.valid_to,c.closed_by,c.closed_at,"
            "c.reason_code,c.provenance::text AS provenance_json,c.created_at "
            "FROM ingredient_substance_mapping_closures c "
            "JOIN ingredient_substances b ON b.id=c.ingredient_substance_id "
            "WHERE b.ingredient_id=%s ORDER BY c.id",
            (ingredient_id,),
        )
        closures = _records(cursor)
        return MappingHistoryRows(bridges, proposals, decisions, materializations, closures)

    def load_snapshot_prerequisite(self, cursor, snapshot_id: int) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT id,status,snapshot_digest FROM scientific_evidence_snapshots "
            "WHERE id=%s FOR SHARE",
            (snapshot_id,),
        )
        return _record(cursor, cursor.fetchone())

    def load_protocol_prerequisite(
        self, cursor, protocol_version_id: int
    ) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT id,lifecycle_status,published_at,protocol_digest "
            "FROM scientific_evaluation_protocol_versions WHERE id=%s FOR SHARE",
            (protocol_version_id,),
        )
        return _record(cursor, cursor.fetchone())
