import unittest

from app.services.deterministic_ingredient_resolver import (
    DeterministicIngredientResolver,
)
from app.services.ingredient_candidates import IngredientCandidate


def candidate(ingredient_id, match_type, confidence=1.0):
    rationale = {
        "exact_canonical": "exact canonical normalized match",
        "exact_accepted_alias": "exact accepted alias match",
        "fuzzy_canonical": "fuzzy canonical name similarity",
        "fuzzy_accepted_alias": "fuzzy accepted alias similarity",
    }[match_type]
    return IngredientCandidate(
        ingredient_id=ingredient_id,
        canonical_name=f"Ingredient {ingredient_id}",
        candidate_method="deterministic",
        candidate_confidence=confidence,
        rationale=rationale,
        match_type=match_type,
    )


class DeterministicIngredientResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = DeterministicIngredientResolver()

    def test_unique_exact_canonical_resolves(self):
        result = self.resolver.resolve([candidate(1, "exact_canonical")])
        self.assertTrue(result.resolved)
        self.assertEqual((result.ingredient_id, result.reason), (1, "exact_canonical"))

    def test_unique_exact_accepted_alias_resolves(self):
        result = self.resolver.resolve([candidate(1, "exact_accepted_alias")])
        self.assertTrue(result.resolved)
        self.assertEqual(result.reason, "exact_accepted_alias")

    def test_same_ingredient_with_two_exact_evidences_resolves_once(self):
        result = self.resolver.resolve(
            [candidate(1, "exact_canonical"), candidate(1, "exact_accepted_alias")]
        )
        self.assertTrue(result.resolved)
        self.assertEqual(result.ingredient_id, 1)
        self.assertEqual(result.reason, "exact_canonical")

    def test_unique_exact_is_not_blocked_by_fuzzy_candidates(self):
        result = self.resolver.resolve(
            [
                candidate(1, "exact_accepted_alias"),
                candidate(2, "fuzzy_canonical", 0.949),
                candidate(3, "fuzzy_accepted_alias", 0.94),
            ]
        )
        self.assertTrue(result.resolved)
        self.assertEqual(result.ingredient_id, 1)

    def test_distinct_exact_candidates_are_ambiguous(self):
        result = self.resolver.resolve(
            [candidate(1, "exact_canonical"), candidate(2, "exact_accepted_alias")]
        )
        self.assertFalse(result.resolved)

    def test_ambiguous_exact_aliases_are_not_resolved(self):
        result = self.resolver.resolve(
            [candidate(1, "exact_accepted_alias"), candidate(2, "exact_accepted_alias")]
        )
        self.assertFalse(result.resolved)

    def test_single_high_confidence_fuzzy_is_never_resolved(self):
        result = self.resolver.resolve([candidate(1, "fuzzy_canonical", 0.999)])
        self.assertFalse(result.resolved)

    def test_multiple_fuzzy_and_zero_candidates_are_not_resolved(self):
        self.assertFalse(
            self.resolver.resolve(
                [candidate(1, "fuzzy_canonical"), candidate(2, "fuzzy_accepted_alias")]
            ).resolved
        )
        self.assertFalse(self.resolver.resolve([]).resolved)


if __name__ == "__main__":
    unittest.main()
