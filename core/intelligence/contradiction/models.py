"""FININT OMEGA — Contradiction detection models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ContradictionCategory(str, Enum):
    MANAGEMENT_VS_FINANCIALS = "management_vs_financials"
    GUIDANCE_VS_ACTUAL = "guidance_vs_actual"
    NARRATIVE_VS_MARKET = "narrative_vs_market"
    THESIS_VS_EVIDENCE = "thesis_vs_evidence"
    VALUATION_VS_GROWTH = "valuation_vs_growth"
    EARNINGS_VS_CASHFLOW = "earnings_vs_cashflow"
    PEER_COMPARISON = "peer_comparison"
    TEMPORAL_DIVERGENCE = "temporal_divergence"


class ContradictionSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INFO = "info"


class EvidenceConflict(BaseModel):
    """A conflict between two pieces of evidence."""
    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_a: str
    evidence_b: str
    category: ContradictionCategory
    severity: ContradictionSeverity
    description: str
    metric: str = ""
    value_a: float | None = None
    value_b: float | None = None
    deviation_pct: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContradictionItem(BaseModel):
    """A detected contradiction."""
    contradiction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: ContradictionCategory
    severity: ContradictionSeverity
    statement: str
    conflicting_evidence: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    description: str = ""
    requires_investigation: bool = False
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContradictionResult(BaseModel):
    """Result of contradiction detection."""
    entity: str
    contradictions_found: int = 0
    contradictions: list[ContradictionItem] = Field(default_factory=list)
    conflicts: list[EvidenceConflict] = Field(default_factory=list)
    overall_severity: ContradictionSeverity = ContradictionSeverity.INFO
    summary: str = ""
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
