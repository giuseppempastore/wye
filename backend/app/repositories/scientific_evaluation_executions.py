"""Caller-owned PostgreSQL access for Phase 7.6.4C execution persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _record(cursor, row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {column.name: value for column, value in zip(cursor.description, row)}


def _records(cursor) -> tuple[dict[str, Any], ...]:
    return tuple(_record(cursor, row) for row in cursor.fetchall())


class PostgresScientificEvaluationExecutionRepository:
    """Execute bounded SQL without committing or rolling back the caller."""

    def load_protocol(self, cursor, protocol_version_id: int) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT id,lifecycle_status,published_at,protocol_digest "
            "FROM scientific_evaluation_protocol_versions WHERE id=%s FOR SHARE",
            (protocol_version_id,),
        )
        return _record(cursor, cursor.fetchone())

    def load_snapshot(self, cursor, snapshot_id: int) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT id,status,snapshot_digest,member_count FROM scientific_evidence_snapshots "
            "WHERE id=%s FOR SHARE",
            (snapshot_id,),
        )
        return _record(cursor, cursor.fetchone())

    def load_artifact(self, cursor, artifact_id: int) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT id,artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,json_payload FROM scientific_evaluation_artifacts WHERE id=%s FOR SHARE",
            (artifact_id,),
        )
        return _record(cursor, cursor.fetchone())

    def load_execution(self, cursor, execution_id: int, *, lock: bool = False) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT * FROM scientific_evaluation_executions WHERE id=%s" + (
                " FOR UPDATE" if lock else ""
            ),
            (execution_id,),
        )
        return _record(cursor, cursor.fetchone())

    def load_execution_by_digest(
        self, cursor, semantic_digest: bytes, *, lock: bool = False
    ) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT * FROM scientific_evaluation_executions WHERE semantic_execution_digest=%s"
            + (" FOR UPDATE" if lock else ""),
            (semantic_digest,),
        )
        return _record(cursor, cursor.fetchone())

    def insert_execution(self, cursor, values: dict[str, Any]) -> dict[str, Any] | None:
        cursor.execute(
            "INSERT INTO scientific_evaluation_executions("
            "execution_key,protocol_version_id,evidence_snapshot_id,target_type,substance_id,ingredient_id,"
            "target_artifact_id,mapping_state_artifact_id,input_artifact_id,configuration_artifact_id,"
            "semantic_identity_artifact_id,comparison_execution_id,execution_mode,protocol_digest,"
            "evidence_snapshot_digest,input_digest,configuration_digest,semantic_execution_digest,"
            "requested_by,requested_at) VALUES("
            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) "
            "ON CONFLICT(semantic_execution_digest) DO NOTHING RETURNING *",
            (
                values["execution_key"],
                values["protocol_version_id"],
                values["evidence_snapshot_id"],
                values["target_type"],
                values["substance_id"],
                values["ingredient_id"],
                values["target_artifact_id"],
                values["mapping_state_artifact_id"],
                values["input_artifact_id"],
                values["configuration_artifact_id"],
                values["semantic_identity_artifact_id"],
                values["comparison_execution_id"],
                values["execution_mode"],
                values["protocol_digest"],
                values["evidence_snapshot_digest"],
                values["input_digest"],
                values["configuration_digest"],
                values["semantic_execution_digest"],
                values["requested_by"],
            ),
        )
        return _record(cursor, cursor.fetchone())

    def load_idempotency(self, cursor, scope: str, key: str) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT * FROM scientific_evaluation_idempotency_keys "
            "WHERE operation_type='create_execution' AND request_scope=%s AND request_key=%s "
            "FOR UPDATE",
            (scope, key),
        )
        return _record(cursor, cursor.fetchone())

    def insert_idempotency(
        self, cursor, *, scope: str, key: str, semantic_digest: bytes, execution_id: int
    ) -> dict[str, Any] | None:
        cursor.execute(
            "INSERT INTO scientific_evaluation_idempotency_keys("
            "operation_type,request_scope,request_key,expected_semantic_digest,execution_id) "
            "VALUES('create_execution',%s,%s,%s,%s) "
            "ON CONFLICT(operation_type,request_scope,request_key) DO NOTHING RETURNING *",
            (scope, key, semantic_digest, execution_id),
        )
        return _record(cursor, cursor.fetchone())

    def next_attempt_number(self, cursor, execution_id: int) -> int:
        cursor.execute(
            "SELECT COALESCE(MAX(attempt_number),0)+1 "
            "FROM scientific_evaluation_execution_attempts WHERE execution_id=%s",
            (execution_id,),
        )
        return cursor.fetchone()[0]

    def load_latest_attempt(self, cursor, execution_id: int) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT * FROM scientific_evaluation_execution_attempts WHERE execution_id=%s "
            "ORDER BY attempt_number DESC LIMIT 1 FOR UPDATE",
            (execution_id,),
        )
        return _record(cursor, cursor.fetchone())

    def insert_attempt(self, cursor, values: dict[str, Any]) -> dict[str, Any]:
        cursor.execute(
            "INSERT INTO scientific_evaluation_execution_attempts("
            "attempt_key,execution_id,attempt_number,engine_build_artifact_id,worker_id,lease_token,"
            "lease_expires_at,heartbeat_at,started_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NOW()) RETURNING *",
            (
                values["attempt_key"],
                values["execution_id"],
                values["attempt_number"],
                values["engine_build_artifact_id"],
                values["worker_id"],
                values["lease_token"],
                values["lease_expires_at"],
                values["heartbeat_at"],
            ),
        )
        return _record(cursor, cursor.fetchone())

    def load_attempt(self, cursor, attempt_id: int, *, lock: bool = False) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT * FROM scientific_evaluation_execution_attempts WHERE id=%s"
            + (" FOR UPDATE" if lock else ""),
            (attempt_id,),
        )
        return _record(cursor, cursor.fetchone())

    def transition_execution(
        self, cursor, execution_id: int, status: str, *, completed: bool = False
    ) -> None:
        if status == "running":
            cursor.execute(
                "UPDATE scientific_evaluation_executions SET technical_status='running',"
                "started_at=COALESCE(started_at,NOW()) WHERE id=%s",
                (execution_id,),
            )
        elif status == "pending":
            cursor.execute(
                "UPDATE scientific_evaluation_executions SET technical_status='pending',completed_at=NULL "
                "WHERE id=%s",
                (execution_id,),
            )
        elif completed:
            cursor.execute(
                "UPDATE scientific_evaluation_executions SET technical_status=%s,completed_at=NOW() "
                "WHERE id=%s",
                (status, execution_id),
            )
        else:
            cursor.execute(
                "UPDATE scientific_evaluation_executions SET technical_status=%s WHERE id=%s",
                (status, execution_id),
            )

    def heartbeat_attempt(
        self,
        cursor,
        *,
        attempt_id: int,
        lease_token: str,
        heartbeat_at: datetime,
        lease_expires_at: datetime,
    ) -> dict[str, Any] | None:
        cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET heartbeat_at=%s,lease_expires_at=%s "
            "WHERE id=%s AND attempt_status='running' AND lease_token=%s "
            "AND heartbeat_at<=%s AND lease_expires_at<=%s RETURNING *",
            (
                heartbeat_at,
                lease_expires_at,
                attempt_id,
                lease_token,
                heartbeat_at,
                lease_expires_at,
            ),
        )
        return _record(cursor, cursor.fetchone())

    def close_attempt(
        self,
        cursor,
        *,
        attempt_id: int,
        status: str,
        error_category: str | None = None,
        error_code: str | None = None,
        retryable: bool | None = None,
        error_artifact_id: int | None = None,
    ) -> dict[str, Any] | None:
        cursor.execute(
            "UPDATE scientific_evaluation_execution_attempts SET attempt_status=%s,ended_at=NOW(),"
            "lease_token=NULL,lease_expires_at=NULL,heartbeat_at=NULL,error_category=%s,error_code=%s,"
            "retryable=%s,error_artifact_id=%s WHERE id=%s AND attempt_status='running' RETURNING *",
            (status, error_category, error_code, retryable, error_artifact_id, attempt_id),
        )
        return _record(cursor, cursor.fetchone())

    def load_snapshot_members(self, cursor, snapshot_id: int) -> tuple[dict[str, Any], ...]:
        cursor.execute(
            "SELECT id,member_kind,member_identity_digest,member_semantic_digest,membership_ordinal "
            "FROM scientific_evidence_snapshot_members WHERE snapshot_id=%s "
            "ORDER BY membership_ordinal,id FOR SHARE",
            (snapshot_id,),
        )
        return _records(cursor)

    def insert_selection_decision(self, cursor, values: dict[str, Any]) -> int:
        cursor.execute(
            "INSERT INTO scientific_evidence_selection_decisions("
            "execution_id,snapshot_member_id,decision,selection_role,resolution_state,reason_namespace,"
            "reason_version,primary_reason_code,decision_artifact_id,decision_digest) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (
                values["execution_id"], values["snapshot_member_id"], values["decision"],
                values["selection_role"], values["resolution_state"], values["reason_namespace"],
                values["reason_version"], values["primary_reason_code"],
                values["decision_artifact_id"], values["decision_digest"],
            ),
        )
        return cursor.fetchone()[0]

    def insert_result(self, cursor, values: dict[str, Any]) -> int:
        cursor.execute(
            "INSERT INTO scientific_evaluation_results("
            "result_key,execution_id,result_kind,result_schema_version,scientific_status_namespace,"
            "scientific_status_version,scientific_status_code,canonical_artifact_id,result_digest) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            tuple(values[key] for key in (
                "result_key", "execution_id", "result_kind", "result_schema_version",
                "scientific_status_namespace", "scientific_status_version",
                "scientific_status_code", "canonical_artifact_id", "result_digest",
            )),
        )
        return cursor.fetchone()[0]

    def insert_component(self, cursor, values: dict[str, Any]) -> int:
        cursor.execute(
            "INSERT INTO scientific_evaluation_result_components("
            "result_id,component_kind,component_schema_version,component_role,component_artifact_id,"
            "component_digest,component_ordinal) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            tuple(values[key] for key in (
                "result_id", "component_kind", "component_schema_version", "component_role",
                "component_artifact_id", "component_digest", "component_ordinal",
            )),
        )
        return cursor.fetchone()[0]

    def insert_trace(self, cursor, values: dict[str, Any]) -> int:
        cursor.execute(
            "INSERT INTO scientific_evaluation_traces("
            "trace_key,execution_id,result_id,trace_schema_version,canonical_artifact_id,trace_digest,"
            "result_digest,selection_digest,protocol_digest,evidence_snapshot_digest,input_digest) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            tuple(values[key] for key in (
                "trace_key", "execution_id", "result_id", "trace_schema_version",
                "canonical_artifact_id", "trace_digest", "result_digest", "selection_digest",
                "protocol_digest", "evidence_snapshot_digest", "input_digest",
            )),
        )
        return cursor.fetchone()[0]

    def insert_publication(self, cursor, values: dict[str, Any]) -> dict[str, Any]:
        cursor.execute(
            "INSERT INTO scientific_evaluation_publications("
            "publication_key,execution_id,result_id,trace_id,successful_attempt_id,"
            "selection_manifest_artifact_id,bundle_artifact_id,selection_digest,result_digest,"
            "trace_digest,publication_bundle_digest,published_by,published_at) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) RETURNING *",
            tuple(values[key] for key in (
                "publication_key", "execution_id", "result_id", "trace_id", "successful_attempt_id",
                "selection_manifest_artifact_id", "bundle_artifact_id", "selection_digest",
                "result_digest", "trace_digest", "publication_bundle_digest", "published_by",
            )),
        )
        return _record(cursor, cursor.fetchone())

    def load_publication(self, cursor, execution_id: int) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT p.*,r.canonical_artifact_id AS result_artifact_id,"
            "t.canonical_artifact_id AS trace_artifact_id "
            "FROM scientific_evaluation_publications p "
            "JOIN scientific_evaluation_results r ON r.id=p.result_id "
            "JOIN scientific_evaluation_traces t ON t.id=p.trace_id "
            "WHERE p.execution_id=%s FOR SHARE OF p,r,t",
            (execution_id,),
        )
        return _record(cursor, cursor.fetchone())

    def load_comparison_publication(self, cursor, execution_id: int) -> dict[str, Any] | None:
        return self.load_publication(cursor, execution_id)

    def insert_replay_verification(self, cursor, values: dict[str, Any]) -> dict[str, Any]:
        keys = (
            "verification_key", "execution_id", "comparison_publication_id", "successful_attempt_id",
            "verification_artifact_id", "verification_digest", "expected_publication_bundle_digest",
            "expected_selection_digest", "expected_result_digest", "expected_trace_digest",
            "recomputed_selection_artifact_id", "recomputed_result_artifact_id",
            "recomputed_trace_artifact_id", "recomputed_selection_digest",
            "recomputed_result_digest", "recomputed_trace_digest", "verification_status",
        )
        cursor.execute(
            "INSERT INTO scientific_evaluation_replay_verifications("
            + ",".join(keys)
            + ") VALUES("
            + ",".join(["%s"] * len(keys))
            + ") RETURNING *",
            tuple(values[key] for key in keys),
        )
        return _record(cursor, cursor.fetchone())

    def load_replay_verification(self, cursor, execution_id: int) -> dict[str, Any] | None:
        cursor.execute(
            "SELECT * FROM scientific_evaluation_replay_verifications WHERE execution_id=%s FOR SHARE",
            (execution_id,),
        )
        return _record(cursor, cursor.fetchone())
