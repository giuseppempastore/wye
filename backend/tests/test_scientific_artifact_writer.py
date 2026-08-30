"""PostgreSQL integration tests for the canonical scientific artifact writer."""

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
import uuid

import psycopg2
from psycopg2 import errors
from psycopg2.extras import Json

from app.db import _parse_user_postgres_file
from app.scientific_evaluation.artifact_contracts import build_artifact_envelope
from app.scientific_evaluation.canonicalization import canonicalize_json
from app.scientific_evaluation.errors import (
    ArtifactBytesUnavailableError,
    ArtifactContractError,
    ArtifactIntegrityError,
    IncompatibleArtifactError,
    InvalidArtifactLocationError,
)
from app.services.scientific_evaluation_artifacts import (
    ScientificArtifactWriteRequest,
    ScientificArtifactWriter,
)


BACKEND = Path(__file__).resolve().parents[1]
REPOSITORY = BACKEND.parent


def _postgres_settings(database="postgres"):
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    if not user or not password:
        file_user, file_password = _parse_user_postgres_file(
            REPOSITORY / "postgres" / "user_postgres.txt"
        )
        user = user or file_user
        password = password or file_password
    if not user or not password:
        raise RuntimeError("PostgreSQL test credentials are unavailable")
    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "user": user,
        "password": password,
        "dbname": database,
    }


def _connection(database):
    return psycopg2.connect(**_postgres_settings(database))


def _alembic(database, *args):
    environment = os.environ.copy()
    settings = _postgres_settings(database)
    environment.update(
        {
            "PGHOST": str(settings["host"]),
            "PGPORT": str(settings["port"]),
            "PGUSER": str(settings["user"]),
            "PGPASSWORD": str(settings["password"]),
            "PGDATABASE": database,
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)


def _create_database():
    database = f"wye_test_artifact_writer_{uuid.uuid4().hex[:12]}"
    connection = _connection("postgres")
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{database}"')
    finally:
        connection.close()
    return database


def _drop_database(database):
    connection = _connection("postgres")
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname=%s AND pid <> pg_backend_pid()",
                (database,),
            )
            cursor.execute(f'DROP DATABASE IF EXISTS "{database}"')
    finally:
        connection.close()


def _request(seed="one", kind="scientific_evidence_snapshot_query", schema="1"):
    return ScientificArtifactWriteRequest(
        artifact_kind=kind,
        schema_version=schema,
        payload={"scope": {"seed": seed}, "technical_predicates": []},
    )


def _canonical(request):
    envelope = build_artifact_envelope(
        request.artifact_kind,
        request.schema_version,
        request.payload,
        canonicalization_version=request.canonicalization_version,
        content_type=request.content_type,
    )
    canonical_bytes = canonicalize_json(envelope)
    return envelope, canonical_bytes, sha256(canonical_bytes).digest()


@unittest.skipUnless(
    os.getenv("WYE_RUN_ARTIFACT_WRITER_POSTGRES_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificArtifactWriterPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = _create_database()
        try:
            _alembic(cls.database, "upgrade", "head")
        except Exception:
            _drop_database(cls.database)
            raise

    @classmethod
    def tearDownClass(cls):
        _drop_database(cls.database)

    def setUp(self):
        self.connection = _connection(self.database)
        self.connection.autocommit = False
        self.cursor = self.connection.cursor()
        self.writer = ScientificArtifactWriter()

    def tearDown(self):
        try:
            self.connection.rollback()
        finally:
            self.cursor.close()
            self.connection.close()

    def test_create_and_retry_reuse_one_artifact_and_inline_location(self):
        request = _request("retry")
        first = self.writer.write_verified_inline(self.cursor, request)
        second = self.writer.write_verified_inline(self.cursor, request)
        self.assertFalse(first.artifact_reused)
        self.assertFalse(first.location_reused)
        self.assertTrue(second.artifact_reused)
        self.assertTrue(second.location_reused)
        self.assertEqual(first.artifact.id, second.artifact.id)
        self.assertEqual(first.location.id, second.location.id)
        self.assertEqual(first.artifact.content_digest, sha256(first.canonical_bytes).digest())
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_artifacts WHERE id=%s",
            (first.artifact.id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_artifact_locations "
            "WHERE artifact_id=%s",
            (first.artifact.id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)
        self.cursor.execute(
            "SELECT storage_mode,storage_object_id,location_status,"
            "verified_at IS NOT NULL,octet_length(canonical_bytes) "
            "FROM scientific_evaluation_artifact_locations WHERE id=%s",
            (first.location.id,),
        )
        self.assertEqual(
            self.cursor.fetchone(),
            ("inline", None, "verified", True, len(first.canonical_bytes)),
        )

    def test_jsonb_cache_is_canonical_envelope_but_not_hash_source(self):
        request = _request("cache")
        persisted = self.writer.write_verified_inline(self.cursor, request)
        envelope, canonical_bytes, _ = _canonical(request)
        self.assertEqual(persisted.artifact.json_payload, envelope)
        self.assertEqual(persisted.canonical_bytes, canonical_bytes)
        self.assertNotEqual(
            json.dumps(envelope).encode("utf-8"),
            persisted.canonical_bytes,
        )

    def test_u0000_payload_omits_optional_jsonb_cache_but_keeps_exact_bytes(self):
        request = ScientificArtifactWriteRequest(
            artifact_kind="scientific_evidence_snapshot_query",
            schema_version="1",
            payload={"key\x00": "value\x00"},
        )
        first = self.writer.write_verified_inline(self.cursor, request)
        second = self.writer.write_verified_inline(self.cursor, request)
        self.assertIsNone(first.artifact.json_payload)
        self.assertIn(b"\\u0000", first.canonical_bytes)
        self.assertEqual(first.artifact.content_length, len(first.canonical_bytes))
        self.assertEqual(first.location.canonical_bytes, first.canonical_bytes)
        self.assertEqual(first.artifact.id, second.artifact.id)
        self.assertEqual(first.location.id, second.location.id)

    def test_writer_does_not_commit_caller_transaction(self):
        persisted = self.writer.write_verified_inline(self.cursor, _request("transaction"))
        observer = _connection(self.database)
        try:
            with observer.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM scientific_evaluation_artifacts WHERE id=%s",
                    (persisted.artifact.id,),
                )
                self.assertEqual(cursor.fetchone()[0], 0)
            self.connection.commit()
            with observer.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM scientific_evaluation_artifacts WHERE id=%s",
                    (persisted.artifact.id,),
                )
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            observer.close()

    def test_rollback_leaves_no_artifact_or_location(self):
        persisted = self.writer.write_verified_inline(self.cursor, _request("rollback"))
        digest = persisted.artifact.content_digest
        self.connection.rollback()
        observer = _connection(self.database)
        try:
            with observer.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM scientific_evaluation_artifacts "
                    "WHERE content_digest=%s",
                    (digest,),
                )
                self.assertEqual(cursor.fetchone()[0], 0)
        finally:
            observer.close()

    def test_unknown_kind_schema_and_canonicalization_fail_before_write(self):
        self.cursor.execute("SELECT count(*) FROM scientific_evaluation_artifacts")
        count_before = self.cursor.fetchone()[0]
        requests = (
            _request("kind", kind="future_artifact"),
            _request("schema", schema="2"),
            ScientificArtifactWriteRequest(
                "protocol_definition", "1", {}, canonicalization_version="other"
            ),
        )
        for request in requests:
            with self.subTest(request=request), self.assertRaises(ArtifactContractError):
                self.writer.write_verified_inline(self.cursor, request)
        self.cursor.execute("SELECT count(*) FROM scientific_evaluation_artifacts")
        self.assertEqual(self.cursor.fetchone()[0], count_before)

    def test_existing_digest_with_incompatible_metadata_fails_explicitly(self):
        request = _request("metadata")
        envelope, canonical_bytes, digest = _canonical(request)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,json_payload,verified_at) "
            "VALUES('protocol_review','1','wye-c14n-json-v1','sha256',%s,%s,"
            "'application/vnd.wye.scientific+json',%s,NOW())",
            (digest, len(canonical_bytes), Json(envelope)),
        )
        with self.assertRaises(IncompatibleArtifactError):
            self.writer.write_verified_inline(self.cursor, request)

    def test_existing_identity_with_incompatible_jsonb_cache_fails_explicitly(self):
        request = _request("bad-cache")
        _, canonical_bytes, digest = _canonical(request)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,json_payload,verified_at) "
            "VALUES(%s,%s,'wye-c14n-json-v1','sha256',%s,%s,"
            "'application/vnd.wye.scientific+json',%s,NOW())",
            (
                request.artifact_kind,
                request.schema_version,
                digest,
                len(canonical_bytes),
                Json({"incompatible": True}),
            ),
        )
        with self.assertRaises(IncompatibleArtifactError):
            self.writer.write_verified_inline(self.cursor, request)

    def test_existing_identity_without_authoritative_inline_bytes_is_not_reused(self):
        request = _request("no-bytes")
        envelope, canonical_bytes, digest = _canonical(request)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,json_payload,verified_at) "
            "VALUES(%s,%s,'wye-c14n-json-v1','sha256',%s,%s,"
            "'application/vnd.wye.scientific+json',%s,NOW())",
            (
                request.artifact_kind,
                request.schema_version,
                digest,
                len(canonical_bytes),
                Json(envelope),
            ),
        )
        with self.assertRaises(ArtifactBytesUnavailableError):
            self.writer.write_verified_inline(self.cursor, request)

    def test_verified_inline_hash_mismatch_is_an_integrity_error(self):
        request = _request("bad-bytes")
        envelope, canonical_bytes, digest = _canonical(request)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,json_payload,verified_at) "
            "VALUES(%s,%s,'wye-c14n-json-v1','sha256',%s,%s,"
            "'application/vnd.wye.scientific+json',%s,NOW()) RETURNING id",
            (
                request.artifact_kind,
                request.schema_version,
                digest,
                len(canonical_bytes),
                Json(envelope),
            ),
        )
        artifact_id = self.cursor.fetchone()[0]
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifact_locations "
            "(location_key,artifact_id,storage_mode,canonical_bytes,location_status,"
            "verified_at) VALUES(%s,%s,'inline',%s,'verified',NOW())",
            (str(uuid.uuid4()), artifact_id, b"x" * len(canonical_bytes)),
        )
        with self.assertRaises(ArtifactIntegrityError):
            self.writer.write_verified_inline(self.cursor, request)

    def test_nonverified_inline_location_is_rejected(self):
        request = _request("quarantined")
        envelope, canonical_bytes, digest = _canonical(request)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,json_payload,verified_at) "
            "VALUES(%s,%s,'wye-c14n-json-v1','sha256',%s,%s,"
            "'application/vnd.wye.scientific+json',%s,NOW()) RETURNING id",
            (
                request.artifact_kind,
                request.schema_version,
                digest,
                len(canonical_bytes),
                Json(envelope),
            ),
        )
        artifact_id = self.cursor.fetchone()[0]
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifact_locations "
            "(location_key,artifact_id,storage_mode,canonical_bytes,location_status) "
            "VALUES(%s,%s,'inline',%s,'quarantined')",
            (str(uuid.uuid4()), artifact_id, canonical_bytes),
        )
        with self.assertRaises(InvalidArtifactLocationError):
            self.writer.write_verified_inline(self.cursor, request)

    def test_database_location_immutability_remains_authoritative(self):
        persisted = self.writer.write_verified_inline(self.cursor, _request("immutable"))
        self.connection.commit()
        with self.connection.cursor() as cursor:
            with self.assertRaises(errors.ObjectNotInPrerequisiteState):
                cursor.execute(
                    "UPDATE scientific_evaluation_artifact_locations "
                    "SET canonical_bytes=%s WHERE id=%s",
                    (
                        b"x" * len(persisted.canonical_bytes),
                        persisted.location.id,
                    ),
                )

    def test_concurrent_identical_writers_converge(self):
        request = _request("concurrent")
        _, _, digest = _canonical(request)
        barrier = threading.Barrier(2)
        outcomes = []
        outcome_lock = threading.Lock()

        def worker():
            connection = _connection(self.database)
            try:
                with connection.cursor() as cursor:
                    barrier.wait(timeout=10)
                    persisted = ScientificArtifactWriter().write_verified_inline(
                        cursor, request
                    )
                connection.commit()
                outcome = (persisted.artifact.id, persisted.location.id)
            finally:
                connection.close()
            with outcome_lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(len(outcomes), 2)
        self.assertEqual(outcomes[0], outcomes[1])
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_artifacts "
            "WHERE content_digest=%s",
            (digest,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)
        self.cursor.execute(
            "SELECT count(*) FROM scientific_evaluation_artifact_locations l "
            "JOIN scientific_evaluation_artifacts a ON a.id=l.artifact_id "
            "WHERE a.content_digest=%s",
            (digest,),
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
