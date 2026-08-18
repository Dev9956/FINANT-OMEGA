"""FININT OMEGA — ClickHouse writer for analytical data storage."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()

_SCHEMAS_APPLIED = False


def _get_client():
    """Create a ClickHouse client using clickhouse-connect."""
    import clickhouse_connect
    import os

    return clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
        port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
        database=os.environ.get("CLICKHOUSE_DB", "finintel_omega"),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
    )


def apply_schema() -> None:
    """Apply the ClickHouse market schema (idempotent)."""
    global _SCHEMAS_APPLIED
    if _SCHEMAS_APPLIED:
        return

    client = _get_client()
    schema_sql = """
    CREATE TABLE IF NOT EXISTS market_daily (
        symbol String,
        date Date,
        exchange String,
        currency String,
        open Float64,
        high Float64,
        low Float64,
        close Float64,
        adjusted_close Float64,
        volume UInt64,
        turnover Float64,
        data_version UInt32 DEFAULT 1,
        inserted_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    PARTITION BY toYYYYMM(date)
    ORDER BY (symbol, date);

    CREATE TABLE IF NOT EXISTS companies (
        symbol String,
        name String,
        exchange String,
        currency String,
        isin String DEFAULT '',
        sector String DEFAULT '',
        industry String DEFAULT '',
        country String DEFAULT '',
        is_active UInt8 DEFAULT 1,
        created_at DateTime DEFAULT now(),
        updated_at DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree(updated_at)
    ORDER BY (symbol, exchange);

    CREATE TABLE IF NOT EXISTS financial_statements (
        symbol String,
        period_end Date,
        statement_type String,
        fiscal_year UInt32,
        fiscal_quarter UInt32,
        currency String,
        revenue Float64 DEFAULT 0,
        cost_of_goods_sold Float64 DEFAULT 0,
        gross_profit Float64 DEFAULT 0,
        operating_expenses Float64 DEFAULT 0,
        ebitda Float64 DEFAULT 0,
        ebit Float64 DEFAULT 0,
        interest_expense Float64 DEFAULT 0,
        net_income Float64 DEFAULT 0,
        eps_diluted Float64 DEFAULT 0,
        eps_basic Float64 DEFAULT 0,
        shares_outstanding Float64 DEFAULT 0,
        total_assets Float64 DEFAULT 0,
        total_liabilities Float64 DEFAULT 0,
        total_equity Float64 DEFAULT 0,
        total_debt Float64 DEFAULT 0,
        cash_and_equivalents Float64 DEFAULT 0,
        operating_cash_flow Float64 DEFAULT 0,
        capital_expenditures Float64 DEFAULT 0,
        free_cash_flow Float64 DEFAULT 0,
        data_version UInt32 DEFAULT 1,
        inserted_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    PARTITION BY (statement_type, toYYYYMM(period_end))
    ORDER BY (symbol, period_end, statement_type);

    CREATE TABLE IF NOT EXISTS financial_ratios (
        symbol String,
        date Date,
        pe_ratio Float64 DEFAULT 0,
        pb_ratio Float64 DEFAULT 0,
        ev_ebitda Float64 DEFAULT 0,
        ev_sales Float64 DEFAULT 0,
        roe Float64 DEFAULT 0,
        roce Float64 DEFAULT 0,
        roa Float64 DEFAULT 0,
        gross_margin Float64 DEFAULT 0,
        operating_margin Float64 DEFAULT 0,
        net_margin Float64 DEFAULT 0,
        debt_equity Float64 DEFAULT 0,
        current_ratio Float64 DEFAULT 0,
        quick_ratio Float64 DEFAULT 0,
        revenue_growth_yoy Float64 DEFAULT 0,
        earnings_growth_yoy Float64 DEFAULT 0,
        fcf_yield Float64 DEFAULT 0,
        dividend_yield Float64 DEFAULT 0,
        inserted_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    PARTITION BY toYYYYMM(date)
    ORDER BY (symbol, date);

    CREATE TABLE IF NOT EXISTS macro_indicators (
        indicator_id String,
        indicator_name String,
        country String,
        date Date,
        value Float64,
        unit String,
        source String,
        frequency String,
        inserted_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    PARTITION BY toYYYYMM(date)
    ORDER BY (indicator_id, country, date);

    CREATE TABLE IF NOT EXISTS source_registry (
        source_id String,
        source_name String,
        source_type String,
        provider String,
        license String,
        refresh_frequency String,
        coverage String,
        status String,
        created_at DateTime DEFAULT now(),
        updated_at DateTime DEFAULT now(),
        metadata String DEFAULT '{}'
    ) ENGINE = MergeTree()
    ORDER BY source_id;

    CREATE TABLE IF NOT EXISTS dataset_registry (
        dataset_id String,
        source_id String,
        name String,
        description String,
        stage String,
        schema_version UInt32,
        data_version UInt32,
        coverage_start Date,
        coverage_end Date,
        row_count UInt64,
        quality_status String,
        timezone String,
        currency String,
        created_at DateTime DEFAULT now(),
        updated_at DateTime DEFAULT now(),
        metadata String DEFAULT '{}'
    ) ENGINE = MergeTree()
    ORDER BY (dataset_id, source_id);
    """
    for statement in schema_sql.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            client.command(stmt)
    client.close()
    _SCHEMAS_APPLIED = True
    logger.info("clickhouse_schema_applied")


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        f = float(val)
        if f != f:  # NaN check
            return default
        return f
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


_CH_MIN_DATE = date(1970, 1, 1)
_CH_MAX_DATE = date(2149, 6, 4)


def _safe_date(val: Any) -> date:
    d = _parse_date(val)
    if d < _CH_MIN_DATE:
        return _CH_MIN_DATE
    if d > _CH_MAX_DATE:
        return _CH_MAX_DATE
    return d


def _parse_date(val: Any) -> date:
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        val = val.strip()
        try:
            return date.fromisoformat(val[:10])
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val[:10], fmt).date()
            except ValueError:
                continue
    return date.today()


class ClickHouseWriter:
    """Writer for persisting financial data to ClickHouse analytics tables."""

    def __init__(self) -> None:
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            self._client = _get_client()
            apply_schema()
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    # ---- Market Daily ----

    def write_market_daily(self, records: list[dict]) -> int:
        """Write daily OHLCV market records. Returns count written."""
        client = self._ensure_client()
        if not records:
            return 0

        rows = []
        for r in records:
            rows.append([
                str(r.get("symbol", "")),
                _safe_date(r.get("date")),
                str(r.get("exchange", "")),
                str(r.get("currency", "")),
                _safe_float(r.get("open")),
                _safe_float(r.get("high")),
                _safe_float(r.get("low")),
                _safe_float(r.get("close")),
                _safe_float(r.get("adjusted_close")),
                _safe_int(r.get("volume")),
                _safe_float(r.get("turnover")),
                _safe_int(r.get("data_version", 1)),
            ])

        client.insert(
            "market_daily",
            rows,
            column_names=[
                "symbol", "date", "exchange", "currency",
                "open", "high", "low", "close", "adjusted_close",
                "volume", "turnover", "data_version",
            ],
        )
        logger.info("clickhouse_market_daily_written", count=len(rows))
        return len(rows)

    # ---- Companies ----

    def write_companies(self, records: list[dict]) -> int:
        """Write company records (upsert via ReplacingMergeTree)."""
        client = self._ensure_client()
        if not records:
            return 0

        rows = []
        for r in records:
            rows.append([
                str(r.get("symbol", "")),
                str(r.get("name", "")),
                str(r.get("exchange", "")),
                str(r.get("currency", "")),
                str(r.get("isin", "")),
                str(r.get("sector", "")),
                str(r.get("industry", "")),
                str(r.get("country", "")),
                1,  # is_active
            ])

        client.insert(
            "companies",
            rows,
            column_names=[
                "symbol", "name", "exchange", "currency",
                "isin", "sector", "industry", "country", "is_active",
            ],
        )
        logger.info("clickhouse_companies_written", count=len(rows))
        return len(rows)

    # ---- Financial Statements ----

    def write_financial_statements(self, records: list[dict]) -> int:
        """Write financial statement records."""
        client = self._ensure_client()
        if not records:
            return 0

        rows = []
        for r in records:
            rows.append([
                str(r.get("symbol", "")),
                _safe_date(r.get("period_end")),
                str(r.get("statement_type", "")),
                _safe_int(r.get("fiscal_year")),
                _safe_int(r.get("fiscal_quarter")),
                str(r.get("currency", "USD")),
                _safe_float(r.get("revenue")),
                _safe_float(r.get("cost_of_goods_sold")),
                _safe_float(r.get("gross_profit")),
                _safe_float(r.get("operating_expenses")),
                _safe_float(r.get("ebitda")),
                _safe_float(r.get("ebit")),
                _safe_float(r.get("interest_expense")),
                _safe_float(r.get("net_income")),
                _safe_float(r.get("eps_diluted")),
                _safe_float(r.get("eps_basic")),
                _safe_float(r.get("shares_outstanding")),
                _safe_float(r.get("total_assets")),
                _safe_float(r.get("total_liabilities")),
                _safe_float(r.get("total_equity")),
                _safe_float(r.get("total_debt")),
                _safe_float(r.get("cash_and_equivalents")),
                _safe_float(r.get("operating_cash_flow")),
                _safe_float(r.get("capital_expenditures")),
                _safe_float(r.get("free_cash_flow")),
            ])

        client.insert(
            "financial_statements",
            rows,
            column_names=[
                "symbol", "period_end", "statement_type",
                "fiscal_year", "fiscal_quarter", "currency",
                "revenue", "cost_of_goods_sold", "gross_profit",
                "operating_expenses", "ebitda", "ebit",
                "interest_expense", "net_income", "eps_diluted",
                "eps_basic", "shares_outstanding",
                "total_assets", "total_liabilities", "total_equity",
                "total_debt", "cash_and_equivalents",
                "operating_cash_flow", "capital_expenditures",
                "free_cash_flow",
            ],
        )
        logger.info("clickhouse_financial_statements_written", count=len(rows))
        return len(rows)

    # ---- Financial Ratios ----

    def write_financial_ratios(self, records: list[dict]) -> int:
        """Write financial ratio records."""
        client = self._ensure_client()
        if not records:
            return 0

        rows = []
        for r in records:
            rows.append([
                str(r.get("symbol", "")),
                _safe_date(r.get("date")),
                _safe_float(r.get("pe_ratio")),
                _safe_float(r.get("pb_ratio")),
                _safe_float(r.get("ev_ebitda")),
                _safe_float(r.get("ev_sales")),
                _safe_float(r.get("roe")),
                _safe_float(r.get("roce")),
                _safe_float(r.get("roa")),
                _safe_float(r.get("gross_margin")),
                _safe_float(r.get("operating_margin")),
                _safe_float(r.get("net_margin")),
                _safe_float(r.get("debt_equity")),
                _safe_float(r.get("current_ratio")),
                _safe_float(r.get("quick_ratio")),
                _safe_float(r.get("revenue_growth_yoy")),
                _safe_float(r.get("earnings_growth_yoy")),
                _safe_float(r.get("fcf_yield")),
                _safe_float(r.get("dividend_yield")),
            ])

        client.insert(
            "financial_ratios",
            rows,
            column_names=[
                "symbol", "date",
                "pe_ratio", "pb_ratio", "ev_ebitda", "ev_sales",
                "roe", "roce", "roa",
                "gross_margin", "operating_margin", "net_margin",
                "debt_equity", "current_ratio", "quick_ratio",
                "revenue_growth_yoy", "earnings_growth_yoy",
                "fcf_yield", "dividend_yield",
            ],
        )
        logger.info("clickhouse_financial_ratios_written", count=len(rows))
        return len(rows)

    # ---- Macro Indicators ----

    def write_macro_indicators(self, records: list[dict]) -> int:
        """Write macro economic indicator records (batched by month to avoid partition explosion)."""
        client = self._ensure_client()
        if not records:
            return 0

        # Group by year-month to avoid exceeding max_partitions_per_insert_block
        batches: dict[str, list] = {}
        for r in records:
            d = _safe_date(r.get("date"))
            key = f"{d.year}-{d.month:02d}"
            if key not in batches:
                batches[key] = []
            batches[key].append([
                str(r.get("indicator_id", "")),
                str(r.get("indicator_name", "")),
                str(r.get("country", "")),
                d,
                _safe_float(r.get("value")),
                str(r.get("unit", "")),
                str(r.get("source", "")),
                str(r.get("frequency", "")),
            ])

        col_names = [
            "indicator_id", "indicator_name", "country", "date",
            "value", "unit", "source", "frequency",
        ]
        total = 0
        for batch_rows in batches.values():
            client.insert("macro_indicators", batch_rows, column_names=col_names)
            total += len(batch_rows)

        logger.info("clickhouse_macro_indicators_written", count=total)
        return total

    # ---- Source Registry ----

    def write_source_registry(self, records: list[dict]) -> int:
        """Write data source registry records."""
        client = self._ensure_client()
        if not records:
            return 0

        rows = []
        for r in records:
            rows.append([
                str(r.get("source_id", "")),
                str(r.get("source_name", "")),
                str(r.get("source_type", "")),
                str(r.get("provider", "")),
                str(r.get("license", "")),
                str(r.get("refresh_frequency", "")),
                str(r.get("coverage", "")),
                str(r.get("status", "")),
                json.dumps(r.get("metadata", {})),
            ])

        client.insert(
            "source_registry",
            rows,
            column_names=[
                "source_id", "source_name", "source_type", "provider",
                "license", "refresh_frequency", "coverage", "status",
                "metadata",
            ],
        )
        logger.info("clickhouse_source_registry_written", count=len(rows))
        return len(rows)

    # ---- Idempotent write (with duplicate detection) ----

    def write_market_daily_idempotent(self, records: list[dict]) -> int:
        """Write market daily records with idempotency (dedup by symbol+date).

        Uses SELECT to check existing before insert.
        """
        client = self._ensure_client()
        if not records:
            return 0

        new_records = []
        for r in records:
            symbol = str(r.get("symbol", ""))
            d = _safe_date(r.get("date"))
            existing = client.query(
                "SELECT count() FROM market_daily WHERE symbol = {s: String} AND date = {d: Date}",
                parameters={"s": symbol, "d": d},
            )
            if existing.result_rows[0][0] == 0:
                new_records.append(r)

        if new_records:
            return self.write_market_daily(new_records)
        return 0
