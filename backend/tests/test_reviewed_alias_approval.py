import os
import unittest
import uuid

from app.db import get_connection
from app.repositories.ingredient_catalog import PostgresIngredientCatalogRepository
from app.repositories.ingredient_mapping_reviews import PostgresIngredientMappingReviewRepository
from app.services.ingredient_mapping_reviews import (
    IngredientMappingReviewError,
    IngredientMappingReviewService,
)


class FailingAliasRepository(PostgresIngredientMappingReviewRepository):
    def insert_approved_alias(self, *args, **kwargs):
        super().insert_approved_alias(*args, **kwargs)
        raise RuntimeError("forced alias persistence failure")


@unittest.skipUnless(
    os.environ.get("WYE_TEST_DATABASE"),
    "requires WYE_TEST_DATABASE pointing to an isolated database migrated to 0006",
)
class ReviewedAliasApprovalTests(unittest.TestCase):
    def setUp(self):
        self.connection = get_connection()
        self.product_ids = []
        self.ingredient_ids = []

    def tearDown(self):
        try:
            self.connection.rollback()
            with self.connection.cursor() as cursor:
                if self.product_ids:
                    cursor.execute(
                        "DELETE FROM ingredient_mapping_reviews WHERE product_ingredient_id IN "
                        "(SELECT id FROM product_ingredients WHERE product_id = ANY(%s))",
                        (self.product_ids,),
                    )
                    cursor.execute("DELETE FROM product_ingredients WHERE product_id = ANY(%s)", (self.product_ids,))
                    cursor.execute("DELETE FROM products WHERE id = ANY(%s)", (self.product_ids,))
                if self.ingredient_ids:
                    cursor.execute("DELETE FROM ingredient_aliases WHERE ingredient_id = ANY(%s)", (self.ingredient_ids,))
                    cursor.execute("DELETE FROM ingredients WHERE id = ANY(%s)", (self.ingredient_ids,))
            self.connection.commit()
        finally:
            self.connection.close()

    def canonical(self, name=None):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id", (name or f"alias-target-{uuid.uuid4().hex}",))
            ingredient_id = cursor.fetchone()[0]
        self.connection.commit(); self.ingredient_ids.append(ingredient_id); return ingredient_id

    def review(self, ingredient_id, raw="Observed Alias", normalized=None, language="it", accepted=True):
        normalized = raw.casefold() if normalized is None else normalized
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO products (barcode,product_name,category) VALUES (%s,'Alias approval','food') RETURNING id", (f"alias-approval-{uuid.uuid4().hex}",))
            product_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO product_ingredients (product_id,ingredient_id,raw_name,normalized_text,detected_language,position_in_list,mapping_method,mapping_status,mapping_provenance) "
                "VALUES (%s,%s,%s,%s,%s,1,%s,%s,'{\"normalization_version\":\"ingredient_normalization_v1\"}'::jsonb) RETURNING id",
                (product_id, ingredient_id if accepted else None, raw, normalized, language, "manual_review" if accepted else "unmapped", "accepted" if accepted else "needs_review"),
            )
            product_ingredient_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO ingredient_mapping_reviews (product_ingredient_id,raw_text,normalized_text,detected_language,review_status,requested_by_method,reviewed_at) "
                "VALUES (%s,%s,%s,%s,%s,'deterministic',CASE WHEN %s THEN NOW() ELSE NULL END) RETURNING id",
                (product_ingredient_id, raw, normalized, language, "accepted" if accepted else "pending", accepted),
            )
            review_id = cursor.fetchone()[0]
            candidate_id = None
            if ingredient_id is not None:
                cursor.execute(
                    "INSERT INTO ingredient_mapping_review_candidates (review_id,ingredient_id,candidate_method,candidate_confidence,rationale,is_selected) "
                    "VALUES (%s,%s,'deterministic',1.0,'fixture',%s) RETURNING id",
                    (review_id, ingredient_id, accepted),
                )
                candidate_id = cursor.fetchone()[0]
        self.connection.commit(); self.product_ids.append(product_id)
        return product_id, product_ingredient_id, review_id, candidate_id

    def insert_alias(self, ingredient_id, normalized_alias, status="accepted", language="it"):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ingredient_aliases (ingredient_id,alias_name,normalized_alias,language,alias_type,confidence,is_primary,mapping_method,mapping_status) "
                "VALUES (%s,%s,%s,%s,'synonym',0.5,FALSE,'legacy',%s) RETURNING id",
                (ingredient_id, normalized_alias, normalized_alias, language, status),
            )
            alias_id = cursor.fetchone()[0]
        self.connection.commit(); return alias_id

    def history(self, review_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT r.review_status,r.reviewed_at,r.reviewed_by,r.review_provenance,pi.ingredient_id,pi.mapping_status,pi.mapping_method,pi.mapping_provenance,array_agg(c.id ORDER BY c.id),array_agg(c.is_selected ORDER BY c.id) "
                "FROM ingredient_mapping_reviews r JOIN product_ingredients pi ON pi.id=r.product_ingredient_id LEFT JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id "
                "WHERE r.id=%s GROUP BY r.id,pi.id", (review_id,),
            )
            return cursor.fetchone()

    def test_accepted_review_creates_complete_alias_without_changing_history(self):
        ingredient_id = self.canonical("Citric acid")
        _, product_ingredient_id, review_id, _ = self.review(ingredient_id, raw="  E-330  ", normalized="e330")
        before = self.history(review_id)
        result = IngredientMappingReviewService().approve_alias(review_id)
        alias = result["alias"]
        self.assertTrue(result["created"])
        self.assertEqual((alias["alias_name"],alias["normalized_alias"],alias["ingredient_id"],alias["language"]), ("  E-330  ","e330",ingredient_id,"it"))
        self.assertEqual((alias["alias_type"],float(alias["confidence"]),alias["is_primary"],alias["mapping_method"],alias["mapping_status"]), ("synonym",1.0,False,"manual_review","accepted"))
        self.assertIsNotNone(alias["approved_at"])
        provenance = alias["review_provenance"]
        self.assertEqual((provenance["source"],provenance["review_id"],provenance["product_ingredient_id"],provenance["normalization_version"]), ("human_mapping_review",review_id,product_ingredient_id,"ingredient_normalization_v1"))
        self.assertIn("label_extraction_item_id", provenance)
        self.assertEqual(self.history(review_id), before)

    def test_repeated_approval_is_idempotent(self):
        ingredient_id = self.canonical(); _,_,review_id,_ = self.review(ingredient_id)
        first = IngredientMappingReviewService().approve_alias(review_id)
        second = IngredientMappingReviewService().approve_alias(review_id)
        self.assertTrue(first["created"]); self.assertFalse(second["created"])
        self.assertEqual(first["alias"]["id"], second["alias"]["id"])

    def test_nonaccepted_reviews_are_rejected(self):
        ingredient_id = self.canonical()
        for status in ("pending","ambiguous","rejected"):
            _,pi_id,review_id,_ = self.review(ingredient_id,raw=status,accepted=False)
            if status != "pending":
                with self.connection.cursor() as cursor:
                    cursor.execute("UPDATE ingredient_mapping_reviews SET review_status=%s,reviewed_at=NOW() WHERE id=%s",(status,review_id))
                    cursor.execute("UPDATE product_ingredients SET mapping_status=%s,mapping_method='manual_review' WHERE id=%s",(status,pi_id))
                self.connection.commit()
            with self.assertRaises(IngredientMappingReviewError) as caught:
                IngredientMappingReviewService().approve_alias(review_id)
            self.assertEqual(caught.exception.status,409)

    def test_incoherent_accepted_mapping_is_rejected(self):
        selected=self.canonical(); divergent=self.canonical(); _,pi_id,review_id,_=self.review(selected)
        with self.connection.cursor() as cursor: cursor.execute("UPDATE product_ingredients SET ingredient_id=%s WHERE id=%s",(divergent,pi_id))
        self.connection.commit()
        with self.assertRaises(IngredientMappingReviewError) as caught: IngredientMappingReviewService().approve_alias(review_id)
        self.assertEqual(caught.exception.code,"inconsistent_accepted_review")

    def test_accepted_collision_with_other_ingredient_is_conflict(self):
        target=self.canonical(); other=self.canonical(); _,_,review_id,_=self.review(target,raw="Shared Alias")
        self.insert_alias(other,"shared alias")
        with self.assertRaises(IngredientMappingReviewError) as caught: IngredientMappingReviewService().approve_alias(review_id)
        self.assertEqual((caught.exception.code,caught.exception.status),("alias_collision",409))

    def test_existing_accepted_alias_for_same_ingredient_is_reused(self):
        ingredient_id=self.canonical(); _,_,review_id,_=self.review(ingredient_id)
        alias_id=self.insert_alias(ingredient_id,"observed alias")
        result=IngredientMappingReviewService().approve_alias(review_id)
        self.assertFalse(result["created"]); self.assertEqual(result["alias"]["id"],alias_id)

    def test_deprecated_and_legacy_aliases_are_conflicts(self):
        for status in ("deprecated","legacy_unreviewed"):
            ingredient_id=self.canonical(); raw=f"Historical {status}"; _,_,review_id,_=self.review(ingredient_id,raw=raw)
            self.insert_alias(ingredient_id,raw.casefold(),status=status)
            with self.assertRaises(IngredientMappingReviewError) as caught: IngredientMappingReviewService().approve_alias(review_id)
            self.assertEqual(caught.exception.code,"alias_historical_collision")

    def test_failure_rolls_back_alias_and_preserves_mapping_history(self):
        ingredient_id=self.canonical(); _,_,review_id,_=self.review(ingredient_id); before=self.history(review_id)
        service=IngredientMappingReviewService(repository=FailingAliasRepository())
        with self.assertRaisesRegex(RuntimeError,"forced alias"): service.approve_alias(review_id)
        self.assertEqual(self.history(review_id),before)
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM ingredient_aliases WHERE normalized_alias='observed alias' AND language='it'")
            self.assertEqual(cursor.fetchone()[0],0)

    def test_alias_is_visible_to_catalog_without_retroactive_remapping(self):
        ingredient_id=self.canonical(); _,_,accepted_id,_=self.review(ingredient_id,raw="Future Alias")
        _,_,pending_id,_=self.review(ingredient_id,raw="Future Alias",accepted=False); pending_before=self.history(pending_id)
        IngredientMappingReviewService().approve_alias(accepted_id)
        catalog=PostgresIngredientCatalogRepository().load_catalog()
        self.assertTrue(any(a.ingredient_id==ingredient_id and a.normalized_alias=="future alias" and a.mapping_status=="accepted" for a in catalog.aliases))
        self.assertEqual(self.history(pending_id),pending_before)

    def test_missing_language_and_normalization_mismatch_are_rejected(self):
        ingredient_id=self.canonical(); _,_,missing,_=self.review(ingredient_id,raw="No Language",language=None)
        with self.assertRaises(IngredientMappingReviewError) as caught: IngredientMappingReviewService().approve_alias(missing)
        self.assertEqual(caught.exception.code,"alias_language_missing")
        _,_,mismatch,_=self.review(ingredient_id,raw="Correct",normalized="wrong")
        with self.assertRaises(IngredientMappingReviewError) as caught: IngredientMappingReviewService().approve_alias(mismatch)
        self.assertEqual(caught.exception.code,"normalization_mismatch")


if __name__ == "__main__":
    unittest.main()
