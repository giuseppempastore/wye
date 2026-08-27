import os
from dataclasses import dataclass

def _positive(name, default):
    value=int(os.getenv(name, default))
    if value <= 0: raise RuntimeError(f"{name} must be positive")
    return value

@dataclass(frozen=True)
class StorageSettings:
    provider: str; endpoint: str | None; bucket: str; region: str; access_key: str; secret_key: str
    force_path_style: bool; upload_ttl: int; read_ttl: int; max_image_bytes: int; cleanup_after: int
    @classmethod
    def from_env(cls):
        provider=os.getenv("WYE_STORAGE_PROVIDER","").lower()
        if provider not in {"r2","minio","s3"}: raise RuntimeError("WYE_STORAGE_PROVIDER must be r2, minio, or s3")
        required={n:os.getenv(n,"") for n in ("WYE_STORAGE_BUCKET","WYE_STORAGE_ACCESS_KEY","WYE_STORAGE_SECRET_KEY")}
        if not all(required.values()): raise RuntimeError("Object storage configuration is incomplete")
        return cls(provider,os.getenv("WYE_STORAGE_ENDPOINT") or None,required["WYE_STORAGE_BUCKET"],os.getenv("WYE_STORAGE_REGION") or ("auto" if provider=="r2" else "us-east-1"),required["WYE_STORAGE_ACCESS_KEY"],required["WYE_STORAGE_SECRET_KEY"],os.getenv("WYE_STORAGE_FORCE_PATH_STYLE","false").lower() in {"1","true","yes"},_positive("WYE_STORAGE_UPLOAD_TTL_SECONDS",900),_positive("WYE_STORAGE_READ_TTL_SECONDS",300),_positive("WYE_STORAGE_MAX_IMAGE_BYTES",15728640),_positive("WYE_STORAGE_CLEANUP_AFTER_SECONDS",1800))
