"""Deterministic integrity validation for the Phase 7.7.4 review delivery.

The validator proves package composition and byte identity only. It does not
assess scientific correctness, reviewer competence, reviewer authenticity, or
scientific approval, and it has no database or network dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app.scientific_evaluation.canonicalization import canonical_sha256
from app.scientific_evaluation.selection_approval import (
    FROZEN_GOLDEN_CORPUS_DIGEST,
    FROZEN_POLICY_DIGEST,
    FROZEN_POLICY_VERSION,
    ApprovalArtifactFormatError,
    FrozenSelectionPackageIntegrityError,
    load_frozen_selection_package,
)


DELIVERY_PACKAGE_RELATIVE_PATH = Path(
    "external_review/selection_policy_1.0.0-candidate.1"
)
DELIVERY_MANIFEST_FILENAME = "DELIVERY_MANIFEST.json"
DELIVERY_MANIFEST_SCHEMA = "wye_external_scientific_review_delivery_manifest"
DELIVERY_MANIFEST_SCHEMA_VERSION = "1"
DELIVERY_CONTENT_SCHEMA = "wye_external_scientific_review_delivery_content"
DELIVERY_CONTENT_SCHEMA_VERSION = "1"
DELIVERY_PACKAGE_KEY = "selection_policy_1.0.0-candidate.1"
DELIVERY_SOURCE_HEAD = "15c2ae425c9a11fb3c39e703a958a653a1e5f6e3"
DELIVERY_CONTENT_DIGEST = (
    "0430725210a2857c92f0c3d78a6f1f4c11b96be891030205808d0e422126dec1"
)
DELIVERY_MANIFEST_DIGEST = (
    "6073e3f77abb756d2670cae404b5a96c9706242c63295d6ee449a0691fda49b9"
)


class ReviewDeliveryIntegrityError(RuntimeError):
    """The governed external-review delivery package is incomplete or changed."""


@dataclass(frozen=True)
class ReviewDeliveryValidation:
    package_path: Path
    file_count: int
    manifest_digest: str
    package_content_digest: str
    candidate_version: str
    candidate_digest: str
    golden_corpus_digest: str


@dataclass(frozen=True)
class _ExpectedEntry:
    path: str
    artifact_role: str
    dependency_class: str
    original_repository_path: str | None
    frozen: bool
    supporting_only: bool


_EXPECTED_ENTRIES = (
    _ExpectedEntry(
        "README.md", "reviewer_readme", "generated", None, False, True
    ),
    _ExpectedEntry(
        "WYE_SELECTION_GOLDEN_CASES.md",
        "golden_corpus_document",
        "required",
        "WYE_SELECTION_GOLDEN_CASES.md",
        True,
        False,
    ),
    _ExpectedEntry(
        "WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json",
        "golden_corpus_manifest",
        "required",
        "WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json",
        True,
        False,
    ),
    _ExpectedEntry(
        "WYE_SELECTION_POLICY_CANDIDATE_V1.json",
        "selection_policy_candidate",
        "required",
        "WYE_SELECTION_POLICY_CANDIDATE_V1.json",
        True,
        False,
    ),
    _ExpectedEntry(
        "WYE_SELECTION_POLICY_EXTERNAL_REVIEW_HANDOFF.md",
        "external_review_handoff",
        "required",
        "WYE_SELECTION_POLICY_EXTERNAL_REVIEW_HANDOFF.md",
        False,
        False,
    ),
    _ExpectedEntry(
        "WYE_SELECTION_POLICY_FREEZE.md",
        "selection_policy_technical_freeze",
        "supporting",
        "WYE_SELECTION_POLICY_FREEZE.md",
        True,
        True,
    ),
    _ExpectedEntry(
        "WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md",
        "scientific_review_package",
        "required",
        "WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md",
        False,
        False,
    ),
)

_MANIFEST_KEYS = frozenset(
    {
        "canonicalization_version",
        "closed_set",
        "files",
        "manifest_path",
        "package_content_digest",
        "package_content_digest_algorithm",
        "package_key",
        "package_phase",
        "package_purpose",
        "review_subject",
        "schema_id",
        "schema_version",
        "source_repository",
    }
)
_ENTRY_KEYS = frozenset(
    {
        "artifact_role",
        "byte_size",
        "dependency_class",
        "frozen",
        "original_repository_path",
        "path",
        "scientifically_reviewed",
        "sha256",
        "supporting_only",
    }
)


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ReviewDeliveryIntegrityError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object
        )
    except ReviewDeliveryIntegrityError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewDeliveryIntegrityError(
            "delivery manifest is not valid unambiguous UTF-8 JSON"
        ) from exc
    if type(value) is not dict:
        raise ReviewDeliveryIntegrityError("delivery manifest must be one JSON object")
    return value


def _file_digest(path: Path) -> tuple[int, str, bytes]:
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ReviewDeliveryIntegrityError(f"cannot read package file: {path.name}") from exc
    return len(content), sha256(content).hexdigest(), content


def _content_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": DELIVERY_CONTENT_SCHEMA,
        "schema_version": DELIVERY_CONTENT_SCHEMA_VERSION,
        "package_key": manifest.get("package_key"),
        "files": manifest.get("files"),
    }


def validate_review_delivery(
    repository_root: Path | str,
    package_path: Path | str | None = None,
) -> ReviewDeliveryValidation:
    """Validate the exact closed Phase 7.7.4 delivery without side effects."""

    root = Path(repository_root)
    package = Path(package_path) if package_path is not None else root / DELIVERY_PACKAGE_RELATIVE_PATH
    manifest_path = package / DELIVERY_MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise ReviewDeliveryIntegrityError("required delivery manifest is missing")

    manifest = _load_manifest(manifest_path)
    if frozenset(manifest) != _MANIFEST_KEYS:
        raise ReviewDeliveryIntegrityError("delivery manifest fields do not match schema v1")
    if manifest.get("schema_id") != DELIVERY_MANIFEST_SCHEMA:
        raise ReviewDeliveryIntegrityError("delivery manifest schema_id mismatch")
    if manifest.get("schema_version") != DELIVERY_MANIFEST_SCHEMA_VERSION:
        raise ReviewDeliveryIntegrityError("delivery manifest schema_version mismatch")
    if manifest.get("canonicalization_version") != "wye-c14n-json-v1":
        raise ReviewDeliveryIntegrityError("delivery canonicalization mismatch")
    if manifest.get("closed_set") is not True:
        raise ReviewDeliveryIntegrityError("delivery package must declare a closed set")
    if manifest.get("manifest_path") != DELIVERY_MANIFEST_FILENAME:
        raise ReviewDeliveryIntegrityError("delivery manifest path mismatch")
    if manifest.get("package_key") != DELIVERY_PACKAGE_KEY:
        raise ReviewDeliveryIntegrityError("delivery package key mismatch")
    if manifest.get("package_phase") != "7.7.4":
        raise ReviewDeliveryIntegrityError("delivery package phase mismatch")
    if manifest.get("package_content_digest_algorithm") != "sha256":
        raise ReviewDeliveryIntegrityError("delivery content digest algorithm mismatch")
    if manifest.get("source_repository") != {
        "branch": "ingredients_score",
        "head": DELIVERY_SOURCE_HEAD,
    }:
        raise ReviewDeliveryIntegrityError("delivery source repository context mismatch")
    if manifest.get("review_subject") != {
        "candidate_version": FROZEN_POLICY_VERSION,
        "golden_case_count": 28,
        "golden_corpus_digest": FROZEN_GOLDEN_CORPUS_DIGEST,
        "scientific_approval_present": False,
        "selection_policy_digest": FROZEN_POLICY_DIGEST,
    }:
        raise ReviewDeliveryIntegrityError("delivery review subject mismatch")

    calculated_manifest_digest = canonical_sha256(manifest).hex()
    if calculated_manifest_digest != DELIVERY_MANIFEST_DIGEST:
        raise ReviewDeliveryIntegrityError("delivery manifest digest mismatch")
    calculated_content_digest = canonical_sha256(_content_payload(manifest)).hex()
    if manifest.get("package_content_digest") != calculated_content_digest:
        raise ReviewDeliveryIntegrityError("delivery package content digest mismatch")
    if calculated_content_digest != DELIVERY_CONTENT_DIGEST:
        raise ReviewDeliveryIntegrityError("delivery package content identity changed")

    entries = manifest.get("files")
    if type(entries) is not list or len(entries) != len(_EXPECTED_ENTRIES):
        raise ReviewDeliveryIntegrityError("delivery manifest file list is incomplete")

    expected_paths = {DELIVERY_MANIFEST_FILENAME, *(item.path for item in _EXPECTED_ENTRIES)}
    actual_paths = {
        item.relative_to(package).as_posix()
        for item in package.rglob("*")
        if item.is_file()
    }
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        unexpected = sorted(actual_paths - expected_paths)
        raise ReviewDeliveryIntegrityError(
            f"delivery closed-set mismatch; missing={missing}; unexpected={unexpected}"
        )

    try:
        frozen = load_frozen_selection_package(package)
    except (FrozenSelectionPackageIntegrityError, ApprovalArtifactFormatError) as exc:
        raise ReviewDeliveryIntegrityError(
            f"frozen review subject is invalid inside delivery: {exc}"
        ) from exc
    if frozen.policy_version != FROZEN_POLICY_VERSION:
        raise ReviewDeliveryIntegrityError("delivery candidate version mismatch")
    if frozen.policy_digest != FROZEN_POLICY_DIGEST:
        raise ReviewDeliveryIntegrityError("delivery candidate digest mismatch")
    if frozen.golden_corpus_digest != FROZEN_GOLDEN_CORPUS_DIGEST:
        raise ReviewDeliveryIntegrityError("delivery golden corpus digest mismatch")

    for entry, expected in zip(entries, _EXPECTED_ENTRIES, strict=True):
        if type(entry) is not dict or frozenset(entry) != _ENTRY_KEYS:
            raise ReviewDeliveryIntegrityError("delivery file entry shape mismatch")
        fixed_fields = {
            "artifact_role": expected.artifact_role,
            "dependency_class": expected.dependency_class,
            "frozen": expected.frozen,
            "original_repository_path": expected.original_repository_path,
            "path": expected.path,
            "scientifically_reviewed": False,
            "supporting_only": expected.supporting_only,
        }
        if any(entry.get(key) != value for key, value in fixed_fields.items()):
            raise ReviewDeliveryIntegrityError(
                f"delivery file classification mismatch: {expected.path}"
            )
        if type(entry.get("byte_size")) is not int or entry["byte_size"] < 0:
            raise ReviewDeliveryIntegrityError(
                f"invalid byte size in manifest: {expected.path}"
            )
        digest = entry.get("sha256")
        if type(digest) is not str or len(digest) != 64:
            raise ReviewDeliveryIntegrityError(
                f"invalid SHA-256 in manifest: {expected.path}"
            )

        copied_size, copied_digest, copied_bytes = _file_digest(package / expected.path)
        if copied_size != entry["byte_size"] or copied_digest != digest:
            raise ReviewDeliveryIntegrityError(
                f"delivery file size or digest mismatch: {expected.path}"
            )
        if expected.original_repository_path is not None:
            source_size, source_digest, source_bytes = _file_digest(
                root / expected.original_repository_path
            )
            if (
                source_size != copied_size
                or source_digest != copied_digest
                or source_bytes != copied_bytes
            ):
                raise ReviewDeliveryIntegrityError(
                    f"delivery copy differs from repository source: {expected.path}"
                )

    return ReviewDeliveryValidation(
        package_path=package,
        file_count=len(actual_paths),
        manifest_digest=calculated_manifest_digest,
        package_content_digest=calculated_content_digest,
        candidate_version=frozen.policy_version,
        candidate_digest=frozen.policy_digest,
        golden_corpus_digest=frozen.golden_corpus_digest,
    )
