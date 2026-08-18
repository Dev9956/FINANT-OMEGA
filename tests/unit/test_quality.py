"""Tests for Research Quality Score."""

import pytest
from core.intelligence.quality.engine import QualityEngine


class TestQualityEngine:
    def setup_method(self):
        self.engine = QualityEngine()

    def test_evaluate_high_quality(self):
        result = self.engine.evaluate(
            evidence_count=15, source_quality=0.9, numerical_accuracy=0.95,
            freshness=0.8, contradictions_found=3, contradictions_addressed=3,
            completeness=0.9, uncertainty_disclosed=True, reproducible=True,
        )
        assert result.overall_score >= 0.8
        assert result.grade == "A"

    def test_evaluate_low_quality(self):
        result = self.engine.evaluate(
            evidence_count=2, source_quality=0.3, numerical_accuracy=0.4,
            freshness=0.2, contradictions_found=5, contradictions_addressed=1,
            completeness=0.3,
        )
        assert result.overall_score < 0.5
        assert result.grade == "D"

    def test_evaluate_medium_quality(self):
        result = self.engine.evaluate(
            evidence_count=8, source_quality=0.7, numerical_accuracy=0.8,
            freshness=0.6, contradictions_found=2, contradictions_addressed=2,
            completeness=0.7, uncertainty_disclosed=True,
        )
        assert result.grade in ("B", "C")

    def test_recommendations_generated(self):
        result = self.engine.evaluate(evidence_count=1, source_quality=0.3)
        assert len(result.recommendations) > 0

    def test_dimension_scores(self):
        result = self.engine.evaluate(evidence_count=10, source_quality=0.8)
        assert len(result.dimension_scores) == 8