"""FININT OMEGA — Persistence layer."""

from core.persistence.base import (
    BaseRepository,
    DatabaseManager,
    RepositoryConfig,
)
from core.persistence.db import (
    get_pool,
    init_db,
    close_db,
    is_pg_available,
)

__all__ = [
    "BaseRepository",
    "DatabaseManager",
    "RepositoryConfig",
    "get_pool",
    "init_db",
    "close_db",
    "is_pg_available",
]
