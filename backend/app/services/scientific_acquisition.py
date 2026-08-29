"""Artifact-first registration for acquired scientific bytes."""

from dataclasses import dataclass
import io
import json

import psycopg2.extras

from app.db import get_connection
from app.scientific_ingestion.contracts import ScientificArtifactReference
from app.scientific_ingestion.errors import ScientificPersistenceConflict


@dataclass(frozen=True)
class RegisteredScientificArtifact:
    release_id: int
    reference: ScientificArtifactReference
    reused: bool


class ScientificArtifactRegistrationService:
    """Serialize one logical artifact and reject changed upstream bytes."""

    def __init__(self, storage, *, storage_provider="local", bucket="scientific",
                 connection_factory=get_connection):
        self.storage, self.storage_provider, self.bucket = storage, storage_provider, bucket
        self.connection_factory = connection_factory

    def register_efsa_qps(self, acquired, *, artifact_key="primary"):
        release = acquired.release
        object_key = f"scientific/{release.source_key}/{release.dataset_key}/{acquired.sha256}.xlsx"
        connection = self.connection_factory()
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                               (f"{release.source_key}:{release.dataset_key}:{release.external_release_key}:{artifact_key}",))
                cursor.execute("""INSERT INTO sources(source_key,source_name,source_type,url)
                    VALUES(%s,'European Food Safety Authority','scientific','https://www.efsa.europa.eu/')
                    ON CONFLICT(source_key) DO UPDATE SET source_name=EXCLUDED.source_name RETURNING id""",
                    (release.source_key,))
                source_id = cursor.fetchone()["id"]
                cursor.execute("""INSERT INTO source_datasets(source_id,dataset_name,dataset_key,description)
                    VALUES(%s,'Qualified Presumption of Safety list',%s,'Official EFSA QPS Knowledge Junction release')
                    ON CONFLICT(source_id,dataset_key) DO UPDATE SET dataset_name=EXCLUDED.dataset_name RETURNING id""",
                    (source_id, release.dataset_key))
                dataset_id = cursor.fetchone()["id"]
                cursor.execute("""INSERT INTO source_dataset_releases(
                    dataset_id,external_release_key,version_label,released_at,source_url,format,release_status,license_text)
                    VALUES(%s,%s,%s,%s,%s,'xlsx','validated',%s)
                    ON CONFLICT(dataset_id,external_release_key) DO UPDATE
                    SET version_label=source_dataset_releases.version_label RETURNING id""",
                    (dataset_id, release.external_release_key, release.external_release_key,
                     acquired.released_on, acquired.locator, acquired.license_id))
                release_id = cursor.fetchone()["id"]
                cursor.execute("""SELECT a.id,a.storage_object_id,a.raw_checksum_value,a.byte_size,
                    o.object_key FROM scientific_release_artifacts a JOIN storage_objects o ON o.id=a.storage_object_id
                    WHERE a.release_id=%s AND a.artifact_key=%s FOR UPDATE""", (release_id, artifact_key))
                existing = cursor.fetchone()
                if existing:
                    if existing["raw_checksum_value"] != acquired.sha256 or existing["byte_size"] != acquired.byte_size:
                        raise ScientificPersistenceConflict("same EFSA release has changed upstream artifact bytes")
                    reference = self._reference(existing["storage_object_id"], artifact_key, acquired)
                    connection.commit()
                    return RegisteredScientificArtifact(release_id, reference, True)
                metadata = self.storage.head_object(object_key)
                if metadata is None:
                    metadata = self.storage.put_object(object_key, io.BytesIO(acquired.body),
                                                       acquired.content_type, acquired.sha256)
                elif metadata.byte_size != acquired.byte_size or (metadata.metadata or {}).get("sha256") not in (None, acquired.sha256):
                    raise ScientificPersistenceConflict("content-addressed storage object integrity conflict")
                cursor.execute("""INSERT INTO storage_objects(storage_provider,bucket,object_key,object_version,
                    checksum_algorithm,checksum_value,mime_type,byte_size)
                    VALUES(%s,%s,%s,%s,'sha256',%s,%s,%s)
                    ON CONFLICT DO NOTHING RETURNING id""", (self.storage_provider, self.bucket, object_key,
                    metadata.version, acquired.sha256, acquired.content_type, acquired.byte_size))
                row = cursor.fetchone()
                if row is None:
                    cursor.execute("""SELECT id FROM storage_objects WHERE storage_provider=%s AND bucket=%s
                        AND object_key=%s AND COALESCE(object_version,'')=COALESCE(%s,'')""",
                        (self.storage_provider, self.bucket, object_key, metadata.version))
                    row = cursor.fetchone()
                storage_id = row["id"]
                provenance = {**acquired.acquisition_metadata, "locator": acquired.locator,
                    "record_doi": acquired.record_doi, "concept_doi": acquired.concept_doi,
                    "provider_checksum": acquired.provider_checksum,
                    "checksum_established_before_persistence": True}
                cursor.execute("""INSERT INTO scientific_release_artifacts(release_id,storage_object_id,
                    artifact_key,artifact_role,format,media_type,raw_checksum_algorithm,raw_checksum_value,
                    byte_size,acquired_at,provenance) VALUES(%s,%s,%s,'primary','xlsx',%s,'sha256',%s,%s,NOW(),%s)""",
                    (release_id, storage_id, artifact_key, acquired.content_type, acquired.sha256,
                     acquired.byte_size, psycopg2.extras.Json(provenance)))
            connection.commit()
            return RegisteredScientificArtifact(release_id, self._reference(storage_id, artifact_key, acquired), False)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _reference(storage_id, artifact_key, acquired):
        return ScientificArtifactReference(artifact_key=artifact_key, artifact_role="primary",
            storage_object_id=storage_id, raw_checksum_algorithm="sha256",
            raw_checksum_value=acquired.sha256, byte_size=acquired.byte_size,
            source_locator=acquired.locator, content_type=acquired.content_type,
            acquisition_metadata=acquired.acquisition_metadata)


class StorageArtifactPayloadReader:
    def __init__(self, storage, key_by_storage_id, *, max_bytes=5 * 1024 * 1024):
        self.storage, self.key_by_storage_id, self.max_bytes = storage, key_by_storage_id, max_bytes

    def read_bytes(self, artifact):
        target = io.BytesIO()
        self.storage.download_to(self.key_by_storage_id(artifact.storage_object_id), target)
        body = target.getvalue()
        import hashlib
        if len(body) > self.max_bytes or len(body) != artifact.byte_size or hashlib.sha256(body).hexdigest() != artifact.raw_checksum_value:
            raise ScientificPersistenceConflict("stored scientific artifact failed read-time integrity verification")
        return body
