import hashlib
import html
import io
import json
import os
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date
from pathlib import Path
from threading import Barrier

import httpx
import psycopg2.extras

from app.db import get_connection
from app.repositories.scientific_persistence import PostgresScientificPersistenceRepository
from app.scientific_ingestion.adapters.openfoodtox_real import (
    AcquiredOpenFoodToxArtifact, OPENFOODTOX_CONCEPT_DOI,
    OPENFOODTOX_CONTENT_TYPE, OPENFOODTOX_EXTERNAL_RELEASE_KEY,
    OPENFOODTOX_FILENAME, OPENFOODTOX_RECORD_DOI, OpenFoodTox3Adapter,
    OpenFoodToxArtifactParser, OpenFoodToxIuclidXlsxParser,
    OpenFoodToxRemoteAcquirer, configured_openfoodtox_acquirer,
)
from app.scientific_ingestion.checksums import parser_output_checksum
from app.scientific_ingestion.contracts import (
    ScientificIngestionConfiguration,
)
from app.scientific_ingestion.errors import (
    ScientificAcquisitionError, ScientificParserError, ScientificPersistenceConflict,
)
from app.scientific_ingestion.http_transport import (
    ControlledHttpTransport, HttpAttemptResponse, HttpContentError, HttpRequest,
    HttpResponseError, HttpRetryPolicy,
)
from app.services.scientific_acquisition import ScientificArtifactRegistrationService
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import ScientificIngestionService
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver
from app.services.substance_resolution_reviews import SubstanceResolutionReviewService
from app.storage.base import ObjectMetadata


FIXTURE = (Path(__file__).parent / "fixtures" / "scientific_sources"
           / "openfoodtox_3_iuclid_minimal.json")


def fixture_document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def xlsx_from_fixture(document=None):
    document = document or fixture_document()
    sheets = document["sheets"]

    def worksheet(rows):
        headers = []
        for row in rows:
            for key in row:
                if key not in headers:
                    headers.append(key)
        values = [headers] + [[row.get(key, "") for key in headers] for row in rows]
        xml_rows = []
        for row_number, row in enumerate(values, 1):
            cells = []
            for column, value in enumerate(row, 1):
                number, letters = column, ""
                while number:
                    number, remainder = divmod(number - 1, 26)
                    letters = chr(65 + remainder) + letters
                cells.append(
                    f'<c r="{letters}{row_number}" t="inlineStr"><is><t>'
                    f'{html.escape(str(value))}</t></is></c>'
                )
            xml_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')
        return ('<?xml version="1.0"?><worksheet '
                'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>')

    workbook_sheets, relationships = [], []
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, (name, rows) in enumerate(sheets.items(), 1):
            workbook_sheets.append(
                f'<sheet name="{html.escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
            )
            relationships.append(
                f'<Relationship Id="rId{index}" Target="worksheets/sheet{index}.xml" '
                'Type="worksheet"/>'
            )
            archive.writestr(f"xl/worksheets/sheet{index}.xml", worksheet(rows))
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?><workbook '
            'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?><Relationships '
            'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{"".join(relationships)}</Relationships>',
        )
    return output.getvalue()


class QueueExecutor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers, timeouts, max_bytes):
        self.calls.append(url)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def response(status, body=b"", headers=None, url="https://zenodo.org/resource"):
    values = {"content-length": str(len(body)), **(headers or {})}
    return HttpAttemptResponse(url, status, values, body)


def metadata(body, *, checksum=None, overrides=None):
    result = {
        "id": 19388272,
        "doi": OPENFOODTOX_RECORD_DOI,
        "conceptdoi": OPENFOODTOX_CONCEPT_DOI,
        "metadata": {
            "publication_date": "2026-04-30",
            "license": {"id": "cc-by-nd-4.0"},
        },
        "files": [{
            "key": OPENFOODTOX_FILENAME,
            "size": len(body),
            "checksum": checksum or "md5:" + hashlib.md5(
                body, usedforsecurity=False
            ).hexdigest(),
            "links": {"self": "https://zenodo.org/openfoodtox.xlsx"},
        }],
    }
    if overrides:
        overrides(result)
    return json.dumps(result).encode()


def transport_for(body, *, metadata_body=None, content_type="application/octet-stream"):
    executor = QueueExecutor([
        response(200, metadata_body or metadata(body)),
        response(200, body, {"content-type": content_type}),
    ])
    return ControlledHttpTransport(executor=executor), executor


class OpenFoodToxAcquisitionTests(unittest.TestCase):
    def test_official_metadata_artifact_checksum_and_generic_mime(self):
        workbook = xlsx_from_fixture()
        transport, executor = transport_for(workbook)
        acquired = OpenFoodToxRemoteAcquirer(transport).acquire()
        self.assertEqual(len(executor.calls), 2)
        self.assertEqual(acquired.release.external_release_key,
                         OPENFOODTOX_EXTERNAL_RELEASE_KEY)
        self.assertEqual(acquired.sha256, hashlib.sha256(workbook).hexdigest())
        self.assertEqual(acquired.provider_checksum,
                         "md5:" + hashlib.md5(workbook, usedforsecurity=False).hexdigest())
        self.assertEqual(acquired.acquisition_metadata["actual_content_type"],
                         "application/octet-stream")

    def test_content_type_and_container_are_both_validated(self):
        workbook = xlsx_from_fixture()
        for mime in (OPENFOODTOX_CONTENT_TYPE, "application/octet-stream", "application/zip"):
            with self.subTest(mime=mime):
                transport, _ = transport_for(workbook, content_type=mime)
                self.assertEqual(OpenFoodToxRemoteAcquirer(transport).acquire().body, workbook)
        transport, _ = transport_for(workbook, content_type="text/html")
        with self.assertRaisesRegex(ScientificAcquisitionError, "Content-Type"):
            OpenFoodToxRemoteAcquirer(transport).acquire()
        transport, _ = transport_for(b"not-xlsx")
        with self.assertRaisesRegex(ScientificAcquisitionError, "container validation"):
            OpenFoodToxRemoteAcquirer(transport).acquire()

    def test_provider_checksum_mismatch_and_invalid_metadata_fail_before_persistence(self):
        workbook = xlsx_from_fixture()
        bad_checksum = metadata(workbook, checksum="md5:" + "0" * 32)
        transport, _ = transport_for(workbook, metadata_body=bad_checksum)
        with self.assertRaisesRegex(ScientificAcquisitionError, "checksum mismatch"):
            OpenFoodToxRemoteAcquirer(transport).acquire()
        missing_doi = metadata(workbook, overrides=lambda value: value.pop("doi"))
        transport = ControlledHttpTransport(executor=QueueExecutor([
            response(200, missing_doi)
        ]))
        with self.assertRaisesRegex(ScientificAcquisitionError, "metadata"):
            OpenFoodToxRemoteAcquirer(transport).acquire()

    def test_truncated_and_oversized_downloads_fail_in_shared_transport(self):
        workbook = xlsx_from_fixture()
        executor = QueueExecutor([
            response(200, metadata(workbook)),
            HttpAttemptResponse(
                "https://zenodo.org/openfoodtox.xlsx", 200,
                {"content-length": str(len(workbook) + 1),
                 "content-type": "application/octet-stream"}, workbook,
            ),
        ])
        with self.assertRaises(HttpContentError):
            OpenFoodToxRemoteAcquirer(
                ControlledHttpTransport(executor=executor)
            ).acquire()
        transport, _ = transport_for(workbook)
        with self.assertRaises(HttpContentError):
            OpenFoodToxRemoteAcquirer(
                transport, max_artifact_bytes=len(workbook) - 1
            ).acquire()

    def test_shared_http_failure_policy_remains_explicit(self):
        for status in (400, 401, 403, 404):
            with self.subTest(status=status):
                executor = QueueExecutor([response(status)])
                client = ControlledHttpTransport(executor=executor)
                with self.assertRaises(HttpResponseError):
                    client.get(HttpRequest(
                        "https://zenodo.org/openfoodtox", frozenset({"zenodo.org"})
                    ))
                self.assertEqual(len(executor.calls), 1)
        for status in (408, 429, 500, 502, 503, 504):
            with self.subTest(status=status):
                executor = QueueExecutor([response(status), response(200, b"ok")])
                client = ControlledHttpTransport(
                    executor=executor,
                    retry_policy=HttpRetryPolicy(
                        max_attempts=2, base_backoff_seconds=0,
                        max_backoff_seconds=0, jitter_ratio=0,
                    ),
                    sleep=lambda _: None,
                )
                self.assertEqual(client.get(HttpRequest(
                    "https://zenodo.org/openfoodtox", frozenset({"zenodo.org"})
                )).body, b"ok")
                self.assertEqual(len(executor.calls), 2)
        for error in (httpx.ReadTimeout("timeout"), httpx.ConnectError("dns")):
            executor = QueueExecutor([error, error])
            client = ControlledHttpTransport(
                executor=executor,
                retry_policy=HttpRetryPolicy(
                    max_attempts=2, base_backoff_seconds=0,
                    max_backoff_seconds=0, jitter_ratio=0,
                ),
                sleep=lambda _: None,
            )
            with self.assertRaises(ScientificAcquisitionError):
                client.get(HttpRequest(
                    "https://zenodo.org/openfoodtox", frozenset({"zenodo.org"})
                ))


class OpenFoodToxParserTests(unittest.TestCase):
    def test_real_shape_join_is_deterministic_and_preserves_raw_semantics(self):
        parser = OpenFoodToxIuclidXlsxParser(OpenFoodTox3Adapter(), max_records=1)
        workbook = xlsx_from_fixture()
        first = parser.parse_bytes(workbook, locator="https://zenodo.org/openfoodtox.xlsx")
        second = parser.parse_bytes(workbook, locator="https://zenodo.org/openfoodtox.xlsx")
        self.assertEqual(first, second)
        self.assertEqual(parser_output_checksum(first), parser_output_checksum(second))
        record = first.records[0]
        self.assertEqual(record.source_record_key, "study-0001")
        self.assertEqual(record.substance_identifiers[0].namespace_key, "cas")
        self.assertEqual(record.substance_identifiers[0].raw_value, "1668-54-8")
        self.assertEqual(record.substance_identifiers[1].namespace_key, "efsa_param_code")
        self.assertEqual(record.assessment.document_reference,
                         "https://doi.org/10.2903/j.efsa.2020.6181")
        self.assertEqual(record.findings[0].value_numeric, 1000)
        self.assertEqual(record.findings[0].unit, "mg/kg bw")
        self.assertEqual(record.raw_record["join"]["dossier_uuid"], "dossier-0001")
        self.assertEqual(record.raw_record["literature"]["GeneralInfo.Source"],
                         "doi:10.2903/j.efsa.2020.6181")

    def test_provider_reference_never_falls_back_to_internal_key(self):
        for source in ("", "zenodo_record_19388272", "doi:not-a-doi"):
            with self.subTest(source=source):
                document = fixture_document()
                document["sheets"]["LIT"][0]["GeneralInfo.Source"] = source
                parsed = OpenFoodToxIuclidXlsxParser(
                    OpenFoodTox3Adapter(), max_records=1
                ).parse_bytes(xlsx_from_fixture(document))
                self.assertEqual(len(parsed.records), 0)
                self.assertEqual(parsed.rejected_records[0].error_code,
                                 "malformed_provider_record")

    def test_recognized_unregistered_identifier_is_preserved_for_review(self):
        document = fixture_document()
        document["sheets"]["REF_SUB"][0]["Inventory.CASNumber"] = ""
        parsed = OpenFoodToxIuclidXlsxParser(
            OpenFoodTox3Adapter(), max_records=1
        ).parse_bytes(xlsx_from_fixture(document))
        identifier = parsed.records[0].substance_identifiers[0]
        self.assertEqual(identifier.namespace_key, "efsa_param_code")
        self.assertEqual(identifier.provenance["governance"],
                         "recognized_unregistered_review")

    def test_malformed_scientific_payload_is_a_controlled_parser_failure(self):
        with self.assertRaisesRegex(ScientificParserError, "valid XLSX container"):
            OpenFoodToxIuclidXlsxParser(
                OpenFoodTox3Adapter(), max_records=1
            ).parse_bytes(b"not-an-xlsx")


class MemoryStorage:
    def __init__(self):
        self.objects = {}

    def head_object(self, key):
        value = self.objects.get(key)
        if value is None:
            return None
        return ObjectMetadata(
            key, len(value), OPENFOODTOX_CONTENT_TYPE,
            metadata={"sha256": hashlib.sha256(value).hexdigest()},
        )

    def put_object(self, key, source, mime_type, sha256):
        value = source.read()
        self.objects.setdefault(key, value)
        return ObjectMetadata(key, len(value), mime_type, metadata={"sha256": sha256})

    def download_to(self, key, target):
        target.write(self.objects[key])


class FailingFindingRepository(PostgresScientificPersistenceRepository):
    def _persist_finding(self, cursor, assessment_id, finding):
        raise RuntimeError("phase643 synthetic finding persistence failure")


def acquired_fixture(body=None):
    body = body or xlsx_from_fixture()
    return AcquiredOpenFoodToxArtifact(
        release=OpenFoodTox3Adapter().discover_release(),
        locator="https://zenodo.org/openfoodtox.xlsx",
        filename=OPENFOODTOX_FILENAME,
        content_type=OPENFOODTOX_CONTENT_TYPE,
        body=body,
        sha256=hashlib.sha256(body).hexdigest(),
        byte_size=len(body),
        released_on=date(2026, 4, 30),
        record_doi=OPENFOODTOX_RECORD_DOI,
        concept_doi=OPENFOODTOX_CONCEPT_DOI,
        license_id="cc-by-nd-4.0",
        provider_checksum="md5:" + hashlib.md5(
            body, usedforsecurity=False
        ).hexdigest(),
        acquisition_metadata={"mode": "offline_fixture"},
    )


@unittest.skipUnless(os.environ.get("WYE_TEST_DATABASE"),
                     "requires isolated PostgreSQL at 0017")
class OpenFoodToxPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.storage = MemoryStorage()
        self.service = ScientificArtifactRegistrationService(
            self.storage, storage_provider="memory", bucket="phase643"
        )

    def test_first_write_concurrency_and_changed_upstream_conflict(self):
        custom_release = "zenodo_record_phase643_first_write_" + os.urandom(4).hex()
        acquired = replace(
            acquired_fixture(),
            release=OpenFoodTox3Adapter(custom_release).discover_release(),
        )
        barrier = Barrier(2)
        artifact_key = "oft_concurrent_" + os.urandom(6).hex()

        def register(_):
            barrier.wait(timeout=5)
            return self.service.register_openfoodtox(
                acquired, artifact_key=artifact_key
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(register, range(2)))
        self.assertEqual(len({item.reference.storage_object_id for item in results}), 1)
        self.assertEqual(sorted(item.reused for item in results), [False, True])
        restarted = ScientificArtifactRegistrationService(
            self.storage, storage_provider="memory", bucket="phase643"
        ).register_openfoodtox(acquired, artifact_key=artifact_key)
        self.assertTrue(restarted.reused)
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM scientific_release_artifacts WHERE artifact_key=%s",
                    (artifact_key,),
                )
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            connection.close()
        changed = replace(acquired_fixture(xlsx_from_fixture({
            **fixture_document(),
            "sheets": {
                **fixture_document()["sheets"],
                "LIT": [{
                    **fixture_document()["sheets"]["LIT"][0],
                    "GeneralInfo.Name": "Changed upstream",
                }],
            },
        })), release=acquired.release)
        with self.assertRaises(ScientificPersistenceConflict):
            self.service.register_openfoodtox(changed, artifact_key=artifact_key)

    def test_concurrent_changed_upstream_has_one_winner_and_one_conflict(self):
        custom_release = "zenodo_record_phase643_race_conflict_" + os.urandom(4).hex()
        release = OpenFoodTox3Adapter(custom_release).discover_release()
        first = replace(acquired_fixture(), release=release)
        changed_document = fixture_document()
        changed_document["sheets"]["LIT"][0]["GeneralInfo.Name"] = "Changed bytes"
        second = replace(
            acquired_fixture(xlsx_from_fixture(changed_document)), release=release
        )
        barrier = Barrier(2)
        artifact_key = "oft_conflict_" + os.urandom(6).hex()

        def register(acquired):
            barrier.wait(timeout=5)
            try:
                return self.service.register_openfoodtox(
                    acquired, artifact_key=artifact_key
                )
            except ScientificPersistenceConflict as exc:
                return exc

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(register, (first, second)))
        self.assertEqual(sum(not isinstance(item, Exception) for item in results), 1)
        self.assertEqual(sum(isinstance(item, ScientificPersistenceConflict)
                             for item in results), 1)

    def test_postgres_e2e_provenance_idempotency_and_resolution_candidate(self):
        acquired = acquired_fixture()
        artifact_key = "oft_e2e_" + os.urandom(6).hex()
        registered = self.service.register_openfoodtox(
            acquired, artifact_key=artifact_key
        )
        substance_id = self._install_verified_cas("1668-54-8")
        parser = OpenFoodToxArtifactParser(
            OpenFoodTox3Adapter(), self._reader(acquired), max_records=1
        )
        config = ScientificIngestionConfiguration(
            adapter=OpenFoodTox3Adapter().metadata,
            semantic_configuration={"provider": "openfoodtox", "max_records": 1},
        )
        ingestion = ScientificIngestionService()
        idempotency_key = "phase643-e2e-" + os.urandom(6).hex()
        prepared = ingestion.prepare_ingestion_run(
            acquired.release, config, (artifact_key,), idempotency_key
        )
        executor = ScientificIngestionExecutor(
            parser, PostgresScientificSubstanceResolver(), ingestion,
            resolution_review_service=SubstanceResolutionReviewService(),
        )
        first = executor.execute(prepared)
        retry = executor.execute(ingestion.prepare_ingestion_run(
            acquired.release, config, (artifact_key,), idempotency_key
        ))
        self.assertEqual((first.records_accepted, first.assessments_written,
                          first.findings_written), (1, 1, 1))
        self.assertTrue(retry.reused_terminal_run)
        connection = get_connection()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""SELECT src.source_key,d.dataset_key,rel.external_release_key,
                    a.document_reference,a.substance_id,a.raw_record,f.raw_payload,
                    art.raw_checksum_value,art.provenance
                    FROM scientific_assessments a
                    JOIN scientific_assessment_findings f ON f.assessment_id=a.id
                    JOIN scientific_ingestion_runs run ON run.id=a.ingestion_run_id
                    JOIN source_dataset_releases rel ON rel.id=run.release_id
                    JOIN source_datasets d ON d.id=rel.dataset_id
                    JOIN sources src ON src.id=d.source_id
                    JOIN scientific_ingestion_run_artifacts membership
                      ON membership.ingestion_run_id=run.id
                    JOIN scientific_release_artifacts art
                      ON art.id=membership.release_artifact_id
                    WHERE run.id=%s""", (prepared.id,))
                row = cursor.fetchone()
                self.assertEqual(row["source_key"], "openfoodtox")
                self.assertEqual(row["dataset_key"], "openfoodtox_3")
                self.assertEqual(row["external_release_key"],
                                 OPENFOODTOX_EXTERNAL_RELEASE_KEY)
                self.assertEqual(row["document_reference"],
                                 "https://doi.org/10.2903/j.efsa.2020.6181")
                self.assertEqual(row["substance_id"], substance_id)
                self.assertEqual(row["raw_checksum_value"], acquired.sha256)
                self.assertEqual(row["provenance"]["record_doi"],
                                 OPENFOODTOX_RECORD_DOI)
                self.assertEqual(row["provenance"]["concept_doi"],
                                 OPENFOODTOX_CONCEPT_DOI)
                self.assertEqual(row["raw_record"]["join"]["literature_uuid"],
                                 "literature-0001")
                self.assertTrue(any(
                    key.startswith("ResultsAndDiscussion.")
                    for key in row["raw_payload"]
                ))
        finally:
            connection.close()

    def test_unregistered_efsa_parameter_code_creates_one_review_candidate(self):
        document = fixture_document()
        document["sheets"]["REF_SUB"][0]["Inventory.CASNumber"] = ""
        body = xlsx_from_fixture(document)
        custom_release = "zenodo_record_phase643_unresolved_" + os.urandom(4).hex()
        acquired = replace(
            acquired_fixture(body),
            release=OpenFoodTox3Adapter(custom_release).discover_release(),
        )
        artifact_key = "oft_unresolved_" + os.urandom(6).hex()
        self.service.register_openfoodtox(acquired, artifact_key=artifact_key)
        adapter = OpenFoodTox3Adapter(custom_release)
        parser = OpenFoodToxArtifactParser(
            adapter, self._reader(acquired), max_records=1
        )
        config = ScientificIngestionConfiguration(
            adapter=adapter.metadata,
            semantic_configuration={"provider": "openfoodtox", "max_records": 1},
        )
        ingestion = ScientificIngestionService()
        prepared = ingestion.prepare_ingestion_run(
            acquired.release, config, (artifact_key,),
            "phase643-unresolved-" + os.urandom(6).hex(),
        )
        result = ScientificIngestionExecutor(
            parser, PostgresScientificSubstanceResolver(), ingestion,
            resolution_review_service=SubstanceResolutionReviewService(),
        ).execute(prepared)
        self.assertEqual((result.records_accepted, result.assessments_written,
                          result.findings_written), (0, 0, 0))
        self.assertEqual(result.rejected_resolutions[0].reason_code, "unknown_namespace")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT count(*)
                    FROM substance_resolution_candidate_occurrences occurrence
                    JOIN substance_resolution_candidates candidate
                      ON candidate.id=occurrence.candidate_id
                    WHERE occurrence.ingestion_run_id=%s
                      AND candidate.namespace_key='efsa_param_code'""", (prepared.id,))
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            connection.close()

    def test_efsa_and_openfoodtox_keep_independent_evidence_for_one_substance(self):
        from backend.tests.test_phase_641_scientific_source_adapters import (
            ScientificSourceAdapterPostgresTests,
        )

        phase641 = ScientificSourceAdapterPostgresTests(methodName="runTest")
        efsa = phase641._install(
            "efsa", "phase643-coexist-efsa-" + os.urandom(6).hex()
        )
        efsa_result = phase641._executor(efsa).execute(efsa["prepared"])
        self.assertEqual(efsa_result.assessments_written, 1)

        document = fixture_document()
        document["sheets"]["REF_SUB"][0]["Inventory.CASNumber"] = "50-00-0"
        body = xlsx_from_fixture(document)
        custom_release = "zenodo_record_phase643_coexist_" + os.urandom(4).hex()
        adapter = OpenFoodTox3Adapter(custom_release)
        acquired = replace(
            acquired_fixture(body), release=adapter.discover_release()
        )
        artifact_key = "oft_coexist_" + os.urandom(6).hex()
        self.service.register_openfoodtox(acquired, artifact_key=artifact_key)
        config = ScientificIngestionConfiguration(
            adapter=adapter.metadata,
            semantic_configuration={"provider": "openfoodtox", "max_records": 1},
        )
        ingestion = ScientificIngestionService()
        prepared = ingestion.prepare_ingestion_run(
            acquired.release, config, (artifact_key,),
            "phase643-coexist-oft-" + os.urandom(6).hex(),
        )
        result = ScientificIngestionExecutor(
            OpenFoodToxArtifactParser(
                adapter, self._reader(acquired), max_records=1
            ),
            PostgresScientificSubstanceResolver(), ingestion,
            resolution_review_service=SubstanceResolutionReviewService(),
        ).execute(prepared)
        self.assertEqual((result.assessments_written, result.findings_written), (1, 1))
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT src.source_key,count(*)
                    FROM scientific_assessments assessment
                    JOIN scientific_ingestion_runs run
                      ON run.id=assessment.ingestion_run_id
                    JOIN source_dataset_releases release ON release.id=run.release_id
                    JOIN source_datasets dataset ON dataset.id=release.dataset_id
                    JOIN sources src ON src.id=dataset.source_id
                    WHERE assessment.substance_id=%s
                      AND run.id IN (%s,%s)
                    GROUP BY src.source_key""",
                    (efsa["substance_id"], efsa["prepared"].id, prepared.id))
                self.assertEqual(dict(cursor.fetchall()), {"efsa": 1, "openfoodtox": 1})
        finally:
            connection.close()

    def test_persistence_failure_rolls_back_assessment_and_finding_atomically(self):
        acquired = acquired_fixture()
        artifact_key = "oft_rollback_" + os.urandom(6).hex()
        self.service.register_openfoodtox(acquired, artifact_key=artifact_key)
        self._install_verified_cas("1668-54-8")
        adapter = OpenFoodTox3Adapter()
        config = ScientificIngestionConfiguration(
            adapter=adapter.metadata,
            semantic_configuration={"provider": "openfoodtox", "max_records": 1},
        )
        ingestion = ScientificIngestionService()
        prepared = ingestion.prepare_ingestion_run(
            acquired.release, config, (artifact_key,),
            "phase643-rollback-" + os.urandom(6).hex(),
        )
        executor = ScientificIngestionExecutor(
            OpenFoodToxArtifactParser(
                adapter, self._reader(acquired), max_records=1
            ),
            PostgresScientificSubstanceResolver(), ingestion,
            repository=FailingFindingRepository(),
            resolution_review_service=SubstanceResolutionReviewService(),
        )
        with self.assertRaisesRegex(RuntimeError, "finding persistence failure"):
            executor.execute(prepared)
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",
                    (prepared.id,),
                )
                self.assertEqual(cursor.fetchone()[0], 0)
                cursor.execute(
                    "SELECT run_status FROM scientific_ingestion_runs WHERE id=%s",
                    (prepared.id,),
                )
                self.assertEqual(cursor.fetchone()[0], "failed")
        finally:
            connection.close()

    @staticmethod
    def _reader(acquired):
        class Reader:
            def read_bytes(self, artifact):
                if artifact.raw_checksum_value != acquired.sha256:
                    raise ScientificPersistenceConflict("fixture checksum mismatch")
                return acquired.body
        return Reader()

    @staticmethod
    def _install_verified_cas(value):
        connection = get_connection()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""INSERT INTO substance_identifier_namespaces(
                    namespace_key,namespace_version,display_name,
                    normalization_rule_version,provenance)
                    VALUES('cas','1','CAS Registry Number','cas_identity_v1',%s)
                    ON CONFLICT(namespace_key,namespace_version) DO NOTHING""",
                    (psycopg2.extras.Json({"controlled_test_registration": True}),))
                cursor.execute("""SELECT id FROM substance_identifier_namespaces
                    WHERE namespace_key='cas' AND namespace_version='1'""")
                namespace_id = cursor.fetchone()["id"]
                normalized_name = "phase643_" + value.replace("-", "_")
                cursor.execute("SELECT id FROM substances WHERE normalized_name=%s",
                               (normalized_name,))
                row = cursor.fetchone()
                if row is None:
                    cursor.execute("""INSERT INTO substances(
                        preferred_name,normalized_name,substance_type,status)
                        VALUES(%s,%s,'chemical_substance','active') RETURNING id""",
                        ("OpenFoodTox fixture substance " + value, normalized_name))
                    row = cursor.fetchone()
                substance_id = row["id"]
                cursor.execute("""INSERT INTO substance_identifiers(
                    substance_id,namespace_id,identifier_system,identifier_value,
                    normalized_value,is_primary,verification_status,provenance)
                    VALUES(%s,%s,'CASRN',%s,%s,TRUE,'verified',%s)
                    ON CONFLICT(namespace_id,normalized_value) DO NOTHING""",
                    (substance_id, namespace_id, value, value,
                     psycopg2.extras.Json({"phase": "6.4.3", "fixture": True})))
            connection.commit()
            return substance_id
        finally:
            connection.close()


@unittest.skipUnless(os.environ.get("WYE_RUN_REAL_OPENFOODTOX_TESTS") == "1",
                     "real OpenFoodTox network test requires explicit opt-in")
class RealOpenFoodToxOptInTests(unittest.TestCase):
    def test_real_release_is_bounded_and_parseable(self):
        acquired = configured_openfoodtox_acquirer().acquire()
        parsed = OpenFoodToxIuclidXlsxParser(
            OpenFoodTox3Adapter(
                acquired.release.external_release_key,
                record_doi=acquired.record_doi,
            ), max_records=1,
        ).parse_bytes(acquired.body, locator=acquired.locator)
        self.assertEqual(acquired.sha256, hashlib.sha256(acquired.body).hexdigest())
        self.assertEqual(len(parsed.records), 1)


@unittest.skipUnless(
    os.environ.get("WYE_RUN_REAL_OPENFOODTOX_TESTS") == "1"
    and os.environ.get("WYE_TEST_DATABASE"),
    "real OpenFoodTox persistence E2E requires opt-in and isolated PostgreSQL",
)
class RealOpenFoodToxPersistenceOptInTests(OpenFoodToxPersistenceTests):
    def test_remote_artifact_to_verified_identity_assessment_and_finding(self):
        acquired = configured_openfoodtox_acquirer().acquire()
        adapter = OpenFoodTox3Adapter(
            acquired.release.external_release_key, record_doi=acquired.record_doi
        )
        preview = OpenFoodToxIuclidXlsxParser(adapter, max_records=1).parse_bytes(
            acquired.body, locator=acquired.locator
        )
        identifier = next(item for item in preview.records[0].substance_identifiers
                          if item.namespace_key == "cas")
        substance_id = self._install_verified_cas(identifier.normalized_value)
        self.service.register_openfoodtox(
            acquired, artifact_key="oft_real_primary"
        )
        parser = OpenFoodToxArtifactParser(adapter, self._reader(acquired), max_records=1)
        config = ScientificIngestionConfiguration(
            adapter=adapter.metadata,
            semantic_configuration={"provider": "openfoodtox", "max_records": 1},
        )
        ingestion = ScientificIngestionService()
        prepared = ingestion.prepare_ingestion_run(
            acquired.release, config, ("oft_real_primary",), "phase643-real-e2e"
        )
        result = ScientificIngestionExecutor(
            parser, PostgresScientificSubstanceResolver(), ingestion,
            resolution_review_service=SubstanceResolutionReviewService(),
        ).execute(prepared)
        self.assertEqual((result.assessments_written, result.findings_written), (1, 1))
        connection = get_connection()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""SELECT a.document_reference,a.substance_id,
                    count(f.id) AS findings
                    FROM scientific_assessments a
                    JOIN scientific_assessment_findings f ON f.assessment_id=a.id
                    WHERE a.ingestion_run_id=%s
                    GROUP BY a.id""", (prepared.id,))
                row = cursor.fetchone()
                self.assertTrue(row["document_reference"].startswith("https://doi.org/10."))
                self.assertNotIn("zenodo_record_", row["document_reference"])
                self.assertEqual(row["substance_id"], substance_id)
                print(json.dumps({
                    "bytes": acquired.byte_size,
                    "sha256": acquired.sha256,
                    "content_type": acquired.acquisition_metadata["actual_content_type"],
                    "record_doi": acquired.record_doi,
                    "concept_doi": acquired.concept_doi,
                    "native_identifier": identifier.normalized_value,
                    "resolution": "verified",
                    "assessments": result.assessments_written,
                    "findings": result.findings_written,
                    "document_reference": row["document_reference"],
                }, sort_keys=True))
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
