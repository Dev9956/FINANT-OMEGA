"""Tests for the Scheduled Research module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.research.scheduled.executor import ScheduledExecutor
from core.research.scheduled.models import JobStatus, ScheduleFrequency
from core.research.scheduled.scheduler import ResearchScheduler


class TestResearchScheduler:
    """Tests for ResearchScheduler."""

    def setup_method(self) -> None:
        self.scheduler = ResearchScheduler()

    def test_create_schedule(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="Daily Tech Check",
            question="What changed in tech stocks?",
            frequency=ScheduleFrequency.DAILY,
        )
        assert schedule.name == "Daily Tech Check"
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.next_run is not None

    def test_create_once_schedule(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="One-time",
            question="Check MSFT",
            frequency=ScheduleFrequency.ONCE,
        )
        assert schedule.frequency == ScheduleFrequency.ONCE

    def test_update_schedule(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="Original",
            question="Question",
            frequency=ScheduleFrequency.DAILY,
        )
        updated = self.scheduler.update_schedule(
            schedule.schedule_id,
            {"name": "Updated Name"},
        )
        assert updated.name == "Updated Name"

    def test_delete_schedule(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="To Delete",
            question="Question",
        )
        assert self.scheduler.delete_schedule(schedule.schedule_id) is True
        assert self.scheduler.delete_schedule(schedule.schedule_id) is False

    def test_get_schedules(self) -> None:
        self.scheduler.create_schedule("S1", "Q1")
        self.scheduler.create_schedule("S2", "Q2")
        schedules = self.scheduler.get_schedules()
        assert len(schedules) == 2

    def test_get_due_schedules(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="Past Due",
            question="Q",
            frequency=ScheduleFrequency.DAILY,
            time_of_day="00:00",
        )
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        schedule.next_run = now - timedelta(hours=1)
        due = self.scheduler.get_due_schedules()
        assert len(due) >= 1

    def test_mark_run_complete(self) -> None:
        from core.research.scheduled.models import ScheduledRun

        schedule = self.scheduler.create_schedule("S", "Q")
        run = ScheduledRun(schedule_id=schedule.schedule_id)
        self.scheduler._runs[schedule.schedule_id] = [run]
        self.scheduler.mark_run_complete(
            schedule.schedule_id, run.run_id, JobStatus.COMPLETED
        )
        assert schedule.last_run is not None

    def test_calculate_next_run_daily(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="S", question="Q", frequency=ScheduleFrequency.DAILY, time_of_day="09:00"
        )
        next_run = self.scheduler.calculate_next_run(schedule)
        assert next_run is not None
        assert next_run.hour == 9

    def test_calculate_next_run_weekly(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="S", question="Q", frequency=ScheduleFrequency.WEEKLY, time_of_day="10:00"
        )
        next_run = self.scheduler.calculate_next_run(schedule)
        assert next_run is not None

    def test_calculate_next_run_monthly(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="S", question="Q", frequency=ScheduleFrequency.MONTHLY
        )
        next_run = self.scheduler.calculate_next_run(schedule)
        assert next_run is not None
        assert next_run.day == 1

    def test_calculate_next_run_quarterly(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="S", question="Q", frequency=ScheduleFrequency.QUARTERLY
        )
        next_run = self.scheduler.calculate_next_run(schedule)
        assert next_run is not None

    def test_get_runs(self) -> None:
        schedule = self.scheduler.create_schedule("S", "Q")
        runs = self.scheduler.get_runs(schedule.schedule_id)
        assert isinstance(runs, list)

    def test_disabled_schedule_not_due(self) -> None:
        schedule = self.scheduler.create_schedule(
            name="Disabled",
            question="Q",
            frequency=ScheduleFrequency.DAILY,
        )
        schedule.enabled = False
        due = self.scheduler.get_due_schedules()
        assert schedule.schedule_id not in [s.schedule_id for s in due]


class TestScheduledExecutor:
    """Tests for ScheduledExecutor."""

    def setup_method(self) -> None:
        self.executor = ScheduledExecutor(enable_sleep=False)
        self.scheduler = ResearchScheduler()

    def test_execute_schedule(self) -> None:
        schedule = self.scheduler.create_schedule("S", "Q")
        run = self.executor.execute_schedule(schedule)
        assert run.status == JobStatus.COMPLETED

    def test_execute_with_handler(self) -> None:
        schedule = self.scheduler.create_schedule("S", "Q")

        def handler(question: str) -> dict:
            return {"answer": "test"}

        run = self.executor.execute_schedule(schedule, handler)
        assert run.status == JobStatus.COMPLETED

    def test_detect_changes(self) -> None:
        last = {"price": 100}
        new = {"price": 105}
        assert self.executor.detect_changes("AAPL", last, new) is True

    def test_no_changes(self) -> None:
        last = {"price": 100}
        new = {"price": 100}
        assert self.executor.detect_changes("AAPL", last, new) is False

    def test_new_data_has_changes(self) -> None:
        last = {}
        new = {"price": 100}
        assert self.executor.detect_changes("AAPL", last, new) is True

    def test_dead_letter_queue(self) -> None:
        schedule = self.scheduler.create_schedule("S", "Q")

        def failing_handler(question: str) -> dict:
            raise ValueError("Test error")

        run = self.executor.execute_schedule(schedule, failing_handler)
        assert run.status == JobStatus.FAILED
        assert len(self.executor.get_dead_letter_queue()) == 1
