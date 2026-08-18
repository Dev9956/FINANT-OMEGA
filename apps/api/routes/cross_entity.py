"""FININT OMEGA — Cross-Entity Intelligence API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.cross_entity.engine import CrossEntityEngine
from core.intelligence.cross_entity.models import CrossEntityRequest, EntityMetrics, RankingCriterion

router = APIRouter(prefix="/api/v1/intelligence/cross-entity", tags=["cross-entity"])

_engine: CrossEntityEngine | None = None


def _get_engine() -> CrossEntityEngine:
    global _engine
    if _engine is None:
        _engine = CrossEntityEngine()
    return _engine


class RegisterEntityRequest(BaseModel):
    symbol: str
    name: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)
    thesis_health: str = ""
    anomaly_score: float = 0.0


class AnalyzeRequest(BaseModel):
    symbols: list[str]
    criteria: list[str] = Field(default_factory=lambda: ["composite"])
    max_results: int = 50


@router.post("/entities")
def register_entity(req: RegisterEntityRequest):
    engine = _get_engine()
    entity = EntityMetrics(
        entity_id=req.symbol,
        symbol=req.symbol,
        name=req.name,
        metrics=req.metrics,
        thesis_health=req.thesis_health,
        anomaly_score=req.anomaly_score,
    )
    eid = engine.register_entity(entity)
    return {"entity_id": eid}


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    engine = _get_engine()
    criteria = [RankingCriterion(c) for c in req.criteria]
    request = CrossEntityRequest(
        symbols=req.symbols,
        criteria=criteria,
        max_results=req.max_results,
    )
    result = engine.analyze(request)
    return result


@router.get("/results/{result_id}")
def get_result(result_id: str):
    engine = _get_engine()
    result = engine.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/weakening-thesis")
def find_weakening_thesis():
    engine = _get_engine()
    return {"entities": engine.find_weakening_thesis()}


@router.get("/strong-cashflow-low-valuation")
def find_strong_cashflow_low_valuation():
    engine = _get_engine()
    return {"entities": engine.find_strong_cashflow_low_valuation()}


@router.get("/high-anomaly")
def find_high_anomaly(threshold: float = 0.7):
    engine = _get_engine()
    return {"entities": engine.find_high_anomaly(threshold=threshold)}
