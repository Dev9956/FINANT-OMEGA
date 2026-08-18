"""FININT OMEGA — Debate Engine API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.debate.engine import DebateEngine

router = APIRouter(prefix="/api/v1/intelligence/debate", tags=["debate"])

_engine: DebateEngine | None = None


def _get_engine() -> DebateEngine:
    global _engine
    if _engine is None:
        _engine = DebateEngine()
    return _engine


class RunDebateRequest(BaseModel):
    question: str
    context: dict | None = None
    evidence_items: list[str] = Field(default_factory=list)


@router.post("")
def run_debate(req: RunDebateRequest):
    engine = _get_engine()
    result = engine.run_debate(
        question=req.question,
        context=req.context,
        evidence_items=req.evidence_items,
    )
    return result


@router.get("/{debate_id}")
def get_debate(debate_id: str):
    engine = _get_engine()
    debate = engine.get_debate(debate_id)
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debate
