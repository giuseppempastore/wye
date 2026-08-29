"""Execute a prepared parser run without holding database locks while parsing."""

from dataclasses import dataclass
import psycopg2.extras

from app.db import get_connection
from app.repositories.scientific_persistence import PostgresScientificPersistenceRepository
from app.scientific_ingestion.checksums import parser_output_checksum
from app.scientific_ingestion.errors import ScientificParserError, ScientificPersistenceConflict
from app.services.scientific_ingestion import ScientificInvalidRunTransition


@dataclass(frozen=True)
class ScientificRejectedResolution:
    source_record_key: str
    reason_code: str


@dataclass(frozen=True)
class ScientificExecutionResult:
    run_id: int
    run_status: str
    records_seen: int
    records_accepted: int
    records_rejected: int
    assessments_written: int
    findings_written: int
    warnings_count: int
    parser_output_checksum: str | None
    rejected_resolutions: tuple[ScientificRejectedResolution, ...] = ()
    reused_terminal_run: bool = False


class ScientificIngestionExecutor:
    """Parse outside transactions, persist record batches, then finalize briefly."""

    def __init__(self, parser, resolver, ingestion_service, repository=None,
                 connection_factory=get_connection, resolution_review_service=None):
        self.parser = parser
        self.resolver = resolver
        self.ingestion_service = ingestion_service
        self.repository = repository or PostgresScientificPersistenceRepository()
        self.connection_factory = connection_factory
        self.resolution_review_service = resolution_review_service

    def execute(self, prepared):
        context = self._load_context(prepared.id)
        self._validate_prepared(context, prepared)
        if context["run_status"] == "succeeded":
            return self._terminal_result(context)
        if context["run_status"] in ("failed", "cancelled"):
            raise ScientificInvalidRunTransition("terminal failed/cancelled run requires a new run")
        if context["run_status"] == "pending":
            try:
                self.ingestion_service.mark_running(prepared.id)
            except ScientificInvalidRunTransition:
                context = self._load_context(prepared.id)
                if context["run_status"] == "succeeded":
                    return self._terminal_result(context)
                if context["run_status"] != "running":
                    raise
        try:
            parsed = self.parser.parse(prepared.manifest)
            if parsed.parser_version != context["parser_version"]:
                raise ScientificParserError("parser result version differs from prepared run")
            if parsed.normalization_schema_version != context["normalization_schema_version"]:
                raise ScientificParserError("normalization version differs from prepared run")
            output_checksum = parser_output_checksum(parsed)
            resolved, rejected = [], [
                ScientificRejectedResolution(item.source_record_key, item.error_code)
                for item in parsed.rejected_records
            ]
            for record in parsed.records:
                resolution = self.resolver.resolve(record)
                if resolution.status == "resolved" and resolution.record is not None:
                    resolved.append(resolution.record)
                else:
                    if self.resolution_review_service is not None:
                        self.resolution_review_service.record_resolution(
                            prepared.id, record, resolution,
                            {"executor": "scientific_ingestion_v1"},
                        )
                    rejected.append(ScientificRejectedResolution(
                        record.source_record_key,
                        resolution.reason_code or f"substance_{resolution.status}",
                    ))
            finding_count = 0
            for record in resolved:
                persisted = self._persist_one(prepared.id, context["release_id"], record)
                finding_count += len(persisted.finding_ids)
            counters = dict(
                records_seen=parsed.records_seen,
                records_accepted=len(resolved), records_rejected=len(rejected),
                assessments_written=len(resolved), findings_written=finding_count,
                warnings_count=parsed.warnings_count,
            )
            self._finalize(prepared.id, output_checksum, counters)
            return ScientificExecutionResult(
                prepared.id, "succeeded", parser_output_checksum=output_checksum,
                rejected_resolutions=tuple(rejected), **counters
            )
        except Exception as exc:
            try:
                current = self._load_context(prepared.id)
                if current["run_status"] == "running":
                    self.ingestion_service.mark_failed(
                        prepared.id, getattr(exc, "code", "scientific_execution_failed"),
                        str(exc)[:2000],
                    )
            except Exception:
                pass
            raise

    def _persist_one(self, run_id, release_id, record):
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                context = self.repository.load_run_context(cursor, run_id)
                if context is None or context["release_id"] != release_id or context["run_status"] != "running":
                    raise ScientificPersistenceConflict("run/release coherence or status changed")
                persisted = self.repository.persist_record(cursor, run_id, release_id, record)
            connection.commit()
            return persisted
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _load_context(self, run_id):
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                context = self.repository.load_run_context(cursor, run_id)
            if context is None:
                raise ScientificPersistenceConflict("prepared ingestion run was not found")
            return context
        finally:
            connection.close()

    def _finalize(self, run_id, checksum, counters):
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                updated = self.repository.finalize_succeeded(cursor, run_id, checksum, counters)
                if not updated:
                    current = self.repository.load_run_context(cursor, run_id)
                    if current is None or current["run_status"] != "succeeded" or current["parser_output_checksum_value"] != checksum:
                        raise ScientificPersistenceConflict("run finalization conflict")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _validate_prepared(context, prepared):
        if str(context["run_key"]) != str(prepared.run_key):
            raise ScientificPersistenceConflict("prepared run key does not match persisted run")
        if (context["artifact_manifest_algorithm"] != prepared.manifest.fingerprint_algorithm
                or context["artifact_manifest_fingerprint"] != prepared.manifest.fingerprint):
            raise ScientificPersistenceConflict("prepared manifest does not match persisted run")

    @staticmethod
    def _terminal_result(context):
        return ScientificExecutionResult(
            run_id=context["id"], run_status="succeeded",
            records_seen=context["records_seen"], records_accepted=context["records_accepted"],
            records_rejected=context["records_rejected"],
            assessments_written=context["assessments_written"],
            findings_written=context["findings_written"],warnings_count=context["warnings_count"],
            parser_output_checksum=context["parser_output_checksum_value"],
            reused_terminal_run=True,
        )
