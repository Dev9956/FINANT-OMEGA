"""FININT OMEGA — Object storage abstraction."""

from core.storage.base import (
    ObjectStorage,
    StorageConfig,
    StorageObject,
    get_storage,
)

__all__ = [
    "ObjectStorage",
    "StorageConfig",
    "StorageObject",
    "get_storage",
]
