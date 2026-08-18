"""FININT OMEGA — Scheduled executor for running scheduled research."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from core.research.scheduled.models import (
    JobStatus,
    ResearchSchedule,
    ScheduledRun,
)

logger = structlog.get_logger()


class ScheduledExecutor:
    """Execute scheduled research jobs with idempotency and retry logic."""

    MAX_RETRIES = 3
    BASE_BACKOFF_S = 1.0

    def __init__(self, *, enable_sleep: bool = True) -> None:
        self._running: dict[str, bool] = {}
        self._dead_letter_queue: list[ScheduledRun] = []
        self._enable_sleep = enable_sleep

    def execute_schedule(
        self,
        schedule: ResearchSchedule,
        research_handler: Any = None,
    ) -> ScheduledRun:
        """Execute a scheduled research job idempotently with retry."""
        if self._running.get(schedule.schedule_id, False):
            logger.info("schedule_already_running", schedule_id=schedule.schedule_id)
            return ScheduledRun(
                schedule_id=schedule.schedule_id,
                status=JobStatus.RUNNING,
            )

        self._running[schedule.schedule_id] = True
        run = ScheduledRun(
            schedule_id=schedule.schedule_id,
            research_id=str(uuid.uuid4()),
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        last_error: Exception | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                if research_handler:
                    result = research_handler(schedule.question)
                else:
                    result = self._default_research(schedule.question)
                run.status = JobStatus.COMPLETED
                run.completed_at = datetime.now(timezone.utc)
                run.retry_count = attempt
                logger.info(
                    "schedule_completed",
                    schedule_id=schedule.schedule_id,
                    run_id=run.run_id,
                )
                break
            except Exception as e:
                last_error = e
                run.retry_count = attempt
                if attempt < self.MAX_RETRIES:
                    backoff = self.BASE_BACKOFF_S * (2 ** (attempt - 1))
                    logger.warning(
                        "schedule_retry",
                        schedule_id=schedule.schedule_id,
                        retry=attempt,
                        backoff_s=backoff,
                    )
                    if self._enable_sleep:
                        time.sleep(min(backoff, 10))
                else:
                    run.status = JobStatus.FAILED
                    run.error_message = str(e)
                    run.completed_at = datetime.now(timezone.utc)
                    self._dead_letter_queue.append(run)
                    logger.error(
                        "schedule_failed_permanently",
                        schedule_id=schedule.schedule_id,
                        error=str(e),
                    )
        else:
            if last_error:
                run.status = JobStatus.FAILED
                run.error_message = str(last_error)
                run.completed_at = datetime.now(timezone.utc)

        self._running[schedule.schedule_id] = False
        return run

    def detect_changes(self, symbol: str, last_data: dict, new_data: dict) -> bool:
        """Detect if meaningful changes occurred between data snapshots."""
        if not last_data:
            return True
        for key in new_data:
            if key in last_data:
                old_val = last_data[key]
                new_val = new_data[key]
                if old_val != new_val and new_val is not None:
                    return True
        new_keys = set(new_data.keys()) - set(last_data.keys())
        if new_keys:
            return True
        return False

    def run_if_changes(
        self,
        schedule: ResearchSchedule,
        symbol: str,
        last_data: dict,
        new_data: dict,
        research_handler: Any = None,
    ) -> ScheduledRun | None:
        """Run research only if changes are detected."""
        if self.detect_changes(symbol, last_data, new_data):
            return self.execute_schedule(schedule, research_handler)
        logger.info("no_changes_detected", schedule_id=schedule.schedule_id, symbol=symbol)
        return None

    def get_dead_letter_queue(self) -> list[ScheduledRun]:
        """Get failed runs in the dead letter queue."""
        return list(self._dead_letter_queue)

    def retry_from_dead_letter(self, schedule: ResearchSchedule, research_handler: Any = None) -> ScheduledRun | None:
        """Retry a failed run from the dead letter queue."""
        for i, run in enumerate(self._dead_letter_queue):
            if run.schedule_id == schedule.schedule_id:
                self._dead_letter_queue.pop(i)
                run.retry_count = 0
                run.status = JobStatus.PENDING
                return self.execute_schedule(schedule, research_handler)
        return None

    def _default_research(self, question: str) -> dict:
        """Default research handler (stub)."""
        return {
            "question": question,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
