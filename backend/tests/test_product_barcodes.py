import unittest

from app.barcodes import ProductBarcodeKind, validate_product_barcode
from scripts.seed_mobile_dev import BARCODE as MOBILE_DEV_FIXTURE_BARCODE


class ProductBarcodeTests(unittest.TestCase):
    def test_mobile_dev_fixture_uses_a_valid_product_barcode(self):
        result = validate_product_barcode(MOBILE_DEV_FIXTURE_BARCODE)
        self.assertTrue(result.valid)
        self.assertEqual(result.kind, ProductBarcodeKind.EAN_13)

    def test_supported_gtin_formats(self):
        cases = {
            "96385074": ProductBarcodeKind.EAN_8,
            "036000291452": ProductBarcodeKind.UPC_A,
            "4006381333931": ProductBarcodeKind.EAN_13,
            "10012345678902": ProductBarcodeKind.GTIN_14,
        }
        for value, expected_kind in cases.items():
            with self.subTest(kind=expected_kind):
                result = validate_product_barcode(value)
                self.assertTrue(result.valid)
                self.assertEqual(result.kind, expected_kind)
                self.assertEqual(result.value, value)

    def test_only_outer_whitespace_is_harmless(self):
        self.assertEqual(
            validate_product_barcode("  4006381333931\r\n").value,
            "4006381333931",
        )
        self.assertEqual(
            validate_product_barcode("4006 381333931").reason,
            "non_numeric",
        )

    def test_invalid_checksum_is_rejected(self):
        result = validate_product_barcode("4006381333932")
        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "invalid_checksum")

    def test_qr_url_and_text_are_rejected(self):
        for value in (
            "https://example.test/4006381333931",
            "product-4006381333931",
            "４００６３８１３３３９３１",
        ):
            with self.subTest(value_type=type(value).__name__):
                self.assertEqual(validate_product_barcode(value).reason, "non_numeric")

    def test_wrong_lengths_are_rejected(self):
        for value in ("1", "1234567", "123456789", "12345678901", "123456789012345"):
            with self.subTest(length=len(value)):
                result = validate_product_barcode(value)
                self.assertFalse(result.valid)
                self.assertEqual(result.reason, "invalid_length")

    def test_safe_log_fields_never_contain_value(self):
        value = "4006381333931"
        fields = validate_product_barcode(value).safe_log_fields
        self.assertNotIn(value, repr(fields))
        self.assertEqual(fields["length"], 13)
        self.assertEqual(fields["reason"], "ok")


if __name__ == "__main__":
    unittest.main()
