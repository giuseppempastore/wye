import os
import unittest
import uuid

from app.db import get_connection
from app.repositories.substance_registry import SubstanceIdentifierLookup
from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata, ScientificIngestionConfiguration, ScientificParserResult,
    ScientificReleaseIdentity, SubstanceIdentifierInput,
)
from app.scientific_ingestion.fake import FakeScientificArtifactParser
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import ScientificIngestionService
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver


class _CursorContext:
    def __enter__(self): return object()
    def __exit__(self,*args): return False


class _Connection:
    def set_session(self,**kwargs): self.readonly=kwargs.get("readonly")
    def cursor(self,**kwargs): return _CursorContext()
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


class _Repository:
    def __init__(self, rows): self.rows=rows; self.received=None
    def lookup_identifiers(self,cursor,identifiers): self.received=identifiers; return self.rows


def identifier(key="ns",version="1",value="x"):
    return SubstanceIdentifierInput(namespace_key=key,namespace_version=version,
        raw_value=value,normalized_value=value)


def record_with(*identifiers):
    record=FakeScientificArtifactParser().parse(type("Manifest",(),{"fingerprint":"a"*64})()).records[0]
    return record.model_copy(update={"substance_identifiers":tuple(identifiers)})


def lookup(value="x",namespace_id=1,identifier_id=10,identifier_status="verified",
           substance_id=100,substance_status="active",key="ns",version="1"):
    return SubstanceIdentifierLookup(key,version,value,namespace_id,identifier_id,
        identifier_status,substance_id,substance_status)


class ScientificSubstanceResolutionUnitTests(unittest.TestCase):
    def resolve(self,rows,*identifiers):
        repo=_Repository(tuple(rows)); connection=_Connection()
        result=PostgresScientificSubstanceResolver(repo,lambda:connection).resolve(record_with(*identifiers))
        self.assertTrue(connection.readonly); return result,repo

    def test_one_and_multiple_identifiers_resolve_same_active_substance(self):
        one,_=self.resolve([lookup()],identifier())
        self.assertEqual((one.status,one.record.substance_id,one.reason_code),("resolved",100,"verified_match"))
        multiple,_=self.resolve([lookup("x"),lookup("y",identifier_id=11)],identifier(value="x"),identifier(value="y"))
        self.assertEqual(multiple.record.substance_id,100); self.assertEqual(len(multiple.diagnostics),2)

    def test_partial_match_and_repeated_identifier_are_deterministic(self):
        partial,_=self.resolve([lookup("x"),lookup("missing",identifier_id=None,identifier_status=None,substance_id=None,substance_status=None)],identifier(value="x"),identifier(value="missing"))
        self.assertEqual(partial.status,"resolved"); self.assertEqual([d.outcome for d in partial.diagnostics],["matched","unmatched"])
        repeated,repo=self.resolve([lookup("x")],identifier(value="x"),identifier(value="x"))
        self.assertEqual(repeated.status,"resolved"); self.assertEqual(len(repo.received),1)

    def test_conflict_zero_match_and_unknown_namespace(self):
        conflict,_=self.resolve([lookup("x",substance_id=100),lookup("y",identifier_id=11,substance_id=200)],identifier(value="x"),identifier(value="y"))
        self.assertEqual(conflict.status,"ambiguous"); self.assertEqual(conflict.conflicting_substance_ids,(100,200))
        zero,_=self.resolve([lookup("x",identifier_id=None,identifier_status=None,substance_id=None,substance_status=None)],identifier())
        self.assertEqual((zero.status,zero.reason_code),("unresolved","no_verified_identifier_match"))
        unknown,_=self.resolve([lookup("x",namespace_id=None,identifier_id=None,identifier_status=None,substance_id=None,substance_status=None)],identifier())
        self.assertEqual((unknown.status,unknown.reason_code),("unresolved","unknown_namespace"))

    def test_nonverified_identifier_statuses_never_resolve(self):
        for status in ("pending_review","rejected","deprecated"):
            with self.subTest(status=status):
                result,_=self.resolve([lookup(identifier_status=status)],identifier())
                self.assertEqual(result.status,"unresolved"); self.assertEqual(result.diagnostics[0].outcome,"ignored_identifier_status")

    def test_inactive_substances_do_not_auto_resolve(self):
        pending,_=self.resolve([lookup(substance_status="review_pending")],identifier())
        self.assertEqual((pending.status,pending.reason_code),("ambiguous","inactive_substance"))
        deprecated,_=self.resolve([lookup(substance_status="deprecated")],identifier())
        self.assertEqual((deprecated.status,deprecated.reason_code),("rejected","deprecated_substance"))


class _StaticParser:
    def __init__(self,result): self.result=result
    def parse(self,manifest): return self.result


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"),"requires isolated PostgreSQL at 0013")
class ScientificSubstanceResolutionPostgresTests(unittest.TestCase):
    def fixture(self,statuses=("verified","verified"),substance_statuses=("active","active")):
        suffix=uuid.uuid4().hex; namespace_key=f"registry_ns_{suffix}"
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id",(f"registry_source_{suffix}",suffix)); source_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,%s,%s) RETURNING id",(source_id,suffix,f"registry_dataset_{suffix}")); dataset_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,%s) RETURNING id",(dataset_id,f"registry_release_{suffix}",suffix)); release_id=cur.fetchone()[0]
                checksum="a"*64; cur.execute("INSERT INTO storage_objects(storage_provider,bucket,object_key,byte_size,checksum_algorithm,checksum_value) VALUES('test','scientific',%s,128,'sha256',%s) RETURNING id",(f"registry/{suffix}",checksum)); storage_id=cur.fetchone()[0]
                cur.execute("INSERT INTO scientific_release_artifacts(release_id,storage_object_id,artifact_key,artifact_role,raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at) VALUES(%s,%s,'primary','primary','sha256',%s,128,NOW())",(release_id,storage_id,checksum))
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Registry test','registry_v1') RETURNING id",(namespace_key,)); namespace_id=cur.fetchone()[0]
                substance_ids=[]; identifier_ids=[]
                for index,(identifier_status,substance_status) in enumerate(zip(statuses,substance_statuses)):
                    cur.execute("INSERT INTO substances(preferred_name,normalized_name,status) VALUES(%s,%s,%s) RETURNING id",(f"Registry {index}",f"registry_{index}_{suffix}",substance_status)); substance_id=cur.fetchone()[0]; substance_ids.append(substance_id)
                    cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",(substance_id,namespace_id,"misleading_legacy_system",f"RAW-{index}",f"test-{index}",identifier_status)); identifier_ids.append(cur.fetchone()[0])
            conn.commit()
        finally: conn.close()
        metadata=ScientificAdapterMetadata(source_key=f"registry_source_{suffix}",dataset_key=f"registry_dataset_{suffix}",adapter_version="fake-adapter-1",acquisition_version="fake-acquisition-1",parser_version="fake-parser-1",normalization_schema_version="fake-normalization-1")
        release=ScientificReleaseIdentity(source_key=metadata.source_key,dataset_key=metadata.dataset_key,external_release_key=f"registry_release_{suffix}")
        service=ScientificIngestionService(); prepared=service.prepare_ingestion_run(release,ScientificIngestionConfiguration(adapter=metadata),("primary",),f"registry-{suffix}")
        base=FakeScientificArtifactParser().parse(prepared.manifest)
        records=[]
        for index,record in enumerate(base.records):
            records.append(record.model_copy(update={"substance_identifiers":(identifier(namespace_key,"1",f"test-{index}"),)}))
        result=base.model_copy(update={"records":tuple(records)})
        return prepared,service,result,tuple(substance_ids),tuple(identifier_ids),namespace_key

    def registry_counts(self):
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT (SELECT count(*) FROM substances),(SELECT count(*) FROM substance_identifiers),(SELECT count(*) FROM substance_identifier_namespaces)"); return cur.fetchone()
        finally: conn.close()

    def test_real_namespace_verified_lookup_executor_and_registry_immutability(self):
        prepared,service,result,substances,identifier_ids,namespace_key=self.fixture(); before=self.registry_counts(); resolver=PostgresScientificSubstanceResolver()
        direct=resolver.resolve(result.records[0]); self.assertEqual(direct.record.substance_id,substances[0]); self.assertEqual(direct.diagnostics[0].identifier_id,identifier_ids[0]); self.assertEqual(direct.diagnostics[0].namespace_key,namespace_key)
        executed=ScientificIngestionExecutor(_StaticParser(result),resolver,service).execute(prepared)
        self.assertEqual((executed.records_accepted,executed.assessments_written,executed.findings_written),(2,2,3)); self.assertEqual(self.registry_counts(),before)

    def test_unresolved_pending_deprecated_and_inactive_are_not_materialized(self):
        for identifier_status,substance_status,expected in [
            ("pending_review","active","unresolved"),("deprecated","active","unresolved"),
            ("verified","review_pending","ambiguous"),("verified","deprecated","rejected")]:
            with self.subTest(identifier_status=identifier_status,substance_status=substance_status):
                prepared,service,result,_,_,_=self.fixture((identifier_status,"verified"),(substance_status,"active")); one=result.model_copy(update={"records":(result.records[0],)})
                executed=ScientificIngestionExecutor(_StaticParser(one),PostgresScientificSubstanceResolver(),service).execute(prepared)
                self.assertEqual((executed.records_accepted,executed.records_rejected),(0,1)); self.assertEqual(executed.rejected_resolutions[0].reason_code,{"unresolved":"no_verified_identifier_match","ambiguous":"inactive_substance","rejected":"deprecated_substance"}[expected])

    def test_ambiguous_and_same_substance_multi_identifier(self):
        prepared,service,result,substances,_,namespace_key=self.fixture(); first=result.records[0]
        conflict=first.model_copy(update={"substance_identifiers":(identifier(namespace_key,"1","test-0"),identifier(namespace_key,"1","test-1"))})
        ambiguous=PostgresScientificSubstanceResolver().resolve(conflict); self.assertEqual(ambiguous.status,"ambiguous")
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Second test','v1') RETURNING id",(f"second_{namespace_key}",)); second_ns=cur.fetchone()[0]
                cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,'wrong','RAW-X','same-a','verified')",(substances[0],second_ns))
            conn.commit()
        finally: conn.close()
        agreement=first.model_copy(update={"substance_identifiers":(identifier(namespace_key,"1","test-0"),identifier(f"second_{namespace_key}","1","same-a"))})
        resolved=PostgresScientificSubstanceResolver().resolve(agreement); self.assertEqual(resolved.record.substance_id,substances[0]); self.assertEqual(len(resolved.diagnostics),2)


    def test_unknown_ambiguous_and_same_substance_agreement_execute_end_to_end(self):
        prepared,service,result,substances,_,namespace_key=self.fixture()
        unknown=result.records[0].model_copy(update={"substance_identifiers":(identifier(namespace_key,"1","test-unknown"),)})
        unknown_result=result.model_copy(update={"records":(unknown,)})
        executed=ScientificIngestionExecutor(_StaticParser(unknown_result),PostgresScientificSubstanceResolver(),service).execute(prepared)
        self.assertEqual((executed.records_accepted,executed.records_rejected),(0,1))
        self.assertEqual(executed.rejected_resolutions[0].reason_code,"no_verified_identifier_match")

        prepared2,service2,result2,_,_,namespace_key2=self.fixture()
        conflict=result2.records[0].model_copy(update={"substance_identifiers":(
            identifier(namespace_key2,"1","test-0"),identifier(namespace_key2,"1","test-1"))})
        ambiguous_result=result2.model_copy(update={"records":(conflict,)})
        ambiguous=ScientificIngestionExecutor(_StaticParser(ambiguous_result),PostgresScientificSubstanceResolver(),service2).execute(prepared2)
        self.assertEqual((ambiguous.records_accepted,ambiguous.records_rejected),(0,1))
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM scientific_assessments WHERE ingestion_run_id=%s",(prepared2.id,)); self.assertEqual(cur.fetchone()[0],0)
        finally: conn.close()

        prepared3,service3,result3,substances3,_,namespace_key3=self.fixture()
        second_key=f"second_{namespace_key3}"
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Second E2E','v1') RETURNING id",(second_key,)); second_ns=cur.fetchone()[0]
                cur.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,verification_status) VALUES(%s,%s,'wrong','RAW-X','same-a','verified')",(substances3[0],second_ns))
            conn.commit()
        finally: conn.close()
        agreement=result3.records[0].model_copy(update={"substance_identifiers":(
            identifier(namespace_key3,"1","test-0"),identifier(second_key,"1","same-a"))})
        agreement_result=result3.model_copy(update={"records":(agreement,)})
        agreed=ScientificIngestionExecutor(_StaticParser(agreement_result),PostgresScientificSubstanceResolver(),service3).execute(prepared3)
        self.assertEqual((agreed.records_accepted,agreed.assessments_written),(1,1))
if __name__ == "__main__": unittest.main()
