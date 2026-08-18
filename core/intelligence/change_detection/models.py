"""FININT OMEGA — Advanced change detection models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Types of changes that can be detected."""

    NUMERICAL = "numerical"
    TEXTUAL = "textual"
    STRUCTURAL = "structural"
    SENTIMENT = "sentiment"
    GUIDANCE = "guidance"
    RISK = "risk"
    OUTLOOK = "outlook"


class ChangeSeverity(str, Enum):
    """Severity classification for detected changes."""

    TRIVIAL = "trivial"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class DetectedChange(BaseModel):
    """A single detected change between two data snapshots."""

    change_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    change_type: ChangeType
    severity: ChangeSeverity = ChangeSeverity.TRIVIAL
    field: str
    old_value: object
    new_value: object
    change_pct: float = 0.0
    evidence: str = ""
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComparisonResult(BaseModel):
    """Result of comparing two periods of data."""

    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_a: str
    entity_b: str
    period_a: str
    period_b: str
    changes: list[DetectedChange] = Field(default_factory=list)
    overall_significance: float = 0.0
    summary: str = ""
