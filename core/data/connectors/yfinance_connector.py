"""FININT OMEGA — yfinance data connector for real market data."""

from __future__ import annotations

import hashlib
import importlib
import time
from datetime import date, datetime, timezone
from typing import Any

import structlog

from core.data.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    DataQuality,
    register_connector,
)

logger = structlog.get_logger()

# Lazy import to avoid import errors when yfinance is not installed
_yf = None


def _get_yf():
    global _yf
    if _yf is None:
        try:
            _yf = importlib.import_module("yfinance")
        except ImportError:
            raise ImportError(
                "yfinance is required for real market data. "
                "Install with: pip install yfinance"
            )
    return _yf


class YFinanceMarketConnector(BaseConnector):
    """Real market data connector using yfinance.

    Provider-agnostic: can be replaced with Bloomberg, FactSet, etc.
    by implementing _fetch_raw with a different data source.
    """

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        super().__init__(
            source_id="yfinance_market",
            name="Yahoo Finance (yfinance)",
            config=config or ConnectorConfig(
                timeout_seconds=30.0,
                max_retries=3,
                retry_delay_seconds=1.0,
                rate_limit_per_second=2.0,  # yfinance has rate limits
                cache_ttl_seconds=600.0,  # 10 min cache for market data
            ),
        )
        self._quality = DataQuality.REAL

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Fetch OHLCV data from yfinance."""
        symbol = kwargs.get("symbol")
        if not symbol:
            raise ValueError("symbol is required")

        period = kwargs.get("period", "1y")
        interval = kwargs.get("interval", "1d")

        yf = _get_yf()
        ticker = yf.Ticker(symbol)

        # Fetch historical data
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            logger.warning("yfinance_empty_data", symbol=symbol)
            return []

        records = []
        for idx, row in df.iterrows():
            dt = idx.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            records.append({
                "symbol": symbol,
                "date": dt.date().isoformat(),
                "open": float(row.get("Open", 0)),
                "high": float(row.get("High", 0)),
                "low": float(row.get("Low", 0)),
                "close": float(row.get("Close", 0)),
                "volume": int(row.get("Volume", 0)),
                "adjusted_close": float(row.get("Close", 0)),
                "_source": self.source_id,
                "_event_time": dt.isoformat(),
                "_publication_time": dt.isoformat(),
                "_available_time": dt.isoformat(),
                "_entity_id": symbol,
                "_instrument_id": symbol,
                "_raw_reference_id": f"yfinance:{symbol}:{dt.date().isoformat()}",
            })

        return records

    def health_check(self) -> bool:
        try:
            yf = _get_yf()
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            return bool(info)
        except Exception as e:
            logger.error("yfinance_health_check_failed", error=str(e))
            return False


class YFinanceFundamentalsConnector(BaseConnector):
    """Real fundamentals connector using yfinance."""

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        super().__init__(
            source_id="yfinance_fundamentals",
            name="Yahoo Finance Fundamentals",
            config=config or ConnectorConfig(
                timeout_seconds=30.0,
                max_retries=3,
                retry_delay_seconds=2.0,
                rate_limit_per_second=1.0,  # Slower rate for fundamentals
                cache_ttl_seconds=3600.0,  # 1 hour cache
            ),
        )
        self._quality = DataQuality.REAL

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Fetch fundamental data from yfinance."""
        symbol = kwargs.get("symbol")
        if not symbol:
            raise ValueError("symbol is required")

        yf = _get_yf()
        ticker = yf.Ticker(symbol)
        records = []

        # Get info (current snapshot)
        try:
            info = ticker.info
            if info:
                records.append({
                    "symbol": symbol,
                    "data_type": "info",
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "market_cap": info.get("marketCap"),
                    "enterprise_value": info.get("enterpriseValue"),
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "peg_ratio": info.get("pegRatio"),
                    "price_to_book": info.get("priceToBook"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "return_on_equity": info.get("returnOnEquity"),
                    "return_on_assets": info.get("returnOnAssets"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                    "profit_margins": info.get("profitMargins"),
                    "operating_margins": info.get("operatingMargins"),
                    "free_cashflow": info.get("freeCashflow"),
                    "dividend_yield": info.get("dividendYield"),
                    "beta": info.get("beta"),
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                    "currency": info.get("currency", "USD"),
                    "_source": self.source_id,
                    "_entity_id": symbol,
                    "_publication_time": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            logger.warning("yfinance_info_error", symbol=symbol, error=str(e))

        # Get financials (income statement)
        try:
            financials = ticker.financials
            if financials is not None and not financials.empty:
                for col in financials.columns[:4]:  # Last 4 periods
                    period_data = financials[col].dropna().to_dict()
                    if period_data:
                        records.append({
                            "symbol": symbol,
                            "data_type": "income_statement",
                            "period_end": col.date().isoformat() if hasattr(col, "date") else str(col),
                            "total_revenue": float(period_data.get("Total Revenue", 0)),
                            "cost_of_revenue": float(period_data.get("Cost Of Revenue", 0)),
                            "gross_profit": float(period_data.get("Gross Profit", 0)),
                            "operating_income": float(period_data.get("Operating Income", 0)),
                            "net_income": float(period_data.get("Net Income", 0)),
                            "eps_diluted": float(period_data.get("Diluted EPS", 0)),
                            "_source": self.source_id,
                            "_entity_id": symbol,
                            "_event_time": col.isoformat() if hasattr(col, "isoformat") else str(col),
                        })
        except Exception as e:
            logger.warning("yfinance_financials_error", symbol=symbol, error=str(e))

        # Get balance sheet
        try:
            balance = ticker.balance_sheet
            if balance is not None and not balance.empty:
                for col in balance.columns[:4]:
                    period_data = balance[col].dropna().to_dict()
                    if period_data:
                        records.append({
                            "symbol": symbol,
                            "data_type": "balance_sheet",
                            "period_end": col.date().isoformat() if hasattr(col, "date") else str(col),
                            "total_assets": float(period_data.get("Total Assets", 0)),
                            "total_liabilities": float(period_data.get("Total Liabilities Net Minority Interest", 0)),
                            "total_equity": float(period_data.get("Stockholders Equity", 0)),
                            "cash_and_equivalents": float(period_data.get("Cash And Cash Equivalents", 0)),
                            "total_debt": float(period_data.get("Total Debt", 0)),
                            "_source": self.source_id,
                            "_entity_id": symbol,
                            "_event_time": col.isoformat() if hasattr(col, "isoformat") else str(col),
                        })
        except Exception as e:
            logger.warning("yfinance_balance_sheet_error", symbol=symbol, error=str(e))

        # Get cash flow
        try:
            cashflow = ticker.cashflow
            if cashflow is not None and not cashflow.empty:
                for col in cashflow.columns[:4]:
                    period_data = cashflow[col].dropna().to_dict()
                    if period_data:
                        records.append({
                            "symbol": symbol,
                            "data_type": "cash_flow",
                            "period_end": col.date().isoformat() if hasattr(col, "date") else str(col),
                            "operating_cashflow": float(period_data.get("Operating Cash Flow", 0)),
                            "capital_expenditure": float(period_data.get("Capital Expenditure", 0)),
                            "free_cashflow": float(period_data.get("Free Cash Flow", 0)),
                            "_source": self.source_id,
                            "_entity_id": symbol,
                            "_event_time": col.isoformat() if hasattr(col, "isoformat") else str(col),
                        })
        except Exception as e:
            logger.warning("yfinance_cashflow_error", symbol=symbol, error=str(e))

        return records

    def health_check(self) -> bool:
        try:
            yf = _get_yf()
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            return bool(info)
        except Exception:
            return False


class YFinanceEarningsConnector(BaseConnector):
    """Real earnings/estimates connector using yfinance."""

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        super().__init__(
            source_id="yfinance_earnings",
            name="Yahoo Finance Earnings",
            config=config or ConnectorConfig(
                timeout_seconds=30.0,
                max_retries=3,
                retry_delay_seconds=2.0,
                rate_limit_per_second=1.0,
                cache_ttl_seconds=3600.0,
            ),
        )
        self._quality = DataQuality.REAL

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Fetch earnings data from yfinance."""
        symbol = kwargs.get("symbol")
        if not symbol:
            raise ValueError("symbol is required")

        yf = _get_yf()
        ticker = yf.Ticker(symbol)
        records = []

        # Get earnings dates
        try:
            earnings_dates = ticker.earnings_dates
            if earnings_dates is not None and not earnings_dates.empty:
                for idx, row in earnings_dates.iterrows():
                    records.append({
                        "symbol": symbol,
                        "data_type": "earnings_date",
                        "date": idx.date().isoformat() if hasattr(idx, "date") else str(idx),
                        "eps_estimate": float(row.get("EPS Estimate", 0)) if row.get("EPS Estimate") else None,
                        "reported_eps": float(row.get("Reported EPS", 0)) if row.get("Reported EPS") else None,
                        "surprise_pct": float(row.get("Surprise(%)", 0)) if row.get("Surprise(%)") else None,
                        "_source": self.source_id,
                        "_entity_id": symbol,
                    })
        except Exception as e:
            logger.warning("yfinance_earnings_dates_error", symbol=symbol, error=str(e))

        # Get analyst recommendations
        try:
            recommendations = ticker.recommendations
            if recommendations is not None and not recommendations.empty:
                for idx, row in recommendations.head(20).iterrows():
                    records.append({
                        "symbol": symbol,
                        "data_type": "analyst_recommendation",
                        "date": idx.date().isoformat() if hasattr(idx, "date") else str(idx),
                        "firm": row.get("From", ""),
                        "action": row.get("Action", ""),
                        "recommendation": row.get("To", ""),
                        "_source": self.source_id,
                        "_entity_id": symbol,
                    })
        except Exception as e:
            logger.warning("yfinance_recommendations_error", symbol=symbol, error=str(e))

        # Get analyst price targets
        try:
            target = ticker.analyst_price_targets
            if target:
                records.append({
                    "symbol": symbol,
                    "data_type": "price_target",
                    "mean_target": target.get("mean"),
                    "median_target": target.get("median"),
                    "high_target": target.get("high"),
                    "low_target": target.get("low"),
                    "number_of_analysts": target.get("numberOfAnalystOpinions"),
                    "_source": self.source_id,
                    "_entity_id": symbol,
                })
        except Exception as e:
            logger.warning("yfinance_price_targets_error", symbol=symbol, error=str(e))

        return records

    def health_check(self) -> bool:
        try:
            yf = _get_yf()
            ticker = yf.Ticker("AAPL")
            return ticker.earnings_dates is not None
        except Exception:
            return False


# Register connectors
register_connector("yfinance_market", YFinanceMarketConnector)
register_connector("yfinance_fundamentals", YFinanceFundamentalsConnector)
register_connector("yfinance_earnings", YFinanceEarningsConnector)
