"""Phase 6.4.4 persistent batch recovery and provider-neutral orchestration."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event
import unittest
import uuid

import psycopg2.extras

from app.db import get_connection
from app.scientific_ingestion.adapters.common import (
    LocalFixtureArtifact,
    LocalFixtureArtifactReader,
)
from app.scientific_ingestion.adapters.efsa import EfsaAdapter, EfsaArtifactParser
from app.scientific_ingestion.adapters.openfoodtox import (
    OpenFoodToxAdapter,
    OpenFoodToxArtifactParser,
)
from app.scientific_ingestion.contracts import (
    ScientificArtifactManifest,
    ScientificArtifactReference,
    ScientificIngestionConfiguration,
)
from app.scientific_ingestion.errors import (
    ScientificAcquisitionError,
    ScientificParserError,
    ScientificPersistenceConflict,
)
from app.services.scientific_batch import (
    ScientificBatchArtifactResult,
    ScientificBatchExecutionOutcome,
    ScientificBatchFailure,
    ScientificBatchIngestionService,
    ScientificBatchPlan,
    ScientificBatchWorkIdentity,
    ScientificBatchWorkItem,
)
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import ScientificIngestionService
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver
from app.services.substance_resolution_reviews import SubstanceResolutionReviewService
from app.repositories.scientific_persistence import PostgresScientificPersistenceRepository


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL")
class ScientificBatchSchemaGapTests(unittest.TestCase):
    def test_persistent_batch_checkpoint_schema_exists(self):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT to_regclass('public.scientific_batch_plans'),
                           to_regclass('public.scientific_batch_work_items'),
                           to_regclass('public.scientific_batch_work_attempts')
                """)
                self.assertEqual(
                    cursor.fetchone(),
                    (
                        "scientific_batch_plans",
                        "scientific_batch_work_items",
                        "scientific_batch_work_attempts",
                    ),
                )
        finally:
            connection.close()


class ScientificBatchContractTests(unittest.TestCase):
    @staticmethod
    def identity(release="release-a", parser="parser-1"):
        return ScientificBatchWorkIdentity(
            source_key="efsa", dataset_key="efsa_qps",
            external_release_key=release, artifact_keys=("primary",),
            source_adapter_version="adapter-1",
            acquisition_version="acquisition-1", parser_version=parser,
            normalization_schema_version="schema-1",
            config_fingerprint=sha256(b"config").hexdigest(),
        )

    @staticmethod
    def item(identity):
        return ScientificBatchWorkItem(
            identity,
            lambda: ScientificBatchArtifactResult(sha256(b"artifact").hexdigest(), True),
            lambda artifact, key: ScientificBatchExecutionOutcome(1, 1, 1, 1),
        )

    def test_semantic_identity_includes_release_artifact_parser_and_config(self):
        base = self.identity()
        self.assertEqual(base.work_key, self.identity().work_key)
        self.assertNotEqual(base.work_key, self.identity(release="release-b").work_key)
        self.assertNotEqual(base.work_key, self.identity(parser="parser-2").work_key)
        multi_a = ScientificBatchWorkIdentity(
            **{**base.as_dict(), "artifact_keys": ("primary", "metadata")}
        )
        multi_b = ScientificBatchWorkIdentity(
            **{**base.as_dict(), "artifact_keys": ("metadata", "primary")}
        )
        self.assertEqual(multi_a.work_key, multi_b.work_key)

    def test_plan_identity_is_order_independent_and_rejects_duplicates(self):
        first = self.item(self.identity("release-a"))
        second = self.item(self.identity("release-b"))
        self.assertEqual(
            ScientificBatchPlan((first, second)).plan_key,
            ScientificBatchPlan((second, first)).plan_key,
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            ScientificBatchPlan((first, first))


class FailingFindingRepository(PostgresScientificPersistenceRepository):
    def _persist_finding(self, cursor, assessment_id, finding):
        raise RuntimeError("phase644 injected finding persistence failure")


class MutableClock:
    def __init__(self):
        self.value = datetime(2026, 8, 29, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0018")
class ScientificBatchRecoveryPostgresTests(unittest.TestCase):
    FIXTURES = Path(__file__).resolve().parent / "fixtures" / "scientific_sources"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def _pipeline(self, provider, release_key, *, parser_version=None,
                  acquire_failures=None, ingest_failures=None,
                  failing_finding_once=False):
        source = self.FIXTURES / (
            "efsa_minimal.json" if provider == "efsa" else "openfoodtox_minimal.json"
        )
        document = json.loads(source.read_text(encoding="utf-8"))
        if provider == "efsa":
            document["release"]["official_release"] = release_key
            adapter_class, parser_class = EfsaAdapter, EfsaArtifactParser
        else:
            document["catalog"]["snapshot_date"] = release_key
            adapter_class, parser_class = OpenFoodToxAdapter, OpenFoodToxArtifactParser
        fixture = self.temp_path / f"{provider}_{release_key}_{uuid.uuid4().hex}.json"
        fixture.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
        options = {"parser_version": parser_version} if parser_version else {}
        adapter = adapter_class(fixture, **options)
        release = adapter.discover_release()
        payload = fixture.read_bytes()
        checksum = sha256(payload).hexdigest()
        artifact_key = "primary"
        locator = f"fixture://phase644/{provider}/{release_key}/{checksum}"
        connection = get_connection()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO sources(source_key,source_name,source_type,url)
                    VALUES(%s,%s,'scientific',%s)
                    ON CONFLICT(source_key) DO UPDATE SET source_name=EXCLUDED.source_name
                    RETURNING id
                """, (provider, provider.upper(), f"https://fixture.invalid/{provider}"))
                source_id = cursor.fetchone()["id"]
                cursor.execute("""
                    INSERT INTO source_datasets(source_id,dataset_name,dataset_key,description)
                    VALUES(%s,%s,%s,'Phase 6.4.4 bounded fixture')
                    ON CONFLICT(source_id,dataset_key) DO UPDATE SET dataset_name=EXCLUDED.dataset_name
                    RETURNING id
                """, (source_id, adapter.metadata.dataset_key, adapter.metadata.dataset_key))
                dataset_id = cursor.fetchone()["id"]
                cursor.execute("""
                    INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label)
                    VALUES(%s,%s,%s)
                    ON CONFLICT(dataset_id,external_release_key) DO UPDATE
                      SET version_label=EXCLUDED.version_label RETURNING id
                """, (dataset_id, release_key, release_key))
                release_id = cursor.fetchone()["id"]
                cursor.execute("""
                    INSERT INTO storage_objects(storage_provider,bucket,object_key,
                      checksum_algorithm,checksum_value,mime_type,byte_size)
                    VALUES('fixture','phase644',%s,'sha256',%s,'application/json',%s)
                    ON CONFLICT DO NOTHING RETURNING id
                """, (locator, checksum, len(payload)))
                row = cursor.fetchone()
                if row is None:
                    cursor.execute("""
                        SELECT id FROM storage_objects WHERE storage_provider='fixture'
                          AND bucket='phase644' AND object_key=%s
                          AND COALESCE(object_version,'')=''
                    """, (locator,))
                    row = cursor.fetchone()
                storage_id = row["id"]
                cursor.execute("""
                    INSERT INTO scientific_release_artifacts(
                      release_id,storage_object_id,artifact_key,artifact_role,format,
                      media_type,raw_checksum_algorithm,raw_checksum_value,byte_size,
                      acquired_at,provenance)
                    VALUES(%s,%s,%s,'primary','json','application/json','sha256',%s,%s,NOW(),%s)
                    ON CONFLICT(release_id,artifact_key) DO NOTHING
                """, (
                    release_id, storage_id, artifact_key, checksum, len(payload),
                    psycopg2.extras.Json({"phase": "6.4.4", "locator": locator}),
                ))
                self._known_cas(cursor)
            connection.commit()
        finally:
            connection.close()
        reference = ScientificArtifactReference(
            artifact_key=artifact_key, artifact_role="primary",
            storage_object_id=storage_id, raw_checksum_algorithm="sha256",
            raw_checksum_value=checksum, byte_size=len(payload),
            source_locator=locator, content_type="application/json",
            acquisition_metadata={"phase": "6.4.4"},
        )
        manifest = ScientificArtifactManifest.build(release, (reference,))
        local = LocalFixtureArtifact(
            fixture, artifact_key, "primary", storage_id, "application/json", provider,
        )
        parser = parser_class(adapter, LocalFixtureArtifactReader(local))
        configuration = ScientificIngestionConfiguration(
            adapter=adapter.metadata,
            semantic_configuration={"provider": provider, "phase": "6.4.4"},
        )
        identity = ScientificBatchWorkIdentity(
            source_key=release.source_key, dataset_key=release.dataset_key,
            external_release_key=release.external_release_key,
            artifact_keys=(artifact_key,),
            source_adapter_version=adapter.metadata.adapter_version,
            acquisition_version=adapter.metadata.acquisition_version,
            parser_version=adapter.metadata.parser_version,
            normalization_schema_version=adapter.metadata.normalization_schema_version,
            config_fingerprint=configuration.fingerprint,
        )
        acquisition_errors = list(acquire_failures or ())
        ingestion_errors = list(ingest_failures or ())
        state = {"acquisitions": 0, "ingestions": 0, "finding_failed": False}

        def acquire():
            state["acquisitions"] += 1
            if acquisition_errors:
                raise acquisition_errors.pop(0)
            return ScientificBatchArtifactResult(
                manifest.fingerprint, state["acquisitions"] == 1, manifest,
            )

        def ingest(artifact, idempotency_key):
            state["ingestions"] += 1
            if ingestion_errors:
                error = ingestion_errors.pop(0)
                raise error
            ingestion = ScientificIngestionService()
            prepared = ingestion.prepare_ingestion_run(
                release, configuration, (artifact_key,), idempotency_key,
            )
            repository = None
            if failing_finding_once and not state["finding_failed"]:
                state["finding_failed"] = True
                repository = FailingFindingRepository()
            executor = ScientificIngestionExecutor(
                parser, PostgresScientificSubstanceResolver(), ingestion,
                repository=repository,
                resolution_review_service=SubstanceResolutionReviewService(),
            )
            try:
                result = executor.execute(prepared)
            except Exception as exc:
                raise ScientificBatchFailure(
                    "persistence_failure", str(exc), True, prepared.id
                ) from exc
            reused = result.reused_terminal_run
            return ScientificBatchExecutionOutcome(
                result.run_id, result.records_seen,
                0 if reused else result.assessments_written,
                0 if reused else result.findings_written,
                result.assessments_written if reused else 0,
                result.findings_written if reused else 0,
            )

        return ScientificBatchWorkItem(identity, acquire, ingest, max_attempts=2), state

    @staticmethod
    def _known_cas(cursor):
        cursor.execute("""
            INSERT INTO substance_identifier_namespaces(
              namespace_key,namespace_version,display_name,
              normalization_rule_version,provenance)
            VALUES('cas','1','CAS Registry Number','cas_identity_v1',%s)
            ON CONFLICT(namespace_key,namespace_version) DO NOTHING
        """, (psycopg2.extras.Json({"phase": "6.4.4"}),))
        cursor.execute("""
            SELECT id FROM substance_identifier_namespaces
            WHERE namespace_key='cas' AND namespace_version='1'
        """)
        namespace_id = cursor.fetchone()["id"]
        cursor.execute(
            "SELECT id FROM substances WHERE normalized_name='phase641_formaldehyde'"
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute("""
                INSERT INTO substances(
                  preferred_name,normalized_name,substance_type,status)
                VALUES('Formaldehyde fixture','phase641_formaldehyde',
                       'chemical_substance','active') RETURNING id
            """)
            row = cursor.fetchone()
        substance_id = row["id"]
        cursor.execute("""
            INSERT INTO substance_identifiers(
              substance_id,namespace_id,identifier_system,identifier_value,
              normalized_value,is_primary,verification_status,provenance)
            VALUES(%s,%s,'CASRN','50-00-0','50-00-0',TRUE,'verified',%s)
            ON CONFLICT(namespace_id,normalized_value) DO NOTHING
        """, (
            substance_id, namespace_id,
            psycopg2.extras.Json({"phase": "6.4.4", "fixture": True}),
        ))

    def test_full_bounded_multi_provider_resume_and_summary(self):
        efsa_a, _ = self._pipeline("efsa", "phase644-efsa-a")
        oft_failure, _ = self._pipeline(
            "openfoodtox", "phase644-oft-failed",
            acquire_failures=(ScientificParserError("malformed permanent provider payload"),),
        )
        efsa_retry, _ = self._pipeline(
            "efsa", "phase644-efsa-b",
            acquire_failures=(ScientificAcquisitionError("temporary provider outage"),),
        )
        oft_success, _ = self._pipeline("openfoodtox", "phase644-oft-c")
        plan = ScientificBatchPlan((efsa_a, oft_failure, efsa_retry, oft_success))
        service = ScientificBatchIngestionService()
        first = service.execute(plan)
        self.assertEqual([item.state for item in first.results],
                         ["completed", "failed", "retryable", "completed"])
        second = ScientificBatchIngestionService().execute(plan)
        self.assertEqual([item.state for item in second.results],
                         ["already_completed", "failed", "completed", "already_completed"])
        self.assertEqual(second.counters["items_reused"], 2)
        self.assertEqual(second.counters["items_completed"], 1)
        history = service.history(plan.plan_key)
        self.assertTrue(any(row["attempt_status"] == "retryable" for row in history))
        self.assertTrue(any(row["attempt_status"] == "completed" for row in history))
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT source.source_key,count(*)
                    FROM scientific_assessments assessment
                    JOIN scientific_ingestion_runs run ON run.id=assessment.ingestion_run_id
                    JOIN source_dataset_releases release ON release.id=run.release_id
                    JOIN source_datasets dataset ON dataset.id=release.dataset_id
                    JOIN sources source ON source.id=dataset.source_id
                    WHERE run.id=ANY(%s) GROUP BY source.source_key
                """, ([item.ingestion_run_id for item in second.results
                         if item.ingestion_run_id],))
                self.assertEqual(
                    dict(cursor.fetchall()), {"efsa": 2, "openfoodtox": 1}
                )
                cursor.execute("""
                    SELECT source.source_key,count(*)
                    FROM scientific_assessments assessment
                    JOIN scientific_ingestion_runs run ON run.id=assessment.ingestion_run_id
                    JOIN source_dataset_releases release ON release.id=run.release_id
                    JOIN source_datasets dataset ON dataset.id=release.dataset_id
                    JOIN sources source ON source.id=dataset.source_id
                    WHERE run.id IN (
                      SELECT ingestion_run_id FROM scientific_batch_work_items
                      WHERE batch_plan_id=(SELECT id FROM scientific_batch_plans WHERE plan_key=%s)
                        AND ingestion_run_id IS NOT NULL)
                    GROUP BY source.source_key
                """, (plan.plan_key,))
                self.assertEqual(dict(cursor.fetchall()), {"efsa": 2, "openfoodtox": 1})
        finally:
            connection.close()

    def test_restart_reclaims_stale_lease_after_artifact_checkpoint(self):
        item, state = self._pipeline("efsa", "phase644-crash-after-artifact")
        original_ingest = item.ingest

        def crash_once(artifact, key):
            if state.get("crashed") is None:
                state["crashed"] = True
                raise SystemExit("simulated process termination")
            return original_ingest(artifact, key)

        item = ScientificBatchWorkItem(item.identity, item.acquire, crash_once, 2)
        plan = ScientificBatchPlan((item,))
        clock = MutableClock()
        service = ScientificBatchIngestionService(clock=clock, lease_seconds=1)
        with self.assertRaises(SystemExit):
            service.execute(plan)
        clock.advance(2)
        resumed = ScientificBatchIngestionService(clock=clock, lease_seconds=1).execute(plan)
        self.assertEqual(resumed.results[0].state, "completed")
        self.assertEqual(resumed.results[0].attempt, 2)
        self.assertTrue(resumed.results[0].artifact_reused)
        history = service.history(plan.plan_key)
        self.assertEqual([row["attempt_status"] for row in history],
                         ["abandoned", "completed"])

    def test_crash_before_artifact_and_completed_retry_are_safe(self):
        item, state = self._pipeline("openfoodtox", "phase644-crash-before-artifact")
        original_acquire = item.acquire

        def crash_once():
            if state.get("crashed_before") is None:
                state["crashed_before"] = True
                raise SystemExit("crash before artifact persistence")
            return original_acquire()

        item = ScientificBatchWorkItem(item.identity, crash_once, item.ingest, 2)
        plan = ScientificBatchPlan((item,))
        clock = MutableClock()
        service = ScientificBatchIngestionService(clock=clock, lease_seconds=1)
        with self.assertRaises(SystemExit):
            service.execute(plan)
        clock.advance(2)
        self.assertEqual(service.execute(plan).results[0].state, "completed")
        self.assertEqual(service.execute(plan).results[0].state, "already_completed")

    def test_finding_failure_rolls_back_then_logical_retry_succeeds(self):
        item, _ = self._pipeline(
            "openfoodtox", "phase644-finding-rollback", failing_finding_once=True,
        )
        plan = ScientificBatchPlan((item,))
        service = ScientificBatchIngestionService()
        first = service.execute(plan)
        self.assertEqual(first.results[0].state, "retryable")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*) FROM scientific_assessments
                    WHERE ingestion_run_id=(
                      SELECT ingestion_run_id FROM scientific_batch_work_attempts
                      WHERE work_item_id=(SELECT id FROM scientific_batch_work_items
                        WHERE work_key=%s) AND attempt_number=1)
                """, (item.identity.work_key,))
                self.assertEqual(cursor.fetchone()[0], 0)
        finally:
            connection.close()
        second = service.execute(plan)
        self.assertEqual(second.results[0].state, "completed")

    def test_concurrent_workers_use_one_claim_and_converge(self):
        item, _ = self._pipeline("efsa", "phase644-worker-race")
        started, release = Event(), Event()
        original_acquire = item.acquire

        def slow_acquire():
            started.set()
            release.wait(5)
            return original_acquire()

        item = ScientificBatchWorkItem(item.identity, slow_acquire, item.ingest, 2)
        plan = ScientificBatchPlan((item,))
        first_service = ScientificBatchIngestionService()
        second_service = ScientificBatchIngestionService()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first_future = pool.submit(first_service.execute, plan)
            self.assertTrue(started.wait(5))
            overlapping = pool.submit(second_service.execute, plan).result(timeout=5)
            self.assertEqual(overlapping.results[0].state, "retryable")
            self.assertEqual(overlapping.results[0].error_class, "work_item_claimed")
            release.set()
            self.assertEqual(first_future.result(timeout=10).results[0].state, "completed")
        self.assertEqual(second_service.execute(plan).results[0].state, "already_completed")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*),max(attempt_count) FROM scientific_batch_work_items
                    WHERE batch_plan_id=(SELECT id FROM scientific_batch_plans WHERE plan_key=%s)
                """, (plan.plan_key,))
                self.assertEqual(cursor.fetchone(), (1, 1))
        finally:
            connection.close()

    def test_changed_upstream_conflict_isolated_from_other_item(self):
        valid, _ = self._pipeline("efsa", "phase644-conflict-valid")
        conflict, _ = self._pipeline(
            "openfoodtox", "phase644-conflict",
            acquire_failures=(ScientificPersistenceConflict("changed upstream bytes"),),
        )
        summary = ScientificBatchIngestionService().execute(
            ScientificBatchPlan((valid, conflict))
        )
        self.assertEqual([item.state for item in summary.results],
                         ["completed", "conflict"])
        self.assertEqual(summary.counters["items_conflicted"], 1)

    def test_reclaimed_work_rejects_changed_manifest_without_overwrite(self):
        item, state = self._pipeline("efsa", "phase644-checkpoint-conflict")
        original_ingest = item.ingest

        def crash_after_checkpoint(artifact, key):
            if state.get("checkpoint_crash") is None:
                state["checkpoint_crash"] = True
                raise SystemExit("crash after immutable artifact checkpoint")
            return original_ingest(artifact, key)

        first_fingerprint = sha256(b"first-manifest").hexdigest()
        second_fingerprint = sha256(b"changed-manifest").hexdigest()
        fingerprints = [first_fingerprint, second_fingerprint]

        def changed_acquire():
            return ScientificBatchArtifactResult(fingerprints.pop(0), True)

        item = ScientificBatchWorkItem(
            item.identity, changed_acquire, crash_after_checkpoint, 2,
        )
        plan = ScientificBatchPlan((item,))
        clock = MutableClock()
        service = ScientificBatchIngestionService(clock=clock, lease_seconds=1)
        with self.assertRaises(SystemExit):
            service.execute(plan)
        clock.advance(2)
        result = service.execute(plan).results[0]
        self.assertEqual(result.state, "conflict")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT artifact_manifest_fingerprint
                    FROM scientific_batch_work_items WHERE work_key=%s
                """, (item.identity.work_key,))
                self.assertEqual(cursor.fetchone()[0], first_fingerprint)
        finally:
            connection.close()

    def test_same_artifact_reprocesses_only_when_parser_identity_changes(self):
        shared, _ = self._pipeline("efsa", "phase644-shared")
        extra, _ = self._pipeline("openfoodtox", "phase644-extra")
        first_plan = ScientificBatchPlan((shared,))
        second_plan = ScientificBatchPlan((shared, extra))
        service = ScientificBatchIngestionService()
        first = service.execute(first_plan).results[0]
        second = service.execute(second_plan).results[0]
        self.assertEqual(first.ingestion_run_id, second.ingestion_run_id)
        self.assertGreater(second.assessments_reused, 0)
        changed, _ = self._pipeline(
            "efsa", "phase644-shared", parser_version="efsa-parser-2",
        )
        changed_result = service.execute(ScientificBatchPlan((changed,))).results[0]
        self.assertNotEqual(first.ingestion_run_id, changed_result.ingestion_run_id)

    def test_larger_bounded_workload_has_unique_deterministic_checkpoint(self):
        anchor, _ = self._pipeline("efsa", "phase644-workload-anchor")
        anchor_result = ScientificBatchIngestionService().execute(
            ScientificBatchPlan((anchor,))
        ).results[0]
        items = []
        for index in range(40):
            identity = ScientificBatchWorkIdentity(
                source_key="efsa" if index % 2 == 0 else "openfoodtox",
                dataset_key="bounded_batch", external_release_key=f"release-{index:03d}",
                artifact_keys=("primary",), source_adapter_version="adapter-1",
                acquisition_version="fixture-1", parser_version="parser-1",
                normalization_schema_version="schema-1",
                config_fingerprint=sha256(f"config-{index}".encode()).hexdigest(),
            )
            items.append(ScientificBatchWorkItem(
                identity,
                lambda index=index: ScientificBatchArtifactResult(
                    sha256(f"artifact-{index}".encode()).hexdigest(), True,
                ),
                lambda artifact, key, run=anchor_result.ingestion_run_id:
                    ScientificBatchExecutionOutcome(run, 1, 0, 0),
            ))
        plan = ScientificBatchPlan(tuple(items))
        service = ScientificBatchIngestionService()
        first = service.execute(plan)
        second = service.execute(ScientificBatchPlan(tuple(reversed(items))))
        self.assertEqual(first.plan_key, second.plan_key)
        self.assertEqual(first.counters["items_completed"], 40)
        self.assertEqual(second.counters["items_reused"], 40)
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*),count(DISTINCT work_key)
                    FROM scientific_batch_work_items
                    WHERE batch_plan_id=(SELECT id FROM scientific_batch_plans WHERE plan_key=%s)
                """, (plan.plan_key,))
                self.assertEqual(cursor.fetchone(), (40, 40))
        finally:
            connection.close()

    def test_failure_taxonomy_and_bounded_retry_exhaustion(self):
        cases = (
            ("acquire", ScientificAcquisitionError("503 exhausted"),
             "retryable", "acquisition_failure"),
            ("acquire", ScientificBatchFailure(
                "artifact_registration_failure", "storage unavailable", True
            ), "retryable", "artifact_registration_failure"),
            ("ingest", ScientificBatchFailure(
                "integrity_failure", "checksum", False
            ), "failed", "integrity_failure"),
            ("ingest", ScientificParserError("parser"),
             "failed", "parser_failure"),
            ("ingest", ScientificBatchFailure(
                "identity_failure", "identifier rejected", False
            ), "failed", "identity_failure"),
            ("ingest", ScientificBatchFailure(
                "persistence_failure", "assessment write failed", True
            ), "retryable", "persistence_failure"),
            ("acquire", ScientificPersistenceConflict("conflict"),
             "conflict", "conflict"),
        )
        for index, (stage, error, expected, category) in enumerate(cases):
            identity = ScientificBatchContractTests.identity(f"taxonomy-{index}")
            acquire = (
                (lambda error=error: (_ for _ in ()).throw(error))
                if stage == "acquire"
                else (lambda: ScientificBatchArtifactResult(
                    sha256(b"taxonomy-artifact").hexdigest(), True
                ))
            )
            ingest = (
                (lambda artifact, key, error=error: (_ for _ in ()).throw(error))
                if stage == "ingest"
                else (lambda artifact, key: ScientificBatchExecutionOutcome(1, 0, 0, 0))
            )
            item = ScientificBatchWorkItem(
                identity, acquire, ingest, max_attempts=2,
            )
            service = ScientificBatchIngestionService()
            first = service.execute(ScientificBatchPlan((item,))).results[0]
            self.assertEqual(first.state, expected)
            self.assertEqual(first.error_class, category)
            if expected == "retryable":
                second = service.execute(ScientificBatchPlan((item,))).results[0]
                self.assertEqual(second.state, "retryable")
                third = service.execute(ScientificBatchPlan((item,))).results[0]
                self.assertEqual(third.state, "failed")
                self.assertEqual(third.error_class, "retry_exhausted")


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated lifecycle PostgreSQL",
)
class ScientificBatchRecoveryLifecycleTests(unittest.TestCase):
    backend = Path(__file__).resolve().parents[1]

    def alembic(self, *args, success=True):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args], cwd=self.backend,
            text=True, capture_output=True,
        )
        if success and result.returncode != 0:
            self.fail(result.stdout + result.stderr)
        if not success and result.returncode == 0:
            self.fail("Alembic command unexpectedly succeeded")
        return result

    def test_0017_0018_0017_0018_and_nonrepresentable_preflight(self):
        self.alembic("downgrade", "0017_ingredient_mapping_history")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regclass('scientific_batch_plans')")
                self.assertIsNone(cursor.fetchone()[0])
        finally:
            connection.close()
        self.alembic("upgrade", "0018_scientific_batch_recovery")
        self.alembic("downgrade", "0017_ingredient_mapping_history")
        self.alembic("upgrade", "0018_scientific_batch_recovery")
        identity = ScientificBatchContractTests.identity("lifecycle-release")
        item = ScientificBatchContractTests.item(identity)
        ScientificBatchIngestionService()._ensure_plan(ScientificBatchPlan((item,)))
        failure = self.alembic(
            "downgrade", "0017_ingredient_mapping_history", success=False,
        )
        self.assertIn("not representable", failure.stdout + failure.stderr)
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version_num FROM alembic_version")
                self.assertEqual(cursor.fetchone()[0], "0018_scientific_batch_recovery")
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
