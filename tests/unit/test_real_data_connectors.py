"""Tests for real data connectors — M15.5 Phase 1."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from core.data.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    DataCache,
    DataProvenance,
    DataQuality,
    DataRecord,
    RateLimiter,
)


class TestRateLimiter:
    def test_acquire_within_rate(self):
        limiter = RateLimiter(rate=10.0)
        assert limiter.acquire() is True

    def test_acquire_exhausts_tokens(self):
        limiter = RateLimiter(rate=1.0)
        assert limiter.acquire() is True
        # Second acquire immediately should fail
        assert limiter.acquire() is False


class TestDataCache:
    def test_cache_miss(self):
        cache = DataCache(max_size=100, ttl_seconds=300)
        result = cache.get(symbol="AAPL")
        assert result is None

    def test_cache_hit(self):
        cache = DataCache(max_size=100, ttl_seconds=300)
        records = [DataRecord(data={"price": 100}, provenance=DataProvenance(
            source="test", provider="test", retrieved_at=datetime.now(timezone.utc)
        ))]
        cache.put(records, symbol="AAPL")
        result = cache.get(symbol="AAPL")
        assert result is not None
        assert len(result) == 1
        assert result[0].data["price"] == 100

    def test_cache_eviction(self):
        cache = DataCache(max_size=2, ttl_seconds=300)
        for i in range(3):
            cache.put([DataRecord(data={"i": i}, provenance=DataProvenance(
                source="test", provider="test", retrieved_at=datetime.now(timezone.utc)
            ))], symbol=f"S{i}")
        assert len(cache._cache) == 2


class TestDataProvenance:
    def test_provenance_to_dict(self):
        prov = DataProvenance(
            source="yfinance",
            provider="Yahoo Finance",
            retrieved_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            event_time=datetime(2024, 12, 31, tzinfo=timezone.utc),
            quality=DataQuality.REAL,
        )
        d = prov.to_dict()
        assert d["source"] == "yfinance"
        assert d["quality"] == "real"
        assert d["event_time"] == "2024-12-31T00:00:00+00:00"


class TestDataRecord:
    def test_getitem(self):
        record = DataRecord(
            data={"price": 100, "volume": 1000},
            provenance=DataProvenance(
                source="test", provider="test", retrieved_at=datetime.now(timezone.utc)
            ),
        )
        assert record["price"] == 100
        assert record.get("missing", "default") == "default"


class TestConnectorConfig:
    def test_default_config(self):
        config = ConnectorConfig()
        assert config.timeout_seconds == 30.0
        assert config.max_retries == 3
        assert config.rate_limit_per_second == 10.0

    def test_custom_config(self):
        config = ConnectorConfig(timeout_seconds=60.0, max_retries=5)
        assert config.timeout_seconds == 60.0
        assert config.max_retries == 5


class MockTestConnector(BaseConnector):
    """Test connector that returns controlled data."""

    def __init__(self, config: ConnectorConfig | None = None):
        super().__init__("test_connector", "Test", config)
        self._quality = DataQuality.REAL

    def _fetch_raw(self, **kwargs):
        return [{
            "symbol": kwargs.get("symbol", "TEST"),
            "price": 100.0,
            "volume": 1000,
            "_source": self.source_id,
        }]

    def health_check(self):
        return True


class TestBaseConnector:
    def test_fetch_with_provenance(self):
        connector = MockTestConnector()
        records = connector.fetch(symbol="TEST")
        assert len(records) == 1
        assert records[0].data["symbol"] == "TEST"
        assert records[0].provenance.quality == DataQuality.REAL
        assert records[0].provenance.source == "test_connector"

    def test_disabled_connector(self):
        config = ConnectorConfig(enabled=False)
        connector = MockTestConnector(config)
        records = connector.fetch(symbol="TEST")
        assert len(records) == 0

    def test_connector_stats(self):
        connector = MockTestConnector()
        connector.fetch(symbol="TEST")
        stats = connector.get_stats()
        assert stats["call_count"] == 1
        assert stats["error_count"] == 0


@pytest.mark.skipif(
    not os.environ.get("YFINANCE_TEST"),
    reason="Set YFINANCE_TEST=1 to run real data tests"
)
class TestYFinanceMarketConnector:
    def test_fetch_market_data(self):
        from core.data.connectors.yfinance_connector import YFinanceMarketConnector
        connector = YFinanceMarketConnector()
        records = connector.fetch(symbol="AAPL", period="5d", interval="1d")
        assert len(records) > 0
        assert records[0].data["symbol"] == "AAPL"
        assert "close" in records[0].data
        assert records[0].provenance.quality == DataQuality.REAL

    def test_health_check(self):
        from core.data.connectors.yfinance_connector import YFinanceMarketConnector
        connector = YFinanceMarketConnector()
        assert connector.health_check() is True


@pytest.mark.skipif(
    not os.environ.get("YFINANCE_TEST"),
    reason="Set YFINANCE_TEST=1 to run real data tests"
)
class TestYFinanceFundamentalsConnector:
    def test_fetch_fundamentals(self):
        from core.data.connectors.yfinance_connector import YFinanceFundamentalsConnector
        connector = YFinanceFundamentalsConnector()
        records = connector.fetch(symbol="AAPL")
        assert len(records) > 0
        data_types = [r.data.get("data_type") for r in records]
        assert "info" in data_types


@pytest.mark.skipif(
    not os.environ.get("SECEdgar_TEST"),
    reason="Set SECEDGAR_TEST=1 to run real data tests"
)
class TestSECEdgarConnector:
    def test_fetch_filings(self):
        from core.data.connectors.sec_edgar_connector import SECEdgarCompanyConnector
        connector = SECEdgarCompanyConnector()
        records = connector.fetch(symbol="AAPL")
        assert len(records) > 0
        assert records[0].provenance.quality == DataQuality.REAL


class TestDataProviderManager:
    def test_manager_fetch(self):
        from core.data.connectors.manager import DataProviderManager
        manager = DataProviderManager()
        # Mock connector won't be registered, so this will raise
        with pytest.raises(ValueError):
            manager.fetch("nonexistent", symbol="TEST")
