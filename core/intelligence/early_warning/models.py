"""FININT OMEGA — Early warning models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class WarningCategory(str, Enum):
    REVENUE_DETERIORATION = "revenue_deterioration"
    MARGIN_COMPRESSION = "margin_compression"
    CASHFLOW_DIVERGENCE = "cashflow_divergence"
    LEVERAGE_INCREASE = "leverage_increase"
    INVENTORY_BUILDUP = "inventory_buildup"
    RECEIVABLES_GROWTH = "receivables_growth"
    GUIDANCE_CUT = "guidance_cut"
    EARNINGS_REVISION = "earnings_revision"
    VALUATION_EXTREME = "valuation_extreme"
    UNUSUAL_VOLUME = "unusual_volume"
    SENTIMENT_SHIFT = "sentiment_shift"
    GOVERNANCE_SIGNAL = "governance_signal"


class WarningSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EarlyWarning(BaseModel):
    """An early warning signal."""
    warning_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    category: WarningCategory
    severity: WarningSeverity
    indicator: str
    current_value: float
    threshold: float
    deviation_pct: float = 0.0
    description: str
    evidence: list[str] = Field(default_factory=list)
    recommended_investigation: str = ""
    confidence: float = 0.7
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
