"""Official OpenFoodTox 3.0 acquisition and deterministic IUCLID XLSX parsing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
import re

from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata, ScientificAssessmentInput,
    ScientificFindingInput, ScientificParsedRecord, ScientificParserResult,
    ScientificRecordRejection, ScientificReleaseIdentity,
    SubstanceIdentifierInput,
)
from app.scientific_ingestion.errors import ScientificAcquisitionError, ScientificParserError
from app.scientific_ingestion.http_transport import (
    ControlledHttpTransport, HttpRequest, HttpRetryPolicy, HttpTimeouts,
)
from app.scientific_ingestion.references import (
    canonical_doi_url, canonical_source_doi_url,
)
from app.scientific_ingestion.xlsx import BoundedXlsxReader


ZENODO_HOST = "zenodo.org"
OPENFOODTOX_RECORD_ID = "19388272"
OPENFOODTOX_RECORD_DOI = "10.5281/zenodo.19388272"
OPENFOODTOX_CONCEPT_DOI = "10.5281/zenodo.780543"
OPENFOODTOX_EXTERNAL_RELEASE_KEY = "zenodo_record_19388272"
OPENFOODTOX_FILENAME = "OFT3.0 export repository.xlsx"
OPENFOODTOX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
OPENFOODTOX_ALLOWED_CONTENT_TYPES = frozenset({
    OPENFOODTOX_CONTENT_TYPE,
    "application/octet-stream",
    "application/zip",
})


@dataclass(frozen=True)
class AcquiredOpenFoodToxArtifact:
    release: ScientificReleaseIdentity
    locator: str
    filename: str
    content_type: str
    body: bytes
    sha256: str
    byte_size: int
    released_on: date
    record_doi: str
    concept_doi: str
    license_id: str
    provider_checksum: str | None
    acquisition_metadata: dict


class OpenFoodTox3Adapter:
    SOURCE_KEY = "openfoodtox"
    DATASET_KEY = "openfoodtox_3"

    def __init__(self, external_release_key=OPENFOODTOX_EXTERNAL_RELEASE_KEY, *,
                 record_doi=OPENFOODTOX_RECORD_DOI):
        self.external_release_key = external_release_key
        self.record_doi = record_doi
        self.release_document_reference = canonical_doi_url(record_doi)
        self.metadata = ScientificAdapterMetadata(
            source_key=self.SOURCE_KEY,
            dataset_key=self.DATASET_KEY,
            adapter_version="openfoodtox-3-adapter-1",
            acquisition_version="zenodo-record-acquisition-1",
            parser_version="openfoodtox-iuclid-xlsx-parser-1",
            normalization_schema_version="wye-scientific-record-1",
        )

    def discover_release(self):
        return ScientificReleaseIdentity(
            source_key=self.SOURCE_KEY,
            dataset_key=self.DATASET_KEY,
            external_release_key=self.external_release_key,
        )


class OpenFoodToxRemoteAcquirer:
    """Acquire one pinned official OpenFoodTox XLSX release without parsing it."""

    def __init__(self, transport, *, record_id=OPENFOODTOX_RECORD_ID,
                 base_url="https://zenodo.org", max_metadata_bytes=1024 * 1024,
                 max_artifact_bytes=30 * 1024 * 1024,
                 max_decompressed_bytes=160 * 1024 * 1024,
                 user_agent="WYE-scientific-ingestion/6.4.3"):
        if not str(record_id).isdigit():
            raise ValueError("Zenodo record id must be numeric")
        if base_url.rstrip("/") != "https://zenodo.org":
            raise ValueError("OpenFoodTox base URL must be the allow-listed official repository")
        self.transport = transport
        self.record_id = str(record_id)
        self.base_url = base_url.rstrip("/")
        self.max_metadata_bytes = max_metadata_bytes
        self.max_artifact_bytes = max_artifact_bytes
        self.max_decompressed_bytes = max_decompressed_bytes
        self.headers = {"Accept": "application/json", "User-Agent": user_agent}

    def acquire(self):
        metadata_url = f"{self.base_url}/api/records/{self.record_id}"
        response = self.transport.get(HttpRequest(
            metadata_url, frozenset({ZENODO_HOST}), self.headers,
            self.max_metadata_bytes,
        ))
        try:
            document = json.loads(response.body)
            metadata = document["metadata"]
            record_doi = document.get("doi") or metadata["doi"]
            concept_doi = document.get("conceptdoi") or metadata["conceptdoi"]
            released_on = date.fromisoformat(metadata["publication_date"])
            license_id = metadata["license"]["id"]
            files = [item for item in document["files"]
                     if item.get("key") == OPENFOODTOX_FILENAME]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ScientificAcquisitionError(
                "invalid OpenFoodTox Knowledge Junction record metadata"
            ) from exc
        try:
            canonical_doi_url(record_doi)
            canonical_doi_url(concept_doi)
        except ValueError as exc:
            raise ScientificAcquisitionError(
                "invalid OpenFoodTox Knowledge Junction DOI metadata"
            ) from exc
        if concept_doi != OPENFOODTOX_CONCEPT_DOI or len(files) != 1:
            raise ScientificAcquisitionError(
                "unexpected OpenFoodTox record identity or XLSX file set"
            )
        item = files[0]
        try:
            locator = item["links"]["self"]
            expected_size = int(item["size"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ScientificAcquisitionError(
                "invalid OpenFoodTox artifact metadata"
            ) from exc
        artifact = self.transport.get(HttpRequest(
            locator, frozenset({ZENODO_HOST}),
            {"Accept": "*/*", "User-Agent": self.headers["User-Agent"]},
            self.max_artifact_bytes,
        ))
        raw_content_type = artifact.headers.get("content-type", "")
        actual_content_types = tuple(
            value.split(";", 1)[0].strip().lower()
            for value in raw_content_type.split(",") if value.strip()
        )
        if (not actual_content_types
                or any(value not in OPENFOODTOX_ALLOWED_CONTENT_TYPES
                       for value in actual_content_types)):
            raise ScientificAcquisitionError(
                "incompatible OpenFoodTox artifact Content-Type: "
                f"{raw_content_type or 'missing'}"
            )
        body = artifact.body
        if expected_size != len(body):
            raise ScientificAcquisitionError(
                "OpenFoodTox artifact size differs from record metadata"
            )
        provider_checksum = item.get("checksum")
        if provider_checksum:
            if not provider_checksum.startswith("md5:"):
                raise ScientificAcquisitionError(
                    "unsupported OpenFoodTox provider checksum algorithm"
                )
            actual_md5 = hashlib.md5(body, usedforsecurity=False).hexdigest()
            if actual_md5 != provider_checksum[4:].lower():
                raise ScientificAcquisitionError(
                    "OpenFoodTox artifact checksum mismatch"
                )
        try:
            with BoundedXlsxReader(
                body, provider="OpenFoodTox",
                max_decompressed_bytes=self.max_decompressed_bytes,
            ):
                pass
        except ScientificParserError as exc:
            raise ScientificAcquisitionError(
                "OpenFoodTox artifact failed XLSX container validation"
            ) from exc
        sha256 = hashlib.sha256(body).hexdigest()
        release = ScientificReleaseIdentity(
            source_key=OpenFoodTox3Adapter.SOURCE_KEY,
            dataset_key=OpenFoodTox3Adapter.DATASET_KEY,
            external_release_key=f"zenodo_record_{self.record_id}",
        )
        return AcquiredOpenFoodToxArtifact(
            release=release, locator=locator, filename=item["key"],
            content_type=OPENFOODTOX_CONTENT_TYPE, body=body, sha256=sha256,
            byte_size=len(body), released_on=released_on, record_doi=record_doi,
            concept_doi=concept_doi, license_id=license_id,
            provider_checksum=provider_checksum,
            acquisition_metadata={
                "record_id": self.record_id,
                "record_url": metadata_url,
                "record_doi": record_doi,
                "concept_doi": concept_doi,
                "metadata_attempts": response.attempts,
                "artifact_attempts": artifact.attempts,
                "source_release_date": released_on.isoformat(),
                "actual_content_type": actual_content_types[0],
                "raw_content_type": raw_content_type,
                "provider_record_metadata": document,
            },
        )


def configured_openfoodtox_acquirer():
    """Build the network client only for an explicit caller/opt-in test."""
    transport = ControlledHttpTransport(
        timeouts=HttpTimeouts(
            connect_seconds=float(os.getenv(
                "WYE_OPENFOODTOX_CONNECT_TIMEOUT_SECONDS", "10"
            )),
            read_seconds=float(os.getenv(
                "WYE_OPENFOODTOX_READ_TIMEOUT_SECONDS", "120"
            )),
        ),
        retry_policy=HttpRetryPolicy(
            max_attempts=int(os.getenv("WYE_OPENFOODTOX_MAX_ATTEMPTS", "3")),
            base_backoff_seconds=float(os.getenv(
                "WYE_OPENFOODTOX_BACKOFF_SECONDS", "0.5"
            )),
        ),
    )
    return OpenFoodToxRemoteAcquirer(
        transport,
        record_id=os.getenv("WYE_OPENFOODTOX_RECORD_ID", OPENFOODTOX_RECORD_ID),
        max_artifact_bytes=int(os.getenv(
            "WYE_OPENFOODTOX_MAX_ARTIFACT_BYTES", str(30 * 1024 * 1024)
        )),
        max_decompressed_bytes=int(os.getenv(
            "WYE_OPENFOODTOX_MAX_DECOMPRESSED_BYTES", str(160 * 1024 * 1024)
        )),
        user_agent=os.getenv(
            "WYE_OPENFOODTOX_USER_AGENT", "WYE-scientific-ingestion/6.4.3"
        ),
    )


class OpenFoodToxIuclidXlsxParser:
    """Join explicit IUCLID document relations; never infer scientific meaning."""

    SHEETS = (
        "DOSSIER", "DOSSIER_DOCS", "REF_SUB", "SUB", "LIT",
        "END_STUDY_REC.HumanHealth",
    )

    def __init__(self, adapter: OpenFoodTox3Adapter, *, max_records=500,
                 max_scanned_records=100000,
                 max_decompressed_bytes=160 * 1024 * 1024,
                 max_archive_entries=200):
        self.adapter = adapter
        self.max_records = max_records
        self.max_scanned_records = max_scanned_records
        self.max_decompressed_bytes = max_decompressed_bytes
        self.max_archive_entries = max_archive_entries

    def parse_bytes(self, body: bytes, *, locator=None):
        with BoundedXlsxReader(
            body, provider="OpenFoodTox",
            max_decompressed_bytes=self.max_decompressed_bytes,
            max_archive_entries=self.max_archive_entries,
        ) as workbook:
            tables = {name: workbook.records(name) for name in self.SHEETS}
        parsed, rejected = [], []
        context = self._build_context(tables)
        studies = sorted(
            tables["END_STUDY_REC.HumanHealth"],
            key=lambda row: row.get("Document UUID", ""),
        )
        scanned = 0
        for raw_study in studies:
            if len(parsed) >= self.max_records:
                break
            if scanned >= self.max_scanned_records:
                break
            scanned += 1
            record_key = raw_study.get("Document UUID", "").strip() or "missing_uuid"
            try:
                parsed.append(self._parse_study(raw_study, context, locator))
            except (KeyError, ValueError, InvalidOperation) as exc:
                rejected.append(ScientificRecordRejection(
                    source_record_key=record_key,
                    error_code="malformed_provider_record",
                    error_summary=str(exc) or "malformed OpenFoodTox IUCLID record",
                    raw_record=self._compact(raw_study),
                ))
        parsed.sort(key=lambda item: item.source_record_key)
        rejected.sort(key=lambda item: item.source_record_key)
        return ScientificParserResult(
            records=tuple(parsed), rejected_records=tuple(rejected),
            metadata={
                "provider": "openfoodtox",
                "dataset": "openfoodtox_3",
                "native_format": "iuclid_6_oht_xlsx",
                "native_sheet": "END_STUDY_REC.HumanHealth",
                "release_identity": self.adapter.discover_release().model_dump(mode="json"),
                "records_available": len(studies),
                "records_scanned": scanned,
                "records_bounded": len(parsed),
            },
            parser_version=self.adapter.metadata.parser_version,
            normalization_schema_version=self.adapter.metadata.normalization_schema_version,
        )

    @staticmethod
    def _build_context(tables):
        documents_by_dossier = {}
        dossiers_by_document = {}
        for row in tables["DOSSIER_DOCS"]:
            dossier_id = row.get("DOSSIER UUID", "").strip()
            document_id = row.get("DOCUMENT UUID", "").strip()
            document_type = row.get("DOCUMENT TYPE", "").strip()
            if dossier_id and document_id:
                documents_by_dossier.setdefault(dossier_id, []).append(
                    (document_type, document_id)
                )
                dossiers_by_document.setdefault(document_id, []).append(dossier_id)
        return {
            "documents_by_dossier": documents_by_dossier,
            "dossiers_by_document": dossiers_by_document,
            "dossiers": OpenFoodToxIuclidXlsxParser._index(
                tables["DOSSIER"], "Document UUID"
            ),
            "substances": OpenFoodToxIuclidXlsxParser._index(
                tables["SUB"], "Document UUID"
            ),
            "reference_substances": OpenFoodToxIuclidXlsxParser._index(
                tables["REF_SUB"], "Document UUID"
            ),
            "literature": OpenFoodToxIuclidXlsxParser._index(
                tables["LIT"], "Document UUID"
            ),
        }

    @staticmethod
    def _index(rows, key):
        result = {}
        for row in rows:
            value = row.get(key, "").strip()
            if value:
                if value in result:
                    raise ValueError(f"duplicate IUCLID identity in {key}: {value}")
                result[value] = row
        return result

    def _parse_study(self, study, context, artifact_locator):
        study_id = self._required(study, "Document UUID")
        dossier_ids = sorted(set(context["dossiers_by_document"].get(study_id, ())))
        if not dossier_ids:
            raise ValueError("study has no explicit dossier association")
        joined = []
        for dossier_id in dossier_ids:
            substance_ids = sorted(
                document_id for kind, document_id
                in context["documents_by_dossier"].get(dossier_id, ())
                if kind == "SUBSTANCE"
            )
            if len(substance_ids) == 1 and dossier_id in context["dossiers"]:
                joined.append((dossier_id, substance_ids[0]))
        if len(joined) != 1:
            raise ValueError("study does not resolve to one explicit dossier/substance pair")
        dossier_id, substance_id = joined[0]
        dossier = context["dossiers"][dossier_id]
        substance = context["substances"].get(substance_id)
        if substance is None:
            raise ValueError("dossier substance document is missing")
        reference_id = self._required(substance, "ReferenceSubstance.ReferenceSubstance")
        reference = context["reference_substances"].get(reference_id)
        if reference is None:
            raise ValueError("reference substance document is missing")
        literature_id = self._required(study, "DataSource.Reference")
        literature = context["literature"].get(literature_id)
        if literature is None:
            raise ValueError("study literature reference is missing")
        document_reference = canonical_source_doi_url(
            self._required(literature, "GeneralInfo.Source")
        )
        identifiers = self._identifiers(reference, study_id, artifact_locator)
        source_locator = (
            f"{artifact_locator or 'openfoodtox'}#"
            f"END_STUDY_REC.HumanHealth/{study_id}"
        )
        finding = self._finding(study, source_locator)
        published = dossier.get("LiteratureReference.DateOfEvaluation", "").strip()
        compact = {
            "study": self._compact(study),
            "dossier": self._compact(dossier),
            "substance": self._compact(substance),
            "reference_substance": self._compact(reference),
            "literature": self._compact(literature),
            "join": {
                "dossier_uuid": dossier_id,
                "substance_uuid": substance_id,
                "reference_substance_uuid": reference_id,
                "literature_uuid": literature_id,
            },
        }
        endpoint = self._required(study, "AdministrativeData.Endpoint")
        return ScientificParsedRecord(
            source_record_key=study_id,
            source_record_locator=source_locator,
            raw_record=compact,
            substance_identifiers=identifiers,
            assessment=ScientificAssessmentInput(
                source_record_key=study_id,
                external_assessment_id=study_id,
                external_assessment_version=self.adapter.external_release_key,
                assessment_type=self._required(study, "Definition"),
                assessment_version=self.adapter.external_release_key,
                assessment_status="published",
                published_at=date.fromisoformat(published) if published else None,
                document_reference=document_reference,
                conclusion_text=study.get(
                    "ResultsAndDiscussion.EffectLevels.Efflevel.RemarksOnResults.Remarks"
                ) or study.get("ResultsAndDiscussion.EffectLevels.RemarksOnResult.Remarks"),
                assessment_data={
                    "provider": "openfoodtox",
                    "dataset": "openfoodtox_3",
                    "iuclid_definition": study["Definition"],
                    "endpoint": endpoint,
                    "efsa_question_number": dossier.get("DataSource.EFSAQuestionNumber"),
                },
                raw_record=compact,
            ),
            findings=(finding,),
        )

    @staticmethod
    def _identifiers(reference, study_id, artifact_locator):
        values = []
        cas = (reference.get("Inventory.CASNumber")
               or reference.get("CAS number") or "").strip()
        if cas:
            if not re.fullmatch(r"\d{2,7}-\d{2}-\d", cas):
                raise ValueError("malformed CAS identifier")
            values.append(("cas", cas, "CAS Registry Number"))
        efsa_code = reference.get("EFSA PARAM CODE", "").strip()
        if efsa_code:
            if not re.fullmatch(r"RF-\d{8}-PAR", efsa_code):
                raise ValueError("malformed EFSA parameter code")
            values.append(("efsa_param_code", efsa_code, "EFSA PARAM CODE"))
        if not values:
            raise ValueError("reference substance has no supported native identifier")
        source_locator = (
            f"{artifact_locator or 'openfoodtox'}#"
            f"END_STUDY_REC.HumanHealth/{study_id}"
        )
        return tuple(SubstanceIdentifierInput(
            namespace_key=namespace,
            namespace_version="1",
            raw_value=raw_value,
            normalized_value=raw_value.strip().upper() if namespace == "efsa_param_code"
            else raw_value.strip(),
            is_primary=index == 0,
            source_record_locator=source_locator,
            provenance={
                "authority": "EFSA",
                "dataset": "OpenFoodTox 3.0",
                "native_field": native_field,
                "governance": "registered" if namespace == "cas"
                else "recognized_unregistered_review",
            },
        ) for index, (namespace, raw_value, native_field) in enumerate(values))

    @staticmethod
    def _finding(study, source_locator):
        prefix = "ResultsAndDiscussion.EffectLevels.Efflevel."
        endpoint = (study.get(prefix + "Endpoint")
                    or study.get("AdministrativeData.Endpoint") or "").strip()
        lower = study.get(prefix + "EffectLevel.lowerValue", "").strip()
        upper = study.get(prefix + "EffectLevel.upperValue", "").strip()
        qualifier = (study.get(prefix + "EffectLevel.lowerQualifier")
                     or study.get(prefix + "EffectLevel.upperQualifier") or "").strip()
        raw_value = upper or lower
        numeric = None
        if raw_value:
            numeric = Decimal(raw_value)
        unit = (study.get(prefix + "EffectLevel.Unit")
                or study.get(prefix + "EffectLevel.Unit.Other") or "").strip() or None
        species = (study.get("MaterialsAndMethods.TestAnimals.Species")
                   or study.get("MaterialsAndMethods.Method.SpeciesStrain.SpeciesStrain")
                   or "").strip()
        route = study.get("MaterialsAndMethods.AdministrationExposure.RouteOfAdministration", "").strip()
        sex = (study.get(prefix + "Sex")
               or study.get("MaterialsAndMethods.TestAnimals.Sex") or "").strip()
        population = "; ".join(value for value in (species, sex, route) if value) or None
        raw_effect = {
            key: value for key, value in study.items()
            if value and (key.startswith("ResultsAndDiscussion.")
                          or key.startswith("MaterialsAndMethods."))
        }
        display = " ".join(value for value in (qualifier, raw_value, unit) if value)
        return ScientificFindingInput(
            source_record_key=f"{study['Document UUID']}::effect",
            source_finding_key="reported_effect",
            source_ordinal=0,
            endpoint=endpoint,
            value_numeric=numeric,
            value_text=display or endpoint,
            unit=unit,
            population_context=population,
            evidence_type="openfoodtox_iuclid_reported_study",
            conclusion_text=(study.get(prefix + "RemarksOnResults.Remarks")
                             or study.get("ResultsAndDiscussion.EffectLevels.RemarksOnResult.Remarks")),
            source_locator=source_locator,
            raw_payload=raw_effect,
        )

    @staticmethod
    def _required(row, key):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"missing OpenFoodTox field: {key}")
        return value.strip()

    @staticmethod
    def _compact(row):
        return {key: value for key, value in row.items() if value != ""}


class OpenFoodToxArtifactParser:
    """Manifest wrapper that keeps storage and HTTP outside the IUCLID parser."""

    def __init__(self, adapter, payload_reader, **parser_options):
        self.adapter = adapter
        self.payload_reader = payload_reader
        self.parser = OpenFoodToxIuclidXlsxParser(adapter, **parser_options)

    def parse(self, manifest):
        if manifest.release != self.adapter.discover_release() or len(manifest.artifacts) != 1:
            raise ScientificParserError("OpenFoodTox manifest identity is invalid")
        artifact = manifest.artifacts[0]
        return self.parser.parse_bytes(
            self.payload_reader.read_bytes(artifact), locator=artifact.source_locator
        )
