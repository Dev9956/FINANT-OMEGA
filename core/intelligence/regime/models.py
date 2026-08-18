"""FININT OMEGA — Regime detection models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class MarketRegime(str, Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    INFLATIONARY = "inflationary"
    DEFLATIONARY = "deflationary"
    STAGFLATION = "stagflation"
    HIGH_GROWTH = "high_growth"
    RECESSION = "recession"
    LIQUIDITY_STRESS = "liquidity_stress"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class RegimeConfidence(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class RegimeSignal(BaseModel):
    """A signal contributing to regime classification."""
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    indicator: str
    value: float
    threshold: float = 0.0
    direction: str = "bullish"  # bullish, bearish, neutral
    weight: float = 1.0
    description: str = ""


class RegimeResult(BaseModel):
    """Result of regime detection."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    regime: MarketRegime
    confidence: RegimeConfidence
    confidence_score: float = 0.0
    signals: list[RegimeSignal] = Field(default_factory=list)
    supporting_signals: list[str] = Field(default_factory=list)
    conflicting_signals: list[str] = Field(default_factory=list)
    historical_similar: list[str] = Field(default_factory=list)
    summary: str = ""
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
