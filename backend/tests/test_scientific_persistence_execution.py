import os
import threading
import unittest
import uuid
from decimal import Decimal

import psycopg2.extras

from app.db import get_connection
from app.repositories.scientific_persistence import PostgresScientificPersistenceRepository
from app.scientific_ingestion.checksums import (
    assessment_checksum, finding_checksum, parser_output_checksum,
)
from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata, ScientificIngestionConfiguration, ScientificReleaseIdentity,
)
from app.scientific_ingestion.errors import ScientificParserError, ScientificPersistenceConflict
from app.scientific_ingestion.fake import FakeScientificArtifactParser
from app.scientific_ingestion.resolution import FakeScientificSubstanceResolver
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import ScientificIngestionService


class ScientificChecksumUnitTests(unittest.TestCase):
    def test_parser_assessment_and_finding_checksums_are_stable_and_semantic(self):
        parser = FakeScientificArtifactParser()
        manifest = type("Manifest", (), {"fingerprint": "a" * 64})()
        first = parser.parse(manifest); second = parser.parse(manifest)
        self.assertEqual(parser_output_checksum(first), parser_output_checksum(second))
        changed_finding = first.records[0].findings[0].model_copy(update={"value_numeric": Decimal("99")})
        changed_record = first.records[0].model_copy(update={"findings": (changed_finding,) + first.records[0].findings[1:]})
        changed = first.model_copy(update={"records": (changed_record,) + first.records[1:]})
        self.assertNotEqual(parser_output_checksum(first), parser_output_checksum(changed))
        self.assertNotEqual(finding_checksum(first.records[0].findings[0]), finding_checksum(changed_finding))
        changed_assessment = first.records[0].assessment.model_copy(update={"assessment_version": "2"})
        self.assertNotEqual(assessment_checksum(first.records[0].assessment), assessment_checksum(changed_assessment))


class FatalFakeParser:
    def parse(self, manifest):
        raise ScientificParserError("synthetic parser failure")


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0013")
class ScientificPersistenceExecutionTests(unittest.TestCase):
    def fixture(self):
        suffix=uuid.uuid4().hex
        source_key=f"execution_source_{suffix}"; dataset_key=f"execution_dataset_{suffix}"; release_key=f"execution_release_{suffix}"
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id",(source_key,source_key)); source_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,%s,%s) RETURNING id",(source_id,dataset_key,dataset_key)); dataset_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,%s) RETURNING id",(dataset_id,release_key,release_key)); release_id=cur.fetchone()[0]
                checksum="a"*64
                cur.execute("INSERT INTO storage_objects(storage_provider,bucket,object_key,byte_size,checksum_algorithm,checksum_value) VALUES('test','scientific',%s,128,'sha256',%s) RETURNING id",(f"execution/{suffix}",checksum)); storage_id=cur.fetchone()[0]
                cur.execute("INSERT INTO scientific_release_artifacts(release_id,storage_object_id,artifact_key,artifact_role,raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at) VALUES(%s,%s,'primary','primary','sha256',%s,128,NOW())",(release_id,storage_id,checksum))
                substance_ids=[]
                for label in ("A","B"):
                    cur.execute("INSERT INTO substances(preferred_name,normalized_name,substance_type) VALUES(%s,%s,'unknown') RETURNING id",(f"Test Substance {label} {suffix}",f"test_substance_{label.lower()}_{suffix}")); substance_ids.append(cur.fetchone()[0])
            conn.commit()
        finally: conn.close()
        metadata=ScientificAdapterMetadata(source_key=source_key,dataset_key=dataset_key,
            adapter_version="fake-adapter-1",acquisition_version="fake-acquisition-1",
            parser_version="fake-parser-1",normalization_schema_version="fake-normalization-1")
        release=ScientificReleaseIdentity(source_key=source_key,dataset_key=dataset_key,external_release_key=release_key)
        config=ScientificIngestionConfiguration(adapter=metadata)
        service=ScientificIngestionService()
        prepared=service.prepare_ingestion_run(release,config,("primary",),f"execution-{suffix}")
        return prepared,service,release_id,tuple(substance_ids),source_key

    def resolver(self, substance_ids, unresolved_b=False):
        return FakeScientificSubstanceResolver(
            {"test_record_a":substance_ids[0],"test_record_b":substance_ids[1]},
            {"test_record_b":"unresolved"} if unresolved_b else None,
        )

    def test_full_pipeline_retry_checksums_raw_payload_and_provenance(self):
        prepared,service,release_id,substances,source_key=self.fixture()
        executor=ScientificIngestionExecutor(FakeScientificArtifactParser(),self.resolver(substances),service)
        result=executor.execute(prepared)
        self.assertEqual((result.records_seen,result.records_accepted,result.records_rejected),(2,2,0))
        self.assertEqual((result.assessments_written,result.findings_written,result.warnings_count),(2,3,1))
        retry=executor.execute(prepared); self.assertTrue(retry.reused_terminal_run); self.assertEqual(retry.parser_output_checksum,result.parser_output_checksum)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*),count(raw_record),count(normalized_checksum_value) FROM scientific_assessments WHERE ingestion_run_id=%s",(prepared.id,)); self.assertEqual(cur.fetchone(),(2,2,2))
                cur.execute("SELECT count(*),count(raw_payload),count(finding_fingerprint) FROM scientific_assessment_findings WHERE assessment_id IN (SELECT id FROM scientific_assessments WHERE ingestion_run_id=%s)",(prepared.id,)); self.assertEqual(cur.fetchone(),(3,3,3))
                cur.execute("SELECT count(DISTINCT s.id),count(DISTINCT a.id),count(DISTINCT f.id),count(DISTINCT j.release_artifact_id),max(src.source_key) FROM substances s JOIN scientific_assessments a ON a.substance_id=s.id JOIN scientific_assessment_findings f ON f.assessment_id=a.id JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id JOIN scientific_ingestion_run_artifacts j ON j.ingestion_run_id=r.id JOIN scientific_release_artifacts ra ON ra.id=j.release_artifact_id JOIN source_dataset_releases rel ON rel.id=r.release_id JOIN source_datasets d ON d.id=rel.dataset_id JOIN sources src ON src.id=d.source_id WHERE r.id=%s",(prepared.id,)); self.assertEqual(cur.fetchone(),(2,2,3,1,source_key))
                cur.execute("SELECT parser_output_checksum_algorithm,parser_output_checksum_value FROM scientific_ingestion_runs WHERE id=%s",(prepared.id,)); algorithm,value=cur.fetchone(); self.assertEqual(algorithm,"sha256"); self.assertEqual(value,result.parser_output_checksum)
        finally: conn.close()

    def test_unresolved_record_is_rejected_without_dummy_assessment(self):
        prepared,service,_,substances,_=self.fixture()
        result=ScientificIngestionExecutor(FakeScientificArtifactParser(),self.resolver(substances,True),service).execute(prepared)
        self.assertEqual((result.records_seen,result.records_accepted,result.records_rejected),(2,1,1))
        self.assertEqual((result.assessments_written,result.findings_written),(1,2))
        self.assertEqual(result.rejected_resolutions[0].reason_code,"substance_unresolved")

    def test_parser_failure_marks_run_failed_without_materializations(self):
        prepared,service,_,substances,_=self.fixture()
        with self.assertRaises(ScientificParserError):
            ScientificIngestionExecutor(FatalFakeParser(),self.resolver(substances),service).execute(prepared)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT run_status,error_code FROM scientific_ingestion_runs WHERE id=%s",(prepared.id,)); self.assertEqual(cur.fetchone(),("failed","scientific_parser_error"))
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],0)
        finally: conn.close()

    def test_conflicting_assessment_fails_run_without_silent_reuse(self):
        prepared,service,release_id,substances,_=self.fixture(); parser=FakeScientificArtifactParser(); parsed=parser.parse(prepared.manifest)
        service.mark_running(prepared.id)
        repository=PostgresScientificPersistenceRepository(); resolved=self.resolver(substances).resolve(parsed.records[0]).record
        conn=get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur: repository.persist_record(cur,prepared.id,release_id,resolved)
            conn.commit()
        finally: conn.close()
        conflicting_assessment=parsed.records[0].assessment.model_copy(update={"assessment_version":"conflict"})
        conflict_record=parsed.records[0].model_copy(update={"assessment":conflicting_assessment})
        conflict_result=parsed.model_copy(update={"records":(conflict_record,)})
        class ConflictParser:
            def parse(self, manifest): return conflict_result
        with self.assertRaises(ScientificPersistenceConflict):
            ScientificIngestionExecutor(ConflictParser(),self.resolver(substances),service).execute(prepared)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT run_status FROM scientific_ingestion_runs WHERE id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],"failed")
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],1)
        finally: conn.close()

    def test_atomic_finding_conflict_and_concurrent_idempotent_persistence(self):
        prepared,service,release_id,substances,_=self.fixture(); service.mark_running(prepared.id)
        parsed=FakeScientificArtifactParser().parse(prepared.manifest); resolved=self.resolver(substances).resolve(parsed.records[0]).record
        repository=PostgresScientificPersistenceRepository(); barrier=threading.Barrier(2); outputs=[]; errors=[]
        def worker():
            conn=get_connection()
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    barrier.wait(); outputs.append(repository.persist_record(cur,prepared.id,release_id,resolved))
                conn.commit()
            except Exception as exc: conn.rollback(); errors.append(exc)
            finally: conn.close()
        threads=[threading.Thread(target=worker) for _ in range(2)]; [t.start() for t in threads]; [t.join(20) for t in threads]
        self.assertFalse(errors); self.assertEqual(outputs[0].assessment_id,outputs[1].assessment_id)
        changed=parsed.records[0].findings[1].model_copy(update={"value_numeric":Decimal("999")})
        new_finding=parsed.records[0].findings[0].model_copy(update={"source_record_key":"new_finding_before_conflict"})
        conflict_record=parsed.records[0].model_copy(update={"findings":(new_finding,changed)})
        conflict=self.resolver(substances).resolve(conflict_record).record
        conn=get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                with self.assertRaises(ScientificPersistenceConflict): repository.persist_record(cur,prepared.id,release_id,conflict)
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],1)
                cur.execute("SELECT count(*) FROM scientific_assessment_findings WHERE assessment_id=%s",(outputs[0].assessment_id,)); self.assertEqual(cur.fetchone()[0],2)
        finally: conn.close()


if __name__ == "__main__": unittest.main()
