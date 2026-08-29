"""Provider-neutral persistent batch orchestration for scientific ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import logging
import time
from typing import Any, Callable
from uuid import UUID, uuid4

import psycopg2.extras

from app.db import get_connection
from app.scientific_ingestion.canonicalization import canonical_sha256
from app.scientific_ingestion.errors import (
    ScientificAcquisitionError,
    ScientificParserError,
    ScientificPersistenceConflict,
    ScientificRecordValidationError,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScientificBatchWorkIdentity:
    source_key: str
    dataset_key: str
    external_release_key: str
    artifact_keys: tuple[str, ...]
    source_adapter_version: str
    acquisition_version: str
    parser_version: str
    normalization_schema_version: str
    config_fingerprint: str

    def __post_init__(self):
        scalar_values = (
            self.source_key, self.dataset_key, self.external_release_key,
            self.source_adapter_version, self.acquisition_version,
            self.parser_version, self.normalization_schema_version,
            self.config_fingerprint,
        )
        if any(not isinstance(value, str) or not value.strip() for value in scalar_values):
            raise ValueError("scientific batch work identity fields must be non-empty")
        if (not self.artifact_keys or len(self.artifact_keys) != len(set(self.artifact_keys))
                or any(not isinstance(value, str) or not value.strip()
                       for value in self.artifact_keys)):
            raise ValueError("scientific batch artifact selection must be non-empty and unique")
        if len(self.config_fingerprint) != 64 or any(
            char not in "0123456789abcdef" for char in self.config_fingerprint
        ):
            raise ValueError("scientific batch config fingerprint must be sha256")

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_key": self.source_key,
            "dataset_key": self.dataset_key,
            "external_release_key": self.external_release_key,
            "artifact_keys": sorted(self.artifact_keys),
            "source_adapter_version": self.source_adapter_version,
            "acquisition_version": self.acquisition_version,
            "parser_version": self.parser_version,
            "normalization_schema_version": self.normalization_schema_version,
            "config_fingerprint": self.config_fingerprint,
        }

    @property
    def work_key(self) -> str:
        return canonical_sha256({"scientific_batch_work_identity_v1": self.as_dict()})


@dataclass(frozen=True)
class ScientificBatchArtifactResult:
    manifest_fingerprint: str
    created: bool
    payload: Any = None

    def __post_init__(self):
        if len(self.manifest_fingerprint) != 64 or any(
            char not in "0123456789abcdef" for char in self.manifest_fingerprint
        ):
            raise ValueError("artifact manifest fingerprint must be sha256")


@dataclass(frozen=True)
class ScientificBatchExecutionOutcome:
    ingestion_run_id: int
    records_processed: int
    assessments_created: int
    findings_created: int
    assessments_reused: int = 0
    findings_reused: int = 0

    def __post_init__(self):
        if self.ingestion_run_id <= 0 or any(value < 0 for value in (
            self.records_processed, self.assessments_created, self.findings_created,
            self.assessments_reused, self.findings_reused,
        )):
            raise ValueError("batch execution outcome contains invalid counters")


@dataclass(frozen=True)
class ScientificBatchFailure(Exception):
    category: str
    detail: str
    retryable: bool = False
    ingestion_run_id: int | None = None

    def __str__(self):
        return self.detail


@dataclass(frozen=True)
class ScientificBatchWorkItem:
    identity: ScientificBatchWorkIdentity
    acquire: Callable[[], ScientificBatchArtifactResult]
    ingest: Callable[[ScientificBatchArtifactResult, str], ScientificBatchExecutionOutcome]
    max_attempts: int = 2

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("batch work item max_attempts must be positive")


@dataclass(frozen=True)
class ScientificBatchPlan:
    items: tuple[ScientificBatchWorkItem, ...]
    plan_key: str = field(init=False)
    definition: dict[str, Any] = field(init=False)

    def __post_init__(self):
        if not self.items:
            raise ValueError("scientific batch plan must contain work")
        keys = [item.identity.work_key for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("scientific batch plan contains duplicate work identity")
        definition = {
            "schema": "scientific_batch_plan_v1",
            "items": sorted(
                ({"identity": item.identity.as_dict(), "max_attempts": item.max_attempts}
                 for item in self.items),
                key=lambda value: canonical_sha256(value),
            ),
        }
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "plan_key", canonical_sha256(definition))


@dataclass(frozen=True)
class ScientificBatchWorkResult:
    work_key: str
    provider: str
    state: str
    attempt: int
    error_class: str | None = None
    error_detail: str | None = None
    artifact_created: bool = False
    artifact_reused: bool = False
    records_processed: int = 0
    assessments_created: int = 0
    assessments_reused: int = 0
    findings_created: int = 0
    findings_reused: int = 0
    ingestion_run_id: int | None = None


@dataclass(frozen=True)
class ScientificBatchSummary:
    plan_key: str
    execution_key: UUID
    results: tuple[ScientificBatchWorkResult, ...]
    elapsed_seconds: float

    @property
    def counters(self) -> dict[str, int | float]:
        return {
            "items_total": len(self.results),
            "items_completed": sum(item.state == "completed" for item in self.results),
            "items_failed": sum(item.state == "failed" for item in self.results),
            "items_retryable": sum(item.state == "retryable" for item in self.results),
            "items_conflicted": sum(item.state == "conflict" for item in self.results),
            "items_reused": sum(item.state == "already_completed" for item in self.results),
            "artifacts_created": sum(item.artifact_created for item in self.results),
            "artifacts_reused": sum(item.artifact_reused for item in self.results),
            "assessments_created": sum(item.assessments_created for item in self.results),
            "assessments_reused": sum(item.assessments_reused for item in self.results),
            "findings_created": sum(item.findings_created for item in self.results),
            "findings_reused": sum(item.findings_reused for item in self.results),
            "elapsed_seconds": self.elapsed_seconds,
        }


class ScientificBatchIngestionService:
    """Persist plans, lease independent work, and resume safely after restart."""

    def __init__(self, *, connection_factory=get_connection,
                 clock=lambda: datetime.now(timezone.utc), monotonic=time.monotonic,
                 lease_seconds=60, execution_key_factory=uuid4):
        if lease_seconds <= 0:
            raise ValueError("batch lease must be bounded and positive")
        self.connection_factory = connection_factory
        self.clock = clock
        self.monotonic = monotonic
        self.lease_seconds = lease_seconds
        self.execution_key_factory = execution_key_factory

    def execute(self, plan: ScientificBatchPlan) -> ScientificBatchSummary:
        started = self.monotonic()
        execution_key = self.execution_key_factory()
        plan_id = self._ensure_plan(plan)
        results = tuple(
            self._execute_item(plan_id, item, execution_key) for item in plan.items
        )
        return ScientificBatchSummary(
            plan.plan_key, execution_key, results,
            max(0.0, self.monotonic() - started),
        )

    def history(self, plan_key: str) -> tuple[dict[str, Any], ...]:
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT item.work_key,item.source_key,item.dataset_key,
                           item.external_release_key,item.work_status,item.attempt_count,
                           attempt.attempt_number,attempt.execution_key,
                           attempt.attempt_status,attempt.error_class,
                           attempt.error_detail,attempt.started_at,attempt.completed_at
                    FROM scientific_batch_plans plan
                    JOIN scientific_batch_work_items item ON item.batch_plan_id=plan.id
                    LEFT JOIN scientific_batch_work_attempts attempt
                      ON attempt.work_item_id=item.id
                    WHERE plan.plan_key=%s
                    ORDER BY item.work_key,attempt.attempt_number
                """, (plan_key,))
                return tuple(dict(row) for row in cursor.fetchall())
        finally:
            connection.close()

    def _ensure_plan(self, plan):
        checksum = canonical_sha256(plan.definition)
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO scientific_batch_plans(
                      plan_key,definition_checksum_value,plan_definition)
                    VALUES(%s,%s,%s) ON CONFLICT(plan_key) DO NOTHING
                """, (plan.plan_key, checksum, psycopg2.extras.Json(plan.definition)))
                cursor.execute("""
                    SELECT id,definition_checksum_value,plan_definition
                    FROM scientific_batch_plans WHERE plan_key=%s FOR SHARE
                """, (plan.plan_key,))
                row = cursor.fetchone()
                if (row is None or row["definition_checksum_value"] != checksum
                        or row["plan_definition"] != plan.definition):
                    raise ScientificPersistenceConflict("batch plan identity conflict")
                for item in plan.items:
                    identity = item.identity
                    cursor.execute("""
                        INSERT INTO scientific_batch_work_items(
                          batch_plan_id,work_key,source_key,dataset_key,
                          external_release_key,artifact_keys,source_adapter_version,
                          acquisition_version,parser_version,normalization_schema_version,
                          config_fingerprint,work_identity,max_attempts)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(batch_plan_id,work_key) DO NOTHING
                    """, (
                        row["id"], identity.work_key, identity.source_key,
                        identity.dataset_key, identity.external_release_key,
                        psycopg2.extras.Json(sorted(identity.artifact_keys)),
                        identity.source_adapter_version,
                        identity.acquisition_version, identity.parser_version,
                        identity.normalization_schema_version,
                        identity.config_fingerprint,
                        psycopg2.extras.Json(identity.as_dict()), item.max_attempts,
                    ))
                    cursor.execute("""
                        SELECT work_identity,max_attempts FROM scientific_batch_work_items
                        WHERE batch_plan_id=%s AND work_key=%s
                    """, (row["id"], identity.work_key))
                    existing = cursor.fetchone()
                    if (existing["work_identity"] != identity.as_dict()
                            or existing["max_attempts"] != item.max_attempts):
                        raise ScientificPersistenceConflict("batch work identity conflict")
            connection.commit()
            return row["id"]
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _execute_item(self, plan_id, item, batch_execution_key):
        claim = self._claim(plan_id, item.identity.work_key)
        if claim["action"] != "execute":
            return self._existing_result(item.identity, claim)
        work_id = claim["id"]
        attempt = claim["attempt_count"]
        lease_token = claim["lease_token"]
        artifact = None
        item_started = self.monotonic()
        self._log(item.identity, batch_execution_key, attempt, "running")
        try:
            artifact = item.acquire()
            self._checkpoint_artifact(work_id, attempt, lease_token, artifact)
            idempotency_key = f"batch:{item.identity.work_key}:attempt:{attempt}"
            outcome = item.ingest(artifact, idempotency_key)
            result = ScientificBatchWorkResult(
                item.identity.work_key, item.identity.source_key, "completed", attempt,
                artifact_created=artifact.created,
                artifact_reused=not artifact.created,
                records_processed=outcome.records_processed,
                assessments_created=outcome.assessments_created,
                assessments_reused=outcome.assessments_reused,
                findings_created=outcome.findings_created,
                findings_reused=outcome.findings_reused,
                ingestion_run_id=outcome.ingestion_run_id,
            )
            self._finish(work_id, attempt, lease_token, "succeeded", result)
            self._log(item.identity, batch_execution_key, attempt, "completed",
                      duration=max(0.0, self.monotonic() - item_started), result=result)
            return result
        except Exception as exc:
            category, retryable, state = self._classify(exc)
            result = ScientificBatchWorkResult(
                item.identity.work_key, item.identity.source_key, state, attempt,
                error_class=category, error_detail=str(exc)[:2000],
                artifact_created=bool(artifact and artifact.created),
                artifact_reused=bool(artifact and not artifact.created),
                ingestion_run_id=getattr(exc, "ingestion_run_id", None),
            )
            self._finish(work_id, attempt, lease_token,
                         "retryable" if retryable else state, result)
            self._log(item.identity, batch_execution_key, attempt, state,
                      duration=max(0.0, self.monotonic() - item_started), result=result)
            return result

    def _claim(self, plan_id, work_key):
        now = self.clock()
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM scientific_batch_work_items
                    WHERE batch_plan_id=%s AND work_key=%s FOR UPDATE
                """, (plan_id, work_key))
                row = cursor.fetchone()
                if row is None:
                    raise ScientificPersistenceConflict("batch work item disappeared")
                if row["work_status"] == "succeeded":
                    connection.commit()
                    return {**row, "action": "already_completed"}
                if row["work_status"] in ("failed", "conflict"):
                    connection.commit()
                    return {**row, "action": row["work_status"]}
                if row["work_status"] == "running" and row["lease_expires_at"] > now:
                    connection.commit()
                    return {**row, "action": "busy"}
                if row["work_status"] == "running":
                    cursor.execute("""
                        UPDATE scientific_batch_work_attempts
                        SET attempt_status='abandoned',completed_at=%s,
                            error_class='stale_worker_lease',
                            error_detail='worker lease expired before completion'
                        WHERE work_item_id=%s AND attempt_number=%s
                          AND attempt_status='running'
                    """, (now, row["id"], row["attempt_count"]))
                if row["attempt_count"] >= row["max_attempts"]:
                    cursor.execute("""
                        UPDATE scientific_batch_work_items SET work_status='failed',
                          lease_token=NULL,lease_expires_at=NULL,
                          error_class='retry_exhausted',
                          error_detail='bounded work-item attempts exhausted',
                          completed_at=%s,updated_at=%s WHERE id=%s RETURNING *
                    """, (now, now, row["id"]))
                    exhausted = cursor.fetchone()
                    connection.commit()
                    return {**exhausted, "action": "failed"}
                attempt = row["attempt_count"] + 1
                lease_token = uuid4()
                execution_key = self.execution_key_factory()
                cursor.execute("""
                    UPDATE scientific_batch_work_items SET work_status='running',
                      attempt_count=%s,lease_token=%s,lease_expires_at=%s,
                      started_at=COALESCE(started_at,%s),completed_at=NULL,
                      error_class=NULL,error_detail=NULL,updated_at=%s
                    WHERE id=%s RETURNING *
                """, (
                    attempt, str(lease_token), now + timedelta(seconds=self.lease_seconds),
                    now, now, row["id"],
                ))
                claimed = cursor.fetchone()
                cursor.execute("""
                    INSERT INTO scientific_batch_work_attempts(
                      work_item_id,attempt_number,execution_key,attempt_status,started_at)
                    VALUES(%s,%s,%s,'running',%s)
                """, (row["id"], attempt, str(execution_key), now))
            connection.commit()
            return {
                **claimed, "action": "execute", "lease_token": lease_token,
                "execution_key": execution_key,
            }
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _checkpoint_artifact(self, work_id, attempt, lease_token, artifact):
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT artifact_manifest_fingerprint
                    FROM scientific_batch_work_items
                    WHERE id=%s AND attempt_count=%s AND lease_token=%s
                      AND work_status='running' FOR UPDATE
                """, (work_id, attempt, str(lease_token)))
                existing = cursor.fetchone()
                if existing is None:
                    raise ScientificPersistenceConflict(
                        "batch artifact checkpoint lost its lease"
                    )
                previous = existing["artifact_manifest_fingerprint"]
                if previous is not None and previous != artifact.manifest_fingerprint:
                    raise ScientificPersistenceConflict(
                        "same batch work identity produced changed artifact bytes"
                    )
                cursor.execute("""
                    UPDATE scientific_batch_work_items
                    SET artifact_manifest_fingerprint=%s,artifact_created=%s,updated_at=%s
                    WHERE id=%s AND attempt_count=%s AND lease_token=%s
                      AND work_status='running'
                """, (
                    artifact.manifest_fingerprint, artifact.created, self.clock(),
                    work_id, attempt, str(lease_token),
                ))
                if cursor.rowcount != 1:
                    raise ScientificPersistenceConflict("batch artifact checkpoint lost its lease")
                cursor.execute("""
                    UPDATE scientific_batch_work_attempts
                    SET artifact_manifest_fingerprint=%s,artifact_created=%s
                    WHERE work_item_id=%s AND attempt_number=%s
                      AND attempt_status='running'
                """, (artifact.manifest_fingerprint, artifact.created, work_id, attempt))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _finish(self, work_id, attempt, lease_token, attempt_status, result):
        now = self.clock()
        work_status = "succeeded" if attempt_status == "succeeded" else attempt_status
        summary = {
            "state": result.state,
            "artifact_created": result.artifact_created,
            "artifact_reused": result.artifact_reused,
            "records_processed": result.records_processed,
            "assessments_created": result.assessments_created,
            "assessments_reused": result.assessments_reused,
            "findings_created": result.findings_created,
            "findings_reused": result.findings_reused,
        }
        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE scientific_batch_work_items SET work_status=%s,
                      lease_token=NULL,lease_expires_at=NULL,ingestion_run_id=%s,
                      records_processed=%s,assessments_written=%s,assessments_reused=%s,
                      findings_written=%s,findings_reused=%s,
                      error_class=%s,error_detail=%s,completed_at=%s,updated_at=%s
                    WHERE id=%s AND attempt_count=%s AND lease_token=%s
                      AND work_status='running'
                """, (
                    work_status, result.ingestion_run_id, result.records_processed,
                    result.assessments_created, result.assessments_reused,
                    result.findings_created, result.findings_reused,
                    result.error_class, result.error_detail, now, now,
                    work_id, attempt, str(lease_token),
                ))
                if cursor.rowcount != 1:
                    raise ScientificPersistenceConflict("batch result lost its lease")
                cursor.execute("""
                    UPDATE scientific_batch_work_attempts SET attempt_status=%s,
                      completed_at=%s,ingestion_run_id=%s,records_processed=%s,
                      assessments_written=%s,assessments_reused=%s,
                      findings_written=%s,findings_reused=%s,error_class=%s,
                      error_detail=%s,result_summary=%s
                    WHERE work_item_id=%s AND attempt_number=%s
                      AND attempt_status='running'
                """, (
                    "completed" if attempt_status == "succeeded" else attempt_status,
                    now, result.ingestion_run_id, result.records_processed,
                    result.assessments_created, result.assessments_reused,
                    result.findings_created, result.findings_reused,
                    result.error_class, result.error_detail,
                    psycopg2.extras.Json(summary), work_id, attempt,
                ))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _classify(exc):
        if isinstance(exc, ScientificBatchFailure):
            return exc.category, exc.retryable, "retryable" if exc.retryable else "failed"
        if isinstance(exc, ScientificPersistenceConflict):
            return "conflict", False, "conflict"
        if isinstance(exc, ScientificAcquisitionError):
            return "acquisition_failure", True, "retryable"
        if isinstance(exc, ScientificParserError):
            return "parser_failure", False, "failed"
        if isinstance(exc, ScientificRecordValidationError):
            return "identity_failure", False, "failed"
        code = getattr(exc, "code", "")
        if "integrity" in code:
            return "integrity_failure", False, "failed"
        return "persistence_failure", True, "retryable"

    @staticmethod
    def _existing_result(identity, row):
        action = row["action"]
        if action == "already_completed":
            state, error_class, error_detail = "already_completed", None, None
        elif action == "busy":
            state, error_class = "retryable", "work_item_claimed"
            error_detail = "another worker owns a bounded active lease"
        else:
            state = action
            error_class, error_detail = row.get("error_class"), row.get("error_detail")
        created = row.get("artifact_created")
        return ScientificBatchWorkResult(
            identity.work_key, identity.source_key, state, row["attempt_count"],
            error_class=error_class, error_detail=error_detail,
            artifact_created=bool(created) if state != "already_completed" else False,
            artifact_reused=(state == "already_completed" and created is not None),
            records_processed=row.get("records_processed", 0),
            assessments_reused=(row.get("assessments_written", 0)
                                + row.get("assessments_reused", 0)
                                if state == "already_completed" else 0),
            findings_reused=(row.get("findings_written", 0)
                             + row.get("findings_reused", 0)
                             if state == "already_completed" else 0),
            ingestion_run_id=row.get("ingestion_run_id"),
        )

    @staticmethod
    def _log(identity, batch_execution_key, attempt, state, *, duration=None, result=None):
        event = {
            "batch_execution_id": str(batch_execution_key),
            "work_item_identity": identity.work_key,
            "provider": identity.source_key,
            "dataset": identity.dataset_key,
            "release": identity.external_release_key,
            "artifacts": sorted(identity.artifact_keys),
            "adapter_version": identity.source_adapter_version,
            "parser_version": identity.parser_version,
            "attempt": attempt,
            "state": state,
        }
        if duration is not None:
            event["duration_seconds"] = duration
        if result is not None:
            event.update({
                "error_class": result.error_class,
                "records_processed": result.records_processed,
                "assessments_created": result.assessments_created,
                "findings_created": result.findings_created,
            })
        logger.info("scientific_batch_work_item", extra={"scientific_batch": event})
