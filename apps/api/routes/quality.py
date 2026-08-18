"""FININT OMEGA — Research Quality API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.intelligence.quality.engine import QualityEngine

router = APIRouter(prefix="/api/v1/intelligence/quality", tags=["quality"])

_engine: QualityEngine | None = None


def _get_engine() -> QualityEngine:
    global _engine
    if _engine is None:
        _engine = QualityEngine()
    return _engine


class EvaluateRequest(BaseModel):
    evidence_count: int = 0
    source_quality: float = 0.5
    numerical_accuracy: float = 0.5
    freshness: float = 0.5
    contradictions_found: int = 0
    contradictions_addressed: int = 0
    completeness: float = 0.5
    uncertainty_disclosed: bool = False
    reproducible: bool = False


@router.post("/evaluate")
def evaluate(req: EvaluateRequest):
    engine = _get_engine()
    return engine.evaluate(**req.model_dump())
