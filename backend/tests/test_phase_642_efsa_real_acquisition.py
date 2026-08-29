import hashlib
import io
import json
import os
import unittest
import zipfile
from datetime import date
from concurrent.futures import ThreadPoolExecutor

import httpx
import psycopg2.extras

from app.db import get_connection

from app.scientific_ingestion.adapters.efsa_qps import (
    AcquiredEfsaArtifact, EfsaQpsAdapter, EfsaQpsArtifactParser,
    EfsaQpsRemoteAcquirer, EfsaQpsXlsxParser,
    QPS_CONCEPT_DOI, QPS_EXTERNAL_RELEASE_KEY, QPS_RECORD_DOI,
)
from app.services.scientific_acquisition import ScientificArtifactRegistrationService
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import ScientificIngestionService
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver
from app.services.substance_resolution_reviews import SubstanceResolutionReviewService
from app.scientific_ingestion.contracts import ScientificArtifactManifest, ScientificIngestionConfiguration
from app.storage.base import ObjectMetadata
from app.scientific_ingestion.errors import ScientificAcquisitionError, ScientificParserError
from app.scientific_ingestion.http_transport import (
    ControlledHttpTransport, HttpAttemptResponse, HttpContentError, HttpPolicyError,
    HttpRequest, HttpResponseError, HttpRetryPolicy,
)


def xlsx_bytes(species="Bacillus example", qualification="For production purposes only"):
    shared = ["title", "Microbiological Group", "Microbiological Subgroup", "Family", "Genus",
              "Species", "Synonyms: valid names according to authoritative databases",
              "Qualification 1", "Qualification 2", "Qualification 3",
              "Bacteria", "Firmicutes", "Exampleaceae", "Bacillus", species, "", qualification]
    def row(number, values):
        cells = "".join(f'<c r="{chr(65+i)}{number}" t="s"><v>{shared.index(v)}</v></c>'
                        for i, v in enumerate(values))
        return f'<row r="{number}">{cells}</row>'
    sheet = ('<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             + row(1, ["title"]) + row(2, shared[1:10])
             + row(3, ["Bacteria", "Firmicutes", "Exampleaceae", "Bacillus", species, "", qualification, "", ""])
             + '</sheetData></worksheet>')
    workbook = '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="QPS List" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="worksheet"/></Relationships>'
    strings = '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' + "".join(f"<si><t>{v}</t></si>" for v in shared) + "</sst>"
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/sharedStrings.xml", strings)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return out.getvalue()


class QueueExecutor:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []
    def __call__(self, url, headers, timeouts, max_bytes):
        self.calls.append(url)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def response(status, body=b"", headers=None, url="https://zenodo.org/resource"):
    values = {"content-length": str(len(body)), **(headers or {})}
    return HttpAttemptResponse(url, status, values, body)


class TransportPolicyTests(unittest.TestCase):
    def transport(self, responses, attempts=3):
        executor = QueueExecutor(responses)
        sleeps = []
        return ControlledHttpTransport(executor=executor,
            retry_policy=HttpRetryPolicy(max_attempts=attempts, base_backoff_seconds=.1,
                                         max_backoff_seconds=2, jitter_ratio=0),
            sleep=sleeps.append), executor, sleeps

    def test_valid_response_and_allow_list(self):
        transport, executor, _ = self.transport([response(200, b"ok")])
        got = transport.get(HttpRequest("https://zenodo.org/a", frozenset({"zenodo.org"})))
        self.assertEqual((got.body, got.attempts), (b"ok", 1))
        with self.assertRaises(HttpPolicyError):
            transport.get(HttpRequest("https://evil.invalid/a", frozenset({"zenodo.org"})))

    def test_redirect_is_controlled_and_host_checked(self):
        transport, _, _ = self.transport([
            response(302, headers={"location": "/final"}), response(200, b"ok")])
        self.assertEqual(transport.get(HttpRequest("https://zenodo.org/start",
            frozenset({"zenodo.org"}))).body, b"ok")
        transport, _, _ = self.transport([response(301, headers={"location": "https://evil.invalid/x"})])
        with self.assertRaises(HttpPolicyError):
            transport.get(HttpRequest("https://zenodo.org/start", frozenset({"zenodo.org"})))

    def test_permanent_http_matrix_is_not_retried(self):
        for status in (204, 400, 401, 403, 404):
            with self.subTest(status=status):
                transport, executor, _ = self.transport([response(status)])
                with self.assertRaises(HttpResponseError):
                    transport.get(HttpRequest("https://zenodo.org/x", frozenset({"zenodo.org"})))
                self.assertEqual(len(executor.calls), 1)

    def test_transient_matrix_has_bounded_retry_and_retry_after(self):
        for status in (408, 429, 500, 502, 503, 504):
            with self.subTest(status=status):
                transport, executor, sleeps = self.transport([
                    response(status, headers={"retry-after": "1"}), response(200, b"ok")])
                self.assertEqual(transport.get(HttpRequest("https://zenodo.org/x",
                    frozenset({"zenodo.org"}))).attempts, 2)
                self.assertEqual((len(executor.calls), sleeps), (2, [1.0]))

    def test_timeout_and_connection_failure_are_bounded(self):
        for failure in (httpx.ReadTimeout("late"), httpx.ConnectError("dns")):
            transport, executor, _ = self.transport([failure, failure, failure])
            with self.assertRaises(ScientificAcquisitionError):
                transport.get(HttpRequest("https://zenodo.org/x", frozenset({"zenodo.org"})))
            self.assertEqual(len(executor.calls), 3)

    def test_truncation_and_size_violation_are_permanent(self):
        transport, executor, _ = self.transport([
            HttpAttemptResponse("https://zenodo.org/x", 200, {"content-length": "9"}, b"short")])
        with self.assertRaises(HttpContentError):
            transport.get(HttpRequest("https://zenodo.org/x", frozenset({"zenodo.org"})))
        self.assertEqual(len(executor.calls), 1)
        transport, _, _ = self.transport([response(200, b"too large")])
        with self.assertRaises(HttpContentError):
            transport.get(HttpRequest("https://zenodo.org/x", frozenset({"zenodo.org"}), max_bytes=2))


class EfsaAcquisitionAndParserTests(unittest.TestCase):
    def test_acquisition_verifies_metadata_size_and_checksum_before_parse(self):
        workbook = xlsx_bytes()
        md5 = hashlib.md5(workbook, usedforsecurity=False).hexdigest()
        metadata = json.dumps({"metadata": {"doi": QPS_RECORD_DOI, "conceptdoi": QPS_CONCEPT_DOI,
            "publication_date": "2026-07-06", "license": {"id": "cc-by-4.0"}},
            "files": [{"key": "qps.xlsx", "size": len(workbook), "checksum": "md5:" + md5,
                       "links": {"self": "https://zenodo.org/api/records/21216051/files/qps.xlsx/content"}}]}).encode()
        transport, _, _ = TransportPolicyTests().transport([response(200, metadata), response(200, workbook)])
        acquired = EfsaQpsRemoteAcquirer(transport).acquire()
        self.assertEqual(acquired.sha256, hashlib.sha256(workbook).hexdigest())
        self.assertEqual(acquired.release.external_release_key, QPS_EXTERNAL_RELEASE_KEY)

    def test_real_shape_parser_is_deterministic_and_preserves_raw(self):
        parser = EfsaQpsXlsxParser(EfsaQpsAdapter())
        first = parser.parse_bytes(xlsx_bytes())
        second = parser.parse_bytes(xlsx_bytes())
        self.assertEqual(first, second)
        record = first.records[0]
        self.assertEqual(record.substance_identifiers[0].namespace_key, "efsa_qps_taxon")
        self.assertEqual(record.raw_record["Species"], "Bacillus example")
        self.assertEqual(len(record.findings), 2)

    def test_invalid_container_never_produces_records(self):
        with self.assertRaises(ScientificParserError):
            EfsaQpsXlsxParser(EfsaQpsAdapter()).parse_bytes(b"not an xlsx")


class MemoryStorage:
    def __init__(self): self.objects = {}
    def head_object(self, key):
        value = self.objects.get(key)
        return None if value is None else ObjectMetadata(key, len(value), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", metadata={"sha256": hashlib.sha256(value).hexdigest()})
    def put_object(self, key, source, mime_type, sha256):
        value = source.read()
        self.objects.setdefault(key, value)
        return ObjectMetadata(key, len(value), mime_type, metadata={"sha256": sha256})
    def download_to(self, key, target): target.write(self.objects[key])


@unittest.skipUnless(os.environ.get("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0017")
class ArtifactPersistenceTests(unittest.TestCase):
    def acquired(self, body=None):
        body = body or xlsx_bytes()
        return AcquiredEfsaArtifact(EfsaQpsAdapter().discover_release(), "https://zenodo.org/file",
            "qps.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", body,
            hashlib.sha256(body).hexdigest(), len(body), date(2026, 7, 6), QPS_RECORD_DOI,
            QPS_CONCEPT_DOI, "cc-by-4.0", None, {"test": True})

    def test_idempotency_changed_upstream_and_two_workers(self):
        storage = MemoryStorage()
        service = ScientificArtifactRegistrationService(storage, storage_provider="memory", bucket="phase642")
        acquired = self.acquired()
        first = service.register_efsa_qps(acquired)
        second = service.register_efsa_qps(acquired)
        self.assertFalse(first.reused)
        self.assertTrue(second.reused)
        self.assertEqual(first.reference.storage_object_id, second.reference.storage_object_id)
        with self.assertRaises(Exception):
            service.register_efsa_qps(self.acquired(xlsx_bytes("Changed upstream")))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: service.register_efsa_qps(acquired), range(2)))
        self.assertEqual(len({r.reference.storage_object_id for r in results}), 1)


@unittest.skipUnless(os.environ.get("WYE_RUN_REAL_EFSA_TESTS") == "1",
                     "real EFSA network test requires explicit opt-in")
class RealEfsaOptInTests(unittest.TestCase):
    def test_real_official_qps_release_is_bounded_and_parseable(self):
        transport = ControlledHttpTransport()
        acquired = EfsaQpsRemoteAcquirer(transport).acquire()
        parsed = EfsaQpsXlsxParser(EfsaQpsAdapter(acquired.record_doi), max_records=3).parse_bytes(
            acquired.body, locator=acquired.locator)
        self.assertEqual(acquired.sha256, hashlib.sha256(acquired.body).hexdigest())
        self.assertGreater(len(parsed.records), 0)
        self.assertLessEqual(len(parsed.records), 3)


@unittest.skipUnless(os.environ.get("WYE_RUN_REAL_EFSA_TESTS") == "1" and os.environ.get("WYE_TEST_DATABASE"),
                     "real EFSA persistence E2E requires opt-in and isolated PostgreSQL")
class RealEfsaPersistenceOptInTests(unittest.TestCase):
    def test_remote_artifact_to_verified_identity_assessment_and_findings(self):
        acquired = EfsaQpsRemoteAcquirer(ControlledHttpTransport()).acquire()
        adapter = EfsaQpsAdapter(acquired.release.external_release_key)
        preview = EfsaQpsXlsxParser(adapter, max_records=1).parse_bytes(acquired.body,
                                                                       locator=acquired.locator)
        identifier = preview.records[0].substance_identifiers[0]
        storage = MemoryStorage()
        registered = ScientificArtifactRegistrationService(
            storage, storage_provider="memory", bucket="phase642-real"
        ).register_efsa_qps(acquired)
        connection = get_connection()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""INSERT INTO substance_identifier_namespaces(
                    namespace_key,namespace_version,display_name,normalization_rule_version,provenance)
                    VALUES('efsa_qps_taxon','1','EFSA QPS taxonomic unit','efsa_qps_taxon_v1',%s)
                    ON CONFLICT(namespace_key,namespace_version) DO NOTHING""",
                    (psycopg2.extras.Json({"controlled_test_registration": True}),))
                cursor.execute("SELECT id FROM substance_identifier_namespaces WHERE namespace_key='efsa_qps_taxon' AND namespace_version='1'")
                namespace_id = cursor.fetchone()["id"]
                cursor.execute("""INSERT INTO substances(preferred_name,normalized_name,scientific_name,
                    substance_type,status) VALUES(%s,%s,%s,'biological_substance','active') RETURNING id""",
                    (identifier.raw_value, "phase642_" + identifier.normalized_value.replace(" ", "_"), identifier.raw_value))
                substance_id = cursor.fetchone()["id"]
                cursor.execute("""INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,
                    identifier_value,normalized_value,is_primary,verification_status,provenance)
                    VALUES(%s,%s,'EFSA_QPS_TAXON',%s,%s,TRUE,'verified',%s)""",
                    (substance_id, namespace_id, identifier.raw_value, identifier.normalized_value,
                     psycopg2.extras.Json({"record_doi": acquired.record_doi})))
            connection.commit()
        finally:
            connection.close()
        manifest = ScientificArtifactManifest.build(acquired.release, (registered.reference,))
        class Reader:
            def read_bytes(self, artifact): return acquired.body
        parser = EfsaQpsArtifactParser(adapter, Reader(), max_records=1)
        config = ScientificIngestionConfiguration(adapter=adapter.metadata,
            semantic_configuration={"provider": "efsa", "dataset": "qps", "max_records": 1})
        service = ScientificIngestionService()
        prepared = service.prepare_ingestion_run(acquired.release, config, ("primary",),
                                                  "phase642-real-e2e")
        result = ScientificIngestionExecutor(parser, PostgresScientificSubstanceResolver(), service,
            resolution_review_service=SubstanceResolutionReviewService()).execute(prepared)
        self.assertEqual((result.assessments_written, result.records_accepted), (1, 1))
        self.assertGreaterEqual(result.findings_written, 1)


if __name__ == "__main__":
    unittest.main()
