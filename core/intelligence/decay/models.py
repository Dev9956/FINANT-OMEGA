"""FININT OMEGA — Information decay models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class DecayFactor(str, Enum):
    EARNINGS_FILING = "earnings_filing"
    NEWS_ARTICLE = "news_article"
    ANALYST_REPORT = "analyst_report"
    MACRO_DATA = "macro_data"
    REGULATORY_FILING = "regulatory_filing"
    MARKET_DATA = "market_data"
    MANAGEMENT_STATEMENT = "management_statement"
    INDUSTRY_REPORT = "industry_report"


class FreshnessScore(BaseModel):
    """Freshness scoring for an evidence item."""
    base_freshness: float = 1.0
    decay_adjusted: float = 1.0
    confirmation_boost: float = 0.0
    final_score: float = 1.0


class EvidenceItem(BaseModel):
    """An evidence item with decay tracking."""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    source: str = ""
    decay_factor: DecayFactor = DecayFactor.NEWS_ARTICLE
    published_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_time: datetime | None = None
    available_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed: bool = False
    confirmation_time: datetime | None = None
    source_quality: float = 0.7
    confidence: float = 0.7
