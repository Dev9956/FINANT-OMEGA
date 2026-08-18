"""FININT OMEGA — Scheduled research models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ScheduleFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY_PENDING = "retry_pending"


class ResearchSchedule(BaseModel):
    """A scheduled research job definition."""

    schedule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    question: str
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    time_of_day: str = "09:00"
    timezone: str = "UTC"
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class ScheduledRun(BaseModel):
    """Record of a scheduled research run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    schedule_id: str
    research_id: str = ""
    status: JobStatus = JobStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0
