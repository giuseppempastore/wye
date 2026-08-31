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
REVISION = "0020_scientific_evidence_snapshots"
PARENT_REVISION = "0019_scientific_evaluation_foundation"
REPOSITORY_HEAD = "0021_scientific_evaluation_publication"
SNAPSHOT_TABLES = (
    "scientific_evidence_snapshots",
    "scientific_evidence_snapshot_members",
)
LEGACY_TABLES = (
    "product_scores",
    "ingredient_risk_profiles",
    "ingredient_evidence",
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
    database = f"wye_test_snapshot_{label}_{uuid.uuid4().hex[:12]}"
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


def _revision(database):
    connection = _connection(database)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM alembic_version")
            return cursor.fetchone()[0]
    finally:
        connection.close()


def _insert_artifact(cursor, artifact_kind, seed, located=True, schema_version="1"):
    canonical_bytes = (
        f'{{"artifact_type":"{artifact_kind}","seed":"{seed}"}}'
    ).encode("utf-8")
    digest = sha256(canonical_bytes).digest()
    cursor.execute(
        "INSERT INTO scientific_evaluation_artifacts "
        "(artifact_kind,schema_version,canonicalization_version,digest_algorithm,"
        "content_digest,content_length,content_type,json_payload,verified_at) "
        "VALUES(%s,%s,'wye-c14n-json-v1','sha256',%s,%s,"
        "'application/vnd.wye.scientific+json',%s::jsonb,NOW()) RETURNING id",
        (
            artifact_kind,
            schema_version,
            digest,
            len(canonical_bytes),
            canonical_bytes.decode("utf-8"),
        ),
    )
    artifact_id = cursor.fetchone()[0]
    if located:
        cursor.execute(
            "INSERT INTO scientific_evaluation_artifact_locations "
            "(location_key,artifact_id,storage_mode,canonical_bytes,location_status,verified_at) "
            "VALUES(%s,%s,'inline',%s,'verified',NOW())",
            (str(uuid.uuid4()), artifact_id, canonical_bytes),
        )
    return artifact_id, digest


def _insert_snapshot(cursor, query_artifact_id=None):
    if query_artifact_id is None:
        query_artifact_id, _ = _insert_artifact(
            cursor, "scientific_evidence_snapshot_query", uuid.uuid4().hex
        )
    snapshot_key = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO scientific_evidence_snapshots "
        "(snapshot_key,snapshot_policy_key,snapshot_policy_version,as_of,evidence_cutoff,"
        "query_definition_artifact_id,canonicalization_version,digest_algorithm,created_by) "
        "VALUES(%s,'phase_7_candidate_universe','1',NOW(),NOW()-INTERVAL '1 day',%s,"
        "'wye-c14n-json-v1','sha256','snapshot_test') RETURNING id",
        (snapshot_key, query_artifact_id),
    )
    return cursor.fetchone()[0], snapshot_key


def _insert_evidence(cursor, suffix=None):
    suffix = suffix or uuid.uuid4().hex
    cursor.execute(
        "INSERT INTO sources(source_name,source_type,source_key) "
        "VALUES(%s,'scientific',%s) RETURNING id",
        (f"Snapshot source {suffix}", f"snapshot_source_{suffix}"),
    )
    source_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO source_datasets(source_id,dataset_name,dataset_key) "
        "VALUES(%s,%s,%s) RETURNING id",
        (source_id, f"Snapshot dataset {suffix}", f"snapshot_dataset_{suffix}"),
    )
    dataset_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO source_dataset_releases "
        "(dataset_id,version_label,release_status,external_release_key,released_at,acquired_at) "
        "VALUES(%s,'v1','validated',%s,NOW()-INTERVAL '2 days',NOW()-INTERVAL '1 day') "
        "RETURNING id",
        (dataset_id, f"snapshot_release_{suffix}"),
    )
    release_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO substances(preferred_name,normalized_name,substance_type,status) "
        "VALUES(%s,%s,'chemical_substance','active') RETURNING id",
        (f"Snapshot substance {suffix}", f"snapshot_substance_{suffix}"),
    )
    substance_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO scientific_ingestion_runs "
        "(release_id,run_key,importer_name,importer_version,source_adapter_version,"
        "acquisition_version,parser_version,normalization_schema_version,"
        "artifact_manifest_algorithm,artifact_manifest_fingerprint,run_status,"
        "started_at,completed_at) VALUES "
        "(%s,%s,'snapshot_importer','1','1','1','1','1','sha256',%s,'succeeded',"
        "NOW()-INTERVAL '1 hour',NOW()) RETURNING id",
        (release_id, str(uuid.uuid4()), sha256(suffix.encode()).hexdigest()),
    )
    ingestion_run_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO scientific_assessments "
        "(substance_id,source_dataset_release_id,assessment_type,assessment_version,"
        "assessment_status,ingestion_run_id,source_record_key,raw_record) "
        "VALUES(%s,%s,'toxicology','1','published',%s,%s,'{}'::jsonb) RETURNING id",
        (substance_id, release_id, ingestion_run_id, f"assessment_{suffix}"),
    )
    assessment_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO scientific_assessment_findings "
        "(assessment_id,endpoint,value_text,source_record_key,source_finding_key,"
        "source_ordinal,raw_payload) VALUES "
        "(%s,'snapshot_endpoint','observed',%s,%s,0,'{}'::jsonb) RETURNING id",
        (assessment_id, f"finding_record_{suffix}", f"finding_{suffix}"),
    )
    finding_id = cursor.fetchone()[0]
    return {
        "source_id": source_id,
        "dataset_id": dataset_id,
        "release_id": release_id,
        "substance_id": substance_id,
        "ingestion_run_id": ingestion_run_id,
        "assessment_id": assessment_id,
        "finding_id": finding_id,
    }


def _insert_finding(cursor, assessment_id, suffix=None):
    suffix = suffix or uuid.uuid4().hex
    cursor.execute(
        "INSERT INTO scientific_assessment_findings "
        "(assessment_id,endpoint,value_text,source_record_key,source_finding_key,"
        "source_ordinal,raw_payload) VALUES "
        "(%s,'snapshot_endpoint','observed',%s,%s,1,'{}'::jsonb) RETURNING id",
        (assessment_id, f"finding_record_{suffix}", f"finding_{suffix}"),
    )
    return cursor.fetchone()[0]


def _insert_member(
    cursor,
    snapshot_id,
    evidence,
    ordinal=0,
    member_kind="finding",
    identity_seed=None,
    semantic_seed=None,
    finding_id=None,
):
    identity_seed = identity_seed or uuid.uuid4().hex
    semantic_seed = semantic_seed or uuid.uuid4().hex
    artifact_id, semantic_digest = _insert_artifact(
        cursor, "scientific_evidence_snapshot_member", semantic_seed
    )
    identity_digest = sha256(identity_seed.encode("utf-8")).digest()
    if finding_id is None and member_kind == "finding":
        finding_id = evidence["finding_id"]
    cursor.execute(
        "INSERT INTO scientific_evidence_snapshot_members "
        "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
        "source_dataset_release_id,member_identity_digest,member_payload_artifact_id,"
        "member_semantic_digest,membership_ordinal,status_as_of) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published') RETURNING id",
        (
            snapshot_id,
            member_kind,
            finding_id if member_kind == "finding" else None,
            evidence["assessment_id"],
            evidence["ingestion_run_id"],
            evidence["release_id"],
            identity_digest,
            artifact_id,
            semantic_digest,
            ordinal,
        ),
    )
    return cursor.fetchone()[0], identity_digest, semantic_digest, artifact_id


def _seal_snapshot(cursor, snapshot_id, member_count, manifest_seed=None):
    manifest_id, manifest_digest = _insert_artifact(
        cursor,
        "scientific_evidence_snapshot_manifest",
        manifest_seed or uuid.uuid4().hex,
    )
    cursor.execute(
        "UPDATE scientific_evidence_snapshots SET "
        "manifest_artifact_id=%s,snapshot_digest=%s,member_count=%s,status='sealed',"
        "sealed_by='snapshot_test',sealed_at=NOW() WHERE id=%s",
        (manifest_id, manifest_digest, member_count, snapshot_id),
    )
    return manifest_id, manifest_digest


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvidenceSnapshotTests(unittest.TestCase):
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

    def tearDown(self):
        try:
            self.connection.rollback()
        finally:
            self.cursor.close()
            self.connection.close()

    def _reset(self):
        self.connection.rollback()
        self.cursor.close()
        self.cursor = self.connection.cursor()

    def test_repository_head_schema_shape_and_bigint_keys(self):
        self.assertEqual(_revision(self.database), REPOSITORY_HEAD)
        expected_columns = {
            "scientific_evidence_snapshots": {
                "id", "snapshot_key", "snapshot_policy_key",
                "snapshot_policy_version", "as_of", "evidence_cutoff",
                "query_definition_artifact_id", "canonicalization_version",
                "digest_algorithm", "manifest_artifact_id", "snapshot_digest",
                "member_count", "status", "created_by", "sealed_by",
                "created_at", "sealed_at",
            },
            "scientific_evidence_snapshot_members": {
                "id", "snapshot_id", "member_kind", "finding_id",
                "assessment_id", "ingestion_run_id", "source_dataset_release_id",
                "member_identity_digest", "member_payload_artifact_id",
                "member_semantic_digest", "membership_ordinal", "status_as_of",
                "created_at",
            },
        }
        for table, columns in expected_columns.items():
            self.cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                (table,),
            )
            self.assertEqual({row[0] for row in self.cursor.fetchall()}, columns)
            self.cursor.execute(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s AND column_name='id'",
                (table,),
            )
            self.assertEqual(self.cursor.fetchone()[0], "bigint")

    def test_constraints_indexes_and_restrictive_foreign_keys(self):
        expected_constraints = {
            "uq_scientific_evidence_snapshots_key",
            "ck_scientific_evidence_snapshots_state",
            "fk_scientific_evidence_snapshots_query_artifact",
            "uq_scientific_evidence_snapshot_members_ordinal",
            "uq_scientific_evidence_snapshot_members_identity",
            "fk_scientific_evidence_snapshot_members_finding",
            "fk_scientific_evaluation_governance_snapshot",
            "ck_scientific_evaluation_governance_entity_reference",
        }
        self.cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname = ANY(%s)",
            (list(expected_constraints),),
        )
        self.assertEqual({row[0] for row in self.cursor.fetchall()}, expected_constraints)
        expected_indexes = {
            "uq_scientific_evidence_snapshots_identity",
            "idx_scientific_evidence_snapshots_status_cutoff",
            "uq_scientific_evidence_snapshot_members_finding",
            "uq_scientific_evidence_snapshot_members_assessment",
            "idx_scientific_evidence_snapshot_members_order",
            "idx_scientific_evaluation_governance_snapshot",
        }
        self.cursor.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE schemaname='public' AND indexname = ANY(%s)",
            (list(expected_indexes),),
        )
        self.assertEqual({row[0] for row in self.cursor.fetchall()}, expected_indexes)
        self.cursor.execute(
            "SELECT con.confdeltype FROM pg_constraint con "
            "JOIN pg_class rel ON rel.oid=con.conrelid "
            "WHERE con.contype='f' AND rel.relname = ANY(%s)",
            (list(SNAPSHOT_TABLES) + ["scientific_evaluation_governance_events"],),
        )
        actions = [row[0] for row in self.cursor.fetchall()]
        self.assertGreaterEqual(len(actions), 19)
        self.assertTrue(all(action == "r" for action in actions))

    def test_snapshot_checks_and_external_uuid_uniqueness(self):
        query_id, _ = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_query", uuid.uuid4().hex
        )
        _, snapshot_key = _insert_snapshot(self.cursor, query_id)
        with self.assertRaises(errors.UniqueViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evidence_snapshots "
                "(snapshot_key,snapshot_policy_key,snapshot_policy_version,as_of,"
                "evidence_cutoff,query_definition_artifact_id,canonicalization_version,"
                "digest_algorithm,created_by) VALUES "
                "(%s,'phase_7_candidate_universe','1',NOW(),NOW()-INTERVAL '1 day',%s,"
                "'wye-c14n-json-v1','sha256','test')",
                (snapshot_key, query_id),
            )
        self._reset()
        query_id, _ = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_query", uuid.uuid4().hex
        )
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evidence_snapshots "
                "(snapshot_key,snapshot_policy_key,snapshot_policy_version,as_of,"
                "evidence_cutoff,query_definition_artifact_id,canonicalization_version,"
                "digest_algorithm,created_by) VALUES "
                "(%s,'phase_7_candidate_universe','1',NOW(),NOW()+INTERVAL '1 day',%s,"
                "'wye-c14n-json-v1','sha256','test')",
                (str(uuid.uuid4()), query_id),
            )
        self._reset()
        query_id, _ = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_query", uuid.uuid4().hex
        )
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evidence_snapshots "
                "(snapshot_key,snapshot_policy_key,snapshot_policy_version,as_of,"
                "evidence_cutoff,query_definition_artifact_id,canonicalization_version,"
                "digest_algorithm,created_by) VALUES "
                "(%s,'phase_7_candidate_universe','1',NOW(),NOW(),%s,'other','sha1','test')",
                (str(uuid.uuid4()), query_id),
            )

    def test_artifact_kind_digest_and_verified_location_guards(self):
        wrong_query_id, _ = _insert_artifact(
            self.cursor, "protocol_definition", uuid.uuid4().hex
        )
        _insert_snapshot(self.cursor, wrong_query_id)
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self._reset()

        wrong_schema_query_id, _ = _insert_artifact(
            self.cursor,
            "scientific_evidence_snapshot_query",
            uuid.uuid4().hex,
            schema_version="2",
        )
        _insert_snapshot(self.cursor, wrong_schema_query_id)
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self._reset()

        snapshot_id, _ = _insert_snapshot(self.cursor)
        manifest_id, _ = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_manifest", uuid.uuid4().hex
        )
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "UPDATE scientific_evidence_snapshots SET manifest_artifact_id=%s,"
                "snapshot_digest=%s,member_count=0,status='sealed',sealed_by='test',"
                "sealed_at=NOW() WHERE id=%s",
                (manifest_id, b"short", snapshot_id),
            )
        self._reset()

        snapshot_id, _ = _insert_snapshot(self.cursor)
        manifest_id, manifest_digest = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_manifest", uuid.uuid4().hex,
            located=False,
        )
        self.cursor.execute(
            "UPDATE scientific_evidence_snapshots SET manifest_artifact_id=%s,"
            "snapshot_digest=%s,member_count=0,status='sealed',sealed_by='test',"
            "sealed_at=NOW() WHERE id=%s",
            (manifest_id, manifest_digest, snapshot_id),
        )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self._reset()

        snapshot_id, _ = _insert_snapshot(self.cursor)
        manifest_id, manifest_digest = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_manifest", uuid.uuid4().hex
        )
        self.cursor.execute(
            "UPDATE scientific_evidence_snapshots SET manifest_artifact_id=%s,"
            "snapshot_digest=%s,member_count=0,status='sealed',sealed_by='test',"
            "sealed_at=NOW() WHERE id=%s",
            (manifest_id, bytes.fromhex("f" * 64), snapshot_id),
        )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()

    def test_member_artifact_kind_schema_and_digest_binding(self):
        for artifact_kind, schema_version, digest_override in (
            ("protocol_definition", "1", None),
            ("scientific_evidence_snapshot_member", "2", None),
            ("scientific_evidence_snapshot_member", "1", sha256(b"other").digest()),
        ):
            snapshot_id, _ = _insert_snapshot(self.cursor)
            evidence = _insert_evidence(self.cursor)
            artifact_id, artifact_digest = _insert_artifact(
                self.cursor,
                artifact_kind,
                uuid.uuid4().hex,
                schema_version=schema_version,
            )
            self.cursor.execute(
                "INSERT INTO scientific_evidence_snapshot_members "
                "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                "source_dataset_release_id,member_identity_digest,member_payload_artifact_id,"
                "member_semantic_digest,membership_ordinal,status_as_of) "
                "VALUES(%s,'finding',%s,%s,%s,%s,%s,%s,%s,0,'published')",
                (
                    snapshot_id,
                    evidence["finding_id"],
                    evidence["assessment_id"],
                    evidence["ingestion_run_id"],
                    evidence["release_id"],
                    sha256(uuid.uuid4().bytes).digest(),
                    artifact_id,
                    digest_override or artifact_digest,
                ),
            )
            with self.assertRaises(errors.CheckViolation):
                self.connection.commit()
            self._reset()

    def test_member_shape_digest_duplicates_and_fk_restrict(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        evidence = _insert_evidence(self.cursor)
        member_id, identity_digest, semantic_digest, artifact_id = _insert_member(
            self.cursor, snapshot_id, evidence
        )
        self.connection.commit()
        with self.connection.cursor() as cursor:
            with self.assertRaises(errors.UniqueViolation):
                cursor.execute(
                    "INSERT INTO scientific_evidence_snapshot_members "
                    "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                    "source_dataset_release_id,member_identity_digest,"
                    "member_payload_artifact_id,member_semantic_digest,membership_ordinal,"
                    "status_as_of) SELECT snapshot_id,member_kind,finding_id,assessment_id,"
                    "ingestion_run_id,source_dataset_release_id,member_identity_digest,"
                    "member_payload_artifact_id,member_semantic_digest,1,status_as_of "
                    "FROM scientific_evidence_snapshot_members WHERE id=%s",
                    (member_id,),
                )
        self.connection.rollback()
        with self.connection.cursor() as cursor:
            with self.assertRaises(errors.RestrictViolation):
                cursor.execute(
                    "DELETE FROM scientific_assessments WHERE id=%s",
                    (evidence["assessment_id"],),
                )
        self.connection.rollback()
        with self.connection.cursor() as cursor:
            with self.assertRaises(errors.CheckViolation):
                cursor.execute(
                    "INSERT INTO scientific_evidence_snapshot_members "
                    "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                    "source_dataset_release_id,member_identity_digest,"
                    "member_payload_artifact_id,member_semantic_digest,membership_ordinal,"
                    "status_as_of) VALUES(%s,'assessment',%s,%s,%s,%s,%s,%s,%s,2,'published')",
                    (
                        snapshot_id, evidence["finding_id"], evidence["assessment_id"],
                        evidence["ingestion_run_id"], evidence["release_id"],
                        sha256(b"bad-shape").digest(), artifact_id, semantic_digest,
                    ),
                )

    def test_digest_lengths_and_equal_semantic_payloads_remain_distinct(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        evidence = _insert_evidence(self.cursor)
        artifact_id, semantic_digest = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_member", uuid.uuid4().hex
        )
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evidence_snapshot_members "
                "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                "source_dataset_release_id,member_identity_digest,member_payload_artifact_id,"
                "member_semantic_digest,membership_ordinal,status_as_of) "
                "VALUES(%s,'finding',%s,%s,%s,%s,%s,%s,%s,0,'published')",
                (
                    snapshot_id, evidence["finding_id"], evidence["assessment_id"],
                    evidence["ingestion_run_id"], evidence["release_id"], b"short",
                    artifact_id, semantic_digest,
                ),
            )
        self._reset()

        snapshot_id, _ = _insert_snapshot(self.cursor)
        evidence = _insert_evidence(self.cursor)
        second_finding = _insert_finding(self.cursor, evidence["assessment_id"])
        artifact_id, semantic_digest = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_member", uuid.uuid4().hex
        )
        for ordinal, finding_id in enumerate((evidence["finding_id"], second_finding)):
            self.cursor.execute(
                "INSERT INTO scientific_evidence_snapshot_members "
                "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                "source_dataset_release_id,member_identity_digest,member_payload_artifact_id,"
                "member_semantic_digest,membership_ordinal,status_as_of) "
                "VALUES(%s,'finding',%s,%s,%s,%s,%s,%s,%s,%s,'published')",
                (
                    snapshot_id, finding_id, evidence["assessment_id"],
                    evidence["ingestion_run_id"], evidence["release_id"],
                    sha256(f"identity-{ordinal}".encode()).digest(), artifact_id,
                    semantic_digest, ordinal,
                ),
            )
        self.connection.commit()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*),count(DISTINCT member_semantic_digest) "
                "FROM scientific_evidence_snapshot_members WHERE snapshot_id=%s",
                (snapshot_id,),
            )
            self.assertEqual(cursor.fetchone(), (2, 1))

    def test_member_provenance_and_assessment_finding_coexistence(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        evidence = _insert_evidence(self.cursor)
        _insert_member(self.cursor, snapshot_id, evidence)
        self.connection.commit()
        with self.connection.cursor() as cursor:
            _insert_member(
                cursor, snapshot_id, evidence, ordinal=1, member_kind="assessment"
            )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()
        self.connection.rollback()

        with self.connection.cursor() as cursor:
            snapshot_id, _ = _insert_snapshot(cursor)
            first = _insert_evidence(cursor)
            second = _insert_evidence(cursor)
            artifact_id, semantic_digest = _insert_artifact(
                cursor, "scientific_evidence_snapshot_member", uuid.uuid4().hex
            )
            cursor.execute(
                "INSERT INTO scientific_evidence_snapshot_members "
                "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                "source_dataset_release_id,member_identity_digest,member_payload_artifact_id,"
                "member_semantic_digest,membership_ordinal,status_as_of) "
                "VALUES(%s,'finding',%s,%s,%s,%s,%s,%s,%s,0,'published')",
                (
                    snapshot_id, first["finding_id"], second["assessment_id"],
                    second["ingestion_run_id"], second["release_id"],
                    sha256(b"wrong-provenance").digest(), artifact_id, semantic_digest,
                ),
            )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()

    def test_zero_member_snapshot_and_manifest_consistency(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        _seal_snapshot(self.cursor, snapshot_id, 0)
        self.connection.commit()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT status,member_count,octet_length(snapshot_digest) "
                "FROM scientific_evidence_snapshots WHERE id=%s",
                (snapshot_id,),
            )
            self.assertEqual(cursor.fetchone(), ("sealed", 0, 32))

    def test_sealed_snapshot_and_members_are_immutable(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        evidence = _insert_evidence(self.cursor)
        member_id, _, _, _ = _insert_member(self.cursor, snapshot_id, evidence)
        _seal_snapshot(self.cursor, snapshot_id, 1)
        self.connection.commit()
        statements = (
            ("UPDATE scientific_evidence_snapshots SET sealed_by='other' WHERE id=%s", snapshot_id),
            ("DELETE FROM scientific_evidence_snapshots WHERE id=%s", snapshot_id),
            ("UPDATE scientific_evidence_snapshot_members SET status_as_of='changed' WHERE id=%s", member_id),
            ("DELETE FROM scientific_evidence_snapshot_members WHERE id=%s", member_id),
        )
        for statement, row_id in statements:
            with self.connection.cursor() as cursor:
                with self.assertRaises(errors.ObjectNotInPrerequisiteState):
                    cursor.execute(statement, (row_id,))
            self.connection.rollback()
        with self.connection.cursor() as cursor:
            other = _insert_evidence(cursor)
            with self.assertRaises(errors.ObjectNotInPrerequisiteState):
                _insert_member(cursor, snapshot_id, other, ordinal=1)

    def test_canonical_order_is_independent_of_insertion_order(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        first = _insert_evidence(self.cursor)
        second = _insert_evidence(self.cursor)
        candidates = []
        for evidence, seed in ((first, "z_identity"), (second, "a_identity")):
            artifact_id, semantic_digest = _insert_artifact(
                self.cursor, "scientific_evidence_snapshot_member", seed
            )
            candidates.append(
                {
                    "evidence": evidence,
                    "identity": sha256(seed.encode()).digest(),
                    "semantic": semantic_digest,
                    "artifact": artifact_id,
                }
            )
        ordered = sorted(candidates, key=lambda item: ("finding", item["identity"], item["semantic"]))
        ordinals = {item["identity"]: position for position, item in enumerate(ordered)}
        for item in reversed(candidates):
            evidence = item["evidence"]
            self.cursor.execute(
                "INSERT INTO scientific_evidence_snapshot_members "
                "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                "source_dataset_release_id,member_identity_digest,member_payload_artifact_id,"
                "member_semantic_digest,membership_ordinal,status_as_of) "
                "VALUES(%s,'finding',%s,%s,%s,%s,%s,%s,%s,%s,'published')",
                (
                    snapshot_id, evidence["finding_id"], evidence["assessment_id"],
                    evidence["ingestion_run_id"], evidence["release_id"], item["identity"],
                    item["artifact"], item["semantic"], ordinals[item["identity"]],
                ),
            )
        _seal_snapshot(self.cursor, snapshot_id, 2)
        self.connection.commit()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT membership_ordinal FROM scientific_evidence_snapshot_members "
                "WHERE snapshot_id=%s ORDER BY id",
                (snapshot_id,),
            )
            insertion_ordinals = [row[0] for row in cursor.fetchall()]
            self.assertNotEqual(insertion_ordinals, sorted(insertion_ordinals))

    def test_noncanonical_ordinal_is_rejected_at_seal(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        evidence = _insert_evidence(self.cursor)
        _insert_member(self.cursor, snapshot_id, evidence, ordinal=1)
        _seal_snapshot(self.cursor, snapshot_id, 1)
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()

    def test_governance_snapshot_extension_append_only_and_typed(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_governance_events "
            "(event_key,entity_type,snapshot_id,event_type,actor_identifier,reason_code,"
            "effective_at) VALUES(%s,'evidence_snapshot',%s,'annotation','test_actor',"
            "'snapshot_note',NOW()) RETURNING id",
            (str(uuid.uuid4()), snapshot_id),
        )
        event_id = self.cursor.fetchone()[0]
        with self.assertRaises(errors.ObjectNotInPrerequisiteState):
            self.cursor.execute(
                "UPDATE scientific_evaluation_governance_events "
                "SET reason_code='changed' WHERE id=%s",
                (event_id,),
            )
        self._reset()
        snapshot_id, _ = _insert_snapshot(self.cursor)
        self.cursor.execute(
            "INSERT INTO scientific_evaluation_governance_events "
            "(event_key,entity_type,snapshot_id,event_type,actor_identifier,reason_code,"
            "effective_at) VALUES(%s,'evidence_snapshot',%s,'annotation','test_actor',"
            "'snapshot_delete_guard',NOW()) RETURNING id",
            (str(uuid.uuid4()), snapshot_id),
        )
        event_id = self.cursor.fetchone()[0]
        with self.assertRaises(errors.ObjectNotInPrerequisiteState):
            self.cursor.execute(
                "DELETE FROM scientific_evaluation_governance_events WHERE id=%s",
                (event_id,),
            )
        self._reset()
        snapshot_id, _ = _insert_snapshot(self.cursor)
        with self.assertRaises(errors.CheckViolation):
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_governance_events "
                "(event_key,entity_type,snapshot_id,related_protocol_id,event_type,"
                "actor_identifier,reason_code,effective_at) VALUES "
                "(%s,'evidence_snapshot',%s,1,'supersedes','test_actor','bad_type',NOW())",
                (str(uuid.uuid4()), snapshot_id),
            )

    def test_snapshot_supersession_cycle_is_rejected(self):
        first_id, _ = _insert_snapshot(self.cursor)
        second_id, _ = _insert_snapshot(self.cursor)
        for owner, related in ((first_id, second_id), (second_id, first_id)):
            self.cursor.execute(
                "INSERT INTO scientific_evaluation_governance_events "
                "(event_key,entity_type,snapshot_id,event_type,related_snapshot_id,"
                "actor_identifier,reason_code,effective_at) VALUES "
                "(%s,'evidence_snapshot',%s,'supersedes',%s,'test_actor','cycle',NOW())",
                (str(uuid.uuid4()), owner, related),
            )
        with self.assertRaises(errors.CheckViolation):
            self.connection.commit()

    def test_historical_member_survives_current_assessment_status_change(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        evidence = _insert_evidence(self.cursor)
        _insert_member(self.cursor, snapshot_id, evidence)
        _seal_snapshot(self.cursor, snapshot_id, 1)
        self.connection.commit()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE scientific_assessments SET assessment_status='superseded' WHERE id=%s",
                (evidence["assessment_id"],),
            )
        self.connection.commit()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM scientific_evidence_snapshot_members "
                "WHERE snapshot_id=%s AND assessment_id=%s",
                (snapshot_id, evidence["assessment_id"]),
            )
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_concurrent_identical_snapshot_sealing_has_one_winner(self):
        first_id, _ = _insert_snapshot(self.cursor)
        second_id, _ = _insert_snapshot(self.cursor)
        manifest_id, digest = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_manifest", uuid.uuid4().hex
        )
        self.connection.commit()
        barrier = threading.Barrier(2)
        outcomes = []
        lock = threading.Lock()

        def worker(snapshot_id):
            connection = _connection(self.database)
            try:
                with connection.cursor() as cursor:
                    barrier.wait(timeout=10)
                    cursor.execute(
                        "UPDATE scientific_evidence_snapshots SET manifest_artifact_id=%s,"
                        "snapshot_digest=%s,member_count=0,status='sealed',sealed_by='race',"
                        "sealed_at=NOW() WHERE id=%s",
                        (manifest_id, digest, snapshot_id),
                    )
                connection.commit()
                outcome = "committed"
            except errors.UniqueViolation:
                connection.rollback()
                outcome = "unique_conflict"
            finally:
                connection.close()
            with lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=worker, args=(row_id,)) for row_id in (first_id, second_id)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertCountEqual(outcomes, ["committed", "unique_conflict"])
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM scientific_evidence_snapshots "
                "WHERE status='sealed' AND snapshot_digest=%s",
                (digest,),
            )
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_concurrent_seal_blocks_member_mutation(self):
        snapshot_id, _ = _insert_snapshot(self.cursor)
        manifest_id, digest = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_manifest", uuid.uuid4().hex
        )
        evidence = _insert_evidence(self.cursor)
        artifact_id, semantic_digest = _insert_artifact(
            self.cursor, "scientific_evidence_snapshot_member", uuid.uuid4().hex
        )
        identity_digest = sha256(uuid.uuid4().bytes).digest()
        self.connection.commit()

        sealer = _connection(self.database)
        mutation_outcome = []
        started = threading.Event()
        try:
            with sealer.cursor() as cursor:
                cursor.execute(
                    "UPDATE scientific_evidence_snapshots SET manifest_artifact_id=%s,"
                    "snapshot_digest=%s,member_count=0,status='sealed',sealed_by='race',"
                    "sealed_at=NOW() WHERE id=%s",
                    (manifest_id, digest, snapshot_id),
                )

            def mutate():
                connection = _connection(self.database)
                try:
                    with connection.cursor() as cursor:
                        started.set()
                        cursor.execute(
                            "INSERT INTO scientific_evidence_snapshot_members "
                            "(snapshot_id,member_kind,finding_id,assessment_id,ingestion_run_id,"
                            "source_dataset_release_id,member_identity_digest,"
                            "member_payload_artifact_id,member_semantic_digest,"
                            "membership_ordinal,status_as_of) VALUES "
                            "(%s,'finding',%s,%s,%s,%s,%s,%s,%s,0,'published')",
                            (
                                snapshot_id, evidence["finding_id"], evidence["assessment_id"],
                                evidence["ingestion_run_id"], evidence["release_id"],
                                identity_digest, artifact_id, semantic_digest,
                            ),
                        )
                    connection.commit()
                    mutation_outcome.append("committed")
                except errors.ObjectNotInPrerequisiteState:
                    connection.rollback()
                    mutation_outcome.append("sealed_conflict")
                finally:
                    connection.close()

            thread = threading.Thread(target=mutate)
            thread.start()
            self.assertTrue(started.wait(5))
            sealer.commit()
            thread.join(20)
            self.assertFalse(thread.is_alive())
            self.assertEqual(mutation_outcome, ["sealed_conflict"])
        finally:
            sealer.close()


@unittest.skipUnless(
    os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1",
    "requires isolated PostgreSQL database creation privileges",
)
class ScientificEvidenceSnapshotLifecycleTests(unittest.TestCase):
    def test_fresh_chain_and_empty_downgrade(self):
        database = _create_database("empty_downgrade")
        try:
            _alembic(database, "upgrade", REVISION)
            self.assertEqual(_revision(database), REVISION)
            _alembic(database, "downgrade", PARENT_REVISION)
            self.assertEqual(_revision(database), PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    for table in SNAPSHOT_TABLES:
                        cursor.execute("SELECT to_regclass(%s)", (table,))
                        self.assertIsNone(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='scientific_evaluation_governance_events' "
                        "AND column_name IN ('snapshot_id','related_snapshot_id')"
                    )
                    self.assertEqual(cursor.fetchall(), [])
                    cursor.execute(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conrelid='scientific_evaluation_governance_events'::regclass "
                        "AND conname='ck_scientific_evaluation_governance_entity_type'"
                    )
                    restored_entity_check = cursor.fetchone()[0]
                    self.assertNotIn("evidence_snapshot", restored_entity_check)
                    cursor.execute(
                        "SELECT tgname FROM pg_trigger "
                        "WHERE tgrelid='scientific_evaluation_governance_events'::regclass "
                        "AND NOT tgisinternal AND tgname = ANY(%s) ORDER BY tgname",
                        ([
                            "trg_scientific_evaluation_governance_immutable",
                            "trg_scientific_evaluation_governance_lineage",
                        ],),
                    )
                    self.assertEqual(
                        [row[0] for row in cursor.fetchall()],
                        [
                            "trg_scientific_evaluation_governance_immutable",
                            "trg_scientific_evaluation_governance_lineage",
                        ],
                    )
            finally:
                connection.close()
        finally:
            _drop_database(database)

    def test_downgrade_refuses_building_snapshot(self):
        database = _create_database("building_downgrade")
        try:
            _alembic(database, "upgrade", REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    _insert_snapshot(cursor)
                connection.commit()
            finally:
                connection.close()
            failure = _alembic(database, "downgrade", PARENT_REVISION, success=False)
            self.assertIn("not representable", failure.stdout + failure.stderr)
            self.assertEqual(_revision(database), REVISION)
        finally:
            _drop_database(database)

    def test_downgrade_refuses_sealed_snapshot_history(self):
        database = _create_database("sealed_downgrade")
        try:
            _alembic(database, "upgrade", REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    snapshot_id, _ = _insert_snapshot(cursor)
                    _seal_snapshot(cursor, snapshot_id, 0)
                connection.commit()
            finally:
                connection.close()
            failure = _alembic(database, "downgrade", PARENT_REVISION, success=False)
            self.assertIn("not representable", failure.stdout + failure.stderr)
            self.assertEqual(_revision(database), REVISION)
        finally:
            _drop_database(database)

    def test_downgrade_refuses_snapshot_governance_history(self):
        database = _create_database("governance_downgrade")
        try:
            _alembic(database, "upgrade", REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    snapshot_id, _ = _insert_snapshot(cursor)
                    cursor.execute(
                        "INSERT INTO scientific_evaluation_governance_events "
                        "(event_key,entity_type,snapshot_id,event_type,actor_identifier,"
                        "reason_code,effective_at) VALUES "
                        "(%s,'evidence_snapshot',%s,'annotation','test_actor',"
                        "'downgrade_guard',NOW())",
                        (str(uuid.uuid4()), snapshot_id),
                    )
                connection.commit()
            finally:
                connection.close()
            failure = _alembic(database, "downgrade", PARENT_REVISION, success=False)
            self.assertIn("not representable", failure.stdout + failure.stderr)
            self.assertEqual(_revision(database), REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT count(*) FROM scientific_evaluation_governance_events "
                        "WHERE snapshot_id=%s",
                        (snapshot_id,),
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
            finally:
                connection.close()
        finally:
            _drop_database(database)

    def test_upgrade_from_0019_preserves_phase_six_foundation_and_legacy(self):
        database = _create_database("preservation")
        try:
            _alembic(database, "upgrade", PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO products(barcode,product_name,category) "
                        "VALUES('snapshot-preservation','Preserved product','food')"
                    )
                    evidence = _insert_evidence(cursor, "preserved")
                    artifact_id, _ = _insert_artifact(
                        cursor, "protocol_definition", "preserved_foundation"
                    )
                    cursor.execute(
                        "INSERT INTO scientific_evaluation_protocols "
                        "(protocol_key,domain_key,target_entity_type,governance_owner,created_by) "
                        "VALUES('snapshot_preserved_protocol','food_toxicology','substance',"
                        "'board','test_actor')"
                    )
                    cursor.execute(
                        "SELECT table_name,column_name,data_type,is_nullable "
                        "FROM information_schema.columns WHERE table_schema='public' "
                        "AND table_name = ANY(%s) ORDER BY table_name,ordinal_position",
                        (list(LEGACY_TABLES),),
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
                        "SELECT count(*) FROM products WHERE barcode='snapshot-preservation'"
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
                    cursor.execute(
                        "SELECT count(*) FROM scientific_assessments WHERE id=%s",
                        (evidence["assessment_id"],),
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
                    cursor.execute(
                        "SELECT count(*) FROM scientific_evaluation_artifacts WHERE id=%s",
                        (artifact_id,),
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
                    cursor.execute(
                        "SELECT count(*) FROM scientific_evaluation_protocols "
                        "WHERE protocol_key='snapshot_preserved_protocol'"
                    )
                    self.assertEqual(cursor.fetchone()[0], 1)
                    cursor.execute(
                        "SELECT table_name,column_name,data_type,is_nullable "
                        "FROM information_schema.columns WHERE table_schema='public' "
                        "AND table_name = ANY(%s) ORDER BY table_name,ordinal_position",
                        (list(LEGACY_TABLES),),
                    )
                    self.assertEqual(cursor.fetchall(), legacy_shape)
                    cursor.execute(
                        "SELECT DISTINCT parent.relname FROM pg_constraint con "
                        "JOIN pg_class child ON child.oid=con.conrelid "
                        "JOIN pg_class parent ON parent.oid=con.confrelid "
                        "WHERE con.contype='f' AND child.relname = ANY(%s) "
                        "AND parent.relname = ANY(%s)",
                        (list(SNAPSHOT_TABLES), list(LEGACY_TABLES)),
                    )
                    self.assertEqual(cursor.fetchall(), [])
            finally:
                connection.close()
        finally:
            _drop_database(database)

    def test_preflight_collision_fails_without_partial_foundation(self):
        database = _create_database("collision")
        try:
            _alembic(database, "upgrade", PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute("CREATE TABLE scientific_evidence_snapshots(id INTEGER)")
                connection.commit()
            finally:
                connection.close()
            failure = _alembic(database, "upgrade", REVISION, success=False)
            self.assertIn("snapshot object collision", failure.stdout + failure.stderr)
            self.assertEqual(_revision(database), PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT to_regclass('scientific_evidence_snapshot_members')"
                    )
                    self.assertIsNone(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='scientific_evaluation_governance_events' "
                        "AND column_name='snapshot_id'"
                    )
                    self.assertEqual(cursor.fetchall(), [])
            finally:
                connection.close()
        finally:
            _drop_database(database)

    def test_preflight_rejects_missing_0019_governance_guard(self):
        database = _create_database("governance_preflight")
        try:
            _alembic(database, "upgrade", PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DROP TRIGGER trg_scientific_evaluation_governance_immutable "
                        "ON scientific_evaluation_governance_events"
                    )
                connection.commit()
            finally:
                connection.close()
            failure = _alembic(database, "upgrade", REVISION, success=False)
            self.assertIn(
                "expected 0019 governance shape is missing",
                failure.stdout + failure.stderr,
            )
            self.assertEqual(_revision(database), PARENT_REVISION)
            connection = _connection(database)
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT to_regclass('scientific_evidence_snapshots')")
                    self.assertIsNone(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='scientific_evaluation_governance_events' "
                        "AND column_name='snapshot_id'"
                    )
                    self.assertEqual(cursor.fetchall(), [])
            finally:
                connection.close()
        finally:
            _drop_database(database)


if __name__ == "__main__":
    unittest.main()
