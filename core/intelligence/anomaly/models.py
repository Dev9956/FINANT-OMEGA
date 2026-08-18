"""FININT OMEGA — Anomaly detection models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    RATIO_DIVERGENCE = "ratio_divergence"
    WORKING_CAPITAL = "working_capital"
    CASHFLOW_DIVERGENCE = "cashflow_divergence"
    MARGIN_ANOMALY = "margin_anomaly"
    DEBT_MOVEMENT = "debt_movement"
    VALUATION_ANOMALY = "valuation_anomaly"
    TRADING_ANOMALY = "trading_anomaly"
    PEER_RELATIVE = "peer_relative"


class AnomalyScore(BaseModel):
    """Scoring breakdown for an anomaly."""
    statistical_score: float = 0.0
    peer_score: float = 0.0
    historical_score: float = 0.0
    overall_score: float = 0.0


class AnomalyItem(BaseModel):
    """A detected financial anomaly."""
    anomaly_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    anomaly_type: AnomalyType
    score: AnomalyScore
    affected_metrics: list[str] = Field(default_factory=list)
    description: str = ""
    historical_context: str = ""
    peer_context: str = ""
    evidence: list[str] = Field(default_factory=list)
    investigation_priority: str = "medium"
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
