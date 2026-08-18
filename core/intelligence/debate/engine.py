"""FININT OMEGA — AI Investment Debate Engine."""

from __future__ import annotations

import time

from core.intelligence.debate.models import (
    AnalystArgument,
    AnalystRole,
    DebateConfig,
    DebateResult,
    EvidenceVerification,
    SynthesisResult,
)


class DebateEngine:
    """Multi-agent adversarial analysis: Bull vs Bear vs Neutral → Synthesis."""

    def __init__(self, config: DebateConfig | None = None) -> None:
        self._config = config or DebateConfig()
        self._debates: dict[str, DebateResult] = {}

    def run_debate(
        self,
        question: str,
        context: dict | None = None,
        evidence_items: list[str] | None = None,
    ) -> DebateResult:
        start = time.time()
        ctx = context or {}
        evidence = evidence_items or []

        bull = self._run_bull_analyst(question, ctx, evidence)
        bear = self._run_bear_analyst(question, ctx, evidence)
        neutral = self._run_neutral_verifier(evidence, bull, bear)
        synthesis = self._run_synthesis_judge(question, bull, bear, neutral)

        duration_ms = (time.time() - start) * 1000

        result = DebateResult(
            question=question,
            bull_argument=bull,
            bear_argument=bear,
            neutral_verification=neutral,
            synthesis=synthesis,
            evidence_items=evidence,
            duration_ms=duration_ms,
            status="completed",
        )

        self._debates[result.debate_id] = result
        return result

    def get_debate(self, debate_id: str) -> DebateResult | None:
        return self._debates.get(debate_id)

    def _run_bull_analyst(
        self, question: str, context: dict, evidence: list[str],
    ) -> AnalystArgument:
        positive_keywords = {"growth", "catalyst", "accelerat", "strong", "improv", "upside", "beat", "exceed"}
        key_points = []
        for e in evidence:
            e_lower = e.lower()
            if any(kw in e_lower for kw in positive_keywords):
                key_points.append(e)

        if not key_points and evidence:
            key_points = [f"Potential positive: {e}" for e in evidence[:3]]

        bullish_evidence = [e for e in evidence if any(kw in e.lower() for kw in positive_keywords)]

        return AnalystArgument(
            analyst_role=AnalystRole.BULL,
            thesis=f"Bull case for: {question}",
            key_points=key_points[:self._config.max_evidence_per_analyst],
            evidence=bullish_evidence,
            confidence=min(len(bullish_evidence) / max(len(evidence), 1) + 0.3, 0.9),
            catalysts_identified=key_points[:3],
        )

    def _run_bear_analyst(
        self, question: str, context: dict, evidence: list[str],
    ) -> AnalystArgument:
        negative_keywords = {"risk", "decline", "deteriorat", "weak", "threat", "challenge", "miss", "downside"}
        key_points = []
        for e in evidence:
            e_lower = e.lower()
            if any(kw in e_lower for kw in negative_keywords):
                key_points.append(e)

        if not key_points and evidence:
            key_points = [f"Potential concern: {e}" for e in evidence[:3]]

        bearish_evidence = [e for e in evidence if any(kw in e.lower() for kw in negative_keywords)]

        return AnalystArgument(
            analyst_role=AnalystRole.BEAR,
            thesis=f"Bear case for: {question}",
            key_points=key_points[:self._config.max_evidence_per_analyst],
            evidence=bearish_evidence,
            confidence=min(len(bearish_evidence) / max(len(evidence), 1) + 0.3, 0.9),
            risks_identified=key_points[:3],
        )

    def _run_neutral_verifier(
        self,
        evidence: list[str],
        bull: AnalystArgument,
        bear: AnalystArgument,
    ) -> list[EvidenceVerification]:
        verifications = []
        bull_evidence_set = set(bull.evidence)
        bear_evidence_set = set(bear.evidence)

        for item in evidence:
            supported_by_bull = item in bull_evidence_set
            supported_by_bear = item in bear_evidence_set

            verified = supported_by_bull != supported_by_bear or (not supported_by_bull and not supported_by_bear)
            corroboration = 1 if supported_by_bull else 0
            contradiction = 1 if supported_by_bear and not supported_by_bull else 0

            verifications.append(EvidenceVerification(
                evidence_item=item,
                verified=verified,
                source_quality=0.7 if verified else 0.4,
                corroboration_count=corroboration,
                contradiction_count=contradiction,
            ))

        return verifications

    def _run_synthesis_judge(
        self,
        question: str,
        bull: AnalystArgument,
        bear: AnalystArgument,
        neutral: list[EvidenceVerification],
    ) -> SynthesisResult:
        verified_count = sum(1 for v in neutral if v.verified)
        total = len(neutral) if neutral else 1
        evidence_quality = verified_count / total

        bull_confidence = bull.confidence
        bear_confidence = bear.confidence
        total_conf = bull_confidence + bear_confidence
        if total_conf > 0:
            bull_weight = bull_confidence / total_conf
            bear_weight = bear_confidence / total_conf
        else:
            bull_weight = bear_weight = 0.5

        final_confidence = (bull_weight * bull_confidence + bear_weight * bear_confidence) * evidence_quality

        consensus = []
        disputes = []
        if bull.key_points and bear.key_points:
            common = set(bull.key_points) & set(bear.key_points)
            consensus = list(common)
            disputes = list(set(bull.key_points + bear.key_points) - common)

        if bull_confidence > bear_confidence + 0.2:
            action = "Lean bullish — stronger evidence base"
        elif bear_confidence > bull_confidence + 0.2:
            action = "Lean bearish — stronger risk evidence"
        else:
            action = "Neutral — evidence is balanced"

        return SynthesisResult(
            conclusion=f"Debate synthesis for: {question}",
            bull_argument=bull.thesis,
            bear_argument=bear.thesis,
            evidence_quality_score=evidence_quality,
            key_consensus=consensus,
            key_disputes=disputes,
            final_confidence=final_confidence,
            recommended_action=action,
            risk_assessment=f"Bear confidence: {bear_confidence:.2f}, Bull confidence: {bull_confidence:.2f}",
        )
