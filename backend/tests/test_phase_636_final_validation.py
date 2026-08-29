"""Integrated closure validation for the complete Phase 6.3 pipeline."""

import os
import subprocess
import sys
import unittest
import uuid
from datetime import date
from pathlib import Path

from app.db import get_connection
from app.repositories.ingredient_substance_mapping import PostgresIngredientSubstanceMappingRepository
from app.repositories.substance_registry_mutations import PostgresSubstanceRegistryMutationRepository
from app.services.ingredient_substance_mapping import IngredientSubstanceMappingError,IngredientSubstanceMappingService
from app.services.scientific_execution import ScientificIngestionExecutor
from app.services.scientific_ingestion import PreparedScientificIngestionRun
from app.services.scientific_substance_resolution import PostgresScientificSubstanceResolver
from app.services.substance_registry_materialization import SubstanceRegistryMaterializationService
from app.services.substance_resolution_reviews import SubstanceResolutionReviewService
import tests.test_scientific_substance_resolution as registry_fixtures


class _StaticParser:
    def __init__(self,result): self.result=result
    def parse(self,manifest): return self.result


class _FailingRegistryAuditRepository(PostgresSubstanceRegistryMutationRepository):
    def create_materialization(self,*args,**kwargs):
        raise RuntimeError("synthetic registry audit failure")


class _FailingMappingAuditRepository(PostgresIngredientSubstanceMappingRepository):
    def create_materialization(self,*args,**kwargs):
        raise RuntimeError("synthetic mapping audit failure")


def registry_fixture():
    helper=registry_fixtures.ScientificSubstanceResolutionPostgresTests(
        "test_real_namespace_verified_lookup_executor_and_registry_immutability")
    return helper.fixture()


def unknown(record,namespace_key,value):
    identifier=record.substance_identifiers[0].model_copy(update={
        "namespace_key":namespace_key,"normalized_value":value,"raw_value":value})
    return record.model_copy(update={"substance_identifiers":(identifier,)})


def new_run_from(prepared):
    connection=get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
              INSERT INTO scientific_ingestion_runs(
                release_id,run_key,idempotency_key,importer_name,importer_version,
                source_adapter_version,acquisition_version,parser_version,
                normalization_schema_version,artifact_manifest_algorithm,
                artifact_manifest_fingerprint,run_status)
              SELECT release_id,%s,%s,importer_name,importer_version,
                source_adapter_version,acquisition_version,parser_version,
                normalization_schema_version,artifact_manifest_algorithm,
                artifact_manifest_fingerprint,'pending'
              FROM scientific_ingestion_runs WHERE id=%s RETURNING id,run_key
            """,(str(uuid.uuid4()),f"phase636-{uuid.uuid4().hex}",prepared.id))
            run_id,run_key=cursor.fetchone()
            cursor.execute("INSERT INTO scientific_ingestion_run_artifacts(ingestion_run_id,release_artifact_id,manifest_position) SELECT %s,release_artifact_id,manifest_position FROM scientific_ingestion_run_artifacts WHERE ingestion_run_id=%s",(run_id,prepared.id))
        connection.commit()
    finally: connection.close()
    return PreparedScientificIngestionRun(run_id,run_key,"pending",prepared.manifest,False)


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"),"requires isolated PostgreSQL at 0017")
class Phase636FinalValidationTests(unittest.TestCase):
    def test_complete_learning_product_and_provenance_traversal(self):
        prepared,ingestion,result,substances,_,namespace_key=registry_fixture()
        value=f"phase636-{uuid.uuid4().hex}"
        record=unknown(result.records[0],namespace_key,value)
        resolver=PostgresScientificSubstanceResolver(); resolution=resolver.resolve(record)
        self.assertEqual(resolution.status,"unresolved")
        review=SubstanceResolutionReviewService()
        candidate=review.record_resolution(prepared.id,record,resolution,{"phase":"6.3.6"})[0]
        decision=review.decide(candidate["candidate_id"],"associate_existing","reviewer:636","verified_identity",substances[0])
        before_identifier_count=self._count("substance_identifiers")
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM substance_registry_materializations WHERE decision_id=%s",(decision["id"],)); self.assertEqual(cursor.fetchone()[0],0)
        finally:
            connection.close()
        materialization=SubstanceRegistryMaterializationService().materialize_decision(decision["id"],"materializer:636")
        retry=SubstanceRegistryMaterializationService().materialize_decision(decision["id"],"retry-worker")
        self.assertEqual(materialization["id"],retry["id"]); self.assertEqual(self._count("substance_identifiers"),before_identifier_count+1)
        future=new_run_from(prepared); parser_result=result.model_copy(update={"records":(record,)})
        executed=ScientificIngestionExecutor(_StaticParser(parser_result),resolver,ingestion,resolution_review_service=review).execute(future)
        self.assertEqual((executed.records_accepted,executed.assessments_written,executed.findings_written),(1,1,len(record.findings)))

        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                token=uuid.uuid4().hex
                cursor.execute("INSERT INTO ingredients(canonical_name) VALUES(%s) RETURNING id",(f"Phase 636 ingredient {token}",)); ingredient_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO products(barcode,product_name,category) VALUES(%s,'Phase 636 product','food') RETURNING id",(f"phase636-{token}",)); product_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO product_label_documents(product_id,raw_text,source_type,document_type) VALUES(%s,'Phase 636 ingredient','manual_input','ingredients') RETURNING id",(product_id,)); document_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO label_extraction_runs(label_document_id,extraction_method,run_status,completed_at) VALUES(%s,'deterministic','succeeded',NOW()) RETURNING id",(document_id,)); extraction_run_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO label_extraction_items(extraction_run_id,item_type,raw_text,normalized_text,extraction_status) VALUES(%s,'ingredient','Phase 636 ingredient','phase 636 ingredient','validated') RETURNING id",(extraction_run_id,)); item_id=cursor.fetchone()[0]
                cursor.execute("""INSERT INTO product_ingredients(product_id,ingredient_id,raw_name,normalized_text,label_extraction_item_id,mapping_method,mapping_status,mapping_provenance) VALUES(%s,%s,'Phase 636 ingredient','phase 636 ingredient',%s,'deterministic_alias','accepted','{"rule":"fixture_exact_v1"}'::jsonb)""",(product_id,ingredient_id,item_id))
            connection.commit()
        finally: connection.close()
        mapping=IngredientSubstanceMappingService(); proposal=mapping.propose_mapping(
            proposal_key=uuid.uuid4(),ingredient_id=ingredient_id,substance_id=substances[0],
            relationship_type="represents",mapping_method="manual_review",proposed_by="reviewer:636")
        mapping.review_proposal(proposal["id"],"accept","reviewer:636","scientific_bridge",effective_from=date.today(),materialized_by="materializer:636")
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                  SELECT p.id,lei.id,i.id,bridge.id,s.id,si.id,a.id,f.id,r.id,
                         rel.id,ds.id,src.id
                  FROM products p
                  JOIN product_ingredients pi ON pi.product_id=p.id
                  JOIN label_extraction_items lei ON lei.id=pi.label_extraction_item_id
                  JOIN ingredients i ON i.id=pi.ingredient_id
                  JOIN ingredient_substances bridge ON bridge.ingredient_id=i.id
                    AND bridge.mapping_status='accepted' AND bridge.valid_from<=CURRENT_DATE
                    AND (bridge.valid_to IS NULL OR bridge.valid_to>=CURRENT_DATE)
                  JOIN substances s ON s.id=bridge.substance_id AND s.status='active'
                  JOIN substance_identifiers si ON si.substance_id=s.id
                    AND si.verification_status='verified' AND si.normalized_value=%s
                  JOIN scientific_assessments a ON a.substance_id=s.id AND a.ingestion_run_id=%s
                  JOIN scientific_assessment_findings f ON f.assessment_id=a.id
                  JOIN scientific_ingestion_runs r ON r.id=a.ingestion_run_id
                  JOIN source_dataset_releases rel ON rel.id=r.release_id
                  JOIN source_datasets ds ON ds.id=rel.dataset_id
                  JOIN sources src ON src.id=ds.source_id
                  WHERE p.id=%s
                """,(value,future.id,product_id)); rows=cursor.fetchall()
            self.assertEqual(len(rows),len(record.findings)); self.assertTrue(all(row[0]==product_id and row[2]==ingredient_id and row[4]==substances[0] for row in rows))
        finally: connection.close()

    def test_registry_mutation_rolls_back_when_audit_write_fails(self):
        prepared,_,result,substances,_,namespace_key=registry_fixture(); value=f"rollback-{uuid.uuid4().hex}"
        record=unknown(result.records[0],namespace_key,value); resolution=PostgresScientificSubstanceResolver().resolve(record)
        review=SubstanceResolutionReviewService(); candidate=review.record_resolution(prepared.id,record,resolution)[0]
        decision=review.decide(candidate["candidate_id"],"associate_existing","reviewer","approved",substances[0])
        with self.assertRaisesRegex(RuntimeError,"audit failure"):
            SubstanceRegistryMaterializationService(repository=_FailingRegistryAuditRepository()).materialize_decision(decision["id"],"worker")
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM substance_identifiers i JOIN substance_identifier_namespaces n ON n.id=i.namespace_id WHERE n.namespace_key=%s AND i.normalized_value=%s",(namespace_key,value)); self.assertEqual(cursor.fetchone()[0],0)
                cursor.execute("SELECT count(*) FROM substance_registry_materializations WHERE decision_id=%s",(decision["id"],)); self.assertEqual(cursor.fetchone()[0],0)
        finally: connection.close()

    def test_mapping_acceptance_and_provenance_failures_are_atomic(self):
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                token=uuid.uuid4().hex
                cursor.execute("INSERT INTO ingredients(canonical_name) VALUES(%s) RETURNING id",(f"Atomic ingredient {token}",)); ingredient_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO substances(preferred_name,normalized_name,status) VALUES(%s,%s,'active') RETURNING id",(f"Atomic substance {token}",f"atomic {token}")); substance_id=cursor.fetchone()[0]
            connection.commit()
        finally: connection.close()
        service=IngredientSubstanceMappingService(); proposal=service.propose_mapping(
            proposal_key=uuid.uuid4(),ingredient_id=ingredient_id,substance_id=substance_id,
            relationship_type="represents",mapping_method="manual_review",proposed_by="reviewer")
        with self.assertRaisesRegex(RuntimeError,"audit failure"):
            IngredientSubstanceMappingService(repository=_FailingMappingAuditRepository()).review_proposal(
                proposal["id"],"accept","reviewer","approved",effective_from=date.today(),materialized_by="worker")
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT proposal_status FROM ingredient_substance_mapping_proposals WHERE id=%s",(proposal["id"],)); self.assertEqual(cursor.fetchone()[0],"pending_review")
                cursor.execute("SELECT count(*) FROM ingredient_substance_mapping_decisions WHERE proposal_id=%s",(proposal["id"],)); self.assertEqual(cursor.fetchone()[0],0)
                cursor.execute("SELECT count(*) FROM ingredient_substances WHERE ingredient_id=%s AND substance_id=%s",(ingredient_id,substance_id)); self.assertEqual(cursor.fetchone()[0],0)
        finally: connection.close()

        prepared,_,_,_,_,_=registry_fixture(); mismatch_key=uuid.uuid4()
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT dataset_id FROM source_dataset_releases WHERE id=(SELECT release_id FROM scientific_ingestion_runs WHERE id=%s)",(prepared.id,)); dataset_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,'mismatch') RETURNING id",(dataset_id,f"mismatch-{uuid.uuid4().hex}")); wrong_release=cursor.fetchone()[0]
            connection.commit()
        finally: connection.close()
        with self.assertRaisesRegex(IngredientSubstanceMappingError,"another release"):
            service.propose_mapping(proposal_key=mismatch_key,ingredient_id=ingredient_id,
                substance_id=substance_id,relationship_type="contains",mapping_method="dataset",
                proposed_by="dataset",release_id=wrong_release,run_id=prepared.id)
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM ingredient_substance_mapping_proposals WHERE proposal_key=%s",(str(mismatch_key),)); self.assertEqual(cursor.fetchone()[0],0)
        finally: connection.close()

    @staticmethod
    def _count(table):
        connection=get_connection()
        try:
            with connection.cursor() as cursor: cursor.execute(f"SELECT count(*) FROM {table}"); return cursor.fetchone()[0]
        finally: connection.close()


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS")=="1","requires isolated lifecycle PostgreSQL")
class Phase636LifecycleTests(unittest.TestCase):
    backend=Path(__file__).resolve().parents[1]
    def alembic(self,*args,success=True):
        result=subprocess.run([sys.executable,"-m","alembic",*args],cwd=self.backend,text=True,capture_output=True)
        self.assertEqual(result.returncode==0,success,result.stdout+result.stderr); return result

    def test_0012_through_0017_legacy_and_preflight_atomicity(self):
        self.alembic("downgrade","0012_ingredient_substance_guard")
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                token=uuid.uuid4().hex
                cursor.execute("INSERT INTO ingredients(canonical_name) VALUES(%s) RETURNING id",(f"Legacy 636 ingredient {token}",)); ingredient_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO substances(preferred_name,normalized_name) VALUES(%s,%s) RETURNING id",(f"Legacy 636 substance {token}",f"legacy 636 {token}")); substance_id=cursor.fetchone()[0]
                cursor.execute("INSERT INTO ingredient_substances(ingredient_id,substance_id,relationship_type,mapping_method,mapping_status) VALUES(%s,%s,'represents','legacy','legacy_unreviewed') RETURNING id",(ingredient_id,substance_id)); mapping_id=cursor.fetchone()[0]
            connection.commit()
        finally: connection.close()
        self.alembic("upgrade","0017_ingredient_mapping_history")
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT reviewed_by,reviewed_at,valid_from,source_dataset_release_id,ingestion_run_id,provenance FROM ingredient_substances WHERE id=%s",(mapping_id,)); self.assertEqual(cursor.fetchone(),(None,None,None,None,None,None))
        finally: connection.close()
        self.alembic("downgrade","0016_substance_creation"); self.alembic("upgrade","0017_ingredient_mapping_history")
        proposal=IngredientSubstanceMappingService().propose_mapping(proposal_key=uuid.uuid4(),ingredient_id=ingredient_id,substance_id=substance_id,relationship_type="contains",mapping_method="manual_review",proposed_by="test")
        failure=self.alembic("downgrade","0016_substance_creation",success=False); self.assertIn("not representable",failure.stdout+failure.stderr)
        connection=get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cursor.fetchone()[0],"0017_ingredient_mapping_history")
                cursor.execute("SELECT count(*) FROM ingredient_substance_mapping_proposals WHERE id=%s",(proposal["id"],)); self.assertEqual(cursor.fetchone()[0],1)
                cursor.execute("SELECT reviewed_by,valid_from,provenance FROM ingredient_substances WHERE id=%s",(mapping_id,)); self.assertEqual(cursor.fetchone(),(None,None,None))
        finally: connection.close()


if __name__=="__main__": unittest.main()
