"""Deterministic OpenFoodTox fixture adapter and parser foundation."""

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


class OpenFoodToxAdapter:
    SOURCE_KEY = "openfoodtox"
    DATASET_KEY = "openfoodtox_effects"
    FORMAT = "openfoodtox_snapshot_v1"
    NAMESPACE_MAP = {"CASRN": "cas", "PUBCHEM_CID": "pubchem_cid"}

    def __init__(self, fixture_path: Path, *, adapter_version="openfoodtox-adapter-1",
                 acquisition_version="fixture-acquisition-1",
                 parser_version="openfoodtox-parser-1",
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

    def discover_release(self):
        document = load_json_object(self.fixture_path.read_bytes(), self.SOURCE_KEY)
        self._validate_document_identity(document)
        return self._release_identity(document)

    @classmethod
    def _release_identity(cls, document):
        release_key = require_text(document.get("catalog", {}).get("snapshot_date"),
                                   "catalog.snapshot_date")
        return ScientificReleaseIdentity(
            source_key=cls.SOURCE_KEY,
            dataset_key=cls.DATASET_KEY,
            external_release_key=release_key,
        )

    @classmethod
    def _validate_document_identity(cls, document):
        if document.get("format") != cls.FORMAT:
            raise ScientificParserError("unsupported OpenFoodTox fixture format")
        if document.get("catalog", {}).get("dataset") != cls.DATASET_KEY:
            raise ScientificParserError("OpenFoodTox dataset identity mismatch")


class OpenFoodToxArtifactParser:
    def __init__(self, adapter: OpenFoodToxAdapter, payload_reader):
        self.adapter = adapter
        self.payload_reader = payload_reader

    def parse(self, manifest):
        artifact = primary_artifact(manifest)
        document = load_json_object(self.payload_reader.read_bytes(artifact), "openfoodtox")
        self.adapter._validate_document_identity(document)
        release = self.adapter._release_identity(document)
        if manifest.release != release:
            raise ScientificParserError("OpenFoodTox fixture release differs from manifest")
        native_records = document.get("entries")
        if not isinstance(native_records, list):
            raise ScientificParserError("OpenFoodTox entries must be an array")

        records, rejections, warnings = [], [], []
        seen = {}
        ordered = sorted(enumerate(native_records), key=lambda item: self._sort_key(item[1], item[0]))
        for ordinal, raw in ordered:
            record_key = self._record_key(raw, ordinal)
            if not isinstance(raw, dict):
                rejections.append(self._rejection(record_key, "malformed_provider_record",
                                                  "OpenFoodTox entry must be an object", None))
                continue
            fingerprint = canonical_sha256(raw)
            if record_key in seen:
                code = "duplicate_native_record" if seen[record_key] == fingerprint else "duplicate_native_record_conflict"
                if code == "duplicate_native_record":
                    warnings.append(ScientificParserWarning(
                        code=code, message="Identical OpenFoodTox native entry was ignored",
                        source_record_locator=self._locator(record_key),
                    ))
                else:
                    rejections.append(self._rejection(
                        record_key, code, "Conflicting OpenFoodTox native entry key", raw
                    ))
                continue
            seen[record_key] = fingerprint
            try:
                records.append(self._parse_record(raw, record_key))
            except UnsupportedOpenFoodToxNamespace as exc:
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
                "provider": "openfoodtox",
                "native_format": self.adapter.FORMAT,
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
        identities = raw["compound_ids"]
        if not isinstance(identities, list) or not identities:
            raise ValueError("compound_ids must be a non-empty array")
        parsed_identifiers = []
        locator = self._locator(record_key)
        for native in identities:
            if not isinstance(native, dict):
                raise ValueError("compound identifier must be an object")
            native_namespace = require_text(native.get("scheme"), "compound_ids.scheme")
            if native_namespace not in self.adapter.NAMESPACE_MAP:
                raise UnsupportedOpenFoodToxNamespace(
                    f"unsupported OpenFoodTox namespace: {native_namespace}"
                )
            raw_identifier = require_text(native.get("identifier"), "compound_ids.identifier")
            parsed_identifiers.append(SubstanceIdentifierInput(
                namespace_key=self.adapter.NAMESPACE_MAP[native_namespace],
                namespace_version="1",
                raw_value=raw_identifier,
                normalized_value=raw_identifier.strip(),
                is_primary=len(parsed_identifiers) == 0,
                source_record_locator=locator,
                provenance={"provider": "openfoodtox", "native_namespace": native_namespace},
            ))
        study = raw["study"]
        effects = raw.get("effects", [])
        if not isinstance(study, dict) or not isinstance(effects, list):
            raise ValueError("study must be an object and effects an array")
        parsed_findings = tuple(
            self._parse_effect(record_key, locator, item, ordinal)
            for ordinal, item in enumerate(effects)
        )
        published = study.get("publication_date")
        return ScientificParsedRecord(
            source_record_key=record_key,
            source_record_locator=locator,
            raw_record=raw,
            substance_identifiers=tuple(parsed_identifiers),
            assessment=ScientificAssessmentInput(
                source_record_key=record_key,
                external_assessment_id=require_text(study.get("study_id"), "study.study_id"),
                external_assessment_version=require_text(study.get("revision"), "study.revision"),
                assessment_type=require_text(study.get("study_type"), "study.study_type"),
                assessment_version=require_text(study.get("revision"), "study.revision"),
                assessment_status=study.get("status", "pending_review"),
                published_at=date.fromisoformat(published) if published else None,
                document_reference=study.get("reference"),
                conclusion_text=study.get("summary"),
                assessment_data={"provider": "openfoodtox", "native_entry_id": record_key},
                raw_record=raw,
            ),
            findings=parsed_findings,
        )

    @staticmethod
    def _parse_effect(record_key, locator, raw, ordinal):
        if not isinstance(raw, dict):
            raise ValueError("effect must be an object")
        native_key = require_text(raw.get("effect_id"), "effect.effect_id")
        numeric = raw.get("dose")
        return ScientificFindingInput(
            source_record_key=f"{record_key}::effect::{native_key}",
            source_finding_key=native_key,
            source_ordinal=ordinal,
            endpoint=raw.get("endpoint"),
            value_numeric=Decimal(str(numeric)) if numeric is not None else None,
            value_text=raw.get("result"),
            unit=raw.get("unit"),
            population_context=raw.get("test_system"),
            evidence_type=raw.get("evidence_type"),
            conclusion_text=raw.get("conclusion"),
            source_locator=locator,
            raw_payload=raw,
        )

    @staticmethod
    def _sort_key(raw, ordinal):
        return (raw.get("entry_id", "") if isinstance(raw, dict) else "", ordinal)

    @staticmethod
    def _record_key(raw, ordinal):
        if isinstance(raw, dict) and isinstance(raw.get("entry_id"), str) and raw["entry_id"].strip():
            return raw["entry_id"].strip()
        return f"openfoodtox_rejected_{ordinal:06d}"

    @staticmethod
    def _locator(record_key):
        return f"openfoodtox://entry/{record_key}"

    @staticmethod
    def _rejection(record_key, code, summary, raw):
        return ScientificRecordRejection(
            source_record_key=record_key,
            error_code=code,
            error_summary=summary or code,
            raw_record=raw,
        )


class UnsupportedOpenFoodToxNamespace(ValueError):
    pass
