from dataclasses import dataclass
from enum import Enum


class ProductBarcodeKind(str, Enum):
    EAN_8 = "ean8"
    UPC_A = "upc_a"
    EAN_13 = "ean13"
    GTIN_14 = "gtin14"


@dataclass(frozen=True)
class ProductBarcodeValidation:
    valid: bool
    value: str | None
    kind: ProductBarcodeKind | None
    length: int
    reason: str

    @property
    def safe_log_fields(self) -> dict[str, str | int | bool | None]:
        return {
            "kind": self.kind.value if self.kind else None,
            "length": self.length,
            "valid": self.valid,
            "reason": self.reason,
        }


_KINDS = {
    8: ProductBarcodeKind.EAN_8,
    12: ProductBarcodeKind.UPC_A,
    13: ProductBarcodeKind.EAN_13,
    14: ProductBarcodeKind.GTIN_14,
}


def validate_product_barcode(raw_value: str | None) -> ProductBarcodeValidation:
    value = (raw_value or "").strip()
    if not value:
        return ProductBarcodeValidation(False, None, None, 0, "empty")
    if not value.isascii() or not value.isdigit():
        return ProductBarcodeValidation(False, None, None, len(value), "non_numeric")
    kind = _KINDS.get(len(value))
    if kind is None:
        return ProductBarcodeValidation(False, None, None, len(value), "invalid_length")

    weighted_sum = 0
    for position, character in enumerate(reversed(value[:-1]), start=1):
        weighted_sum += int(character) * (3 if position % 2 else 1)
    expected = (10 - weighted_sum % 10) % 10
    if expected != int(value[-1]):
        return ProductBarcodeValidation(False, None, kind, len(value), "invalid_checksum")
    return ProductBarcodeValidation(True, value, kind, len(value), "ok")
