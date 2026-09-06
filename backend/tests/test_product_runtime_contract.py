import unittest

from app.main import _coerce_nutrition_values, _unavailable_score_view


class ProductRuntimeContractTests(unittest.TestCase):
    def test_missing_nutrition_is_allowed_and_remains_empty(self):
        self.assertEqual(_coerce_nutrition_values(None), {})
        self.assertEqual(_coerce_nutrition_values({}), {})

    def test_unavailable_score_state_contains_no_numeric_score(self):
        score_view = _unavailable_score_view()

        self.assertEqual(
            score_view["ingredient_goodness_percent"]["evaluability_status"],
            "not_computable",
        )
        self.assertIsNone(
            score_view["ingredient_goodness_percent"]["score_value"]
        )
        self.assertEqual(
            score_view["nutrition_goodness_percent"]["evaluability_status"],
            "not_computable",
        )
        self.assertIsNone(
            score_view["nutrition_goodness_percent"]["score_value"]
        )
        self.assertEqual(score_view["overall_score"]["availability"], "deferred")
        self.assertNotIn("score_value", score_view["overall_score"])


if __name__ == "__main__":
    unittest.main()
