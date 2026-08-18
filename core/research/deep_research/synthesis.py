"""FININT OMEGA — Deep Research Engine: evidence synthesis."""

from __future__ import annotations

from collections import defaultdict

from core.research.deep_research.models import (
    ConflictItem,
    EvidenceItem,
    ResearchConfig,
    ResearchSynthesis,
)


class ResearchSynthesizer:
    """Synthesize evidence into a coherent research conclusion."""

    def synthesize(
        self,
        research_id: str,
        evidence: list[EvidenceItem],
        conflicts: list[ConflictItem],
        config: ResearchConfig | None = None,
    ) -> ResearchSynthesis:
        """Synthesize evidence and conflicts into a final research synthesis."""
        if not evidence:
            return ResearchSynthesis(
                research_id=research_id,
                conclusion="No evidence was gathered to support any conclusion.",
                confidence=0.0,
                evidence_ids=[],
                limitations=["No evidence collected"],
                methodology="No research tasks executed",
            )

        claims_map = self._group_evidence_by_claim(evidence)
        consensus, disagreement = self._detect_consensus_disagreement(claims_map)
        confidence = self._compute_overall_confidence(evidence, conflicts)
        limitations = self._generate_limitations(evidence, conflicts, config)
        methodology = self._generate_methodology(evidence, config)

        conclusion_parts: list[str] = []
        if consensus:
            conclusion_parts.append("Consensus findings:")
            for claim, ev_list in consensus.items():
                avg_conf = sum(e.confidence for e in ev_list) / len(ev_list)
                conclusion_parts.append(
                    f"- {claim} (confidence: {avg_conf:.2f}, {len(ev_list)} sources)"
                )

        if disagreement:
            conclusion_parts.append("Areas of disagreement:")
            for claim_pair, items in disagreement.items():
                conclusion_parts.append(f"- {claim_pair}")

        if not conclusion_parts:
            conclusion_parts.append(
                "The research gathered evidence but could not form a clear conclusion."
            )

        all_evidence_ids = [e.evidence_id for e in evidence]

        return ResearchSynthesis(
            research_id=research_id,
            conclusion="\n".join(conclusion_parts),
            confidence=confidence,
            evidence_ids=all_evidence_ids,
            limitations=limitations,
            methodology=methodology,
            claims=list(consensus.keys()),
        )

    def _group_evidence_by_claim(
        self,
        evidence: list[EvidenceItem],
    ) -> dict[str, list[EvidenceItem]]:
        """Group evidence items by the claim they support or contradict."""
        groups: dict[str, list[EvidenceItem]] = defaultdict(list)
        for ev in evidence:
            claim = ev.supports_claim or ev.contradicts_claim or "general"
            groups[claim].append(ev)
        return dict(groups)

    def _detect_consensus_disagreement(
        self,
        claims_map: dict[str, list[EvidenceItem]],
    ) -> tuple[dict[str, list[EvidenceItem]], dict[str, list[EvidenceItem]]]:
        """Separate consensus claims from disputed ones."""
        consensus: dict[str, list[EvidenceItem]] = {}
        disagreement: dict[str, list[EvidenceItem]] = {}

        for claim, items in claims_map.items():
            if claim == "general":
                continue
            supporting = [e for e in items if e.supports_claim == claim]
            contradicting = [e for e in items if e.contradicts_claim == claim]

            if len(contradicting) == 0 and len(supporting) > 0:
                consensus[claim] = items
            elif len(contradicting) > 0 and len(supporting) > 0:
                disagreement[claim] = items
            elif len(supporting) > 0:
                consensus[claim] = items

        return consensus, disagreement

    def _compute_overall_confidence(
        self,
        evidence: list[EvidenceItem],
        conflicts: list[ConflictItem],
    ) -> float:
        """Compute overall confidence score."""
        if not evidence:
            return 0.0

        avg_confidence = sum(e.confidence for e in evidence) / len(evidence)

        unresolved = sum(1 for c in conflicts if c.resolution is None)
        conflict_penalty = min(unresolved * 0.05, 0.3)

        return max(0.0, min(1.0, avg_confidence - conflict_penalty))

    def _generate_limitations(
        self,
        evidence: list[EvidenceItem],
        conflicts: list[ConflictItem],
        config: ResearchConfig | None,
    ) -> list[str]:
        """Generate a list of limitations."""
        limitations: list[str] = []

        if not evidence:
            limitations.append("No evidence was collected")
            return limitations

        avg_conf = sum(e.confidence for e in evidence) / len(evidence)
        if avg_conf < 0.5:
            limitations.append("Low average evidence confidence")

        source_types = {e.source_type for e in evidence}
        if len(source_types) < 2:
            limitations.append("Limited source diversity")

        unresolved_conflicts = [c for c in conflicts if c.resolution is None]
        if unresolved_conflicts:
            limitations.append(
                f"{len(unresolved_conflicts)} unresolved conflicts"
            )

        if config and config.depth.value == "shallow":
            limitations.append("Shallow research depth")

        return limitations

    def _generate_methodology(
        self,
        evidence: list[EvidenceItem],
        config: ResearchConfig | None,
    ) -> str:
        """Generate a methodology summary."""
        source_types = list({e.source_type for e in evidence})
        parts = [
            f"Collected {len(evidence)} evidence items",
            f"from {len(source_types)} source types: {', '.join(source_types)}.",
        ]
        if config:
            parts.append(f"Research depth: {config.depth.value}.")
        return " ".join(parts)
