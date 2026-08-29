import os
import threading
import unittest
import uuid

import psycopg2
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db import get_connection
from app.repositories.ingredient_catalog import PostgresIngredientCatalogRepository
from app.routes.ingredient_mapping_reviews import router
from app.services.ingredient_mapping_reviews import (
    IngredientMappingReviewError,
    IngredientMappingReviewService,
)
from app.services.ingredient_mappings import IngredientMappingService


@unittest.skipUnless(
    os.environ.get("WYE_TEST_DATABASE"),
    "requires WYE_TEST_DATABASE pointing to isolated PostgreSQL at 0006",
)
class Phase5EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.connection=get_connection(); self.product_ids=[]; self.storage_ids=[]; self.ingredient_ids=[]
        os.environ["WYE_IMAGE_API_KEY"]="phase58-secret"
        app=FastAPI(); app.include_router(router); self.client=TestClient(app)
        self.headers={"X-Wye-Image-Key":"phase58-secret"}

    def tearDown(self):
        os.environ.pop("WYE_IMAGE_API_KEY",None)
        try:
            self.connection.rollback()
            with self.connection.cursor() as cursor:
                if self.product_ids:
                    cursor.execute("DELETE FROM ingredient_mapping_reviews WHERE product_ingredient_id IN (SELECT id FROM product_ingredients WHERE product_id=ANY(%s))",(self.product_ids,))
                    cursor.execute("DELETE FROM product_ingredients WHERE product_id=ANY(%s)",(self.product_ids,))
                    cursor.execute("DELETE FROM product_label_documents WHERE product_image_id IN (SELECT id FROM product_images WHERE product_id=ANY(%s))",(self.product_ids,))
                    cursor.execute("DELETE FROM product_images WHERE product_id=ANY(%s)",(self.product_ids,))
                    cursor.execute("DELETE FROM products WHERE id=ANY(%s)",(self.product_ids,))
                if self.storage_ids: cursor.execute("DELETE FROM storage_objects WHERE id=ANY(%s)",(self.storage_ids,))
                if self.ingredient_ids:
                    cursor.execute("DELETE FROM ingredient_aliases WHERE ingredient_id=ANY(%s)",(self.ingredient_ids,))
                    cursor.execute("DELETE FROM ingredients WHERE id=ANY(%s)",(self.ingredient_ids,))
            self.connection.commit()
        finally: self.connection.close()

    def canonical(self,name):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id",(name,)); value=cursor.fetchone()[0]
        self.connection.commit(); self.ingredient_ids.append(value); return value

    def product(self):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO products (barcode,product_name,category) VALUES (%s,'Phase 5.8 E2E','food') RETURNING id",(f"phase58-{uuid.uuid4().hex}",)); value=cursor.fetchone()[0]
        self.connection.commit(); self.product_ids.append(value); return value

    def extraction_run(self,product_id,items):
        suffix=uuid.uuid4().hex
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO storage_objects (storage_provider,bucket,object_key) VALUES ('test','phase58',%s) RETURNING id",(f"phase58/{suffix}",)); storage_id=cursor.fetchone()[0]; self.storage_ids.append(storage_id)
            cursor.execute("INSERT INTO product_images (product_id,image_type,storage_object_id,mime_type,checksum,source,status) VALUES (%s,'ingredients',%s,'image/jpeg',%s,'user_submission','active') RETURNING id",(product_id,storage_id,suffix.ljust(64,'a')[:64])); image_id=cursor.fetchone()[0]
            cursor.execute("INSERT INTO product_label_documents (product_image_id,source_type,document_type) VALUES (%s,'image_derived','ingredients') RETURNING id",(image_id,)); document_id=cursor.fetchone()[0]
            cursor.execute("INSERT INTO label_extraction_runs (label_document_id,extraction_method,run_status,completed_at) VALUES (%s,'deterministic','succeeded',NOW()) RETURNING id",(document_id,)); run_id=cursor.fetchone()[0]
            item_ids=[]
            for position,(raw,language,structured) in enumerate(items,1):
                cursor.execute("INSERT INTO label_extraction_items (extraction_run_id,item_type,raw_text,detected_language,structured_value,position_in_document) VALUES (%s,'ingredient',%s,%s,%s::jsonb,%s) RETURNING id",(run_id,raw,language,structured,position)); item_ids.append(cursor.fetchone()[0])
        self.connection.commit(); return run_id,item_ids

    def mapping(self,item_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT pi.id AS product_ingredient_id,pi.ingredient_id,pi.raw_name,pi.normalized_text,pi.mapping_method,pi.mapping_status,pi.mapping_provenance,r.id AS review_id,r.review_status,r.reviewed_at,r.reviewed_by,r.review_provenance,(SELECT count(*) FROM ingredient_mapping_review_candidates c WHERE c.review_id=r.id) AS candidate_count,(SELECT count(*) FROM ingredient_mapping_review_candidates c WHERE c.review_id=r.id AND c.is_selected) AS selected_count FROM product_ingredients pi JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id WHERE pi.label_extraction_item_id=%s",(item_id,)); return cursor.fetchone()

    def candidate_ids(self,review_id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT id,ingredient_id FROM ingredient_mapping_review_candidates WHERE review_id=%s ORDER BY candidate_confidence DESC NULLS LAST,id",(review_id,)); return cursor.fetchall()

    def test_full_phase5_pipeline(self):
        citric=self.canonical("Acido Citrico")
        sodium=self.canonical("Sodium benzoate")
        ambiguous_a=self.canonical("Ambiguous Exact")
        ambiguous_b=self.canonical("Ambiguous Exact")
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO ingredient_aliases (ingredient_id,alias_name,normalized_alias,language,alias_type,confidence,is_primary,mapping_method,mapping_status,approved_at) VALUES (%s,'E330','e330','it','e_number',1.0,FALSE,'manual_review','accepted',NOW())",(citric,))
        self.connection.commit()

        product_id=self.product()
        run_id,item_ids=self.extraction_run(product_id,(
            ("Acido Citrico","it",'{"quantity":"1%"}'),
            ("E 330","it",'{}'),
            ("Sodium benzoat","en",'{}'),
            ("Ambiguous Exact","en",'{}'),
            ("qxzv unknown phase five eight","en",'{}'),
        ))
        first=IngredientMappingService().map_run(product_id,run_id)
        self.assertEqual(len(first.mappings),5)
        exact=self.mapping(item_ids[0]); alias_exact=self.mapping(item_ids[1]); fuzzy=self.mapping(item_ids[2]); ambiguous=self.mapping(item_ids[3]); zero=self.mapping(item_ids[4])
        self.assertEqual((exact[1],exact[3],exact[4],exact[5],exact[8],exact[13]),(citric,"acido citrico","deterministic_alias","accepted","accepted",1))
        self.assertEqual((alias_exact[1],alias_exact[3],alias_exact[5],alias_exact[8],alias_exact[13]),(citric,"e330","accepted","accepted",1))
        self.assertEqual((fuzzy[1],fuzzy[5],fuzzy[8],fuzzy[12],fuzzy[13]),(None,"needs_review","pending",1,0))
        self.assertEqual((ambiguous[1],ambiguous[5],ambiguous[8],ambiguous[12],ambiguous[13]),(None,"needs_review","pending",2,0))
        self.assertEqual((zero[1],zero[5],zero[8],zero[12],zero[13]),(None,"needs_review","pending",0,0))

        retro_product=self.product(); retro_run,retro_items=self.extraction_run(retro_product,(("Sodium benzoat","en",'{}'),)); IngredientMappingService().map_run(retro_product,retro_run); retro_before=self.mapping(retro_items[0])

        fuzzy_candidate=self.candidate_ids(fuzzy[7])[0]
        response=self.client.post(f"/ingredient-mapping-reviews/{fuzzy[7]}/decision",headers=self.headers,json={"status":"accepted","candidate_id":fuzzy_candidate[0]})
        self.assertEqual(response.status_code,200)
        accepted=self.mapping(item_ids[2]); self.assertEqual((accepted[1],accepted[4],accepted[5],accepted[8],accepted[10],accepted[13]),(sodium,"manual_review","accepted","accepted",None,1)); self.assertIsNotNone(accepted[9]); self.assertEqual(accepted[11]["resolution_type"],"human_review")

        response=self.client.post(f"/ingredient-mapping-reviews/{ambiguous[7]}/decision",headers=self.headers,json={"status":"ambiguous"}); self.assertEqual(response.status_code,200)
        ambiguous_done=self.mapping(item_ids[3]); self.assertEqual((ambiguous_done[1],ambiguous_done[5],ambiguous_done[8],ambiguous_done[13]),(None,"ambiguous","ambiguous",0)); self.assertEqual(ambiguous_done[11]["decision"],"ambiguous")
        response=self.client.post(f"/ingredient-mapping-reviews/{zero[7]}/decision",headers=self.headers,json={"status":"rejected"}); self.assertEqual(response.status_code,200)
        rejected=self.mapping(item_ids[4]); self.assertEqual((rejected[1],rejected[5],rejected[8],rejected[13]),(None,"rejected","rejected",0)); self.assertEqual(rejected[11]["decision"],"rejected")

        response=self.client.post(f"/ingredient-mapping-reviews/{fuzzy[7]}/approve-alias",headers=self.headers); self.assertEqual(response.status_code,200)
        approved=response.json()["alias"]; self.assertEqual((approved["alias_name"],approved["normalized_alias"],approved["language"],approved["ingredient_id"],approved["mapping_status"],approved["mapping_method"],approved["confidence"],approved["is_primary"]),("Sodium benzoat","sodium benzoat","en",sodium,"accepted","manual_review",1.0,False)); self.assertEqual(approved["review_provenance"]["review_id"],fuzzy[7])
        catalog=PostgresIngredientCatalogRepository().load_catalog(); self.assertTrue(any(a.ingredient_id==sodium and a.normalized_alias=="sodium benzoat" and a.mapping_status=="accepted" for a in catalog.aliases))
        self.assertEqual(self.mapping(retro_items[0]),retro_before)

        future_product=self.product(); future_run,future_items=self.extraction_run(future_product,(("Sodium benzoat","en",'{}'),)); IngredientMappingService().map_run(future_product,future_run); future=self.mapping(future_items[0]); self.assertEqual((future[1],future[4],future[5],future[8],future[13]),(sodium,"deterministic_alias","accepted","accepted",1)); self.assertIn("exact_accepted_alias",future[11]["resolution_reason"])

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*),count(DISTINCT pi.id),count(DISTINCT r.id),count(DISTINCT c.id) FROM product_ingredients pi JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id LEFT JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id WHERE pi.product_id=%s",(product_id,)); counts_before=cursor.fetchone()
        second=IngredientMappingService().map_run(product_id,run_id); self.assertTrue(all(not m.created for m in second.mappings))
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*),count(DISTINCT pi.id),count(DISTINCT r.id),count(DISTINCT c.id) FROM product_ingredients pi JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id LEFT JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id WHERE pi.product_id=%s",(product_id,)); self.assertEqual(cursor.fetchone(),counts_before)
        repeat=self.client.post(f"/ingredient-mapping-reviews/{fuzzy[7]}/approve-alias",headers=self.headers); self.assertEqual(repeat.status_code,200); self.assertFalse(repeat.json()["created"]); self.assertEqual(repeat.json()["alias"]["id"],approved["id"])

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT p.id,pi.raw_name,pi.normalized_text,pi.mapping_provenance->>'normalization_version',pi.mapping_provenance->>'candidate_generation_version',r.review_provenance->>'resolution_version',r.review_provenance->>'resolution_type',c.is_selected,i.id,lei.id,ler.id,pld.id,pim.id FROM products p JOIN product_ingredients pi ON pi.product_id=p.id JOIN ingredients i ON i.id=pi.ingredient_id JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id AND c.is_selected JOIN label_extraction_items lei ON lei.id=pi.label_extraction_item_id JOIN label_extraction_runs ler ON ler.id=lei.extraction_run_id JOIN product_label_documents pld ON pld.id=ler.label_document_id JOIN product_images pim ON pim.id=pld.product_image_id WHERE pi.label_extraction_item_id=%s",(item_ids[0],)); traversal=cursor.fetchone()
        self.assertEqual(traversal[0],product_id); self.assertEqual(traversal[1:5],("Acido Citrico","acido citrico","ingredient_normalization_v1","ingredient_candidate_generation_v1")); self.assertEqual((traversal[5],traversal[6],traversal[7],traversal[8],traversal[9],traversal[10]),("ingredient_deterministic_resolution_v1","deterministic_auto",True,citric,item_ids[0],run_id)); self.assertTrue(all(value is not None for value in traversal[11:]))

    def test_concurrent_alias_approval_converges_and_alias_uniqueness_holds(self):
        ingredient_id=self.canonical("Concurrent Alias Target"); product_id=self.product(); run_id,item_ids=self.extraction_run(product_id,(("Concurrent Alias Targe","en",'{}'),)); IngredientMappingService().map_run(product_id,run_id); mapping=self.mapping(item_ids[0]); candidate=self.candidate_ids(mapping[7])[0]; IngredientMappingReviewService().decide(mapping[7],"accepted",candidate[0])
        barrier=threading.Barrier(2); results=[]; lock=threading.Lock()
        def approve():
            barrier.wait()
            try: outcome=IngredientMappingReviewService().approve_alias(mapping[7])["created"]
            except IngredientMappingReviewError as exc: outcome=exc.status
            with lock: results.append(outcome)
        threads=[threading.Thread(target=approve) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(15)
        self.assertFalse(any(thread.is_alive() for thread in threads)); self.assertCountEqual(results,[True,False])
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM ingredient_aliases WHERE normalized_alias='concurrent alias targe' AND language='en'"); self.assertEqual(cursor.fetchone()[0],1)
        other=self.canonical("Other Concurrent Target")
        with self.assertRaises(psycopg2.IntegrityError):
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO ingredient_aliases (ingredient_id,alias_name,normalized_alias,language,mapping_status) VALUES (%s,'duplicate','concurrent alias targe','en','accepted')",(other,))
            self.connection.commit()
        self.connection.rollback()


if __name__=="__main__": unittest.main()
