import unittest

from app.services.ai_normalizer import parse_ai_response, normalize_photo_text


class AiNormalizerTests(unittest.TestCase):
    def test_parse_ai_response(self):
        payload = {
            "ingredients": [
                "sugar",
                "cocoa powder",
                "milk powder",
            ],
            "nutrition": {
                "energy_kcal": 150,
                "protein_g": 8,
                "carbs_g": 24,
                "fat_g": 6,
                "sugar_g": 12,
                "fiber_g": 3,
                "sodium_mg": 90,
            },
        }

        result = parse_ai_response(payload)

        self.assertEqual(result["ingredients"], ["sugar", "cocoa powder", "milk powder"])
        self.assertEqual(result["nutrition"]["energy_kcal"], 150)
        self.assertEqual(result["nutrition"]["protein_g"], 8)
        self.assertEqual(result["nutrition"]["carbs_g"], 24)
        self.assertEqual(result["nutrition"]["fat_g"], 6)

    def test_normalize_photo_text_ignores_nutrition_values_in_ingredient_list(self):
        raw_text = """
        Ingredienti:
        farina di grano, zucchero, latte, cacao in polvere,
        Nutrizione per 100 g:
        energia 420 kcal, proteine 12 g, carboidrati 55 g, grassi 18 g
        """

        result = normalize_photo_text(raw_text)

        self.assertIn("farina di grano", " ".join(result["ingredients"]).lower())
        self.assertIn("zucchero", " ".join(result["ingredients"]).lower())
        self.assertNotIn("420", " ".join(result["ingredients"]))
        self.assertNotIn("kcal", " ".join(result["ingredients"]).lower())
        self.assertIn("energy_kcal", result["nutrition"])


if __name__ == "__main__":
    unittest.main()
