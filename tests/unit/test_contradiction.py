"""Tests for Contradiction Hunter."""

import pytest
from core.intelligence.contradiction.models import (
    ContradictionCategory,
    ContradictionSeverity,
)
from core.intelligence.contradiction.detector import ContradictionDetector


class TestContradictionDetector:
    def setup_method(self):
        self.detector = ContradictionDetector()

    def test_management_vs_financials_positive_statement_declining_metrics(self):
        statements = ["Demand remains strong and growth is accelerating"]
        financials = {
            "revenue_growth": {"current": 5.0, "previous": 15.0},
            "margin_change": {"current": -8.0, "previous": 2.0},
        }
        contradictions = self.detector.detect_management_vs_financials(statements, financials)
        assert len(contradictions) > 0
        assert contradictions[0].category == ContradictionCategory.MANAGEMENT_VS_FINANCIALS

    def test_management_vs_financials_aligned(self):
        statements = ["Demand remains strong"]
        financials = {
            "revenue_growth": {"current": 15.0, "previous": 10.0},
        }
        contradictions = self.detector.detect_management_vs_financials(statements, financials)
        assert len(contradictions) == 0

    def test_guidance_vs_actual_miss(self):
        guidance = {"revenue": 100.0, "eps": 2.50}
        actuals = {"revenue": 75.0, "eps": 2.40}
        contradictions = self.detector.detect_guidance_vs_actual(guidance, actuals)
        assert len(contradictions) == 1
        assert contradictions[0].severity == ContradictionSeverity.CRITICAL

    def test_guidance_vs_actual_meet(self):
        guidance = {"revenue": 100.0, "eps": 2.50}
        actuals = {"revenue": 101.0, "eps": 2.55}
        contradictions = self.detector.detect_guidance_vs_actual(guidance, actuals)
        assert len(contradictions) == 0

    def test_narrative_vs_numbers_bullish_narrative_declining_metrics(self):
        narrative = "Strong growth momentum and accelerating demand"
        metrics = {
            "revenue": {"current": 100, "previous": 110},
            "margin": {"current": 20, "previous": 25},
            "orders": {"current": 50, "previous": 60},
        }
        result = self.detector.detect_narrative_vs_numbers(narrative, metrics)
        assert result.contradictions_found > 0
        assert result.overall_severity in (ContradictionSeverity.HIGH, ContradictionSeverity.MODERATE)

    def test_narrative_vs_numbers_aligned(self):
        narrative = "Strong growth momentum"
        metrics = {
            "revenue": {"current": 110, "previous": 100},
            "margin": {"current": 25, "previous": 20},
        }
        result = self.detector.detect_narrative_vs_numbers(narrative, metrics)
        assert result.contradictions_found == 0

    def test_earnings_vs_cashflow_divergence(self):
        earnings = {"net_income": 1000000, "growth_rate": 15.0}
        cashflow = {"operating_cashflow": -500000, "growth_rate": -20.0}
        contradictions = self.detector.detect_earnings_vs_cashflow(earnings, cashflow)
        assert len(contradictions) == 2

    def test_earnings_vs_cashflow_aligned(self):
        earnings = {"net_income": 1000000, "growth_rate": 15.0}
        cashflow = {"operating_cashflow": 1200000, "growth_rate": 12.0}
        contradictions = self.detector.detect_earnings_vs_cashflow(earnings, cashflow)
        assert len(contradictions) == 0

    def test_score_contradictions_empty(self):
        result = self.detector.score_contradictions([])
        assert result["score"] == 0

    def test_score_contradictions_critical(self):
        from core.intelligence.contradiction.models import ContradictionItem
        items = [
            ContradictionItem(
                category=ContradictionCategory.MANAGEMENT_VS_FINANCIALS,
                severity=ContradictionSeverity.CRITICAL,
                statement="test",
            )
        ]
        result = self.detector.score_contradictions(items)
        assert result["critical"] == 1
