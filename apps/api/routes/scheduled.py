"""FININT OMEGA — Scheduled research API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.research.scheduled.executor import ScheduledExecutor
from core.research.scheduled.models import JobStatus, ResearchSchedule, ScheduleFrequency
from core.research.scheduled.scheduler import ResearchScheduler

router = APIRouter(prefix="/api/v1/scheduled", tags=["scheduled"])

_scheduler = ResearchScheduler()
_executor = ScheduledExecutor()


class ScheduleCreateRequest(BaseModel):
    """Request body for creating a schedule."""

    name: str
    question: str
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    time_of_day: str = "09:00"
    timezone: str = "UTC"


class ScheduleUpdateRequest(BaseModel):
    """Request body for updating a schedule."""

    name: str | None = None
    question: str | None = None
    frequency: ScheduleFrequency | None = None
    time_of_day: str | None = None
    timezone: str | None = None
    enabled: bool | None = None


@router.post("")
async def create_schedule(request: ScheduleCreateRequest) -> dict:
    """Create a new research schedule."""
    schedule = _scheduler.create_schedule(
        name=request.name,
        question=request.question,
        frequency=request.frequency,
        time_of_day=request.time_of_day,
        timezone=request.timezone,
    )
    return schedule.model_dump(mode="json")


@router.get("")
async def list_schedules() -> list[dict]:
    """List all research schedules."""
    return [s.model_dump(mode="json") for s in _scheduler.get_schedules()]


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: str, request: ScheduleUpdateRequest) -> dict:
    """Update an existing schedule."""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    try:
        schedule = _scheduler.update_schedule(schedule_id, updates)
        return schedule.model_dump(mode="json")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str) -> dict:
    """Delete a research schedule."""
    deleted = _scheduler.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")
    return {"deleted": True, "schedule_id": schedule_id}


@router.post("/{schedule_id}/run")
async def trigger_run(schedule_id: str) -> dict:
    """Trigger an immediate run of a schedule."""
    schedules = _scheduler.get_schedules()
    schedule = next((s for s in schedules if s.schedule_id == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")
    run = _executor.execute_schedule(schedule)
    _scheduler.mark_run_complete(schedule_id, run.run_id, run.status)
    return run.model_dump(mode="json")


@router.get("/runs")
async def get_runs(schedule_id: str | None = None) -> list[dict]:
    """Get run history."""
    runs = _scheduler.get_runs(schedule_id)
    return [r.model_dump(mode="json") for r in runs]
