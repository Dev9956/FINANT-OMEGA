"""FININT OMEGA — Research loop models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class LoopPhase(str, Enum):
    OBSERVE = "observe"
    DETECT = "detect"
    INVESTIGATE = "investigate"
    HYPOTHESIZE = "hypothesize"
    TEST = "test"
    VERIFY = "verify"
    CONCLUDE = "conclude"
    PREDICT = "predict"
    MONITOR = "monitor"
    MEASURE = "measure"
    CALIBRATE = "calibrate"
    UPDATE = "update"


class LoopStep(BaseModel):
    """A single step in the research loop."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phase: LoopPhase
    description: str
    input_data: dict = Field(default_factory=dict)
    output_data: dict = Field(default_factory=dict)
    status: str = "pending"
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchIteration(BaseModel):
    """One complete iteration of the research loop."""
    iteration_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    steps: list[LoopStep] = Field(default_factory=list)
    current_phase: LoopPhase = LoopPhase.OBSERVE
    findings: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    status: str = "running"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class LoopConfig(BaseModel):
    """Configuration for the research loop."""
    max_steps: int = 50
    max_iterations: int = 5
    timeout_seconds: float = 300.0
    allowed_tools: list[str] = Field(default_factory=list)
    stopping_conditions: list[str] = Field(default_factory=list)
    max_cost: float = 100.0


class LoopResult(BaseModel):
    """Final result of the research loop."""
    loop_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    iterations: list[ResearchIteration] = Field(default_factory=list)
    final_findings: list[str] = Field(default_factory=list)
    final_hypotheses: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    total_steps: int = 0
    status: str = "completed"
    audit_trail: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
