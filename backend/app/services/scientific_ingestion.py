"""Atomic orchestration of scientific run identity and artifact provenance."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID, uuid4

import psycopg2
import psycopg2.extras

from app.db import get_connection
from app.repositories.scientific_ingestion import PostgresScientificIngestionRepository
from app.scientific_ingestion.contracts import ScientificArtifactManifest, ScientificArtifactReference
from app.scientific_ingestion.errors import ScientificIngestionError, ScientificPersistenceConflict


class ScientificResourceNotFound(ScientificIngestionError):
    code = "scientific_resource_not_found"


class ScientificArtifactIntegrityError(ScientificIngestionError):
    code = "scientific_artifact_integrity_error"


class ScientificInvalidRunTransition(ScientificIngestionError):
    code = "scientific_invalid_run_transition"


@dataclass(frozen=True)
class PreparedScientificIngestionRun:
    id: int
    run_key: UUID
    status: str
    manifest: ScientificArtifactManifest
    reused: bool


class ScientificIngestionService:
    """Create one run and its exact canonical artifact membership atomically."""

    def __init__(self, repository=None, connection_factory: Callable = get_connection,
                 importer_name="wye_scientific_ingestion",
                 importer_version="scientific_ingestion_service_v1",
                 clock=lambda: datetime.now(timezone.utc), run_key_factory=uuid4):
        self.repository = repository or PostgresScientificIngestionRepository()
        self.connection_factory = connection_factory
        self.importer_name = importer_name
        self.importer_version = importer_version
        self.clock = clock
        self.run_key_factory = run_key_factory

    def prepare_ingestion_run(self, release, configuration, artifact_keys,
                              idempotency_key=None):
        adapter = configuration.adapter
        if (adapter.source_key, adapter.dataset_key) != (release.source_key, release.dataset_key):
            raise ScientificArtifactIntegrityError("configuration identity does not match release")
        artifact_keys = tuple(artifact_keys)
        if not artifact_keys or len(set(artifact_keys)) != len(artifact_keys):
            raise ScientificArtifactIntegrityError("artifact selection must be non-empty and unique")
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                release_row = self.repository.resolve_release(
                    cursor, release.source_key, release.dataset_key, release.external_release_key)
                if release_row is None:
                    raise ScientificResourceNotFound("scientific release was not found")
                artifacts = self.repository.load_artifacts(cursor, release_row.id, artifact_keys)
                if len(artifacts) != len(artifact_keys):
                    raise ScientificResourceNotFound("one or more selected artifacts were not found")
                self._validate_artifacts(release_row.id, artifacts)
                references = tuple(ScientificArtifactReference(
                    artifact_key=a.artifact_key, artifact_role=a.artifact_role,
                    storage_object_id=a.storage_object_id,
                    raw_checksum_algorithm=a.raw_checksum_algorithm,
                    raw_checksum_value=a.raw_checksum_value, byte_size=a.byte_size,
                    source_locator=a.source_locator, content_type=a.content_type,
                    acquisition_metadata=a.acquisition_metadata,
                ) for a in artifacts)
                manifest = ScientificArtifactManifest.build(release, references)
                values = self._run_values(release_row.id, configuration, manifest, idempotency_key)
                run, reused = self._create_or_reconcile(cursor, values, artifacts)
            connection.commit()
            return PreparedScientificIngestionRun(run.id, run.run_key, run.run_status, manifest, reused)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_run(self, run_key):
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                return self.repository.get_run_by_key(cursor, run_key)
        finally:
            connection.close()

    def mark_running(self, run_id):
        return self._transition(run_id, ("pending",), "running")

    def mark_succeeded(self, run_id, **counters):
        expected = {"records_seen", "records_accepted", "records_rejected",
                    "assessments_written", "findings_written", "warnings_count"}
        if set(counters) != expected or any(value < 0 for value in counters.values()):
            raise ScientificInvalidRunTransition("all non-negative terminal counters are required")
        if counters["records_accepted"] + counters["records_rejected"] > counters["records_seen"]:
            raise ScientificInvalidRunTransition("accepted and rejected records exceed records seen")
        return self._transition(run_id, ("running",), "succeeded", counters)

    def mark_failed(self, run_id, error_code, error_summary=None):
        if not error_code or not error_code.strip():
            raise ScientificInvalidRunTransition("failed runs require an error code")
        return self._transition(run_id, ("running",), "failed",
                                {"error_code": error_code, "error_summary": error_summary})

    def mark_cancelled(self, run_id):
        return self._transition(run_id, ("pending", "running"), "cancelled")

    def _transition(self, run_id, from_statuses, to_status, values=None):
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                run = self.repository.transition_run(cursor, run_id, from_statuses, to_status,
                    {"at": self.clock(), **(values or {})})
                if run is None:
                    raise ScientificInvalidRunTransition(f"run cannot transition to {to_status}")
            connection.commit()
            return run
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _create_or_reconcile(self, cursor, values, artifacts):
        cursor.execute("SAVEPOINT scientific_run_insert")
        try:
            run = self.repository.create_run(cursor, values)
            self.repository.persist_membership(cursor, run.id, artifacts)
            cursor.execute("RELEASE SAVEPOINT scientific_run_insert")
            return run, False
        except psycopg2.IntegrityError as exc:
            constraint = getattr(exc.diag, "constraint_name", None)
            cursor.execute("ROLLBACK TO SAVEPOINT scientific_run_insert")
            if constraint != self.repository.IDEMPOTENCY_CONSTRAINT or values["idempotency_key"] is None:
                raise ScientificPersistenceConflict(f"persistence constraint conflict: {constraint}") from exc
            run = self.repository.find_idempotent_run(cursor, values)
            expected_ids = tuple(artifact.id for artifact in artifacts)
            if run is None or self.repository.membership_ids(cursor, run.id) != expected_ids:
                raise ScientificPersistenceConflict("idempotent run membership does not match") from exc
            return run, True

    @staticmethod
    def _validate_artifacts(release_id, artifacts):
        for artifact in artifacts:
            if artifact.release_id != release_id:
                raise ScientificArtifactIntegrityError("artifact belongs to another release")
            if artifact.storage_checksum_algorithm is not None and (
                artifact.storage_checksum_algorithm != artifact.raw_checksum_algorithm
                or artifact.storage_checksum_value != artifact.raw_checksum_value):
                raise ScientificArtifactIntegrityError("artifact and storage checksums differ")
            if (artifact.storage_byte_size is not None and artifact.byte_size is not None
                    and artifact.storage_byte_size != artifact.byte_size):
                raise ScientificArtifactIntegrityError("artifact and storage byte sizes differ")

    def _run_values(self, release_id, configuration, manifest, idempotency_key):
        adapter = configuration.adapter
        return {
            "release_id": release_id, "run_key": str(self.run_key_factory()),
            "idempotency_key": idempotency_key, "importer_name": self.importer_name,
            "importer_version": self.importer_version,
            "source_adapter_version": adapter.adapter_version,
            "acquisition_version": adapter.acquisition_version,
            "parser_version": adapter.parser_version,
            "normalization_schema_version": adapter.normalization_schema_version,
            "artifact_manifest_algorithm": manifest.fingerprint_algorithm,
            "artifact_manifest_fingerprint": manifest.fingerprint,
            "config_checksum_algorithm": configuration.fingerprint_algorithm,
            "config_checksum_value": configuration.fingerprint,
            "provenance": {"manifest_canonicalization_version": manifest.canonicalization_version,
                           "config_canonicalization_version": configuration.canonicalization_version},
        }
