"""Provider-neutral orchestration for Phase 7.6.4C execution persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.repositories.scientific_evaluation_executions import (
    PostgresScientificEvaluationExecutionRepository,
)
from app.scientific_evaluation.errors import (
    ActiveExecutionAttemptError,
    ExecutionConflictError,
    ExecutionIdempotencyConflictError,
    ExecutionNotStartableError,
    ExecutionPublicationConflictError,
    ExecutionRequestError,
    IncompleteSelectionCoverageError,
    IncompatibleCanonicalOutputError,
    InvalidExecutionAttemptTransitionError,
    InvalidProtocolLifecycleError,
    NonRetryableExecutionError,
    ReplayComparisonUnavailableError,
    ReplayVerificationConflictError,
    UnsealedEvidenceSnapshotError,
)
from app.scientific_evaluation.execution import (
    AttemptError,
    AttemptStartRequest,
    PublicationOutputInput,
    ReplayOutputInput,
    SemanticExecutionRequest,
    build_attempt_error_payload,
    build_component_payload,
    build_configuration_payload,
    build_engine_build_payload,
    build_execution_identity_payload,
    build_publication_bundle_payload,
    build_replay_verification_payload,
    build_result_payload,
    build_selection_decision_payload,
    build_selection_manifest_payload,
    build_trace_payload,
    validate_decision,
    validate_semantic_request,
)
from app.services.scientific_evaluation_artifacts import (
    PersistedScientificArtifact,
    ScientificArtifactWriteRequest,
    ScientificArtifactWriter,
)


@dataclass(frozen=True)
class ExecutionCreationResult:
    execution: dict[str, Any]
    configuration_artifact: PersistedScientificArtifact
    identity_artifact: PersistedScientificArtifact
    execution_reused: bool
    idempotency_reused: bool


@dataclass(frozen=True)
class ExecutionAttemptResult:
    attempt: dict[str, Any]
    engine_build_artifact: PersistedScientificArtifact


@dataclass(frozen=True)
class PublicationRuntimeResult:
    publication: dict[str, Any]
    selection_artifact: PersistedScientificArtifact
    result_artifact: PersistedScientificArtifact
    trace_artifact: PersistedScientificArtifact
    bundle_artifact: PersistedScientificArtifact
    publication_reused: bool


@dataclass(frozen=True)
class ReplayVerificationRuntimeResult:
    verification: dict[str, Any]
    selection_artifact: PersistedScientificArtifact
    result_artifact: PersistedScientificArtifact
    trace_artifact: PersistedScientificArtifact
    verification_artifact: PersistedScientificArtifact
    verification_reused: bool


@dataclass(frozen=True)
class _PreparedPublication:
    decision_rows: tuple[dict[str, Any], ...]
    component_rows: tuple[dict[str, Any], ...]
    selection_artifact: PersistedScientificArtifact
    result_artifact: PersistedScientificArtifact
    trace_artifact: PersistedScientificArtifact
    bundle_artifact: PersistedScientificArtifact


class ScientificEvaluationExecutionService:
    """Coordinate execution history inside a caller-owned transaction.

    No method commits, rolls back or closes the supplied connection/cursor.
    Canonical output content is supplied by the caller; this service validates
    structure and persists it without performing scientific selection/scoring.
    """

    def __init__(
        self,
        repository: PostgresScientificEvaluationExecutionRepository | None = None,
        artifact_writer: ScientificArtifactWriter | None = None,
    ):
        self.repository = repository or PostgresScientificEvaluationExecutionRepository()
        self.artifact_writer = artifact_writer or ScientificArtifactWriter()

    def create_or_reuse_execution(
        self, cursor, request: SemanticExecutionRequest
    ) -> ExecutionCreationResult:
        validate_semantic_request(request)
        protocol = self.repository.load_protocol(cursor, request.protocol_version_id)
        snapshot = self.repository.load_snapshot(cursor, request.evidence_snapshot_id)
        self._validate_protocol(protocol, request.execution_mode)
        if snapshot is None or snapshot["status"] != "sealed" or snapshot["snapshot_digest"] is None:
            raise UnsealedEvidenceSnapshotError("execution requires a sealed evidence snapshot")

        target = self._require_artifact(
            cursor, request.target_artifact_id, "scientific_evaluation_target", request.target_digest
        )
        input_artifact = self._require_artifact(
            cursor, request.input_artifact_id, "scientific_evaluation_input", request.input_digest
        )
        mapping = None
        if request.mapping_state_artifact_id is not None:
            mapping = self._require_artifact(
                cursor,
                request.mapping_state_artifact_id,
                "scientific_mapping_state_manifest",
                None,
            )
        self._validate_target_and_input(request, target, mapping, input_artifact)

        configuration_artifact = self._write(
            cursor,
            "scientific_evaluation_configuration",
            build_configuration_payload(request.configuration),
        )
        comparison = None
        comparison_digest = None
        if request.comparison_execution_id is not None:
            comparison = self.repository.load_execution(
                cursor, request.comparison_execution_id, lock=False
            )
            if comparison is None:
                raise ExecutionRequestError("comparison execution does not exist")
            comparison_digest = bytes(comparison["semantic_execution_digest"])
            self._validate_comparison(
                request, comparison, configuration_artifact.artifact.id
            )
            if (
                request.execution_mode == "REPLAY"
                and self.repository.load_comparison_publication(
                    cursor, request.comparison_execution_id
                )
                is None
            ):
                raise ReplayComparisonUnavailableError(
                    "REPLAY comparison execution has no canonical publication"
                )

        identity_payload = build_execution_identity_payload(
            protocol_digest=bytes(protocol["protocol_digest"]),
            evidence_snapshot_digest=bytes(snapshot["snapshot_digest"]),
            input_digest=request.input_digest,
            execution_mode=request.execution_mode,
            configuration_digest=configuration_artifact.artifact.content_digest,
            comparison_semantic_execution_digest=comparison_digest,
        )
        identity_artifact = self._write(
            cursor, "scientific_evaluation_execution_identity", identity_payload
        )
        values = {
            "execution_key": str(uuid4()),
            "protocol_version_id": request.protocol_version_id,
            "evidence_snapshot_id": request.evidence_snapshot_id,
            "target_type": request.target_type,
            "substance_id": request.target_id if request.target_type == "substance" else None,
            "ingredient_id": request.target_id if request.target_type == "ingredient" else None,
            "target_artifact_id": request.target_artifact_id,
            "mapping_state_artifact_id": request.mapping_state_artifact_id,
            "input_artifact_id": request.input_artifact_id,
            "configuration_artifact_id": configuration_artifact.artifact.id,
            "semantic_identity_artifact_id": identity_artifact.artifact.id,
            "comparison_execution_id": request.comparison_execution_id,
            "execution_mode": request.execution_mode,
            "protocol_digest": bytes(protocol["protocol_digest"]),
            "evidence_snapshot_digest": bytes(snapshot["snapshot_digest"]),
            "input_digest": request.input_digest,
            "configuration_digest": configuration_artifact.artifact.content_digest,
            "semantic_execution_digest": identity_artifact.artifact.content_digest,
            "requested_by": request.requested_by,
        }
        execution = self.repository.insert_execution(cursor, values)
        reused = execution is None
        if reused:
            execution = self.repository.load_execution_by_digest(
                cursor, identity_artifact.artifact.content_digest, lock=True
            )
            if execution is None or not self._execution_matches(execution, values):
                raise ExecutionConflictError(
                    "existing semantic execution has incompatible canonical roots"
                )

        idempotency_reused = False
        if request.idempotency_scope is not None:
            inserted = self.repository.insert_idempotency(
                cursor,
                scope=request.idempotency_scope,
                key=request.idempotency_key or "",
                semantic_digest=identity_artifact.artifact.content_digest,
                execution_id=execution["id"],
            )
            idempotency_reused = inserted is None
            if inserted is None:
                existing_key = self.repository.load_idempotency(
                    cursor, request.idempotency_scope, request.idempotency_key or ""
                )
                if existing_key is None or (
                    bytes(existing_key["expected_semantic_digest"])
                    != identity_artifact.artifact.content_digest
                    or existing_key["execution_id"] != execution["id"]
                ):
                    raise ExecutionIdempotencyConflictError(
                        "idempotency scope/key is bound to another semantic execution"
                    )
        return ExecutionCreationResult(
            execution,
            configuration_artifact,
            identity_artifact,
            reused,
            idempotency_reused,
        )

    def start_attempt(
        self, cursor, request: AttemptStartRequest
    ) -> ExecutionAttemptResult:
        if not isinstance(request, AttemptStartRequest):
            raise ExecutionRequestError("attempt request must use AttemptStartRequest")
        execution = self.repository.load_execution(cursor, request.execution_id, lock=True)
        if execution is None:
            raise ExecutionNotStartableError("execution does not exist")
        if execution["technical_status"] == "running":
            raise ActiveExecutionAttemptError("execution already has a running attempt")
        if execution["technical_status"] not in {"pending", "failed"}:
            raise ExecutionNotStartableError(
                f"execution status {execution['technical_status']} cannot start an attempt"
            )
        latest = self.repository.load_latest_attempt(cursor, request.execution_id)
        if latest is not None and latest["attempt_status"] in {"failed", "abandoned"}:
            if latest["retryable"] is not True:
                raise NonRetryableExecutionError("latest failed attempt is not retryable")
        if request.heartbeat_at.tzinfo is None or request.lease_expires_at.tzinfo is None:
            raise ExecutionRequestError("attempt lease timestamps must be timezone-aware")
        if not isinstance(request.lease_token, UUID):
            raise ExecutionRequestError("lease_token must be a UUID")
        if request.worker_id is not None and (
            type(request.worker_id) is not str
            or not request.worker_id.strip()
            or len(request.worker_id) > 255
        ):
            raise ExecutionRequestError("worker_id must be a nonblank string up to 255 characters")
        if request.lease_expires_at <= request.heartbeat_at:
            raise ExecutionRequestError("lease_expires_at must be after heartbeat_at")
        build_payload = build_engine_build_payload(request.engine_build)
        config = self.repository.load_artifact(cursor, execution["configuration_artifact_id"])
        if config is None:
            raise ExecutionRequestError("execution configuration artifact is unavailable")
        contract = self._payload(config).get("engine_contract")
        if not isinstance(contract, dict):
            raise ExecutionRequestError("execution configuration contract is unavailable")
        if (
            request.engine_build.engine_key != contract["engine_key"]
            or request.engine_build.semantic_compatibility_version
            != contract["semantic_compatibility_version"]
        ):
            raise ExecutionRequestError("engine build does not implement execution configuration")
        build_artifact = self._write(cursor, "scientific_evaluation_engine_build", build_payload)
        attempt_number = self.repository.next_attempt_number(cursor, request.execution_id)
        self.repository.transition_execution(cursor, request.execution_id, "running")
        attempt = self.repository.insert_attempt(
            cursor,
            {
                "attempt_key": str(uuid4()),
                "execution_id": request.execution_id,
                "attempt_number": attempt_number,
                "engine_build_artifact_id": build_artifact.artifact.id,
                "worker_id": request.worker_id,
                "lease_token": str(request.lease_token),
                "lease_expires_at": request.lease_expires_at,
                "heartbeat_at": request.heartbeat_at,
            },
        )
        return ExecutionAttemptResult(attempt, build_artifact)

    def heartbeat_attempt(
        self,
        cursor,
        *,
        attempt_id: int,
        lease_token: UUID,
        heartbeat_at: datetime,
        lease_expires_at: datetime,
    ) -> dict[str, Any]:
        if heartbeat_at.tzinfo is None or lease_expires_at.tzinfo is None:
            raise ExecutionRequestError("heartbeat timestamps must be timezone-aware")
        if not isinstance(lease_token, UUID):
            raise ExecutionRequestError("lease_token must be a UUID")
        if lease_expires_at <= heartbeat_at:
            raise ExecutionRequestError("lease extension must expire after heartbeat")
        attempt = self.repository.heartbeat_attempt(
            cursor,
            attempt_id=attempt_id,
            lease_token=str(lease_token),
            heartbeat_at=heartbeat_at,
            lease_expires_at=lease_expires_at,
        )
        if attempt is None:
            raise InvalidExecutionAttemptTransitionError(
                "attempt is terminal or lease token does not match"
            )
        return attempt

    def fail_attempt(self, cursor, attempt_id: int, error: AttemptError) -> dict[str, Any]:
        attempt = self.repository.load_attempt(cursor, attempt_id, lock=True)
        if attempt is None or attempt["attempt_status"] != "running":
            raise InvalidExecutionAttemptTransitionError("only a running attempt can fail")
        execution = self.repository.load_execution(cursor, attempt["execution_id"], lock=True)
        if execution is None:
            raise InvalidExecutionAttemptTransitionError("attempt execution is unavailable")
        error_artifact = self._write(
            cursor, "scientific_evaluation_attempt_error", build_attempt_error_payload(error)
        )
        closed = self.repository.close_attempt(
            cursor,
            attempt_id=attempt_id,
            status="failed",
            error_category=error.category,
            error_code=error.code,
            retryable=error.retryable,
            error_artifact_id=error_artifact.artifact.id,
        )
        if closed is None:
            raise InvalidExecutionAttemptTransitionError("attempt changed concurrently")
        self.repository.transition_execution(
            cursor, execution["id"], "pending" if error.retryable else "failed",
            completed=not error.retryable,
        )
        return closed

    def mark_attempt_succeeded(self, cursor, attempt_id: int) -> dict[str, Any]:
        attempt = self.repository.load_attempt(cursor, attempt_id, lock=True)
        if attempt is None or attempt["attempt_status"] != "running":
            raise InvalidExecutionAttemptTransitionError("only a running attempt can succeed")
        closed = self.repository.close_attempt(cursor, attempt_id=attempt_id, status="succeeded")
        if closed is None:
            raise InvalidExecutionAttemptTransitionError("attempt changed concurrently")
        return closed

    def publish(
        self,
        cursor,
        *,
        execution_id: int,
        attempt_id: int,
        output: PublicationOutputInput,
    ) -> PublicationRuntimeResult:
        execution = self.repository.load_execution(cursor, execution_id, lock=True)
        if execution is None or execution["execution_mode"] == "REPLAY":
            raise ExecutionPublicationConflictError("REPLAY cannot own a publication")
        prepared = self._prepare_publication(cursor, execution, output)
        if execution["technical_status"] == "completed":
            publication = self.repository.load_publication(cursor, execution_id)
            if publication is None or not self._publication_matches(publication, prepared):
                raise ExecutionPublicationConflictError(
                    "existing publication differs from supplied canonical output"
                )
            return PublicationRuntimeResult(
                publication,
                prepared.selection_artifact,
                prepared.result_artifact,
                prepared.trace_artifact,
                prepared.bundle_artifact,
                True,
            )
        attempt = self.repository.load_attempt(cursor, attempt_id, lock=True)
        if (
            execution["technical_status"] != "running"
            or attempt is None
            or attempt["execution_id"] != execution_id
            or attempt["attempt_status"] != "running"
        ):
            raise ExecutionPublicationConflictError(
                "publication requires the execution's running attempt"
            )
        for row in prepared.decision_rows:
            self.repository.insert_selection_decision(cursor, row)
        result_id = self.repository.insert_result(
            cursor,
            {
                "result_key": str(uuid4()),
                "execution_id": execution_id,
                "result_kind": output.result_kind,
                "result_schema_version": output.result_schema_version,
                "scientific_status_namespace": output.scientific_status_namespace,
                "scientific_status_version": output.scientific_status_version,
                "scientific_status_code": output.scientific_status_code,
                "canonical_artifact_id": prepared.result_artifact.artifact.id,
                "result_digest": prepared.result_artifact.artifact.content_digest,
            },
        )
        for row in prepared.component_rows:
            row = dict(row)
            row["result_id"] = result_id
            self.repository.insert_component(cursor, row)
        trace_id = self.repository.insert_trace(
            cursor,
            {
                "trace_key": str(uuid4()),
                "execution_id": execution_id,
                "result_id": result_id,
                "trace_schema_version": output.trace_schema_version,
                "canonical_artifact_id": prepared.trace_artifact.artifact.id,
                "trace_digest": prepared.trace_artifact.artifact.content_digest,
                "result_digest": prepared.result_artifact.artifact.content_digest,
                "selection_digest": prepared.selection_artifact.artifact.content_digest,
                "protocol_digest": bytes(execution["protocol_digest"]),
                "evidence_snapshot_digest": bytes(execution["evidence_snapshot_digest"]),
                "input_digest": bytes(execution["input_digest"]),
            },
        )
        self.mark_attempt_succeeded(cursor, attempt_id)
        self.repository.transition_execution(cursor, execution_id, "completed", completed=True)
        publication = self.repository.insert_publication(
            cursor,
            {
                "publication_key": str(uuid4()),
                "execution_id": execution_id,
                "result_id": result_id,
                "trace_id": trace_id,
                "successful_attempt_id": attempt_id,
                "selection_manifest_artifact_id": prepared.selection_artifact.artifact.id,
                "bundle_artifact_id": prepared.bundle_artifact.artifact.id,
                "selection_digest": prepared.selection_artifact.artifact.content_digest,
                "result_digest": prepared.result_artifact.artifact.content_digest,
                "trace_digest": prepared.trace_artifact.artifact.content_digest,
                "publication_bundle_digest": prepared.bundle_artifact.artifact.content_digest,
                "published_by": output.published_by,
            },
        )
        return PublicationRuntimeResult(
            publication,
            prepared.selection_artifact,
            prepared.result_artifact,
            prepared.trace_artifact,
            prepared.bundle_artifact,
            False,
        )

    def verify_replay(
        self,
        cursor,
        *,
        execution_id: int,
        attempt_id: int,
        output: ReplayOutputInput,
    ) -> ReplayVerificationRuntimeResult:
        if not isinstance(output, ReplayOutputInput):
            raise ExecutionRequestError("replay output must use ReplayOutputInput")
        execution = self.repository.load_execution(cursor, execution_id, lock=True)
        if execution is None or execution["execution_mode"] != "REPLAY":
            raise ReplayVerificationConflictError("verification requires a REPLAY execution")
        comparison = self.repository.load_comparison_publication(
            cursor, execution["comparison_execution_id"]
        )
        if comparison is None:
            raise ReplayComparisonUnavailableError(
                "comparison execution has no canonical publication"
            )
        selection = self._write_raw(
            cursor, "scientific_evidence_selection_manifest", output.selection_manifest_payload
        )
        result = self._write_raw(cursor, "scientific_evaluation_result", output.result_payload)
        trace = self._write_raw(cursor, "scientific_evaluation_trace", output.trace_payload)
        comparison_execution = self.repository.load_execution(
            cursor, execution["comparison_execution_id"]
        )
        if comparison_execution is None:
            raise ReplayComparisonUnavailableError("comparison execution is unavailable")
        self._validate_replay_output_roots(
            comparison_execution, output, selection, result
        )
        verification_payload, status = build_replay_verification_payload(
            replay_execution_digest=bytes(execution["semantic_execution_digest"]),
            comparison_execution_digest=bytes(
                comparison_execution["semantic_execution_digest"]
            ),
            comparison_bundle_digest=bytes(comparison["publication_bundle_digest"]),
            expected_selection_digest=bytes(comparison["selection_digest"]),
            expected_result_digest=bytes(comparison["result_digest"]),
            expected_trace_digest=bytes(comparison["trace_digest"]),
            recomputed_selection_digest=selection.artifact.content_digest,
            recomputed_result_digest=result.artifact.content_digest,
            recomputed_trace_digest=trace.artifact.content_digest,
        )
        verification_artifact = self._write(
            cursor, "scientific_evaluation_replay_verification", verification_payload
        )
        if execution["technical_status"] == "completed":
            verification = self.repository.load_replay_verification(cursor, execution_id)
            if verification is None or not self._verification_matches(
                verification, selection, result, trace, verification_artifact, status
            ):
                raise ReplayVerificationConflictError(
                    "existing verification differs from recomputed canonical roots"
                )
            return ReplayVerificationRuntimeResult(
                verification, selection, result, trace, verification_artifact, True
            )
        attempt = self.repository.load_attempt(cursor, attempt_id, lock=True)
        if (
            execution["technical_status"] != "running"
            or attempt is None
            or attempt["execution_id"] != execution_id
            or attempt["attempt_status"] != "running"
        ):
            raise ReplayVerificationConflictError(
                "replay verification requires the execution's running attempt"
            )
        verification = self.repository.insert_replay_verification(
            cursor,
            {
                "verification_key": str(uuid4()),
                "execution_id": execution_id,
                "comparison_publication_id": comparison["id"],
                "successful_attempt_id": attempt_id,
                "verification_artifact_id": verification_artifact.artifact.id,
                "verification_digest": verification_artifact.artifact.content_digest,
                "expected_publication_bundle_digest": bytes(
                    comparison["publication_bundle_digest"]
                ),
                "expected_selection_digest": bytes(comparison["selection_digest"]),
                "expected_result_digest": bytes(comparison["result_digest"]),
                "expected_trace_digest": bytes(comparison["trace_digest"]),
                "recomputed_selection_artifact_id": selection.artifact.id,
                "recomputed_result_artifact_id": result.artifact.id,
                "recomputed_trace_artifact_id": trace.artifact.id,
                "recomputed_selection_digest": selection.artifact.content_digest,
                "recomputed_result_digest": result.artifact.content_digest,
                "recomputed_trace_digest": trace.artifact.content_digest,
                "verification_status": status,
            },
        )
        self.mark_attempt_succeeded(cursor, attempt_id)
        self.repository.transition_execution(cursor, execution_id, "completed", completed=True)
        return ReplayVerificationRuntimeResult(
            verification, selection, result, trace, verification_artifact, False
        )

    def _prepare_publication(
        self, cursor, execution: dict[str, Any], output: PublicationOutputInput
    ) -> _PreparedPublication:
        if not isinstance(output, PublicationOutputInput):
            raise ExecutionRequestError("publication output must use PublicationOutputInput")
        if type(output.decisions) is not tuple or type(output.components) is not tuple:
            raise ExecutionRequestError("publication decisions/components must be tuples")
        if (
            type(output.published_by) is not str
            or not output.published_by.strip()
            or len(output.published_by) > 255
        ):
            raise ExecutionRequestError(
                "published_by must be a nonblank string up to 255 characters"
            )
        members = self.repository.load_snapshot_members(cursor, execution["evidence_snapshot_id"])
        members_by_id = {member["id"]: member for member in members}
        supplied_ids = [decision.snapshot_member_id for decision in output.decisions]
        if len(supplied_ids) != len(set(supplied_ids)) or set(supplied_ids) != set(members_by_id):
            raise IncompleteSelectionCoverageError(
                "selection decisions must cover every snapshot member exactly once"
            )
        decision_rows = []
        descriptors = []
        for decision in output.decisions:
            validate_decision(decision)
            member = members_by_id[decision.snapshot_member_id]
            artifact = self._write(
                cursor,
                "scientific_evidence_selection_decision",
                build_selection_decision_payload(
                    execution_digest=bytes(execution["semantic_execution_digest"]),
                    member=member,
                    decision=decision,
                ),
            )
            decision_rows.append(
                {
                    "execution_id": execution["id"],
                    "snapshot_member_id": decision.snapshot_member_id,
                    "decision": decision.decision,
                    "selection_role": decision.selection_role,
                    "resolution_state": decision.resolution_state,
                    "reason_namespace": decision.reason_namespace,
                    "reason_version": decision.reason_version,
                    "primary_reason_code": decision.primary_reason_code,
                    "decision_artifact_id": artifact.artifact.id,
                    "decision_digest": artifact.artifact.content_digest,
                }
            )
            descriptors.append(
                {
                    "decision": decision.decision,
                    "decision_digest": artifact.artifact.content_digest.hex(),
                    "member_identity_digest": bytes(member["member_identity_digest"]).hex(),
                    "member_semantic_digest": bytes(member["member_semantic_digest"]).hex(),
                    "primary_reason_code": decision.primary_reason_code,
                    "resolution_state": decision.resolution_state,
                    "selection_role": decision.selection_role,
                }
            )
        selection = self._write(
            cursor,
            "scientific_evidence_selection_manifest",
            build_selection_manifest_payload(
                execution_digest=bytes(execution["semantic_execution_digest"]),
                descriptors=descriptors,
            ),
        )
        component_rows = []
        component_descriptors = []
        for ordinal, component in enumerate(output.components):
            artifact = self._write(
                cursor,
                "scientific_evaluation_result_component",
                build_component_payload(
                    execution_digest=bytes(execution["semantic_execution_digest"]),
                    ordinal=ordinal,
                    component=component,
                ),
            )
            component_rows.append(
                {
                    "component_kind": component.component_kind,
                    "component_schema_version": component.component_schema_version,
                    "component_role": component.component_role,
                    "component_artifact_id": artifact.artifact.id,
                    "component_digest": artifact.artifact.content_digest,
                    "component_ordinal": ordinal,
                }
            )
            component_descriptors.append(
                {
                    "component_digest": artifact.artifact.content_digest.hex(),
                    "component_kind": component.component_kind,
                    "component_ordinal": ordinal,
                    "component_role": component.component_role,
                    "component_schema_version": component.component_schema_version,
                }
            )
        result = self._write(
            cursor,
            "scientific_evaluation_result",
            build_result_payload(
                execution_digest=bytes(execution["semantic_execution_digest"]),
                output=output,
                component_descriptors=component_descriptors,
            ),
        )
        trace = self._write(
            cursor,
            "scientific_evaluation_trace",
            build_trace_payload(
                execution_digest=bytes(execution["semantic_execution_digest"]),
                protocol_digest=bytes(execution["protocol_digest"]),
                snapshot_digest=bytes(execution["evidence_snapshot_digest"]),
                input_digest=bytes(execution["input_digest"]),
                selection_digest=selection.artifact.content_digest,
                result_digest=result.artifact.content_digest,
                trace_schema_version=output.trace_schema_version,
                content=output.trace_content,
            ),
        )
        bundle = self._write(
            cursor,
            "scientific_evaluation_publication_bundle",
            build_publication_bundle_payload(
                execution_digest=bytes(execution["semantic_execution_digest"]),
                protocol_digest=bytes(execution["protocol_digest"]),
                snapshot_digest=bytes(execution["evidence_snapshot_digest"]),
                input_digest=bytes(execution["input_digest"]),
                configuration_digest=bytes(execution["configuration_digest"]),
                selection_digest=selection.artifact.content_digest,
                result_digest=result.artifact.content_digest,
                trace_digest=trace.artifact.content_digest,
            ),
        )
        return _PreparedPublication(
            tuple(decision_rows), tuple(component_rows), selection, result, trace, bundle
        )

    def _write(
        self, cursor, artifact_kind: str, payload: dict[str, Any]
    ) -> PersistedScientificArtifact:
        return self.artifact_writer.write_verified_inline(
            cursor, ScientificArtifactWriteRequest(artifact_kind, "1", payload)
        )

    def _write_raw(
        self, cursor, artifact_kind: str, payload: dict[str, Any]
    ) -> PersistedScientificArtifact:
        if type(payload) is not dict:
            raise IncompatibleCanonicalOutputError(
                f"{artifact_kind} payload must be a canonical JSON object"
            )
        if payload.get("artifact_type") != artifact_kind or payload.get("schema_version") != "1":
            raise IncompatibleCanonicalOutputError(
                f"invalid {artifact_kind}/1 payload boundary"
            )
        return self._write(cursor, artifact_kind, payload)

    def _require_artifact(
        self,
        cursor,
        artifact_id: int,
        artifact_kind: str,
        digest: bytes | None,
    ) -> dict[str, Any]:
        artifact = self.repository.load_artifact(cursor, artifact_id)
        if artifact is None or (
            artifact["artifact_kind"] != artifact_kind
            or artifact["schema_version"] != "1"
            or artifact["canonicalization_version"] != "wye-c14n-json-v1"
            or artifact["digest_algorithm"] != "sha256"
            or (digest is not None and bytes(artifact["content_digest"]) != digest)
            or not isinstance(artifact["json_payload"], dict)
        ):
            raise ExecutionRequestError(f"invalid canonical artifact role: {artifact_kind}/1")
        return artifact

    @staticmethod
    def _validate_protocol(protocol: dict[str, Any] | None, mode: str) -> None:
        if protocol is None or protocol["protocol_digest"] is None:
            raise InvalidProtocolLifecycleError("protocol version does not exist")
        if mode in {"NORMAL", "REFRESH"}:
            valid = protocol["lifecycle_status"] == "published"
        else:
            valid = protocol["lifecycle_status"] in {"published", "deprecated", "retired"}
        if not valid or protocol["published_at"] is None:
            raise InvalidProtocolLifecycleError(
                f"protocol lifecycle is not executable for {mode}"
            )

    @staticmethod
    def _payload(artifact: dict[str, Any]) -> dict[str, Any]:
        cache = artifact["json_payload"]
        if not isinstance(cache, dict) or not isinstance(cache.get("payload"), dict):
            raise ExecutionRequestError("canonical artifact JSON cache is unavailable")
        return cache["payload"]

    def _validate_target_and_input(
        self,
        request: SemanticExecutionRequest,
        target: dict[str, Any],
        mapping: dict[str, Any] | None,
        input_artifact: dict[str, Any],
    ) -> None:
        target_payload = self._payload(target)
        input_payload = self._payload(input_artifact)
        if (
            target_payload.get("target_type") != request.target_type
            or target_payload.get("entity_id") != request.target_id
        ):
            raise ExecutionRequestError("concrete target disagrees with target artifact")
        input_target = input_payload.get("target") or {}
        mapping_state = input_payload.get("mapping_state") or {}
        if (
            input_target.get("target_type") != request.target_type
            or input_target.get("target_artifact_digest") != request.target_digest.hex()
        ):
            raise ExecutionRequestError("canonical input target root mismatch")
        if request.target_type == "substance":
            if mapping is not None or mapping_state.get("applicability") != "not_applicable":
                raise ExecutionRequestError("substance mapping state must be not_applicable")
        elif (
            mapping is None
            or mapping_state.get("applicability") != "required"
            or mapping_state.get("manifest_digest")
            != bytes(mapping["content_digest"]).hex()
        ):
            raise ExecutionRequestError("ingredient canonical input mapping root mismatch")

    @staticmethod
    def _validate_comparison(
        request: SemanticExecutionRequest,
        comparison: dict[str, Any],
        configuration_artifact_id: int,
    ) -> None:
        if request.execution_mode == "REPLAY" and not (
            request.protocol_version_id == comparison["protocol_version_id"]
            and request.evidence_snapshot_id == comparison["evidence_snapshot_id"]
            and request.input_artifact_id == comparison["input_artifact_id"]
            and configuration_artifact_id == comparison["configuration_artifact_id"]
        ):
            raise ExecutionRequestError(
                "REPLAY must preserve historical protocol/snapshot/input/configuration"
            )
        if request.execution_mode == "REFRESH" and not (
            request.target_type == comparison["target_type"]
            and request.target_id
            == (
                comparison["substance_id"]
                if request.target_type == "substance"
                else comparison["ingredient_id"]
            )
            and (
                request.evidence_snapshot_id != comparison["evidence_snapshot_id"]
                or request.input_artifact_id != comparison["input_artifact_id"]
            )
        ):
            raise ExecutionRequestError("REFRESH requires same target and changed snapshot/input")
        if request.execution_mode == "COUNTERFACTUAL" and not (
            request.evidence_snapshot_id == comparison["evidence_snapshot_id"]
            and request.input_artifact_id == comparison["input_artifact_id"]
            and (
                request.protocol_version_id != comparison["protocol_version_id"]
                or configuration_artifact_id != comparison["configuration_artifact_id"]
            )
        ):
            raise ExecutionRequestError(
                "COUNTERFACTUAL must preserve snapshot/input and change protocol/configuration"
            )

    @staticmethod
    def _validate_replay_output_roots(
        comparison: dict[str, Any],
        output: ReplayOutputInput,
        selection: PersistedScientificArtifact,
        result: PersistedScientificArtifact,
    ) -> None:
        semantic_digest = bytes(comparison["semantic_execution_digest"]).hex()
        if (
            output.selection_manifest_payload.get("execution_semantic_digest")
            != semantic_digest
            or output.result_payload.get("execution_semantic_digest") != semantic_digest
            or output.trace_payload.get("execution_semantic_digest") != semantic_digest
            or output.trace_payload.get("protocol_digest")
            != bytes(comparison["protocol_digest"]).hex()
            or output.trace_payload.get("evidence_snapshot_digest")
            != bytes(comparison["evidence_snapshot_digest"]).hex()
            or output.trace_payload.get("input_digest")
            != bytes(comparison["input_digest"]).hex()
            or output.trace_payload.get("selection_digest")
            != selection.artifact.content_digest.hex()
            or output.trace_payload.get("result_digest")
            != result.artifact.content_digest.hex()
        ):
            raise IncompatibleCanonicalOutputError(
                "REPLAY output payload roots do not describe the comparison execution"
            )

    @staticmethod
    def _execution_matches(execution: dict[str, Any], expected: dict[str, Any]) -> bool:
        for key in (
            "protocol_version_id", "evidence_snapshot_id", "target_type", "substance_id",
            "ingredient_id", "target_artifact_id", "mapping_state_artifact_id",
            "input_artifact_id", "configuration_artifact_id", "semantic_identity_artifact_id",
            "comparison_execution_id", "execution_mode",
        ):
            if execution[key] != expected[key]:
                return False
        for key in (
            "protocol_digest", "evidence_snapshot_digest", "input_digest",
            "configuration_digest", "semantic_execution_digest",
        ):
            if bytes(execution[key]) != expected[key]:
                return False
        return True

    @staticmethod
    def _publication_matches(
        publication: dict[str, Any], prepared: _PreparedPublication
    ) -> bool:
        return (
            publication["selection_manifest_artifact_id"]
            == prepared.selection_artifact.artifact.id
            and publication["result_artifact_id"] == prepared.result_artifact.artifact.id
            and publication["trace_artifact_id"] == prepared.trace_artifact.artifact.id
            and publication["bundle_artifact_id"] == prepared.bundle_artifact.artifact.id
            and bytes(publication["selection_digest"])
            == prepared.selection_artifact.artifact.content_digest
            and bytes(publication["result_digest"])
            == prepared.result_artifact.artifact.content_digest
            and bytes(publication["trace_digest"])
            == prepared.trace_artifact.artifact.content_digest
            and bytes(publication["publication_bundle_digest"])
            == prepared.bundle_artifact.artifact.content_digest
        )

    @staticmethod
    def _verification_matches(
        verification: dict[str, Any],
        selection: PersistedScientificArtifact,
        result: PersistedScientificArtifact,
        trace: PersistedScientificArtifact,
        verification_artifact: PersistedScientificArtifact,
        status: str,
    ) -> bool:
        return (
            verification["verification_status"] == status
            and verification["recomputed_selection_artifact_id"] == selection.artifact.id
            and verification["recomputed_result_artifact_id"] == result.artifact.id
            and verification["recomputed_trace_artifact_id"] == trace.artifact.id
            and verification["verification_artifact_id"] == verification_artifact.artifact.id
        )
