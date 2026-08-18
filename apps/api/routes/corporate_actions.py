"""FININT OMEGA — Corporate actions API routes."""

from __future__ import annotations

from datetime import date

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.analytics.corporate_actions.engine import CorporateActionsEngine
from core.analytics.corporate_actions.models import ActionType, CorporateActionRecord

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/corporate-actions", tags=["corporate_actions"])

_engine = CorporateActionsEngine()


def get_engine() -> CorporateActionsEngine:
    """Get the corporate actions engine instance."""
    return _engine


class AddActionRequest(BaseModel):
    """Request to add a corporate action."""

    symbol: str
    action_type: ActionType
    ex_date: date
    effective_date: date | None = None
    ratio: float | None = None
    dividend_per_share: float | None = None
    description: str = ""


class AdjustPricesRequest(BaseModel):
    """Request to adjust prices for corporate actions."""

    symbol: str
    prices: list[dict] = Field(description="List of {date, close, symbol}")


@router.post("", status_code=201)
async def add_corporate_action(request: AddActionRequest) -> dict:
    """Add a corporate action."""
    engine = get_engine()
    record = CorporateActionRecord(**request.model_dump())
    action_id = engine.add_action(record)
    return {"action_id": action_id, "status": "created"}


@router.get("/{symbol}")
async def get_actions(
    symbol: str,
    since_date: date | None = Query(default=None, description="Filter from this date"),
) -> list[dict]:
    """Get corporate actions for a symbol."""
    engine = get_engine()
    actions = engine.get_actions(symbol, since_date)
    return [a.model_dump(mode="json") for a in actions]


@router.post("/adjust")
async def adjust_prices(request: AdjustPricesRequest) -> dict:
    """Adjust prices for corporate actions."""
    engine = get_engine()
    actions = engine.get_actions(request.symbol)
    if not actions:
        raise HTTPException(status_code=404, detail=f"No corporate actions found for {request.symbol}")

    adjusted = engine.adjust_prices(request.prices, actions)
    return {
        "symbol": request.symbol,
        "adjusted_prices": [a.model_dump(mode="json") for a in adjusted],
    }
