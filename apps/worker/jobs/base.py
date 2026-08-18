"""FININT OMEGA — Base job classes for the worker system."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobResult(BaseModel):
    """Result of a job execution."""

    job_id: str
    status: JobStatus
    output: dict = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    metadata: dict = Field(default_factory=dict)


class BaseJob(ABC):
    """Abstract base class for all worker jobs."""

    def __init__(self, job_id: str | None = None, name: str = "unnamed_job") -> None:
        self.job_id = job_id or str(uuid.uuid4())
        self.name = name
        self.status = JobStatus.PENDING
        self.created_at = datetime.now(timezone.utc)

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """Execute the job. Must be overridden by subclasses."""
        ...

    def run(self, **kwargs) -> JobResult:
        """Run the job with error handling and timing."""
        self.status = JobStatus.RUNNING
        started = datetime.now(timezone.utc)
        try:
            output = self.execute(**kwargs)
            self.status = JobStatus.COMPLETED
            completed = datetime.now(timezone.utc)
            return JobResult(
                job_id=self.job_id,
                status=JobStatus.COMPLETED,
                output=output or {},
                started_at=started,
                completed_at=completed,
                duration_ms=(completed - started).total_seconds() * 1000,
            )
        except Exception as e:
            self.status = JobStatus.FAILED
            completed = datetime.now(timezone.utc)
            return JobResult(
                job_id=self.job_id,
                status=JobStatus.FAILED,
                error=str(e),
                started_at=started,
                completed_at=completed,
                duration_ms=(completed - started).total_seconds() * 1000,
            )

    def cancel(self) -> None:
        self.status = JobStatus.CANCELLED

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
