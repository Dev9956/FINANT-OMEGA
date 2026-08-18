"""FININT OMEGA — Company monitoring models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class MonitorMetric(str, Enum):
    """Types of metrics to monitor for a company."""

    PRICE = "price"
    VALUATION = "valuation"
    FINANCIALS = "financials"
    EARNINGS = "earnings"
    GUIDANCE = "guidance"
    ESTIMATES = "estimates"
    NEWS = "news"
    FILINGS = "filings"
    MANAGEMENT = "management"
    RISK = "risk"
    THESIS = "thesis"


class MaterialityLevel(str, Enum):
    """Materiality classification for a state diff."""

    NORMAL = "normal"
    NOTABLE = "notable"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


class CompanyState(BaseModel):
    """Snapshot of a company's monitored metrics at a point in time."""

    symbol: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict = Field(default_factory=dict, description="Map of metric name to value")
    snapshot_version: int = 1


class StateDiff(BaseModel):
    """A detected change between two company states for a single metric."""

    symbol: str
    metric: str
    old_value: object
    new_value: object
    change_pct: float = 0.0
    is_material: bool = False
    materiality_score: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MonitoringAlert(BaseModel):
    """An alert generated when a material change is detected."""

    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    metric: str
    diff: StateDiff
    materiality: MaterialityLevel = MaterialityLevel.NORMAL
    thesis_impact: str = "neutral"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
