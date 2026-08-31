import os
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import threading
import unittest
import uuid

import psycopg2
from psycopg2 import errors

from app.db import _parse_user_postgres_file


BACKEND = Path(__file__).resolve().parents[1]
REPOSITORY = BACKEND.parent
REVISION = "0019_scientific_evaluation_foundation"
PARENT_REVISION = "0018_scientific_batch_recovery"
REPOSITORY_HEAD = "0020_scientific_evidence_snapshots"
FOUNDATION_TABLES = (
    "scientific_evaluation_artifacts",
    "scientific_evaluation_artifact_locations",
    "scientific_evaluation_protocols",
    "scientific_evaluation_protocol_versions",
    "scientific_evaluation_governance_events",
)


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


def _alembic(database, *args, success=True):
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
    if success and result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    if not success and result.returncode == 0:
        raise AssertionError("Alembic command unexpectedly succeeded")
    return result


def _create_database(label):
    database = f"wye_test_eval_{label}_{uuid.uuid4().hex[:12]}"
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
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (database,),
            )
            cursor.execute(f'DROP DATABASE IF EXISTS "{database}"')
    finally:
        connection.close()


def _revision(database):
    connection = _connection(database)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM alembic_version")
            return cursor.fetchone()[0]
    finally:
        connection.close()


def _insert_artifact(cursor, seed, artifact_kind="protocol_definition"):
    canonical_bytes = (f'{{"seed":"{seed}"}}').encode("utf-8")
    digest = sha256(canonical_bytes).digest()
    cursor.execute(
        "INSERT INTO scientific_evaluation_artifacts "
        "(artifact_kind, schema_version, canonicalization_version, digest_algorithm, "
        "content_digest, content_length, content_type, json_payload, verified_at) "
        "VALUES (%s, '1.0.0', 'wye-c14n-json-v1', 'sha256', %s, %s, "
        "'application/vnd.wye.scientific+json', %s::jsonb, NOW()) RETURNING id",
        (artifact_kind, digest, len(canonical_bytes), canonical_bytes.decode("utf-8")),
    )
    artifact_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO scientific_evaluation_artifact_locations "
        "(location_key, artifact_id, storage_mode, canonical_bytes, location_status, verified_at) "
        "VALUES (%s, %s, 'inline', %s, 'verified', NOW()) RETURNING id",
        (str(uuid.uuid4()), artifact_id, canonical_bytes),
    )
    return artifact_id, cursor.fetchone()[0], digest, canonical_bytes


def _insert_protocol(cursor, key=None):
    protocol_key = key or f"protocol_{uuid.uuid4().hex}"
    cursor.execute(
        "INSERT INTO scientific_evaluation_protocols "
        "(protocol_key, domain_key, target_entity_type, governance_owner, created_by) "
        "VALUES (%s, 'food_toxicology', 'substance', 'scientific_board', 'test_actor') "
        "RETURNING id",
        (protocol_key,),
    )
    return cursor.fetchone()[0], protocol_key


def _insert_draft_version(cursor, protocol_id, semantic_version="1.0.0"):
    cursor.execute(
        "INSERT INTO scientific_evaluation_protocol_versions "
        "(protocol_id, semantic_version, lifecycle_status, created_by) "
        "VALUES (%s, %s, 'draft', 'test_actor') RETURNING id",
        (protocol_id, semantic_version),
    )
    return cursor.fetchone()[0]


def _governance_event(cursor, version_id, event_type, reason="test_transition"):
    cursor.execute(
        "INSERT INTO scientific_evaluation_governance_events "
        "(event_key, entity_type, protocol_version_id, event_type, actor_identifier, "
        "reason_code, effective_at) "
        "VALUES (%s, 'protocol_version', %s, %s, 'test_actor', %s, NOW()) RETURNING id",
        (str(uuid.uuid4()), version_id, event_type, reason),
    )
    return cursor.fetchone()[0]


def _publish_protocol_version(connection):
    fixture_key = uuid.uuid4().hex
    with connection.cursor() as cursor:
        canonical_id, _, digest, _ = _insert_artifact(
            cursor, f"canonical_{fixture_key}", "protocol_definition"
        )
        review_id, _, _, _ = _insert_artifact(
            cursor, f"review_{fixture_key}", "protocol_review"
        )
        protocol_id, _ = _insert_protocol(cursor)
        version_id = _insert_draft_version(cursor, protocol_id)
        cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions "
            "SET lifecycle_status='scientific_review' WHERE id=%s",
            (version_id,),
        )
        _governance_event(cursor, version_id, "submitted_for_review")
    connection.commit()
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions SET lifecycle_status='approved', "
            "canonical_artifact_id=%s, protocol_digest=%s, review_artifact_id=%s, "
            "effective_from=CURRENT_DATE WHERE id=%s",
            (canonical_id, digest, review_id, version_id),
        )
        _governance_event(cursor, version_id, "approved")
    connection.commit()
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions "
            "SET lifecycle_status='published', published_at=NOW() WHERE id=%s",
            (version_id,),
        )
        _governance_event(cursor, version_id, "published")
    connection.commit()
    return protocol_id, version_id, canonical_id, review_id


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvaluationFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = _create_database("schema")
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
        self.cursor.execute("SAVEPOINT foundation_test")

    def tearDown(self):
        try:
            self.connection.rollback()
        finally:
            self.cursor.close()
            self.connection.close()

    def _reset_after_error(self):
        self.connection.rollback()
        self.cursor.close()
        self.cursor = self.connection.cursor()
        self.cursor.execute("SAVEPOINT foundation_test")

    def test_repository_head_and_five_foundation_tables(self):
        self.assertEqual(_revision(self.database), REPOSITORY_HEAD)
        self.cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name = ANY(%s) ORDER BY table_name",
            (list(FOUNDATION_TABLES),),
        )
        self.assertEqual(
            [row[0] for row in self.cursor.fetchall()], sorted(FOUNDATION_TABLES)
        )

    def test_expected_columns_and_bigint_primary_keys(self):
        expected = {
            "scientific_evaluation_artifacts": {
                "id", "artifact_kind", "schema_version", "canonicalization_version",
                "digest_algorithm", "content_digest", "content_length", "content_type",
                "json_payload", "created_at", "verified_at",
            },
            "scientific_evaluation_artifact_locations": {
                "id", "location_key", "artifact_id", "storage_mode", "canonical_bytes",
                "storage_object_id", "location_status", "created_at", "verified_at",
            },
            "scientific_evaluation_protocols": {
                "id", "protocol_key", "domain_key", "target_entity_type",
                "governance_owner", "created_by", "created_at",
            },
            "scientific_evaluation_protocol_versions": {
                "id", "protocol_id", "semantic_version", "lifecycle_status",
                "canonical_artifact_id", "protocol_digest", "review_artifact_id",
                "effective_from", "created_by", "created_at", "published_at", "retired_at",
            },
            "scientific_evaluation_governance_events": {
                "id", "event_key", "entity_type", "protocol_id", "protocol_version_id",
                "artifact_id", "artifact_location_id", "event_type", "predecessor_event_id",
                "related_protocol_id", "related_protocol_version_id", "related_artifact_id",
                "related_artifact_location_id", "actor_identifier", "reason_code",
                "rationale_artifact_id", "metadata", "effective_at", "created_at",
            },
        }
        for table, columns in expected.items():
            self.cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                (table,),
            )
            self.assertTrue(columns.issubset({row[0] for row in self.cursor.fetchall()}))
        self.cursor.execute(
            "SELECT table_name, data_type FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name = ANY(%s) AND column_name='id'",
            (list(FOUNDATION_TABLES),),
        )
        self.assertTrue(all(data_type == "bigint" for _, data_type in self.cursor.fetchall()))

    def test_named_pk_fk_unique_check_and_indexes_exist(self):
        expected_constraints = {
            "pk_scientific_evaluation_artifacts",
            "uq_scientific_evaluation_artifacts_identity",
            "ck_scientific_evaluation_artifacts_digest_length",
            "fk_scientific_evaluation_artifact_locations_artifact",
            "uq_scientific_evaluation_protocols_key",
            "uq_scientific_evaluation_protocol_versions_semver",
            "ck_scientific_evaluation_protocol_versions_status",
            "fk_scientific_evaluation_governance_predecessor",
            "ck_scientific_evaluation_governance_entity_reference",
        }
        self.cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname = ANY(%s)",
            (list(expected_constraints),),
        )
        self.assertEqual({row[0] for row in self.cursor.fetchall()}, expected_constraints)
        expected_indexes = {
            "idx_scientific_evaluation_artifacts_kind_created",
            "idx_scientific_evaluation_artifact_locations_artifact_status",
            "idx_scientific_evaluation_protocol_versions_lifecycle",
            "idx_scientific_evaluation_governance_protocol_version",
            "uq_scientific_evaluation_artifact_object_location",
            "uq_scientific_evaluation_protocol_version_digest",
        }
        self.cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND indexname = ANY(%s)",
            (list(expected_indexes),),
        )
        self.assertEqual({row[0] for row in self.cursor.fetchall()}, expected_indexes)

    def test_all_foundation_foreign_keys_are_restrictive(self):
        self.cursor.execute(
            "SELECT conname, confdeltype FROM pg_constraint con "
            "JOIN pg_class rel ON rel.oid=con.conrelid "
            "WHERE rel.relname = ANY(%s) AND con.contype='f'",
            (list(FOUNDATION_TABLES),),
        )
        foreign_keys = self.cursor.fetchall()
        self.assertGreaterEqual(len(foreign_keys), 13)
        self.assertTrue(all(delete_action == "r" for _, delete_action in foreign_keys))

    def test_digest_length_content_and_status_checks_reject_invalid_rows(self):
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_artifacts "
                "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
                "content_digest,content_length,content_type,verified_at) VALUES "
                "('protocol_definition','1','wye-c14n-json-v1','sha256',%s,0,"
                "'application/vnd.wye.scientific+json',NOW())",
                (b"short",),
            )
        self._reset_after_error()
        protocol_id, _ = _insert_protocol(self.cursor)
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_protocol_versions "
                "(protocol_id,semantic_version,lifecycle_status,created_by) "
                "VALUES(%s,'1.0.0','invalid','test_actor')",
                (protocol_id,),
            )

    def test_inline_location_length_is_checked(self):
        canonical_bytes = b'{"seed":"c"}'
        digest = bytes.fromhex("c" * 64)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,verified_at) VALUES "
            "('protocol_definition','1','wye-c14n-json-v1','sha256',%s,%s,"
            "'application/vnd.wye.scientific+json',NOW()) RETURNING id",
            (digest, len(canonical_bytes)),
        )
        artifact_id = self.cursor.fetchone()[0]
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_artifact_locations "
                "(location_key,artifact_id,storage_mode,canonical_bytes,verified_at) "
                "VALUES(%s,%s,'inline',%s,NOW())",
                (str(uuid.uuid4()), artifact_id, b"wrong"),
            )

    def test_artifact_identity_is_immutable_and_duplicate_identity_is_rejected(self):
        artifact_id, _, digest, canonical_bytes = _insert_artifact(self.cursor, "d")
        with self.assertRaises(errors.ObjectNotInPrerequisiteState):
            self.cursor.execute(
                "UPDATE scientific_evaluation_artifacts SET json_payload='{}'::jsonb WHERE id=%s",
                (artifact_id,),
            )
        self._reset_after_error()
        artifact_id, _, digest, canonical_bytes = _insert_artifact(self.cursor, "d")
        with self.assertRaises(errors.UniqueViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_artifacts "
                "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
                "content_digest,content_length,content_type,verified_at) VALUES "
                "('another_kind','2','wye-c14n-json-v1','sha256',%s,%s,"
                "'application/vnd.wye.scientific+json',NOW())",
                (digest, len(canonical_bytes)),
            )
        self._reset_after_error()
        artifact_id, _, _, _ = _insert_artifact(self.cursor, "d")
        with self.assertRaises(errors.ObjectNotInPrerequisiteState):
            self.cursor.execute(
                "DELETE FROM scientific_evaluation_artifacts WHERE id=%s", (artifact_id,)
            )

    def test_protocol_key_and_semantic_version_uniqueness(self):
        protocol_id, protocol_key = _insert_protocol(self.cursor)
        with self.assertRaises(errors.UniqueViolation):
            _insert_protocol(self.cursor, protocol_key)
        self._reset_after_error()
        protocol_id, _ = _insert_protocol(self.cursor)
        _insert_draft_version(self.cursor, protocol_id, "1.0.0")
        with self.assertRaises(errors.UniqueViolation):
            _insert_draft_version(self.cursor, protocol_id, "1.0.0")
        self._reset_after_error()
        protocol_id, _ = _insert_protocol(self.cursor)
        first = _insert_draft_version(self.cursor, protocol_id, "1.0.0")
        second = _insert_draft_version(self.cursor, protocol_id, "1.1.0")
        self.assertNotEqual(first, second)

    def test_basic_semver_shape_is_database_enforced(self):
        protocol_id, _ = _insert_protocol(self.cursor)
        with self.assertRaises(errors.CheckViolation):
            _insert_draft_version(self.cursor, protocol_id, "01.0")

    def test_published_protocol_semantics_are_immutable_but_deprecation_is_governed(self):
        self.connection.commit()
        protocol_id, version_id, _, _ = _publish_protocol_version(self.connection)
        with self.connection.cursor() as cursor:
            with self.assertRaises(errors.ObjectNotInPrerequisiteState):
                cursor.execute(
                    "UPDATE scientific_evaluation_protocol_versions "
                    "SET semantic_version='1.0.1' WHERE id=%s",
                    (version_id,),
                )
        self.connection.rollback()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE scientific_evaluation_protocol_versions "
                "SET lifecycle_status='deprecated' WHERE id=%s",
                (version_id,),
            )
            _governance_event(cursor, version_id, "deprecated")
        self.connection.commit()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT lifecycle_status FROM scientific_evaluation_protocol_versions WHERE id=%s",
                (version_id,),
            )
            self.assertEqual(cursor.fetchone()[0], "deprecated")
        self.cursor.close()
        self.cursor = self.connection.cursor()

    def test_lifecycle_transition_requires_same_transaction_governance_event(self):
        protocol_id, _ = _insert_protocol(self.cursor)
        version_id = _insert_draft_version(self.cursor, protocol_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions "
            "SET lifecycle_status='scientific_review' WHERE id=%s",
            (version_id,),
        )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()

    def test_protocol_owner_change_requires_same_transaction_governance_event(self):
        self.connection.commit()
        protocol_id, _ = _insert_protocol(self.cursor)
        self.connection.commit()
        self.cursor.execute(
            "UPDATE scientific_evaluation_protocols SET governance_owner='new_board' "
            "WHERE id=%s",
            (protocol_id,),
        )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self.connection.rollback()

        self.cursor.execute(
            "UPDATE scientific_evaluation_protocols SET governance_owner='new_board' "
            "WHERE id=%s",
            (protocol_id,),
        )
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_governance_events "
            "(event_key,entity_type,protocol_id,event_type,actor_identifier,"
            "reason_code,effective_at) VALUES "
            "(%s,'protocol',%s,'annotation','test_actor','owner_transfer',NOW())",
            (str(uuid.uuid4()), protocol_id),
        )
        self.connection.commit()
        self.cursor.execute(
            "SELECT governance_owner FROM scientific_evaluation_protocols WHERE id=%s",
            (protocol_id,),
        )
        self.assertEqual(self.cursor.fetchone()[0], "new_board")

    def test_protocol_digest_and_verified_locations_are_deferred_guards(self):
        self.connection.commit()
        canonical_id, _, digest, _ = _insert_artifact(
            self.cursor, uuid.uuid4().hex, "protocol_definition"
        )
        review_id, _, _, _ = _insert_artifact(
            self.cursor, uuid.uuid4().hex, "protocol_review"
        )
        protocol_id, _ = _insert_protocol(self.cursor)
        version_id = _insert_draft_version(self.cursor, protocol_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions "
            "SET lifecycle_status='scientific_review' WHERE id=%s",
            (version_id,),
        )
        _governance_event(self.cursor, version_id, "submitted_for_review")
        self.connection.commit()

        self.cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions "
            "SET lifecycle_status='approved', canonical_artifact_id=%s, "
            "protocol_digest=%s, review_artifact_id=%s WHERE id=%s",
            (canonical_id, bytes.fromhex("a" * 64), review_id, version_id),
        )
        _governance_event(self.cursor, version_id, "approved")
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self.connection.rollback()

        canonical_bytes = b'{"seed":"unlocated-canonical"}'
        review_bytes = b'{"seed":"unlocated-review"}'
        unlocated = []
        for artifact_kind, payload in (
            ("protocol_definition", canonical_bytes),
            ("protocol_review", review_bytes),
        ):
            artifact_digest = sha256(payload).digest()
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_artifacts "
                "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
                "content_digest,content_length,content_type,json_payload,verified_at) "
                "VALUES(%s,'1.0.0','wye-c14n-json-v1','sha256',%s,%s,"
                "'application/vnd.wye.scientific+json',%s::jsonb,NOW()) RETURNING id",
                (artifact_kind, artifact_digest, len(payload), payload.decode("utf-8")),
            )
            unlocated.append((self.cursor.fetchone()[0], artifact_digest))
        protocol_id, _ = _insert_protocol(self.cursor)
        version_id = _insert_draft_version(self.cursor, protocol_id)
        self.cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions "
            "SET lifecycle_status='scientific_review' WHERE id=%s",
            (version_id,),
        )
        _governance_event(self.cursor, version_id, "submitted_for_review")
        self.connection.commit()
        self.cursor.execute(
            "UPDATE scientific_evaluation_protocol_versions "
            "SET lifecycle_status='approved', canonical_artifact_id=%s, "
            "protocol_digest=%s, review_artifact_id=%s WHERE id=%s",
            (unlocated[0][0], unlocated[0][1], unlocated[1][0], version_id),
        )
        _governance_event(self.cursor, version_id, "approved")
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()

    def test_artifact_location_status_transition_requires_governance_event(self):
        _, location_id, _, _ = _insert_artifact(self.cursor, uuid.uuid4().hex)
        self.cursor.execute(
            "UPDATE scientific_evaluation_artifact_locations "
            "SET location_status='quarantined' WHERE id=%s",
            (location_id,),
        )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self.connection.rollback()
        self.cursor.close()
        self.cursor = self.connection.cursor()
        _, location_id, _, _ = _insert_artifact(self.cursor, uuid.uuid4().hex)
        self.cursor.execute(
            "UPDATE scientific_evaluation_artifact_locations "
            "SET location_status='quarantined' WHERE id=%s",
            (location_id,),
        )
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_governance_events "
            "(event_key,entity_type,artifact_location_id,event_type,actor_identifier,"
            "reason_code,effective_at) VALUES "
            "(%s,'artifact_location',%s,'integrity_compromised','test_actor',"
            "'checksum_review',NOW())",
            (str(uuid.uuid4()), location_id),
        )
        self.connection.commit()

    def test_governance_events_are_append_only_and_fk_restricts_history(self):
        protocol_id, _ = _insert_protocol(self.cursor)
        version_id = _insert_draft_version(self.cursor, protocol_id)
        event_id = _governance_event(self.cursor, version_id, "annotation")
        with self.assertRaises(errors.ObjectNotInPrerequisiteState):
            self.cursor.execute(
                "UPDATE scientific_evaluation_governance_events "
                "SET reason_code='changed' WHERE id=%s",
                (event_id,),
            )
        self._reset_after_error()
        protocol_id, _ = _insert_protocol(self.cursor)
        version_id = _insert_draft_version(self.cursor, protocol_id)
        event_id = _governance_event(self.cursor, version_id, "annotation")
        with self.assertRaises(errors.ObjectNotInPrerequisiteState):
            self.cursor.execute(
                "DELETE FROM scientific_evaluation_governance_events WHERE id=%s",
                (event_id,),
            )
        self._reset_after_error()
        protocol_id, _ = _insert_protocol(self.cursor)
        _insert_draft_version(self.cursor, protocol_id)
        with self.assertRaises(errors.RestrictViolation):
            self.cursor.execute(
                "DELETE FROM scientific_evaluation_protocols WHERE id=%s", (protocol_id,)
            )

    def test_governance_predecessor_and_supersession_cycles_are_rejected(self):
        protocol_id, _ = _insert_protocol(self.cursor)
        version_id = _insert_draft_version(self.cursor, protocol_id)
        self.cursor.execute(
            "SELECT nextval(pg_get_serial_sequence("
            "'scientific_evaluation_governance_events','id')), "
            "nextval(pg_get_serial_sequence("
            "'scientific_evaluation_governance_events','id'))"
        )
        first_event_id, second_event_id = self.cursor.fetchone()
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_governance_events "
            "(id,event_key,entity_type,protocol_version_id,event_type,predecessor_event_id,"
            "actor_identifier,reason_code,effective_at) VALUES "
            "(%s,%s,'protocol_version',%s,'annotation',%s,'test_actor','cycle_a',NOW()),"
            "(%s,%s,'protocol_version',%s,'annotation',%s,'test_actor','cycle_b',NOW())",
            (
                first_event_id,
                str(uuid.uuid4()),
                version_id,
                second_event_id,
                second_event_id,
                str(uuid.uuid4()),
                version_id,
                first_event_id,
            ),
        )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self.connection.rollback()

        first_protocol_id, _ = _insert_protocol(self.cursor)
        second_protocol_id, _ = _insert_protocol(self.cursor)
        for owner_id, related_id in (
            (first_protocol_id, second_protocol_id),
            (second_protocol_id, first_protocol_id),
        ):
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_governance_events "
                "(event_key,entity_type,protocol_id,event_type,related_protocol_id,"
                "actor_identifier,reason_code,effective_at) VALUES "
                "(%s,'protocol',%s,'supersedes',%s,'test_actor','cycle',NOW())",
                (str(uuid.uuid4()), owner_id, related_id),
            )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()

    def test_partial_artifact_and_published_field_updates_are_rejected(self):
        artifact_id, _, _, _ = _insert_artifact(self.cursor, "e")
        with self.assertRaises(errors.ObjectNotInPrerequisiteState):
            self.cursor.execute(
                "UPDATE scientific_evaluation_artifacts "
                "SET created_at=created_at + INTERVAL '1 second' WHERE id=%s",
                (artifact_id,),
            )
        self._reset_after_error()
        self.connection.commit()
        _, version_id, _, _ = _publish_protocol_version(self.connection)
        with self.connection.cursor() as cursor:
            with self.assertRaises(errors.ObjectNotInPrerequisiteState):
                cursor.execute(
                    "UPDATE scientific_evaluation_protocol_versions "
                    "SET protocol_digest=%s WHERE id=%s",
                    (bytes.fromhex("f" * 64), version_id),
                )
        self.connection.rollback()
        self.cursor.close()
        self.cursor = self.connection.cursor()

    def _run_concurrent(self, statements):
        barrier = threading.Barrier(len(statements))
        outcomes = []
        lock = threading.Lock()

        def worker(statement, parameters):
            connection = _connection(self.database)
            try:
                with connection.cursor() as cursor:
                    barrier.wait(timeout=10)
                    cursor.execute(statement, parameters)
                connection.commit()
                outcome = "committed"
            except errors.UniqueViolation:
                connection.rollback()
                outcome = "unique_conflict"
            finally:
                connection.close()
            with lock:
                outcomes.append(outcome)

        threads = [
            threading.Thread(target=worker, args=item, daemon=True) for item in statements
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertCountEqual(outcomes, ["committed", "unique_conflict"])

    def test_concurrent_same_protocol_key_has_one_winner(self):
        key = f"concurrent_protocol_{uuid.uuid4().hex}"
        statement = (
            "INSERT INTO scientific_evaluation_protocols "
            "(protocol_key,domain_key,target_entity_type,governance_owner,created_by) "
            "VALUES(%s,'food_toxicology','substance','board','test_actor')"
        )
        self._run_concurrent(((statement, (key,)), (statement, (key,))))

    def test_concurrent_same_protocol_version_has_one_winner(self):
        protocol_id, _ = _insert_protocol(self.cursor)
        self.connection.commit()
        statement = (
            "INSERT INTO scientific_evaluation_protocol_versions "
            "(protocol_id,semantic_version,lifecycle_status,created_by) "
            "VALUES(%s,'9.0.0','draft','test_actor')"
        )
        self._run_concurrent(
            ((statement, (protocol_id,)), (statement, (protocol_id,)))
        )

    def test_concurrent_same_artifact_digest_has_one_winner(self):
        digest = bytes.fromhex("9" * 64)
        statement = (
            "INSERT INTO scientific_evaluation_artifacts "
            "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
            "content_digest,content_length,content_type,verified_at) "
            "VALUES('protocol_definition','1','wye-c14n-json-v1','sha256',%s,0,"
            "'application/vnd.wye.scientific+json',NOW())"
        )
        self._run_concurrent(((statement, (digest,)), (statement, (digest,))))


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvaluationFoundationLifecycleTests(unittest.TestCase):
    def test_upgrade_existing_0018_preserves_phase_six_and_legacy_rows(self):
        database = _create_database("upgrade")
        try:
            _alembic(database, "upgrade", PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO products(barcode,product_name,category) "
                        "VALUES('foundation-preservation','Preserved product','food')"
                    )
                    cursor.execute(
                        "SELECT count(*) FROM products WHERE barcode='foundation-preservation'"
                    )
                    product_count = cursor.fetchone()[0]
                    cursor.execute(
                        "SELECT count(*) FROM product_scores"
                    )
                    legacy_score_count = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO scientific_batch_plans "
                        "(plan_key,definition_checksum_value,plan_definition) "
                        "VALUES(%s,%s,'{}'::jsonb)",
                        ("1" * 64, "2" * 64),
                    )
                    cursor.execute(
                        "SELECT table_name,column_name,data_type,is_nullable "
                        "FROM information_schema.columns WHERE table_schema='public' "
                        "AND table_name IN "
                        "('product_scores','ingredient_risk_profiles','ingredient_evidence') "
                        "ORDER BY table_name,ordinal_position"
                    )
                    legacy_shape = cursor.fetchall()
                connection.commit()
            finally:
                connection.close()
            _alembic(database, "upgrade", REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT count(*) FROM products WHERE barcode='foundation-preservation'"
                    )
                    self.assertEqual(cursor.fetchone()[0], product_count)
                    cursor.execute("SELECT count(*) FROM product_scores")
                    self.assertEqual(cursor.fetchone()[0], legacy_score_count)
                    cursor.execute("SELECT count(*) FROM scientific_batch_plans")
                    self.assertEqual(cursor.fetchone()[0], 1)
                    cursor.execute(
                        "SELECT table_name,column_name,data_type,is_nullable "
                        "FROM information_schema.columns WHERE table_schema='public' "
                        "AND table_name IN "
                        "('product_scores','ingredient_risk_profiles','ingredient_evidence') "
                        "ORDER BY table_name,ordinal_position"
                    )
                    self.assertEqual(cursor.fetchall(), legacy_shape)
                    cursor.execute(
                        "SELECT DISTINCT parent.relname FROM pg_constraint con "
                        "JOIN pg_class child ON child.oid=con.conrelid "
                        "JOIN pg_class parent ON parent.oid=con.confrelid "
                        "WHERE con.contype='f' AND child.relname = ANY(%s) "
                        "AND parent.relname IN "
                        "('product_scores','ingredient_risk_profiles','ingredient_evidence')",
                        (list(FOUNDATION_TABLES),),
                    )
                    self.assertEqual(cursor.fetchall(), [])
                    for table in FOUNDATION_TABLES:
                        cursor.execute(f"SELECT count(*) FROM {table}")
                        self.assertEqual(cursor.fetchone()[0], 0)
            finally:
                connection.close()
        finally:
            _drop_database(database)

    def test_fresh_database_upgrade_and_empty_downgrade(self):
        database = _create_database("empty_downgrade")
        try:
            _alembic(database, "upgrade", "head")
            self.assertEqual(_revision(database), REPOSITORY_HEAD)
            _alembic(database, "downgrade", PARENT_REVISION)
            self.assertEqual(_revision(database), PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    for table in FOUNDATION_TABLES:
                        cursor.execute("SELECT to_regclass(%s)", (table,))
                        self.assertIsNone(cursor.fetchone()[0])
            finally:
                connection.close()
        finally:
            _drop_database(database)

    def test_downgrade_with_canonical_rows_fails_without_deleting_history(self):
        database = _create_database("protected_downgrade")
        try:
            _alembic(database, "upgrade", REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    _insert_protocol(cursor)
                connection.commit()
            finally:
                connection.close()
            failure = _alembic(
                database, "downgrade", PARENT_REVISION, success=False
            )
            self.assertIn("not representable", failure.stdout + failure.stderr)
            self.assertEqual(_revision(database), REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM scientific_evaluation_protocols")
                    self.assertEqual(cursor.fetchone()[0], 1)
            finally:
                connection.close()
        finally:
            _drop_database(database)

    def test_upgrade_preflight_rejects_incompatible_collision(self):
        database = _create_database("collision")
        try:
            _alembic(database, "upgrade", PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute("CREATE TABLE scientific_evaluation_protocols(id INTEGER)")
                connection.commit()
            finally:
                connection.close()
            failure = _alembic(database, "upgrade", REVISION, success=False)
            self.assertIn("foundation object collision", failure.stdout + failure.stderr)
            self.assertEqual(_revision(database), PARENT_REVISION)
        finally:
            _drop_database(database)


if __name__ == "__main__":
    unittest.main()
