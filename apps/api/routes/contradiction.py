"""FININT OMEGA — Contradiction detection API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.intelligence.contradiction.detector import ContradictionDetector

router = APIRouter(prefix="/api/v1/intelligence/contradictions", tags=["contradictions"])

_detector: ContradictionDetector | None = None


def _get_detector() -> ContradictionDetector:
    global _detector
    if _detector is None:
        _detector = ContradictionDetector()
    return _detector


class ManagementVsFinancialsRequest(BaseModel):
    management_statements: list[str]
    financial_data: dict[str, dict]


class GuidanceVsActualRequest(BaseModel):
    guidance: dict[str, float]
    actuals: dict[str, float]


class NarrativeVsNumbersRequest(BaseModel):
    narrative: str
    metrics: dict[str, dict]


class EarningsVsCashflowRequest(BaseModel):
    earnings_data: dict[str, float]
    cashflow_data: dict[str, float]


@router.post("/management-vs-financials")
def detect_management_vs_financials(req: ManagementVsFinancialsRequest):
    detector = _get_detector()
    contradictions = detector.detect_management_vs_financials(
        req.management_statements, req.financial_data,
    )
    score = detector.score_contradictions(contradictions)
    return {"contradictions": contradictions, "score": score}


@router.post("/guidance-vs-actual")
def detect_guidance_vs_actual(req: GuidanceVsActualRequest):
    detector = _get_detector()
    contradictions = detector.detect_guidance_vs_actual(req.guidance, req.actuals)
    score = detector.score_contradictions(contradictions)
    return {"contradictions": contradictions, "score": score}


@router.post("/narrative-vs-numbers")
def detect_narrative_vs_numbers(req: NarrativeVsNumbersRequest):
    detector = _get_detector()
    result = detector.detect_narrative_vs_numbers(req.narrative, req.metrics)
    return result


@router.post("/earnings-vs-cashflow")
def detect_earnings_vs_cashflow(req: EarningsVsCashflowRequest):
    detector = _get_detector()
    contradictions = detector.detect_earnings_vs_cashflow(
        req.earnings_data, req.cashflow_data,
    )
    score = detector.score_contradictions(contradictions)
    return {"contradictions": contradictions, "score": score}
