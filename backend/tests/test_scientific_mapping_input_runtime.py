"""Real PostgreSQL tests for Phase 7.6.4A canonical mapping/input runtime."""

from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import threading
import unittest
import uuid

import psycopg2

TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_scientific_evidence_snapshots import (  # noqa: E402
    _alembic,
    _connection,
    _create_database,
    _drop_database,
)

from app.scientific_evaluation.errors import (  # noqa: E402
    CounterfactualAuthorizationUnavailableError,
    HistoricalTargetStateUnavailableError,
    InvalidProtocolLifecycleError,
    UnsealedEvidenceSnapshotError,
    UnsupportedEvaluationTargetError,
)
from app.scientific_evaluation.mapping_inputs import (  # noqa: E402
    CanonicalEvaluationInputRequest,
)
from app.scientific_evaluation.snapshots import (  # noqa: E402
    SnapshotConstructionRequest,
)
from app.services.scientific_evaluation_artifacts import (  # noqa: E402
    ScientificArtifactWriteRequest,
    ScientificArtifactWriter,
)
from app.services.scientific_evidence_snapshots import (  # noqa: E402
    ScientificEvidenceSnapshotService,
)
from app.services.scientific_mapping_state import (  # noqa: E402
    ScientificMappingStateService,
)


UTC = timezone.utc
BASE = datetime(2026, 1, 2, 9, 0, tzinfo=UTC)
AS_OF = datetime(2030, 8, 30, 12, 0, tzinfo=UTC)


def _request(target_type, target_id, as_of=AS_OF):
    return CanonicalEvaluationInputRequest(target_type, target_id, as_of)


@unittest.skipUnless(
    os.getenv("WYE_RUN_MAPPING_INPUT_POSTGRES_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificMappingInputRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = _create_database("mapping_input")
        try:
            _alembic(cls.database, "upgrade", "head")
        except Exception:
            _drop_database(cls.database)
            raise

    @classmethod
    def tearDownClass(cls):
        _drop_database(cls.database)

    def setUp(self):
        self.connection = _connection(self.database)
        self.connection.autocommit = False
        self.cursor = self.connection.cursor()
        self.service = ScientificMappingStateService()

    def tearDown(self):
        try:
            self.connection.rollback()
        finally:
            self.cursor.close()
            self.connection.close()

    def _targets(self):
        token = uuid.uuid4().hex
        self.cursor.execute(
            "INSERT INTO ingredients(canonical_name,common_name,ingredient_group,cas_number,"
            "created_at,updated_at) VALUES(%s,%s,'test_group','77-92-9',%s,%s) RETURNING id",
            (
                f"Mapping input ingredient {token}",
                f"Ingredient {token}",
                BASE - timedelta(days=365),
                BASE - timedelta(days=365),
            ),
        )
        ingredient_id = self.cursor.fetchone()[0]
        self.cursor.execute(
            "INSERT INTO substances(preferred_name,normalized_name,substance_type,status,"
            "created_at,updated_at) VALUES(%s,%s,'chemical_substance','active',%s,%s) RETURNING id",
            (
                f"Mapping substance {token}",
                f"mapping substance {token}",
                BASE - timedelta(days=365),
                BASE - timedelta(days=365),
            ),
        )
        substance_id = self.cursor.fetchone()[0]
        return ingredient_id, substance_id

    def _bridge(
        self,
        ingredient_id,
        substance_id,
        *,
        relationship="represents",
        status="accepted",
        method="manual_review",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        created_at=BASE,
    ):
        reviewed = BASE if method == "manual_review" and status in {
            "accepted", "ambiguous", "rejected"
        } else None
        self.cursor.execute(
            "INSERT INTO ingredient_substances(ingredient_id,substance_id,"
            "relationship_type,mapping_method,mapping_status,reviewed_by,reviewed_at,"
            "valid_from,valid_to,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "RETURNING id",
            (
                ingredient_id,
                substance_id,
                relationship,
                method,
                status,
                "reviewer:test" if reviewed else None,
                reviewed,
                valid_from,
                valid_to,
                created_at,
            ),
        )
        return self.cursor.fetchone()[0]

    def _authority(
        self,
        ingredient_id,
        substance_id,
        *,
        bridge_id=None,
        relationship="represents",
        outcome="applied",
        offset=0,
        materialize=True,
        decision_type="accept",
        effective_from=date(2026, 1, 1),
    ):
        when = BASE + timedelta(minutes=offset)
        proposal_key = uuid.uuid4()
        proposal_status = (
            "accepted" if decision_type == "accept" else "rejected" if decision_type == "reject" else "pending_review"
        )
        self.cursor.execute(
            "INSERT INTO ingredient_substance_mapping_proposals("
            "proposal_key,ingredient_id,substance_id,relationship_type,mapping_method,"
            "mapping_confidence,proposed_by,proposal_status,provenance,created_at) "
            "VALUES(%s,%s,%s,%s,'manual_review',0.900,'proposer:test',%s,%s::jsonb,%s) RETURNING id",
            (
                str(proposal_key),
                ingredient_id,
                substance_id,
                relationship,
                proposal_status,
                '{"fixture":"mapping_input"}',
                when,
            ),
        )
        proposal_id = self.cursor.fetchone()[0]
        self.cursor.execute(
            "INSERT INTO ingredient_substance_mapping_decisions("
            "proposal_id,decision_type,effective_from,reviewed_by,reviewed_at,reason_code,created_at) "
            "VALUES(%s,%s,%s,'reviewer:test',%s,'fixture_decision',%s) RETURNING id",
            (
                proposal_id,
                decision_type,
                effective_from if decision_type == "accept" else None,
                when + timedelta(seconds=10),
                when + timedelta(seconds=10),
            ),
        )
        decision_id = self.cursor.fetchone()[0]
        if decision_type == "accept" and bridge_id is None:
            bridge_id = self._bridge(
                ingredient_id,
                substance_id,
                relationship=relationship,
                created_at=when + timedelta(seconds=15),
            )
        materialization_id = None
        if decision_type == "accept" and materialize:
            self.cursor.execute(
                "INSERT INTO ingredient_substance_mapping_materializations("
                "decision_id,proposal_id,ingredient_substance_id,materialization_status,"
                "materialized_by,materialized_at,created_at) "
                "VALUES(%s,%s,%s,%s,'worker:test',%s,%s) RETURNING id",
                (
                    decision_id,
                    proposal_id,
                    bridge_id,
                    outcome,
                    when + timedelta(seconds=20),
                    when + timedelta(seconds=20),
                ),
            )
            materialization_id = self.cursor.fetchone()[0]
        return {
            "bridge_id": bridge_id,
            "proposal_id": proposal_id,
            "decision_id": decision_id,
            "materialization_id": materialization_id,
        }

    def _pending_proposal(self, ingredient_id, substance_id, *, relationship="contains"):
        self.cursor.execute(
            "INSERT INTO ingredient_substance_mapping_proposals("
            "proposal_key,ingredient_id,substance_id,relationship_type,mapping_method,"
            "proposed_by,created_at) VALUES(%s,%s,%s,%s,'manual_review','proposer:test',%s) "
            "RETURNING id",
            (str(uuid.uuid4()), ingredient_id, substance_id, relationship, BASE),
        )
        return self.cursor.fetchone()[0]

    def _artifact_payload(self, artifact_id):
        self.cursor.execute(
            "SELECT json_payload->'payload' FROM scientific_evaluation_artifacts WHERE id=%s",
            (artifact_id,),
        )
        return self.cursor.fetchone()[0]

    def test_targets_empty_mapping_and_product_rejection(self):
        ingredient_id, substance_id = self._targets()
        ingredient = self.service.build_evaluation_input(
            self.cursor, _request("ingredient", ingredient_id)
        )
        self.assertEqual(ingredient.mapping_state.resolution_state, "empty")
        self.assertEqual(ingredient.mapping_state.members, ())
        self.assertEqual(
            self._artifact_payload(ingredient.input_artifact.artifact.id)["mapping_state"]["applicability"],
            "required",
        )
        substance = self.service.build_evaluation_input(
            self.cursor, _request("substance", substance_id)
        )
        self.assertIsNone(substance.mapping_state)
        self.assertEqual(
            self._artifact_payload(substance.input_artifact.artifact.id)["mapping_state"],
            {"applicability": "not_applicable", "manifest_digest": None, "resolution_state": "not_applicable"},
        )
        with self.assertRaises(UnsupportedEvaluationTargetError):
            self.service.build_evaluation_input(self.cursor, _request("product", 1))
        historical_ingredient, _ = self._targets()
        self.cursor.execute(
            "UPDATE ingredients SET updated_at=%s WHERE id=%s",
            (AS_OF + timedelta(seconds=1), historical_ingredient),
        )
        with self.assertRaises(HistoricalTargetStateUnavailableError):
            self.service.build_evaluation_input(
                self.cursor, _request("ingredient", historical_ingredient)
            )

    def test_one_applied_authority_builds_member_manifest_and_input(self):
        ingredient_id, substance_id = self._targets()
        authority = self._authority(ingredient_id, substance_id)
        result = self.service.build_evaluation_input(
            self.cursor, _request("ingredient", ingredient_id)
        )
        mapping = result.mapping_state
        self.assertEqual((mapping.resolution_state, len(mapping.members)), ("resolved", 1))
        self.assertEqual(mapping.members[0].bridge_id, authority["bridge_id"])
        self.assertEqual(mapping.members[0].authority_chain_count, 1)
        member_payload = self._artifact_payload(mapping.members[0].artifact.artifact.id)
        self.assertEqual(member_payload["authority_chains"][0]["materialization"]["materialization_status"], "applied")
        manifest = self._artifact_payload(mapping.manifest_artifact.artifact.id)
        self.assertEqual((manifest["member_count"], manifest["observation_count"]), (1, 0))
        self.assertEqual(mapping.mapping_snapshot_digest.hex(), self._artifact_payload(result.input_artifact.artifact.id)["mapping_state"]["manifest_digest"])

    def test_multiple_authorities_share_one_member_and_are_ordered(self):
        ingredient_id, substance_id = self._targets()
        first = self._authority(ingredient_id, substance_id, offset=2)
        self._authority(
            ingredient_id,
            substance_id,
            bridge_id=first["bridge_id"],
            outcome="already_current",
            offset=1,
        )
        result = self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        self.assertEqual(len(result.mapping_state.members), 1)
        member = result.mapping_state.members[0]
        self.assertEqual(member.authority_chain_count, 2)
        payload = self._artifact_payload(member.artifact.artifact.id)
        self.assertEqual(
            [item["materialization"]["materialization_status"] for item in payload["authority_chains"]],
            ["already_current", "applied"],
        )

    def test_authority_timestamp_tie_uses_identity_digest(self):
        ingredient_id, substance_id = self._targets()
        first = self._authority(ingredient_id, substance_id, offset=1)
        self._authority(
            ingredient_id,
            substance_id,
            bridge_id=first["bridge_id"],
            outcome="already_current",
            offset=1,
        )
        result = self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        chains = self._artifact_payload(result.mapping_state.members[0].artifact.artifact.id)["authority_chains"]
        digests = [item["authority_chain_identity_digest"] for item in chains]
        self.assertEqual(digests, sorted(digests))

    def test_controlled_adoption_is_not_retroactive(self):
        ingredient_id, substance_id = self._targets()
        bridge_id = self._bridge(
            ingredient_id,
            substance_id,
            method="legacy",
            created_at=BASE - timedelta(days=10),
        )
        self._authority(
            ingredient_id,
            substance_id,
            bridge_id=bridge_id,
            outcome="already_current",
            offset=10,
        )
        before = self.service.build_evaluation_input(
            self.cursor,
            _request("ingredient", ingredient_id, BASE + timedelta(minutes=5)),
        )
        self.assertEqual(before.mapping_state.resolution_state, "history_unavailable")
        self.assertIn("uncontrolled_accepted_bridge", {o.reason_code for o in before.mapping_state.observations})
        after = self.service.build_evaluation_input(
            self.cursor,
            _request("ingredient", ingredient_id, BASE + timedelta(minutes=11)),
        )
        self.assertEqual((after.mapping_state.resolution_state, len(after.mapping_state.members)), ("resolved", 1))

    def test_resolution_states_and_non_member_observations(self):
        ingredient_id, substance_id = self._targets()
        self._pending_proposal(ingredient_id, substance_id)
        unavailable = self.service.build_evaluation_input(
            self.cursor, _request("ingredient", ingredient_id)
        )
        self.assertEqual(unavailable.mapping_state.resolution_state, "history_unavailable")
        self.assertEqual(unavailable.mapping_state.observations[0].reason_code, "pending_proposal")
        other = self._targets()[1]
        self._authority(ingredient_id, other, relationship="contains")
        partial = self.service.build_evaluation_input(
            self.cursor, _request("ingredient", ingredient_id)
        )
        self.assertEqual(partial.mapping_state.resolution_state, "partially_resolved")
        manifest = self._artifact_payload(partial.mapping_state.manifest_artifact.artifact.id)
        self.assertEqual(manifest["resolution_reason_codes"], ["additional_candidates_unresolved", "pending_proposal"])

    def test_rejected_deferred_ambiguous_and_unmaterialized_classification(self):
        ingredient_id, substance_id = self._targets()
        self._authority(ingredient_id, substance_id, decision_type="reject", materialize=False)
        deferred_substance = self._targets()[1]
        self._authority(ingredient_id, deferred_substance, decision_type="defer", materialize=False)
        ambiguous_substance = self._targets()[1]
        self._bridge(ingredient_id, ambiguous_substance, status="ambiguous")
        accepted_substance = self._targets()[1]
        self._authority(ingredient_id, accepted_substance, materialize=False)
        result = self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        reasons = {item.reason_code for item in result.mapping_state.observations}
        self.assertTrue(
            {"rejected_decision", "deferred_decision", "ambiguous_bridge", "accepted_not_materialized_as_of"}.issubset(reasons)
        )
        self.assertEqual(result.mapping_state.resolution_state, "history_unavailable")

    def test_recorded_materialization_and_effective_authority_boundaries(self):
        ingredient_id, substance_id = self._targets()
        future_materialization = self._authority(ingredient_id, substance_id)
        future_time = BASE + timedelta(days=2)
        self.cursor.execute(
            "UPDATE ingredient_substance_mapping_materializations "
            "SET materialized_at=%s,created_at=%s WHERE id=%s",
            (future_time, future_time, future_materialization["materialization_id"]),
        )
        not_yet_materialized = self.service.build_evaluation_input(
            self.cursor,
            _request("ingredient", ingredient_id, BASE + timedelta(days=1)),
        )
        self.assertIn(
            "accepted_not_materialized_as_of",
            {item.reason_code for item in not_yet_materialized.mapping_state.observations},
        )

        later_substance = self._targets()[1]
        bridge_id = self._bridge(
            ingredient_id,
            later_substance,
            relationship="contains",
            valid_from=date(2031, 1, 1),
        )
        self._authority(
            ingredient_id,
            later_substance,
            bridge_id=bridge_id,
            relationship="contains",
            effective_from=date(2031, 1, 1),
        )
        not_yet_effective = self.service.build_evaluation_input(
            self.cursor, _request("ingredient", ingredient_id)
        )
        self.assertIn(
            "accepted_authority_not_effective",
            {item.reason_code for item in not_yet_effective.mapping_state.observations},
        )

    def test_inconsistent_materialization_invalidates_reconstruction(self):
        ingredient_id, substance_id = self._targets()
        other_substance = self._targets()[1]
        bridge_id = self._bridge(ingredient_id, other_substance)
        self._authority(ingredient_id, substance_id, bridge_id=bridge_id)
        result = self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        self.assertEqual(result.mapping_state.resolution_state, "history_unavailable")
        self.assertIn("materialization_inconsistent", {o.reason_code for o in result.mapping_state.observations})

    def test_effective_date_and_future_closure_visibility(self):
        ingredient_id, substance_id = self._targets()
        authority = self._authority(ingredient_id, substance_id)
        closure_time = BASE + timedelta(days=10)
        self.cursor.execute(
            "UPDATE ingredient_substances SET valid_to=%s WHERE id=%s",
            (date(2026, 1, 5), authority["bridge_id"]),
        )
        self.cursor.execute(
            "INSERT INTO ingredient_substance_mapping_closures("
            "ingredient_substance_id,valid_to,closed_by,closed_at,reason_code,created_at) "
            "VALUES(%s,%s,'reviewer:test',%s,'closed',%s)",
            (authority["bridge_id"], date(2026, 1, 5), closure_time, closure_time),
        )
        before = self.service.build_evaluation_input(
            self.cursor, _request("ingredient", ingredient_id, BASE + timedelta(days=1))
        )
        self.assertEqual(before.mapping_state.resolution_state, "resolved")
        on_end = self.service.build_evaluation_input(
            self.cursor, _request("ingredient", ingredient_id, closure_time)
        )
        self.assertEqual(on_end.mapping_state.resolution_state, "empty")
        self.assertIn("out_of_effective_range", {o.reason_code for o in on_end.mapping_state.observations})

    def test_inclusive_validity_boundaries_with_visible_closure(self):
        ingredient_id, substance_id = self._targets()
        authority = self._authority(ingredient_id, substance_id, offset=-1440)
        closure_time = datetime(2026, 1, 4, 12, 0, tzinfo=UTC)
        self.cursor.execute(
            "UPDATE ingredient_substances SET valid_to='2026-01-05' WHERE id=%s",
            (authority["bridge_id"],),
        )
        self.cursor.execute(
            "INSERT INTO ingredient_substance_mapping_closures("
            "ingredient_substance_id,valid_to,closed_by,closed_at,reason_code,created_at) "
            "VALUES(%s,'2026-01-05','reviewer:test',%s,'closed',%s)",
            (authority["bridge_id"], closure_time, closure_time),
        )
        first_day = self.service.build_evaluation_input(
            self.cursor,
            _request("ingredient", ingredient_id, datetime(2026, 1, 1, 23, 59, tzinfo=UTC)),
        )
        last_day = self.service.build_evaluation_input(
            self.cursor,
            _request("ingredient", ingredient_id, datetime(2026, 1, 5, 23, 59, tzinfo=UTC)),
        )
        after = self.service.build_evaluation_input(
            self.cursor,
            _request("ingredient", ingredient_id, datetime(2026, 1, 6, tzinfo=UTC)),
        )
        self.assertEqual(first_day.mapping_state.resolution_state, "resolved")
        self.assertEqual(last_day.mapping_state.resolution_state, "resolved")
        self.assertEqual(after.mapping_state.resolution_state, "empty")

    def test_bridge_observation_reason_matrix(self):
        ingredient_id, substance_id = self._targets()
        pending_substance = substance_id
        ambiguous_substance = self._targets()[1]
        rejected_substance = self._targets()[1]
        legacy_substance = self._targets()[1]
        uncontrolled_substance = self._targets()[1]
        incomplete_substance = self._targets()[1]
        closure_bad_substance = self._targets()[1]
        self._bridge(
            ingredient_id, pending_substance, status="pending_review", valid_from=None
        )
        self._bridge(
            ingredient_id, ambiguous_substance, status="ambiguous", valid_from=None
        )
        self._bridge(
            ingredient_id, rejected_substance, status="rejected", valid_from=None
        )
        self._bridge(
            ingredient_id,
            legacy_substance,
            status="legacy_unreviewed",
            method="legacy",
            valid_from=None,
        )
        self._bridge(ingredient_id, uncontrolled_substance, status="accepted", method="legacy")
        self._bridge(ingredient_id, incomplete_substance, status="accepted", method="legacy", valid_from=None)
        self._bridge(
            ingredient_id,
            closure_bad_substance,
            status="accepted",
            method="legacy",
            valid_to=date(2026, 12, 31),
        )
        result = self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        reasons = {observation.reason_code for observation in result.mapping_state.observations}
        self.assertTrue(
            {
                "pending_review_bridge",
                "ambiguous_bridge",
                "rejected_bridge",
                "legacy_unreviewed_bridge",
                "uncontrolled_accepted_bridge",
                "history_incomplete",
                "closure_history_inconsistent",
            }.issubset(reasons)
        )
        self.assertEqual(result.mapping_state.resolution_state, "history_unavailable")

    def test_all_relationship_types_remain_distinct_and_canonically_ordered(self):
        ingredient_id, first_substance = self._targets()
        relationships = [
            "represents",
            "contains",
            "derived_from",
            "mixture_component",
            "equivalent_to",
        ]
        substance_ids = [first_substance, *[self._targets()[1] for _ in range(4)]]
        for offset, (relationship, substance_id) in enumerate(zip(relationships, substance_ids)):
            self._authority(
                ingredient_id,
                substance_id,
                relationship=relationship,
                offset=offset,
            )
        result = self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        observed = [member.descriptor.relationship_type for member in result.mapping_state.members]
        self.assertEqual(observed, sorted(relationships, key=lambda value: value.encode("utf-8")))
        self.assertEqual(len(observed), 5)

    def test_retry_reuses_all_canonical_roots_and_history_is_immutable(self):
        ingredient_id, substance_id = self._targets()
        first_authority = self._authority(ingredient_id, substance_id)
        request = _request("ingredient", ingredient_id)
        first = self.service.build_evaluation_input(self.cursor, request)
        retry = self.service.build_evaluation_input(self.cursor, request)
        self.assertEqual(first.input_artifact.artifact.id, retry.input_artifact.artifact.id)
        self.assertEqual(first.mapping_state.manifest_artifact.artifact.id, retry.mapping_state.manifest_artifact.artifact.id)
        original_identity = first.mapping_state.members[0].member_identity_digest
        original_member_digest = first.mapping_state.members[0].artifact.artifact.content_digest
        self._authority(
            ingredient_id,
            substance_id,
            bridge_id=first_authority["bridge_id"],
            outcome="already_current",
            offset=20,
        )
        later = self.service.build_evaluation_input(self.cursor, request)
        self.assertEqual(original_identity, later.mapping_state.members[0].member_identity_digest)
        self.assertNotEqual(original_member_digest, later.mapping_state.members[0].artifact.artifact.content_digest)
        self.assertNotEqual(first.mapping_state.mapping_snapshot_digest, later.mapping_state.mapping_snapshot_digest)

    def test_transaction_rollback_removes_artifacts(self):
        ingredient_id, substance_id = self._targets()
        self._authority(ingredient_id, substance_id)
        self.connection.commit()
        result = self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        artifact_id = result.input_artifact.artifact.id
        self.connection.rollback()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM scientific_evaluation_artifacts WHERE id=%s", (artifact_id,))
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_concurrent_identical_inputs_converge(self):
        ingredient_id, substance_id = self._targets()
        self._authority(ingredient_id, substance_id)
        self.connection.commit()
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def worker():
            connection = _connection(self.database)
            try:
                with connection.cursor() as cursor:
                    barrier.wait()
                    value = ScientificMappingStateService().build_evaluation_input(
                        cursor, _request("ingredient", ingredient_id)
                    )
                    results.append(
                        (
                            value.target.artifact.artifact.id,
                            value.mapping_state.members[0].artifact.artifact.id,
                            value.mapping_state.manifest_artifact.artifact.id,
                            value.input_artifact.artifact.id,
                        )
                    )
                connection.commit()
            except Exception as exc:  # pragma: no cover - asserted below
                connection.rollback()
                errors.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertFalse(errors, errors)
        self.assertEqual(len(set(results)), 1)

    def _zero_snapshot(self, *, seal):
        request = SnapshotConstructionRequest(
            snapshot_policy_key="mapping_input_prerequisite",
            snapshot_policy_version="1",
            as_of=AS_OF,
            evidence_cutoff=AS_OF - timedelta(days=1),
            scope={"target": "prerequisite"},
            technical_predicates=(),
            members=(),
            created_by="mapping_input_test",
            sealed_by="mapping_input_test",
        )
        service = ScientificEvidenceSnapshotService()
        if seal:
            return service.build_and_seal(self.cursor, request).snapshot
        return service.create_building(self.cursor, request)

    def _protocol(self, lifecycle="draft"):
        writer = ScientificArtifactWriter()
        definition = writer.write_verified_inline(
            self.cursor,
            ScientificArtifactWriteRequest("protocol_definition", "1", {"fixture": str(uuid.uuid4())}),
        )
        review = writer.write_verified_inline(
            self.cursor,
            ScientificArtifactWriteRequest("protocol_review", "1", {"fixture": str(uuid.uuid4())}),
        )
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_protocols("
            "protocol_key,domain_key,target_entity_type,governance_owner,created_by) "
            "VALUES(%s,'food_toxicology','ingredient','governance:test','creator:test') RETURNING id",
            (f"mapping_input_{uuid.uuid4().hex}",),
        )
        protocol_id = self.cursor.fetchone()[0]
        published_at = BASE if lifecycle in {"published", "deprecated", "retired"} else None
        retired_at = BASE if lifecycle == "retired" else None
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_protocol_versions("
            "protocol_id,semantic_version,lifecycle_status,canonical_artifact_id,"
            "protocol_digest,review_artifact_id,created_by,published_at,retired_at) "
            "VALUES(%s,'1.0.0',%s,%s,%s,%s,'creator:test',%s,%s) RETURNING id",
            (
                protocol_id,
                lifecycle,
                definition.artifact.id if lifecycle != "draft" else None,
                definition.artifact.content_digest if lifecycle != "draft" else None,
                review.artifact.id if lifecycle != "draft" else None,
                published_at,
                retired_at,
            ),
        )
        version_id = self.cursor.fetchone()[0]
        if lifecycle != "draft":
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_governance_events("
                "event_key,entity_type,protocol_version_id,event_type,actor_identifier,"
                "reason_code,effective_at) VALUES(%s,'protocol_version',%s,%s,"
                "'governance:test','fixture',%s)",
                (
                    str(uuid.uuid4()),
                    version_id,
                    lifecycle if lifecycle in {"published", "deprecated", "retired"} else "approved",
                    BASE,
                ),
            )
        return version_id

    def test_snapshot_and_protocol_prerequisite_validation(self):
        building = self._zero_snapshot(seal=False)
        draft = self._protocol("draft")
        with self.assertRaises(UnsealedEvidenceSnapshotError):
            self.service.validate_execution_prerequisites(
                self.cursor, snapshot_id=building.id, protocol_version_id=draft, execution_type="NORMAL"
            )
        sealed = self._zero_snapshot(seal=True)
        with self.assertRaises(InvalidProtocolLifecycleError):
            self.service.validate_execution_prerequisites(
                self.cursor, snapshot_id=sealed.id, protocol_version_id=draft, execution_type="NORMAL"
            )
        published = self._protocol("published")
        self.service.validate_execution_prerequisites(
            self.cursor, snapshot_id=sealed.id, protocol_version_id=published, execution_type="NORMAL"
        )
        self.service.validate_execution_prerequisites(
            self.cursor, snapshot_id=sealed.id, protocol_version_id=published, execution_type="REFRESH"
        )
        deprecated = self._protocol("deprecated")
        retired = self._protocol("retired")
        for historical in (deprecated, retired):
            self.service.validate_execution_prerequisites(
                self.cursor,
                snapshot_id=sealed.id,
                protocol_version_id=historical,
                execution_type="REPLAY",
            )
        with self.assertRaises(InvalidProtocolLifecycleError):
            self.service.validate_execution_prerequisites(
                self.cursor,
                snapshot_id=sealed.id,
                protocol_version_id=deprecated,
                execution_type="NORMAL",
            )
        with self.assertRaises(CounterfactualAuthorizationUnavailableError):
            self.service.validate_execution_prerequisites(
                self.cursor,
                snapshot_id=sealed.id,
                protocol_version_id=published,
                execution_type="COUNTERFACTUAL",
            )

    def test_legacy_scoring_isolation(self):
        ingredient_id, substance_id = self._targets()
        self._authority(ingredient_id, substance_id)
        self.cursor.execute(
            "SELECT (SELECT count(*) FROM product_scores),"
            "(SELECT count(*) FROM ingredient_risk_profiles),"
            "(SELECT count(*) FROM ingredient_evidence)"
        )
        before = self.cursor.fetchone()
        self.service.build_evaluation_input(self.cursor, _request("ingredient", ingredient_id))
        self.cursor.execute(
            "SELECT (SELECT count(*) FROM product_scores),"
            "(SELECT count(*) FROM ingredient_risk_profiles),"
            "(SELECT count(*) FROM ingredient_evidence)"
        )
        self.assertEqual(self.cursor.fetchone(), before)


if __name__ == "__main__":
    unittest.main()
