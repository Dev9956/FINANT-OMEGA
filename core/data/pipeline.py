"""FININT OMEGA — Data pipeline framework: raw → bronze → silver → gold."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class PipelineStatus(str, Enum):
    """Status of a pipeline run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStep(BaseModel):
    """A single step in a data pipeline."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    order: int = 0
    input_columns: list[str] = Field(default_factory=list)
    output_columns: list[str] = Field(default_factory=list)


class PipelineRun(BaseModel):
    """Record of a pipeline execution."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_name: str
    status: PipelineStatus = PipelineStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    input_rows: int | None = None
    output_rows: int | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)


class DataPipeline:
    """Base class for data pipelines with raw→bronze→silver→gold stages."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.steps: list[PipelineStep] = []
        self._runs: list[PipelineRun] = []

    def add_step(self, name: str, description: str = "", order: int | None = None) -> PipelineStep:
        """Add a pipeline step."""
        step_order = order if order is not None else len(self.steps)
        step = PipelineStep(name=name, description=description, order=step_order)
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order)
        return step

    def validate_raw(self, data: dict | list) -> tuple[bool, list[str]]:
        """Validate raw data. Override in subclass."""
        return True, []

    def bronze_transform(self, data: dict | list) -> dict | list:
        """Transform raw → bronze. Override in subclass."""
        return data

    def silver_transform(self, data: dict | list) -> dict | list:
        """Transform bronze → silver. Override in subclass."""
        return data

    def gold_transform(self, data: dict | list) -> dict | list:
        """Transform silver → gold. Override in subclass."""
        return data

    def run(self, raw_data: dict | list) -> PipelineRun:
        """Execute the full pipeline."""
        run = PipelineRun(pipeline_name=self.name, status=PipelineStatus.RUNNING)
        logger.info("pipeline_started", pipeline=self.name, run_id=run.run_id)

        try:
            # Validate raw
            valid, errors = self.validate_raw(raw_data)
            if not valid:
                run.status = PipelineStatus.FAILED
                run.error_message = f"Raw validation failed: {errors}"
                logger.error("pipeline_validation_failed", errors=errors)
                return run

            # Bronze
            bronze_data = self.bronze_transform(raw_data)
            logger.info("pipeline_bronze_complete", pipeline=self.name)

            # Silver
            silver_data = self.silver_transform(bronze_data)
            logger.info("pipeline_silver_complete", pipeline=self.name)

            # Gold
            gold_data = self.gold_transform(silver_data)
            logger.info("pipeline_gold_complete", pipeline=self.name)

            run.status = PipelineStatus.COMPLETED
            run.completed_at = datetime.now(timezone.utc)
            if isinstance(gold_data, list):
                run.output_rows = len(gold_data)

        except Exception as e:
            run.status = PipelineStatus.FAILED
            run.error_message = str(e)
            logger.error("pipeline_failed", error=str(e))

        self._runs.append(run)
        return run

    def get_runs(self) -> list[PipelineRun]:
        """Get all pipeline run records."""
        return list(self._runs)
