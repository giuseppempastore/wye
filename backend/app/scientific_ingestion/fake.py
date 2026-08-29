"""Deterministic, in-memory scientific components for contract tests only."""

from decimal import Decimal

from .contracts import (
    ScientificAdapterMetadata,
    ScientificArtifactManifest,
    ScientificArtifactReference,
    ScientificAssessmentInput,
    ScientificFindingInput,
    ScientificParsedRecord,
    ScientificParserResult,
    ScientificParserWarning,
    ScientificReleaseIdentity,
    SubstanceIdentifierInput,
)


class FakeScientificSourceAdapter:
    """Generic test source; intentionally unrelated to any real authority."""

    metadata = ScientificAdapterMetadata(
        source_key="test_source",
        dataset_key="test_dataset",
        adapter_version="fake-adapter-1",
        acquisition_version="fake-acquisition-1",
        parser_version="fake-parser-1",
        normalization_schema_version="fake-normalization-1",
    )

    def discover_release(self) -> ScientificReleaseIdentity:
        return ScientificReleaseIdentity(
            source_key=self.metadata.source_key,
            dataset_key=self.metadata.dataset_key,
            external_release_key="test-release-1",
        )


class FakeScientificArtifactAcquirer:
    def acquire(self, release: ScientificReleaseIdentity) -> ScientificArtifactManifest:
        return ScientificArtifactManifest.build(
            release,
            (
                ScientificArtifactReference(
                    artifact_key="primary",
                    artifact_role="primary",
                    storage_object_id=1001,
                    raw_checksum_algorithm="sha256",
                    raw_checksum_value="a" * 64,
                    byte_size=128,
                ),
            ),
        )


def _record(label: str, ordinal_count: int) -> ScientificParsedRecord:
    record_key = f"test_record_{label.lower()}"
    raw = {"test_label": label, "test_identifier": f"TEST-{label}"}
    findings = tuple(
        ScientificFindingInput(
            source_record_key=f"{record_key}_finding_{ordinal}",
            source_finding_key=f"TEST-FINDING-{label}-{ordinal}",
            source_ordinal=ordinal,
            endpoint="synthetic test endpoint",
            value_numeric=Decimal(ordinal + 1),
            unit="test_unit",
            raw_payload={"test_ordinal": ordinal},
        )
        for ordinal in range(ordinal_count)
    )
    return ScientificParsedRecord(
        source_record_key=record_key,
        source_record_locator=f"memory://fixture/{label.lower()}",
        raw_record=raw,
        substance_identifiers=(
            SubstanceIdentifierInput(
                namespace_key="test_identifier",
                namespace_version="1",
                raw_value=f" TEST-{label} ",
                normalized_value=f"test-{label.lower()}",
                is_primary=True,
                source_record_locator=f"memory://fixture/{label.lower()}",
                provenance={"fixture": True},
            ),
        ),
        assessment=ScientificAssessmentInput(
            source_record_key=record_key,
            external_assessment_id=f"TEST-ASSESSMENT-{label}",
            assessment_type="synthetic_test",
            assessment_version="1",
            assessment_status="pending_review",
            conclusion_text="Synthetic fixture conclusion; not scientific evidence.",
            assessment_data={"fixture": True},
            raw_record=raw,
        ),
        findings=findings,
    )


class FakeScientificArtifactParser:
    def parse(self, manifest: ScientificArtifactManifest) -> ScientificParserResult:
        return ScientificParserResult(
            records=(_record("A", 2), _record("B", 1)),
            warnings=(
                ScientificParserWarning(
                    code="test_warning",
                    message="Synthetic fixture warning",
                    source_record_locator="memory://fixture/b",
                ),
            ),
            metadata={
                "fixture": True,
                "manifest_fingerprint": manifest.fingerprint,
            },
            parser_version="fake-parser-1",
            normalization_schema_version="fake-normalization-1",
        )
