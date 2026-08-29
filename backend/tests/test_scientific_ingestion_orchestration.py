import os
import subprocess
import sys
import threading
import unittest
import uuid
from pathlib import Path

import psycopg2

from app.db import get_connection
from app.scientific_ingestion.contracts import (
    ScientificAdapterMetadata, ScientificIngestionConfiguration, ScientificReleaseIdentity,
)
from app.repositories.scientific_ingestion import ArtifactRow
from app.services.scientific_ingestion import (
    ScientificArtifactIntegrityError, ScientificIngestionService,
    ScientificInvalidRunTransition, ScientificResourceNotFound,
)


def contracts(source_key, dataset_key, release_key, parser="parser-1", semantic=None):
    metadata = ScientificAdapterMetadata(
        source_key=source_key, dataset_key=dataset_key, adapter_version="adapter-1",
        acquisition_version="acquisition-1", parser_version=parser,
        normalization_schema_version="normalization-1",
    )
    return (ScientificReleaseIdentity(source_key=source_key, dataset_key=dataset_key,
            external_release_key=release_key),
            ScientificIngestionConfiguration(adapter=metadata,
                                               semantic_configuration=semantic or {}))


class ScientificIngestionOrchestrationUnitTests(unittest.TestCase):
    def artifact(self, **overrides):
        values=dict(id=1,release_id=10,storage_object_id=20,artifact_key="primary",
                    artifact_role="primary",raw_checksum_algorithm="sha256",
                    raw_checksum_value="a"*64,byte_size=12,
                    storage_checksum_algorithm="sha256",storage_checksum_value="a"*64,
                    storage_byte_size=12)
        values.update(overrides)
        return ArtifactRow(**values)

    def test_same_release_and_storage_metadata_validation(self):
        ScientificIngestionService._validate_artifacts(10,(self.artifact(),))
        with self.assertRaises(ScientificArtifactIntegrityError):
            ScientificIngestionService._validate_artifacts(11,(self.artifact(),))
        with self.assertRaises(ScientificArtifactIntegrityError):
            ScientificIngestionService._validate_artifacts(10,(self.artifact(storage_checksum_value="b"*64),))
        with self.assertRaises(ScientificArtifactIntegrityError):
            ScientificIngestionService._validate_artifacts(10,(self.artifact(storage_byte_size=13),))

    def test_configuration_identity_and_selection_fail_before_database_access(self):
        release, config=contracts("test_source","test_dataset","release_1")
        _, wrong=contracts("other_source","test_dataset","release_1")
        def forbidden_connection():
            raise AssertionError("database must not be reached")
        service=ScientificIngestionService(connection_factory=forbidden_connection)
        with self.assertRaises(ScientificArtifactIntegrityError):
            service.prepare_ingestion_run(release,wrong,("primary",),"x")
        with self.assertRaises(ScientificArtifactIntegrityError):
            service.prepare_ingestion_run(release,config,(),"x")
        with self.assertRaises(ScientificArtifactIntegrityError):
            service.prepare_ingestion_run(release,config,("primary","primary"),"x")

    def test_invalid_terminal_counters_fail_before_database_access(self):
        service=ScientificIngestionService(connection_factory=lambda: (_ for _ in ()).throw(AssertionError("database must not be reached")))
        with self.assertRaises(ScientificInvalidRunTransition):
            service.mark_succeeded(1,records_seen=1,records_accepted=1,records_rejected=1,
                assessments_written=0,findings_written=0,warnings_count=0)


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated PostgreSQL at 0013")
class ScientificIngestionOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.ids = []

    def tearDown(self):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                for source_id in reversed(self.ids):
                    cur.execute("DELETE FROM scientific_ingestion_run_artifacts WHERE ingestion_run_id IN (SELECT id FROM scientific_ingestion_runs WHERE release_id IN (SELECT r.id FROM source_dataset_releases r JOIN source_datasets d ON d.id=r.dataset_id WHERE d.source_id=%s))", (source_id,))
                    cur.execute("DELETE FROM scientific_ingestion_runs WHERE release_id IN (SELECT r.id FROM source_dataset_releases r JOIN source_datasets d ON d.id=r.dataset_id WHERE d.source_id=%s)", (source_id,))
                    cur.execute("DELETE FROM scientific_release_artifacts WHERE release_id IN (SELECT r.id FROM source_dataset_releases r JOIN source_datasets d ON d.id=r.dataset_id WHERE d.source_id=%s)", (source_id,))
                    cur.execute("DELETE FROM storage_objects WHERE object_key LIKE %s", (f"phase622/{source_id}/%",))
                    cur.execute("DELETE FROM source_dataset_releases WHERE dataset_id IN (SELECT id FROM source_datasets WHERE source_id=%s)", (source_id,))
                    cur.execute("DELETE FROM source_datasets WHERE source_id=%s", (source_id,))
                    cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()
        finally:
            conn.close()

    def fixture(self, keys=("artifact_a", "artifact_b", "artifact_c"), release_key=None):
        suffix = uuid.uuid4().hex
        source_key, dataset_key = f"test_source_{suffix}", f"test_dataset_{suffix}"
        release_key = release_key or f"release_{suffix}"
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id", (source_key, source_key))
                source_id = cur.fetchone()[0]; self.ids.append(source_id)
                cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,%s,%s) RETURNING id", (source_id,dataset_key,dataset_key)); dataset_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,%s) RETURNING id", (dataset_id,release_key,release_key)); release_id=cur.fetchone()[0]
                artifacts = {}
                for position, key in enumerate(keys):
                    checksum = format(position + 1, "064x")
                    cur.execute("INSERT INTO storage_objects(storage_provider,bucket,object_key,byte_size,checksum_algorithm,checksum_value) VALUES('test','scientific',%s,%s,'sha256',%s) RETURNING id", (f"phase622/{source_id}/{key}", position+10, checksum)); storage_id=cur.fetchone()[0]
                    cur.execute("INSERT INTO scientific_release_artifacts(release_id,storage_object_id,artifact_key,artifact_role,raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at) VALUES(%s,%s,%s,%s,'sha256',%s,%s,NOW()) RETURNING id", (release_id,storage_id,key,"primary" if position==0 else "attachment",checksum,position+10)); artifacts[key]=cur.fetchone()[0]
            conn.commit()
        finally: conn.close()
        release, config = contracts(source_key,dataset_key,release_key)
        return release_id, artifacts, release, config

    def service(self): return ScientificIngestionService()

    def test_create_subset_positions_lookup_and_provenance_traversal(self):
        release_id, artifacts, release, config = self.fixture()
        result = self.service().prepare_ingestion_run(release, config, ("artifact_c","artifact_a"), "retry-1")
        self.assertFalse(result.reused); self.assertEqual([a.artifact_key for a in result.manifest.artifacts], ["artifact_a","artifact_c"])
        self.assertEqual(self.service().get_run(result.run_key).id, result.id)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT a.artifact_key,j.manifest_position,s.source_key FROM scientific_ingestion_runs r JOIN scientific_ingestion_run_artifacts j ON j.ingestion_run_id=r.id JOIN scientific_release_artifacts a ON a.id=j.release_artifact_id JOIN storage_objects o ON o.id=a.storage_object_id JOIN source_dataset_releases rel ON rel.id=r.release_id JOIN source_datasets d ON d.id=rel.dataset_id JOIN sources s ON s.id=d.source_id WHERE r.id=%s ORDER BY j.manifest_position", (result.id,))
                self.assertEqual([(r[0],r[1]) for r in cur.fetchall()], [("artifact_a",0),("artifact_c",1)])
        finally: conn.close()

    def test_idempotency_versions_and_manifest(self):
        _, _, release, config = self.fixture()
        first=self.service().prepare_ingestion_run(release,config,("artifact_a",),"same")
        retry=self.service().prepare_ingestion_run(release,config,("artifact_a",),"same")
        other_key=self.service().prepare_ingestion_run(release,config,("artifact_a",),"other")
        _, parser2=contracts(release.source_key,release.dataset_key,release.external_release_key,"parser-2")
        other_parser=self.service().prepare_ingestion_run(release,parser2,("artifact_a",),"same")
        other_manifest=self.service().prepare_ingestion_run(release,config,("artifact_b",),"same")
        self.assertTrue(retry.reused); self.assertEqual(first.run_key,retry.run_key)
        self.assertEqual(len({first.run_key,other_key.run_key,other_parser.run_key,other_manifest.run_key}),4)

    def test_missing_cross_release_and_checksum_mismatch_are_rejected_without_run(self):
        release_id, artifacts, release, config=self.fixture()
        with self.assertRaises(ScientificResourceNotFound): self.service().prepare_ingestion_run(release,config,("missing",),"x")
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("UPDATE storage_objects SET checksum_value=%s WHERE id=(SELECT storage_object_id FROM scientific_release_artifacts WHERE id=%s)", ("f"*64,artifacts["artifact_a"]))
            conn.commit()
        finally: conn.close()
        with self.assertRaises(ScientificArtifactIntegrityError): self.service().prepare_ingestion_run(release,config,("artifact_a",),"x")
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT count(*) FROM scientific_ingestion_runs WHERE release_id=%s",(release_id,)); self.assertEqual(cur.fetchone()[0],0)
        finally: conn.close()

    def test_junction_constraints_and_fk_restrict(self):
        _, artifacts, release, config=self.fixture()
        run=self.service().prepare_ingestion_run(release,config,("artifact_a","artifact_b"),"x")
        conn=get_connection(); conn.autocommit=False
        try:
            with conn.cursor() as cur:
                for sql,args in [
                    ("INSERT INTO scientific_ingestion_run_artifacts VALUES(%s,%s,2,NOW())",(run.id,artifacts["artifact_a"])),
                    ("UPDATE scientific_ingestion_run_artifacts SET manifest_position=0 WHERE ingestion_run_id=%s AND release_artifact_id=%s",(run.id,artifacts["artifact_b"])),
                    ("UPDATE scientific_ingestion_run_artifacts SET manifest_position=-1 WHERE ingestion_run_id=%s AND release_artifact_id=%s",(run.id,artifacts["artifact_b"])),
                    ("DELETE FROM scientific_release_artifacts WHERE id=%s",(artifacts["artifact_a"],))]:
                    with self.assertRaises(psycopg2.IntegrityError): cur.execute(sql,args)
                    conn.rollback()
        finally: conn.close()

    def test_status_transitions_and_counters(self):
        _,_,release,config=self.fixture()
        run=self.service().prepare_ingestion_run(release,config,("artifact_a",),"x")
        self.assertEqual(self.service().mark_running(run.id).run_status,"running")
        succeeded=self.service().mark_succeeded(run.id,records_seen=3,records_accepted=2,records_rejected=1,assessments_written=2,findings_written=4,warnings_count=0)
        self.assertEqual(succeeded.run_status,"succeeded")
        with self.assertRaises(ScientificInvalidRunTransition): self.service().mark_running(run.id)

    def test_concurrent_idempotent_callers_converge(self):
        _,_,release,config=self.fixture(); barrier=threading.Barrier(2); results=[]; errors=[]
        def worker():
            try:
                barrier.wait(); results.append(self.service().prepare_ingestion_run(release,config,("artifact_a","artifact_c"),"race"))
            except Exception as exc: errors.append(exc)
        threads=[threading.Thread(target=worker) for _ in range(2)]
        [t.start() for t in threads]; [t.join(20) for t in threads]
        self.assertFalse(errors); self.assertEqual(len(results),2); self.assertEqual(results[0].run_key,results[1].run_key)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT count(DISTINCT r.id),count(j.*) FROM scientific_ingestion_runs r LEFT JOIN scientific_ingestion_run_artifacts j ON j.ingestion_run_id=r.id WHERE r.run_key=%s GROUP BY r.id",(str(results[0].run_key),)); self.assertEqual(cur.fetchone(),(1,2))
        finally: conn.close()


@unittest.skipUnless(os.getenv("WYE_RUN_MIGRATION_LIFECYCLE_TESTS") == "1", "requires isolated PostgreSQL lifecycle DB")
class IngestionRunArtifactLifecycleTests(unittest.TestCase):
    backend=Path(__file__).resolve().parents[1]
    def alembic(self,*args,success=True):
        result=subprocess.run([sys.executable,"-m","alembic",*args],cwd=self.backend,text=True,capture_output=True)
        self.assertEqual(result.returncode==0,success,result.stdout+result.stderr); return result
    def test_safe_and_unsafe_downgrade(self):
        self.alembic("downgrade","0012_ingredient_substance_guard")
        self.alembic("upgrade","0013_ingestion_run_artifacts")
        self.alembic("downgrade","0012_ingredient_substance_guard")
        self.alembic("upgrade","0013_ingestion_run_artifacts")
        conn=get_connection()
        try:
            with conn.cursor() as cur: cur.execute("SELECT to_regclass('scientific_ingestion_run_artifacts')"); self.assertIsNotNone(cur.fetchone()[0])
        finally: conn.close()
        suffix=uuid.uuid4().hex
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO sources(source_key,source_name,source_type) VALUES(%s,%s,'scientific') RETURNING id",(f"lifecycle_source_{suffix}",suffix)); source_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_datasets(source_id,dataset_name,dataset_key) VALUES(%s,%s,%s) RETURNING id",(source_id,suffix,f"lifecycle_dataset_{suffix}")); dataset_id=cur.fetchone()[0]
                cur.execute("INSERT INTO source_dataset_releases(dataset_id,external_release_key,version_label) VALUES(%s,%s,%s) RETURNING id",(dataset_id,f"lifecycle_release_{suffix}",suffix)); release_id=cur.fetchone()[0]
                checksum="a"*64
                cur.execute("INSERT INTO storage_objects(storage_provider,bucket,object_key,byte_size,checksum_algorithm,checksum_value) VALUES('test','scientific',%s,1,'sha256',%s) RETURNING id",(f"lifecycle/{suffix}",checksum)); storage_id=cur.fetchone()[0]
                cur.execute("INSERT INTO scientific_release_artifacts(release_id,storage_object_id,artifact_key,artifact_role,raw_checksum_algorithm,raw_checksum_value,byte_size,acquired_at) VALUES(%s,%s,'primary','primary','sha256',%s,1,NOW()) RETURNING id",(release_id,storage_id,checksum)); artifact_id=cur.fetchone()[0]
                cur.execute("INSERT INTO scientific_ingestion_runs(release_id,run_key,importer_name,importer_version,source_adapter_version,acquisition_version,parser_version,normalization_schema_version,artifact_manifest_algorithm,artifact_manifest_fingerprint) VALUES(%s,%s,'test','1','1','1','1','1','sha256',%s) RETURNING id",(release_id,str(uuid.uuid4()),checksum)); run_id=cur.fetchone()[0]
                cur.execute("INSERT INTO scientific_ingestion_run_artifacts VALUES(%s,%s,0,NOW())",(run_id,artifact_id))
            conn.commit()
        finally: conn.close()
        result=self.alembic("downgrade","0012_ingredient_substance_guard",success=False)
        self.assertIn("contains non-representable provenance",result.stdout+result.stderr)
        conn=get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version_num FROM alembic_version"); self.assertEqual(cur.fetchone()[0],"0013_ingestion_run_artifacts")
                cur.execute("SELECT count(*) FROM scientific_ingestion_run_artifacts WHERE ingestion_run_id=%s",(run_id,)); self.assertEqual(cur.fetchone()[0],1)
                cur.execute("DELETE FROM scientific_ingestion_run_artifacts WHERE ingestion_run_id=%s",(run_id,)); cur.execute("DELETE FROM scientific_ingestion_runs WHERE id=%s",(run_id,))
                cur.execute("DELETE FROM scientific_release_artifacts WHERE id=%s",(artifact_id,)); cur.execute("DELETE FROM storage_objects WHERE id=%s",(storage_id,))
                cur.execute("DELETE FROM source_dataset_releases WHERE id=%s",(release_id,)); cur.execute("DELETE FROM source_datasets WHERE id=%s",(dataset_id,)); cur.execute("DELETE FROM sources WHERE id=%s",(source_id,))
            conn.commit()
        finally: conn.close()


if __name__ == "__main__": unittest.main()
