"""FININT OMEGA — Data ingestion pipeline: providers → ClickHouse."""

from __future__ import annotations

import time

import structlog

from core.data.connectors.base import DataRecord
from core.data.connectors.manager import DataProviderManager

# Import connectors to trigger self-registration
import core.data.connectors.yfinance_connector  # noqa: F401
import core.data.connectors.fred_connector  # noqa: F401
import core.data.connectors.sec_edgar_connector  # noqa: F401

from core.persistence.clickhouse_writer import ClickHouseWriter

logger = structlog.get_logger()


class DataIngestionPipeline:
    """End-to-end pipeline: fetch from providers → validate → normalize → ClickHouse."""

    def __init__(self) -> None:
        self.manager = DataProviderManager()
        self.writer = ClickHouseWriter()

    def ingest_market(
        self, symbols: list[str], period: str = "5d", interval: str = "1d"
    ) -> dict:
        """Ingest market OHLCV data for given symbols."""
        stats = {"symbols": len(symbols), "records_written": 0, "errors": []}
        all_records = []

        for symbol in symbols:
            try:
                records = self.manager.fetch_market(symbol, period=period, interval=interval)
                for rec in records:
                    d = rec.data
                    all_records.append({
                        "symbol": d.get("symbol", symbol),
                        "date": d.get("date", ""),
                        "exchange": d.get("exchange", "OTHER"),
                        "currency": d.get("currency", "USD"),
                        "open": d.get("open", 0),
                        "high": d.get("high", 0),
                        "low": d.get("low", 0),
                        "close": d.get("close", 0),
                        "adjusted_close": d.get("adjusted_close", 0),
                        "volume": d.get("volume", 0),
                        "turnover": d.get("turnover", 0),
                    })
                logger.info("ingest_market_fetch", symbol=symbol, records=len(records))
            except Exception as e:
                stats["errors"].append({"symbol": symbol, "error": str(e)})
                logger.error("ingest_market_fetch_failed", symbol=symbol, error=str(e))

        if all_records:
            written = self.writer.write_market_daily(all_records)
            stats["records_written"] = written

        return stats

    def ingest_companies(self, symbols: list[str]) -> dict:
        """Ingest company identifier data."""
        stats = {"symbols": len(symbols), "records_written": 0, "errors": []}
        all_records = []

        for symbol in symbols:
            try:
                records = self.manager.fetch_fundamentals(symbol)
                for rec in records:
                    d = rec.data
                    all_records.append({
                        "symbol": symbol,
                        "name": d.get("shortName", d.get("longName", symbol)),
                        "exchange": d.get("exchange", "OTHER"),
                        "currency": d.get("currency", "USD"),
                        "sector": d.get("sector", ""),
                        "industry": d.get("industry", ""),
                        "country": d.get("country", ""),
                    })
                logger.info("ingest_companies_fetch", symbol=symbol, records=len(records))
            except Exception as e:
                stats["errors"].append({"symbol": symbol, "error": str(e)})
                logger.error("ingest_companies_fetch_failed", symbol=symbol, error=str(e))

        if all_records:
            written = self.writer.write_companies(all_records)
            stats["records_written"] = written

        return stats

    def ingest_macro(self, series_ids: list[str]) -> dict:
        """Ingest macro economic indicator data."""
        stats = {"series": len(series_ids), "records_written": 0, "errors": []}
        all_records = []

        for series_id in series_ids:
            try:
                records = self.manager.fetch_macro(series_id)
                for rec in records:
                    d = rec.data
                    all_records.append({
                        "indicator_id": series_id,
                        "indicator_name": d.get("title", series_id),
                        "country": d.get("country", "US"),
                        "date": d.get("date", ""),
                        "value": d.get("value", 0),
                        "unit": d.get("units", ""),
                        "source": "FRED",
                        "frequency": d.get("frequency", "monthly"),
                    })
                logger.info("ingest_macro_fetch", series_id=series_id, records=len(records))
            except Exception as e:
                stats["errors"].append({"series_id": series_id, "error": str(e)})
                logger.error("ingest_macro_fetch_failed", series_id=series_id, error=str(e))

        if all_records:
            written = self.writer.write_macro_indicators(all_records)
            stats["records_written"] = written

        return stats

    def ingest_full(self, symbols: list[str] | None = None) -> dict:
        """Run full ingestion: market + companies + macro."""
        if symbols is None:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

        start = time.monotonic()
        results = {
            "market": self.ingest_market(symbols),
            "companies": self.ingest_companies(symbols),
            "macro": self.ingest_macro(["GDP", "UNRATE", "CPIAUCSL"]),
            "duration_s": 0,
        }
        results["duration_s"] = round(time.monotonic() - start, 2)
        total_written = sum(
            r.get("records_written", 0) for r in results.values() if isinstance(r, dict)
        )
        results["total_written"] = total_written
        logger.info("ingest_full_complete", total_written=total_written, duration_s=results["duration_s"])
        return results

    def close(self) -> None:
        self.writer.close()
