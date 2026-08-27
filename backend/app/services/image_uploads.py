import hashlib, secrets, tempfile, uuid
from datetime import datetime, timedelta, timezone
import psycopg2.extras
from app.db import get_connection

ALLOWED={"image/jpeg":("jpg",b"\xff\xd8\xff"),"image/png":("png",b"\x89PNG\r\n\x1a\n"),"image/webp":("webp",None)}
class UploadError(Exception):
    def __init__(self,code,message,status=422): self.code,self.message,self.status=code,message,status

def _magic(data):
    if data.startswith(ALLOWED["image/jpeg"][1]): return "image/jpeg"
    if data.startswith(ALLOWED["image/png"][1]): return "image/png"
    if len(data)>=12 and data[:4]==b"RIFF" and data[8:12]==b"WEBP": return "image/webp"
    return None

class ImageUploadService:
    def __init__(self,adapter,settings,connection_factory=get_connection): self.adapter,self.settings,self.connection_factory=adapter,settings,connection_factory
    def initialize(self,product_id,image_type,mime_type,byte_size,sha256):
        if image_type not in {"product_front","ingredients","nutrition","other"}: raise UploadError("invalid_image_type","Invalid image type")
        if mime_type not in ALLOWED: raise UploadError("mime_not_allowed","MIME type is not allowed")
        if byte_size<1 or byte_size>self.settings.max_image_bytes: raise UploadError("invalid_size","Image size exceeds policy")
        sha256=sha256.lower()
        if len(sha256)!=64 or any(c not in "0123456789abcdef" for c in sha256): raise UploadError("invalid_checksum","SHA-256 must be 64 hex characters")
        upload_id=uuid.uuid4(); key=f"staging/{upload_id}/{secrets.token_hex(16)}.{ALLOWED[mime_type][0]}"
        conn=self.connection_factory()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT 1 FROM products WHERE id=%s",(product_id,))
                if not cur.fetchone(): raise UploadError("product_not_found","Product not found",404)
                target=self.adapter.create_upload(key,mime_type,self.settings.upload_ttl)
                cur.execute("""INSERT INTO product_image_uploads(id,product_id,image_type,storage_provider,bucket,staging_object_key,declared_mime_type,declared_byte_size,declared_checksum_value,expires_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()+(%s||' seconds')::interval)""",(str(upload_id),product_id,image_type,self.settings.provider,self.settings.bucket,key,mime_type,byte_size,sha256,self.settings.cleanup_after))
            conn.commit()
        except: conn.rollback(); raise
        finally: conn.close()
        return {"upload_id":str(upload_id),"upload_url":target.url,"method":"PUT","headers":target.headers,"expires_at":target.expires_at}
    def _fail(self,upload_id,code,detail):
        conn=self.connection_factory()
        try:
            with conn.cursor() as cur: cur.execute("UPDATE product_image_uploads SET status='failed',failure_code=%s,failure_detail=%s,updated_at=NOW() WHERE id=%s AND status<>'finalized'",(code,detail[:500],str(upload_id)))
            conn.commit()
        finally: conn.close()
    def finalize(self,product_id,upload_id):
        conn=self.connection_factory()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM product_image_uploads WHERE id=%s AND product_id=%s FOR UPDATE",(str(upload_id),product_id)); row=cur.fetchone()
                if not row: raise UploadError("upload_not_found","Upload not found",404)
                if row["status"]=="finalized": return self._result(row)
                if row["status"] in {"failed","abandoned"}: raise UploadError("upload_terminal","Upload is not finalizable",409)
                cur.execute("UPDATE product_image_uploads SET status='verifying',verification_started_at=NOW(),updated_at=NOW() WHERE id=%s",(str(upload_id),))
            conn.commit()
        finally: conn.close()
        try:
            head=self.adapter.head_object(row["staging_object_key"])
            if not head: raise UploadError("object_missing","Uploaded object does not exist",404)
            if head.byte_size!=row["declared_byte_size"]: raise UploadError("size_mismatch","Uploaded size does not match declaration")
            if head.mime_type and head.mime_type.split(';')[0].lower()!=row["declared_mime_type"]: raise UploadError("mime_mismatch","Storage MIME does not match declaration")
            with tempfile.SpooledTemporaryFile(max_size=min(self.settings.max_image_bytes,2*1024*1024)) as tmp:
                self.adapter.download_to(row["staging_object_key"],tmp); size=tmp.tell()
                if size>self.settings.max_image_bytes: raise UploadError("file_too_large","Uploaded object exceeds policy")
                tmp.seek(0); prefix=tmp.read(16); mime=_magic(prefix); tmp.seek(0)
                if mime!=row["declared_mime_type"]: raise UploadError("content_mismatch","File signature does not match MIME")
                digest=hashlib.sha256()
                while True:
                    chunk=tmp.read(1024*1024)
                    if not chunk: break
                    digest.update(chunk)
                checksum=digest.hexdigest()
                if checksum!=row["declared_checksum_value"]: raise UploadError("checksum_mismatch","SHA-256 does not match declaration")
                final_key=f"objects/sha256/{checksum[:2]}/{checksum}"
                final=self.adapter.head_object(final_key)
                if final and (final.byte_size!=size or (final.metadata or {}).get("wye-sha256") not in {None,checksum}): raise UploadError("storage_collision","Existing content-addressed object conflicts",500)
                if not final: tmp.seek(0); final=self.adapter.put_object(final_key,tmp,mime,checksum)
            result=self._commit(row,final_key,final.version if final else None,mime,size,checksum)
            try: self.adapter.delete_object(row["staging_object_key"])
            except Exception: pass
            return result
        except UploadError as e:
            self._fail(upload_id,e.code,e.message)
            try: self.adapter.delete_object(row["staging_object_key"])
            except Exception: pass
            raise
    def _commit(self,row,key,version,mime,size,checksum):
        conn=self.connection_factory()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM product_image_uploads WHERE id=%s FOR UPDATE",(str(row["id"]),)); locked=cur.fetchone()
                if locked["status"]=="finalized": return self._result(locked)
                cur.execute("SELECT id FROM products WHERE id=%s FOR UPDATE",(row["product_id"],))
                cur.execute("""INSERT INTO storage_objects(storage_provider,bucket,object_key,object_version,checksum_algorithm,checksum_value,mime_type,byte_size) VALUES(%s,%s,%s,%s,'sha256',%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id""",(self.settings.provider,self.settings.bucket,key,version,checksum,mime,size)); found=cur.fetchone()
                if found: storage_id=found["id"]
                else:
                    cur.execute("SELECT id FROM storage_objects WHERE storage_provider=%s AND bucket=%s AND object_key=%s AND COALESCE(object_version,'')=COALESCE(%s,'')",(self.settings.provider,self.settings.bucket,key,version)); storage_id=cur.fetchone()["id"]
                cur.execute("SELECT * FROM product_images WHERE product_id=%s AND image_type=%s AND is_current=TRUE FOR UPDATE",(row["product_id"],row["image_type"])); old=cur.fetchone()
                if old and old["storage_object_id"]==storage_id: image_id=old["id"]
                else:
                    cur.execute("""INSERT INTO product_images(product_id,image_type,storage_object_id,mime_type,byte_size,checksum,source,status,is_current,provenance) VALUES(%s,%s,%s,%s,%s,%s,'user_submission','rejected',FALSE,%s::jsonb) RETURNING id""",(row["product_id"],row["image_type"],storage_id,mime,size,checksum,'{"phase":"image_upload_v1"}')); image_id=cur.fetchone()["id"]
                    if old: cur.execute("UPDATE product_images SET status='superseded',is_current=FALSE,superseded_at=NOW(),superseded_by_image_id=%s WHERE id=%s",(image_id,old["id"]))
                    cur.execute("UPDATE product_images SET status='active',is_current=TRUE WHERE id=%s",(image_id,))
                cur.execute("""UPDATE product_image_uploads SET status='finalized',verified_mime_type=%s,verified_byte_size=%s,verified_checksum_algorithm='sha256',verified_checksum_value=%s,verified_at=NOW(),storage_object_id=%s,product_image_id=%s,finalized_at=NOW(),updated_at=NOW() WHERE id=%s RETURNING *""",(mime,size,checksum,storage_id,image_id,str(row["id"]))); result=self._result(cur.fetchone())
            conn.commit(); return result
        except: conn.rollback(); raise
        finally: conn.close()
    @staticmethod
    def _result(row): return {"upload_id":str(row["id"]),"status":"finalized","storage_object_id":row["storage_object_id"],"product_image_id":row["product_image_id"]}
