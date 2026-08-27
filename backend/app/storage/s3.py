from datetime import datetime, timedelta, timezone
from botocore.config import Config
from botocore.exceptions import ClientError
import boto3
from .base import StorageAdapter, UploadTarget, ObjectMetadata

class S3StorageAdapter(StorageAdapter):
    def __init__(self, settings):
        self.settings=settings
        self.client=boto3.client("s3",endpoint_url=settings.endpoint,region_name=settings.region,aws_access_key_id=settings.access_key,aws_secret_access_key=settings.secret_key,config=Config(signature_version="s3v4",s3={"addressing_style":"path" if settings.force_path_style else "auto"}))
    def create_upload(self,key,mime_type,ttl):
        url=self.client.generate_presigned_url("put_object",Params={"Bucket":self.settings.bucket,"Key":key,"ContentType":mime_type},ExpiresIn=ttl)
        return UploadTarget(url,{"Content-Type":mime_type},datetime.now(timezone.utc)+timedelta(seconds=ttl))
    def head_object(self,key):
        try: r=self.client.head_object(Bucket=self.settings.bucket,Key=key)
        except ClientError as e:
            if e.response.get("Error",{}).get("Code") in {"404","NoSuchKey","NotFound"}: return None
            raise
        return ObjectMetadata(key,r["ContentLength"],r.get("ContentType"),r.get("VersionId"),r.get("Metadata",{}))
    def download_to(self,key,target):
        body=self.client.get_object(Bucket=self.settings.bucket,Key=key)["Body"]
        for chunk in body.iter_chunks(1024*1024): target.write(chunk)
    def put_object(self,key,source,mime_type,sha256):
        source.seek(0); self.client.upload_fileobj(source,self.settings.bucket,key,ExtraArgs={"ContentType":mime_type,"Metadata":{"wye-sha256":sha256}})
        return self.head_object(key)
    def generate_read_url(self,key,ttl): return self.client.generate_presigned_url("get_object",Params={"Bucket":self.settings.bucket,"Key":key},ExpiresIn=ttl)
    def delete_object(self,key): self.client.delete_object(Bucket=self.settings.bucket,Key=key)
