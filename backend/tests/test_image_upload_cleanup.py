import os, unittest, uuid
from unittest.mock import patch
from app.db import get_connection
from app.storage.config import StorageSettings
from scripts.cleanup_image_uploads import cleanup

class DeletingStorage:
    def __init__(self): self.deleted=[]
    def delete_object(self,key): self.deleted.append(key)

@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"),"requires isolated WYE_TEST_DATABASE")
class UploadCleanupTests(unittest.TestCase):
    def test_expired_upload_is_abandoned_and_only_staging_key_is_deleted(self):
        conn=get_connection(); cur=conn.cursor(); suffix=uuid.uuid4().hex
        cur.execute("INSERT INTO products(barcode,product_name,category) VALUES(%s,'Cleanup','food') RETURNING id",(f"cleanup-{suffix}",)); product=cur.fetchone()[0]
        upload=uuid.uuid4(); key=f"staging/{upload}/orphan.jpg"
        cur.execute("""INSERT INTO product_image_uploads(id,product_id,image_type,storage_provider,bucket,staging_object_key,declared_mime_type,declared_byte_size,declared_checksum_value,expires_at) VALUES(%s,%s,'other','s3','test',%s,'image/jpeg',10,%s,NOW()-INTERVAL '1 minute')""",(str(upload),product,key,"a"*64)); conn.commit()
        storage=DeletingStorage(); settings=StorageSettings("s3",None,"test","us-east-1","x","x",True,900,300,100,1800)
        with patch("scripts.cleanup_image_uploads.StorageSettings.from_env",return_value=settings), patch("scripts.cleanup_image_uploads.get_storage_adapter",return_value=storage): self.assertEqual(cleanup(),1)
        cur.execute("SELECT status FROM product_image_uploads WHERE id=%s",(str(upload),)); self.assertEqual(cur.fetchone()[0],"abandoned"); self.assertEqual(storage.deleted,[key])
        cur.execute("DELETE FROM product_image_uploads WHERE id=%s",(str(upload),)); cur.execute("DELETE FROM products WHERE id=%s",(product,)); conn.commit(); cur.close(); conn.close()
