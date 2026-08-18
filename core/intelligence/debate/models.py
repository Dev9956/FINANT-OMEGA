"""FININT OMEGA — Debate engine models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AnalystRole(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"
    EVIDENCE_VERIFIER = "evidence_verifier"
    SYNTHESIS_JUDGE = "synthesis_judge"


class AnalystArgument(BaseModel):
    """An argument from one analyst."""
    analyst_role: AnalystRole
    thesis: str
    key_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    risks_identified: list[str] = Field(default_factory=list)
    catalysts_identified: list[str] = Field(default_factory=list)


class EvidenceVerification(BaseModel):
    """Verification of evidence quality."""
    evidence_item: str
    verified: bool = False
    source_quality: float = 0.0
    corroboration_count: int = 0
    contradiction_count: int = 0
    notes: str = ""


class SynthesisResult(BaseModel):
    """Final synthesis from the judge."""
    conclusion: str
    bull_argument: str
    bear_argument: str
    evidence_quality_score: float = 0.0
    key_consensus: list[str] = Field(default_factory=list)
    key_disputes: list[str] = Field(default_factory=list)
    final_confidence: float = 0.0
    dissenting_views: list[str] = Field(default_factory=list)
    recommended_action: str = ""
    risk_assessment: str = ""


class DebateConfig(BaseModel):
    """Configuration for a debate run."""
    max_evidence_per_analyst: int = 10
    min_evidence_threshold: int = 3
    confidence_threshold: float = 0.6
    enable_evidence_verification: bool = True


class DebateResult(BaseModel):
    """Complete result of a debate."""
    debate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    bull_argument: AnalystArgument | None = None
    bear_argument: AnalystArgument | None = None
    neutral_verification: list[EvidenceVerification] = Field(default_factory=list)
    synthesis: SynthesisResult | None = None
    evidence_items: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
