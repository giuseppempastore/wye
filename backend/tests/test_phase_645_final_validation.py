"""Final integrated validation for Phase 6 scientific evidence ingestion."""

from datetime import date
import os
import unittest
import uuid

from app.db import get_connection
from app.services.ingredient_substance_mapping import IngredientSubstanceMappingService
from app.services.scientific_batch import ScientificBatchIngestionService, ScientificBatchPlan
from backend.tests import test_phase_644_batch_recovery as batch_fixtures


@unittest.skipUnless(
    os.getenv("WYE_TEST_DATABASE"),
    "requires isolated PostgreSQL at 0018",
)
class Phase645FinalValidationTests(unittest.TestCase):
    def test_product_traverses_to_batch_produced_scientific_evidence(self):
        helper = batch_fixtures.ScientificBatchRecoveryPostgresTests(
            "test_full_bounded_multi_provider_resume_and_summary"
        )
        helper.setUp()
        try:
            item, _ = helper._pipeline("efsa", "phase645-efsa-batch")
            summary = ScientificBatchIngestionService().execute(
                ScientificBatchPlan((item,))
            )
        finally:
            helper.tearDown()

        self.assertEqual(summary.results[0].state, "completed")
        ingestion_run_id = summary.results[0].ingestion_run_id
        self.assertIsNotNone(ingestion_run_id)

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT a.substance_id, si.normalized_value
                    FROM scientific_assessments a
                    JOIN substance_identifiers si ON si.substance_id=a.substance_id
                    WHERE a.ingestion_run_id=%s
                      AND si.verification_status='verified'
                    ORDER BY si.id
                    LIMIT 1
                    """,
                    (ingestion_run_id,),
                )
                substance_id, identifier = cursor.fetchone()
                token = uuid.uuid4().hex
                cursor.execute(
                    "INSERT INTO ingredients(canonical_name) VALUES(%s) RETURNING id",
                    (f"Phase 645 ingredient {token}",),
                )
                ingredient_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO products(barcode,product_name,category)
                    VALUES(%s,'Phase 645 batch product','food') RETURNING id
                    """,
                    (f"phase645-{token}",),
                )
                product_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO product_label_documents(
                      product_id,raw_text,source_type,document_type)
                    VALUES(%s,'Phase 645 ingredient','manual_input','ingredients')
                    RETURNING id
                    """,
                    (product_id,),
                )
                document_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO label_extraction_runs(
                      label_document_id,extraction_method,run_status,completed_at)
                    VALUES(%s,'deterministic','succeeded',NOW()) RETURNING id
                    """,
                    (document_id,),
                )
                extraction_run_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO label_extraction_items(
                      extraction_run_id,item_type,raw_text,normalized_text,
                      extraction_status)
                    VALUES(%s,'ingredient','Phase 645 ingredient',%s,'validated')
                    RETURNING id
                    """,
                    (extraction_run_id, f"phase 645 ingredient {token}"),
                )
                extraction_item_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO product_ingredients(
                      product_id,ingredient_id,raw_name,normalized_text,
                      label_extraction_item_id,mapping_method,mapping_status,
                      mapping_provenance)
                    VALUES(%s,%s,'Phase 645 ingredient',%s,%s,
                      'deterministic_alias','accepted',
                      '{"rule":"phase645_fixture_exact_v1"}'::jsonb)
                    """,
                    (
                        product_id,
                        ingredient_id,
                        f"phase 645 ingredient {token}",
                        extraction_item_id,
                    ),
                )
            connection.commit()
        finally:
            connection.close()

        mapping = IngredientSubstanceMappingService()
        proposal = mapping.propose_mapping(
            proposal_key=uuid.uuid4(),
            ingredient_id=ingredient_id,
            substance_id=substance_id,
            relationship_type="represents",
            mapping_method="manual_review",
            proposed_by="reviewer:phase645",
        )
        mapping.review_proposal(
            proposal["id"],
            "accept",
            "reviewer:phase645",
            "scientific_bridge",
            effective_from=date.today(),
            materialized_by="materializer:phase645",
        )

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT p.id,lei.id,i.id,bridge.id,s.id,si.id,a.id,f.id,
                           run.id,artifact.id,release.id,dataset.id,source.id,
                           batch_item.id,batch_attempt.id
                    FROM products p
                    JOIN product_ingredients pi ON pi.product_id=p.id
                    JOIN label_extraction_items lei
                      ON lei.id=pi.label_extraction_item_id
                    JOIN ingredients i ON i.id=pi.ingredient_id
                    JOIN ingredient_substances bridge
                      ON bridge.ingredient_id=i.id
                     AND bridge.mapping_status='accepted'
                     AND bridge.valid_from<=CURRENT_DATE
                     AND (bridge.valid_to IS NULL OR bridge.valid_to>=CURRENT_DATE)
                    JOIN substances s
                      ON s.id=bridge.substance_id AND s.status='active'
                    JOIN substance_identifiers si
                      ON si.substance_id=s.id
                     AND si.verification_status='verified'
                     AND si.normalized_value=%s
                    JOIN scientific_assessments a
                      ON a.substance_id=s.id AND a.ingestion_run_id=%s
                    JOIN scientific_assessment_findings f
                      ON f.assessment_id=a.id
                    JOIN scientific_ingestion_runs run
                      ON run.id=a.ingestion_run_id
                    JOIN scientific_ingestion_run_artifacts membership
                      ON membership.ingestion_run_id=run.id
                    JOIN scientific_release_artifacts artifact
                      ON artifact.id=membership.release_artifact_id
                    JOIN source_dataset_releases release
                      ON release.id=run.release_id
                    JOIN source_datasets dataset ON dataset.id=release.dataset_id
                    JOIN sources source ON source.id=dataset.source_id
                    JOIN scientific_batch_work_items batch_item
                      ON batch_item.ingestion_run_id=run.id
                     AND batch_item.work_status='succeeded'
                    JOIN scientific_batch_work_attempts batch_attempt
                      ON batch_attempt.work_item_id=batch_item.id
                     AND batch_attempt.attempt_status='completed'
                    WHERE p.id=%s
                    """,
                    (identifier, ingestion_run_id, product_id),
                )
                rows = cursor.fetchall()
        finally:
            connection.close()

        self.assertGreaterEqual(len(rows), 1)
        self.assertTrue(all(row[0] == product_id for row in rows))
        self.assertTrue(all(row[4] == substance_id for row in rows))
        self.assertTrue(all(row[8] == ingestion_run_id for row in rows))


if __name__ == "__main__":
    unittest.main()
