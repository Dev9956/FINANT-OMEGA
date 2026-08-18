"""Tests for persistence layer — M15.5 Phase 4."""

from __future__ import annotations

import pytest

from core.persistence.base import DatabaseManager, RepositoryConfig
from core.persistence.thesis_repository import ThesisRepository


@pytest.fixture
def repo_config():
    return RepositoryConfig(use_mock=True)


@pytest.fixture
def thesis_repo(repo_config):
    return ThesisRepository(config=repo_config)


class TestRepositoryConfig:
    def test_default_config(self):
        config = RepositoryConfig()
        assert config.use_mock is True

    def test_custom_config(self):
        config = RepositoryConfig(
            postgres_dsn="postgresql://localhost/test",
            use_mock=False,
        )
        assert config.postgres_dsn == "postgresql://localhost/test"
        assert config.use_mock is False


class TestDatabaseManager:
    def test_register_and_get(self):
        manager = DatabaseManager()
        repo = ThesisRepository()
        manager.register("thesis", repo)
        retrieved = manager.get("thesis")
        assert retrieved is repo

    def test_get_unknown_repo(self):
        manager = DatabaseManager()
        with pytest.raises(ValueError):
            manager.get("nonexistent")


class TestThesisRepositoryMock:
    @pytest.mark.asyncio
    async def test_save_and_get(self, thesis_repo):
        thesis = {
            "symbol": "AAPL",
            "title": "Apple is undervalued",
            "thesis_text": "Strong fundamentals and growth",
            "confidence": 0.7,
        }
        saved = await thesis_repo.save(thesis)
        assert saved["thesis_id"]
        assert saved["symbol"] == "AAPL"

        retrieved = await thesis_repo.get(saved["thesis_id"])
        assert retrieved is not None
        assert retrieved["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_update_status(self, thesis_repo):
        thesis = await thesis_repo.save({"symbol": "AAPL", "title": "Test"})
        updated = await thesis_repo.update_status(thesis["thesis_id"], "invalidated")
        assert updated is True

        retrieved = await thesis_repo.get(thesis["thesis_id"])
        assert retrieved["status"] == "invalidated"

    @pytest.mark.asyncio
    async def test_delete(self, thesis_repo):
        thesis = await thesis_repo.save({"symbol": "AAPL", "title": "Test"})
        deleted = await thesis_repo.delete(thesis["thesis_id"])
        assert deleted is True

        retrieved = await thesis_repo.get(thesis["thesis_id"])
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_list_by_user(self, thesis_repo):
        await thesis_repo.save({"symbol": "AAPL", "title": "Thesis 1", "user_id": "user1"})
        await thesis_repo.save({"symbol": "GOOGL", "title": "Thesis 2", "user_id": "user1"})
        await thesis_repo.save({"symbol": "MSFT", "title": "Thesis 3", "user_id": "user2"})

        results = await thesis_repo.list_by_user("user1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_by_user_with_status(self, thesis_repo):
        await thesis_repo.save({"symbol": "AAPL", "title": "T1", "user_id": "u1", "status": "active"})
        await thesis_repo.save({"symbol": "GOOGL", "title": "T2", "user_id": "u1", "status": "invalidated"})

        active = await thesis_repo.list_by_user("u1", status="active")
        assert len(active) == 1
        assert active[0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_save_version(self, thesis_repo):
        thesis = await thesis_repo.save({"symbol": "AAPL", "title": "Test"})
        version = await thesis_repo.save_version(
            thesis["thesis_id"],
            {"thesis_text": "Updated thesis", "version_number": 1, "created_by": "user1"},
        )
        assert version["version_id"]

        versions = await thesis_repo.get_versions(thesis["thesis_id"])
        assert len(versions) == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, thesis_repo):
        result = await thesis_repo.get("nonexistent-id")
        assert result is None


class TestDatabaseManagerInit:
    @pytest.mark.asyncio
    async def test_initialize(self):
        manager = DatabaseManager()
        await manager.initialize()
        assert manager._initialized is True

    @pytest.mark.asyncio
    async def test_close(self):
        manager = DatabaseManager()
        await manager.close()
