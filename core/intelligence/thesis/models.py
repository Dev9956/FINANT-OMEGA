"""FININT OMEGA — Thesis models with versioning, triggers, and invalidation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ThesisStatus(str, Enum):
    ACTIVE = "active"
    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    INVALIDATED = "invalidated"
    CLOSED = "closed"


class ThesisConfidence(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class TriggerType(str, Enum):
    METRIC_THRESHOLD = "metric_threshold"
    EVIDENCE_ADDITION = "evidence_addition"
    EVIDENCE_REMOVAL = "evidence_removal"
    STATUS_CHANGE = "status_change"
    CONFIDENCE_CHANGE = "confidence_change"
    TIME_BASED = "time_based"


class InvalidationCondition(BaseModel):
    """Condition that would invalidate the thesis."""
    condition_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    metric: str = ""
    threshold: float = 0.0
    comparator: str = "lt"  # lt, gt, eq, lte, gte
    consecutive_periods: int = 1
    currently_met: bool = False
    periods_met: int = 0


class ThesisTrigger(BaseModel):
    """A trigger condition for thesis evaluation."""
    trigger_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_type: TriggerType
    description: str
    metric: str = ""
    threshold: float = 0.0
    direction: str = "above"  # above, below
    enabled: bool = True
    fired: bool = False
    fired_at: datetime | None = None


class ThesisVersion(BaseModel):
    """A versioned snapshot of a thesis."""
    version_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version_number: int
    thesis_id: str
    title: str
    bull_case: str
    base_case: str = ""
    bear_case: str
    key_drivers: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.7
    confidence_level: ThesisConfidence = ThesisConfidence.MODERATE
    status: ThesisStatus = ThesisStatus.ACTIVE
    time_horizon: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    change_summary: str = ""
    change_reason: str = ""


class ThesisUpdate(BaseModel):
    """Record of a thesis update."""
    update_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thesis_id: str
    from_version: int
    to_version: int
    changes: list[str] = Field(default_factory=list)
    evidence_added: list[str] = Field(default_factory=list)
    evidence_removed: list[str] = Field(default_factory=list)
    confidence_change: float = 0.0
    status_change: ThesisStatus | None = None
    reason: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThesisEvaluation(BaseModel):
    """Result of evaluating a thesis."""
    thesis_id: str
    health: str  # strengthening, weakening, stable, invalidated
    confidence: float
    confidence_change: float
    status: ThesisStatus
    supporting_count: int = 0
    contradicting_count: int = 0
    triggers_fired: list[str] = Field(default_factory=list)
    invalidation_met: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThesisEvolution(BaseModel):
    """Timeline of thesis changes."""
    thesis_id: str
    versions: list[ThesisVersion] = Field(default_factory=list)
    updates: list[ThesisUpdate] = Field(default_factory=list)
    total_versions: int = 0
    confidence_trend: list[float] = Field(default_factory=list)
    status_history: list[str] = Field(default_factory=list)
