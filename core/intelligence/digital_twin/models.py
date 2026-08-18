"""FININT OMEGA — Digital twin models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TwinSnapshot(BaseModel):
    """A snapshot of the digital twin state."""
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    financials: dict[str, float] = Field(default_factory=dict)
    market: dict[str, float] = Field(default_factory=dict)
    valuation: dict[str, float] = Field(default_factory=dict)
    risk: dict[str, float] = Field(default_factory=dict)
    thesis: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TwinScenario(BaseModel):
    """A scenario applied to the digital twin."""
    scenario_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    changes: dict[str, float] = Field(default_factory=dict)
    affected_metrics: dict[str, float] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = 0.5


class DigitalTwin(BaseModel):
    """A dynamic representation of a company/asset."""
    twin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity: str
    name: str = ""
    snapshots: list[TwinSnapshot] = Field(default_factory=list)
    scenarios: list[TwinScenario] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
