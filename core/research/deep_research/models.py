"""FININT OMEGA — Deep Research Engine: core data models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ResearchStatus(str, Enum):
    """Status of a research run."""

    PENDING = "pending"
    PLANNING = "planning"
    RESEARCHING = "researching"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchDepth(str, Enum):
    """Depth level for research."""

    SHALLOW = "shallow"
    STANDARD = "standard"
    DEEP = "deep"


class ResearchConfig(BaseModel):
    """Configuration for a deep research run."""

    depth: ResearchDepth = ResearchDepth.STANDARD
    max_tasks: int = Field(default=8, ge=1, le=100)
    max_sources: int = Field(default=50, ge=1, le=1000)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    budget_tokens: int = Field(default=100_000, ge=1_000, le=10_000_000)

    @classmethod
    def for_depth(cls, depth: ResearchDepth) -> ResearchConfig:
        """Create a config preset for a given depth."""
        presets = {
            ResearchDepth.SHALLOW: cls(depth=depth, max_tasks=3, max_sources=10, timeout_seconds=60, budget_tokens=20_000),
            ResearchDepth.STANDARD: cls(depth=depth, max_tasks=8, max_sources=30, timeout_seconds=300, budget_tokens=100_000),
            ResearchDepth.DEEP: cls(depth=depth, max_tasks=15, max_sources=100, timeout_seconds=900, budget_tokens=500_000),
        }
        return presets[depth]


class TaskStatus(str, Enum):
    """Status of a single research task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ResearchTask(BaseModel):
    """A single task within a research run."""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    status: TaskStatus = TaskStatus.PENDING
    sub_questions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    result: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    """A single piece of evidence collected during research."""

    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = Field(description="e.g. market_data, fundamentals, news, filing")
    source_id: str = Field(description="Identifier of the source")
    content: str = Field(description="The evidence content or summary")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    supports_claim: str | None = Field(default=None, description="Claim this evidence supports")
    contradicts_claim: str | None = Field(default=None, description="Claim this evidence contradicts")
    metadata: dict = Field(default_factory=dict)


class ConflictStatus(str, Enum):
    """Status of a conflict resolution."""

    UNRESOLVED = "unresolved"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IRREDUCIBLE = "irreducible"


class ConflictItem(BaseModel):
    """A conflict between two pieces of evidence."""

    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_a: str
    claim_b: str
    evidence_a_ids: list[str] = Field(default_factory=list)
    evidence_b_ids: list[str] = Field(default_factory=list)
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    resolution: str | None = None
    resolution_status: ConflictStatus = ConflictStatus.UNRESOLVED
    metadata: dict = Field(default_factory=dict)


class ResearchSynthesis(BaseModel):
    """Final synthesis of a research run."""

    synthesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    research_id: str
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    methodology: str = ""
    claims: list[str] = Field(default_factory=list, description="Key claims in the synthesis")
    metadata: dict = Field(default_factory=dict)


class ResearchRun(BaseModel):
    """A complete deep research run."""

    research_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    status: ResearchStatus = ResearchStatus.PENDING
    config: ResearchConfig = Field(default_factory=ResearchConfig)
    tasks: list[ResearchTask] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)
    synthesis: ResearchSynthesis | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
