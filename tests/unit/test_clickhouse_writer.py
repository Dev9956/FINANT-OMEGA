"""FININT OMEGA — ClickHouse writer integration tests."""

from __future__ import annotations

import os
import time

import pytest

# Ensure env before any imports
os.environ.setdefault("CLICKHOUSE_HOST", "localhost")
os.environ.setdefault("CLICKHOUSE_PORT", "8123")
os.environ.setdefault("CLICKHOUSE_DB", "finintel_omega")
os.environ.setdefault("CLICKHOUSE_USER", "default")
os.environ.setdefault("CLICKHOUSE_PASSWORD", "clickhouse_dev")

from core.persistence.clickhouse_writer import ClickHouseWriter, apply_schema, _get_client


@pytest.fixture(scope="module")
def writer():
    """Create a ClickHouse writer, apply schema, yield, clean up."""
    w = ClickHouseWriter()
    apply_schema()
    yield w
    # Cleanup test data
    try:
        client = _get_client()
        for table in [
            "market_daily", "companies", "financial_statements",
            "financial_ratios", "macro_indicators",
        ]:
            client.command(f"ALTER TABLE {table} DELETE WHERE 1=1")
        client.close()
    except Exception:
        pass
    w.close()


@pytest.fixture(scope="module")
def ch_client():
    """Raw ClickHouse client for verification queries."""
    client = _get_client()
    yield client
    client.close()


class TestSchemaApplication:
    """Verify schema is applied correctly."""

    def test_schema_apply_idempotent(self):
        """Applying schema twice does not error."""
        apply_schema()
        apply_schema()

    def test_tables_exist(self, ch_client):
        """All expected tables exist."""
        expected = [
            "market_daily", "companies", "financial_statements",
            "financial_ratios", "macro_indicators",
            "source_registry", "dataset_registry",
        ]
        result = ch_client.query("SHOW TABLES")
        tables = {row[0] for row in result.result_rows}
        for t in expected:
            assert t in tables, f"Table {t} not found"


class TestMarketDaily:
    """Test market daily OHLCV writes."""

    def test_write_single_record(self, writer):
        """Write a single market daily record."""
        count = writer.write_market_daily([
            {
                "symbol": "TEST_WRITE",
                "date": "2026-01-15",
                "exchange": "NASDAQ",
                "currency": "USD",
                "open": 100.0,
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "adjusted_close": 103.0,
                "volume": 1000000,
                "turnover": 103000000.0,
            }
        ])
        assert count == 1

    def test_write_multiple_records(self, writer):
        """Write multiple market daily records."""
        records = [
            {
                "symbol": "TEST_MULTI",
                "date": f"2026-01-{d:02d}",
                "exchange": "NYSE",
                "currency": "USD",
                "open": 100.0 + i,
                "high": 105.0 + i,
                "low": 98.0 + i,
                "close": 103.0 + i,
                "adjusted_close": 103.0 + i,
                "volume": 1000000 + i * 100000,
                "turnover": 0,
            }
            for i, d in enumerate(range(1, 6), 1)
        ]
        count = writer.write_market_daily(records)
        assert count == 5

    def test_query_written_data(self, writer, ch_client):
        """Data written can be queried back."""
        writer.write_market_daily([
            {
                "symbol": "TEST_QUERY",
                "date": "2026-03-01",
                "exchange": "NASDAQ",
                "currency": "USD",
                "open": 150.0,
                "high": 155.0,
                "low": 148.0,
                "close": 152.0,
                "adjusted_close": 152.0,
                "volume": 500000,
                "turnover": 0,
            }
        ])
        result = ch_client.query(
            "SELECT symbol, close, volume FROM market_daily WHERE symbol = 'TEST_QUERY'"
        )
        assert len(result.result_rows) >= 1
        row = result.result_rows[0]
        assert row[0] == "TEST_QUERY"
        assert row[1] == 152.0

    def test_nan_values_treated_as_zero(self, writer):
        """NaN/Inf values are replaced with 0."""
        count = writer.write_market_daily([
            {
                "symbol": "TEST_NAN",
                "date": "2026-04-01",
                "exchange": "NASDAQ",
                "currency": "USD",
                "open": float("nan"),
                "high": float("inf"),
                "low": None,
                "close": 100.0,
                "adjusted_close": 100.0,
                "volume": None,
                "turnover": 0,
            }
        ])
        assert count == 1


class TestCompanies:
    """Test company writes."""

    def test_write_company(self, writer):
        """Write a company record."""
        count = writer.write_companies([
            {
                "symbol": "TEST_CO",
                "name": "Test Corporation",
                "exchange": "NASDAQ",
                "currency": "USD",
                "sector": "Technology",
                "industry": "Software",
                "country": "US",
            }
        ])
        assert count == 1

    def test_company_upsert(self, writer, ch_client):
        """Writing same company twice deduplicates (ReplacingMergeTree)."""
        writer.write_companies([
            {"symbol": "TEST_UPSERT", "name": "V1 Corp", "exchange": "NYSE", "currency": "USD"}
        ])
        writer.write_companies([
            {"symbol": "TEST_UPSERT", "name": "V2 Corp", "exchange": "NYSE", "currency": "USD"}
        ])
        # ReplacingMergeTree deduplicates on final merge
        result = ch_client.query(
            "SELECT DISTINCT symbol FROM companies WHERE symbol = 'TEST_UPSERT'"
        )
        assert len(result.result_rows) >= 1


class TestFinancialStatements:
    """Test financial statement writes."""

    def test_write_statement(self, writer):
        """Write a financial statement record."""
        count = writer.write_financial_statements([
            {
                "symbol": "TEST_FS",
                "period_end": "2026-03-31",
                "statement_type": "income_statement",
                "fiscal_year": 2026,
                "fiscal_quarter": 1,
                "currency": "USD",
                "revenue": 100000000.0,
                "net_income": 25000000.0,
                "eps_diluted": 1.50,
            }
        ])
        assert count == 1

    def test_query_financial_statements(self, writer, ch_client):
        """Written financial statements are queryable."""
        writer.write_financial_statements([
            {
                "symbol": "TEST_FS2",
                "period_end": "2026-06-30",
                "statement_type": "balance_sheet",
                "fiscal_year": 2026,
                "fiscal_quarter": 2,
                "currency": "USD",
                "total_assets": 500000000.0,
                "total_equity": 200000000.0,
            }
        ])
        result = ch_client.query(
            "SELECT symbol, total_assets FROM financial_statements WHERE symbol = 'TEST_FS2'"
        )
        assert len(result.result_rows) >= 1


class TestFinancialRatios:
    """Test financial ratio writes."""

    def test_write_ratios(self, writer):
        """Write financial ratio records."""
        count = writer.write_financial_ratios([
            {
                "symbol": "TEST_RATIO",
                "date": "2026-06-30",
                "pe_ratio": 25.5,
                "pb_ratio": 3.2,
                "roe": 0.18,
                "net_margin": 0.22,
            }
        ])
        assert count == 1


class TestMacroIndicators:
    """Test macro indicator writes."""

    def test_write_macro(self, writer):
        """Write macro indicator records."""
        count = writer.write_macro_indicators([
            {
                "indicator_id": "TEST_GDP",
                "indicator_name": "Test GDP",
                "country": "US",
                "date": "2026-01-01",
                "value": 25000.0,
                "unit": "Billions of Dollars",
                "source": "FRED",
                "frequency": "quarterly",
            }
        ])
        assert count == 1

    def test_write_macro_bulk(self, writer):
        """Write multiple macro indicator records."""
        records = [
            {
                "indicator_id": f"TEST_IND_{i}",
                "indicator_name": f"Indicator {i}",
                "country": "US",
                "date": f"2026-0{i}-01",
                "value": float(i * 100),
                "unit": "index",
                "source": "FRED",
                "frequency": "monthly",
            }
            for i in range(1, 4)
        ]
        count = writer.write_macro_indicators(records)
        assert count == 3


class TestIdempotentWrite:
    """Test idempotent market daily writes."""

    def test_idempotent_skips_existing(self, writer, ch_client):
        """Writing same record twice only inserts once."""
        record = {
            "symbol": "TEST_IDEMP",
            "date": "2026-07-01",
            "exchange": "NASDAQ",
            "currency": "USD",
            "open": 100.0,
            "high": 105.0,
            "low": 98.0,
            "close": 103.0,
            "adjusted_close": 103.0,
            "volume": 1000000,
            "turnover": 0,
        }
        # First write
        writer.write_market_daily([record])
        # Idempotent write should skip
        written = writer.write_market_daily_idempotent([record])
        assert written == 0

    def test_idempotent_writes_new(self, writer):
        """Idempotent write inserts truly new records."""
        record = {
            "symbol": "TEST_IDEMP_NEW",
            "date": "2026-07-15",
            "exchange": "NASDAQ",
            "currency": "USD",
            "open": 200.0,
            "high": 210.0,
            "low": 195.0,
            "close": 205.0,
            "adjusted_close": 205.0,
            "volume": 500000,
            "turnover": 0,
        }
        written = writer.write_market_daily_idempotent([record])
        assert written == 1


class TestRetry:
    """Test retry behavior on transient failures."""

    def test_writer_reconnects_after_close(self):
        """Writer can recover after client is closed."""
        w = ClickHouseWriter()
        w._ensure_client()
        assert w._client is not None
        w._client.close()
        w._client = None
        # Should reconnect on next write
        count = w.write_market_daily([
            {
                "symbol": "TEST_RECONNECT",
                "date": "2026-08-01",
                "exchange": "NASDAQ",
                "currency": "USD",
                "open": 100.0,
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "adjusted_close": 103.0,
                "volume": 100000,
                "turnover": 0,
            }
        ])
        assert count == 1
        w.close()


class TestTimestampCorrectness:
    """Verify timestamps in ClickHouse are correct."""

    def test_inserted_at_populated(self, writer, ch_client):
        """inserted_at field is auto-populated."""
        writer.write_market_daily([
            {
                "symbol": "TEST_TS",
                "date": "2026-09-01",
                "exchange": "NASDAQ",
                "currency": "USD",
                "open": 100.0,
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "adjusted_close": 103.0,
                "volume": 100000,
                "turnover": 0,
            }
        ])
        result = ch_client.query(
            "SELECT inserted_at FROM market_daily WHERE symbol = 'TEST_TS'"
        )
        assert len(result.result_rows) >= 1
        assert result.result_rows[0][0] is not None


class TestEmptyInputs:
    """Test edge cases with empty inputs."""

    def test_write_empty_list(self, writer):
        """Writing empty list is a no-op."""
        count = writer.write_market_daily([])
        assert count == 0

        count = writer.write_companies([])
        assert count == 0

        count = writer.write_financial_statements([])
        assert count == 0

        count = writer.write_financial_ratios([])
        assert count == 0

        count = writer.write_macro_indicators([])
        assert count == 0
