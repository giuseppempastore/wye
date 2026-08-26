import unittest

from app.data.ingredients import normalize_barcode, normalize_ingredient


class BarcodeAndIngredientsTests(unittest.TestCase):
    def test_extract_valid_barcode_from_ocr_text(self):
        raw_text = """
        INGREDIENTS
        sugar, cocoa powder, milk powder
        NUTRITION
        energy 420 kcal  protein 12g  carbs 55g
        8718206112001
        """

        self.assertEqual(normalize_barcode(raw_text), "8718206112001")

    def test_normalize_italian_ingredient_names_to_english(self):
        self.assertEqual(normalize_ingredient("zucchero"), "sugar")
        self.assertEqual(normalize_ingredient("cacao in polvere"), "cocoa powder")
        self.assertEqual(normalize_ingredient("latte"), "milk")


if __name__ == "__main__":
    unittest.main()
