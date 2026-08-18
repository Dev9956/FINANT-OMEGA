"""FININT OMEGA — Autonomous Research Loop API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.research_loop.engine import ResearchLoopEngine
from core.intelligence.research_loop.models import LoopConfig

router = APIRouter(prefix="/api/v1/intelligence/research-loop", tags=["research-loop"])

_engine: ResearchLoopEngine | None = None


def _get_engine() -> ResearchLoopEngine:
    global _engine
    if _engine is None:
        _engine = ResearchLoopEngine()
    return _engine


class RunLoopRequest(BaseModel):
    question: str
    initial_data: dict | None = None
    max_steps: int = 50
    max_iterations: int = 5
    timeout_seconds: float = 300.0


@router.post("/run")
def run_loop(req: RunLoopRequest):
    engine = _get_engine()
    config = LoopConfig(
        max_steps=req.max_steps,
        max_iterations=req.max_iterations,
        timeout_seconds=req.timeout_seconds,
    )
    result = engine.run(
        question=req.question,
        initial_data=req.initial_data,
        config=config,
    )
    return result


@router.get("/{loop_id}")
def get_result(loop_id: str):
    engine = _get_engine()
    result = engine.get_result(loop_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Loop result not found")
    return result
