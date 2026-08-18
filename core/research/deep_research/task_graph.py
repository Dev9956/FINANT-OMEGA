"""FININT OMEGA — Deep Research Engine: task graph (DAG) for execution ordering."""

from __future__ import annotations

from datetime import datetime, timezone

from core.research.deep_research.models import ResearchTask, TaskStatus


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in the task graph."""


class TaskGraph:
    """Directed Acyclic Graph of research tasks with dependency management."""

    def __init__(self, tasks: list[ResearchTask]) -> None:
        self._tasks: dict[str, ResearchTask] = {t.task_id: t for t in tasks}
        self._validate_no_cycles()

    def _validate_no_cycles(self) -> None:
        """Detect circular dependencies using DFS."""
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(task_id: str) -> None:
            visited.add(task_id)
            rec_stack.add(task_id)
            task = self._tasks.get(task_id)
            if task is None:
                return
            for dep_id in task.dependencies:
                if dep_id not in self._tasks:
                    continue
                if dep_id not in visited:
                    dfs(dep_id)
                elif dep_id in rec_stack:
                    raise CircularDependencyError(
                        f"Circular dependency detected involving task {dep_id}"
                    )
            rec_stack.discard(task_id)

        for task_id in self._tasks:
            if task_id not in visited:
                dfs(task_id)

    def topological_sort(self) -> list[ResearchTask]:
        """Return tasks in topological order (respecting dependencies)."""
        visited: set[str] = set()
        result: list[ResearchTask] = []

        def dfs(task_id: str) -> None:
            if task_id in visited:
                return
            visited.add(task_id)
            task = self._tasks.get(task_id)
            if task is None:
                return
            for dep_id in task.dependencies:
                if dep_id in self._tasks:
                    dfs(dep_id)
            result.append(task)

        for task_id in self._tasks:
            dfs(task_id)

        return result

    def ready_tasks(self) -> list[ResearchTask]:
        """Return tasks whose dependencies are all completed."""
        completed_ids = {
            tid for tid, t in self._tasks.items() if t.status == TaskStatus.COMPLETED
        }
        ready: list[ResearchTask] = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            if all(dep in completed_ids for dep in task.dependencies):
                ready.append(task)
        return ready

    def complete_task(self, task_id: str, result: str | None = None) -> ResearchTask:
        """Mark a task as completed with its result."""
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now(timezone.utc)
        return task

    def fail_task(self, task_id: str, error: str) -> ResearchTask:
        """Mark a task as failed."""
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.now(timezone.utc)
        return task

    def get_task(self, task_id: str) -> ResearchTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def all_tasks(self) -> list[ResearchTask]:
        """Return all tasks."""
        return list(self._tasks.values())

    def is_complete(self) -> bool:
        """Check if all tasks are completed or failed."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)
            for t in self._tasks.values()
        )

    def pending_count(self) -> int:
        """Count of pending tasks."""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
