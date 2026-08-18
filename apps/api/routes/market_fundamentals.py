"""FININT OMEGA — Market and fundamentals API routes."""

from __future__ import annotations

from datetime import date

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.analytics.earnings import EarningsAnalyzer, EarningsRecord
from core.analytics.fundamentals import FinancialRatioCalculator
from core.analytics.market.prices import MarketPriceAnalyzer
from core.analytics.screening import StockScreener
from core.data.connectors import MockFundamentalsConnector, MockMarketConnector
from core.data.schemas import FinancialStatement, MarketOHLCV

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["market", "fundamentals"])


class MarketQueryRequest(BaseModel):
    """Request for market data query."""

    symbol: str
    start_date: str | None = None
    end_date: str | None = None


class AnalyticsResponse(BaseModel):
    """Response with computed analytics."""

    symbol: str
    cagr: float | None = None
    volatility: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    data_points: int = 0


class ScreeningRequest(BaseModel):
    """Stock screening request."""

    filters: list[dict] = Field(description="List of {field, operator, value}")
    candidates: list[dict] = Field(default_factory=list, description="Candidate stocks data")


from core.data.connectors.yfinance_connector import YFinanceMarketConnector
from core.data.connectors import MockMarketConnector

@router.get("/market/{symbol}/prices")
async def get_market_prices(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
    days: int = 30
) -> list[dict]:
    """Get real market price history for a symbol."""
    try:
        connector = YFinanceMarketConnector()
        records = connector.fetch(symbol=symbol, period=period, interval=interval)
        if records:
            return [r.data for r in records]
    except Exception as e:
        logger.warning("yfinance_fetch_failed_using_fallback", symbol=symbol, error=str(e))
    
    # Fallback connector if yfinance is temporarily unreachable
    connector = MockMarketConnector()
    records = connector.fetch(symbol=symbol, days=days)
    return [r.data for r in records]


@router.post("/market/{symbol}/analytics", response_model=AnalyticsResponse)
async def compute_market_analytics(symbol: str, request: MarketQueryRequest) -> AnalyticsResponse:
    """Compute analytics for a market symbol."""
    connector = MockMarketConnector()
    records = connector.fetch(symbol=symbol, days=365)
    if not records:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    prices = [r.data["close"] for r in records]
    analyzer = MarketPriceAnalyzer()

    returns = analyzer.compute_returns(prices)
    return AnalyticsResponse(
        symbol=symbol,
        cagr=analyzer.compute_cagr(prices),
        volatility=analyzer.compute_volatility(returns),
        sharpe_ratio=analyzer.compute_sharpe_ratio(returns),
        max_drawdown=analyzer.compute_max_drawdown(prices),
        data_points=len(prices),
    )


@router.get("/market/{symbol}/indicators")
async def get_market_indicators(symbol: str, period: int = 20) -> dict:
    """Get technical indicators for a symbol."""
    connector = MockMarketConnector()
    records = connector.fetch(symbol=symbol, days=100)
    prices = [r.data["close"] for r in records]
    analyzer = MarketPriceAnalyzer()

    sma = analyzer.compute_sma(prices, period)
    ema = analyzer.compute_ema(prices, period)
    rsi = analyzer.compute_rsi(prices)
    bb_upper, bb_mid, bb_lower = analyzer.compute_bollinger_bands(prices, period)

    return {
        "symbol": symbol,
        "prices": prices[-period:],
        "sma": [v for v in sma[-period:] if v is not None],
        "ema": [v for v in ema[-period:] if v is not None],
        "rsi": [v for v in rsi[-period:] if v is not None],
        "bollinger_upper": [v for v in bb_upper[-period:] if v is not None],
        "bollinger_lower": [v for v in bb_lower[-period:] if v is not None],
    }


@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str) -> list[dict]:
    """Get financial statements for a symbol."""
    connector = MockFundamentalsConnector()
    records = connector.fetch(symbol=symbol)
    return [r.data for r in records]


@router.get("/fundamentals/{symbol}/ratios")
async def get_financial_ratios(symbol: str) -> dict:
    """Compute financial ratios for a symbol."""
    connector = MockFundamentalsConnector()
    records = connector.fetch(symbol=symbol)
    if not records:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    stmt = FinancialStatement(**records[0].data)
    calc = FinancialRatioCalculator()
    ratios = calc.compute_from_statement(stmt)
    return ratios.model_dump()


@router.post("/screening/query")
async def screen_stocks(request: ScreeningRequest) -> list[dict]:
    """Screen stocks based on criteria."""
    screener = StockScreener()
    results = screener.screen_financials(request.candidates, request.filters)
    return results


@router.get("/earnings/{symbol}/analysis")
async def analyze_earnings(symbol: str) -> dict:
    """Analyze earnings for a symbol (mock data)."""
    analyzer = EarningsAnalyzer()
    # Mock earnings data
    records = [
        EarningsRecord(
            symbol=symbol,
            report_date=date(2025, 1, 15),
            period_end=date(2024, 12, 31),
            eps_actual=15.0,
            eps_estimate=14.0,
            revenue_actual=500000000.0,
            revenue_estimate=480000000.0,
        ),
        EarningsRecord(
            symbol=symbol,
            report_date=date(2024, 10, 15),
            period_end=date(2024, 9, 30),
            eps_actual=13.5,
            eps_estimate=13.0,
            revenue_actual=480000000.0,
            revenue_estimate=470000000.0,
        ),
    ]
    surprise = analyzer.analyze_surprise(records[0])
    momentum = analyzer.compute_earnings_momentum(records)
    return {"surprise": surprise, "momentum": momentum}
