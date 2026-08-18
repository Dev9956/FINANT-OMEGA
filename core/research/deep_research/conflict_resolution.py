"""FININT OMEGA — Deep Research Engine: conflict detection and resolution."""

from __future__ import annotations

from core.research.deep_research.models import (
    ConflictItem,
    ConflictStatus,
    EvidenceItem,
)


class ConflictResolver:
    """Detect, classify, and suggest resolutions for evidence conflicts."""

    def detect_conflicts(
        self,
        evidence_items: list[EvidenceItem],
    ) -> list[ConflictItem]:
        """Detect conflicts between evidence items."""
        conflicts: list[ConflictItem] = []

        supporting: dict[str, list[EvidenceItem]] = {}
        contradicting: dict[str, list[EvidenceItem]] = {}

        for ev in evidence_items:
            if ev.supports_claim:
                supporting.setdefault(ev.supports_claim, []).append(ev)
            if ev.contradicts_claim:
                contradicting.setdefault(ev.contradicts_claim, []).append(ev)

        for claim, contra_items in contradicting.items():
            supp_items = supporting.get(claim, [])
            if supp_items:
                # Compute severity based on confidence difference
                avg_supp_conf = sum(e.confidence for e in supp_items) / len(supp_items)
                avg_contra_conf = sum(e.confidence for e in contra_items) / len(contra_items)
                severity = abs(avg_supp_conf - avg_contra_conf)

                conflict = ConflictItem(
                    claim_a=claim,
                    claim_b=f"contradiction of: {claim}",
                    evidence_a_ids=[e.evidence_id for e in supp_items],
                    evidence_b_ids=[e.evidence_id for e in contra_items],
                    severity=severity,
                    resolution_status=ConflictStatus.UNRESOLVED,
                )
                conflicts.append(conflict)

        return conflicts

    def classify_conflict(
        self,
        severity: float,
        source_reliability: float = 0.5,
    ) -> str:
        """Classify a conflict's severity level."""
        adjusted = severity * (1 - source_reliability * 0.3)
        if adjusted >= 0.7:
            return "critical"
        if adjusted >= 0.4:
            return "moderate"
        return "minor"

    def suggest_resolution(self, conflict: ConflictItem) -> str:
        """Suggest a resolution approach for a conflict."""
        classification = self.classify_conflict(conflict.severity)

        if classification == "critical":
            return (
                "Critical conflict: Requires additional research. "
                "Consider seeking primary sources and expert analysis to "
                "resolve the discrepancy."
            )
        if classification == "moderate":
            return (
                "Moderate conflict: Weigh evidence by source reliability "
                "and recency. Consider the methodology and sample size "
                "of each source."
            )
        return (
            "Minor conflict: Note the disagreement but proceed with "
            "the higher-confidence evidence. Document the limitation."
        )

    def resolve_conflict(
        self,
        conflict: ConflictItem,
        all_evidence: list[EvidenceItem],
    ) -> ConflictItem:
        """Attempt to resolve a conflict automatically."""
        evidence_map = {e.evidence_id: e for e in all_evidence}

        # Gather evidence for both sides
        side_a = [
            evidence_map[eid]
            for eid in conflict.evidence_a_ids
            if eid in evidence_map
        ]
        side_b = [
            evidence_map[eid]
            for eid in conflict.evidence_b_ids
            if eid in evidence_map
        ]

        if not side_a or not side_b:
            conflict.resolution_status = ConflictStatus.IRREDUCIBLE
            conflict.resolution = "Insufficient evidence to resolve"
            return conflict

        # Compare average confidence
        avg_a = sum(e.confidence for e in side_a) / len(side_a)
        avg_b = sum(e.confidence for e in side_b) / len(side_b)

        if abs(avg_a - avg_b) < 0.1:
            conflict.resolution_status = ConflictStatus.IRREDUCIBLE
            conflict.resolution = (
                "Both sides have similar confidence; "
                "manual review required."
            )
        else:
            winner = "A" if avg_a > avg_b else "B"
            conflict.resolution_status = ConflictStatus.RESOLVED
            conflict.resolution = (
                f"Side {winner} has higher average confidence "
                f"({max(avg_a, avg_b):.2f} vs {min(avg_a, avg_b):.2f}). "
                f"Prioritizing side {winner}."
            )

        return conflict
