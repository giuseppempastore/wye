"""Explicit boundary between ingestion and the future substance registry workflow."""

from typing import Literal, Protocol, runtime_checkable

from pydantic import Field

from .contracts import FrozenContract, NonEmptyText, ScientificParsedRecord


class ResolvedScientificRecord(FrozenContract):
    """A parsed record whose canonical substance was supplied externally."""

    source_record_key: NonEmptyText
    substance_id: int = Field(gt=0)
    parsed_record: ScientificParsedRecord


ResolutionStatus = Literal["resolved", "unresolved", "ambiguous", "rejected"]

DiagnosticOutcome = Literal[
    "matched", "unmatched", "unknown_namespace", "ignored_identifier_status",
    "inactive_substance", "deprecated_substance",
]


class SubstanceIdentifierResolutionDiagnostic(FrozenContract):
    namespace_key: NonEmptyText
    namespace_version: NonEmptyText
    normalized_value: NonEmptyText
    outcome: DiagnosticOutcome
    namespace_id: int | None = None
    identifier_id: int | None = None
    identifier_status: str | None = None
    substance_id: int | None = None
    substance_status: str | None = None

class ScientificSubstanceResolution(FrozenContract):
    status: ResolutionStatus
    record: ResolvedScientificRecord | None = None
    reason_code: NonEmptyText | None = None
    diagnostics: tuple[SubstanceIdentifierResolutionDiagnostic, ...] = ()
    conflicting_substance_ids: tuple[int, ...] = ()

    @classmethod
    def resolved(cls, parsed_record: ScientificParsedRecord, substance_id: int,
                 diagnostics: tuple[SubstanceIdentifierResolutionDiagnostic, ...] = ()):
        return cls(
            status="resolved",
            record=ResolvedScientificRecord(
                source_record_key=parsed_record.source_record_key,
                substance_id=substance_id,
                parsed_record=parsed_record,
            ),
            diagnostics=diagnostics,
        )
@runtime_checkable
class ScientificSubstanceResolver(Protocol):
    def resolve(self, record: ScientificParsedRecord) -> ScientificSubstanceResolution: ...


class FakeScientificSubstanceResolver:
    """Deterministic test-only resolver; it performs no identifier lookup."""

    def __init__(self, substance_ids: dict[str, int], statuses: dict[str, str] | None = None):
        self.substance_ids = dict(substance_ids)
        self.statuses = dict(statuses or {})

    def resolve(self, record: ScientificParsedRecord) -> ScientificSubstanceResolution:
        status = self.statuses.get(record.source_record_key, "resolved")
        if status == "resolved" and record.source_record_key in self.substance_ids:
            return ScientificSubstanceResolution.resolved(
                record, self.substance_ids[record.source_record_key]
            )
        if status == "resolved":
            status = "unresolved"
        return ScientificSubstanceResolution(
            status=status,
            reason_code=f"substance_{status}",
        )
