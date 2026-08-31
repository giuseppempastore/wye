"""Deterministic Phase 7.6.4A target, mapping-state and input construction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Mapping

from app.repositories.scientific_mapping_state import (
    MappingHistoryRows,
    PostgresScientificMappingStateRepository,
)
from app.scientific_evaluation.canonicalization import canonical_sha256
from app.scientific_evaluation.errors import (
    CanonicalInputIntegrityError,
    CounterfactualAuthorizationUnavailableError,
    EvaluationTargetNotFoundError,
    HistoricalTargetStateUnavailableError,
    InvalidProtocolLifecycleError,
    MappingInputRequestError,
    MappingStateInconsistentError,
    UnsealedEvidenceSnapshotError,
)
from app.scientific_evaluation.mapping_inputs import (
    CanonicalEvaluationInputRequest,
    MappingMemberDescriptor,
    NonMemberObservation,
    RELATIONSHIP_TYPES,
    build_authority_chain_payload,
    build_evaluation_input_payload,
    build_mapping_manifest_payload,
    build_mapping_member_identity,
    build_mapping_member_payload,
    build_non_member_observation,
    build_observation_subject_identity,
    build_target_payload,
    canonical_observations,
    mapping_day,
    order_authority_chains,
    validate_request,
)
from app.services.scientific_evaluation_artifacts import (
    PersistedScientificArtifact,
    ScientificArtifactWriteRequest,
    ScientificArtifactWriter,
)


@dataclass(frozen=True)
class CanonicalTargetResult:
    target_type: str
    entity_id: int
    artifact: PersistedScientificArtifact


@dataclass(frozen=True)
class CanonicalMappingMemberResult:
    bridge_id: int
    member_identity_digest: bytes
    descriptor: MappingMemberDescriptor
    artifact: PersistedScientificArtifact
    authority_chain_count: int


@dataclass(frozen=True)
class CanonicalMappingStateResult:
    resolution_state: str
    members: tuple[CanonicalMappingMemberResult, ...]
    observations: tuple[NonMemberObservation, ...]
    manifest_artifact: PersistedScientificArtifact

    @property
    def mapping_snapshot_digest(self) -> bytes:
        return self.manifest_artifact.artifact.content_digest


@dataclass(frozen=True)
class CanonicalEvaluationInputResult:
    request: CanonicalEvaluationInputRequest
    target: CanonicalTargetResult
    mapping_state: CanonicalMappingStateResult | None
    input_artifact: PersistedScientificArtifact

    @property
    def input_digest(self) -> bytes:
        return self.input_artifact.artifact.content_digest


class ScientificMappingStateService:
    """Build content-addressed roots inside a caller-owned transaction."""

    def __init__(
        self,
        repository: PostgresScientificMappingStateRepository | None = None,
        artifact_writer: ScientificArtifactWriter | None = None,
    ):
        self.repository = repository or PostgresScientificMappingStateRepository()
        self.artifact_writer = artifact_writer or ScientificArtifactWriter()

    def build_evaluation_input(
        self, cursor, request: CanonicalEvaluationInputRequest
    ) -> CanonicalEvaluationInputResult:
        validate_request(request)
        target = self._write_target(
            cursor,
            target_type=request.target_type,
            entity_id=request.target_id,
            as_of=request.as_of,
        )
        mapping_state: CanonicalMappingStateResult | None
        if request.target_type == "ingredient":
            mapping_state = self._build_ingredient_mapping_state(
                cursor,
                ingredient_id=request.target_id,
                as_of=request.as_of,
                ingredient_target=target,
            )
            resolution_state = mapping_state.resolution_state
            manifest_digest = mapping_state.mapping_snapshot_digest
        else:
            mapping_state = None
            resolution_state = "not_applicable"
            manifest_digest = None

        input_payload = build_evaluation_input_payload(
            request=request,
            target_artifact_digest=target.artifact.artifact.content_digest,
            mapping_resolution_state=resolution_state,
            mapping_manifest_digest=manifest_digest,
        )
        input_artifact = self.artifact_writer.write_verified_inline(
            cursor,
            ScientificArtifactWriteRequest(
                "scientific_evaluation_input", "1", input_payload
            ),
        )
        return CanonicalEvaluationInputResult(
            request=request,
            target=target,
            mapping_state=mapping_state,
            input_artifact=input_artifact,
        )

    def validate_execution_prerequisites(
        self,
        cursor,
        *,
        snapshot_id: int,
        protocol_version_id: int,
        execution_type: str,
    ) -> None:
        if execution_type not in {"NORMAL", "REPLAY", "COUNTERFACTUAL", "REFRESH"}:
            raise MappingInputRequestError("unsupported execution_type")
        snapshot = self.repository.load_snapshot_prerequisite(cursor, snapshot_id)
        if snapshot is None or snapshot["status"] != "sealed":
            raise UnsealedEvidenceSnapshotError("execution requires a sealed evidence snapshot")
        protocol = self.repository.load_protocol_prerequisite(cursor, protocol_version_id)
        if protocol is None:
            raise InvalidProtocolLifecycleError("protocol version does not exist")
        lifecycle = protocol["lifecycle_status"]
        if execution_type in {"NORMAL", "REFRESH"}:
            allowed = lifecycle == "published"
        else:
            allowed = lifecycle in {"published", "deprecated", "retired"}
        if not allowed or protocol["published_at"] is None or protocol["protocol_digest"] is None:
            raise InvalidProtocolLifecycleError(
                f"protocol lifecycle {lifecycle} is not executable for {execution_type}"
            )
        if execution_type == "COUNTERFACTUAL":
            raise CounterfactualAuthorizationUnavailableError(
                "current governance runtime cannot prove counterfactual authorization"
            )

    def _write_target(
        self,
        cursor,
        *,
        target_type: str,
        entity_id: int,
        as_of: datetime,
    ) -> CanonicalTargetResult:
        row = self.repository.load_target(cursor, target_type, entity_id)
        if row is None:
            raise EvaluationTargetNotFoundError(
                f"{target_type} target {entity_id} does not exist"
            )
        as_of_utc = as_of.astimezone(timezone.utc)
        if row["created_at"] > as_of_utc or row["updated_at"] > as_of_utc:
            raise HistoricalTargetStateUnavailableError(
                f"{target_type} {entity_id} state was recorded after as_of"
            )
        payload = build_target_payload(target_type=target_type, row=row, as_of=as_of)
        artifact = self.artifact_writer.write_verified_inline(
            cursor,
            ScientificArtifactWriteRequest("scientific_evaluation_target", "1", payload),
        )
        return CanonicalTargetResult(target_type, entity_id, artifact)

    def _build_ingredient_mapping_state(
        self,
        cursor,
        *,
        ingredient_id: int,
        as_of: datetime,
        ingredient_target: CanonicalTargetResult,
    ) -> CanonicalMappingStateResult:
        self.repository.lock_mapping_history(cursor)
        history = self.repository.load_mapping_history(cursor, ingredient_id)
        day = mapping_day(as_of)
        as_of_utc = as_of.astimezone(timezone.utc)
        visible = self._visible_history(history, as_of_utc)
        observations: list[NonMemberObservation] = []

        bridges = {row["id"]: row for row in visible.bridges}
        proposals = {row["id"]: row for row in visible.proposals}
        decisions = {row["id"]: row for row in visible.decisions}
        closures_by_bridge: dict[int, list[dict[str, Any]]] = {}
        for closure in history.closures:
            closures_by_bridge.setdefault(closure["ingredient_substance_id"], []).append(closure)

        closure_views: dict[int, tuple[date | None, dict[str, Any] | None, bool]] = {}
        for bridge in visible.bridges:
            effective_to, closure, inconsistent = self._closure_view(
                bridge, closures_by_bridge.get(bridge["id"], []), as_of_utc
            )
            closure_views[bridge["id"]] = effective_to, closure, inconsistent
            if inconsistent:
                observations.append(
                    self._observation(
                        observation_kind="closure",
                        reason_code="closure_history_inconsistent",
                        ingredient_id=ingredient_id,
                        bridge=bridge,
                        closure=closure,
                        recorded_at=(
                            self._recorded_at(closure, "closed_at", "created_at")
                            if closure is not None
                            else bridge["created_at"]
                        ),
                        effective_from=bridge.get("valid_from"),
                        effective_to=effective_to,
                    )
                )

        materializations_by_proposal: dict[int, list[dict[str, Any]]] = {}
        for materialization in visible.materializations:
            materializations_by_proposal.setdefault(
                materialization["proposal_id"], []
            ).append(materialization)

        chain_rows_by_bridge: dict[
            int, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]
        ] = {}
        valid_proposal_ids: set[int] = set()
        invalid_materializations: set[int] = set()
        for materialization in visible.materializations:
            proposal = proposals.get(materialization["proposal_id"])
            decision = decisions.get(materialization["decision_id"])
            bridge = bridges.get(materialization["ingredient_substance_id"])
            consistent = (
                proposal is not None
                and decision is not None
                and bridge is not None
                and decision["proposal_id"] == proposal["id"]
                and proposal["ingredient_id"] == bridge["ingredient_id"] == ingredient_id
                and proposal["substance_id"] == bridge["substance_id"]
                and proposal["relationship_type"] == bridge["relationship_type"]
                and decision["decision_type"] == "accept"
                and materialization["materialization_status"] in {"applied", "already_current"}
                and bridge["mapping_status"] == "accepted"
                and bridge["relationship_type"] in RELATIONSHIP_TYPES
            )
            if not consistent:
                invalid_materializations.add(materialization["id"])
                observations.append(
                    self._observation(
                        observation_kind="materialization",
                        reason_code="materialization_inconsistent",
                        ingredient_id=ingredient_id,
                        bridge=bridge,
                        proposal=proposal,
                        decision=decision,
                        materialization=materialization,
                        recorded_at=self._recorded_at(
                            materialization, "materialized_at", "created_at"
                        ),
                    )
                )
                continue
            if decision["effective_from"] > day:
                observations.append(
                    self._observation(
                        observation_kind="decision",
                        reason_code="accepted_authority_not_effective",
                        ingredient_id=ingredient_id,
                        bridge=bridge,
                        proposal=proposal,
                        decision=decision,
                        recorded_at=self._recorded_at(decision, "reviewed_at", "created_at"),
                        effective_from=decision["effective_from"],
                    )
                )
                continue
            if bridge["valid_from"] is None:
                observations.append(
                    self._observation(
                        observation_kind="bridge",
                        reason_code="history_incomplete",
                        ingredient_id=ingredient_id,
                        bridge=bridge,
                        recorded_at=bridge["created_at"],
                    )
                )
                continue
            if closure_views[bridge["id"]][2]:
                continue
            chain_rows_by_bridge.setdefault(bridge["id"], []).append(
                (proposal, decision, materialization)
            )
            valid_proposal_ids.add(proposal["id"])

        member_results: list[CanonicalMappingMemberResult] = []
        included_bridge_ids: set[int] = set()
        substance_targets: dict[int, CanonicalTargetResult] = {}
        for bridge_id, chain_rows in chain_rows_by_bridge.items():
            bridge = bridges[bridge_id]
            effective_to, closure, _ = closure_views[bridge_id]
            if not self._effective_on_day(bridge["valid_from"], effective_to, day):
                observations.append(
                    self._observation(
                        observation_kind="bridge",
                        reason_code="out_of_effective_range",
                        ingredient_id=ingredient_id,
                        bridge=bridge,
                        recorded_at=bridge["created_at"],
                        effective_from=bridge["valid_from"],
                        effective_to=effective_to,
                    )
                )
                continue
            chains = [
                build_authority_chain_payload(
                    bridge_id=bridge_id,
                    proposal=proposal,
                    decision=decision,
                    materialization=materialization,
                )
                for proposal, decision, materialization in chain_rows
            ]
            ordered_chains = order_authority_chains(chains)
            substance_target = substance_targets.get(bridge["substance_id"])
            if substance_target is None:
                substance_target = self._write_target(
                    cursor,
                    target_type="substance",
                    entity_id=bridge["substance_id"],
                    as_of=as_of,
                )
                substance_targets[bridge["substance_id"]] = substance_target
            identity_payload = build_mapping_member_identity(bridge)
            identity_digest = canonical_sha256(identity_payload)
            member_payload = build_mapping_member_payload(
                bridge=bridge,
                member_identity_digest=identity_digest,
                ingredient_target_digest=ingredient_target.artifact.artifact.content_digest,
                substance_target_digest=substance_target.artifact.artifact.content_digest,
                as_of=as_of,
                day=day,
                effective_valid_to=effective_to,
                closure=closure,
                authority_chains=ordered_chains,
            )
            member_artifact = self.artifact_writer.write_verified_inline(
                cursor,
                ScientificArtifactWriteRequest(
                    "scientific_mapping_state_member", "1", member_payload
                ),
            )
            descriptor = MappingMemberDescriptor(
                relationship_type=bridge["relationship_type"],
                substance_target_digest=substance_target.artifact.artifact.content_digest,
                member_identity_digest=identity_digest,
                member_semantic_digest=member_artifact.artifact.content_digest,
            )
            member_results.append(
                CanonicalMappingMemberResult(
                    bridge_id=bridge_id,
                    member_identity_digest=identity_digest,
                    descriptor=descriptor,
                    artifact=member_artifact,
                    authority_chain_count=len(ordered_chains),
                )
            )
            included_bridge_ids.add(bridge_id)

        self._append_bridge_observations(
            observations=observations,
            bridges=visible.bridges,
            included_bridge_ids=included_bridge_ids,
            chain_rows_by_bridge=chain_rows_by_bridge,
            closure_views=closure_views,
            ingredient_id=ingredient_id,
            day=day,
        )
        self._append_proposal_observations(
            observations=observations,
            proposals=visible.proposals,
            decisions=visible.decisions,
            materializations=visible.materializations,
            bridges=bridges,
            valid_proposal_ids=valid_proposal_ids,
            invalid_materializations=invalid_materializations,
            ingredient_id=ingredient_id,
            day=day,
        )

        manifest_payload, resolution_state = build_mapping_manifest_payload(
            as_of=as_of,
            day=day,
            ingredient_target_digest=ingredient_target.artifact.artifact.content_digest,
            members=[member.descriptor for member in member_results],
            observations=observations,
            visible_history=bool(visible.bridges or visible.proposals),
        )
        manifest_artifact = self.artifact_writer.write_verified_inline(
            cursor,
            ScientificArtifactWriteRequest(
                "scientific_mapping_state_manifest", "1", manifest_payload
            ),
        )
        ordered_observations = tuple(canonical_observations(observations))
        member_results.sort(key=lambda member: member.descriptor.order_key())
        return CanonicalMappingStateResult(
            resolution_state=resolution_state,
            members=tuple(member_results),
            observations=ordered_observations,
            manifest_artifact=manifest_artifact,
        )

    @staticmethod
    def _visible_history(
        history: MappingHistoryRows, as_of: datetime
    ) -> MappingHistoryRows:
        bridges = tuple(row for row in history.bridges if row["created_at"] <= as_of)
        proposals = tuple(row for row in history.proposals if row["created_at"] <= as_of)
        decisions = tuple(
            row
            for row in history.decisions
            if row["created_at"] <= as_of and row["reviewed_at"] <= as_of
        )
        materializations = tuple(
            row
            for row in history.materializations
            if row["created_at"] <= as_of and row["materialized_at"] <= as_of
        )
        closures = tuple(
            row
            for row in history.closures
            if row["created_at"] <= as_of and row["closed_at"] <= as_of
        )
        return MappingHistoryRows(bridges, proposals, decisions, materializations, closures)

    @staticmethod
    def _closure_view(
        bridge: Mapping[str, Any], closures: list[dict[str, Any]], as_of: datetime
    ) -> tuple[date | None, dict[str, Any] | None, bool]:
        visible = [
            closure
            for closure in closures
            if closure["created_at"] <= as_of and closure["closed_at"] <= as_of
        ]
        if len(visible) > 1:
            return bridge.get("valid_to"), visible[0], True
        if visible:
            closure = visible[0]
            return closure["valid_to"], closure, bridge.get("valid_to") != closure["valid_to"]
        if closures:
            # A closure recorded later must not leak into the earlier view even
            # though the bridge row has already been updated in current state.
            return None, None, False
        if bridge.get("valid_to") is not None:
            return bridge["valid_to"], None, True
        return None, None, False

    @staticmethod
    def _effective_on_day(valid_from: date | None, valid_to: date | None, day: date) -> bool:
        return valid_from is not None and valid_from <= day and (
            valid_to is None or valid_to >= day
        )

    def _append_bridge_observations(
        self,
        *,
        observations: list[NonMemberObservation],
        bridges: tuple[dict[str, Any], ...],
        included_bridge_ids: set[int],
        chain_rows_by_bridge: dict[int, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]],
        closure_views: dict[int, tuple[date | None, dict[str, Any] | None, bool]],
        ingredient_id: int,
        day: date,
    ) -> None:
        status_reasons = {
            "pending_review": "pending_review_bridge",
            "ambiguous": "ambiguous_bridge",
            "rejected": "rejected_bridge",
            "legacy_unreviewed": "legacy_unreviewed_bridge",
        }
        for bridge in bridges:
            if bridge["ingredient_id"] != ingredient_id:
                raise MappingStateInconsistentError("cross-ingredient bridge loaded")
            if bridge["id"] in included_bridge_ids or closure_views[bridge["id"]][2]:
                continue
            effective_to = closure_views[bridge["id"]][0]
            if bridge["mapping_status"] == "accepted" and bridge.get("valid_from") is None:
                observations.append(
                    self._observation(
                        observation_kind="bridge",
                        reason_code="history_incomplete",
                        ingredient_id=ingredient_id,
                        bridge=bridge,
                        recorded_at=bridge["created_at"],
                        effective_to=effective_to,
                    )
                )
                continue
            reason = status_reasons.get(bridge["mapping_status"])
            if reason is not None:
                # Non-authoritative bridge states remain visible provenance even
                # without a usable validity start. Omitting them would turn
                # unresolved history into a false empty state.
                observations.append(
                    self._observation(
                        observation_kind="bridge",
                        reason_code=reason,
                        ingredient_id=ingredient_id,
                        bridge=bridge,
                        recorded_at=bridge["created_at"],
                        effective_from=bridge.get("valid_from"),
                        effective_to=effective_to,
                    )
                )
                continue
            if not self._effective_on_day(bridge.get("valid_from"), effective_to, day):
                if bridge["id"] not in chain_rows_by_bridge:
                    continue
                # Controlled out-of-range bridges were emitted in the member loop.
                continue
            if bridge["mapping_status"] == "accepted":
                if bridge["id"] in chain_rows_by_bridge:
                    continue
                reason = "uncontrolled_accepted_bridge"
            else:
                continue
            observations.append(
                self._observation(
                    observation_kind="bridge",
                    reason_code=reason,
                    ingredient_id=ingredient_id,
                    bridge=bridge,
                    recorded_at=bridge["created_at"],
                    effective_from=bridge.get("valid_from"),
                    effective_to=effective_to,
                )
            )

    def _append_proposal_observations(
        self,
        *,
        observations: list[NonMemberObservation],
        proposals: tuple[dict[str, Any], ...],
        decisions: tuple[dict[str, Any], ...],
        materializations: tuple[dict[str, Any], ...],
        bridges: dict[int, dict[str, Any]],
        valid_proposal_ids: set[int],
        invalid_materializations: set[int],
        ingredient_id: int,
        day: date,
    ) -> None:
        decisions_by_proposal: dict[int, list[dict[str, Any]]] = {}
        for decision in decisions:
            decisions_by_proposal.setdefault(decision["proposal_id"], []).append(decision)
        mats_by_decision: dict[int, list[dict[str, Any]]] = {}
        for materialization in materializations:
            mats_by_decision.setdefault(materialization["decision_id"], []).append(materialization)
        for proposal in proposals:
            if proposal["id"] in valid_proposal_ids:
                continue
            proposal_decisions = decisions_by_proposal.get(proposal["id"], [])
            terminal = next(
                (item for item in proposal_decisions if item["decision_type"] in {"accept", "reject"}),
                None,
            )
            if terminal is not None and terminal["decision_type"] == "reject":
                observations.append(
                    self._observation(
                        observation_kind="decision",
                        reason_code="rejected_decision",
                        ingredient_id=ingredient_id,
                        proposal=proposal,
                        decision=terminal,
                        recorded_at=self._recorded_at(terminal, "reviewed_at", "created_at"),
                    )
                )
                continue
            if terminal is not None:
                if terminal["effective_from"] > day:
                    observations.append(
                        self._observation(
                            observation_kind="decision",
                            reason_code="accepted_authority_not_effective",
                            ingredient_id=ingredient_id,
                            proposal=proposal,
                            decision=terminal,
                            recorded_at=self._recorded_at(terminal, "reviewed_at", "created_at"),
                            effective_from=terminal["effective_from"],
                        )
                    )
                    continue
                terminal_mats = mats_by_decision.get(terminal["id"], [])
                if not terminal_mats:
                    observations.append(
                        self._observation(
                            observation_kind="decision",
                            reason_code="accepted_not_materialized_as_of",
                            ingredient_id=ingredient_id,
                            proposal=proposal,
                            decision=terminal,
                            recorded_at=self._recorded_at(terminal, "reviewed_at", "created_at"),
                            effective_from=terminal["effective_from"],
                        )
                    )
                elif all(item["id"] in invalid_materializations for item in terminal_mats):
                    pass
                continue
            deferred = [item for item in proposal_decisions if item["decision_type"] == "defer"]
            if deferred:
                decision = max(deferred, key=lambda row: (row["reviewed_at"], row["id"]))
                observations.append(
                    self._observation(
                        observation_kind="decision",
                        reason_code="deferred_decision",
                        ingredient_id=ingredient_id,
                        proposal=proposal,
                        decision=decision,
                        recorded_at=self._recorded_at(decision, "reviewed_at", "created_at"),
                    )
                )
            else:
                observations.append(
                    self._observation(
                        observation_kind="proposal",
                        reason_code="pending_proposal",
                        ingredient_id=ingredient_id,
                        proposal=proposal,
                        recorded_at=proposal["created_at"],
                    )
                )

    def _observation(
        self,
        *,
        observation_kind: str,
        reason_code: str,
        ingredient_id: int,
        recorded_at: datetime,
        bridge: Mapping[str, Any] | None = None,
        proposal: Mapping[str, Any] | None = None,
        decision: Mapping[str, Any] | None = None,
        materialization: Mapping[str, Any] | None = None,
        closure: Mapping[str, Any] | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
    ) -> NonMemberObservation:
        bridge_id = bridge["id"] if bridge is not None else None
        proposal_id = proposal["id"] if proposal is not None else None
        decision_id = decision["id"] if decision is not None else None
        materialization_id = materialization["id"] if materialization is not None else None
        closure_id = closure["id"] if closure is not None else None
        subject_identity = build_observation_subject_identity(
            observation_kind=observation_kind,
            bridge_id=bridge_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            materialization_id=materialization_id,
            closure_id=closure_id,
        )
        context = bridge or proposal
        if context is None:
            raise CanonicalInputIntegrityError("observation has no bridge/proposal context")
        return build_non_member_observation(
            observation_kind=observation_kind,
            reason_code=reason_code,
            subject_identity=subject_identity,
            ingredient_id=ingredient_id,
            bridge_id=bridge_id,
            substance_id=context.get("substance_id"),
            relationship_type=context.get("relationship_type"),
            authority_chain_identity_digest=None,
            recorded_at=recorded_at,
            effective_from=effective_from,
            effective_to=effective_to,
        )

    @staticmethod
    def _recorded_at(record: Mapping[str, Any], *fields: str) -> datetime:
        values = [record[field] for field in fields if record.get(field) is not None]
        if not values:
            raise CanonicalInputIntegrityError("historical observation has no recorded timestamp")
        return max(values)
