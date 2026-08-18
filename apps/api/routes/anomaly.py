"""FININT OMEGA — Anomaly Detection API routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.intelligence.anomaly.detector import AnomalyDetector

router = APIRouter(prefix="/api/v1/intelligence/anomaly", tags=["anomaly"])

_detector: AnomalyDetector | None = None


def _get_detector() -> AnomalyDetector:
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector


class DetectAnomalyRequest(BaseModel):
    symbol: str
    metrics: dict[str, float]
    previous_metrics: dict[str, float] | None = None
    peer_metrics: dict[str, dict[str, float]] | None = None


@router.post("/detect")
def detect_anomaly(req: DetectAnomalyRequest):
    detector = _get_detector()
    anomalies = detector.detect(
        symbol=req.symbol,
        metrics=req.metrics,
        previous_metrics=req.previous_metrics,
        peer_metrics=req.peer_metrics,
    )
    return {"anomalies": anomalies, "count": len(anomalies)}


@router.get("/anomalies")
def get_anomalies(symbol: str | None = None):
    detector = _get_detector()
    anomalies = detector.get_anomalies(symbol=symbol)
    return {"anomalies": anomalies, "count": len(anomalies)}
