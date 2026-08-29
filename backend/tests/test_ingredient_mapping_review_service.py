import os
import threading
import unittest
import uuid

from app.db import get_connection
from app.repositories.ingredient_mapping_reviews import PostgresIngredientMappingReviewRepository
from app.services.ingredient_mapping_reviews import (
    HUMAN_REVIEW_VERSION,
    IngredientMappingReviewError,
    IngredientMappingReviewService,
)


class FailingDecisionRepository(PostgresIngredientMappingReviewRepository):
    def apply_decision(self, *args, **kwargs):
        super().apply_decision(*args, **kwargs)
        raise RuntimeError("forced final decision failure")


@unittest.skipUnless(
    os.environ.get("WYE_TEST_DATABASE"),
    "requires WYE_TEST_DATABASE pointing to an isolated database migrated to 0006",
)
class IngredientMappingReviewServiceTests(unittest.TestCase):
    def setUp(self):
        self.connection = get_connection()
        self.product_ids = []
        self.ingredient_ids = []

    def tearDown(self):
        try:
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
                    cursor.execute("DELETE FROM ingredients WHERE id = ANY(%s)", (self.ingredient_ids,))
            self.connection.commit()
        finally:
            self.connection.close()

    def product(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO products (barcode, product_name, category) VALUES (%s, 'Review API', 'food') RETURNING id",
                (f"review-api-{uuid.uuid4().hex}",),
            )
            value = cursor.fetchone()[0]
        self.connection.commit(); self.product_ids.append(value); return value

    def canonical(self, name=None):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id", (name or f"ingredient-{uuid.uuid4().hex}",))
            value = cursor.fetchone()[0]
        self.connection.commit(); self.ingredient_ids.append(value); return value

    def pending_review(self, candidates=(), raw="E330"):
        product_id = self.product()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO product_ingredients "
                "(product_id, raw_name, normalized_text, detected_language, position_in_list, mapping_method, mapping_status, mapping_provenance) "
                "VALUES (%s, %s, %s, 'it', 1, 'unmapped', 'needs_review', %s::jsonb) RETURNING id",
                (product_id, raw, raw.lower(), '{"normalization_version":"ingredient_normalization_v1","candidate_generation_version":"ingredient_candidate_generation_v1","extraction_item_id":42,"extracted_quantity":"1%"}'),
            )
            product_ingredient_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO ingredient_mapping_reviews "
                "(product_ingredient_id, raw_text, normalized_text, detected_language, requested_by_method, review_provenance) "
                "VALUES (%s, %s, %s, 'it', 'deterministic', '{\"source\":\"mapping_service\"}'::jsonb) RETURNING id",
                (product_ingredient_id, raw, raw.lower()),
            )
            review_id = cursor.fetchone()[0]
            candidate_ids = []
            for rank, ingredient_id in enumerate(candidates):
                cursor.execute(
                    "INSERT INTO ingredient_mapping_review_candidates "
                    "(review_id, ingredient_id, candidate_method, candidate_confidence, rationale) "
                    "VALUES (%s, %s, 'deterministic', %s, %s) RETURNING id",
                    (review_id, ingredient_id, 1 - rank / 10, f"rank {rank}"),
                )
                candidate_ids.append(cursor.fetchone()[0])
        self.connection.commit()
        return product_id, product_ingredient_id, review_id, candidate_ids

    def state(self, review_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT r.review_status, r.reviewed_at, r.reviewed_by, r.review_provenance, "
                "pi.ingredient_id, pi.mapping_status, pi.mapping_method, pi.mapping_provenance, "
                "(SELECT count(*) FROM ingredient_mapping_review_candidates c WHERE c.review_id=r.id AND c.is_selected) "
                "FROM ingredient_mapping_reviews r JOIN product_ingredients pi ON pi.id=r.product_ingredient_id WHERE r.id=%s",
                (review_id,),
            )
            return cursor.fetchone()

    def test_list_and_detail_include_product_and_canonical_candidates(self):
        ingredient_id = self.canonical("Acido citrico")
        product_id, product_ingredient_id, review_id, _ = self.pending_review((ingredient_id,))
        listing = IngredientMappingReviewService().list("pending")["reviews"]
        row = next(item for item in listing if item["review_id"] == review_id)
        self.assertEqual((row["product_id"], row["candidate_count"]), (product_id, 1))
        detail = IngredientMappingReviewService().detail(review_id)
        self.assertEqual(detail["product_ingredient"]["id"], product_ingredient_id)
        self.assertEqual(detail["product_ingredient"]["extracted_quantity"], "1%")
        self.assertEqual(detail["candidates"][0]["canonical_name"], "Acido citrico")

    def test_accept_updates_all_rows_and_preserves_provenance(self):
        first, second = self.canonical("First"), self.canonical("Second")
        _, _, review_id, candidate_ids = self.pending_review((first, second))
        detail = IngredientMappingReviewService().decide(review_id, "accepted", candidate_ids[1])
        state = self.state(review_id)
        self.assertEqual(state[0], "accepted"); self.assertIsNotNone(state[1]); self.assertIsNone(state[2])
        self.assertEqual((state[4], state[5], state[6], state[8]), (second, "accepted", "manual_review", 1))
        self.assertEqual(state[3]["resolution_type"], "human_review")
        self.assertEqual(state[3]["resolution_version"], HUMAN_REVIEW_VERSION)
        self.assertEqual(state[3]["selected_candidate_id"], candidate_ids[1])
        self.assertEqual(state[7]["normalization_version"], "ingredient_normalization_v1")
        self.assertEqual(state[7]["candidate_generation_version"], "ingredient_candidate_generation_v1")
        self.assertEqual(detail["review"]["review_status"], "accepted")

    def test_ambiguous_clears_selection_and_mapping(self):
        ingredient_id = self.canonical()
        _, _, review_id, _ = self.pending_review((ingredient_id,))
        IngredientMappingReviewService().decide(review_id, "ambiguous")
        state = self.state(review_id)
        self.assertEqual((state[0], state[4], state[5], state[6], state[8]), ("ambiguous", None, "ambiguous", "manual_review", 0))
        self.assertEqual(state[7]["decision"], "ambiguous")

    def test_rejected_clears_selection_and_mapping(self):
        ingredient_id = self.canonical()
        _, _, review_id, _ = self.pending_review((ingredient_id,))
        IngredientMappingReviewService().decide(review_id, "rejected")
        state = self.state(review_id)
        self.assertEqual((state[0], state[4], state[5], state[6], state[8]), ("rejected", None, "rejected", "manual_review", 0))

    def test_invalid_accept_and_foreign_candidate_are_rejected(self):
        ingredient_id = self.canonical()
        _, _, review_id, _ = self.pending_review((ingredient_id,))
        _, _, other_review, other_candidates = self.pending_review((ingredient_id,), raw="other")
        with self.assertRaises(IngredientMappingReviewError) as missing:
            IngredientMappingReviewService().decide(review_id, "accepted")
        self.assertEqual(missing.exception.status, 422)
        with self.assertRaises(IngredientMappingReviewError) as foreign:
            IngredientMappingReviewService().decide(review_id, "accepted", other_candidates[0])
        self.assertEqual(foreign.exception.status, 404)
        self.assertEqual(self.state(review_id)[0], "pending")
        self.assertEqual(self.state(other_review)[0], "pending")

    def test_terminal_review_cannot_be_changed(self):
        ingredient_id = self.canonical()
        _, _, review_id, candidate_ids = self.pending_review((ingredient_id,))
        IngredientMappingReviewService().decide(review_id, "accepted", candidate_ids[0])
        before = self.state(review_id)
        with self.assertRaises(IngredientMappingReviewError) as caught:
            IngredientMappingReviewService().decide(review_id, "rejected")
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(self.state(review_id), before)

    def test_zero_candidate_can_be_ambiguous_or_rejected_but_not_accepted(self):
        for decision in ("ambiguous", "rejected"):
            _, _, review_id, _ = self.pending_review((), raw=decision)
            IngredientMappingReviewService().decide(review_id, decision)
            self.assertEqual(self.state(review_id)[0], decision)
        _, _, review_id, _ = self.pending_review((), raw="accept")
        with self.assertRaises(IngredientMappingReviewError):
            IngredientMappingReviewService().decide(review_id, "accepted", 999999999)
        self.assertEqual(self.state(review_id)[0], "pending")

    def test_final_failure_rolls_back_every_table(self):
        ingredient_id = self.canonical()
        _, _, review_id, candidate_ids = self.pending_review((ingredient_id,))
        service = IngredientMappingReviewService(repository=FailingDecisionRepository())
        with self.assertRaisesRegex(RuntimeError, "forced final"):
            service.decide(review_id, "accepted", candidate_ids[0])
        state = self.state(review_id)
        self.assertEqual((state[0], state[4], state[5], state[8]), ("pending", None, "needs_review", 0))

    def test_two_concurrent_decisions_have_one_winner_and_one_conflict(self):
        first, second = self.canonical(), self.canonical()
        _, _, review_id, candidate_ids = self.pending_review((first, second))
        barrier = threading.Barrier(2)
        outcomes = []
        lock = threading.Lock()

        def decide(candidate_id):
            barrier.wait()
            try:
                IngredientMappingReviewService().decide(review_id, "accepted", candidate_id)
                outcome = "accepted"
            except IngredientMappingReviewError as exc:
                outcome = exc.status
            with lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=decide, args=(candidate_id,)) for candidate_id in candidate_ids]
        for thread in threads: thread.start()
        for thread in threads: thread.join(15)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertCountEqual(outcomes, ["accepted", 409])
        state = self.state(review_id)
        self.assertEqual((state[0], state[5], state[8]), ("accepted", "accepted", 1))
        self.assertIn(state[4], (first, second))


if __name__ == "__main__":
    unittest.main()
