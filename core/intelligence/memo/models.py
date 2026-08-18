"""FININT OMEGA — Investment memo models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MemoSection(BaseModel):
    """A section of the investment memo."""
    section_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.5


class InvestmentMemo(BaseModel):
    """A structured investment memo."""
    memo_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity: str
    title: str = ""
    executive_summary: MemoSection | None = None
    thesis: MemoSection | None = None
    bull_case: MemoSection | None = None
    bear_case: MemoSection | None = None
    base_case: MemoSection | None = None
    valuation: MemoSection | None = None
    financial_quality: MemoSection | None = None
    risks: MemoSection | None = None
    contradicting_evidence: MemoSection | None = None
    scenario_analysis: MemoSection | None = None
    what_would_change_my_mind: MemoSection | None = None
    evidence_limitations: MemoSection | None = None
    confidence: float = 0.5
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))