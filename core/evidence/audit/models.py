"""FININT OMEGA — Audit trail Pydantic models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of audit events."""

    research_started = "research_started"
    task_completed = "task_completed"
    evidence_collected = "evidence_collected"
    evidence_verified = "evidence_verified"
    tool_called = "tool_called"
    model_called = "model_called"
    error_occurred = "error_occurred"
    research_completed = "research_completed"


class AuditEvent(BaseModel):
    """A single audit event."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    research_id: str
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditTrail(BaseModel):
    """Complete audit trail for a research session."""

    research_id: str
    events: list[AuditEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolCallRecord(BaseModel):
    """Record of a tool invocation."""

    tool_name: str
    arguments_hash: str
    result_hash: str
    duration_ms: float
    success: bool
    error_message: str | None = None


class ModelCallRecord(BaseModel):
    """Record of an LLM call."""

    model_id: str
    prompt_hash: str
    response_hash: str
    tokens_used: int = 0
    duration_ms: float = 0.0
    cost: float = 0.0


class ExecutionMetadata(BaseModel):
    """Metadata about the execution environment."""

    planner_version: str = "0.1.0"
    agent_versions: dict[str, str] = Field(default_factory=dict)
    llm_config: dict[str, Any] = Field(default_factory=dict)
    tools_used: list[str] = Field(default_factory=list)
    data_versions: dict[str, str] = Field(default_factory=dict)
    document_versions: dict[str, str] = Field(default_factory=dict)
