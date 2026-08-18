"""FININT OMEGA — Research Quality Engine."""

from __future__ import annotations

from core.intelligence.quality.models import QualityDimension, QualityResult


class QualityEngine:
    """Score research quality across multiple dimensions."""

    def __init__(self) -> None:
        self._weights = {
            QualityDimension.EVIDENCE_COVERAGE: 0.2,
            QualityDimension.SOURCE_QUALITY: 0.15,
            QualityDimension.NUMERICAL_ACCURACY: 0.2,
            QualityDimension.FRESHNESS: 0.1,
            QualityDimension.CONTRADICTION_HANDLING: 0.15,
            QualityDimension.COMPLETENESS: 0.1,
            QualityDimension.UNCERTAINTY: 0.05,
            QualityDimension.REPRODUCIBILITY: 0.05,
        }

    def evaluate(
        self,
        evidence_count: int = 0,
        source_quality: float = 0.5,
        numerical_accuracy: float = 0.5,
        freshness: float = 0.5,
        contradictions_found: int = 0,
        contradictions_addressed: int = 0,
        completeness: float = 0.5,
        uncertainty_disclosed: bool = False,
        reproducible: bool = False,
    ) -> QualityResult:
        scores = {}

        coverage = min(evidence_count / 10, 1.0)
        scores[QualityDimension.EVIDENCE_COVERAGE.value] = coverage
        scores[QualityDimension.SOURCE_QUALITY.value] = min(source_quality, 1.0)
        scores[QualityDimension.NUMERICAL_ACCURACY.value] = min(numerical_accuracy, 1.0)
        scores[QualityDimension.FRESHNESS.value] = min(freshness, 1.0)

        if contradictions_found > 0:
            contradiction_score = contradictions_addressed / contradictions_found
        else:
            contradiction_score = 1.0
        scores[QualityDimension.CONTRADICTION_HANDLING.value] = contradiction_score
        scores[QualityDimension.COMPLETENESS.value] = min(completeness, 1.0)
        scores[QualityDimension.UNCERTAINTY.value] = 1.0 if uncertainty_disclosed else 0.3
        scores[QualityDimension.REPRODUCIBILITY.value] = 1.0 if reproducible else 0.3

        overall = sum(
            scores[dim] * self._weights[dim]
            for dim in QualityDimension
        )

        if overall >= 0.85:
            grade = "A"
        elif overall >= 0.7:
            grade = "B"
        elif overall >= 0.5:
            grade = "C"
        else:
            grade = "D"

        recommendations = []
        if coverage < 0.5:
            recommendations.append("Increase evidence coverage")
        if contradiction_score < 0.5:
            recommendations.append("Address more contradictions")
        if not uncertainty_disclosed:
            recommendations.append("Disclose uncertainty levels")
        if not reproducible:
            recommendations.append("Improve reproducibility")

        return QualityResult(
            overall_score=round(overall, 3),
            dimension_scores={k.value if hasattr(k, 'value') else k: v for k, v in scores.items()},
            grade=grade,
            recommendations=recommendations,
        )