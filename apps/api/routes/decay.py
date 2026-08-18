"""FININT OMEGA — Information Decay API routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from core.intelligence.decay.engine import DecayEngine
from core.intelligence.decay.models import DecayFactor, EvidenceItem

router = APIRouter(prefix="/api/v1/intelligence/decay", tags=["decay"])

_engine: DecayEngine | None = None


def _get_engine() -> DecayEngine:
    global _engine
    if _engine is None:
        _engine = DecayEngine()
    return _engine


class AddEvidenceRequest(BaseModel):
    content: str
    source: str = ""
    decay_factor: str = "news_article"
    source_quality: float = 0.7
    confidence: float = 0.7


class ScoreRequest(BaseModel):
    evidence_ids: list[str] | None = None


@router.post("/evidence")
def add_evidence(req: AddEvidenceRequest):
    engine = _get_engine()
    evidence = EvidenceItem(
        content=req.content,
        source=req.source,
        decay_factor=DecayFactor(req.decay_factor),
        source_quality=req.source_quality,
        confidence=req.confidence,
    )
    eid = engine.add_evidence(evidence)
    return {"evidence_id": eid}


@router.post("/score")
def score_evidence(req: ScoreRequest):
    engine = _get_engine()
    results = engine.get_weighted_evidence(evidence_ids=req.evidence_ids)
    return {"evidence": results, "count": len(results)}


@router.post("/confirm/{evidence_id}")
def confirm_evidence(evidence_id: str):
    engine = _get_engine()
    confirmed = engine.confirm_evidence(evidence_id)
    return {"confirmed": confirmed}


@router.get("/all")
def get_all_evidence():
    engine = _get_engine()
    results = engine.score_all_evidence()
    return {"evidence": results, "count": len(results)}
