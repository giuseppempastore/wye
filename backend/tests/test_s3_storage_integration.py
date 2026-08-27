import hashlib, os, requests, unittest, uuid
from moto.server import ThreadedMotoServer
from app.db import get_connection
from app.services.image_uploads import ImageUploadService
from app.storage.config import StorageSettings
from app.storage.s3 import S3StorageAdapter

JPEG=b"\xff\xd8\xff\xe0"+b"moto-e2e"*50
@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"),"requires isolated WYE_TEST_DATABASE")
class MotoEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadedMotoServer(ip_address="127.0.0.1",port=0,verbose=False); cls.server.start(); host,port=cls.server.get_host_and_port()
        cls.settings=StorageSettings("s3",f"http://{host}:{port}","wye-test","us-east-1","test","test",True,900,300,1024*1024,1800)
        cls.adapter=S3StorageAdapter(cls.settings); cls.adapter.client.create_bucket(Bucket=cls.settings.bucket)
    @classmethod
    def tearDownClass(cls): cls.server.stop()
    def test_initialize_signed_put_verify_finalize_and_signed_read(self):
        conn=get_connection(); cur=conn.cursor(); barcode=f"moto-{uuid.uuid4().hex}"; cur.execute("INSERT INTO products(barcode,product_name,category) VALUES(%s,'Moto','food') RETURNING id",(barcode,)); product=cur.fetchone()[0]; conn.commit(); cur.close(); conn.close()
        service=ImageUploadService(self.adapter,self.settings); digest=hashlib.sha256(JPEG).hexdigest(); initialized=service.initialize(product,"ingredients","image/jpeg",len(JPEG),digest)
        response=requests.put(initialized["upload_url"],data=JPEG,headers=initialized["headers"],timeout=10); self.assertLess(response.status_code,300)
        finalized=service.finalize(product,initialized["upload_id"]); self.assertEqual(finalized,service.finalize(product,initialized["upload_id"]))
        conn=get_connection(); cur=conn.cursor(); cur.execute("SELECT so.object_key FROM product_images pi JOIN storage_objects so ON so.id=pi.storage_object_id WHERE pi.id=%s",(finalized["product_image_id"],)); key=cur.fetchone()[0]; read=requests.get(self.adapter.generate_read_url(key,60),timeout=10); self.assertEqual(read.content,JPEG)
        cur.execute("DELETE FROM product_image_uploads WHERE product_id=%s",(product,)); cur.execute("DELETE FROM product_images WHERE product_id=%s",(product,)); cur.execute("DELETE FROM products WHERE id=%s",(product,)); cur.execute("DELETE FROM storage_objects WHERE bucket='wye-test'"); conn.commit(); cur.close(); conn.close()
