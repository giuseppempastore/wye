import os
import subprocess
import sys
import threading
import unittest
import uuid
from pathlib import Path

from app.db import get_connection
from app.scientific_ingestion.contracts import ScientificRecordRejection
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver
from app.services.substance_resolution_reviews import SubstanceResolutionReviewError,SubstanceResolutionReviewService
import tests.test_scientific_substance_resolution as registry_fixtures


class _StaticParser:
    def __init__(self,result): self.result=result
    def parse(self,manifest): return self.result


class _FailingReviewService:
    def record_resolution(self,*args,**kwargs): raise RuntimeError("synthetic candidate persistence failure")


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"),"requires isolated PostgreSQL at 0014")
class SubstanceResolutionReviewWorkflowTests(unittest.TestCase):
    def fixture(self):
        helper=registry_fixtures.ScientificSubstanceResolutionPostgresTests("test_real_namespace_verified_lookup_executor_and_registry_immutability")
        return helper.fixture()

    @staticmethod
    def unknown(record,namespace_key,value="test-unknown"):
        item=record.substance_identifiers[0].model_copy(update={"namespace_key":namespace_key,"normalized_value":value,"raw_value":value})
        return record.model_copy(update={"substance_identifiers":(item,)})

    def capture_unknown(self,prepared,result,namespace_key,review_service=None):
        record=self.unknown(result.records[0],namespace_key); resolution=PostgresScientificSubstanceResolver().resolve(record)
        service=review_service or SubstanceResolutionReviewService(); persisted=service.record_resolution(prepared.id,record,resolution,{"test":True})
        return record,resolution,persisted[0]

    def registry_counts(self):
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT (SELECT count(*) FROM substances),(SELECT count(*) FROM substance_identifiers),(SELECT count(*) FROM substance_identifier_namespaces)"); return cur.fetchone()
        finally: conn.close()

    def test_unknown_candidate_occurrence_idempotency_and_query_path(self):
        prepared,_,result,_,_,namespace_key=self.fixture(); before=self.registry_counts(); record,resolution,persisted=self.capture_unknown(prepared,result,namespace_key)
        repeated=SubstanceResolutionReviewService().record_resolution(prepared.id,record,resolution)[0]
        self.assertEqual(persisted["candidate_id"],repeated["candidate_id"]); self.assertFalse(repeated["occurrence_created"])
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT c.candidate_status,c.candidate_kind,o.source_record_key,s.source_key FROM substance_resolution_candidates c JOIN substance_resolution_candidate_occurrences o ON o.candidate_id=c.id JOIN scientific_ingestion_runs r ON r.id=o.ingestion_run_id JOIN source_dataset_releases rel ON rel.id=r.release_id JOIN source_datasets d ON d.id=rel.dataset_id JOIN sources s ON s.id=d.source_id WHERE c.id=%s",(persisted["candidate_id"],)); status,kind,key,source=cur.fetchone(); self.assertEqual((status,kind,key),("pending_review","unknown_identifier",record.source_record_key)); self.assertTrue(source.startswith("registry_source_"))
                cur.execute("SELECT count(*) FROM substance_resolution_candidate_occurrences WHERE candidate_id=%s",(persisted["candidate_id"],)); self.assertEqual(cur.fetchone()[0],1)
        finally: conn.close()
        self.assertEqual(self.registry_counts(),before)

    def test_repeated_unknown_across_runs_one_candidate_two_occurrences(self):
        first=self.fixture(); second=self.fixture(); service=SubstanceResolutionReviewService()
        _,_,one=self.capture_unknown(first[0],first[2],"shared_unknown_namespace",service)
        _,_,two=self.capture_unknown(second[0],second[2],"shared_unknown_namespace",service)
        self.assertEqual(one["candidate_id"],two["candidate_id"])
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT count(*) FROM substance_resolution_candidate_occurrences WHERE candidate_id=%s",(one["candidate_id"],)); self.assertEqual(cur.fetchone()[0],2)
        finally: conn.close()

    def test_ambiguous_conflict_is_grouped_and_diagnostic(self):
        prepared,_,result,_,_,namespace_key=self.fixture(); record=result.records[0].model_copy(update={"substance_identifiers":(result.records[0].substance_identifiers[0].model_copy(update={"normalized_value":"test-0"}),result.records[0].substance_identifiers[0].model_copy(update={"normalized_value":"test-1"}))})
        resolution=PostgresScientificSubstanceResolver().resolve(record); self.assertEqual(resolution.status,"ambiguous")
        persisted=SubstanceResolutionReviewService().record_resolution(prepared.id,record,resolution)[0]
        detail=SubstanceResolutionReviewService().get(persisted["candidate_id"]); self.assertEqual(detail["candidate"]["candidate_kind"],"identity_conflict")
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT diagnostics FROM substance_resolution_candidate_occurrences WHERE id=%s",(persisted["occurrence_id"],)); diagnostics=cur.fetchone()[0]; self.assertEqual({d["substance_id"] for d in diagnostics},{resolution.conflicting_substance_ids[0],resolution.conflicting_substance_ids[1]})
        finally: conn.close()

    def test_associate_reject_defer_reobservation_and_no_reviewer(self):
        prepared,_,result,substances,_,namespace_key=self.fixture(); service=SubstanceResolutionReviewService(); record,resolution,persisted=self.capture_unknown(prepared,result,namespace_key,service); candidate_id=persisted["candidate_id"]
        service.decide(candidate_id,"defer","reviewer@example","needs_more_data")
        decision=service.decide(candidate_id,"associate_existing","reviewer@example","confirmed_match",substances[0])
        detail=service.get(candidate_id); self.assertEqual(detail["candidate"]["candidate_status"],"resolved_existing"); self.assertEqual(len(detail["decisions"]),2); self.assertEqual(decision["target_substance_id"],substances[0])
        with self.assertRaises(SubstanceResolutionReviewError): service.decide(candidate_id,"reject","other@example","changed_mind")
        reobserved=service.record_resolution(prepared.id,record,resolution)[0]; self.assertEqual(reobserved["candidate_status"],"resolved_existing")
        second=self.fixture(); _,_,rejected=self.capture_unknown(second[0],second[2],"reject_namespace",service); service.decide(rejected["candidate_id"],"reject","reviewer@example","invalid_identity")
        self.assertEqual(service.get(rejected["candidate_id"])["candidate"]["candidate_status"],"rejected")
        with self.assertRaises(SubstanceResolutionReviewError): service.decide(rejected["candidate_id"],"reject","","missing")

    def test_concurrent_candidate_and_terminal_decision_conflicts(self):
        first=self.fixture(); second=self.fixture(); results=[]; errors=[]; barrier=threading.Barrier(2)
        def capture(fixture):
            try: barrier.wait(); results.append(self.capture_unknown(fixture[0],fixture[2],"concurrent_unknown")[2])
            except Exception as exc: errors.append(exc)
        threads=[threading.Thread(target=capture,args=(item,)) for item in (first,second)]; [t.start() for t in threads]; [t.join(20) for t in threads]
        self.assertFalse(errors); self.assertEqual(results[0]["candidate_id"],results[1]["candidate_id"])
        candidate_id=results[0]["candidate_id"]; barrier=threading.Barrier(2); wins=[]; conflicts=[]
        def decide(target):
            try: barrier.wait(); SubstanceResolutionReviewService().decide(candidate_id,"associate_existing",f"reviewer-{target}","race",target); wins.append(target)
            except SubstanceResolutionReviewError as exc: conflicts.append(exc.code)
        threads=[threading.Thread(target=decide,args=(first[3][0],)),threading.Thread(target=decide,args=(first[3][1],))]; [t.start() for t in threads]; [t.join(20) for t in threads]
        self.assertEqual((len(wins),len(conflicts)),(1,1)); self.assertEqual(conflicts[0],"candidate_already_terminal")

    def test_executor_resolved_plus_unknown_and_parser_rejected_not_candidate(self):
        prepared,ingestion_service,result,_,_,namespace_key=self.fixture(); unknown=self.unknown(result.records[1],namespace_key); mixed=result.model_copy(update={"records":(result.records[0],unknown)})
        review=SubstanceResolutionReviewService(); executed=ScientificIngestionExecutor(_StaticParser(mixed),PostgresScientificSubstanceResolver(),ingestion_service,resolution_review_service=review).execute(prepared)
        self.assertEqual((executed.records_seen,executed.records_accepted,executed.records_rejected,executed.assessments_written),(2,1,1,1))
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT count(*) FROM substance_resolution_candidate_occurrences WHERE ingestion_run_id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],1)
        finally: conn.close()
        second=self.fixture(); rejected=ScientificRecordRejection(source_record_key="parser_invalid",error_code="invalid_record",error_summary="synthetic")
        parser_only=second[2].model_copy(update={"records":(),"rejected_records":(rejected,)})
        ScientificIngestionExecutor(_StaticParser(parser_only),PostgresScientificSubstanceResolver(),second[1],resolution_review_service=review).execute(second[0])
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT count(*) FROM substance_resolution_candidate_occurrences WHERE ingestion_run_id=%s",(second[0].id,)); self.assertEqual(cur.fetchone()[0],0)
        finally: conn.close()

    def test_candidate_failure_fails_run_and_registry_is_unchanged(self):
        prepared,ingestion_service,result,_,_,namespace_key=self.fixture(); before=self.registry_counts(); unknown=self.unknown(result.records[0],namespace_key); parser=result.model_copy(update={"records":(unknown,)})
        with self.assertRaises(RuntimeError): ScientificIngestionExecutor(_StaticParser(parser),PostgresScientificSubstanceResolver(),ingestion_service,resolution_review_service=_FailingReviewService()).execute(prepared)
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT run_status FROM scientific_ingestion_runs WHERE id=%s",(prepared.id,)); self.assertEqual(cur.fetchone()[0],"failed")
        finally: conn.close()
        self.assertEqual(self.registry_counts(),before)


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS")=="1","requires isolated lifecycle database")
class SubstanceResolutionReviewLifecycleTests(unittest.TestCase):
    backend=Path(__file__).resolve().parents[1]
    def alembic(self,*args,success=True):
        result=subprocess.run([sys.executable,"-m","alembic",*args],cwd=self.backend,text=True,capture_output=True); self.assertEqual(result.returncode==0,success,result.stdout+result.stderr); return result
    def test_safe_and_unsafe_lifecycle(self):
        self.alembic("downgrade","0013_ingestion_run_artifacts"); self.alembic("upgrade","0014_substance_resolution_review"); self.alembic("downgrade","0013_ingestion_run_artifacts"); self.alembic("upgrade","0014_substance_resolution_review")
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("INSERT INTO substance_resolution_candidates(candidate_key,candidate_kind,namespace_key,namespace_version,normalized_value) VALUES(%s,'unknown_identifier','test','1','x') RETURNING id",("a"*64,)); candidate_id=cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        failure=self.alembic("downgrade","0013_ingestion_run_artifacts",success=False); self.assertIn("contains non-representable data",failure.stdout+failure.stderr)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cur.fetchone()[0],"0014_substance_resolution_review")
                cur.execute("SELECT count(*) FROM substance_resolution_candidates WHERE id=%s",(candidate_id,)); self.assertEqual(cur.fetchone()[0],1)
                cur.execute("DELETE FROM substance_resolution_candidates WHERE id=%s",(candidate_id,))
            conn.commit()
        finally: conn.close()


if __name__=="__main__": unittest.main()
