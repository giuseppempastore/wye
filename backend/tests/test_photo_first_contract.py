import unittest

from pydantic import ValidationError

from app.main import LocalLabelExtraction, _coerce_nutrition_values
from app.product_taxonomy import PRODUCT_CATEGORY_IDS, PRODUCT_TYPE_IDS


class PhotoFirstContractTests(unittest.TestCase):
    def test_controlled_taxonomy_ids_are_stable(self):
        self.assertEqual(
            PRODUCT_TYPE_IDS,
            {"food", "beverage", "supplement", "ingredient", "other"},
        )
        self.assertIn("sweets_snacks", PRODUCT_CATEGORY_IDS)
        self.assertIn("plant_based_alternatives", PRODUCT_CATEGORY_IDS)
        self.assertNotIn("snack", PRODUCT_TYPE_IDS)

    def test_local_ocr_contract_keeps_raw_separate_from_segment(self):
        extraction = LocalLabelExtraction(
            document_type="ingredients",
            raw_text="Ainesosat: past4, vesi",
            detected_language="fi",
            parser_version="photo_field_mapper_v2",
            segment_text="past4, vesi",
        )
        self.assertEqual(extraction.raw_text, "Ainesosat: past4, vesi")
        self.assertEqual(extraction.segment_text, "past4, vesi")
        self.assertIn("past4", extraction.segment_text)

    def test_unsafe_warning_is_rejected(self):
        with self.assertRaises(ValidationError):
            LocalLabelExtraction(
                document_type="nutrition",
                raw_text="Ravintosisältö 100 g",
                detected_language="fi",
                parser_version="photo_field_mapper_v2",
                warnings=["raw text must not be a warning"],
            )

    def test_salt_and_sodium_remain_distinct(self):
        values = _coerce_nutrition_values({"salt_g": "0,8", "sodium_mg": 15})
        self.assertEqual(values, {"salt_g": 0.8, "sodium_mg": 15.0})

    def test_kj_and_kcal_remain_distinct_and_implausible_values_fail(self):
        values = _coerce_nutrition_values(
            {"energy_kj": "840", "energy_kcal": "200"}
        )
        self.assertEqual(values, {"energy_kj": 840.0, "energy_kcal": 200.0})
        with self.assertRaises(Exception):
            _coerce_nutrition_values({"energy_kj": 4001})


if __name__ == "__main__":
    unittest.main()
