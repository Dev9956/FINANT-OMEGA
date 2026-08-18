"""FININT OMEGA — Scenario analysis models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ImpactDirection(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class ScenarioVariable(BaseModel):
    """A variable in the scenario."""
    variable_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    current_value: float
    scenario_value: float
    unit: str = ""
    change_pct: float = 0.0


class VariableChange(BaseModel):
    """Impact of a variable change."""
    variable_name: str
    original_value: float
    new_value: float
    change_pct: float
    impacted_metrics: list[str] = Field(default_factory=list)
    impact_direction: ImpactDirection = ImpactDirection.NEUTRAL


class ScenarioConfig(BaseModel):
    """Configuration for scenario analysis."""
    include_dependencies: bool = True
    max_depth: int = 3
    show_assumptions: bool = True


class ScenarioResult(BaseModel):
    """Result of scenario analysis."""
    scenario_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    variables: list[ScenarioVariable] = Field(default_factory=list)
    variable_changes: list[VariableChange] = Field(default_factory=list)
    affected_metrics: dict[str, float] = Field(default_factory=dict)
    bull_base_bear: dict[str, dict] = Field(default_factory=dict)
    risk_assessment: str = ""
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    summary: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
