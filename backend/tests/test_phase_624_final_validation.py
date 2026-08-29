import os
import unittest
import uuid

import psycopg2.extras

from app.db import get_connection
from app.repositories.scientific_persistence import PostgresScientificPersistenceRepository
from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata, ScientificIngestionConfiguration, ScientificParserResult,
    ScientificParserWarning, ScientificRecordRejection, ScientificReleaseIdentity,
)
from app.scientific_ingestion.errors import ScientificPersistenceConflict
from app.scientific_ingestion.fake import FakeScientificArtifactParser
from app.scientific_ingestion.resolution import FakeScientificSubstanceResolver
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import ScientificIngestionService


class CountingParser:
    def __init__(self, result=None, version=None):
        self.calls=0; self.result=result; self.version=version
    def parse(self, manifest):
        self.calls+=1
        result=self.result or FakeScientificArtifactParser().parse(manifest)
        return result.model_copy(update={"parser_version":self.version}) if self.version else result


class FailingResolver:
    def resolve(self, record):
        raise RuntimeError("synthetic resolver infrastructure failure")


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0013")
class Phase624FinalValidationTests(unittest.TestCase):
    def fixture(self, parser_version="fake-parser-1"):
        suffix=uuid.uuid4().hex; source_key=f"validation_source_{suffix}"; dataset_key=f"validation_dataset_{suffix}"; release_key=f"validation_release_{suffix}"
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id",(source_key,source_key)); source_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,%s,%s) RETURNING id",(source_id,dataset_key,dataset_key)); dataset_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,%s) RETURNING id",(dataset_id,release_key,release_key)); release_id=cur.fetchone()[0]
                artifact_ids={}
                for position,key in enumerate(("artifact_a","artifact_b","artifact_c")):
                    checksum=format(position+1,"064x")
                    cur.execute("INSERT INTO storage_objects(storage_provider,bucket,object_key,byte_size,checksum_algorithm,checksum_value) VALUES('test','scientific',%s,%s,'sha256',%s) RETURNING id",(f"validation/{suffix}/{key}",position+20,checksum)); storage_id=cur.fetchone()[0]
                    cur.execute("INSERT INTO scientific_release_artifacts(release_id,storage_object_id,artifact_key,artifact_role,raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at) VALUES(%s,%s,%s,%s,'sha256',%s,%s,NOW()) RETURNING id",(release_id,storage_id,key,"primary" if position==0 else "attachment",checksum,position+20)); artifact_ids[key]=cur.fetchone()[0]
                substances=[]
                for label in ("a","b"):
                    cur.execute("INSERT INTO substances(preferred_name,normalized_name,substance_type) VALUES(%s,%s,'unknown') RETURNING id",(f"Validation {label} {suffix}",f"validation_{label}_{suffix}")); substances.append(cur.fetchone()[0])
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Validation identifier','validation_v1') RETURNING id",(f"validation_ns_{suffix}",)); namespace_id=cur.fetchone()[0]
                for position,substance_id in enumerate(substances):
                    cur.execute("INSERT INTO substance_identifiers(substance_id,identifier_system,identifier_value,normalized_value,is_primary,verification_status,namespace_id) VALUES(%s,'validation',%s,%s,true,'verified',%s)",(substance_id,f"TEST-{position}",f"test-{position}-{suffix}",namespace_id))
            conn.commit()
        finally: conn.close()
        metadata=ScientificAdapterMetadata(source_key=source_key,dataset_key=dataset_key,
            adapter_version="fake-adapter-1",acquisition_version="fake-acquisition-1",
            parser_version=parser_version,normalization_schema_version="fake-normalization-1")
        release=ScientificReleaseIdentity(source_key=source_key,dataset_key=dataset_key,external_release_key=release_key)
        return release_id,artifact_ids,tuple(substances),release,ScientificIngestionConfiguration(adapter=metadata),source_key

    def prepared(self, fixture, service, keys=("artifact_c","artifact_a"), idem=None):
        _,_,_,release,config,_=fixture
        return service.prepare_ingestion_run(release,config,keys,idem or uuid.uuid4().hex)

    def resolver(self, substances, statuses=None):
        return FakeScientificSubstanceResolver({"test_record_a":substances[0],"test_record_b":substances[1]},statuses)

    def test_full_e2e_exact_subset_checksums_identifiers_and_terminal_retry(self):
        fixture=self.fixture(); _,artifacts,substances,_,_,source_key=fixture; service=ScientificIngestionService()
        first=self.prepared(fixture,service,idem="same-request"); second=self.prepared(fixture,service,idem="same-request")
        self.assertEqual(first.run_key,second.run_key); parser=CountingParser()
        executor=ScientificIngestionExecutor(parser,self.resolver(substances),service); result=executor.execute(first); retry=executor.execute(first)
        self.assertEqual(parser.calls,1); self.assertTrue(retry.reused_terminal_run)
        self.assertEqual((result.records_seen,result.records_accepted,result.records_rejected,result.assessments_written,result.findings_written),(2,2,0,2,3))
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT j.release_artifact_id,j.manifest_position FROM scientific_ingestion_run_artifacts j WHERE j.ingestion_run_id=%s ORDER BY j.manifest_position",(first.id,)); self.assertEqual(cur.fetchall(),[(artifacts["artifact_a"],0),(artifacts["artifact_c"],1)])
                cur.execute("SELECT count(DISTINCT src.id),count(DISTINCT ra.id),count(DISTINCT a.id),count(DISTINCT f.id),count(DISTINCT s.id),count(DISTINCT si.id),bool_and(a.normalized_checksum_algorithm='sha256'),bool_and(f.fingerprint_algorithm='sha256'),max(r.parser_output_checksum_algorithm) FROM sources src JOIN source_datasets d ON d.source_id=src.id JOIN source_dataset_releases rel ON rel.dataset_id=d.id JOIN scientific_ingestion_runs r ON r.release_id=rel.id JOIN scientific_ingestion_run_artifacts j ON j.ingestion_run_id=r.id JOIN scientific_release_artifacts ra ON ra.id=j.release_artifact_id JOIN scientific_assessments a ON a.ingestion_run_id=r.id JOIN scientific_assessment_findings f ON f.assessment_id=a.id JOIN substances s ON s.id=a.substance_id JOIN substance_identifiers si ON si.substance_id=s.id WHERE r.id=%s",(first.id,)); self.assertEqual(cur.fetchone(),(1,2,2,3,2,2,True,True,"sha256"))
                cur.execute("SELECT max(src.source_key) FROM substances s JOIN substance_identifiers si ON si.substance_id=s.id JOIN scientific_assessments a ON a.substance_id=s.id JOIN scientific_assessment_findings f ON f.assessment_id=a.id JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id JOIN scientific_ingestion_run_artifacts j ON j.ingestion_run_id=r.id JOIN scientific_release_artifacts ra ON ra.id=j.release_artifact_id JOIN source_dataset_releases rel ON rel.id=r.release_id JOIN source_datasets d ON d.id=rel.dataset_id JOIN sources src ON src.id=d.source_id WHERE r.id=%s",(first.id,)); self.assertEqual(cur.fetchone()[0],source_key)
        finally: conn.close()

    def test_resolution_outcomes_and_parser_rejection(self):
        fixture=self.fixture(); _,_,substances,_,_,_=fixture; service=ScientificIngestionService(); prepared=self.prepared(fixture,service)
        base=FakeScientificArtifactParser().parse(prepared.manifest); template=base.records[1]
        def clone(key):
            assessment=template.assessment.model_copy(update={"source_record_key":key,"external_assessment_id":key})
            findings=tuple(f.model_copy(update={"source_record_key":f"{key}_finding"}) for f in template.findings)
            return template.model_copy(update={"source_record_key":key,"assessment":assessment,"findings":findings,"raw_record":{"key":key}})
        records=(base.records[0],clone("record_unresolved"),clone("record_ambiguous"),clone("record_rejected"))
        result4=ScientificParserResult(records=records,parser_version=base.parser_version,normalization_schema_version=base.normalization_schema_version)
        resolver=FakeScientificSubstanceResolver({"test_record_a":substances[0]}, {"record_unresolved":"unresolved","record_ambiguous":"ambiguous","record_rejected":"rejected"})
        outcome=ScientificIngestionExecutor(CountingParser(result4),resolver,service).execute(prepared)
        self.assertEqual((outcome.records_seen,outcome.records_accepted,outcome.records_rejected),(4,1,3))
        fixture2=self.fixture(); _,_,substances2,_,_,_=fixture2; prepared2=self.prepared(fixture2,service)
        parser_rejected=ScientificRecordRejection(source_record_key="parser_bad",error_code="invalid_test_record",error_summary="synthetic rejection",raw_record={"bad":True})
        with_rejection=result4.model_copy(update={"records":(base.records[0],),"rejected_records":(parser_rejected,),"warnings":(ScientificParserWarning(code="test_warning",message="synthetic warning"),)})
        rejected=ScientificIngestionExecutor(CountingParser(with_rejection),self.resolver(substances2),service).execute(prepared2)
        self.assertEqual((rejected.records_seen,rejected.records_accepted,rejected.records_rejected,rejected.warnings_count),(2,1,1,1)); self.assertEqual(rejected.rejected_resolutions[0].reason_code,"invalid_test_record")

    def test_resolver_fatal_is_not_unresolved(self):
        fixture=self.fixture(); service=ScientificIngestionService(); prepared=self.prepared(fixture,service)
        with self.assertRaises(RuntimeError): ScientificIngestionExecutor(FakeScientificArtifactParser(),FailingResolver(),service).execute(prepared)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT run_status,error_code FROM scientific_ingestion_runs WHERE id=%s",(prepared.id,)); self.assertEqual(cur.fetchone(),("failed","scientific_execution_failed"))
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],0)
        finally: conn.close()

    def test_retry_after_partial_running_run_converges(self):
        fixture=self.fixture(); release_id,_,substances,_,_,_=fixture; service=ScientificIngestionService(); prepared=self.prepared(fixture,service); service.mark_running(prepared.id)
        parsed=FakeScientificArtifactParser().parse(prepared.manifest); resolver=self.resolver(substances); first=resolver.resolve(parsed.records[0]).record; repository=PostgresScientificPersistenceRepository()
        conn=get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur: repository.persist_record(cur,prepared.id,release_id,first)
            conn.commit()
        finally: conn.close()
        result=ScientificIngestionExecutor(FakeScientificArtifactParser(),resolver,service).execute(prepared)
        self.assertEqual((result.assessments_written,result.findings_written),(2,3))
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],2)
                cur.execute("SELECT count(*) FROM scientific_assessment_findings WHERE assessment_id IN (SELECT id FROM scientific_assessments WHERE ingestion_run_id=%s)",(prepared.id,)); self.assertEqual(cur.fetchone()[0],3)
        finally: conn.close()

    def test_reprocessing_and_different_artifact_preserve_separate_runs(self):
        fixture1=self.fixture("fake-parser-1"); release_id,_,substances,release,config1,_=fixture1; service=ScientificIngestionService()
        run1=service.prepare_ingestion_run(release,config1,("artifact_a","artifact_c"),"same"); ScientificIngestionExecutor(CountingParser(),self.resolver(substances),service).execute(run1)
        metadata2=config1.adapter.model_copy(update={"parser_version":"fake-parser-2"}); config2=config1.model_copy(update={"adapter":metadata2})
        run2=service.prepare_ingestion_run(release,config2,("artifact_a","artifact_c"),"same"); ScientificIngestionExecutor(CountingParser(version="fake-parser-2"),self.resolver(substances),service).execute(run2)
        run3=service.prepare_ingestion_run(release,config1,("artifact_b",),"same")
        self.assertEqual(len({run1.run_key,run2.run_key,run3.run_key}),3); self.assertNotEqual(run1.manifest.fingerprint,run3.manifest.fingerprint)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*),count(DISTINCT ingestion_run_id) FROM scientific_assessments WHERE ingestion_run_id IN (%s,%s)",(run1.id,run2.id)); self.assertEqual(cur.fetchone(),(4,2))
        finally: conn.close()


if __name__ == "__main__": unittest.main()
