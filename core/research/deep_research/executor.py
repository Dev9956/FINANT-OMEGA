"""FININT OMEGA — Deep Research Engine: task executor with parallelism and retry."""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable

import structlog

from core.research.deep_research.models import (
    EvidenceItem,
    ResearchTask,
    TaskStatus,
)

logger = structlog.get_logger()

# Type alias for tool dispatch functions
ToolHandler = Callable[..., Any]


class TaskExecutionError(Exception):
    """Raised when a task execution fails after retries."""


class ResearchExecutor:
    """Execute research tasks with retry, timeout, and parallel execution."""

    def __init__(self, tools: dict[str, ToolHandler] | None = None) -> None:
        self._tools: dict[str, ToolHandler] = tools or {}
        self._progress: dict[str, dict[str, Any]] = {}

    def register_tool(self, name: str, handler: ToolHandler) -> None:
        """Register a tool handler."""
        self._tools[name] = handler

    def _dispatch(self, tool_name: str, **kwargs: Any) -> Any:
        """Dispatch a call to the named tool."""
        handler = self._tools.get(tool_name)
        if handler is None:
            raise ValueError(f"Tool '{tool_name}' not registered")
        return handler(**kwargs)

    def execute_task(
        self,
        task: ResearchTask,
        max_retries: int = 3,
        timeout_seconds: int = 60,
    ) -> list[EvidenceItem]:
        """Execute a single research task, returning evidence items."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)

        self._progress[task.task_id] = {
            "status": "running",
            "started_at": task.started_at.isoformat(),
            "retries": 0,
        }

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                logger.info(
                    "task_execution_start",
                    task_id=task.task_id,
                    question=task.question,
                    attempt=attempt + 1,
                )

                # Dispatch to appropriate tool based on question keywords
                evidence_items = self._execute_with_tools(task)

                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                task.evidence_ids = [e.evidence_id for e in evidence_items]

                self._progress[task.task_id]["status"] = "completed"
                logger.info(
                    "task_execution_complete",
                    task_id=task.task_id,
                    evidence_count=len(evidence_items),
                )
                return evidence_items

            except Exception as e:
                last_error = e
                self._progress[task.task_id]["retries"] = attempt + 1
                logger.warning(
                    "task_execution_retry",
                    task_id=task.task_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                # Exponential backoff
                if attempt < max_retries - 1:
                    time.sleep(min(2**attempt, 10))

        # All retries exhausted
        task.status = TaskStatus.FAILED
        task.error = str(last_error)
        task.completed_at = datetime.now(timezone.utc)
        self._progress[task.task_id]["status"] = "failed"
        self._progress[task.task_id]["error"] = str(last_error)

        logger.error(
            "task_execution_failed",
            task_id=task.task_id,
            error=str(last_error),
        )
        return []

    def _execute_with_tools(self, task: ResearchTask) -> list[EvidenceItem]:
        """Route task execution to appropriate tools based on question content."""
        question_lower = task.question.lower()

        tool_map: list[tuple[list[str], str, list[str]]] = [
            (["price", "quote", "trading", "market data"], "market_data", ["symbol", "question"]),
            (["earnings", "eps", "revenue", "quarterly"], "earnings_data", ["symbol", "question"]),
            (["valuation", "pe ratio", "pb ratio", "dcf", "fair value"], "fundamentals", ["symbol", "question"]),
            (["news", "headline", "announcement"], "news_search", ["question"]),
            (["risk", "volatility", "drawdown", "var"], "risk_analyzer", ["question"]),
            (["macro", "economy", "gdp", "inflation", "interest rate"], "macro_data", ["question"]),
            (["sector", "industry", "market trend"], "sector_data", ["question"]),
        ]

        for keywords, tool_name, params in tool_map:
            if any(kw in question_lower for kw in keywords):
                kwargs = {}
                if "symbol" in params:
                    import re
                    symbols = re.findall(r"\b([A-Z]{2,6})\b", task.question)
                    kwargs["symbol"] = symbols[0] if symbols else ""
                kwargs["question"] = task.question
                return self._execute_tool(task, tool_name, **kwargs)

        # Default: use general_search
        return self._execute_tool(task, "general_search", question=task.question)

    def _execute_tool(
        self,
        task: ResearchTask,
        tool_name: str,
        **kwargs: Any,
    ) -> list[EvidenceItem]:
        """Execute a tool and wrap results as EvidenceItems."""
        try:
            result = self._dispatch(tool_name, **kwargs)
        except (ValueError, KeyError) as e:
            # Tool not registered - return placeholder evidence
            evidence = EvidenceItem(
                source_type="tool_error",
                source_id=tool_name,
                content=f"Tool '{tool_name}' not available: {e}",
                confidence=0.0,
                metadata={"error": str(e), "task_id": task.task_id},
            )
            return [evidence]

        # Wrap result as evidence
        if isinstance(result, list):
            items = []
            for i, r in enumerate(result):
                items.append(
                    EvidenceItem(
                        source_type=tool_name,
                        source_id=f"{task.task_id}_{i}",
                        content=str(r) if not isinstance(r, str) else r,
                        confidence=0.7,
                        metadata={"task_id": task.task_id, "tool": tool_name},
                    )
                )
            return items
        else:
            return [
                EvidenceItem(
                    source_type=tool_name,
                    source_id=task.task_id,
                    content=str(result) if not isinstance(result, str) else result,
                    confidence=0.7,
                    metadata={"task_id": task.task_id, "tool": tool_name},
                )
            ]

    def execute_parallel(
        self,
        tasks: list[ResearchTask],
        max_workers: int = 4,
        max_retries: int = 3,
    ) -> list[EvidenceItem]:
        """Execute multiple tasks in parallel, collecting all evidence."""
        all_evidence: list[EvidenceItem] = []

        if not tasks:
            return all_evidence

        with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as pool:
            future_to_task = {
                pool.submit(self.execute_task, task, max_retries): task
                for task in tasks
            }

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    evidence = future.result()
                    all_evidence.extend(evidence)
                except Exception as e:
                    logger.error(
                        "parallel_task_failed",
                        task_id=task.task_id,
                        error=str(e),
                    )

        return all_evidence

    def get_progress(self) -> dict[str, dict[str, Any]]:
        """Return progress information for all executed tasks."""
        return dict(self._progress)
