"""Golden and boundary tests for wye-c14n-json-v1."""

from copy import deepcopy
from datetime import date, datetime, time, timezone
from decimal import Decimal
import math
import unittest
from uuid import uuid4

from app.scientific_evaluation.artifact_contracts import (
    ARTIFACT_CONTRACTS,
    build_artifact_envelope,
)
from app.scientific_evaluation.canonicalization import (
    canonical_sha256,
    canonicalize_json,
)
from app.scientific_evaluation.errors import (
    ArtifactContractError,
    CanonicalNumberError,
    CanonicalObjectKeyError,
    CanonicalStringError,
    UnsupportedCanonicalValueError,
)


class ScientificEvaluationCanonicalizationTests(unittest.TestCase):
    def test_golden_vector_and_sha256(self):
        # One readable fixture covers key ordering, NFC, arrays, controls and
        # escaping so a byte or digest regression points back to concrete input.
        value = {
            "z": "e\u0301",
            "a": [True, None, 1, "/\n"],
            "é": 'quote"slash\\',
        }
        expected = (
            '{"a":[true,null,1,"/\\u000a"],"z":"é",'
            '"é":"quote\\"slash\\\\"}'
        ).encode("utf-8")
        self.assertEqual(canonicalize_json(value), expected)
        self.assertEqual(
            canonical_sha256(value).hex(),
            "98096f3d682da72dc585661d7704fbacd7ac006f48416df2056cae934ab28a92",
        )

    def test_object_insertion_order_and_nested_order_are_irrelevant(self):
        first = {"z": {"b": 2, "a": 1}, "a": False}
        second = {"a": False, "z": {"a": 1, "b": 2}}
        self.assertEqual(canonicalize_json(first), canonicalize_json(second))

    def test_object_keys_use_unsigned_utf8_byte_order(self):
        self.assertEqual(
            canonicalize_json({"é": 3, "z": 2, "a": 1}),
            '{"a":1,"z":2,"é":3}'.encode("utf-8"),
        )

    def test_arrays_preserve_order(self):
        self.assertNotEqual(canonicalize_json([1, 2]), canonicalize_json([2, 1]))

    def test_unicode_is_nfc_normalized_without_ascii_escaping(self):
        self.assertEqual(canonicalize_json("e\u0301"), '"é"'.encode("utf-8"))
        self.assertEqual(
            canonicalize_json({"e\u0301": "value"}),
            canonicalize_json({"é": "value"}),
        )

    def test_escaping_uses_lowercase_six_byte_control_sequences(self):
        value = '"\\/\b\t\n\f\r\x00\x1f'
        self.assertEqual(
            canonicalize_json(value),
            b'"\\"\\\\/\\u0008\\u0009\\u000a\\u000c\\u000d\\u0000\\u001f"',
        )

    def test_booleans_null_and_signed_64_bit_integers(self):
        self.assertEqual(
            canonicalize_json([True, False, None, -(2**63), 0, 2**63 - 1]),
            b"[true,false,null,-9223372036854775808,0,9223372036854775807]",
        )

    def test_integer_outside_signed_64_bit_is_rejected(self):
        for value in (-(2**63) - 1, 2**63):
            with self.subTest(value=value), self.assertRaises(CanonicalNumberError):
                canonicalize_json(value)

    def test_all_binary_float_values_are_rejected(self):
        for value in (1.5, math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(CanonicalNumberError):
                canonicalize_json(value)

    def test_python_specific_values_are_rejected(self):
        values = (
            Decimal("1.25"),
            date.today(),
            datetime.now(timezone.utc),
            time(12, 30),
            uuid4(),
            b"bytes",
            {"set"},
            ("tuple",),
            object(),
        )
        for value in values:
            with self.subTest(value=type(value).__name__), self.assertRaises(
                UnsupportedCanonicalValueError
            ):
                canonicalize_json(value)

    def test_non_string_and_nfc_duplicate_object_keys_are_rejected(self):
        with self.assertRaises(CanonicalObjectKeyError):
            canonicalize_json({1: "value"})
        with self.assertRaises(CanonicalObjectKeyError):
            canonicalize_json({"é": 1, "e\u0301": 2})

    def test_unpaired_surrogates_are_rejected_in_keys_and_values(self):
        with self.assertRaises(CanonicalStringError):
            canonicalize_json("\ud800")
        with self.assertRaises(CanonicalStringError):
            canonicalize_json({"\udfff": "value"})

    def test_input_is_not_mutated(self):
        value = {"e\u0301": ["e\u0301", {"z": 1, "a": 2}]}
        original = deepcopy(value)
        canonicalize_json(value)
        self.assertEqual(value, original)

    def test_artifact_contract_registry_is_explicit_and_envelope_is_hashed(self):
        self.assertEqual(
            set(ARTIFACT_CONTRACTS),
            {
                ("protocol_definition", "1"),
                ("protocol_review", "1"),
                ("scientific_evidence_snapshot_query", "1"),
                ("scientific_evidence_snapshot_member", "1"),
                ("scientific_evidence_snapshot_manifest", "1"),
                ("scientific_evaluation_target", "1"),
                ("scientific_mapping_state_member", "1"),
                ("scientific_mapping_state_manifest", "1"),
                ("scientific_evaluation_input", "1"),
            },
        )
        envelope = build_artifact_envelope(
            "scientific_evidence_snapshot_query", "1", {"scope": "all"}
        )
        self.assertEqual(
            envelope,
            {
                "artifact_kind": "scientific_evidence_snapshot_query",
                "canonicalization_version": "wye-c14n-json-v1",
                "payload": {"scope": "all"},
                "schema_version": "1",
            },
        )
        self.assertNotEqual(
            canonical_sha256(
                build_artifact_envelope("protocol_definition", "1", {"same": True})
            ),
            canonical_sha256(
                build_artifact_envelope("protocol_review", "1", {"same": True})
            ),
        )

    def test_unknown_contract_envelope_or_media_type_is_rejected(self):
        with self.assertRaises(ArtifactContractError):
            build_artifact_envelope("future_result", "1", {})
        with self.assertRaises(ArtifactContractError):
            build_artifact_envelope("protocol_definition", "2", {})
        with self.assertRaises(ArtifactContractError):
            build_artifact_envelope("protocol_definition", "1", [])
        with self.assertRaises(ArtifactContractError):
            build_artifact_envelope(
                "protocol_definition", "1", {}, content_type="application/json"
            )


if __name__ == "__main__":
    unittest.main()
