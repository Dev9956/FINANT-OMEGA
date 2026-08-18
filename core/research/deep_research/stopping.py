"""FININT OMEGA — Deep Research Engine: stopping criteria."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.research.deep_research.models import (
    EvidenceItem,
    ResearchConfig,
    ResearchTask,
    TaskStatus,
)


@dataclass
class StoppingState:
    """Current state of the research for stopping evaluation."""

    tasks: list[ResearchTask] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)
    config: ResearchConfig = field(default_factory=ResearchConfig)
    elapsed_seconds: float = 0.0


class StoppingCriteria:
    """Evaluate whether research should stop."""

    def __init__(self, config: ResearchConfig | None = None) -> None:
        self._config = config or ResearchConfig()
        self._previous_evidence_hash: int = 0
        self._no_new_evidence_count: int = 0

    def max_tasks_reached(self, state: StoppingState) -> bool:
        """Check if the maximum number of tasks has been reached."""
        completed = sum(
            1
            for t in state.tasks
            if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)
        )
        return completed >= self._config.max_tasks

    def max_sources_reached(self, state: StoppingState) -> bool:
        """Check if the maximum number of sources has been reached."""
        unique_sources = len({e.source_id for e in state.evidence})
        return unique_sources >= self._config.max_sources

    def max_time_reached(self, state: StoppingState) -> bool:
        """Check if the timeout has been reached."""
        return state.elapsed_seconds >= self._config.timeout_seconds

    def confidence_threshold_met(
        self,
        state: StoppingState,
        threshold: float = 0.8,
    ) -> bool:
        """Check if overall evidence confidence meets threshold."""
        if not state.evidence:
            return False
        avg_confidence = sum(e.confidence for e in state.evidence) / len(state.evidence)
        return avg_confidence >= threshold

    def no_new_evidence(self, state: StoppingState) -> bool:
        """Check if research has converged (no new evidence being found)."""
        current_hash = hash(tuple(e.evidence_id for e in state.evidence))
        if current_hash == self._previous_evidence_hash:
            self._no_new_evidence_count += 1
        else:
            self._no_new_evidence_count = 0
        self._previous_evidence_hash = current_hash
        return self._no_new_evidence_count >= 3

    def all_tasks_complete(self, state: StoppingState) -> bool:
        """Check if all tasks are complete (completed, failed, or skipped)."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)
            for t in state.tasks
        )

    def should_stop(self, state: StoppingState) -> tuple[bool, str]:
        """Evaluate all criteria and return whether to stop with a reason."""
        checks: list[tuple[bool, str]] = [
            (self.max_tasks_reached(state), "max_tasks_reached"),
            (self.max_sources_reached(state), "max_sources_reached"),
            (self.max_time_reached(state), "max_time_reached"),
            (self.confidence_threshold_met(state), "confidence_threshold_met"),
            (self.no_new_evidence(state), "no_new_evidence"),
            (self.all_tasks_complete(state), "all_tasks_complete"),
        ]

        for triggered, reason in checks:
            if triggered:
                return True, reason

        return False, ""
