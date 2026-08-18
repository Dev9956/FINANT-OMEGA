"""FININT OMEGA — Workflow Agent Framework: base agent classes and models."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Available agent roles."""

    COMPANY_ANALYST = "company_analyst"
    EARNINGS_ANALYST = "earnings_analyst"
    VALUATION_ANALYST = "valuation_analyst"
    INDUSTRY_ANALYST = "industry_analyst"
    MACRO_ANALYST = "macro_analyst"
    PORTFOLIO_RISK_ANALYST = "portfolio_risk_analyst"
    COMPETITOR_ANALYST = "competitor_analyst"
    THESIS_MONITOR = "thesis_monitor"
    DUE_DILIGENCE = "due_diligence"
    RESEARCH_SYNTHESIS = "research_synthesis"


class EvidencePolicy(str, Enum):
    """Policy for handling evidence."""

    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    role: AgentRole
    allowed_tools: list[str] = Field(default_factory=list)
    max_tokens: int = Field(default=4096, ge=256, le=100_000)
    timeout_seconds: int = Field(default=120, ge=10, le=3600)
    retry_count: int = Field(default=3, ge=0, le=10)
    evidence_policy: EvidencePolicy = EvidencePolicy.MODERATE
    metadata: dict = Field(default_factory=dict)


class AgentInput(BaseModel):
    """Input for an agent execution."""

    research_id: str = ""
    question: str
    context: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    config: AgentConfig | None = None


class AgentOutput(BaseModel):
    """Output from an agent execution."""

    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: AgentRole = AgentRole.COMPANY_ANALYST
    answer: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning_summary: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseAgent(ABC):
    """Abstract base class for all research agents."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(role=self.default_role())
        self._config = config

    @abstractmethod
    def default_role(self) -> AgentRole:
        """Return the default agent role."""
        ...

    @abstractmethod
    def execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent on the given input."""
        ...

    @property
    def role(self) -> AgentRole:
        return self._config.role

    @property
    def config(self) -> AgentConfig:
        return self._config

    def _validate_input(self, input_data: AgentInput) -> None:
        """Validate input data."""
        if not input_data.question or not input_data.question.strip():
            raise ValueError("Agent input question cannot be empty")

    def _build_output(
        self,
        input_data: AgentInput,
        answer: str,
        confidence: float = 0.5,
        reasoning: str = "",
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> AgentOutput:
        """Build a standardized AgentOutput."""
        return AgentOutput(
            role=self._config.role,
            answer=answer,
            confidence=confidence,
            reasoning_summary=reasoning,
            tool_calls=tool_calls or [],
            metadata={"question": input_data.question},
        )
