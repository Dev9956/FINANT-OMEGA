"""FININT OMEGA — Unit tests for advanced change detection."""

import pytest

from core.intelligence.change_detection.comparator import PeriodComparator
from core.intelligence.change_detection.detector import ChangeDetector
from core.intelligence.change_detection.models import (
    ChangeSeverity,
    ChangeType,
    ComparisonResult,
    DetectedChange,
)


class TestChangeDetector:
    """Test numerical, textual, sentiment change detection."""

    def setup_method(self):
        self.detector = ChangeDetector()

    def test_numerical_changes(self):
        a = {"revenue": 100, "profit": 20}
        b = {"revenue": 120, "profit": 18}
        changes = self.detector.detect_numerical_changes(a, b)
        rev = [c for c in changes if c.field == "revenue"]
        assert len(rev) == 1
        assert rev[0].change_pct == pytest.approx(20.0)

    def test_numerical_no_change(self):
        a = {"revenue": 100}
        b = {"revenue": 100}
        changes = self.detector.detect_numerical_changes(a, b)
        assert len(changes) == 0

    def test_numerical_new_field(self):
        a = {"revenue": 100}
        b = {"revenue": 100, "profit": 20}
        changes = self.detector.detect_numerical_changes(a, b)
        profit = [c for c in changes if c.field == "profit"]
        assert len(profit) == 1

    def test_numerical_removed_field(self):
        a = {"revenue": 100, "profit": 20}
        b = {"revenue": 100}
        changes = self.detector.detect_numerical_changes(a, b)
        profit = [c for c in changes if c.field == "profit"]
        assert len(profit) == 1

    def test_numerical_zero_baseline(self):
        a = {"revenue": 0}
        b = {"revenue": 50}
        changes = self.detector.detect_numerical_changes(a, b)
        assert changes[0].change_pct == 100.0

    def test_textual_changes(self):
        changes = self.detector.detect_textual_changes(
            "the company reported strong revenue growth",
            "the company reported weak revenue decline",
        )
        assert len(changes) >= 1
        assert changes[0].change_type == ChangeType.TEXTUAL

    def test_textual_no_change(self):
        changes = self.detector.detect_textual_changes("same text", "same text")
        assert len(changes) == 0

    def test_sentiment_changes(self):
        a = {"overall": 0.7, "sector": 0.5}
        b = {"overall": 0.3, "sector": 0.6}
        changes = self.detector.detect_sentiment_changes(a, b)
        overall = [c for c in changes if c.field == "overall"]
        assert len(overall) == 1
        assert overall[0].change_pct == pytest.approx(-40.0)

    def test_sentiment_no_significant_change(self):
        a = {"overall": 0.5}
        b = {"overall": 0.52}
        changes = self.detector.detect_sentiment_changes(a, b)
        assert len(changes) == 0

    def test_structural_changes(self):
        a = {"name": "str", "value": "str"}
        b = {"name": "str", "value": "str", "new_field": "str"}
        changes = self.detector.detect_structural_changes(a, b)
        assert any(c.field == "new_field" for c in changes)

    def test_guidance_changes(self):
        a = {"revenue_guidance": 500}
        b = {"revenue_guidance": 600}
        changes = self.detector.detect_guidance_changes(a, b)
        assert len(changes) == 1
        assert changes[0].change_pct == pytest.approx(20.0)

    def test_risk_changes(self):
        a = ["regulatory", "market"]
        b = ["market", "cyber"]
        changes = self.detector.detect_risk_changes(a, b)
        types = [(c.field, c.old_value, c.new_value) for c in changes]
        assert any(c.new_value == "cyber" for c in changes)
        assert any(c.old_value == "regulatory" for c in changes)

    def test_severity_classification(self):
        assert ChangeDetector._classify_severity(1.0) == ChangeSeverity.TRIVIAL
        assert ChangeDetector._classify_severity(3.0) == ChangeSeverity.MINOR
        assert ChangeDetector._classify_severity(7.0) == ChangeSeverity.MODERATE
        assert ChangeDetector._classify_severity(15.0) == ChangeSeverity.MAJOR
        assert ChangeDetector._classify_severity(25.0) == ChangeSeverity.CRITICAL


class TestPeriodComparator:
    """Test period comparison and summary generation."""

    def setup_method(self):
        self.comparator = PeriodComparator()

    def test_compare_periods(self):
        a = {"revenue": 100, "profit": 20}
        b = {"revenue": 130, "profit": 25}
        result = self.comparator.compare_periods(a, "Q1", b, "Q2", entity="TCS")
        assert isinstance(result, ComparisonResult)
        assert result.entity_a == "TCS"
        assert len(result.changes) >= 1

    def test_compute_significance_empty(self):
        assert self.comparator.compute_significance([]) == 0.0

    def test_compute_significance_with_changes(self):
        changes = [
            DetectedChange(
                change_type=ChangeType.NUMERICAL,
                severity=ChangeSeverity.CRITICAL,
                field="revenue",
                old_value=100,
                new_value=200,
                confidence=1.0,
            )
        ]
        sig = self.comparator.compute_significance(changes)
        assert sig > 0

    def test_generate_summary_no_changes(self):
        result = ComparisonResult(
            entity_a="TCS", entity_b="TCS", period_a="Q1", period_b="Q2"
        )
        summary = self.comparator.generate_summary(result)
        assert "No significant changes" in summary

    def test_generate_summary_with_changes(self):
        result = ComparisonResult(
            entity_a="TCS",
            entity_b="TCS",
            period_a="Q1",
            period_b="Q2",
            changes=[
                DetectedChange(
                    change_type=ChangeType.NUMERICAL,
                    severity=ChangeSeverity.MAJOR,
                    field="revenue",
                    old_value=100,
                    new_value=150,
                    confidence=0.9,
                )
            ],
            overall_significance=0.8,
        )
        summary = self.comparator.generate_summary(result)
        assert "Q1" in summary
        assert "Q2" in summary
