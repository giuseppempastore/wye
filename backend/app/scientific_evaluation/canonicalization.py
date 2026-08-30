"""Runtime implementation of the frozen ``wye-c14n-json-v1`` profile."""

from __future__ import annotations

from hashlib import sha256
import unicodedata
from typing import Any

from app.scientific_evaluation.errors import (
    CanonicalNumberError,
    CanonicalObjectKeyError,
    CanonicalStringError,
    UnsupportedCanonicalValueError,
)


CANONICALIZATION_VERSION = "wye-c14n-json-v1"
DIGEST_ALGORITHM = "sha256"
MEDIA_TYPE = "application/vnd.wye.scientific+json"

MIN_SIGNED_64 = -(2**63)
MAX_SIGNED_64 = 2**63 - 1


def _canonical_string(value: str, path: str) -> str:
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise CanonicalStringError(f"{path}: unpaired Unicode surrogate is forbidden")
    normalized = unicodedata.normalize("NFC", value)
    escaped: list[str] = ['"']
    for character in normalized:
        codepoint = ord(character)
        if character == '"':
            escaped.append('\\"')
        elif character == "\\":
            escaped.append("\\\\")
        elif codepoint <= 0x1F:
            escaped.append(f"\\u{codepoint:04x}")
        else:
            escaped.append(character)
    escaped.append('"')
    return "".join(escaped)


def _canonical_text(value: Any, path: str) -> str:
    value_type = type(value)
    if value is None:
        return "null"
    if value_type is bool:
        return "true" if value else "false"
    if value_type is int:
        if value < MIN_SIGNED_64 or value > MAX_SIGNED_64:
            raise CanonicalNumberError(f"{path}: integer is outside signed 64-bit range")
        return str(value)
    if value_type is float:
        raise CanonicalNumberError(
            f"{path}: binary floating-point values are forbidden; "
            "use a schema-normalized decimal string"
        )
    if value_type is str:
        return _canonical_string(value, path)
    if value_type is list:
        return "[" + ",".join(
            _canonical_text(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ) + "]"
    if value_type is dict:
        normalized_items: list[tuple[bytes, str, Any]] = []
        normalized_keys: set[str] = set()
        for key, item in value.items():
            if type(key) is not str:
                raise CanonicalObjectKeyError(f"{path}: object keys must be strings")
            normalized_key = unicodedata.normalize("NFC", key)
            _canonical_string(normalized_key, f"{path}.<key>")
            if normalized_key in normalized_keys:
                raise CanonicalObjectKeyError(
                    f"{path}: duplicate object key after Unicode NFC normalization"
                )
            normalized_keys.add(normalized_key)
            normalized_items.append(
                (normalized_key.encode("utf-8"), normalized_key, item)
            )
        normalized_items.sort(key=lambda entry: entry[0])
        return "{" + ",".join(
            _canonical_string(key, f"{path}.<key>")
            + ":"
            + _canonical_text(item, f"{path}.{key}")
            for _, key, item in normalized_items
        ) + "}"
    raise UnsupportedCanonicalValueError(
        f"{path}: unsupported canonical value type {value_type.__name__}"
    )


def canonicalize_json(value: Any) -> bytes:
    """Return deterministic UTF-8 bytes for the narrow canonical JSON v1 domain.

    The function never mutates ``value``. Lists retain order; dictionaries are
    ordered by NFC-normalized UTF-8 key bytes. Binary floats and Python-specific
    convenience types must be normalized explicitly before this boundary.
    """

    return _canonical_text(value, "$").encode("utf-8")


def canonical_sha256(value: Any) -> bytes:
    """Return the 32-byte SHA-256 digest of exact canonical JSON bytes."""

    return sha256(canonicalize_json(value)).digest()
