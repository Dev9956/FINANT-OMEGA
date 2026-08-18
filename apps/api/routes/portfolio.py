"""FININT OMEGA — Portfolio Management API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])

# In-memory portfolio store
_portfolios: dict[str, dict] = {}


class PositionRequest(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    side: str = "long"


class PositionUpdateRequest(BaseModel):
    quantity: float | None = None
    avg_cost: float | None = None


@router.post("/positions", status_code=201)
def add_position(req: PositionRequest):
    pos_id = str(uuid.uuid4())
    position = {
        "position_id": pos_id,
        "symbol": req.symbol.upper(),
        "quantity": req.quantity,
        "avg_cost": req.avg_cost,
        "side": req.side,
        "cost_basis": req.quantity * req.avg_cost,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _portfolios[pos_id] = position
    logger.info("position_added", symbol=req.symbol, quantity=req.quantity)
    return position


@router.get("/positions")
def list_positions():
    positions = list(_portfolios.values())
    total_cost = sum(p["cost_basis"] for p in positions)
    return {
        "positions": positions,
        "count": len(positions),
        "total_cost_basis": round(total_cost, 2),
    }


@router.get("/positions/{position_id}")
def get_position(position_id: str):
    pos = _portfolios.get(position_id)
    if not pos:
        raise HTTPException(404, "Position not found")
    return pos


@router.put("/positions/{position_id}")
def update_position(position_id: str, req: PositionUpdateRequest):
    pos = _portfolios.get(position_id)
    if not pos:
        raise HTTPException(404, "Position not found")
    if req.quantity is not None:
        pos["quantity"] = req.quantity
    if req.avg_cost is not None:
        pos["avg_cost"] = req.avg_cost
    pos["cost_basis"] = pos["quantity"] * pos["avg_cost"]
    pos["updated_at"] = datetime.now(timezone.utc).isoformat()
    return pos


@router.delete("/positions/{position_id}")
def delete_position(position_id: str):
    if position_id not in _portfolios:
        raise HTTPException(404, "Position not found")
    del _portfolios[position_id]
    return {"status": "deleted", "position_id": position_id}


@router.get("/summary")
def portfolio_summary():
    positions = list(_portfolios.values())
    if not positions:
        return {"positions": [], "total_cost_basis": 0, "total_market_value": 0, "total_pnl": 0}
    total_cost = sum(p["cost_basis"] for p in positions)
    return {
        "positions": positions,
        "count": len(positions),
        "total_cost_basis": round(total_cost, 2),
    }
