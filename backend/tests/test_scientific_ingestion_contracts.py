import unittest
from decimal import Decimal

from pydantic import ValidationError

from app.scientific_ingestion.canonicalization import canonical_json_bytes, canonical_sha256
from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata,
    ScientificArtifactAcquirer,
    ScientificArtifactManifest,
    ScientificArtifactParser,
    ScientificArtifactReference,
    ScientificAssessmentInput,
    ScientificChecksum,
    ScientificFindingInput,
    ScientificIngestionConfiguration,
    ScientificParsedRecord,
    ScientificParserResult,
    ScientificReleaseIdentity,
    ScientificSourceAdapter,
    SubstanceIdentifierInput,
)
from app.scientific_ingestion.fake import (
    FakeScientificArtifactAcquirer,
    FakeScientificArtifactParser,
    FakeScientificSourceAdapter,
)


class ScientificIngestionContractTests(unittest.TestCase):
    def metadata(self, **overrides):
        values = dict(
            source_key="test_source",
            dataset_key="test_dataset",
            adapter_version="adapter-1",
            acquisition_version="acquisition-1",
            parser_version="parser-1",
            normalization_schema_version="normalization-1",
        )
        values.update(overrides)
        return ScientificAdapterMetadata(**values)

    def release(self):
        return ScientificReleaseIdentity(
            source_key="test_source",
            dataset_key="test_dataset",
            external_release_key="release-1",
        )

    def artifact(self, key="primary", role="primary", checksum=None, storage_id=1, byte_size=10):
        return ScientificArtifactReference(
            artifact_key=key,
            artifact_role=role,
            storage_object_id=storage_id,
            raw_checksum_algorithm="sha256",
            raw_checksum_value=checksum or "a" * 64,
            byte_size=byte_size,
        )

    def finding(self, **overrides):
        values = dict(
            source_record_key="finding_1",
            source_finding_key="native-finding-1",
            source_ordinal=0,
            endpoint="synthetic endpoint",
            value_numeric=Decimal("1.25"),
            unit="test_unit",
            raw_payload={"native": {"value": 1.25}},
        )
        values.update(overrides)
        return ScientificFindingInput(**values)

    def assessment(self, **overrides):
        values = dict(
            source_record_key="assessment_1",
            external_assessment_id="TEST-ASSESSMENT-1",
            external_assessment_version="1",
            assessment_type="synthetic_test",
            assessment_version="1",
            assessment_status="pending_review",
            document_reference="memory://test/document/1",
            conclusion_text="Synthetic fixture conclusion.",
            assessment_data={"normalized": True},
            raw_record={"native": True},
        )
        values.update(overrides)
        return ScientificAssessmentInput(**values)

    def parsed_record(self):
        return ScientificParsedRecord(
            source_record_key="record_1",
            source_record_locator="memory://test/record/1",
            raw_record={"native": {"field": "value"}},
            substance_identifiers=(
                SubstanceIdentifierInput(
                    namespace_key="test_identifier",
                    namespace_version="1",
                    raw_value=" TEST-001 ",
                    normalized_value="test-001",
                    is_primary=True,
                    source_record_locator="memory://test/record/1",
                    provenance={"fixture": True},
                ),
            ),
            assessment=self.assessment(),
            findings=(self.finding(),),
        )

    def test_adapter_metadata_and_protocols(self):
        adapter = FakeScientificSourceAdapter()
        acquirer = FakeScientificArtifactAcquirer()
        parser = FakeScientificArtifactParser()
        self.assertIsInstance(adapter, ScientificSourceAdapter)
        self.assertIsInstance(acquirer, ScientificArtifactAcquirer)
        self.assertIsInstance(parser, ScientificArtifactParser)
        self.assertEqual(adapter.metadata, self.metadata(
            adapter_version="fake-adapter-1",
            acquisition_version="fake-acquisition-1",
            parser_version="fake-parser-1",
            normalization_schema_version="fake-normalization-1",
        ))

    def test_empty_adapter_versions_and_keys_are_rejected(self):
        for field in (
            "adapter_version",
            "acquisition_version",
            "parser_version",
            "normalization_schema_version",
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    self.metadata(**{field: "   "})
        with self.assertRaises(ValidationError):
            self.metadata(source_key="Invalid Key")

    def test_artifact_validation_checksum_and_byte_size(self):
        artifact = self.artifact()
        self.assertEqual(artifact.raw_checksum_value, "a" * 64)
        with self.assertRaises(ValidationError):
            self.artifact(byte_size=-1)
        with self.assertRaises(ValidationError):
            ScientificArtifactReference(
                artifact_key="primary",
                artifact_role="primary",
                storage_object_id=1,
                raw_checksum_algorithm="sha256",
                byte_size=1,
            )
        for checksum in ("A" * 64, "a" * 63, "not-hex"):
            with self.subTest(checksum=checksum):
                with self.assertRaises(ValidationError):
                    self.artifact(checksum=checksum)

    def test_manifest_requires_unique_artifact_keys(self):
        artifacts = (self.artifact(), self.artifact(storage_id=2, checksum="b" * 64))
        fingerprint = canonical_sha256({"irrelevant": True})
        with self.assertRaisesRegex(ValidationError, "artifact_key must be unique"):
            ScientificArtifactManifest(
                release=self.release(),
                artifacts=artifacts,
                fingerprint=fingerprint,
            )

    def test_manifest_order_is_canonical_and_fingerprint_is_stable(self):
        primary = self.artifact("primary", "primary", "a" * 64, 1, 10)
        metadata = self.artifact("metadata", "metadata", "b" * 64, 2, 20)
        first = ScientificArtifactManifest.build(self.release(), (primary, metadata))
        second = ScientificArtifactManifest.build(self.release(), (metadata, primary))
        repeated = ScientificArtifactManifest.build(self.release(), (primary, metadata))
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(first.fingerprint, repeated.fingerprint)
        self.assertEqual(
            first.fingerprint,
            "715b0726b97d285a1be2b13fded1bb48ce2767b5b4d54c345fd5da5bc860249e",
        )
        self.assertEqual(first.fingerprint_algorithm, "sha256")

    def test_manifest_semantic_changes_change_fingerprint(self):
        base = ScientificArtifactManifest.build(self.release(), (self.artifact(),))
        checksum_changed = ScientificArtifactManifest.build(
            self.release(), (self.artifact(checksum="b" * 64),)
        )
        role_changed = ScientificArtifactManifest.build(
            self.release(), (self.artifact(role="metadata"),)
        )
        artifact_changed = ScientificArtifactManifest.build(
            self.release(), (self.artifact(key="metadata", role="metadata"),)
        )
        self.assertEqual(len({
            base.fingerprint,
            checksum_changed.fingerprint,
            role_changed.fingerprint,
            artifact_changed.fingerprint,
        }), 4)

    def test_canonical_json_is_utf8_stable_and_dict_order_independent(self):
        first = {"z": "caffè", "a": {"two": 2, "one": 1}}
        second = {"a": {"one": 1, "two": 2}, "z": "caffè"}
        expected = '{"a":{"one":1,"two":2},"z":"caffè"}'.encode("utf-8")
        self.assertEqual(canonical_json_bytes(first), expected)
        self.assertEqual(canonical_json_bytes(second), expected)
        self.assertEqual(canonical_sha256(first), canonical_sha256(second))

    def test_ingestion_config_fingerprint_is_versioned_and_semantic(self):
        first = ScientificIngestionConfiguration(
            adapter=self.metadata(), semantic_configuration={"timeout": 10, "mode": "test"}
        )
        reordered = ScientificIngestionConfiguration(
            adapter=self.metadata(), semantic_configuration={"mode": "test", "timeout": 10}
        )
        changed = ScientificIngestionConfiguration(
            adapter=self.metadata(parser_version="parser-2"),
            semantic_configuration={"timeout": 10, "mode": "test"},
        )
        self.assertEqual(first.fingerprint, reordered.fingerprint)
        self.assertNotEqual(first.fingerprint, changed.fingerprint)
        self.assertEqual(first.fingerprint_algorithm, "sha256")
        self.assertEqual(first.canonicalization_version, "scientific_ingestion_config_v1")

    def test_valid_parsed_record_preserves_raw_payload(self):
        record = self.parsed_record()
        self.assertEqual(record.raw_record, {"native": {"field": "value"}})
        self.assertEqual(record.assessment.raw_record, {"native": True})
        self.assertEqual(record.findings[0].raw_payload, {"native": {"value": 1.25}})
        self.assertEqual(record.substance_identifiers[0].raw_value, " TEST-001 ")
        with self.assertRaises(ValidationError):
            record.source_record_key = "changed"

    def test_assessment_and_checksum_validation(self):
        checksum = ScientificChecksum(algorithm="sha256", value="c" * 64)
        assessment = self.assessment(normalized_checksum=checksum)
        self.assertEqual(assessment.normalized_checksum, checksum)
        with self.assertRaises(ValidationError):
            self.assessment(normalized_checksum={"algorithm": "sha256"})
        with self.assertRaises(ValidationError):
            self.assessment(assessment_status="source_specific_status")

    def test_finding_validation_and_ordinal(self):
        finding = self.finding()
        self.assertEqual(finding.value_numeric, Decimal("1.25"))
        with self.assertRaises(ValidationError):
            self.finding(source_ordinal=-1)
        with self.assertRaises(ValidationError):
            ScientificFindingInput(source_record_key="empty_finding")

    def test_fake_pipeline_is_deterministic_ordered_and_database_free(self):
        adapter = FakeScientificSourceAdapter()
        release = adapter.discover_release()
        manifest = FakeScientificArtifactAcquirer().acquire(release)
        first = FakeScientificArtifactParser().parse(manifest)
        second = FakeScientificArtifactParser().parse(manifest)
        self.assertIsInstance(first, ScientificParserResult)
        self.assertEqual(first, second)
        self.assertEqual(tuple(record.source_record_key for record in first.records), (
            "test_record_a",
            "test_record_b",
        ))
        self.assertEqual(tuple(len(record.findings) for record in first.records), (2, 1))
        self.assertEqual(first.records_seen, 2)
        self.assertEqual(first.records_accepted, 2)
        self.assertEqual(first.records_rejected, 0)
        self.assertEqual(first.warnings_count, 1)
        self.assertEqual(first.warnings[0].code, "test_warning")
        self.assertEqual(first.records[0].raw_record["test_label"], "A")
        self.assertEqual(first.metadata["manifest_fingerprint"], manifest.fingerprint)


if __name__ == "__main__":
    unittest.main()
