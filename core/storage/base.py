"""FININT OMEGA — Object storage abstraction for documents and raw data."""

from __future__ import annotations

import hashlib
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

import structlog

logger = structlog.get_logger()


@dataclass
class StorageConfig:
    """Configuration for object storage."""
    backend: str = "local"  # "local", "s3", "mock"
    local_path: str = "./data/storage"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint: str | None = None  # For MinIO or other S3-compatible
    s3_access_key: str = ""
    s3_secret_key: str = ""


@dataclass
class StorageObject:
    """Metadata for a stored object."""
    key: str
    bucket: str
    size_bytes: int
    content_type: str
    content_hash: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "bucket": self.bucket,
            "size_bytes": self.size_bytes,
            "content_type": self.content_type,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class ObjectStorage(ABC):
    """Abstract base class for object storage."""

    @abstractmethod
    def put(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> StorageObject:
        """Store an object."""
        ...

    @abstractmethod
    def get(self, key: str) -> tuple[bytes, StorageObject] | None:
        """Retrieve an object."""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an object."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if an object exists."""
        ...

    @abstractmethod
    def list(self, prefix: str = "", limit: int = 100) -> list[StorageObject]:
        """List objects with a given prefix."""
        ...

    @abstractmethod
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for the object."""
        ...


class LocalObjectStorage(ObjectStorage):
    """Local filesystem object storage for development."""

    def __init__(self, config: StorageConfig) -> None:
        self._base_path = Path(config.local_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def put(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> StorageObject:
        file_path = self._base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, bytes):
            content = data
        else:
            content = data.read()

        file_path.write_bytes(content)
        content_hash = hashlib.sha256(content).hexdigest()

        stat = file_path.stat()
        obj = StorageObject(
            key=key,
            bucket="local",
            size_bytes=stat.st_size,
            content_type=content_type,
            content_hash=content_hash,
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            metadata=metadata or {},
        )
        logger.info("object_stored", key=key, size=stat.st_size)
        return obj

    def get(self, key: str) -> tuple[bytes, StorageObject] | None:
        file_path = self._base_path / key
        if not file_path.exists():
            return None

        content = file_path.read_bytes()
        stat = file_path.stat()
        obj = StorageObject(
            key=key,
            bucket="local",
            size_bytes=stat.st_size,
            content_type="application/octet-stream",
            content_hash=hashlib.sha256(content).hexdigest(),
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )
        return content, obj

    def delete(self, key: str) -> bool:
        file_path = self._base_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        return (self._base_path / key).exists()

    def list(self, prefix: str = "", limit: int = 100) -> list[StorageObject]:
        results = []
        prefix_path = self._base_path / prefix if prefix else self._base_path
        for file_path in prefix_path.rglob("*"):
            if file_path.is_file() and len(results) < limit:
                rel_path = file_path.relative_to(self._base_path)
                stat = file_path.stat()
                results.append(StorageObject(
                    key=str(rel_path),
                    bucket="local",
                    size_bytes=stat.st_size,
                    content_type="application/octet-stream",
                    content_hash="",
                    created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                ))
        return results

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"file://{self._base_path / key}"


class MockObjectStorage(ObjectStorage):
    """In-memory mock object storage for testing."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[bytes, StorageObject]] = {}

    def put(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> StorageObject:
        content = data if isinstance(data, bytes) else data.read()
        content_hash = hashlib.sha256(content).hexdigest()
        obj = StorageObject(
            key=key,
            bucket="mock",
            size_bytes=len(content),
            content_type=content_type,
            content_hash=content_hash,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        self._store[key] = (content, obj)
        return obj

    def get(self, key: str) -> tuple[bytes, StorageObject] | None:
        return self._store.get(key)

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        return key in self._store

    def list(self, prefix: str = "", limit: int = 100) -> list[StorageObject]:
        results = []
        for k, (_, obj) in self._store.items():
            if k.startswith(prefix) and len(results) < limit:
                results.append(obj)
        return results

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"mock://{key}"


def get_storage(config: StorageConfig | None = None) -> ObjectStorage:
    """Get the appropriate storage backend."""
    config = config or StorageConfig()

    if config.backend == "local":
        return LocalObjectStorage(config)
    elif config.backend == "mock":
        return MockObjectStorage()
    else:
        logger.warning("storage_fallback_mock", backend=config.backend)
        return MockObjectStorage()
