"""FININT OMEGA — Deep Research Engine: research quality evaluation."""

from __future__ import annotations

from core.research.deep_research.models import (
    ConflictStatus,
    ResearchRun,
    TaskStatus,
)
from core.research.deep_research.conflict_resolution import ConflictResolver


class ResearchEvaluator:
    """Evaluate the quality and completeness of a research run."""

    def evaluate_completeness(self, research_run: ResearchRun) -> float:
        """Evaluate how complete the research is (0.0 - 1.0)."""
        if not research_run.tasks:
            return 0.0

        completed = sum(
            1 for t in research_run.tasks if t.status == TaskStatus.COMPLETED
        )
        failed = sum(
            1 for t in research_run.tasks if t.status == TaskStatus.FAILED
        )
        total = len(research_run.tasks)

        task_score = completed / total if total > 0 else 0.0
        failure_penalty = (failed / total * 0.3) if total > 0 else 0.0

        # Bonus for having evidence
        evidence_score = min(len(research_run.evidence) / 10, 1.0) * 0.3

        # Bonus for having a synthesis
        synthesis_score = 0.2 if research_run.synthesis else 0.0

        return max(0.0, min(1.0, task_score * 0.5 + evidence_score + synthesis_score - failure_penalty))

    def evaluate_evidence_quality(
        self,
        evidence_items: list,
    ) -> float:
        """Evaluate the average quality of evidence (0.0 - 1.0)."""
        if not evidence_items:
            return 0.0

        total_confidence = sum(e.confidence for e in evidence_items)
        avg_confidence = total_confidence / len(evidence_items)

        # Bonus for source diversity
        source_types = {e.source_type for e in evidence_items}
        diversity_bonus = min(len(source_types) / 5, 0.2)

        return max(0.0, min(1.0, avg_confidence + diversity_bonus))

    def evaluate_consistency(self, research_run: ResearchRun) -> float:
        """Evaluate how consistent the evidence is (0.0 - 1.0)."""
        if not research_run.evidence:
            return 0.0

        # Check for contradictions
        contradictions = sum(
            1 for e in research_run.evidence if e.contradicts_claim
        )
        total = len(research_run.evidence)
        contradiction_ratio = contradictions / total if total > 0 else 0.0

        # Check unresolved conflicts
        unresolved = sum(
            1 for c in research_run.conflicts
            if c.resolution_status == ConflictStatus.UNRESOLVED
        )
        conflict_penalty = min(unresolved * 0.1, 0.5)

        consistency = 1.0 - contradiction_ratio - conflict_penalty
        return max(0.0, min(1.0, consistency))

    def get_evaluation_report(self, research_run: ResearchRun) -> dict:
        """Generate a comprehensive evaluation report."""
        completeness = self.evaluate_completeness(research_run)
        evidence_quality = self.evaluate_evidence_quality(research_run.evidence)
        consistency = self.evaluate_consistency(research_run)

        # Overall score
        scores = [completeness, evidence_quality, consistency]
        overall = sum(scores) / len(scores) if scores else 0.0

        task_summary = {
            "total": len(research_run.tasks),
            "completed": sum(
                1 for t in research_run.tasks if t.status == TaskStatus.COMPLETED
            ),
            "failed": sum(
                1 for t in research_run.tasks if t.status == TaskStatus.FAILED
            ),
            "pending": sum(
                1 for t in research_run.tasks if t.status == TaskStatus.PENDING
            ),
        }

        conflict_summary = {
            "total": len(research_run.conflicts),
            "resolved": sum(
                1 for c in research_run.conflicts
                if c.resolution_status == ConflictStatus.RESOLVED
            ),
            "unresolved": sum(
                1 for c in research_run.conflicts
                if c.resolution_status == ConflictStatus.UNRESOLVED
            ),
        }

        return {
            "research_id": research_run.research_id,
            "overall_score": round(overall, 3),
            "completeness": round(completeness, 3),
            "evidence_quality": round(evidence_quality, 3),
            "consistency": round(consistency, 3),
            "task_summary": task_summary,
            "evidence_count": len(research_run.evidence),
            "conflict_summary": conflict_summary,
            "has_synthesis": research_run.synthesis is not None,
            "synthesis_confidence": (
                research_run.synthesis.confidence
                if research_run.synthesis
                else None
            ),
        }
