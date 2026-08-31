import os
import subprocess
import sys
import threading
import unittest
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import psycopg2

from app.db import get_connection
from app.services.ingredient_substance_mapping import (
    IngredientSubstanceMappingError,
    IngredientSubstanceMappingService,
)


def utc_today():
    return datetime.now(timezone.utc).date()


def seed_pair(active=True):
    connection=get_connection()
    try:
        with connection.cursor() as cursor:
            token=uuid.uuid4().hex
            cursor.execute("INSERT INTO ingredients(canonical_name) VALUES(%s) RETURNING id",(f"Mapping ingredient {token}",)); ingredient_id=cursor.fetchone()[0]
            cursor.execute("INSERT INTO substances(preferred_name,normalized_name,status) VALUES(%s,%s,%s) RETURNING id",(f"Mapping substance {token}",f"mapping substance {token}","active" if active else "review_pending")); substance_id=cursor.fetchone()[0]
        connection.commit(); return ingredient_id,substance_id
    finally: connection.close()


def seed_context():
    connection=get_connection()
    try:
        with connection.cursor() as cursor:
            token=uuid.uuid4().hex
            cursor.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id",(f"map_source_{token}",f"Map source {token}")); source_id=cursor.fetchone()[0]
            cursor.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,'Map dataset',%s) RETURNING id",(source_id,f"map_dataset_{token}")); dataset_id=cursor.fetchone()[0]
            releases=[]
            for suffix in ("a","b"):
                cursor.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,%s) RETURNING id",(dataset_id,f"map_release_{token}_{suffix}",suffix)); releases.append(cursor.fetchone()[0])
            cursor.execute("""INSERT INTO scientific_ingestion_runs(release_id,run_key,importer_name,importer_version,source_adapter_version,acquisition_version,parser_version,normalization_schema_version,artifact_manifest_algorithm,artifact_manifest_fingerprint) VALUES(%s,%s,'test','1','1','1','1','1','sha256',%s) RETURNING id""",(releases[0],str(uuid.uuid4()),"a"*64)); run_id=cursor.fetchone()[0]
        connection.commit(); return source_id,releases[0],releases[1],run_id
    finally: connection.close()


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0017")
class IngredientSubstanceMappingHistoryTests(unittest.TestCase):
    def setUp(self): self.service=IngredientSubstanceMappingService()

    def proposal(self, ingredient, substance, **changes):
        data=dict(proposal_key=uuid.uuid4(),ingredient_id=ingredient,substance_id=substance,
                  relationship_type="represents",mapping_method="manual_review",proposed_by="proposer:test")
        data.update(changes); return self.service.propose_mapping(**data)

    def test_manual_accept_retry_and_current_query(self):
        ingredient,substance=seed_pair(); proposal=self.proposal(ingredient,substance)
        result=self.service.review_proposal(proposal["id"],"accept","reviewer:test","verified",effective_from=date(2025,1,1),materialized_by="worker:test")
        retry=self.service.review_proposal(proposal["id"],"accept","reviewer:test","verified",effective_from=date(2025,1,1),materialized_by="worker:test")
        self.assertEqual(result["materialization"]["ingredient_substance_id"],retry["materialization"]["ingredient_substance_id"])
        current=self.service.current_mappings(ingredient,date(2025,1,2)); self.assertEqual(len(current),1)
        self.assertEqual((current[0]["mapping_status"],current[0]["reviewed_by"],current[0]["valid_from"]),("accepted","reviewer:test",date(2025,1,1)))

    def test_reject_and_inactive_target_do_not_materialize(self):
        ingredient,substance=seed_pair(); proposal=self.proposal(ingredient,substance)
        result=self.service.review_proposal(proposal["id"],"reject","reviewer:test","not equivalent")
        self.assertIsNone(result["materialization"]); self.assertEqual(self.service.current_mappings(ingredient),())
        ingredient,inactive=seed_pair(active=False); proposal=self.proposal(ingredient,inactive)
        with self.assertRaisesRegex(IngredientSubstanceMappingError,"active substance"):
            self.service.review_proposal(proposal["id"],"accept","reviewer:test","approve",effective_from=utc_today(),materialized_by="worker")

    def test_release_run_coherence_is_enforced(self):
        ingredient,substance=seed_pair(); _,release_a,release_b,run_id=seed_context()
        with self.assertRaisesRegex(IngredientSubstanceMappingError,"another release"):
            self.proposal(ingredient,substance,mapping_method="dataset",release_id=release_b,run_id=run_id)
        proposal=self.proposal(ingredient,substance,mapping_method="dataset",release_id=release_a,run_id=run_id)
        accepted=self.service.review_proposal(proposal["id"],"accept","reviewer","source verified",effective_from=utc_today(),materialized_by="worker")
        self.assertIsNotNone(accepted["materialization"])

    def test_close_then_historical_reacceptance(self):
        ingredient,substance=seed_pair(); first=self.proposal(ingredient,substance)
        first_result=self.service.review_proposal(first["id"],"accept","r","first",effective_from=date(2024,1,1),materialized_by="m")
        self.service.close_mapping(first_result["materialization"]["ingredient_substance_id"],date(2024,12,31),"r","superseded")
        overlapping=self.proposal(ingredient,substance)
        with self.assertRaisesRegex(IngredientSubstanceMappingError,"overlaps"):
            self.service.review_proposal(overlapping["id"],"accept","r","overlap",effective_from=date(2024,12,31),materialized_by="m")
        second=self.proposal(ingredient,substance)
        second_result=self.service.review_proposal(second["id"],"accept","r","reaccepted",effective_from=date(2025,1,1),materialized_by="m")
        self.assertNotEqual(first_result["materialization"]["ingredient_substance_id"],second_result["materialization"]["ingredient_substance_id"])
        self.assertEqual(len(self.service.history(ingredient)),2); self.assertEqual(len(self.service.current_mappings(ingredient,date(2025,1,2))),1)

    def test_n_to_m_and_relationship_multiplicity(self):
        ingredient,x=seed_pair(); other_ingredient,y=seed_pair()
        for ing,sub,relationship in ((ingredient,x,"represents"),(ingredient,y,"contains"),(other_ingredient,x,"contains"),(ingredient,x,"equivalent_to")):
            proposal=self.proposal(ing,sub,relationship_type=relationship)
            self.service.review_proposal(proposal["id"],"accept","r","approved",effective_from=utc_today(),materialized_by="m")
        self.assertEqual(len(self.service.current_mappings(ingredient)),3)

    def test_proposal_key_idempotency_and_conflict(self):
        ingredient,substance=seed_pair(); key=uuid.uuid4()
        first=self.proposal(ingredient,substance,proposal_key=key); second=self.proposal(ingredient,substance,proposal_key=key)
        self.assertEqual(first["id"],second["id"])
        other,_=seed_pair()
        with self.assertRaisesRegex(IngredientSubstanceMappingError,"different content"):
            self.proposal(other,substance,proposal_key=key)

    def test_concurrent_acceptance_converges_on_one_current_row(self):
        ingredient,substance=seed_pair(); proposals=[self.proposal(ingredient,substance) for _ in range(2)]
        barrier=threading.Barrier(2); results=[]; errors=[]
        def worker(proposal):
            try:
                barrier.wait(); results.append(IngredientSubstanceMappingService().review_proposal(proposal["id"],"accept","r","approved",effective_from=utc_today(),materialized_by="m"))
            except Exception as exc: errors.append(exc)
        threads=[threading.Thread(target=worker,args=(proposal,)) for proposal in proposals]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertFalse(errors,errors); self.assertEqual(len({r["materialization"]["ingredient_substance_id"] for r in results}),1)
        self.assertEqual(len(self.service.current_mappings(ingredient)),1)

    def test_concurrent_terminal_reviews_one_wins(self):
        ingredient,substance=seed_pair(); proposal=self.proposal(ingredient,substance); barrier=threading.Barrier(2); outcomes=[]
        def worker(decision):
            try:
                barrier.wait(); kwargs={"effective_from":utc_today(),"materialized_by":"m"} if decision=="accept" else {}
                IngredientSubstanceMappingService().review_proposal(proposal["id"],decision,"r",decision,**kwargs); outcomes.append("ok")
            except IngredientSubstanceMappingError: outcomes.append("conflict")
        threads=[threading.Thread(target=worker,args=(decision,)) for decision in ("accept","reject")]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(sorted(outcomes),["conflict","ok"])
    def test_full_bridge_traverses_ingredient_to_scientific_source(self):
        IngredientSubstanceMappingLifecycleTests._assert_full_bridge(self)



@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS")=="1", "requires lifecycle PostgreSQL")
class IngredientSubstanceMappingLifecycleTests(unittest.TestCase):
    backend=Path(__file__).resolve().parents[1]
    def alembic(self,*args,success=True):
        result=subprocess.run([sys.executable,"-m","alembic",*args],cwd=self.backend,text=True,capture_output=True)
        self.assertEqual(result.returncode==0,success,result.stdout+result.stderr); return result
    def _assert_full_bridge(self):
        ingredient,substance=seed_pair(); source_id,release_id,_,run_id=seed_context()
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                token=uuid.uuid4().hex
                cursor.execute("INSERT INTO substance_identifier_namespaces(namespace_key,namespace_version,display_name,normalization_rule_version) VALUES(%s,'1','Mapping test','v1') RETURNING id",(f"mapping_test_{token}",)); namespace_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO substance_identifiers(substance_id,namespace_id,identifier_system,identifier_value,normalized_value,is_primary,verification_status) VALUES(%s,%s,'compat','TEST-X','TEST-X',true,'verified') RETURNING id",(substance,namespace_id)); identifier_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO scientific_assessments(substance_id,source_dataset_release_id,ingestion_run_id,source_record_key,assessment_type,assessment_version,assessment_status,conclusion_text) VALUES(%s,%s,%s,%s,'test','v1','published','Test evidence') RETURNING id",(substance,release_id,run_id,f"record-{token}")); assessment_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO scientific_assessment_findings(assessment_id,source_record_key,conclusion_text) VALUES(%s,%s,'Test finding') RETURNING id",(assessment_id,f"finding-{token}")); finding_id=cursor.fetchone()[0]
            connection.commit()
        finally: connection.close()
        proposal=self.proposal(ingredient,substance,mapping_method="dataset",release_id=release_id,run_id=run_id)
        self.service.review_proposal(proposal["id"],"accept","reviewer","verified bridge",effective_from=utc_today(),materialized_by="worker")
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                  SELECT s.id,si.id,a.id,f.id,r.id,src.id
                  FROM ingredient_substances bridge
                  JOIN substances s ON s.id=bridge.substance_id
                  JOIN substance_identifiers si ON si.substance_id=s.id AND si.verification_status='verified'
                  JOIN scientific_assessments a ON a.substance_id=s.id
                  JOIN scientific_assessment_findings f ON f.assessment_id=a.id
                  JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id
                  JOIN source_dataset_releases rel ON rel.id=r.release_id
                  JOIN source_datasets ds ON ds.id=rel.dataset_id
                  JOIN sources src ON src.id=ds.source_id
                  WHERE bridge.ingredient_id=%s AND bridge.mapping_status='accepted'
                    AND bridge.valid_from<=CURRENT_DATE AND (bridge.valid_to IS NULL OR bridge.valid_to>=CURRENT_DATE)
                """,(ingredient,)); row=cursor.fetchone()
            self.assertEqual(row,(substance,identifier_id,assessment_id,finding_id,run_id,source_id))
        finally: connection.close()


    def test_safe_and_unsafe_lifecycle(self):
        self.alembic("downgrade","0016_substance_creation"); self.alembic("upgrade","0017_ingredient_mapping_history")
        self.alembic("downgrade","0016_substance_creation"); self.alembic("upgrade","0017_ingredient_mapping_history")
        ingredient,substance=seed_pair(); proposal=IngredientSubstanceMappingService().propose_mapping(proposal_key=uuid.uuid4(),ingredient_id=ingredient,substance_id=substance,relationship_type="represents",mapping_method="manual_review",proposed_by="test")
        failed=self.alembic("downgrade","0016_substance_creation",success=False); self.assertIn("not representable",failed.stdout+failed.stderr)
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cursor.fetchone()[0],"0017_ingredient_mapping_history")
                cursor.execute("SELECT count(*) FROM ingredient_substance_mapping_proposals WHERE id=%s",(proposal["id"],)); self.assertEqual(cursor.fetchone()[0],1)
        finally: connection.close()


if __name__=="__main__": unittest.main()
