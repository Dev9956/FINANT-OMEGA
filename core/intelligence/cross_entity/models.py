"""FININT OMEGA — Cross-entity intelligence models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class RankingCriterion(str, Enum):
    EARNINGS_MOMENTUM = "earnings_momentum"
    CASHFLOW_QUALITY = "cashflow_quality"
    VALUATION = "valuation"
    GROWTH = "growth"
    THESIS_HEALTH = "thesis_health"
    RISK = "risk"
    COMPOSITE = "composite"


class EntityMetrics(BaseModel):
    """Metrics for a single entity."""
    entity_id: str
    symbol: str
    name: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)
    thesis_health: str = ""
    anomaly_score: float = 0.0
    warning_count: int = 0
    rank_score: float = 0.0


class RankingResult(BaseModel):
    """Ranking of entities by a criterion."""
    criterion: RankingCriterion
    rankings: list[EntityMetrics] = Field(default_factory=list)
    total_entities: int = 0


class CrossEntityRequest(BaseModel):
    """Request for cross-entity analysis."""
    symbols: list[str]
    criteria: list[RankingCriterion] = Field(default_factory=lambda: [RankingCriterion.COMPOSITE])
    filters: dict[str, dict] = Field(default_factory=dict)
    max_results: int = 50


class CrossEntityResult(BaseModel):
    """Result of cross-entity analysis."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: CrossEntityRequest
    rankings: list[RankingResult] = Field(default_factory=list)
    summary: str = ""
    entities_analyzed: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
