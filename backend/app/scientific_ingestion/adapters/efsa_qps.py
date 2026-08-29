"""Official EFSA QPS release acquisition and deterministic XLSX parsing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import io
import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata, ScientificAssessmentInput,
    ScientificFindingInput, ScientificParsedRecord, ScientificParserResult,
    ScientificReleaseIdentity, SubstanceIdentifierInput,
)
from app.scientific_ingestion.errors import ScientificAcquisitionError, ScientificParserError
from app.scientific_ingestion.http_transport import (
    ControlledHttpTransport, HttpRequest, HttpRetryPolicy, HttpTimeouts,
)


ZENODO_HOST = "zenodo.org"
QPS_CONCEPT_DOI = "10.5281/zenodo.1146566"
QPS_RECORD_ID = "21216051"
QPS_RECORD_DOI = "10.5281/zenodo.21216051"
QPS_EXTERNAL_RELEASE_KEY = "zenodo_record_21216051"
QPS_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass(frozen=True)
class AcquiredEfsaArtifact:
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


class EfsaQpsAdapter:
    SOURCE_KEY = "efsa"
    DATASET_KEY = "efsa_qps"

    def __init__(self, external_release_key=QPS_EXTERNAL_RELEASE_KEY):
        self.external_release_key = external_release_key
        self.metadata = ScientificAdapterMetadata(
            source_key=self.SOURCE_KEY, dataset_key=self.DATASET_KEY,
            adapter_version="efsa-qps-adapter-1", acquisition_version="zenodo-record-acquisition-1",
            parser_version="efsa-qps-xlsx-parser-1",
            normalization_schema_version="wye-scientific-record-1",
        )

    def discover_release(self):
        return ScientificReleaseIdentity(source_key=self.SOURCE_KEY,
            dataset_key=self.DATASET_KEY, external_release_key=self.external_release_key)


class EfsaQpsRemoteAcquirer:
    """Acquire the pinned official release; it does not parse or persist science."""

    def __init__(self, transport, *, record_id=QPS_RECORD_ID, base_url="https://zenodo.org",
                 max_metadata_bytes=1024 * 1024,
                 max_artifact_bytes=5 * 1024 * 1024,
                 user_agent="WYE-scientific-ingestion/6.4.2"):
        if not str(record_id).isdigit():
            raise ValueError("Zenodo record id must be numeric")
        if base_url.rstrip("/") != "https://zenodo.org":
            raise ValueError("EFSA QPS base URL must be the allow-listed official repository")
        self.transport, self.record_id, self.base_url = transport, str(record_id), base_url.rstrip("/")
        self.max_metadata_bytes, self.max_artifact_bytes = max_metadata_bytes, max_artifact_bytes
        self.headers = {"Accept": "application/json", "User-Agent": user_agent}

    def acquire(self):
        metadata_url = f"{self.base_url}/api/records/{self.record_id}"
        response = self.transport.get(HttpRequest(metadata_url, frozenset({ZENODO_HOST}),
            self.headers, self.max_metadata_bytes))
        try:
            document = json.loads(response.body)
            metadata = document["metadata"]
            # Zenodo's current v1 response keeps DOI fields at record level;
            # older exports placed them inside metadata. Support both explicit shapes.
            record_doi = document.get("doi") or metadata["doi"]
            concept_doi = document.get("conceptdoi") or metadata["conceptdoi"]
            released_on = date.fromisoformat(metadata["publication_date"])
            license_id = metadata["license"]["id"]
            files = [item for item in document["files"] if item["key"].lower().endswith(".xlsx")]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ScientificAcquisitionError("invalid EFSA Knowledge Junction record metadata") from exc
        if concept_doi != QPS_CONCEPT_DOI or len(files) != 1:
            raise ScientificAcquisitionError("unexpected EFSA QPS record identity or file set")
        item = files[0]
        locator = item["links"]["self"]
        artifact = self.transport.get(HttpRequest(locator, frozenset({ZENODO_HOST}),
            {"Accept": "*/*", "User-Agent": self.headers["User-Agent"]},
            self.max_artifact_bytes))
        body = artifact.body
        sha256 = hashlib.sha256(body).hexdigest()
        if int(item["size"]) != len(body):
            raise ScientificAcquisitionError("EFSA artifact size differs from record metadata")
        provider_checksum = item.get("checksum")
        if provider_checksum and provider_checksum.startswith("md5:"):
            if hashlib.md5(body, usedforsecurity=False).hexdigest() != provider_checksum[4:]:
                raise ScientificAcquisitionError("EFSA artifact checksum mismatch")
        release = ScientificReleaseIdentity(source_key="efsa", dataset_key="efsa_qps",
            external_release_key=f"zenodo_record_{self.record_id}")
        return AcquiredEfsaArtifact(
            release, locator, item["key"], QPS_CONTENT_TYPE, body, sha256, len(body), released_on,
            record_doi, concept_doi, license_id, provider_checksum,
            {"record_id": self.record_id, "record_url": metadata_url,
             "metadata_attempts": response.attempts, "artifact_attempts": artifact.attempts,
             "source_release_date": released_on.isoformat()},
        )


def configured_efsa_qps_acquirer():
    """Build the real client only when an explicit caller requests it."""
    transport = ControlledHttpTransport(
        timeouts=HttpTimeouts(
            connect_seconds=float(os.getenv("WYE_EFSA_CONNECT_TIMEOUT_SECONDS", "10")),
            read_seconds=float(os.getenv("WYE_EFSA_READ_TIMEOUT_SECONDS", "30")),
        ),
        retry_policy=HttpRetryPolicy(
            max_attempts=int(os.getenv("WYE_EFSA_MAX_ATTEMPTS", "3")),
            base_backoff_seconds=float(os.getenv("WYE_EFSA_BACKOFF_SECONDS", "0.5")),
        ),
    )
    return EfsaQpsRemoteAcquirer(
        transport, record_id=os.getenv("WYE_EFSA_QPS_RECORD_ID", QPS_RECORD_ID),
        max_artifact_bytes=int(os.getenv("WYE_EFSA_MAX_ARTIFACT_BYTES", str(5 * 1024 * 1024))),
        user_agent=os.getenv("WYE_EFSA_USER_AGENT", "WYE-scientific-ingestion/6.4.2"),
    )


class EfsaQpsXlsxParser:
    REQUIRED_HEADERS = ("Microbiological Group", "Microbiological Subgroup", "Family",
                        "Genus", "Species", "Synonyms: valid", "Qualification 1",
                        "Qualification 2", "Qualification 3")

    def __init__(self, adapter: EfsaQpsAdapter, *, max_records=500,
                 max_decompressed_bytes=20 * 1024 * 1024, max_archive_entries=200):
        self.adapter, self.max_records = adapter, max_records
        self.max_decompressed_bytes, self.max_archive_entries = max_decompressed_bytes, max_archive_entries

    def parse_bytes(self, body: bytes, *, locator=None):
        rows = self._read_qps_rows(body)
        parsed = []
        for raw in rows[:self.max_records]:
            species = raw["Species"].strip()
            if not species:
                continue
            normalized = self.normalize_taxon(species)
            record_key = "qps_taxon_" + hashlib.sha256(normalized.encode()).hexdigest()[:24]
            source_locator = f"{locator or 'efsa-qps'}#species={species}"
            findings = [ScientificFindingInput(
                source_record_key=f"{record_key}::recommendation", source_finding_key="recommendation",
                source_ordinal=0, endpoint="qps_status", value_text="recommended",
                evidence_type="efsa_qps_list", source_locator=source_locator,
                raw_payload={"status": "recommended"},
            )]
            for ordinal, key in enumerate(("Qualification 1", "Qualification 2", "Qualification 3"), 1):
                if raw.get(key, "").strip():
                    findings.append(ScientificFindingInput(
                        source_record_key=f"{record_key}::qualification::{ordinal}",
                        source_finding_key=f"qualification_{ordinal}", source_ordinal=ordinal,
                        endpoint="qps_qualification", value_text=raw[key].strip(),
                        evidence_type="efsa_qps_list", source_locator=source_locator,
                        raw_payload={"column": key, "value": raw[key]},
                    ))
            parsed.append(ScientificParsedRecord(
                source_record_key=record_key, source_record_locator=source_locator, raw_record=raw,
                substance_identifiers=(SubstanceIdentifierInput(
                    namespace_key="efsa_qps_taxon", namespace_version="1", raw_value=species,
                    normalized_value=normalized, is_primary=True, source_record_locator=source_locator,
                    provenance={"authority": "EFSA", "dataset": "QPS", "identity_kind": "taxonomic_name"},
                ),),
                assessment=ScientificAssessmentInput(
                    source_record_key=record_key, external_assessment_id=species,
                    external_assessment_version=self.adapter.external_release_key,
                    assessment_type="efsa_qps_recommendation",
                    assessment_version=self.adapter.external_release_key, assessment_status="published",
                    document_reference=f"https://doi.org/{self.adapter.external_release_key}",
                    conclusion_text="Recommended for the Qualified Presumption of Safety list.",
                    assessment_data={"provider": "efsa", "dataset": "qps"}, raw_record=raw,
                ), findings=tuple(findings),
            ))
        parsed.sort(key=lambda item: item.substance_identifiers[0].normalized_value)
        return ScientificParserResult(records=tuple(parsed), metadata={
            "provider": "efsa", "dataset": "efsa_qps", "native_sheet": "QPS List",
            "release_identity": self.adapter.discover_release().model_dump(mode="json"),
            "records_available": len(rows), "records_bounded": len(parsed),
        }, parser_version=self.adapter.metadata.parser_version,
           normalization_schema_version=self.adapter.metadata.normalization_schema_version)

    @staticmethod
    def normalize_taxon(value):
        return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

    def _read_qps_rows(self, body):
        try:
            archive = zipfile.ZipFile(io.BytesIO(body))
        except (zipfile.BadZipFile, OSError) as exc:
            raise ScientificParserError("EFSA QPS artifact is not a valid XLSX container") from exc
        infos = archive.infolist()
        if len(infos) > self.max_archive_entries or sum(i.file_size for i in infos) > self.max_decompressed_bytes:
            raise ScientificParserError("EFSA QPS archive exceeds decompression limits")
        if any(".." in i.filename.split("/") or i.filename.startswith(("/", "\\")) for i in infos):
            raise ScientificParserError("unsafe XLSX archive path")
        try:
            shared = self._shared_strings(archive)
            sheet_path = self._sheet_path(archive, "QPS List")
            matrix = self._sheet_rows(archive.read(sheet_path), shared)
        except (KeyError, ET.ParseError, IndexError, ValueError) as exc:
            raise ScientificParserError("invalid EFSA QPS workbook structure") from exc
        if len(matrix) < 2:
            raise ScientificParserError("EFSA QPS worksheet contains no header")
        headers = matrix[1]
        indexes = {}
        for wanted in self.REQUIRED_HEADERS:
            matches = [i for i, value in enumerate(headers) if value.startswith(wanted)]
            if len(matches) != 1:
                raise ScientificParserError(f"missing or ambiguous QPS header: {wanted}")
            indexes[wanted] = matches[0]
        return [{key: (row[index] if index < len(row) else "") for key, index in indexes.items()}
                for row in matrix[2:] if any(value.strip() for value in row)]

    @staticmethod
    def _shared_strings(archive):
        try:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        except KeyError:
            return []
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        return ["".join(node.text or "" for node in item.iter(ns + "t")) for item in root]

    @staticmethod
    def _sheet_path(archive, name):
        main = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        target_id = next(item.attrib[rel + "id"] for item in workbook.iter(main + "sheet")
                         if item.attrib["name"] == name)
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(item.attrib["Target"] for item in relationships if item.attrib["Id"] == target_id)
        return "xl/" + target.lstrip("/").removeprefix("xl/")

    @staticmethod
    def _sheet_rows(xml, shared):
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        root, rows = ET.fromstring(xml), []
        for row in root.iter(ns + "row"):
            values = {}
            for cell in row.findall(ns + "c"):
                letters = re.match(r"[A-Z]+", cell.attrib["r"]).group()
                column = 0
                for char in letters:
                    column = column * 26 + ord(char) - 64
                node = cell.find(ns + "v")
                value = "" if node is None else node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(n.text or "" for n in cell.iter(ns + "t"))
                values[column - 1] = value
            rows.append([values.get(i, "") for i in range(max(values, default=-1) + 1)])
        return rows


class EfsaQpsArtifactParser:
    """Manifest-facing wrapper that keeps storage reads outside the XLSX parser."""

    def __init__(self, adapter, payload_reader, **parser_options):
        self.adapter, self.payload_reader = adapter, payload_reader
        self.parser = EfsaQpsXlsxParser(adapter, **parser_options)

    def parse(self, manifest):
        if manifest.release != self.adapter.discover_release() or len(manifest.artifacts) != 1:
            raise ScientificParserError("EFSA QPS manifest identity is invalid")
        artifact = manifest.artifacts[0]
        return self.parser.parse_bytes(self.payload_reader.read_bytes(artifact),
                                       locator=artifact.source_locator)
