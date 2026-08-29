"""Versioned canonical checksums for parser and normalized scientific output."""

from typing import Any

from .canonicalization import canonical_sha256


PARSER_OUTPUT_VERSION = "scientific_parser_output_v1"
ASSESSMENT_VERSION = "scientific_normalized_assessment_v1"
FINDING_VERSION = "scientific_normalized_finding_v1"


def _dump(model: Any) -> Any:
    return model.model_dump(mode="json", exclude_none=False)


def parser_output_checksum(result) -> str:
    # Tuple order is preserved because parser record/finding order is source-significant.
    return canonical_sha256({
        "version": PARSER_OUTPUT_VERSION,
        "records": [_dump(record) for record in result.records],
        "rejected_records": [_dump(record) for record in result.rejected_records],
        "warnings": [_dump(warning) for warning in result.warnings],
        "metadata": result.metadata,
        "parser_version": result.parser_version,
        "normalization_schema_version": result.normalization_schema_version,
    })


def assessment_checksum(assessment) -> str:
    payload = _dump(assessment)
    payload.pop("normalized_checksum", None)
    return canonical_sha256({"version": ASSESSMENT_VERSION, "assessment": payload})


def finding_checksum(finding) -> str:
    payload = _dump(finding)
    payload.pop("fingerprint", None)
    return canonical_sha256({"version": FINDING_VERSION, "finding": payload})
