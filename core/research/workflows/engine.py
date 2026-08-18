"""FININT OMEGA — Research workflow engine for orchestrating multi-step research."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep(BaseModel):
    """A single step in a research workflow."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tool_name: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None
    order: int = 0
    depends_on: list[str] = Field(default_factory=list)


class WorkflowRun(BaseModel):
    """Record of a workflow execution."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    steps: list[WorkflowStep] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    results: dict[str, Any] = Field(default_factory=dict)


class ResearchWorkflowEngine:
    """Define and execute multi-step research workflows."""

    def __init__(self) -> None:
        self._workflows: dict[str, list[WorkflowStep]] = {}
        self._tool_handlers: dict[str, callable] = {}

    def register_tool(self, name: str, handler: callable) -> None:
        self._tool_handlers[name] = handler

    def define_workflow(self, name: str, steps: list[WorkflowStep]) -> None:
        self._workflows[name] = sorted(steps, key=lambda s: s.order)

    def list_workflows(self) -> list[str]:
        return list(self._workflows.keys())

    def _dependencies_met(self, step: WorkflowStep, completed: set[str]) -> bool:
        return all(dep in completed for dep in step.depends_on)

    def execute(self, workflow_name: str, initial_context: dict | None = None) -> WorkflowRun:
        steps = self._workflows.get(workflow_name, [])
        if not steps:
            return WorkflowRun(name=workflow_name, status=StepStatus.FAILED)

        run = WorkflowRun(name=workflow_name, steps=[s.model_copy() for s in steps], status=StepStatus.RUNNING)
        completed: set[str] = set()
        context: dict[str, Any] = dict(initial_context or {})

        for step in run.steps:
            if not self._dependencies_met(step, completed):
                step.status = StepStatus.SKIPPED
                continue

            step.status = StepStatus.RUNNING
            handler = self._tool_handlers.get(step.tool_name)
            if handler is None:
                step.status = StepStatus.FAILED
                step.error = f"Tool '{step.tool_name}' not registered"
                continue

            try:
                result = handler(**step.parameters, context=context)
                step.result = result
                step.status = StepStatus.COMPLETED
                completed.add(step.step_id)
                context[step.step_id] = result
                run.results[step.name] = result
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)

        run.status = StepStatus.COMPLETED if all(s.status == StepStatus.COMPLETED for s in run.steps) else StepStatus.FAILED
        run.completed_at = datetime.now(timezone.utc)
        return run
