"""FININT OMEGA — Early Warning API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.intelligence.early_warning.engine import EarlyWarningEngine

router = APIRouter(prefix="/api/v1/intelligence/early-warning", tags=["early-warning"])

_engine: EarlyWarningEngine | None = None


def _get_engine() -> EarlyWarningEngine:
    global _engine
    if _engine is None:
        _engine = EarlyWarningEngine()
    return _engine


class ScanRequest(BaseModel):
    symbol: str
    current_metrics: dict[str, float]
    previous_metrics: dict[str, float] | None = None


@router.post("/scan")
def scan(req: ScanRequest):
    engine = _get_engine()
    warnings = engine.scan(
        symbol=req.symbol,
        current_metrics=req.current_metrics,
        previous_metrics=req.previous_metrics,
    )
    return {"warnings": warnings, "count": len(warnings)}


@router.get("/warnings")
def get_warnings(symbol: str | None = None):
    engine = _get_engine()
    warnings = engine.get_warnings(symbol=symbol)
    return {"warnings": warnings, "count": len(warnings)}
