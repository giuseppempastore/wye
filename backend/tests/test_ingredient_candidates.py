import unittest

from app.repositories.ingredient_catalog import (
    CatalogAlias,
    CatalogIngredient,
    IngredientCatalog,
)
from app.services.ingredient_candidates import (
    FUZZY_SIMILARITY_THRESHOLD,
    MAX_CANDIDATES,
    IngredientCandidateGenerator,
)


class FakeCatalogRepository:
    def __init__(self, ingredients=(), aliases=()):
        self.catalog = IngredientCatalog(tuple(ingredients), tuple(aliases))
        self.load_count = 0

    def load_catalog(self):
        self.load_count += 1
        return self.catalog


def ingredient(ingredient_id, name, status="active"):
    return CatalogIngredient(ingredient_id, name, status)


def alias(ingredient_id, text, status="accepted", language="en"):
    return CatalogAlias(ingredient_id, text, language, status)


class IngredientCandidateGeneratorTests(unittest.TestCase):
    def generate(self, text, ingredients=(), aliases=(), **kwargs):
        repository = FakeCatalogRepository(ingredients, aliases)
        result = IngredientCandidateGenerator(repository, **kwargs).generate(text)
        self.assertEqual(repository.load_count, 1)
        return result

    def test_exact_canonical_unique_match(self):
        result = self.generate("citric acid", [ingredient(1, "Citric Acid")])
        self.assertEqual([item.ingredient_id for item in result.candidates], [1])
        self.assertEqual(result.candidates[0].match_type, "exact_canonical")
        self.assertEqual(result.candidates[0].candidate_confidence, 1.0)
        self.assertEqual(
            result.candidates[0].rationale, "exact canonical normalized match"
        )

    def test_exact_accepted_alias_unique_match(self):
        result = self.generate(
            "acido citrico",
            [ingredient(1, "Citric Acid")],
            [alias(1, "acido citrico", language="it")],
        )
        self.assertEqual(result.candidates[0].match_type, "exact_accepted_alias")
        self.assertEqual(result.candidates[0].rationale, "exact accepted alias match")

    def test_non_accepted_and_inactive_records_are_ignored(self):
        result = self.generate(
            "acido citrico",
            [ingredient(1, "Citric Acid"), ingredient(2, "Acido Citrico", "deprecated")],
            [alias(1, "acido citrico", "legacy_unreviewed")],
        )
        self.assertEqual(result.candidates, ())

    def test_canonical_name_uses_v1_normalization(self):
        result = self.generate("acido citrico", [ingredient(1, "  ACIDO   CITRICO ")])
        self.assertEqual(result.candidates[0].match_type, "exact_canonical")

    def test_e_number_resolves_only_through_catalog_data(self):
        alias_result = self.generate(
            "e330", [ingredient(1, "Citric Acid")], [alias(1, "E-330")]
        )
        canonical_result = self.generate("e330", [ingredient(2, "E 330")])
        no_data_result = self.generate("e330", [ingredient(3, "Other")])
        self.assertEqual(alias_result.candidates[0].ingredient_id, 1)
        self.assertEqual(canonical_result.candidates[0].ingredient_id, 2)
        self.assertEqual(no_data_result.candidates, ())

    def test_no_candidates_is_valid(self):
        self.assertEqual(
            self.generate("unlisted ingredient", [ingredient(1, "salt")]).candidates,
            (),
        )

    def test_ambiguous_exact_alias_returns_all_canonical_ingredients(self):
        result = self.generate(
            "shared alias",
            [ingredient(2, "Beta"), ingredient(1, "Alpha")],
            [alias(2, "shared alias", language="en"), alias(1, "shared alias", language="it")],
        )
        self.assertEqual([item.ingredient_id for item in result.candidates], [1, 2])
        self.assertTrue(all(item.candidate_confidence == 1.0 for item in result.candidates))

    def test_fuzzy_canonical_match(self):
        result = self.generate("citrc acid", [ingredient(1, "citric acid")])
        self.assertEqual(result.candidates[0].match_type, "fuzzy_canonical")
        self.assertEqual(result.candidates[0].rationale, "fuzzy canonical name similarity")

    def test_fuzzy_alias_match(self):
        result = self.generate(
            "lecitina soja",
            [ingredient(1, "Soy Lecithin")],
            [alias(1, "lecitina soia", language="it")],
        )
        self.assertEqual(result.candidates[0].match_type, "fuzzy_accepted_alias")
        self.assertEqual(result.candidates[0].rationale, "fuzzy accepted alias similarity")

    def test_fuzzy_below_threshold_is_excluded(self):
        result = self.generate("cocoa", [ingredient(1, "coconut oil")])
        self.assertEqual(result.candidates, ())
        self.assertEqual(FUZZY_SIMILARITY_THRESHOLD, 0.86)

    def test_exact_candidates_sort_before_fuzzy_candidates(self):
        result = self.generate(
            "citric acid",
            [ingredient(1, "citric acid"), ingredient(2, "citrc acid")],
        )
        self.assertEqual([item.ingredient_id for item in result.candidates], [1, 2])
        self.assertGreater(
            result.candidates[0].candidate_confidence,
            result.candidates[1].candidate_confidence,
        )

    def test_same_ingredient_is_deduplicated_using_strongest_evidence(self):
        result = self.generate(
            "citric acid",
            [ingredient(1, "Citric Acid")],
            [alias(1, "citric acid")],
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].match_type, "exact_canonical")

    def test_max_candidates_is_enforced_and_configurable(self):
        ingredients = [ingredient(index, f"citric acid {index}") for index in range(1, 9)]
        result = self.generate("citric acid", ingredients, fuzzy_threshold=0.7)
        self.assertEqual(MAX_CANDIDATES, 5)
        self.assertEqual(len(result.candidates), MAX_CANDIDATES)
        limited = self.generate("citric acid", ingredients, fuzzy_threshold=0.7, max_candidates=2)
        self.assertEqual(len(limited.candidates), 2)

    def test_confidence_is_always_normalized(self):
        result = self.generate(
            "citric acid",
            [ingredient(1, "citric acid"), ingredient(2, "citrc acid")],
        )
        self.assertTrue(
            all(0.0 <= item.candidate_confidence <= 1.0 for item in result.candidates)
        )

    def test_output_is_deterministic_regardless_of_catalog_order(self):
        ingredients = [ingredient(2, "citrc acid"), ingredient(1, "citric acids")]
        first = self.generate("citric acid", ingredients)
        second = self.generate("citric acid", reversed(ingredients))
        self.assertEqual(first, second)

    def test_language_is_a_tie_breaker_not_a_filter(self):
        repository = FakeCatalogRepository(
            [ingredient(1, "Beta"), ingredient(2, "Alpha")],
            [alias(1, "shared", language="it"), alias(2, "shared", language="en")],
        )
        result = IngredientCandidateGenerator(repository).generate("shared", "it")
        self.assertEqual([item.ingredient_id for item in result.candidates], [1, 2])

    def test_generation_is_read_only_and_does_not_create_mapping_objects(self):
        repository = FakeCatalogRepository(
            [ingredient(1, "Citric Acid")], [alias(1, "acido citrico", language="it")]
        )
        before = repository.catalog
        result = IngredientCandidateGenerator(repository).generate("acido citrico")
        self.assertEqual(repository.catalog, before)
        self.assertEqual(result.candidates[0].candidate_method, "deterministic")
        self.assertFalse(hasattr(result, "product_ingredient_id"))
        self.assertFalse(hasattr(result, "review_id"))

    def test_invalid_input_is_rejected(self):
        repository = FakeCatalogRepository()
        generator = IngredientCandidateGenerator(repository)
        for value in (None, "", " \n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                generator.generate(value)


if __name__ == "__main__":
    unittest.main()
