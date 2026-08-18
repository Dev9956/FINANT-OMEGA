"""FININT OMEGA — M0 unit tests for configuration."""

import os

import pytest

from apps.api.config import Settings, get_settings


class TestSettings:
    """Tests for typed configuration."""

    def test_default_values(self):
        """Settings should have sensible defaults."""
        settings = Settings()
        assert settings.app_env == "development"
        assert settings.postgres_host == "localhost"
        assert settings.postgres_port == 5432
        assert settings.postgres_db == "finintel_omega"
        assert settings.clickhouse_port == 8123
        assert settings.redis_port == 6379
        assert settings.api_port == 8000

    def test_postgres_dsn(self):
        """Postgres DSN should be correctly constructed."""
        settings = Settings()
        dsn = settings.postgres_dsn
        assert "postgresql://" in dsn
        assert "finintel" in dsn
        assert "5432" in dsn

    def test_postgres_dsn_async(self):
        """Async Postgres DSN should use asyncpg driver."""
        settings = Settings()
        dsn = settings.postgres_dsn_async
        assert "postgresql+asyncpg://" in dsn

    def test_redis_url(self):
        """Redis URL should be correctly constructed."""
        settings = Settings()
        url = settings.redis_url
        assert url.startswith("redis://")
        assert "6379" in url

    def test_redis_url_with_password(self):
        """Redis URL with password should include auth."""
        settings = Settings(redis_password="secret")
        url = settings.redis_url
        assert ":secret@" in url

    def test_clickhouse_url(self):
        """ClickHouse URL should be correctly constructed."""
        settings = Settings()
        url = settings.clickhouse_url
        assert url.startswith("http://")
        assert "8123" in url

    def test_env_validation_rejects_invalid(self):
        """Invalid APP_ENV should raise ValueError."""
        with pytest.raises(ValueError, match="APP_ENV must be one of"):
            Settings(app_env="invalid")

    def test_env_validation_accepts_valid(self):
        """Valid APP_ENV values should be accepted."""
        for env in ("development", "staging", "production", "testing"):
            settings = Settings(app_env=env)
            assert settings.app_env == env

    def test_settings_from_env(self, monkeypatch):
        """Settings should read from environment variables."""
        monkeypatch.setenv("POSTGRES_HOST", "remote-db.example.com")
        monkeypatch.setenv("POSTGRES_PORT", "5433")
        settings = Settings()
        assert settings.postgres_host == "remote-db.example.com"
        assert settings.postgres_port == 5433

    def test_get_settings_cached(self):
        """get_settings should return the same instance (lru_cache)."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
