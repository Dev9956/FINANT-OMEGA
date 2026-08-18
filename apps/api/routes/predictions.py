"""FININT OMEGA — Prediction Tracking API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.predictions.engine import PredictionEngine

router = APIRouter(prefix="/api/v1/intelligence/predictions", tags=["predictions"])

_engine: PredictionEngine | None = None


def _get_engine() -> PredictionEngine:
    global _engine
    if _engine is None:
        _engine = PredictionEngine()
    return _engine


class RegisterPredictionRequest(BaseModel):
    entity: str
    prediction_text: str
    metric: str = ""
    predicted_value: float | None = None
    direction: str = ""
    confidence: float = 0.5
    horizon_days: int = 30
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ResolvePredictionRequest(BaseModel):
    actual_value: float


@router.post("")
def register_prediction(req: RegisterPredictionRequest):
    engine = _get_engine()
    pred = engine.register_prediction(
        entity=req.entity,
        prediction_text=req.prediction_text,
        metric=req.metric,
        predicted_value=req.predicted_value,
        direction=req.direction,
        confidence=req.confidence,
        horizon_days=req.horizon_days,
        assumptions=req.assumptions,
        evidence=req.evidence,
    )
    return pred


@router.get("/{prediction_id}")
def get_prediction(prediction_id: str):
    engine = _get_engine()
    pred = engine.get_prediction(prediction_id)
    if pred is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return pred


@router.post("/{prediction_id}/resolve")
def resolve_prediction(prediction_id: str, req: ResolvePredictionRequest):
    engine = _get_engine()
    outcome = engine.resolve_prediction(prediction_id, req.actual_value)
    if outcome is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return outcome


@router.get("")
def list_predictions(entity: str | None = None):
    engine = _get_engine()
    preds = engine.list_predictions(entity=entity)
    return {"predictions": preds, "count": len(preds)}


@router.get("/calibration/report")
def calibration_report():
    engine = _get_engine()
    return {"calibration": engine.compute_calibration(), "brier_score": engine.compute_brier_score()}
