"""FININT OMEGA — Regime Detection API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.intelligence.regime.detector import RegimeDetector

router = APIRouter(prefix="/api/v1/intelligence/regime", tags=["regime"])

_detector: RegimeDetector | None = None


def _get_detector() -> RegimeDetector:
    global _detector
    if _detector is None:
        _detector = RegimeDetector()
    return _detector


class DetectRegimeRequest(BaseModel):
    market_data: dict[str, float] | None = None
    indicators: dict[str, float] | None = None


@router.post("/detect")
def detect_regime(req: DetectRegimeRequest):
    detector = _get_detector()
    result = detector.detect(
        market_data=req.market_data,
        indicators=req.indicators,
    )
    return result
