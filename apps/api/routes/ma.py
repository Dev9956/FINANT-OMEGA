"""FININT OMEGA — M&A intelligence API routes."""

from __future__ import annotations

from datetime import date

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.analytics.ma_intelligence.engine import MAIntelligenceEngine
from core.analytics.ma_intelligence.models import DealStatus, Transaction, TransactionType

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/ma", tags=["ma_intelligence"])

_engine = MAIntelligenceEngine()


def get_engine() -> MAIntelligenceEngine:
    """Get the M&A intelligence engine instance."""
    return _engine


class AddTransactionRequest(BaseModel):
    """Request to add a transaction."""

    transaction_type: TransactionType
    acquirer_symbol: str | None = None
    target_symbol: str | None = None
    deal_value: float | None = None
    deal_date: date
    status: DealStatus = DealStatus.announced
    currency: str = "USD"
    metadata: dict = {}


@router.post("/transactions", status_code=201)
async def add_transaction(request: AddTransactionRequest) -> dict:
    """Add a transaction record."""
    engine = get_engine()
    transaction = Transaction(**request.model_dump())
    tx_id = engine.add_transaction(transaction)
    return {"transaction_id": tx_id, "status": "created"}


@router.get("/transactions/{symbol}")
async def get_transactions(symbol: str) -> list[dict]:
    """Get transactions for a symbol."""
    engine = get_engine()
    txns = engine.get_transactions(symbol)
    return [t.model_dump(mode="json") for t in txns]


@router.get("/active")
async def get_active_deals() -> list[dict]:
    """Get all active (announced) deals."""
    engine = get_engine()
    deals = engine.get_active_deals()
    return [d.model_dump(mode="json") for d in deals]


@router.get("/sector/{sector}")
async def get_sector_transactions(
    sector: str,
    since_date: date | None = Query(default=None, description="Filter from this date"),
) -> list[dict]:
    """Get transactions for a sector."""
    engine = get_engine()
    txns = engine.get_sector_transactions(sector, since_date)
    return [t.model_dump(mode="json") for t in txns]
