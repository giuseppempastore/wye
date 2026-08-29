import os
import threading
import unittest
import uuid

from app.db import get_connection
from app.repositories.ingredient_mappings import PostgresIngredientMappingRepository
from app.services.ingredient_candidates import (
    CandidateGenerationResult,
    IngredientCandidate,
)
from app.services.deterministic_ingredient_resolver import (
    DeterministicResolutionResult,
)
from app.services.ingredient_mappings import (
    IngredientMappingError,
    IngredientMappingService,
)


class NeverResolve:
    def resolve(self, candidates):
        return DeterministicResolutionResult(resolved=False)


class StubCandidateGenerator:
    def __init__(self, candidates_by_text=None):
        self.candidates_by_text = candidates_by_text or {}

    def generate(self, normalized_text, detected_language=None):
        return CandidateGenerationResult(
            normalized_text=normalized_text,
            candidates=tuple(self.candidates_by_text.get(normalized_text, ())),
        )


class FailingCandidateRepository(PostgresIngredientMappingRepository):
    def insert_candidates(self, cursor, review_id, candidates):
        raise RuntimeError("forced candidate persistence failure")


class FailingResolutionRepository(PostgresIngredientMappingRepository):
    def apply_deterministic_resolution(self, *args, **kwargs):
        super().apply_deterministic_resolution(*args, **kwargs)
        raise RuntimeError("forced final resolution failure")


@unittest.skipUnless(
    os.environ.get("WYE_TEST_DATABASE"),
    "requires WYE_TEST_DATABASE pointing to an isolated database migrated to 0006",
)
class IngredientMappingServiceTests(unittest.TestCase):
    def setUp(self):
        self.connection = get_connection()
        self.product_ids = []
        self.storage_ids = []
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
                    cursor.execute(
                        "DELETE FROM product_ingredients WHERE product_id = ANY(%s)",
                        (self.product_ids,),
                    )
                    cursor.execute(
                        "DELETE FROM product_label_documents WHERE product_image_id IN "
                        "(SELECT id FROM product_images WHERE product_id = ANY(%s))",
                        (self.product_ids,),
                    )
                    cursor.execute(
                        "DELETE FROM product_images WHERE product_id = ANY(%s)",
                        (self.product_ids,),
                    )
                    cursor.execute(
                        "DELETE FROM products WHERE id = ANY(%s)",
                        (self.product_ids,),
                    )
                if self.storage_ids:
                    cursor.execute(
                        "DELETE FROM storage_objects WHERE id = ANY(%s)",
                        (self.storage_ids,),
                    )
                if self.ingredient_ids:
                    cursor.execute(
                        "DELETE FROM ingredients WHERE id = ANY(%s)",
                        (self.ingredient_ids,),
                    )
            self.connection.commit()
        finally:
            self.connection.close()

    def product(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO products (barcode, product_name, category) "
                "VALUES (%s, 'Phase 5.4', 'food') RETURNING id",
                (f"mapping-service-{uuid.uuid4().hex}",),
            )
            product_id = cursor.fetchone()[0]
        self.connection.commit()
        self.product_ids.append(product_id)
        return product_id

    def canonical(self, name=None):
        name = name or f"canonical-{uuid.uuid4().hex}"
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ingredients (canonical_name) VALUES (%s) RETURNING id",
                (name,),
            )
            ingredient_id = cursor.fetchone()[0]
        self.connection.commit()
        self.ingredient_ids.append(ingredient_id)
        return ingredient_id

    def extraction_run(self, product_id, image_type="ingredients", status="succeeded", items=()):
        suffix = uuid.uuid4().hex
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO storage_objects (storage_provider, bucket, object_key) "
                "VALUES ('test', 'phase54', %s) RETURNING id",
                (f"phase54/{suffix}",),
            )
            storage_id = cursor.fetchone()[0]
            self.storage_ids.append(storage_id)
            cursor.execute(
                "INSERT INTO product_images "
                "(product_id, image_type, storage_object_id, mime_type, checksum, source, status) "
                "VALUES (%s, %s, %s, 'image/jpeg', %s, 'user_submission', 'active') "
                "RETURNING id",
                (product_id, image_type, storage_id, suffix.ljust(64, "a")[:64]),
            )
            image_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO product_label_documents "
                "(product_image_id, source_type, document_type) "
                "VALUES (%s, 'image_derived', %s) RETURNING id",
                (image_id, image_type),
            )
            document_id = cursor.fetchone()[0]
            error_code = "test_failure" if status == "failed" else None
            completed = status in {"succeeded", "failed", "superseded"}
            cursor.execute(
                "INSERT INTO label_extraction_runs "
                "(label_document_id, extraction_method, run_status, error_code, completed_at) "
                "VALUES (%s, 'deterministic', %s, %s, "
                "CASE WHEN %s THEN NOW() ELSE NULL END) RETURNING id",
                (document_id, status, error_code, completed),
            )
            run_id = cursor.fetchone()[0]
            item_ids = []
            for position, (item_type, raw_text, language, structured) in enumerate(items, 1):
                cursor.execute(
                    "INSERT INTO label_extraction_items "
                    "(extraction_run_id, item_type, raw_text, detected_language, "
                    "structured_value, position_in_document) "
                    "VALUES (%s, %s, %s, %s, %s::jsonb, %s) RETURNING id",
                    (run_id, item_type, raw_text, language, structured, position),
                )
                item_ids.append(cursor.fetchone()[0])
        self.connection.commit()
        return run_id, item_ids

    @staticmethod
    def candidate(
        ingredient_id,
        confidence=1.0,
        rationale="exact accepted alias match",
        match_type="exact_accepted_alias",
    ):
        return IngredientCandidate(
            ingredient_id=ingredient_id,
            canonical_name="Canonical",
            candidate_method="deterministic",
            candidate_confidence=confidence,
            rationale=rationale,
            match_type=match_type,
        )

    def service(self, candidates=None, repository=None, resolver=None):
        return IngredientMappingService(
            candidate_generator=StubCandidateGenerator(candidates),
            resolver=resolver or NeverResolve(),
            mapping_repository=repository,
        )

    def auto_service(self, candidates=None, repository=None):
        return IngredientMappingService(
            candidate_generator=StubCandidateGenerator(candidates),
            mapping_repository=repository,
        )

    def mapping_rows(self, product_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT pi.id, pi.ingredient_id, pi.raw_name, pi.normalized_text, "
                "pi.detected_language, pi.position_in_list, pi.mapping_method, "
                "pi.mapping_status, pi.mapping_provenance, r.id, r.review_status "
                "FROM product_ingredients pi "
                "JOIN ingredient_mapping_reviews r ON r.product_ingredient_id = pi.id "
                "WHERE pi.product_id = %s ORDER BY pi.position_in_list",
                (product_id,),
            )
            return cursor.fetchall()

    def test_succeeded_ingredient_run_materializes_only_ingredient_items(self):
        product_id = self.product()
        run_id, item_ids = self.extraction_run(
            product_id,
            items=(
                ("ingredient_list", "Sugar, salt", "en", "{}"),
                ("ingredient", "  SUGAR ", "en", '{"quantity":"10%"}'),
                ("allergen", "milk", "en", "{}"),
                ("nutrition", "energy", "en", "{}"),
                ("ingredient", "Sea\n Salt", "en", "{}"),
            ),
        )
        result = self.service().map_run(product_id, run_id)
        rows = self.mapping_rows(product_id)
        self.assertEqual(len(result.mappings), 2)
        self.assertEqual([row[2] for row in rows], ["  SUGAR ", "Sea\n Salt"])
        self.assertEqual([row[3] for row in rows], ["sugar", "sea salt"])
        self.assertEqual([row[5] for row in rows], [2, 5])
        self.assertEqual([item.label_extraction_item_id for item in result.mappings], [item_ids[1], item_ids[4]])
        provenance = rows[0][8]
        self.assertEqual(provenance["normalization_version"], "ingredient_normalization_v1")
        self.assertEqual(provenance["candidate_generation_version"], "ingredient_candidate_generation_v1")
        self.assertEqual(provenance["extracted_quantity"], "10%")

    def test_invalid_run_type_status_and_ownership_are_rejected(self):
        product_id = self.product()
        other_product = self.product()
        nutrition_run, _ = self.extraction_run(product_id, "nutrition", items=(("nutrition", "energy", "en", "{}"),))
        failed_run, _ = self.extraction_run(other_product, status="failed", items=(("ingredient", "sugar", "en", "{}"),))
        with self.assertRaisesRegex(IngredientMappingError, "Only ingredient"):
            self.service().map_run(product_id, nutrition_run)
        with self.assertRaisesRegex(IngredientMappingError, "Only succeeded"):
            self.service().map_run(other_product, failed_run)
        with self.assertRaises(IngredientMappingError) as caught:
            self.service().map_run(product_id, failed_run)
        self.assertEqual(caught.exception.code, "extraction_not_found")

    def test_zero_candidates_creates_pending_review_without_selection(self):
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "unknown", "it", "{}"),))
        result = self.service().map_run(product_id, run_id)
        self.assertEqual(result.mappings[0].candidate_count, 0)
        row = self.mapping_rows(product_id)[0]
        self.assertIsNone(row[1])
        self.assertEqual(row[6:8], ("unmapped", "needs_review"))
        self.assertEqual(row[10], "pending")

    def test_one_candidate_is_persisted_pending_and_not_selected(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "sugar", "en", "{}"),))
        self.service({"sugar": [self.candidate(canonical_id)]}).map_run(product_id, run_id)
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT pi.ingredient_id, r.review_status, c.ingredient_id, "
                "c.candidate_confidence, c.rationale, c.is_selected "
                "FROM product_ingredients pi "
                "JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id "
                "JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id "
                "WHERE pi.product_id=%s",
                (product_id,),
            )
            row = cursor.fetchone()
        self.assertEqual(row, (None, "pending", canonical_id, 1.0, "exact accepted alias match", False))

    def test_multiple_and_duplicate_candidates_are_persisted_once_each(self):
        first = self.canonical()
        second = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "cocoa", "en", "{}"),))
        candidates = [self.candidate(first), self.candidate(first, 0.9), self.candidate(second, 0.87)]
        result = self.service({"cocoa": candidates}).map_run(product_id, run_id)
        self.assertEqual(result.mappings[0].candidate_count, 2)

    def test_rerun_reuses_product_ingredient_review_and_candidates(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "sugar", "en", "{}"),))
        service = self.service({"sugar": [self.candidate(canonical_id)]})
        first = service.map_run(product_id, run_id)
        second = service.map_run(product_id, run_id)
        self.assertEqual(first.mappings[0].product_ingredient_id, second.mappings[0].product_ingredient_id)
        self.assertEqual(first.mappings[0].review_id, second.mappings[0].review_id)
        self.assertFalse(second.mappings[0].created)
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM product_ingredients WHERE product_id=%s", (product_id,))
            self.assertEqual(cursor.fetchone()[0], 1)
            cursor.execute("SELECT count(*) FROM ingredient_mapping_reviews WHERE product_ingredient_id=%s", (first.mappings[0].product_ingredient_id,))
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_concluded_review_is_not_reopened_or_overwritten(self):
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "sugar", "en", "{}"),))
        first = self.service().map_run(product_id, run_id)
        with self.connection.cursor() as cursor:
            cursor.execute("UPDATE ingredient_mapping_reviews SET review_status='rejected', reviewed_at=NOW() WHERE id=%s", (first.mappings[0].review_id,))
        self.connection.commit()
        second = self.service().map_run(product_id, run_id)
        self.assertEqual(second.mappings[0].review_id, first.mappings[0].review_id)
        self.assertEqual(second.mappings[0].review_status, "rejected")

    def test_failure_rolls_back_product_ingredient_review_and_candidates(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "sugar", "en", "{}"),))
        service = self.service(
            {"sugar": [self.candidate(canonical_id)]},
            FailingCandidateRepository(),
        )
        with self.assertRaisesRegex(RuntimeError, "forced candidate"):
            service.map_run(product_id, run_id)
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM product_ingredients WHERE product_id=%s", (product_id,))
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_catalog_tables_are_not_modified(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "sugar", "en", "{}"),))
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM ingredients")
            ingredients_before = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM ingredient_aliases")
            aliases_before = cursor.fetchone()[0]
        self.service({"sugar": [self.candidate(canonical_id)]}).map_run(product_id, run_id)
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM ingredients")
            self.assertEqual(cursor.fetchone()[0], ingredients_before)
            cursor.execute("SELECT count(*) FROM ingredient_aliases")
            self.assertEqual(cursor.fetchone()[0], aliases_before)

    def test_concurrent_rerun_leaves_one_materialization_and_pending_review(self):
        product_id = self.product()
        run_id, _ = self.extraction_run(product_id, items=(("ingredient", "sugar", "en", "{}"),))
        results = []
        errors = []

        def worker():
            try:
                results.append(self.service().map_run(product_id, run_id))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM product_ingredients WHERE product_id=%s", (product_id,))
            self.assertEqual(cursor.fetchone()[0], 1)
            cursor.execute("SELECT count(*) FROM ingredient_mapping_reviews WHERE review_status='pending' AND product_ingredient_id IN (SELECT id FROM product_ingredients WHERE product_id=%s)", (product_id,))
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_unique_exact_canonical_is_auto_accepted_atomically(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(
            product_id, items=(("ingredient", "sugar", "en", "{}"),)
        )
        exact = self.candidate(
            canonical_id,
            rationale="exact canonical normalized match",
            match_type="exact_canonical",
        )
        result = self.auto_service({"sugar": [exact]}).map_run(product_id, run_id)
        self.assertEqual(result.mappings[0].review_status, "accepted")
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pi.ingredient_id, pi.mapping_status, pi.mapping_method,
                       pi.mapping_provenance, r.review_status, r.reviewed_at,
                       r.reviewed_by, r.review_provenance,
                       count(*) FILTER (WHERE c.is_selected)
                FROM product_ingredients pi
                JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id
                JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id
                WHERE pi.product_id=%s
                GROUP BY pi.id, r.id
                """,
                (product_id,),
            )
            row = cursor.fetchone()
        self.assertEqual(row[0:3], (canonical_id, "accepted", "deterministic_alias"))
        self.assertEqual(row[4], "accepted")
        self.assertIsNotNone(row[5])
        self.assertIsNone(row[6])
        self.assertEqual(row[8], 1)
        for provenance in (row[3], row[7]):
            self.assertEqual(provenance["resolution_type"], "deterministic_auto")
            self.assertEqual(provenance["resolution_reason"], "exact_canonical")
            self.assertEqual(
                provenance["normalization_version"], "ingredient_normalization_v1"
            )
            self.assertEqual(
                provenance["candidate_generation_version"],
                "ingredient_candidate_generation_v1",
            )

    def test_unique_exact_alias_and_same_id_exact_evidence_auto_accept(self):
        canonical_id = self.canonical()
        for candidates in (
            [self.candidate(canonical_id)],
            [
                self.candidate(
                    canonical_id,
                    rationale="exact canonical normalized match",
                    match_type="exact_canonical",
                ),
                self.candidate(canonical_id),
            ],
        ):
            with self.subTest(candidate_count=len(candidates)):
                product_id = self.product()
                run_id, _ = self.extraction_run(
                    product_id, items=(("ingredient", "e330", "it", "{}"),)
                )
                result = self.auto_service({"e330": candidates}).map_run(
                    product_id, run_id
                )
                self.assertEqual(result.mappings[0].review_status, "accepted")
                self.assertEqual(result.mappings[0].candidate_count, 1)

    def test_unique_exact_with_fuzzy_candidates_auto_accepts_only_exact(self):
        exact_id = self.canonical()
        fuzzy_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(
            product_id, items=(("ingredient", "citric acid", "en", "{}"),)
        )
        candidates = [
            self.candidate(
                exact_id,
                rationale="exact canonical normalized match",
                match_type="exact_canonical",
            ),
            self.candidate(
                fuzzy_id,
                confidence=0.949,
                rationale="fuzzy canonical name similarity",
                match_type="fuzzy_canonical",
            ),
        ]
        self.auto_service({"citric acid": candidates}).map_run(product_id, run_id)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.ingredient_id, c.is_selected
                FROM ingredient_mapping_review_candidates c
                JOIN ingredient_mapping_reviews r ON r.id=c.review_id
                JOIN product_ingredients pi ON pi.id=r.product_ingredient_id
                WHERE pi.product_id=%s ORDER BY c.ingredient_id
                """,
                (product_id,),
            )
            selected = dict(cursor.fetchall())
        self.assertEqual(selected, {exact_id: True, fuzzy_id: False})

    def test_distinct_exact_candidates_remain_pending(self):
        first = self.canonical()
        second = self.canonical()
        for candidates in (
            [
                self.candidate(
                    first,
                    rationale="exact canonical normalized match",
                    match_type="exact_canonical",
                ),
                self.candidate(second),
            ],
            [self.candidate(first), self.candidate(second)],
        ):
            with self.subTest(alias_only=candidates[0].match_type == "exact_accepted_alias"):
                product_id = self.product()
                run_id, _ = self.extraction_run(
                    product_id, items=(("ingredient", "ambiguous", "en", "{}"),)
                )
                result = self.auto_service({"ambiguous": candidates}).map_run(
                    product_id, run_id
                )
                self.assertEqual(result.mappings[0].review_status, "pending")
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT pi.ingredient_id, count(*) FILTER (WHERE c.is_selected)
                        FROM product_ingredients pi
                        JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id
                        JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id
                        WHERE pi.product_id=%s GROUP BY pi.id
                        """,
                        (product_id,),
                    )
                    self.assertEqual(cursor.fetchone(), (None, 0))

    def test_fuzzy_and_zero_candidates_never_auto_accept(self):
        fuzzy_id = self.canonical()
        cases = (
            [self.candidate(
                fuzzy_id, 0.999, "fuzzy canonical name similarity", "fuzzy_canonical"
            )],
            [
                self.candidate(
                    fuzzy_id, 0.949, "fuzzy canonical name similarity", "fuzzy_canonical"
                ),
                self.candidate(
                    self.canonical(), 0.94, "fuzzy accepted alias similarity",
                    "fuzzy_accepted_alias",
                ),
            ],
            [],
        )
        for candidates in cases:
            with self.subTest(candidate_count=len(candidates)):
                product_id = self.product()
                run_id, _ = self.extraction_run(
                    product_id, items=(("ingredient", "fuzzy", "en", "{}"),)
                )
                result = self.auto_service({"fuzzy": candidates}).map_run(
                    product_id, run_id
                )
                self.assertEqual(result.mappings[0].review_status, "pending")
                self.assertIsNone(self.mapping_rows(product_id)[0][1])

    def test_auto_accepted_rerun_is_stable(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(
            product_id, items=(("ingredient", "sugar", "en", "{}"),)
        )
        service = self.auto_service({"sugar": [self.candidate(canonical_id)]})
        first = service.map_run(product_id, run_id)
        second = service.map_run(product_id, run_id)
        self.assertEqual(first.mappings[0].review_id, second.mappings[0].review_id)
        self.assertEqual(second.mappings[0].review_status, "accepted")
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*), count(*) FILTER (WHERE c.is_selected)
                FROM ingredient_mapping_review_candidates c
                WHERE c.review_id=%s
                """,
                (first.mappings[0].review_id,),
            )
            self.assertEqual(cursor.fetchone(), (1, 1))

    def test_ambiguous_and_rejected_reviews_are_not_reconsidered(self):
        canonical_id = self.canonical()
        for terminal_status in ("ambiguous", "rejected"):
            with self.subTest(status=terminal_status):
                product_id = self.product()
                run_id, _ = self.extraction_run(
                    product_id, items=(("ingredient", "sugar", "en", "{}"),)
                )
                initial = self.service().map_run(product_id, run_id)
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE ingredient_mapping_reviews SET review_status=%s, "
                        "reviewed_at=NOW() WHERE id=%s",
                        (terminal_status, initial.mappings[0].review_id),
                    )
                self.connection.commit()
                rerun = self.auto_service(
                    {"sugar": [self.candidate(canonical_id)]}
                ).map_run(product_id, run_id)
                self.assertEqual(rerun.mappings[0].review_status, terminal_status)
                self.assertIsNone(self.mapping_rows(product_id)[0][1])

    def test_final_resolution_failure_rolls_back_everything(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(
            product_id, items=(("ingredient", "sugar", "en", "{}"),)
        )
        service = self.auto_service(
            {"sugar": [self.candidate(canonical_id)]},
            FailingResolutionRepository(),
        )
        with self.assertRaisesRegex(RuntimeError, "forced final resolution"):
            service.map_run(product_id, run_id)
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM product_ingredients WHERE product_id=%s",
                (product_id,),
            )
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_concurrent_exact_resolution_converges(self):
        canonical_id = self.canonical()
        product_id = self.product()
        run_id, _ = self.extraction_run(
            product_id, items=(("ingredient", "sugar", "en", "{}"),)
        )
        results = []
        errors = []

        def worker():
            try:
                results.append(
                    self.auto_service(
                        {"sugar": [self.candidate(canonical_id)]}
                    ).map_run(product_id, run_id)
                )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(DISTINCT pi.id), count(DISTINCT r.id),
                       count(*) FILTER (WHERE c.is_selected),
                       min(r.review_status), min(pi.ingredient_id)
                FROM product_ingredients pi
                JOIN ingredient_mapping_reviews r ON r.product_ingredient_id=pi.id
                JOIN ingredient_mapping_review_candidates c ON c.review_id=r.id
                WHERE pi.product_id=%s
                """,
                (product_id,),
            )
            self.assertEqual(
                cursor.fetchone(), (1, 1, 1, "accepted", canonical_id)
            )


if __name__ == "__main__":
    unittest.main()





