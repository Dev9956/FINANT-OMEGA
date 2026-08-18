"""FININT OMEGA — Deep Research Engine: budget tracking and enforcement."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from core.research.deep_research.models import ResearchConfig


class BudgetExceeded(Exception):
    """Raised when the research budget is exceeded."""


class ResearchBudget:
    """Track and enforce token, API call, and time budgets."""

    def __init__(self, config: ResearchConfig) -> None:
        self._config = config
        self._tokens_used: int = 0
        self._api_calls: int = 0
        self._start_time: float = time.monotonic()
        self._task_count: int = 0

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    @property
    def api_calls(self) -> int:
        return self._api_calls

    @property
    def elapsed_seconds(self) -> float:
        return time.monotonic() - self._start_time

    def record_tokens(self, count: int) -> None:
        """Record token usage."""
        if count < 0:
            raise ValueError("Token count must be non-negative")
        self._tokens_used += count

    def record_api_call(self) -> None:
        """Record an API call."""
        self._api_calls += 1

    def record_task(self) -> None:
        """Record a completed task."""
        self._task_count += 1

    def enforce_budget(self) -> bool:
        """Check if we should continue (True) or stop (False)."""
        if self._tokens_used >= self._config.budget_tokens:
            return False
        if self.elapsed_seconds >= self._config.timeout_seconds:
            return False
        if self._task_count >= self._config.max_tasks:
            return False
        return True

    def check_and_enforce(self) -> None:
        """Raise BudgetExceeded if budget is exceeded."""
        if not self.enforce_budget():
            raise BudgetExceeded(self.get_usage_summary())

    def get_usage_report(self) -> dict:
        """Get a detailed usage report."""
        elapsed = self.elapsed_seconds
        return {
            "tokens_used": self._tokens_used,
            "tokens_budget": self._config.budget_tokens,
            "tokens_utilization": (
                self._tokens_used / self._config.budget_tokens
                if self._config.budget_tokens > 0
                else 0.0
            ),
            "api_calls": self._api_calls,
            "elapsed_seconds": round(elapsed, 2),
            "timeout_seconds": self._config.timeout_seconds,
            "time_utilization": (
                elapsed / self._config.timeout_seconds
                if self._config.timeout_seconds > 0
                else 0.0
            ),
            "tasks_completed": self._task_count,
            "max_tasks": self._config.max_tasks,
            "task_utilization": (
                self._task_count / self._config.max_tasks
                if self._config.max_tasks > 0
                else 0.0
            ),
            "within_budget": self.enforce_budget(),
        }

    def get_usage_summary(self) -> str:
        """Get a human-readable usage summary."""
        report = self.get_usage_report()
        return (
            f"Tokens: {report['tokens_used']}/{report['tokens_budget']} "
            f"({report['tokens_utilization']:.1%}), "
            f"API calls: {report['api_calls']}, "
            f"Time: {report['elapsed_seconds']:.1f}s/{report['timeout_seconds']}s "
            f"({report['time_utilization']:.1%}), "
            f"Tasks: {report['tasks_completed']}/{report['max_tasks']}"
        )
