from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

@dataclass(frozen=True)
class UploadTarget:
    url: str
    headers: dict[str, str]
    expires_at: datetime

@dataclass(frozen=True)
class ObjectMetadata:
    key: str
    byte_size: int
    mime_type: str | None
    version: str | None = None
    metadata: dict[str, str] | None = None

class StorageAdapter(ABC):
    @abstractmethod
    def create_upload(self, key: str, mime_type: str, ttl: int) -> UploadTarget: ...
    @abstractmethod
    def head_object(self, key: str) -> ObjectMetadata | None: ...
    @abstractmethod
    def download_to(self, key: str, target: BinaryIO) -> None: ...
    @abstractmethod
    def put_object(self, key: str, source: BinaryIO, mime_type: str, sha256: str) -> ObjectMetadata: ...
    @abstractmethod
    def generate_read_url(self, key: str, ttl: int) -> str: ...
    @abstractmethod
    def delete_object(self, key: str) -> None: ...
