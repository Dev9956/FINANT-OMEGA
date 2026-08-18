"""Tests for Narrative vs Numbers engine."""

import pytest
from core.intelligence.narrative.models import AlignmentLevel
from core.intelligence.narrative.analyzer import NarrativeAnalyzer


class TestNarrativeAnalyzer:
    def setup_method(self):
        self.analyzer = NarrativeAnalyzer()

    def test_high_alignment_bullish(self):
        narrative = "Strong growth momentum and accelerating demand"
        metrics = {
            "revenue": {"current": 110, "previous": 100},
            "margin": {"current": 25, "previous": 22},
            "orders": {"current": 60, "previous": 50},
        }
        result = self.analyzer.analyze(narrative, metrics)
        assert result.alignment_level == AlignmentLevel.HIGH_ALIGNMENT
        assert result.alignment_score >= 0.75
        assert len(result.supporting_signals) > 0

    def test_high_alignment_bearish(self):
        narrative = "Declining margins and weakening demand"
        metrics = {
            "revenue": {"current": 90, "previous": 100},
            "margin": {"current": 18, "previous": 22},
        }
        result = self.analyzer.analyze(narrative, metrics)
        assert result.alignment_level == AlignmentLevel.HIGH_ALIGNMENT

    def test_low_alignment_divergence(self):
        narrative = "Strong growth momentum"
        metrics = {
            "revenue": {"current": 90, "previous": 100},
            "margin": {"current": 18, "previous": 22},
            "orders": {"current": 40, "previous": 50},
        }
        result = self.analyzer.analyze(narrative, metrics)
        assert result.alignment_level == AlignmentLevel.LOW_ALIGNMENT
        assert len(result.conflicting_signals) > 0

    def test_insufficient_data(self):
        narrative = "Growth is strong"
        metrics = {}
        result = self.analyzer.analyze(narrative, metrics)
        assert result.alignment_level == AlignmentLevel.INSUFFICIENT_DATA

    def test_narrative_components_extracted(self):
        narrative = "Growth is strong but there are risks"
        metrics = {"revenue": {"current": 100, "previous": 90}}
        result = self.analyzer.analyze(narrative, metrics)
        assert len(result.narrative_components) >= 1

    def test_quantitative_signals_extracted(self):
        narrative = "Test"
        metrics = {
            "revenue": {"current": 100, "previous": 90},
            "margin": {"current": 20, "previous": 25},
        }
        result = self.analyzer.analyze(narrative, metrics)
        assert len(result.quantitative_signals) == 2
        assert result.quantitative_signals[0].direction == "up"
        assert result.quantitative_signals[1].direction == "down"

    def test_metric_mappings(self):
        narrative = "Test"
        metrics = {"rev": {"current": 100, "previous": 90}}
        mappings = {"rev": "Revenue Growth"}
        result = self.analyzer.analyze(narrative, metrics, metric_mappings=mappings)
        assert result.quantitative_signals[0].metric == "Revenue Growth"

    def test_empty_narrative(self):
        narrative = ""
        metrics = {"revenue": {"current": 100, "previous": 90}}
        result = self.analyzer.analyze(narrative, metrics)
        assert result.alignment_level in (AlignmentLevel.MODERATE_ALIGNMENT, AlignmentLevel.LOW_ALIGNMENT, AlignmentLevel.INSUFFICIENT_DATA)
