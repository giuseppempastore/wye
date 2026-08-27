from .config import StorageSettings
from .s3 import S3StorageAdapter

def get_storage_adapter(settings=None):
    settings = settings or StorageSettings.from_env()
    return S3StorageAdapter(settings)
