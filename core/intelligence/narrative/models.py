"""FININT OMEGA — Narrative vs Numbers models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AlignmentLevel(str, Enum):
    HIGH_ALIGNMENT = "high_alignment"
    MODERATE_ALIGNMENT = "moderate_alignment"
    LOW_ALIGNMENT = "low_alignment"
    INSUFFICIENT_DATA = "insufficient_data"


class NarrativeComponent(BaseModel):
    """A component extracted from narrative text."""
    component_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    component_type: str  # growth, risk, catalyst, concern, neutral
    sentiment: float = 0.0  # -1 to 1
    keywords: list[str] = Field(default_factory=list)


class QuantitativeSignal(BaseModel):
    """A quantitative signal from financial data."""
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric: str
    current_value: float
    previous_value: float | None = None
    change_pct: float = 0.0
    direction: str = "up"  # up, down, flat
    significance: str = "moderate"  # significant, moderate, minor


class NarrativeAnalysis(BaseModel):
    """Result of narrative vs numbers comparison."""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    narrative: str
    alignment_level: AlignmentLevel
    alignment_score: float = 0.0  # 0-1
    narrative_components: list[NarrativeComponent] = Field(default_factory=list)
    quantitative_signals: list[QuantitativeSignal] = Field(default_factory=list)
    supporting_signals: list[str] = Field(default_factory=list)
    conflicting_signals: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    summary: str = ""
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
