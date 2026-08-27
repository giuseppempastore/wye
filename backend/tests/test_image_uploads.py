import hashlib, io, os, threading, unittest, uuid
from dataclasses import replace
from datetime import datetime, timezone
from app.db import get_connection
from app.services.image_uploads import ImageUploadService, UploadError
from app.storage.base import ObjectMetadata, UploadTarget
from app.storage.config import StorageSettings

JPEG=b"\xff\xd8\xff\xe0"+b"wye-image"*20
class FakeStorage:
    def __init__(self): self.objects={}; self.lock=threading.Lock()
    def create_upload(self,key,mime,ttl): return UploadTarget("https://upload.invalid/"+key,{"Content-Type":mime},datetime.now(timezone.utc))
    def head_object(self,key):
        with self.lock: value=self.objects.get(key)
        return None if value is None else ObjectMetadata(key,len(value[0]),value[1],None,value[2])
    def download_to(self,key,target): target.write(self.objects[key][0])
    def put_object(self,key,source,mime,sha):
        with self.lock: self.objects.setdefault(key,(source.read(),mime,{"wye-sha256":sha}))
        return self.head_object(key)
    def generate_read_url(self,key,ttl): return f"https://read.invalid/{key}?ttl={ttl}"
    def delete_object(self,key): self.objects.pop(key,None)

@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"),"requires isolated WYE_TEST_DATABASE")
class UploadLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings=StorageSettings("s3",None,"test","us-east-1","x","x",True,900,300,1024*1024,1800)
    def setUp(self):
        self.storage=FakeStorage(); self.service=ImageUploadService(self.storage,self.settings)
        conn=get_connection(); cur=conn.cursor(); suffix=uuid.uuid4().hex
        cur.execute("INSERT INTO products(barcode,product_name,category) VALUES(%s,'Upload test','food') RETURNING id",(f"upload-{suffix}",)); self.product=cur.fetchone()[0]; conn.commit(); cur.close(); conn.close()
    def tearDown(self):
        conn=get_connection(); cur=conn.cursor(); cur.execute("DELETE FROM product_image_uploads WHERE product_id=%s",(self.product,)); cur.execute("DELETE FROM product_images WHERE product_id=%s",(self.product,)); cur.execute("DELETE FROM products WHERE id=%s",(self.product,)); cur.execute("DELETE FROM storage_objects so WHERE NOT EXISTS(SELECT 1 FROM product_images pi WHERE pi.storage_object_id=so.id) AND so.bucket='test'"); conn.commit(); cur.close(); conn.close()
    def init(self,data=JPEG,mime="image/jpeg",kind="product_front"):
        digest=hashlib.sha256(data).hexdigest(); result=self.service.initialize(self.product,kind,mime,len(data),digest)
        key=result["upload_url"].split("upload.invalid/",1)[1]; self.storage.objects[key]=(data,mime,{})
        return result
    def test_policy_and_missing_product(self):
        with self.assertRaises(UploadError): self.service.initialize(self.product,"product_front","image/gif",10,"a"*64)
        with self.assertRaises(UploadError): self.service.initialize(self.product,"product_front","image/jpeg",self.settings.max_image_bytes+1,"a"*64)
        with self.assertRaises(UploadError) as caught: self.service.initialize(999999999,"product_front","image/jpeg",10,"a"*64)
        self.assertEqual(caught.exception.status,404)
    def test_finalize_is_idempotent_and_reuses_blob(self):
        upload=self.init(); first=self.service.finalize(self.product,upload["upload_id"]); second=self.service.finalize(self.product,upload["upload_id"])
        self.assertEqual(first,second)
        another=self.init(); reused=self.service.finalize(self.product,another["upload_id"])
        self.assertEqual(first["storage_object_id"],reused["storage_object_id"]); self.assertEqual(first["product_image_id"],reused["product_image_id"])
    def test_absent_size_checksum_and_magic_mismatches_fail(self):
        upload=self.service.initialize(self.product,"product_front","image/jpeg",len(JPEG),hashlib.sha256(JPEG).hexdigest())
        with self.assertRaises(UploadError): self.service.finalize(self.product,upload["upload_id"])
        upload=self.service.initialize(self.product,"product_front","image/jpeg",len(JPEG),hashlib.sha256(JPEG).hexdigest())
        key=upload["upload_url"].split("upload.invalid/",1)[1]
        self.storage.objects[key]=(JPEG[:-1]+b"x","image/jpeg",{})
        with self.assertRaises(UploadError): self.service.finalize(self.product,upload["upload_id"])
        invalid=b"not-an-image".ljust(len(JPEG),b"x")
        upload=self.init(data=invalid)
        with self.assertRaises(UploadError): self.service.finalize(self.product,upload["upload_id"])
    def test_supersession_and_concurrent_finalize_leave_one_current(self):
        uploads=[]
        for marker in (b"a",b"b"):
            data=b"\xff\xd8\xff"+marker*100; uploads.append(self.init(data=data))
        results=[]; errors=[]
        def run(u):
            try: results.append(self.service.finalize(self.product,u["upload_id"]))
            except Exception as e: errors.append(e)
        threads=[threading.Thread(target=run,args=(u,)) for u in uploads]
        [t.start() for t in threads]; [t.join() for t in threads]
        self.assertFalse(errors); self.assertEqual(len(results),2)
        conn=get_connection(); cur=conn.cursor(); cur.execute("SELECT count(*) FROM product_images WHERE product_id=%s AND image_type='product_front' AND is_current",(self.product,)); self.assertEqual(cur.fetchone()[0],1); cur.close(); conn.close()
