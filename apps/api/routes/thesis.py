"""FININT OMEGA — Thesis Engine API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.thesis.models import InvalidationCondition
from core.intelligence.thesis.thesis_engine import ThesisEngine

router = APIRouter(prefix="/api/v1/intelligence/thesis", tags=["thesis"])

_engine: ThesisEngine | None = None


def _get_engine() -> ThesisEngine:
    global _engine
    if _engine is None:
        _engine = ThesisEngine()
    return _engine


class CreateThesisRequest(BaseModel):
    symbol: str
    title: str
    bull_case: str = ""
    base_case: str = ""
    bear_case: str = ""
    key_drivers: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = 0.7
    time_horizon: str = ""


class UpdateThesisRequest(BaseModel):
    change_summary: str = ""
    reason: str = ""
    bull_case: str | None = None
    base_case: str | None = None
    bear_case: str | None = None
    confidence: float | None = None
    key_drivers: list[str] | None = None
    key_risks: list[str] | None = None


class EvaluateThesisRequest(BaseModel):
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    metric_values: dict[str, float] = Field(default_factory=dict)


class AddInvalidationRequest(BaseModel):
    description: str
    metric: str = ""
    threshold: float = 0.0
    comparator: str = "lt"
    consecutive_periods: int = 1


@router.post("")
def create_thesis(req: CreateThesisRequest):
    engine = _get_engine()
    version = engine.create_thesis(
        symbol=req.symbol,
        title=req.title,
        bull_case=req.bull_case,
        base_case=req.base_case,
        bear_case=req.bear_case,
        key_drivers=req.key_drivers,
        key_risks=req.key_risks,
        assumptions=req.assumptions,
        confidence=req.confidence,
        time_horizon=req.time_horizon,
    )
    return {"thesis_id": version.thesis_id, "version": version.version_number, "status": version.status}


@router.get("/{thesis_id}")
def get_thesis(thesis_id: str):
    engine = _get_engine()
    thesis = engine.get_thesis(thesis_id)
    if thesis is None:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return thesis


@router.get("/{thesis_id}/history")
def get_thesis_history(thesis_id: str):
    engine = _get_engine()
    history = engine.get_thesis_history(thesis_id)
    if not history.versions:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return history


@router.put("/{thesis_id}")
def update_thesis(thesis_id: str, req: UpdateThesisRequest):
    engine = _get_engine()
    update_data = req.model_dump(exclude_unset=True)
    version = engine.update_thesis(thesis_id, **update_data)
    if version is None:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return version


@router.post("/{thesis_id}/evaluate")
def evaluate_thesis(thesis_id: str, req: EvaluateThesisRequest):
    engine = _get_engine()
    evaluation = engine.evaluate_thesis(
        thesis_id,
        supporting_evidence=req.supporting_evidence,
        contradicting_evidence=req.contradicting_evidence,
        metric_values=req.metric_values,
    )
    return evaluation


@router.post("/{thesis_id}/invalidation")
def add_invalidation_condition(thesis_id: str, req: AddInvalidationRequest):
    engine = _get_engine()
    condition = InvalidationCondition(
        description=req.description,
        metric=req.metric,
        threshold=req.threshold,
        comparator=req.comparator,
        consecutive_periods=req.consecutive_periods,
    )
    engine.add_invalidation_condition(thesis_id, condition)
    return {"condition_id": condition.condition_id, "status": "added"}


@router.get("")
def list_theses(symbol: str | None = None):
    engine = _get_engine()
    theses = engine.list_theses(symbol=symbol)
    return {"theses": theses, "count": len(theses)}
