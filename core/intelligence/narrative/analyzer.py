"""FININT OMEGA — Narrative vs Numbers analyzer."""

from __future__ import annotations

from core.intelligence.narrative.models import (
    AlignmentLevel,
    NarrativeAnalysis,
    NarrativeComponent,
    QuantitativeSignal,
)


class NarrativeAnalyzer:
    """Compare qualitative narrative statements against quantitative financial data."""

    def __init__(self) -> None:
        self._bullish_keywords = {
            "growth", "accelerat", "strong", "robust", "improv", "expansion",
            "increase", "rise", "gain", "optimis", "outperform", "beat",
            "exceed", "record", "high", "surge", "soar",
        }
        self._bearish_keywords = {
            "decline", "deteriorat", "weak", "compress", "contraction",
            "slowdown", "decrease", "fall", "drop", "loss", "miss",
            "underperform", "risk", "threat", "challenge", "concern",
        }
        self._neutral_keywords = {
            "stable", "maintain", "unchanged", "flat", "steady", "consistent",
        }

    def analyze(
        self,
        narrative: str,
        metrics: dict[str, dict],
        metric_mappings: dict[str, str] | None = None,
    ) -> NarrativeAnalysis:
        narrative_components = self._extract_narrative_components(narrative)
        quantitative_signals = self._extract_quantitative_signals(metrics, metric_mappings)

        bullish_count = sum(1 for c in narrative_components if c.component_type == "growth")
        bearish_count = sum(1 for c in narrative_components if c.component_type == "risk")

        positive_signals = sum(1 for s in quantitative_signals if s.direction == "up")
        negative_signals = sum(1 for s in quantitative_signals if s.direction == "down")

        supporting = []
        conflicting = []

        if bullish_count > 0 and positive_signals > 0:
            supporting.append(f"Narrative bullish ({bullish_count} components) aligned with {positive_signals} positive signals")
        if bearish_count > 0 and negative_signals > 0:
            supporting.append(f"Narrative bearish ({bearish_count} components) aligned with {negative_signals} negative signals")
        if bullish_count > 0 and negative_signals > positive_signals:
            conflicting.append(f"Narrative bullish but {negative_signals} metrics declining vs {positive_signals} improving")
        if bearish_count > 0 and positive_signals > negative_signals:
            conflicting.append(f"Narrative bearish but {positive_signals} metrics improving vs {negative_signals} declining")

        total_signals = len(quantitative_signals)
        if total_signals == 0:
            alignment_level = AlignmentLevel.INSUFFICIENT_DATA
            alignment_score = 0.5
            confidence = 0.3
        else:
            aligned = positive_signals if bullish_count > bearish_count else negative_signals
            alignment_score = aligned / total_signals if total_signals > 0 else 0.5

            if alignment_score >= 0.75:
                alignment_level = AlignmentLevel.HIGH_ALIGNMENT
                confidence = 0.85
            elif alignment_score >= 0.5:
                alignment_level = AlignmentLevel.MODERATE_ALIGNMENT
                confidence = 0.65
            else:
                alignment_level = AlignmentLevel.LOW_ALIGNMENT
                confidence = 0.45

        summary = self._generate_summary(
            alignment_level, alignment_score, supporting, conflicting,
            bullish_count, bearish_count, positive_signals, negative_signals,
        )

        return NarrativeAnalysis(
            narrative=narrative,
            alignment_level=alignment_level,
            alignment_score=alignment_score,
            narrative_components=narrative_components,
            quantitative_signals=quantitative_signals,
            supporting_signals=supporting,
            conflicting_signals=conflicting,
            confidence=confidence,
            summary=summary,
        )

    def _extract_narrative_components(self, narrative: str) -> list[NarrativeComponent]:
        components = []
        sentences = narrative.replace(".", " ").split()
        text_lower = narrative.lower()

        words = set(text_lower.split())

        bullish_hits = words & self._bullish_keywords
        bearish_hits = words & self._bearish_keywords
        neutral_hits = words & self._neutral_keywords

        if bullish_hits:
            sentiment = min(len(bullish_hits) / 3.0, 1.0)
            components.append(NarrativeComponent(
                text=narrative,
                component_type="growth",
                sentiment=sentiment,
                keywords=list(bullish_hits),
            ))

        if bearish_hits:
            sentiment = -min(len(bearish_hits) / 3.0, 1.0)
            components.append(NarrativeComponent(
                text=narrative,
                component_type="risk",
                sentiment=sentiment,
                keywords=list(bearish_hits),
            ))

        if not bullish_hits and not bearish_hits:
            components.append(NarrativeComponent(
                text=narrative,
                component_type="neutral",
                sentiment=0.0,
            ))

        return components

    def _extract_quantitative_signals(
        self,
        metrics: dict[str, dict],
        metric_mappings: dict[str, str] | None = None,
    ) -> list[QuantitativeSignal]:
        signals = []
        mappings = metric_mappings or {}

        for metric_name, values in metrics.items():
            current = values.get("current", 0)
            previous = values.get("previous", values.get("prior", None))

            if previous is not None and previous != 0:
                change_pct = ((current - previous) / abs(previous)) * 100
            else:
                change_pct = 0.0

            if change_pct > 5:
                direction = "up"
                significance = "significant" if change_pct > 20 else "moderate" if change_pct > 10 else "minor"
            elif change_pct < -5:
                direction = "down"
                significance = "significant" if change_pct < -20 else "moderate" if change_pct < -10 else "minor"
            else:
                direction = "flat"
                significance = "minor"

            display_name = mappings.get(metric_name, metric_name)

            signals.append(QuantitativeSignal(
                metric=display_name,
                current_value=current,
                previous_value=previous,
                change_pct=change_pct,
                direction=direction,
                significance=significance,
            ))

        return signals

    def _generate_summary(
        self,
        alignment_level: AlignmentLevel,
        alignment_score: float,
        supporting: list[str],
        conflicting: list[str],
        bullish_count: int,
        bearish_count: int,
        positive_signals: int,
        negative_signals: int,
    ) -> str:
        parts = []

        if alignment_level == AlignmentLevel.HIGH_ALIGNMENT:
            parts.append("Strong alignment between narrative and numbers.")
        elif alignment_level == AlignmentLevel.MODERATE_ALIGNMENT:
            parts.append("Moderate alignment between narrative and numbers.")
        elif alignment_level == AlignmentLevel.LOW_ALIGNMENT:
            parts.append("Low alignment — potential narrative/numbers divergence.")
        else:
            parts.append("Insufficient quantitative data for comparison.")

        parts.append(f"Narrative: {bullish_count} bullish, {bearish_count} bearish components.")
        parts.append(f"Numbers: {positive_signals} positive, {negative_signals} negative signals.")

        if supporting:
            parts.append("Supporting: " + "; ".join(supporting))
        if conflicting:
            parts.append("Conflicting: " + "; ".join(conflicting))

        return " ".join(parts)
