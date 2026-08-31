"""Fail-closed governance gate for the frozen Phase 7.7.1 selection package.

This module validates repository artifacts supplied by an external reviewer. It
does not create approval records and it has no authority to approve scientific
policy. Validation is mechanical: current repository bytes, declared review
scope, record integrity, and provenance fields must all agree.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping
import unicodedata

from app.scientific_evaluation.canonicalization import canonical_sha256, canonicalize_json


APPROVAL_SCHEMA = "wye_selection_policy_approval_record"
APPROVAL_SCHEMA_VERSION = "1"
APPROVAL_ARTIFACT_FILENAME = "WYE_SELECTION_POLICY_EXTERNAL_APPROVAL.json"

FROZEN_POLICY_KEY = "efsa_qps_evidence_selection"
FROZEN_POLICY_VERSION = "1.0.0-candidate.1"
FROZEN_POLICY_CANONICAL_BYTES = 16284
FROZEN_POLICY_DIGEST = (
    "d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615"
)
FROZEN_GOLDEN_DOCUMENT_BYTES = 17040
FROZEN_GOLDEN_DOCUMENT_DIGEST = (
    "d05f6c8832df5111f3ad93611a088b86fd5b5853831bc6892966f06ace7e0e60"
)
FROZEN_GOLDEN_CORPUS_DIGEST = (
    "db535148ece59c222eaac2004594ae19a1e00a2e65448c42a4804dd8cefd8b15"
)
FROZEN_GOLDEN_CASE_COUNT = 28
GOLDEN_CORPUS_SCHEMA_REFERENCE = "wye_selection_golden_corpus_manifest/1"

DECISIONS = frozenset({"approved", "changes_requested", "rejected"})
ROLES = frozenset({"scientific_reviewer", "validation_owner", "release_approver"})

APPROVAL_REQUIRED = "EXTERNAL SCIENTIFIC APPROVAL REQUIRED"
APPROVAL_VALID = "EXTERNAL SCIENTIFIC APPROVAL VALID"
APPROVAL_REJECTED = "EXTERNAL SCIENTIFIC APPROVAL REJECTED"
CHANGES_REQUESTED = "EXTERNAL SCIENTIFIC CHANGES REQUESTED"

REQUIRED_SCOPE = (
    "phase_7_7_1_candidate_policy",
    "phase_7_7_1_golden_corpus",
)
MANDATORY_CATEGORY_C_ITEMS = (
    "efsa_qps_channel_admission",
    "qps_evidence_channel_mapping",
    "qps_status_endpoint_mapping",
    "qps_qualification_endpoint_mapping",
    "population_null_not_applicable_qps_taxonomic_unit",
    "scientific_date_precedence",
    "route_duration_not_applicable",
    "dependency_unknown_contributing",
    "scientific_contribution_role",
    "scientific_claims_and_non_claims",
    "scientific_golden_oracles",
)

_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_KEYS = frozenset(
    {
        "approval_schema",
        "approval_schema_version",
        "approval_key",
        "policy_key",
        "policy_version",
        "selection_policy_digest",
        "role",
        "reviewer_identity",
        "decision",
        "reviewed_at",
        "scope",
        "approved_category_C_items",
        "candidate_review_confirmed",
        "golden_corpus_review_confirmed",
        "golden_case_set_reference",
        "governed_audit_reference",
        "approval_record_digest",
    }
)
_OPTIONAL_KEYS = frozenset({"notes_reference"})
_FORBIDDEN_REVIEWER_IDENTITY_TOKENS = frozenset(
    {
        "ai",
        "application",
        "automation",
        "bootstrap",
        "bot",
        "chatbot",
        "chatgpt",
        "ci",
        "claude",
        "codex",
        "default",
        "fixture",
        "gemini",
        "generated",
        "gpt",
        "llm",
        "migration",
        "model",
        "openai",
        "software",
        "synthetic",
        "system",
        "test",
    }
)


class FrozenSelectionPackageIntegrityError(RuntimeError):
    """The repository no longer contains the exact frozen review subject."""


class ApprovalArtifactFormatError(ValueError):
    """An approval artifact cannot be parsed as one unambiguous JSON object."""


@dataclass(frozen=True)
class FrozenSelectionPackage:
    policy_version: str
    policy_digest: str
    policy_canonical_bytes: int
    golden_document_digest: str
    golden_document_bytes: int
    golden_corpus_digest: str
    golden_case_count: int


@dataclass(frozen=True)
class ApprovalValidation:
    gate_status: str
    errors: tuple[str, ...]
    decision: str | None = None
    reviewer_identity: str | None = None

    @property
    def mechanically_valid(self) -> bool:
        return not self.errors

    @property
    def unlocks_next_gate(self) -> bool:
        return self.gate_status == APPROVAL_VALID and self.mechanically_valid


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ApprovalArtifactFormatError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ApprovalArtifactFormatError(f"cannot read valid UTF-8 JSON from {path.name}") from exc
    if type(value) is not dict:
        raise ApprovalArtifactFormatError(f"{path.name} must contain one JSON object")
    return value


def _normalized_golden_document_bytes(path: Path) -> bytes:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FrozenSelectionPackageIntegrityError(
            "golden corpus document is not readable UTF-8"
        ) from exc
    normalized = unicodedata.normalize(
        "NFC", text.replace("\r\n", "\n").replace("\r", "\n")
    )
    return normalized.encode("utf-8")


def load_frozen_selection_package(repository_root: Path | str) -> FrozenSelectionPackage:
    """Recompute and verify every frozen Phase 7.7.1 identity from repository bytes."""

    root = Path(repository_root)
    candidate = _load_json_object(root / "WYE_SELECTION_POLICY_CANDIDATE_V1.json")
    manifest = _load_json_object(root / "WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json")

    candidate_bytes = canonicalize_json(candidate)
    candidate_digest = sha256(candidate_bytes).hexdigest()
    if candidate.get("schema_id") != "wye_scientific_evidence_selection_policy":
        raise FrozenSelectionPackageIntegrityError("candidate schema_id changed")
    if candidate.get("schema_version") != "1":
        raise FrozenSelectionPackageIntegrityError("candidate schema_version changed")
    if candidate.get("policy_key") != FROZEN_POLICY_KEY:
        raise FrozenSelectionPackageIntegrityError("candidate policy_key changed")
    if candidate.get("policy_version") != FROZEN_POLICY_VERSION:
        raise FrozenSelectionPackageIntegrityError("candidate policy_version changed")
    if len(candidate_bytes) != FROZEN_POLICY_CANONICAL_BYTES:
        raise FrozenSelectionPackageIntegrityError("candidate canonical byte length changed")
    if candidate_digest != FROZEN_POLICY_DIGEST:
        raise FrozenSelectionPackageIntegrityError("candidate canonical digest changed")

    manifest_bytes = canonicalize_json(manifest)
    manifest_digest = sha256(manifest_bytes).hexdigest()
    if manifest.get("schema_id") != "wye_selection_golden_corpus_manifest":
        raise FrozenSelectionPackageIntegrityError("golden manifest schema_id changed")
    if manifest.get("schema_version") != "1":
        raise FrozenSelectionPackageIntegrityError("golden manifest schema_version changed")
    if manifest_digest != FROZEN_GOLDEN_CORPUS_DIGEST:
        raise FrozenSelectionPackageIntegrityError("golden corpus digest changed")
    if manifest.get("case_count") != FROZEN_GOLDEN_CASE_COUNT:
        raise FrozenSelectionPackageIntegrityError("golden case count changed")

    policy_reference = manifest.get("policy")
    if type(policy_reference) is not dict or policy_reference != {
        "policy_key": FROZEN_POLICY_KEY,
        "policy_version": FROZEN_POLICY_VERSION,
        "selection_policy_digest": FROZEN_POLICY_DIGEST,
    }:
        raise FrozenSelectionPackageIntegrityError("golden manifest policy binding changed")

    document = manifest.get("document")
    expected_document = {
        "canonicalization": "utf8-lf-nfc-v1",
        "canonicalized_byte_length": FROZEN_GOLDEN_DOCUMENT_BYTES,
        "sha256": FROZEN_GOLDEN_DOCUMENT_DIGEST,
        "specification_file": "WYE_SELECTION_GOLDEN_CASES.md",
    }
    if type(document) is not dict or document != expected_document:
        raise FrozenSelectionPackageIntegrityError("golden document binding changed")
    golden_bytes = _normalized_golden_document_bytes(root / expected_document["specification_file"])
    if len(golden_bytes) != FROZEN_GOLDEN_DOCUMENT_BYTES:
        raise FrozenSelectionPackageIntegrityError("golden document byte length changed")
    if sha256(golden_bytes).hexdigest() != FROZEN_GOLDEN_DOCUMENT_DIGEST:
        raise FrozenSelectionPackageIntegrityError("golden document digest changed")

    return FrozenSelectionPackage(
        policy_version=FROZEN_POLICY_VERSION,
        policy_digest=candidate_digest,
        policy_canonical_bytes=len(candidate_bytes),
        golden_document_digest=FROZEN_GOLDEN_DOCUMENT_DIGEST,
        golden_document_bytes=len(golden_bytes),
        golden_corpus_digest=manifest_digest,
        golden_case_count=FROZEN_GOLDEN_CASE_COUNT,
    )


def compute_approval_record_digest(record: Mapping[str, Any]) -> str:
    """Hash one record excluding its self-referential digest field.

    This helper establishes record integrity only. It neither signs a record nor
    supplies reviewer authority or a scientific decision.
    """

    if not isinstance(record, Mapping):
        raise ApprovalArtifactFormatError("approval record must be an object")
    payload = dict(record)
    payload.pop("approval_record_digest", None)
    return canonical_sha256(payload).hex()


def _nonblank(value: Any) -> bool:
    return (
        type(value) is str
        and bool(value.strip())
        and "<" not in value
        and ">" not in value
    )


def _forbidden_reviewer_identity(value: Any) -> bool:
    if type(value) is not str:
        return False
    tokens = set(re.findall(r"[a-z0-9]+", value.casefold()))
    return bool(tokens & _FORBIDDEN_REVIEWER_IDENTITY_TOKENS)


def _valid_utc_timestamp(value: Any) -> bool:
    if type(value) is not str or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)


def validate_external_scientific_approval(
    record: Any,
    frozen: FrozenSelectionPackage,
) -> ApprovalValidation:
    """Validate one external record without treating software as scientific authority."""

    if type(record) is not dict:
        return ApprovalValidation(APPROVAL_REQUIRED, ("approval_record_must_be_object",))

    errors: list[str] = []
    keys = frozenset(record)
    for missing in sorted(_REQUIRED_KEYS - keys):
        errors.append(f"missing_field:{missing}")
    for unknown in sorted(keys - _REQUIRED_KEYS - _OPTIONAL_KEYS):
        errors.append(f"unknown_field:{unknown}")

    if record.get("approval_schema") != APPROVAL_SCHEMA:
        errors.append("invalid_approval_schema")
    if record.get("approval_schema_version") != APPROVAL_SCHEMA_VERSION:
        errors.append("invalid_approval_schema_version")
    if not _nonblank(record.get("approval_key")):
        errors.append("invalid_approval_key")
    if record.get("policy_key") != FROZEN_POLICY_KEY:
        errors.append("policy_key_mismatch")
    if record.get("policy_version") != frozen.policy_version:
        errors.append("policy_version_mismatch")
    if record.get("selection_policy_digest") != frozen.policy_digest:
        errors.append("selection_policy_digest_mismatch")

    decision = record.get("decision")
    if decision not in DECISIONS:
        errors.append("invalid_decision")
    role = record.get("role")
    if role not in ROLES:
        errors.append("invalid_role")
    elif role != "scientific_reviewer":
        errors.append("scientific_reviewer_role_required")
    reviewer_identity = record.get("reviewer_identity")
    if not _nonblank(reviewer_identity):
        errors.append("invalid_reviewer_identity")
    elif _forbidden_reviewer_identity(reviewer_identity):
        errors.append("non_external_reviewer_identity")
    if not _valid_utc_timestamp(record.get("reviewed_at")):
        errors.append("invalid_reviewed_at")
    if record.get("candidate_review_confirmed") is not True:
        errors.append("candidate_review_not_confirmed")
    if record.get("golden_corpus_review_confirmed") is not True:
        errors.append("golden_corpus_review_not_confirmed")
    scope = record.get("scope")
    if (
        type(scope) is not list
        or any(type(item) is not str for item in scope)
        or tuple(scope) != REQUIRED_SCOPE
    ):
        errors.append("invalid_review_scope")

    approved_items = record.get("approved_category_C_items")
    if type(approved_items) is not list or any(type(item) is not str for item in approved_items):
        errors.append("invalid_approved_category_C_items")
    else:
        if len(approved_items) != len(set(approved_items)):
            errors.append("duplicate_approved_category_C_item")
        unknown_items = sorted(set(approved_items) - set(MANDATORY_CATEGORY_C_ITEMS))
        if unknown_items:
            errors.extend(f"unknown_category_C_item:{item}" for item in unknown_items)
        if decision == "approved" and tuple(approved_items) != MANDATORY_CATEGORY_C_ITEMS:
            errors.append("mandatory_category_C_items_not_fully_approved")

    golden_reference = record.get("golden_case_set_reference")
    if type(golden_reference) is not dict or frozenset(golden_reference) != {"schema", "digest"}:
        errors.append("invalid_golden_case_set_reference")
    else:
        if golden_reference.get("schema") != GOLDEN_CORPUS_SCHEMA_REFERENCE:
            errors.append("golden_corpus_schema_mismatch")
        if golden_reference.get("digest") != frozen.golden_corpus_digest:
            errors.append("golden_corpus_digest_mismatch")

    if not _nonblank(record.get("governed_audit_reference")):
        errors.append("governed_audit_reference_required")
    notes = record.get("notes_reference")
    if notes is not None and not _nonblank(notes):
        errors.append("invalid_notes_reference")

    record_digest = record.get("approval_record_digest")
    if type(record_digest) is not str or _HEX_DIGEST.fullmatch(record_digest) is None:
        errors.append("invalid_approval_record_digest")
    else:
        try:
            calculated_digest = compute_approval_record_digest(record)
        except Exception:
            errors.append("approval_record_not_canonicalizable")
        else:
            if record_digest != calculated_digest:
                errors.append("approval_record_digest_mismatch")

    if errors:
        return ApprovalValidation(
            APPROVAL_REQUIRED,
            tuple(errors),
            decision if decision in DECISIONS else None,
            reviewer_identity if type(reviewer_identity) is str else None,
        )
    if decision == "approved":
        status = APPROVAL_VALID
    elif decision == "rejected":
        status = APPROVAL_REJECTED
    else:
        status = CHANGES_REQUESTED
    return ApprovalValidation(status, (), decision, reviewer_identity)


def evaluate_repository_approval_gate(
    repository_root: Path | str,
    approval_path: Path | str | None = None,
) -> ApprovalValidation:
    """Evaluate the fixed repository gate without creating or modifying artifacts."""

    root = Path(repository_root)
    try:
        frozen = load_frozen_selection_package(root)
    except (FrozenSelectionPackageIntegrityError, ApprovalArtifactFormatError) as exc:
        return ApprovalValidation(APPROVAL_REQUIRED, (f"frozen_package_invalid:{exc}",))

    path = Path(approval_path) if approval_path is not None else root / APPROVAL_ARTIFACT_FILENAME
    if not path.is_file():
        return ApprovalValidation(APPROVAL_REQUIRED, ("approval_artifact_missing",))
    try:
        record = _load_json_object(path)
    except ApprovalArtifactFormatError as exc:
        return ApprovalValidation(APPROVAL_REQUIRED, (f"malformed_approval_artifact:{exc}",))
    return validate_external_scientific_approval(record, frozen)
