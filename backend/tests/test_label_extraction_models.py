import unittest
from pydantic import ValidationError

from app.extraction.models import LabelExtractionOutput
from app.extraction.prompts.label_extraction_v1 import PROMPT_HASH, PROMPT_ID


class LabelExtractionModelTests(unittest.TestCase):
    def test_valid_ingredients_preserve_order_raw_text_and_allergens(self):
        output = LabelExtractionOutput.model_validate({
            "document_type": "ingredients", "raw_text": "Ingredienti: acqua, sale. Allergeni: latte",
            "detected_languages": ["it"], "ingredient_list_text": "acqua, sale",
            "ingredients": [{"raw_text": "acqua", "quantity": None}, {"raw_text": "sale", "quantity": "2%"}],
            "allergens": [{"raw_text": "latte"}], "nutrition": [],
        })
        self.assertEqual([x.raw_text for x in output.ingredients], ["acqua", "sale"])
        self.assertEqual(output.ingredients[1].quantity, "2%")
        self.assertEqual(output.allergens[0].raw_text, "latte")

    def test_valid_partial_nutrition_preserves_basis(self):
        output = LabelExtractionOutput.model_validate({
            "document_type": "nutrition", "raw_text": "per 100 g energia 20 kcal", "detected_languages": ["it"],
            "ingredient_list_text": None, "ingredients": [], "allergens": [],
            "nutrition": [{"nutrient": "energy", "raw_label": "energia", "value": 20, "unit": "kcal",
                           "basis": {"type": "per_100_g", "quantity": 100, "unit": "g", "raw_text": "per 100 g"}}],
        })
        self.assertEqual(output.nutrition[0].basis.type, "per_100_g")
        self.assertEqual(len(output.nutrition), 1)

    def test_semantically_invalid_mixed_document_is_rejected(self):
        with self.assertRaises(ValidationError):
            LabelExtractionOutput.model_validate({
                "document_type": "nutrition", "raw_text": "x", "ingredient_list_text": "water",
                "detected_languages": [], "ingredients": [{"raw_text": "water", "quantity": None}], "allergens": [], "nutrition": [],
            })

    def test_missing_ingredient_list_and_unknown_nutrient_are_rejected(self):
        with self.assertRaises(ValidationError):
            LabelExtractionOutput.model_validate({"document_type": "ingredients", "raw_text": "x", "detected_languages": [],
                "ingredient_list_text": None, "ingredients": [], "allergens": [], "nutrition": []})
        with self.assertRaises(ValidationError):
            LabelExtractionOutput.model_validate({"document_type": "nutrition", "raw_text": "x", "detected_languages": [],
                "ingredient_list_text": None, "ingredients": [], "allergens": [], "nutrition": [
                {"nutrient": "cholesterol", "raw_label": "cholesterol", "value": 1, "unit": "g", "basis": None}]})

    def test_prompt_is_versioned_and_hashed(self):
        self.assertEqual(PROMPT_ID, "label_extraction_v1")
        self.assertEqual(len(PROMPT_HASH), 64)


if __name__ == "__main__": unittest.main()
