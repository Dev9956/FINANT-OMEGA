"""FININT OMEGA — Period comparator: compare two time periods of data."""

from __future__ import annotations

import structlog

from core.intelligence.change_detection.detector import ChangeDetector
from core.intelligence.change_detection.models import (
    ChangeSeverity,
    ComparisonResult,
    DetectedChange,
)

logger = structlog.get_logger()


class PeriodComparator:
    """Compare two periods of data and generate a structured comparison result."""

    def __init__(self) -> None:
        self._detector = ChangeDetector()

    def compare_periods(
        self,
        data_a: dict,
        period_a: str,
        data_b: dict,
        period_b: str,
        entity: str = "entity",
    ) -> ComparisonResult:
        """Compare two periods and return a ComparisonResult."""
        try:
            all_changes: list[DetectedChange] = []

            num_keys_a = {k: v for k, v in data_a.items() if isinstance(v, (int, float))}
            num_keys_b = {k: v for k, v in data_b.items() if isinstance(v, (int, float))}
            if num_keys_a or num_keys_b:
                all_changes.extend(
                    self._detector.detect_numerical_changes(num_keys_a, num_keys_b)
                )

            text_a = data_a.get("text", "")
            text_b = data_b.get("text", "")
            if isinstance(text_a, str) and isinstance(text_b, str) and text_a or text_b:
                all_changes.extend(
                    self._detector.detect_textual_changes(text_a, text_b)
                )

            sent_a = data_a.get("sentiment", {})
            sent_b = data_b.get("sentiment", {})
            if isinstance(sent_a, dict) and isinstance(sent_b, dict):
                all_changes.extend(
                    self._detector.detect_sentiment_changes(sent_a, sent_b)
                )

            guidance_a = data_a.get("guidance", {})
            guidance_b = data_b.get("guidance", {})
            if isinstance(guidance_a, dict) and isinstance(guidance_b, dict):
                all_changes.extend(
                    self._detector.detect_guidance_changes(guidance_a, guidance_b)
                )

            risks_a = data_a.get("risks", [])
            risks_b = data_b.get("risks", [])
            if isinstance(risks_a, list) and isinstance(risks_b, list):
                all_changes.extend(
                    self._detector.detect_risk_changes(risks_a, risks_b)
                )

            significance = self.compute_significance(all_changes)
            result = ComparisonResult(
                entity_a=entity,
                entity_b=entity,
                period_a=period_a,
                period_b=period_b,
                changes=all_changes,
                overall_significance=significance,
            )
            result.summary = self.generate_summary(result)
            return result
        except Exception as e:
            logger.error("compare_periods_failed", error=str(e))
            return ComparisonResult(
                entity_a=entity,
                entity_b=entity,
                period_a=period_a,
                period_b=period_b,
                summary=f"Comparison failed: {e}",
            )

    def compute_significance(self, changes: list[DetectedChange]) -> float:
        """Compute overall significance score (0.0 to 1.0)."""
        try:
            if not changes:
                return 0.0

            severity_weights: dict[ChangeSeverity, float] = {
                ChangeSeverity.TRIVIAL: 0.1,
                ChangeSeverity.MINOR: 0.3,
                ChangeSeverity.MODERATE: 0.5,
                ChangeSeverity.MAJOR: 0.8,
                ChangeSeverity.CRITICAL: 1.0,
            }

            total = sum(
                severity_weights.get(c.severity, 0.1) * c.confidence
                for c in changes
            )
            max_possible = len(changes) * 1.0
            return min(total / max_possible, 1.0) if max_possible > 0 else 0.0
        except Exception as e:
            logger.error("compute_significance_failed", error=str(e))
            return 0.0

    def generate_summary(self, result: ComparisonResult) -> str:
        """Generate a human-readable summary of the comparison."""
        try:
            total = len(result.changes)
            if total == 0:
                return f"No significant changes detected between {result.period_a} and {result.period_b}."

            severity_counts: dict[str, int] = {}
            for c in result.changes:
                sev = c.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            parts: list[str] = [f"{total} change(s) detected"]
            for sev, count in sorted(severity_counts.items()):
                parts.append(f"{count} {sev}")

            significance_pct = result.overall_significance * 100
            return (
                f"Comparing {result.period_a} vs {result.period_b}: "
                f"{', '.join(parts)}. "
                f"Overall significance: {significance_pct:.0f}%."
            )
        except Exception as e:
            logger.error("generate_summary_failed", error=str(e))
            return "Summary generation failed."
