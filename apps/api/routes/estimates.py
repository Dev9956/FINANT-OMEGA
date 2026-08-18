"""FININT OMEGA — Estimate revisions API routes."""

from __future__ import annotations

from datetime import date

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.analytics.estimates.engine import EstimateEngine
from core.analytics.estimates.models import EstimateRecord

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/estimates", tags=["estimates"])

_engine = EstimateEngine()


def get_engine() -> EstimateEngine:
    """Get the estimate engine instance."""
    return _engine


class AddEstimateRequest(BaseModel):
    """Request to add an estimate record."""

    symbol: str
    metric: str
    period_end: date
    actual_value: float | None = None
    estimate_value: float | None = None
    consensus_value: float | None = None
    estimate_high: float | None = None
    estimate_low: float | None = None
    previous_estimate: float | None = None
    revision_count: int = 0
    source: str = ""


@router.post("", status_code=201)
async def add_estimate(request: AddEstimateRequest) -> dict:
    """Add an estimate record."""
    engine = get_engine()
    record = EstimateRecord(**request.model_dump())
    estimate_id = engine.add_estimate(record)
    return {"estimate_id": estimate_id, "status": "created"}


@router.get("/{symbol}")
async def get_estimates(
    symbol: str,
    metric: str | None = Query(default=None, description="Filter by metric"),
    period: date | None = Query(default=None, description="Filter by period_end"),
) -> list[dict]:
    """Get estimates for a symbol."""
    engine = get_engine()
    records = engine.get_estimates(symbol, metric, period)
    return [r.model_dump(mode="json") for r in records]


@router.get("/{symbol}/surprise")
async def compute_surprise(
    symbol: str,
    period_end: date = Query(description="Period end date"),
    as_of: date | None = Query(default=None, description="Only use estimates available before this date"),
) -> dict:
    """Compute earnings surprise for a symbol and period."""
    engine = get_engine()
    result = engine.compute_surprise(symbol, period_end, as_of)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No estimates found for {symbol} period {period_end}")
    return result.model_dump()


@router.get("/{symbol}/revisions")
async def get_revisions(
    symbol: str,
    lookback_periods: int = Query(default=4, description="Number of periods to look back"),
) -> dict:
    """Get revision momentum for a symbol."""
    engine = get_engine()
    momentum = engine.compute_revision_momentum(symbol, lookback_periods)
    return momentum.model_dump()
