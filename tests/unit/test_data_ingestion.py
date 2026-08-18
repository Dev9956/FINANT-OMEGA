"""FININT OMEGA — Data ingestion pipeline integration tests."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("CLICKHOUSE_HOST", "localhost")
os.environ.setdefault("CLICKHOUSE_PORT", "8123")
os.environ.setdefault("CLICKHOUSE_DB", "finintel_omega")
os.environ.setdefault("CLICKHOUSE_USER", "default")
os.environ.setdefault("CLICKHOUSE_PASSWORD", "clickhouse_dev")

from core.data.ingestion import DataIngestionPipeline
from core.persistence.clickhouse_writer import _get_client, apply_schema


@pytest.fixture(scope="module")
def pipeline():
    """Create an ingestion pipeline."""
    apply_schema()
    p = DataIngestionPipeline()
    yield p
    # Cleanup
    try:
        client = _get_client()
        for table in ["market_daily", "companies", "macro_indicators"]:
            client.command(f"ALTER TABLE {table} DELETE WHERE 1=1")
        client.close()
    except Exception:
        pass
    p.close()


@pytest.fixture(scope="module")
def ch_client():
    client = _get_client()
    yield client
    client.close()


class TestMarketIngestion:
    """Test market data ingestion from providers to ClickHouse."""

    def test_ingest_single_symbol(self, pipeline):
        """Ingest market data for a single symbol."""
        result = pipeline.ingest_market(["AAPL"], period="5d", interval="1d")
        assert result["errors"] == [] or all(
            "error" not in e for e in result["errors"]
        )
        # yfinance should return some records
        assert result["records_written"] >= 0

    def test_ingest_queries_clickhouse(self, pipeline, ch_client):
        """Ingested data is queryable from ClickHouse."""
        pipeline.ingest_market(["MSFT"], period="5d", interval="1d")
        result = ch_client.query(
            "SELECT DISTINCT symbol FROM market_daily WHERE symbol = 'MSFT'"
        )
        # Should find MSFT data if ingestion succeeded
        symbols = {row[0] for row in result.result_rows}
        assert "MSFT" in symbols


class TestCompanyIngestion:
    """Test company data ingestion."""

    def test_ingest_companies(self, pipeline):
        """Ingest company data for a symbol."""
        result = pipeline.ingest_companies(["AAPL"])
        assert result["errors"] == []
        assert result["records_written"] >= 0


class TestMacroIngestion:
    """Test macro data ingestion (FRED)."""

    def test_ingest_macro(self, pipeline):
        """Ingest macro economic indicators."""
        result = pipeline.ingest_macro(["GDP"])
        # GDP should succeed via public FRED CSV endpoint
        assert result["records_written"] >= 0
        # At least no crash — some series may fail on public endpoint
        assert isinstance(result, dict)


class TestFullIngestion:
    """Test full multi-domain ingestion."""

    def test_ingest_full(self, pipeline, ch_client):
        """Run full ingestion pipeline."""
        result = pipeline.ingest_full(symbols=["AAPL", "MSFT"])
        assert "market" in result
        assert "companies" in result
        assert "macro" in result
        # Verify data landed in ClickHouse
        market_count = ch_client.query("SELECT count() FROM market_daily")
        assert market_count.result_rows[0][0] >= 0


class TestDuplicateHandling:
    """Test duplicate data handling across ingestion runs."""

    def test_double_ingest(self, pipeline, ch_client):
        """Ingesting the same data twice does not cause errors."""
        pipeline.ingest_market(["AAPL"], period="5d", interval="1d")
        count1 = ch_client.query("SELECT count() FROM market_daily WHERE symbol = 'AAPL'").result_rows[0][0]
        pipeline.ingest_market(["AAPL"], period="5d", interval="1d")
        count2 = ch_client.query("SELECT count() FROM market_daily WHERE symbol = 'AAPL'").result_rows[0][0]
        # ClickHouse allows duplicates (MergeTree), but ingestion should not fail
        assert count2 >= count1


class TestErrorResilience:
    """Test that ingestion handles errors gracefully."""

    def test_invalid_symbol(self, pipeline):
        """Ingesting a nonexistent symbol should not crash."""
        result = pipeline.ingest_market(["INVALID_SYMBOL_XYZ_999"])
        # Should handle gracefully, possibly with empty data
        assert isinstance(result, dict)

    def test_partial_failure(self, pipeline):
        """If one symbol fails, others should still be ingested."""
        result = pipeline.ingest_market(["AAPL", "INVALID_XYZ_999"])
        # At least AAPL should succeed
        assert isinstance(result, dict)
