import unittest

from app.services.ingredient_normalizer import (
    INGREDIENT_NORMALIZATION_VERSION,
    IngredientNormalizer,
)


class IngredientNormalizerTests(unittest.TestCase):
    def setUp(self):
        self.normalizer = IngredientNormalizer()

    def normalized(self, text):
        return self.normalizer.normalize(text).normalized_text

    def test_result_preserves_raw_text_and_exposes_version(self):
        raw = "  ACIDO CITRICO "
        result = self.normalizer.normalize(raw)
        self.assertEqual(result.raw_text, raw)
        self.assertEqual(result.normalized_text, "acido citrico")
        self.assertEqual(result.normalization_version, "ingredient_normalization_v1")
        self.assertEqual(result.normalization_version, INGREDIENT_NORMALIZATION_VERSION)

    def test_casefold_and_trim(self):
        self.assertEqual(self.normalized("  LECITINA DI SOIA  "), "lecitina di soia")

    def test_collapses_spaces_tabs_and_newlines(self):
        self.assertEqual(
            self.normalized("\tAcido   \n  Citrico\r\n"),
            "acido citrico",
        )

    def test_unicode_is_canonicalized_without_removing_accents(self):
        decomposed = "CAFFE\u0300, pure\u0301, più"
        self.assertEqual(self.normalized(decomposed), "caffè, puré, più")

    def test_european_accented_characters_are_preserved(self):
        self.assertEqual(
            self.normalized("À È É Ì Ò Ù"),
            "à è é ì ò ù",
        )

    def test_typographic_apostrophes_are_canonicalized_not_removed(self):
        self.assertEqual(self.normalized("L’AROMA DʼARANCIA"), "l'aroma d'arancia")

    def test_typographic_dashes_are_canonicalized_not_removed(self):
        self.assertEqual(self.normalized("beta–carotene — naturale"), "beta-carotene - naturale")

    def test_e_number_graphic_variants_converge(self):
        for value in ("E330", "E 330", "E-330"):
            with self.subTest(value=value):
                self.assertEqual(self.normalized(value), "e330")

    def test_e_number_suffixes_are_preserved(self):
        for value in ("E160a", "E 160 a", "E-160-a"):
            with self.subTest(value=value):
                self.assertEqual(self.normalized(value), "e160a")

    def test_already_normalized_e_number_is_unchanged(self):
        self.assertEqual(self.normalized("e330"), "e330")

    def test_parentheses_commas_and_percentages_are_preserved(self):
        self.assertEqual(
            self.normalized("grassi vegetali (palma, girasole) 9%"),
            "grassi vegetali (palma, girasole) 9%",
        )

    def test_realistic_e_number_inside_ingredient_is_only_reformatted(self):
        self.assertEqual(
            self.normalized("Acido Citrico (E 330)"),
            "acido citrico (e330)",
        )

    def test_complex_ingredient_is_not_reinterpreted(self):
        raw = "Olio vegetale (colza, palma), aroma naturale"
        self.assertEqual(
            self.normalized(raw),
            "olio vegetale (colza, palma), aroma naturale",
        )

    def test_realistic_percentage_is_preserved(self):
        self.assertEqual(self.normalized("cacao in polvere 9%"), "cacao in polvere 9%")

    def test_already_normalized_string_is_unchanged(self):
        value = "grassi vegetali (palma, girasole)"
        self.assertEqual(self.normalized(value), value)

    def test_normalization_is_idempotent(self):
        inputs = (
            "  ACIDO   CITRICO (E 330) ",
            "L’AROMA–NATURALE",
            "grassi vegetali (palma,\n girasole) 9%",
        )
        for value in inputs:
            with self.subTest(value=value):
                once = self.normalized(value)
                twice = self.normalized(once)
                self.assertEqual(twice, once)

    def test_empty_string_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            self.normalizer.normalize("")

    def test_whitespace_only_string_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            self.normalizer.normalize(" \t\n ")

    def test_none_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be None"):
            self.normalizer.normalize(None)

    def test_non_string_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "must be a string"):
            self.normalizer.normalize(330)


if __name__ == "__main__":
    unittest.main()
