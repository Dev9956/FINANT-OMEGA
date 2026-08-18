"""FININT OMEGA — Base persistence infrastructure."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class RepositoryConfig:
    """Configuration for database repositories."""
    postgres_dsn: str = ""
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_db: str = "finintel_omega"
    use_mock: bool = True  # Use in-memory mock when no real DB available


class BaseRepository(ABC):
    """Abstract base class for repositories."""

    def __init__(self, config: RepositoryConfig | None = None) -> None:
        self._config = config or RepositoryConfig()
        self._mock_store: dict[str, list[dict]] = {}

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository (create tables, connections, etc.)."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the repository connections."""
        ...


class DatabaseManager:
    """Manages database connections and repositories."""

    def __init__(self, config: RepositoryConfig | None = None) -> None:
        self._config = config or RepositoryConfig(
            postgres_dsn=os.environ.get("DATABASE_URL", "postgresql://localhost/finintel_omega"),
            clickhouse_host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
            clickhouse_port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
            clickhouse_db=os.environ.get("CLICKHOUSE_DB", "finintel_omega"),
        )
        self._repositories: dict[str, BaseRepository] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all repositories."""
        if self._initialized:
            return

        for name, repo in self._repositories.items():
            try:
                await repo.initialize()
                logger.info("repository_initialized", name=name)
            except Exception as e:
                logger.error("repository_init_failed", name=name, error=str(e))

        self._initialized = True

    async def close(self) -> None:
        """Close all repository connections."""
        for name, repo in self._repositories.items():
            try:
                await repo.close()
            except Exception as e:
                logger.error("repository_close_failed", name=name, error=str(e))

    def register(self, name: str, repository: BaseRepository) -> None:
        """Register a repository."""
        self._repositories[name] = repository

    def get(self, name: str) -> BaseRepository:
        """Get a repository by name."""
        if name not in self._repositories:
            raise ValueError(f"Repository '{name}' not registered")
        return self._repositories[name]

    @property
    def config(self) -> RepositoryConfig:
        return self._config


# Singleton
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
