import os
import socket
import unittest
import uuid
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import psycopg2.extras

from app.db import get_connection
from app.repositories.scientific_persistence import PostgresScientificPersistenceRepository
from app.scientific_ingestion.adapters import (
    EfsaAdapter,
    EfsaArtifactParser,
    LocalFixtureArtifact,
    LocalFixtureArtifactAcquirer,
    LocalFixtureArtifactReader,
    OpenFoodToxAdapter,
    OpenFoodToxArtifactParser,
)
from app.scientific_ingestion.checksums import parser_output_checksum
from app.scientific_ingestion.contracts import (
    ScientificArtifactAcquirer,
    ScientificArtifactParser,
    ScientificArtifactPayloadReader,
    ScientificIngestionConfiguration,
    ScientificSourceAdapter,
)
from app.scientific_ingestion.errors import ScientificAcquisitionError, ScientificParserError
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import ScientificIngestionService
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver
from app.services.substance_resolution_reviews import SubstanceResolutionReviewService


FIXTURES = Path(__file__).parent / "fixtures" / "scientific_sources"
PROVIDERS = {
    "efsa": (EfsaAdapter, EfsaArtifactParser, FIXTURES / "efsa_minimal.json"),
    "openfoodtox": (
        OpenFoodToxAdapter,
        OpenFoodToxArtifactParser,
        FIXTURES / "openfoodtox_minimal.json",
    ),
}


def components(provider, storage_object_id=101, parser_version=None, artifact_path=None,
               artifact_key="primary"):
    adapter_class, parser_class, canonical_path = PROVIDERS[provider]
    options = {"parser_version": parser_version} if parser_version else {}
    adapter = adapter_class(canonical_path, **options)
    fixture = LocalFixtureArtifact(
        path=artifact_path or canonical_path,
        artifact_key=artifact_key,
        artifact_role="primary",
        storage_object_id=storage_object_id,
        content_type="application/json",
        provider_key=provider,
    )
    acquirer = LocalFixtureArtifactAcquirer(fixture)
    reader = LocalFixtureArtifactReader(fixture)
    parser = parser_class(adapter, reader)
    return adapter, fixture, acquirer, reader, parser


class ScientificSourceAdapterContractTests(unittest.TestCase):
    def test_common_contract_release_and_artifact_boundaries(self):
        releases = {}
        parser_types = set()
        for provider in PROVIDERS:
            with self.subTest(provider=provider):
                adapter, _, acquirer, reader, parser = components(provider)
                release = adapter.discover_release()
                manifest = acquirer.acquire(release)
                artifact = manifest.artifacts[0]
                self.assertIsInstance(adapter, ScientificSourceAdapter)
                self.assertIsInstance(acquirer, ScientificArtifactAcquirer)
                self.assertIsInstance(reader, ScientificArtifactPayloadReader)
                self.assertIsInstance(parser, ScientificArtifactParser)
                self.assertEqual(release.source_key, provider)
                self.assertEqual(release.dataset_key, adapter.metadata.dataset_key)
                self.assertTrue(release.external_release_key)
                self.assertEqual(artifact.content_type, "application/json")
                self.assertEqual(artifact.byte_size, len(reader.read_bytes(artifact)))
                self.assertTrue(artifact.source_locator.startswith(f"fixture://{provider}/"))
                self.assertEqual(artifact.acquisition_metadata["mode"], "local_fixture")
                releases[provider] = release
                parser_types.add(type(parser))
        self.assertNotEqual(releases["efsa"], releases["openfoodtox"])
        self.assertEqual(len(parser_types), 2)

    def test_efsa_fixture_parsing_is_deterministic_and_preserves_raw(self):
        adapter, _, acquirer, reader, parser = components("efsa")
        manifest = acquirer.acquire(adapter.discover_release())
        first = parser.parse(manifest)
        second = parser.parse(manifest)
        self.assertEqual(first, second)
        self.assertEqual(parser_output_checksum(first), parser_output_checksum(second))
        self.assertEqual(tuple(item.source_record_key for item in first.records), (
            "EFSA-Q-2025-0001", "EFSA-Q-2025-0002",
        ))
        self.assertEqual({item.error_code for item in first.rejected_records}, {
            "malformed_provider_record", "unsupported_namespace",
        })
        self.assertEqual(first.records[0].substance_identifiers[0].namespace_key, "cas")
        self.assertEqual(first.records[0].substance_identifiers[0].raw_value, "50-00-0")
        self.assertEqual(first.records[0].raw_record["question_number"], "EFSA-Q-2025-0001")
        self.assertEqual(first.records[0].assessment.raw_record, first.records[0].raw_record)
        self.assertEqual(first.records[0].findings[0].raw_payload["finding_id"], "ADI-1")
        self.assertEqual(first.metadata["release_identity"], manifest.release.model_dump(mode="json"))
        self.assertEqual(reader.read_bytes(manifest.artifacts[0]), PROVIDERS["efsa"][2].read_bytes())

    def test_openfoodtox_fixture_is_distinct_deterministic_and_deduplicated(self):
        adapter, _, acquirer, _, parser = components("openfoodtox")
        manifest = acquirer.acquire(adapter.discover_release())
        first = parser.parse(manifest)
        second = parser.parse(manifest)
        self.assertEqual(first, second)
        self.assertEqual(tuple(item.source_record_key for item in first.records), (
            "OFT-ENTRY-0001", "OFT-ENTRY-0002",
        ))
        self.assertEqual({item.error_code for item in first.rejected_records}, {
            "malformed_provider_record", "unsupported_namespace",
        })
        self.assertEqual(tuple(item.code for item in first.warnings), ("duplicate_native_record",))
        self.assertEqual(first.records[0].substance_identifiers[0].namespace_key, "cas")
        self.assertEqual(first.records[1].substance_identifiers[0].namespace_key, "pubchem_cid")
        self.assertEqual(first.records[0].assessment.raw_record["entry_id"], "OFT-ENTRY-0001")
        self.assertEqual(first.records[0].findings[0].raw_payload["effect_id"], "EFFECT-1")

    def test_provider_isolation_and_invalid_document_fail_controlled(self):
        efsa_adapter, _, _, _, _ = components("efsa")
        invalid = LocalFixtureArtifact(
            FIXTURES / "openfoodtox_minimal.json", "primary", "primary", 301,
            provider_key="efsa",
        )
        manifest = LocalFixtureArtifactAcquirer(invalid).acquire(efsa_adapter.discover_release())
        with self.assertRaisesRegex(ScientificParserError, "EFSA fixture schema"):
            EfsaArtifactParser(efsa_adapter, LocalFixtureArtifactReader(invalid)).parse(manifest)
        with self.assertRaisesRegex(ScientificParserError, "unsupported EFSA fixture schema"):
            EfsaAdapter(FIXTURES / "efsa_invalid_document.json").discover_release()

    def test_artifact_integrity_and_network_isolation(self):
        for provider in PROVIDERS:
            with self.subTest(provider=provider):
                adapter, _, acquirer, reader, parser = components(provider)
                manifest = acquirer.acquire(adapter.discover_release())
                bad_reference = manifest.artifacts[0].model_copy(
                    update={"raw_checksum_value": "b" * 64}
                )
                bad_manifest = type(manifest).build(manifest.release, (bad_reference,))
                with self.assertRaises(ScientificAcquisitionError):
                    reader.read_bytes(bad_manifest.artifacts[0])
                with patch.object(socket, "create_connection", side_effect=AssertionError("network")):
                    parsed = parser.parse(manifest)
                self.assertGreaterEqual(len(parsed.records), 1)


class FailingFindingRepository(PostgresScientificPersistenceRepository):
    def _persist_finding(self, cursor, assessment_id, finding):
        raise RuntimeError("phase641 synthetic finding persistence failure")


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0017")
class ScientificSourceAdapterPostgresTests(unittest.TestCase):
    def _install(self, provider, idempotency_key, parser_version=None,
                 artifact_path=None, artifact_key="primary"):
        adapter_class, parser_class, canonical_path = PROVIDERS[provider]
        options = {"parser_version": parser_version} if parser_version else {}
        adapter = adapter_class(canonical_path, **options)
        release = adapter.discover_release()
        payload_path = artifact_path or canonical_path
        payload = payload_path.read_bytes()
        checksum = sha256(payload).hexdigest()
        locator = f"fixture://{provider}/{payload_path.name}"
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
                    VALUES(%s,%s,%s,'Phase 6.4.1 offline fixture')
                    ON CONFLICT(source_id,dataset_key) DO UPDATE SET dataset_name=EXCLUDED.dataset_name
                    RETURNING id
                """, (source_id, adapter.metadata.dataset_key, adapter.metadata.dataset_key))
                dataset_id = cursor.fetchone()["id"]
                cursor.execute("""
                    INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label)
                    VALUES(%s,%s,%s)
                    ON CONFLICT(dataset_id,external_release_key) DO UPDATE
                      SET version_label=EXCLUDED.version_label
                    RETURNING id
                """, (dataset_id, release.external_release_key, release.external_release_key))
                release_id = cursor.fetchone()["id"]
                cursor.execute("""
                    INSERT INTO storage_objects(storage_provider,bucket,object_key,
                      checksum_algorithm,checksum_value,mime_type,byte_size)
                    VALUES('fixture','phase641',%s,'sha256',%s,'application/json',%s)
                    ON CONFLICT DO NOTHING RETURNING id
                """, (locator, checksum, len(payload)))
                row = cursor.fetchone()
                if row is None:
                    cursor.execute("""
                        SELECT id FROM storage_objects
                        WHERE storage_provider='fixture' AND bucket='phase641'
                          AND object_key=%s AND COALESCE(object_version,'')=''
                    """, (locator,))
                    row = cursor.fetchone()
                storage_id = row["id"]
                cursor.execute("""
                    INSERT INTO scientific_release_artifacts(
                      release_id,storage_object_id,artifact_key,artifact_role,format,media_type,
                      raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at,provenance)
                    VALUES(%s,%s,%s,'primary','json','application/json','sha256',%s,%s,NOW(),%s)
                    ON CONFLICT(release_id,artifact_key) DO NOTHING
                """, (release_id, storage_id, artifact_key, checksum, len(payload),
                      psycopg2.extras.Json({"mode": "local_fixture", "locator": locator})))
                cursor.execute("""
                    SELECT id,storage_object_id FROM scientific_release_artifacts
                    WHERE release_id=%s AND artifact_key=%s
                """, (release_id, artifact_key))
                artifact_row = cursor.fetchone()
                self.assertEqual(artifact_row["storage_object_id"], storage_id)
                substance_id, identifier_id = self._known_identifier(cursor)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        fixture = LocalFixtureArtifact(
            payload_path, artifact_key, "primary", storage_id,
            "application/json", provider,
        )
        reader = LocalFixtureArtifactReader(fixture)
        parser = parser_class(adapter, reader)
        config = ScientificIngestionConfiguration(
            adapter=adapter.metadata,
            semantic_configuration={"provider": provider, "mode": "fixture"},
        )
        service = ScientificIngestionService()
        prepared = service.prepare_ingestion_run(
            release, config, (artifact_key,), idempotency_key,
        )
        return {
            "adapter": adapter, "release": release, "release_id": release_id,
            "storage_id": storage_id, "substance_id": substance_id,
            "identifier_id": identifier_id, "parser": parser,
            "service": service, "prepared": prepared,
        }

    @staticmethod
    def _known_identifier(cursor):
        cursor.execute("""
            INSERT INTO substance_identifier_namespaces(
              namespace_key,namespace_version,display_name,normalization_rule_version,provenance)
            VALUES('cas','1','CAS Registry Number','cas_identity_v1',%s)
            ON CONFLICT(namespace_key,namespace_version) DO NOTHING
        """, (psycopg2.extras.Json({"phase": "6.4.1"}),))
        cursor.execute("""
            SELECT id FROM substance_identifier_namespaces
            WHERE namespace_key='cas' AND namespace_version='1'
        """)
        namespace_id = cursor.fetchone()["id"]
        cursor.execute("SELECT id FROM substances WHERE normalized_name='phase641_formaldehyde'")
        row = cursor.fetchone()
        if row is None:
            cursor.execute("""
                INSERT INTO substances(preferred_name,normalized_name,substance_type,status)
                VALUES('Formaldehyde fixture','phase641_formaldehyde','chemical_substance','active')
                RETURNING id
            """)
            row = cursor.fetchone()
        substance_id = row["id"]
        cursor.execute("""
            INSERT INTO substance_identifiers(
              substance_id,namespace_id,identifier_system,identifier_value,
              normalized_value,is_primary,verification_status,provenance)
            VALUES(%s,%s,'CASRN','50-00-0','50-00-0',TRUE,'verified',%s)
            ON CONFLICT(namespace_id,normalized_value) DO NOTHING
        """, (substance_id, namespace_id,
              psycopg2.extras.Json({"phase": "6.4.1", "fixture": True})))
        cursor.execute("""
            SELECT id,substance_id FROM substance_identifiers
            WHERE namespace_id=%s AND normalized_value='50-00-0'
        """, (namespace_id,))
        identifier = cursor.fetchone()
        if identifier["substance_id"] != substance_id:
            raise AssertionError("fixture CAS identifier belongs to another substance")
        return substance_id, identifier["id"]

    @staticmethod
    def _executor(context, repository=None):
        return ScientificIngestionExecutor(
            context["parser"], PostgresScientificSubstanceResolver(), context["service"],
            repository=repository,
            resolution_review_service=SubstanceResolutionReviewService(),
        )

    def test_both_provider_paths_persist_provenance_and_control_unknown_identity(self):
        for provider, unknown_namespace, native_key in (
            ("efsa", "efsa_substance", "EFSA-Q-2025-0001"),
            ("openfoodtox", "pubchem_cid", "OFT-ENTRY-0001"),
        ):
            with self.subTest(provider=provider):
                suffix = uuid.uuid4().hex
                context = self._install(provider, f"phase641-e2e-{suffix}")
                connection = get_connection()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT count(*) FROM substances")
                        substances_before = cursor.fetchone()[0]
                finally:
                    connection.close()
                result = self._executor(context).execute(context["prepared"])
                self.assertEqual(result.run_status, "succeeded")
                self.assertEqual(result.records_accepted, 1)
                self.assertEqual(result.assessments_written, 1)
                self.assertEqual(result.findings_written, 1)
                self.assertEqual(result.records_rejected, 3)
                connection = get_connection()
                try:
                    with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                        cursor.execute("SELECT count(*) FROM substances")
                        self.assertEqual(cursor.fetchone()["count"], substances_before)
                        cursor.execute("""
                            SELECT src.source_key,d.dataset_key,rel.external_release_key,
                              art.artifact_key,r.id run_id,a.source_record_key,
                              a.raw_record,f.raw_payload,a.substance_id
                            FROM scientific_assessments a
                            JOIN scientific_assessment_findings f ON f.assessment_id=a.id
                            JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id
                            JOIN scientific_ingestion_run_artifacts j ON j.ingestion_run_id=r.id
                            JOIN scientific_release_artifacts art ON art.id=j.release_artifact_id
                            JOIN source_dataset_releases rel ON rel.id=r.release_id
                            JOIN source_datasets d ON d.id=rel.dataset_id
                            JOIN sources src ON src.id=d.source_id
                            WHERE r.id=%s
                        """, (context["prepared"].id,))
                        traversal = cursor.fetchone()
                        self.assertEqual(traversal["source_key"], provider)
                        self.assertEqual(traversal["dataset_key"], context["adapter"].metadata.dataset_key)
                        self.assertEqual(traversal["external_release_key"], context["release"].external_release_key)
                        self.assertEqual(traversal["artifact_key"], "primary")
                        self.assertEqual(traversal["source_record_key"], native_key)
                        self.assertEqual(traversal["substance_id"], context["substance_id"])
                        self.assertIsInstance(traversal["raw_record"], dict)
                        self.assertIsInstance(traversal["raw_payload"], dict)
                        cursor.execute("""
                            SELECT c.id,c.namespace_id,count(o.id),o.raw_identifiers
                            FROM substance_resolution_candidates c
                            JOIN substance_resolution_candidate_occurrences o ON o.candidate_id=c.id
                            WHERE c.namespace_key=%s AND o.ingestion_run_id=%s
                            GROUP BY c.id,c.namespace_id,o.raw_identifiers
                        """, (unknown_namespace, context["prepared"].id))
                        candidate = cursor.fetchone()
                        self.assertIsNotNone(candidate)
                        self.assertIsNone(candidate["namespace_id"])
                        self.assertEqual(candidate["count"], 1)
                        self.assertEqual(candidate["raw_identifiers"][0]["namespace_key"], unknown_namespace)
                finally:
                    connection.close()

    def test_retry_and_parser_version_reprocessing_are_idempotent(self):
        suffix = uuid.uuid4().hex
        key = f"phase641-retry-{suffix}"
        first = self._install("openfoodtox", key)
        first_result = self._executor(first).execute(first["prepared"])
        retry = self._install("openfoodtox", key)
        self.assertEqual(retry["prepared"].id, first["prepared"].id)
        self.assertTrue(retry["prepared"].reused)
        retry_result = self._executor(retry).execute(retry["prepared"])
        self.assertTrue(retry_result.reused_terminal_run)
        self.assertEqual(retry_result.parser_output_checksum, first_result.parser_output_checksum)

        second = self._install("openfoodtox", key, parser_version="openfoodtox-parser-2")
        self.assertNotEqual(second["prepared"].id, first["prepared"].id)
        second_result = self._executor(second).execute(second["prepared"])
        self.assertEqual(second_result.run_status, "succeeded")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(DISTINCT ingestion_run_id),count(*)
                    FROM scientific_assessments
                    WHERE ingestion_run_id IN (%s,%s)
                """, (first["prepared"].id, second["prepared"].id))
                self.assertEqual(cursor.fetchone(), (2, 2))
                cursor.execute("""
                    SELECT count(*) FROM substance_identifiers i
                    JOIN substance_identifier_namespaces n ON n.id=i.namespace_id
                    WHERE n.namespace_key='cas' AND n.namespace_version='1'
                      AND i.normalized_value='50-00-0'
                """)
                self.assertEqual(cursor.fetchone()[0], 1)
                cursor.execute("""
                    SELECT count(*) FROM substance_resolution_candidates
                    WHERE namespace_key='pubchem_cid' AND namespace_version='1'
                      AND normalized_value='999999999'
                """)
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            connection.close()

    def test_parser_failure_and_record_transaction_rollback(self):
        suffix = uuid.uuid4().hex
        invalid = self._install(
            "efsa", f"phase641-invalid-{suffix}",
            artifact_path=FIXTURES / "efsa_invalid_document.json",
            artifact_key=f"invalid_{suffix}",
        )
        with self.assertRaises(ScientificParserError):
            self._executor(invalid).execute(invalid["prepared"])
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT run_status FROM scientific_ingestion_runs WHERE id=%s",
                               (invalid["prepared"].id,))
                self.assertEqual(cursor.fetchone()[0], "failed")
                cursor.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",
                               (invalid["prepared"].id,))
                self.assertEqual(cursor.fetchone()[0], 0)
        finally:
            connection.close()

        rollback = self._install("efsa", f"phase641-rollback-{suffix}")
        with self.assertRaisesRegex(RuntimeError, "finding persistence failure"):
            self._executor(rollback, FailingFindingRepository()).execute(rollback["prepared"])
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT run_status FROM scientific_ingestion_runs WHERE id=%s",
                               (rollback["prepared"].id,))
                self.assertEqual(cursor.fetchone()[0], "failed")
                cursor.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",
                               (rollback["prepared"].id,))
                self.assertEqual(cursor.fetchone()[0], 0)
                cursor.execute("""
                    SELECT count(*) FROM scientific_assessment_findings f
                    JOIN scientific_assessments a ON a.id=f.assessment_id
                    WHERE a.ingestion_run_id=%s
                """, (rollback["prepared"].id,))
                self.assertEqual(cursor.fetchone()[0], 0)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
