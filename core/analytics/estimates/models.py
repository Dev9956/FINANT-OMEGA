"""FININT OMEGA — Estimate revisions Pydantic models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EstimateRecord(BaseModel):
    """A single estimate record from an analyst."""

    estimate_id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    metric: str
    period_end: date
    actual_value: float | None = None
    estimate_value: float | None = None
    consensus_value: float | None = None
    estimate_high: float | None = None
    estimate_low: float | None = None
    previous_estimate: float | None = None
    revision_count: int = 0
    source: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EPSRecord(BaseModel):
    """EPS-specific estimate record."""

    symbol: str
    period_end: date
    eps_actual: float | None = None
    eps_estimate: float | None = None
    eps_consensus: float | None = None
    eps_previous_estimate: float | None = None
    revision_count: int = 0


class RevenueRecord(BaseModel):
    """Revenue-specific estimate record."""

    symbol: str
    period_end: date
    revenue_actual: float | None = None
    revenue_estimate: float | None = None
    revenue_consensus: float | None = None
    revision_count: int = 0


class EstimateRevision(BaseModel):
    """A detected estimate revision."""

    symbol: str
    metric: str
    old_estimate: float
    new_estimate: float
    revision_pct: float
    revision_date: date
    analyst_count: int = 0


class SurpriseType(str, Enum):
    """Classification of earnings surprise."""

    beat = "beat"
    miss = "miss"
    inline = "inline"


class SurpriseMagnitude(str, Enum):
    """Magnitude of surprise."""

    slight = "slight"
    moderate = "moderate"
    significant = "significant"


class SurpriseResult(BaseModel):
    """Result of surprise computation."""

    symbol: str
    period_end: date
    eps_surprise_pct: float | None = None
    revenue_surprise_pct: float | None = None
    surprise_type: SurpriseType = SurpriseType.inline
    magnitude: SurpriseMagnitude = SurpriseMagnitude.slight


class RevisionMomentum(BaseModel):
    """Momentum score from estimate revisions."""

    symbol: str
    upward_revisions: int = 0
    downward_revisions: int = 0
    net_revisions: int = 0
    momentum_score: float = 0.0
