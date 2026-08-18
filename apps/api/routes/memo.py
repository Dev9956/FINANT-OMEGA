"""FININT OMEGA — Investment Memo API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.memo.engine import MemoEngine

router = APIRouter(prefix="/api/v1/intelligence/memo", tags=["memo"])

_engine: MemoEngine | None = None


def _get_engine() -> MemoEngine:
    global _engine
    if _engine is None:
        _engine = MemoEngine()
    return _engine


class GenerateMemoRequest(BaseModel):
    entity: str
    thesis: str = ""
    bull_case: str = ""
    bear_case: str = ""
    base_case: str = ""
    valuation: str = ""
    financial_quality: str = ""
    risks: str = ""
    contradicting_evidence: str = ""
    scenario_analysis: str = ""
    evidence: list[str] = Field(default_factory=list)
    evidence_limitations: str = ""


@router.post("/generate")
def generate_memo(req: GenerateMemoRequest):
    engine = _get_engine()
    memo = engine.generate(**req.model_dump())
    return memo


@router.get("/{memo_id}")
def get_memo(memo_id: str):
    engine = _get_engine()
    memo = engine.get_memo(memo_id)
    if memo is None:
        raise HTTPException(status_code=404, detail="Memo not found")
    return memo


@router.get("/{memo_id}/render")
def render_memo(memo_id: str, format: str = "markdown"):
    engine = _get_engine()
    memo = engine.get_memo(memo_id)
    if memo is None:
        raise HTTPException(status_code=404, detail="Memo not found")
    if format == "markdown":
        return {"content": engine.render_markdown(memo)}
    return {"content": engine.render_markdown(memo)}
