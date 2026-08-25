import unittest

from app.data.ingredients import parse_ingredient_list
from app.services.ai_normalizer import (
    _fallback_parse,
    _infer_product_metadata,
    analyze_image_with_ai,
    parse_ai_response,
    normalize_photo_text,
)


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

        self.assertIn("wheat flour", " ".join(result["ingredients"]).lower())
        self.assertIn("sugar", " ".join(result["ingredients"]).lower())
        self.assertIn("milk", " ".join(result["ingredients"]).lower())
        self.assertIn("cocoa powder", " ".join(result["ingredients"]).lower())
        self.assertNotIn("420", " ".join(result["ingredients"]))
        self.assertNotIn("kcal", " ".join(result["ingredients"]).lower())
        self.assertIn("energy_kcal", result["nutrition"])

    def test_parse_ai_response_normalizes_ingredients_to_english(self):
        payload = {
            "ingredients": ["zucchero", "cacao in polvere", "latte"],
            "nutrition": {
                "energy_kcal": 420,
                "protein_g": 12,
                "carbs_g": 55,
                "fat_g": 18,
            },
        }

        result = parse_ai_response(payload)

        self.assertEqual(result["ingredients"], ["sugar", "cocoa powder", "milk"])
        self.assertEqual(result["nutrition"]["energy_kcal"], 420)

    def test_analyze_image_with_ai_falls_back_to_ocr_normalization(self):
        result = analyze_image_with_ai(
            "data:image/jpeg;base64,AAAA",
            "Ingredienti: zucchero, cacao in polvere, latte\nEnergia 420 kcal",
        )

        self.assertIn("sugar", result["ingredients"])
        self.assertIn("cocoa powder", result["ingredients"])
        self.assertIn("milk", result["ingredients"])
        self.assertIn("energy_kcal", result["nutrition"])

    def test_parse_ai_response_extracts_product_metadata_and_nutrition(self):
        payload = {
            "product_name": "Granola Bio",
            "brand_name": "Natura Bio",
            "category": "food",
            "ingredients": ["zucchero", "latte"],
            "nutrition": {
                "energy_kcal": 420,
                "protein_g": 12,
                "carbs_g": 55,
                "fat_g": 18,
                "sugar_g": 10,
                "fiber_g": 5,
                "sodium_mg": 80,
            },
        }

        result = parse_ai_response(payload)

        self.assertEqual(result["product_name"], "Granola Bio")
        self.assertEqual(result["brand_name"], "Natura Bio")
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["ingredients"], ["sugar", "milk"])
        self.assertEqual(result["nutrition"]["energy_kcal"], 420)

    def test_parse_ingredient_list_filters_noisy_ocr_tokens(self):
        raw_text = """
        Ingredienti
        1. ero
        2. tto
        3. mia
        4. olo
        5. del
        6. one
        7. nti
        8. dichiarazione nutrizionale
        9. la confezione contiene 12 biscotti
        10. c r a
        11. con cac
        12. coltivaz
        13. sosten
        14. senza
        15. icooki
        16. specifica
        17. leces
        18. oats, sugar, milk
        """

        result = parse_ingredient_list(raw_text)

        self.assertNotIn("ero", [item.lower() for item in result])
        self.assertNotIn("dichiarazione nutrizionale", [item.lower() for item in result])
        self.assertNotIn("biscotti", [item.lower() for item in result])
        self.assertIn("oats", [item.lower() for item in result])
        self.assertIn("sugar", [item.lower() for item in result])
        self.assertIn("milk", [item.lower() for item in result])

    def test_infer_product_metadata_prefers_main_title_over_side_text(self):
        raw_text = """
        Via Roma 14
        Ingredients: wheat, sugar
        Granola Bio Cacao 500g
        Made in Italy
        """

        result = _infer_product_metadata(raw_text)

        self.assertEqual(result["product_name"], "Granola Bio Cacao 500g")
        self.assertEqual(result["brand_name"], "Granola Bio Cacao 500g")

    def test_infer_product_metadata_separates_brand_from_product_name(self):
        raw_text = """
        Bio Natura
        Granola Bio Cacao 500g
        Ingredients: wheat, sugar
        """

        result = _infer_product_metadata(raw_text)

        self.assertEqual(result["product_name"], "Granola Bio Cacao 500g")
        self.assertEqual(result["brand_name"], "Bio Natura")

    def test_fallback_parse_does_not_add_product_title_to_ingredients(self):
        raw_text = """
        Bio Natura
        Granola Bio Cacao
        Ingredients: wheat, sugar, milk
        """

        result = _fallback_parse(raw_text)

        self.assertNotIn("Granola Bio Cacao", [item.lower() for item in result["ingredients"]])
        self.assertIn("wheat", [item.lower() for item in result["ingredients"]])
        self.assertIn("sugar", [item.lower() for item in result["ingredients"]])

    def test_fallback_parse_ignores_ingredient_lines_as_product_title(self):
        raw_text = """
        Ingredienti:
        farina di grano, zucchero, latte, cacao in polvere,
        Nutrizione per 100 g:
        energia 420 kcal, proteine 12 g, carboidrati 55 g, grassi 18 g
        """

        result = _fallback_parse(raw_text)

        self.assertIn("wheat flour", [item.lower() for item in result["ingredients"]])
        self.assertIn("energy_kcal", result["nutrition"])
        self.assertNotEqual(result.get("product_name", "").lower(), "farina di grano, zucchero, latte, cacao in polvere,")


if __name__ == "__main__":
    unittest.main()
