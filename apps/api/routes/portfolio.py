"""FININT OMEGA — Portfolio Management API routes with PostgreSQL persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.persistence.db import get_pool, is_pg_available, _row_to_dict, _rows_to_dicts

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])

# In-memory fallback
_portfolios: dict[str, dict] = {}


class PositionRequest(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    side: str = "long"


class PositionUpdateRequest(BaseModel):
    quantity: float | None = None
    avg_cost: float | None = None


async def _db_list_positions(user_id: str = "dev-user") -> list[dict]:
    pool = await get_pool()
    if pool is None:
        return [p for p in _portfolios.values() if p.get("user_id") == user_id]
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM portfolio_positions WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
        return _rows_to_dicts(rows)


async def _db_get_position(position_id: str) -> dict | None:
    pool = await get_pool()
    if pool is None:
        return _portfolios.get(position_id)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM portfolio_positions WHERE position_id = $1",
            uuid.UUID(position_id),
        )
        return _row_to_dict(row) if row else None


async def _db_create_position(user_id: str, symbol: str, quantity: float, avg_cost: float, side: str) -> dict:
    pos_id = uuid.uuid4()
    cost_basis = round(quantity * avg_cost, 2)
    now = datetime.now(timezone.utc)
    pool = await get_pool()
    if pool is None:
        position = {
            "position_id": str(pos_id),
            "user_id": user_id,
            "symbol": symbol.upper(),
            "quantity": quantity,
            "avg_cost": avg_cost,
            "side": side,
            "cost_basis": cost_basis,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _portfolios[str(pos_id)] = position
        return position
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO portfolio_positions (position_id, user_id, symbol, quantity, avg_cost, side, cost_basis)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *""",
            pos_id, user_id, symbol.upper(), quantity, avg_cost, side, cost_basis,
        )
        return _row_to_dict(row)


async def _db_update_position(position_id: str, quantity: float | None, avg_cost: float | None) -> dict:
    pool = await get_pool()
    now = datetime.now(timezone.utc)
    if pool is None:
        pos = _portfolios.get(position_id)
        if not pos:
            return {}
        if quantity is not None:
            pos["quantity"] = quantity
        if avg_cost is not None:
            pos["avg_cost"] = avg_cost
        pos["cost_basis"] = pos["quantity"] * pos["avg_cost"]
        pos["updated_at"] = now.isoformat()
        return pos
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM portfolio_positions WHERE position_id = $1",
            uuid.UUID(position_id),
        )
        if not existing:
            return {}
        new_qty = quantity if quantity is not None else existing["quantity"]
        new_cost = avg_cost if avg_cost is not None else existing["avg_cost"]
        new_basis = round(new_qty * new_cost, 2)
        row = await conn.fetchrow(
            """UPDATE portfolio_positions SET quantity = $1, avg_cost = $2, cost_basis = $3, updated_at = $4
               WHERE position_id = $5 RETURNING *""",
            new_qty, new_cost, new_basis, now, uuid.UUID(position_id),
        )
        return _row_to_dict(row) if row else {}


async def _db_delete_position(position_id: str) -> bool:
    pool = await get_pool()
    if pool is None:
        if position_id in _portfolios:
            del _portfolios[position_id]
            return True
        return False
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM portfolio_positions WHERE position_id = $1",
            uuid.UUID(position_id),
        )
        return result == "DELETE 1"


@router.post("/positions", status_code=201)
async def add_position(req: PositionRequest):
    position = await _db_create_position("dev-user", req.symbol, req.quantity, req.avg_cost, req.side)
    logger.info("position_added", symbol=req.symbol, quantity=req.quantity)
    return position


@router.get("/positions")
async def list_positions():
    positions = await _db_list_positions("dev-user")
    total_cost = sum(p["cost_basis"] for p in positions)
    return {
        "positions": positions,
        "count": len(positions),
        "total_cost_basis": round(total_cost, 2),
    }


@router.get("/positions/{position_id}")
async def get_position(position_id: str):
    pos = await _db_get_position(position_id)
    if not pos:
        raise HTTPException(404, "Position not found")
    return pos


@router.put("/positions/{position_id}")
async def update_position(position_id: str, req: PositionUpdateRequest):
    pos = await _db_update_position(position_id, req.quantity, req.avg_cost)
    if not pos:
        raise HTTPException(404, "Position not found")
    return pos


@router.delete("/positions/{position_id}")
async def delete_position(position_id: str):
    deleted = await _db_delete_position(position_id)
    if not deleted:
        raise HTTPException(404, "Position not found")
    return {"status": "deleted", "position_id": position_id}


@router.get("/summary")
async def portfolio_summary():
    positions = await _db_list_positions("dev-user")
    if not positions:
        return {
            "positions": [],
            "count": 0,
            "total_cost_basis": 0,
            "total_market_value": 0,
            "total_pnl": 0,
            "allocation": [],
            "risk_metrics": {},
        }

    total_cost = sum(p["cost_basis"] for p in positions)

    allocation = []
    for p in positions:
        pct = (p["cost_basis"] / total_cost * 100) if total_cost > 0 else 0
        allocation.append({
            "symbol": p["symbol"],
            "cost_basis": round(p["cost_basis"], 2),
            "allocation_pct": round(pct, 2),
            "quantity": p["quantity"],
            "avg_cost": p["avg_cost"],
            "side": p["side"],
        })

    symbols = list({p["symbol"] for p in positions})

    return {
        "positions": positions,
        "count": len(positions),
        "total_cost_basis": round(total_cost, 2),
        "total_market_value": round(total_cost, 2),
        "total_pnl": 0.0,
        "allocation": allocation,
        "symbols": symbols,
        "risk_metrics": {
            "concentration_highest": round(max(a["allocation_pct"] for a in allocation), 2) if allocation else 0,
            "num_positions": len(positions),
            "num_symbols": len(symbols),
        },
    }
