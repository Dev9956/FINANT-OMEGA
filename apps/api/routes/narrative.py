"""FININT OMEGA — Narrative vs Numbers API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.intelligence.narrative.analyzer import NarrativeAnalyzer

router = APIRouter(prefix="/api/v1/intelligence/narrative", tags=["narrative"])

_analyzer: NarrativeAnalyzer | None = None


def _get_analyzer() -> NarrativeAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = NarrativeAnalyzer()
    return _analyzer


class AnalyzeNarrativeRequest(BaseModel):
    narrative: str
    metrics: dict[str, dict]
    metric_mappings: dict[str, str] | None = None


@router.post("/analyze")
def analyze_narrative(req: AnalyzeNarrativeRequest):
    analyzer = _get_analyzer()
    result = analyzer.analyze(
        req.narrative,
        req.metrics,
        metric_mappings=req.metric_mappings,
    )
    return result
