"""FININT OMEGA — Thesis repository for persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from core.persistence.base import BaseRepository, RepositoryConfig

logger = structlog.get_logger()


class ThesisRepository(BaseRepository):
    """Repository for persisting investment theses.

    Supports both PostgreSQL (production) and in-memory (development).
    """

    def __init__(self, config: RepositoryConfig | None = None) -> None:
        super().__init__(config)
        self._store: dict[str, dict] = {}
        self._versions: dict[str, list[dict]] = {}
        self._pool = None

    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool if configured."""
        if not self._config.use_mock and self._config.postgres_dsn:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(self._config.postgres_dsn)
                logger.info("thesis_repo_connected")
            except Exception as e:
                logger.warning("thesis_repo_fallback_mock", error=str(e))
                self._pool = None

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()

    async def save(self, thesis: dict) -> dict:
        """Save a thesis (create or update)."""
        thesis_id = thesis.get("thesis_id", str(uuid.uuid4()))
        now = datetime.now(timezone.utc)

        record = {
            "thesis_id": thesis_id,
            "symbol": thesis.get("symbol", ""),
            "title": thesis.get("title", ""),
            "thesis_text": thesis.get("thesis_text", ""),
            "status": thesis.get("status", "active"),
            "confidence": thesis.get("confidence", 0.5),
            "created_at": thesis.get("created_at", now.isoformat()),
            "updated_at": now.isoformat(),
            "user_id": thesis.get("user_id"),
            "metadata": thesis.get("metadata", {}),
        }

        if self._pool:
            # PostgreSQL persistence
            await self._pool.execute(
                """
                INSERT INTO theses (thesis_id, user_id, symbol, title, thesis_text, status, confidence, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (thesis_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    thesis_text = EXCLUDED.thesis_text,
                    status = EXCLUDED.status,
                    confidence = EXCLUDED.confidence,
                    updated_at = NOW(),
                    metadata = EXCLUDED.metadata
                """,
                uuid.UUID(thesis_id),
                uuid.UUID(record["user_id"]) if record["user_id"] else None,
                record["symbol"],
                record["title"],
                record["thesis_text"],
                record["status"],
                record["confidence"],
                str(record["metadata"]),
            )
        else:
            # In-memory fallback
            self._store[thesis_id] = record

        logger.info("thesis_saved", thesis_id=thesis_id, symbol=record["symbol"])
        return record

    async def get(self, thesis_id: str) -> dict | None:
        """Get a thesis by ID."""
        if self._pool:
            row = await self._pool.fetchrow(
                "SELECT * FROM theses WHERE thesis_id = $1",
                uuid.UUID(thesis_id),
            )
            if row:
                return dict(row)
            return None

        return self._store.get(thesis_id)

    async def list_by_user(self, user_id: str, status: str | None = None) -> list[dict]:
        """List theses for a user."""
        if self._pool:
            query = "SELECT * FROM theses WHERE user_id = $1"
            params: list[Any] = [uuid.UUID(user_id)]
            if status:
                query += " AND status = $2"
                params.append(status)
            query += " ORDER BY created_at DESC"
            rows = await self._pool.fetch(query, *params)
            return [dict(r) for r in rows]

        results = [t for t in self._store.values() if t.get("user_id") == user_id]
        if status:
            results = [t for t in results if t.get("status") == status]
        return sorted(results, key=lambda t: t.get("created_at", ""), reverse=True)

    async def update_status(self, thesis_id: str, status: str) -> bool:
        """Update thesis status."""
        if self._pool:
            result = await self._pool.execute(
                "UPDATE theses SET status = $1, updated_at = NOW() WHERE thesis_id = $2",
                status,
                uuid.UUID(thesis_id),
            )
            return result == "UPDATE 1"

        if thesis_id in self._store:
            self._store[thesis_id]["status"] = status
            self._store[thesis_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            return True
        return False

    async def delete(self, thesis_id: str) -> bool:
        """Delete a thesis."""
        if self._pool:
            result = await self._pool.execute(
                "DELETE FROM theses WHERE thesis_id = $1",
                uuid.UUID(thesis_id),
            )
            return result == "DELETE 1"

        if thesis_id in self._store:
            del self._store[thesis_id]
            return True
        return False

    async def save_version(self, thesis_id: str, version: dict) -> dict:
        """Save a thesis version."""
        version_id = str(uuid.uuid4())
        version["version_id"] = version_id
        version["thesis_id"] = thesis_id

        if self._pool:
            await self._pool.execute(
                """
                INSERT INTO thesis_versions (version_id, thesis_id, version_number, thesis_text, confidence, change_reason, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                uuid.UUID(version_id),
                uuid.UUID(thesis_id),
                version.get("version_number", 1),
                version.get("thesis_text", ""),
                version.get("confidence"),
                version.get("change_reason", ""),
                uuid.UUID(version["created_by"]) if version.get("created_by") else None,
            )
        else:
            if thesis_id not in self._versions:
                self._versions[thesis_id] = []
            self._versions[thesis_id].append(version)

        return version

    async def get_versions(self, thesis_id: str) -> list[dict]:
        """Get all versions of a thesis."""
        if self._pool:
            rows = await self._pool.fetch(
                "SELECT * FROM thesis_versions WHERE thesis_id = $1 ORDER BY version_number",
                uuid.UUID(thesis_id),
            )
            return [dict(r) for r in rows]

        return self._versions.get(thesis_id, [])
