"""Deterministic EFSA fixture adapter and parser foundation."""

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.scientific_ingestion.canonicalization import canonical_sha256
from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata,
    ScientificAssessmentInput,
    ScientificFindingInput,
    ScientificParsedRecord,
    ScientificParserResult,
    ScientificParserWarning,
    ScientificRecordRejection,
    ScientificReleaseIdentity,
    SubstanceIdentifierInput,
)
from app.scientific_ingestion.errors import ScientificParserError

from .common import load_json_object, primary_artifact, require_text


class EfsaAdapter:
    SOURCE_KEY = "efsa"
    DATASET_KEY = "efsa_chemical_assessments"
    SCHEMA = "efsa_fixture_v1"
    NAMESPACE_MAP = {"CAS": "cas", "EFSA_SUBSTANCE_ID": "efsa_substance"}

    def __init__(self, fixture_path: Path, *, adapter_version="efsa-adapter-1",
                 acquisition_version="fixture-acquisition-1",
                 parser_version="efsa-parser-1",
                 normalization_schema_version="wye-scientific-record-1"):
        self.fixture_path = Path(fixture_path)
        self.metadata = ScientificAdapterMetadata(
            source_key=self.SOURCE_KEY,
            dataset_key=self.DATASET_KEY,
            adapter_version=adapter_version,
            acquisition_version=acquisition_version,
            parser_version=parser_version,
            normalization_schema_version=normalization_schema_version,
        )

    def discover_release(self) -> ScientificReleaseIdentity:
        document = load_json_object(self.fixture_path.read_bytes(), self.SOURCE_KEY)
        self._validate_document_identity(document)
        return self._release_identity(document)

    @classmethod
    def _release_identity(cls, document):
        release_key = require_text(document.get("release", {}).get("official_release"),
                                   "release.official_release")
        return ScientificReleaseIdentity(
            source_key=cls.SOURCE_KEY,
            dataset_key=cls.DATASET_KEY,
            external_release_key=release_key,
        )

    @classmethod
    def _validate_document_identity(cls, document):
        if document.get("schema") != cls.SCHEMA:
            raise ScientificParserError("unsupported EFSA fixture schema")
        if document.get("source", {}).get("key") != cls.SOURCE_KEY:
            raise ScientificParserError("EFSA source identity mismatch")
        if document.get("dataset", {}).get("key") != cls.DATASET_KEY:
            raise ScientificParserError("EFSA dataset identity mismatch")


class EfsaArtifactParser:
    def __init__(self, adapter: EfsaAdapter, payload_reader):
        self.adapter = adapter
        self.payload_reader = payload_reader

    def parse(self, manifest):
        artifact = primary_artifact(manifest)
        document = load_json_object(self.payload_reader.read_bytes(artifact), "efsa")
        self.adapter._validate_document_identity(document)
        release = self.adapter._release_identity(document)
        if manifest.release != release:
            raise ScientificParserError("EFSA fixture release differs from manifest")
        native_records = document.get("records")
        if not isinstance(native_records, list):
            raise ScientificParserError("EFSA records must be an array")

        records, rejections, warnings = [], [], []
        seen = {}
        ordered = sorted(enumerate(native_records), key=lambda item: self._sort_key(item[1], item[0]))
        for ordinal, raw in ordered:
            record_key = self._record_key(raw, ordinal)
            if not isinstance(raw, dict):
                rejections.append(self._rejection(record_key, "malformed_provider_record",
                                                  "EFSA record must be an object", None))
                continue
            fingerprint = canonical_sha256(raw)
            if record_key in seen:
                code = "duplicate_native_record" if seen[record_key] == fingerprint else "duplicate_native_record_conflict"
                if code == "duplicate_native_record":
                    warnings.append(ScientificParserWarning(
                        code=code, message="Identical EFSA native record was ignored",
                        source_record_locator=self._locator(record_key),
                    ))
                else:
                    rejections.append(self._rejection(
                        record_key, code, "Conflicting EFSA native record key", raw
                    ))
                continue
            seen[record_key] = fingerprint
            try:
                records.append(self._parse_record(raw, record_key))
            except UnsupportedEfsaNamespace as exc:
                rejections.append(self._rejection(record_key, "unsupported_namespace", str(exc), raw))
            except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
                rejections.append(self._rejection(
                    record_key, "malformed_provider_record", str(exc), raw
                ))

        return ScientificParserResult(
            records=tuple(records),
            rejected_records=tuple(sorted(rejections, key=lambda item: item.source_record_key)),
            warnings=tuple(sorted(warnings, key=lambda item: (item.code, item.source_record_locator or ""))),
            metadata={
                "provider": "efsa",
                "native_schema": self.adapter.SCHEMA,
                "native_record_count": len(native_records),
                "manifest_fingerprint": manifest.fingerprint,
                "artifact_locator": artifact.source_locator,
                "artifact_content_type": artifact.content_type,
                "release_identity": release.model_dump(mode="json"),
            },
            parser_version=self.adapter.metadata.parser_version,
            normalization_schema_version=self.adapter.metadata.normalization_schema_version,
        )

    def _parse_record(self, raw, record_key):
        identity = raw["substance_identity"]
        native_namespace = require_text(identity.get("namespace"), "substance_identity.namespace")
        if native_namespace not in self.adapter.NAMESPACE_MAP:
            raise UnsupportedEfsaNamespace(f"unsupported EFSA namespace: {native_namespace}")
        raw_identifier = require_text(identity.get("value"), "substance_identity.value")
        namespace_key = self.adapter.NAMESPACE_MAP[native_namespace]
        assessment = raw["assessment"]
        findings = raw.get("findings", [])
        if not isinstance(assessment, dict) or not isinstance(findings, list):
            raise ValueError("assessment must be an object and findings an array")
        locator = self._locator(record_key)
        parsed_findings = tuple(
            self._parse_finding(record_key, locator, item, ordinal)
            for ordinal, item in enumerate(findings)
        )
        published = assessment.get("published_on")
        return ScientificParsedRecord(
            source_record_key=record_key,
            source_record_locator=locator,
            raw_record=raw,
            substance_identifiers=(SubstanceIdentifierInput(
                namespace_key=namespace_key,
                namespace_version="1",
                raw_value=raw_identifier,
                normalized_value=raw_identifier.strip(),
                is_primary=True,
                source_record_locator=locator,
                provenance={"provider": "efsa", "native_namespace": native_namespace},
            ),),
            assessment=ScientificAssessmentInput(
                source_record_key=record_key,
                external_assessment_id=require_text(assessment.get("assessment_id"), "assessment.assessment_id"),
                external_assessment_version=require_text(assessment.get("version"), "assessment.version"),
                assessment_type=require_text(assessment.get("type"), "assessment.type"),
                assessment_version=require_text(assessment.get("version"), "assessment.version"),
                assessment_status=assessment.get("status", "pending_review"),
                published_at=date.fromisoformat(published) if published else None,
                document_reference=assessment.get("document_reference"),
                conclusion_text=assessment.get("conclusion"),
                assessment_data={"provider": "efsa", "native_question_number": record_key},
                raw_record=raw,
            ),
            findings=parsed_findings,
        )

    @staticmethod
    def _parse_finding(record_key, locator, raw, ordinal):
        if not isinstance(raw, dict):
            raise ValueError("finding must be an object")
        native_key = require_text(raw.get("finding_id"), "finding.finding_id")
        numeric = raw.get("value")
        return ScientificFindingInput(
            source_record_key=f"{record_key}::finding::{native_key}",
            source_finding_key=native_key,
            source_ordinal=ordinal,
            endpoint=raw.get("endpoint"),
            value_numeric=Decimal(str(numeric)) if numeric is not None else None,
            value_text=raw.get("value_text"),
            unit=raw.get("unit"),
            population_context=raw.get("population"),
            evidence_type=raw.get("evidence_type"),
            conclusion_text=raw.get("conclusion"),
            source_locator=locator,
            raw_payload=raw,
        )

    @staticmethod
    def _sort_key(raw, ordinal):
        return (raw.get("question_number", "") if isinstance(raw, dict) else "", ordinal)

    @staticmethod
    def _record_key(raw, ordinal):
        if isinstance(raw, dict) and isinstance(raw.get("question_number"), str) and raw["question_number"].strip():
            return raw["question_number"].strip()
        return f"efsa_rejected_{ordinal:06d}"

    @staticmethod
    def _locator(record_key):
        return f"efsa://assessment/{record_key}"

    @staticmethod
    def _rejection(record_key, code, summary, raw):
        return ScientificRecordRejection(
            source_record_key=record_key,
            error_code=code,
            error_summary=summary or code,
            raw_record=raw,
        )


class UnsupportedEfsaNamespace(ValueError):
    pass
