"""FININT OMEGA — Research scheduler for managing scheduled research jobs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.research.scheduled.models import (
    JobStatus,
    ResearchSchedule,
    ScheduledRun,
    ScheduleFrequency,
)


class ResearchScheduler:
    """Manage research schedules and track runs."""

    def __init__(self) -> None:
        self._schedules: dict[str, ResearchSchedule] = {}
        self._runs: dict[str, list[ScheduledRun]] = {}

    def create_schedule(
        self,
        name: str,
        question: str,
        frequency: ScheduleFrequency = ScheduleFrequency.DAILY,
        time_of_day: str = "09:00",
        timezone: str = "UTC",
    ) -> ResearchSchedule:
        """Create a new research schedule."""
        schedule = ResearchSchedule(
            name=name,
            question=question,
            frequency=frequency,
            time_of_day=time_of_day,
            timezone=timezone,
        )
        schedule.next_run = self.calculate_next_run(schedule)
        self._schedules[schedule.schedule_id] = schedule
        self._runs[schedule.schedule_id] = []
        return schedule

    def update_schedule(self, schedule_id: str, updates: dict) -> ResearchSchedule:
        """Update an existing schedule."""
        if schedule_id not in self._schedules:
            raise KeyError(f"Schedule not found: {schedule_id}")
        schedule = self._schedules[schedule_id]
        for key, value in updates.items():
            if hasattr(schedule, key) and key != "schedule_id":
                setattr(schedule, key, value)
        schedule.next_run = self.calculate_next_run(schedule)
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            self._runs.pop(schedule_id, None)
            return True
        return False

    def get_schedules(self) -> list[ResearchSchedule]:
        """Get all schedules."""
        return list(self._schedules.values())

    def get_due_schedules(self) -> list[ResearchSchedule]:
        """Get schedules that are due to run."""
        now = datetime.now(timezone.utc)
        due = []
        for schedule in self._schedules.values():
            if not schedule.enabled:
                continue
            if schedule.next_run is None:
                due.append(schedule)
            elif schedule.next_run <= now:
                due.append(schedule)
        return due

    def mark_run_complete(self, schedule_id: str, run_id: str, status: JobStatus) -> None:
        """Mark a run as complete and update schedule."""
        if schedule_id not in self._schedules:
            return
        schedule = self._schedules[schedule_id]
        schedule.last_run = datetime.now(timezone.utc)

        if status == JobStatus.COMPLETED and schedule.frequency != ScheduleFrequency.ONCE:
            schedule.next_run = self.calculate_next_run(schedule)
        elif schedule.frequency == ScheduleFrequency.ONCE:
            schedule.enabled = False
            schedule.next_run = None

        runs = self._runs.get(schedule_id, [])
        for run in runs:
            if run.run_id == run_id:
                run.status = status
                run.completed_at = datetime.now(timezone.utc)
                break

    def calculate_next_run(self, schedule: ResearchSchedule) -> datetime | None:
        """Calculate the next run time for a schedule."""
        if schedule.frequency == ScheduleFrequency.ONCE:
            if schedule.last_run is not None:
                return None
            now = datetime.now(timezone.utc)
            hour, minute = map(int, schedule.time_of_day.split(":"))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        now = datetime.now(timezone.utc)
        hour, minute = map(int, schedule.time_of_day.split(":"))

        if schedule.frequency == ScheduleFrequency.DAILY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = 7 - next_run.weekday()
            if days_ahead == 0 and next_run <= now:
                days_ahead = 7
            next_run += timedelta(days=days_ahead)
            return next_run

        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            month = now.month + 1
            year = now.year
            if month > 12:
                month = 1
                year += 1
            return datetime(year, month, 1, hour, minute, 0, tzinfo=timezone.utc)

        elif schedule.frequency == ScheduleFrequency.QUARTERLY:
            month = now.month
            current_quarter = (month - 1) // 3 + 1
            next_quarter = current_quarter + 1
            next_month = (next_quarter - 1) * 3 + 1
            next_year = now.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            return datetime(next_year, next_month, 1, hour, minute, 0, tzinfo=timezone.utc)

        return None

    def get_runs(self, schedule_id: str | None = None) -> list[ScheduledRun]:
        """Get run history, optionally filtered by schedule."""
        if schedule_id:
            return self._runs.get(schedule_id, [])
        all_runs = []
        for runs in self._runs.values():
            all_runs.extend(runs)
        return all_runs
