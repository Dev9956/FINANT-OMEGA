"""Tests for Investment Thesis Engine."""

import pytest
from core.intelligence.thesis.models import (
    InvalidationCondition,
    ThesisConfidence,
    ThesisStatus,
    ThesisVersion,
    TriggerType,
)
from core.intelligence.thesis.thesis_engine import ThesisEngine


class TestThesisEngine:
    def setup_method(self):
        self.engine = ThesisEngine()

    def test_create_thesis(self):
        v = self.engine.create_thesis(
            symbol="AAPL",
            title="Apple Growth Thesis",
            bull_case="AI drives services growth",
            bear_case="iPhone demand weakens",
            confidence=0.8,
        )
        assert v.thesis_id
        assert v.version_number == 1
        assert v.bull_case == "AI drives services growth"
        assert v.status == ThesisStatus.ACTIVE
        assert v.confidence == 0.8
        assert v.confidence_level == ThesisConfidence.HIGH

    def test_get_thesis(self):
        v = self.engine.create_thesis(symbol="AAPL", title="Test")
        retrieved = self.engine.get_thesis(v.thesis_id)
        assert retrieved is not None
        assert retrieved.version_number == 1

    def test_get_thesis_not_found(self):
        assert self.engine.get_thesis("nonexistent") is None

    def test_update_thesis_creates_new_version(self):
        v = self.engine.create_thesis(symbol="AAPL", title="Test", confidence=0.7)
        updated = self.engine.update_thesis(
            v.thesis_id,
            change_summary="Updated bull case",
            reason="New product announcement",
            bull_case="AI + Vision Pro catalyst",
            confidence=0.8,
        )
        assert updated is not None
        assert updated.version_number == 2
        assert updated.bull_case == "AI + Vision Pro catalyst"
        assert updated.confidence == 0.8

    def test_update_thesis_not_found(self):
        assert self.engine.update_thesis("nonexistent") is None

    def test_thesis_history(self):
        v = self.engine.create_thesis(symbol="AAPL", title="Test", confidence=0.6)
        self.engine.update_thesis(v.thesis_id, confidence=0.7)
        self.engine.update_thesis(v.thesis_id, confidence=0.8)

        history = self.engine.get_thesis_history(v.thesis_id)
        assert history.total_versions == 3
        assert history.confidence_trend == [0.6, 0.7, 0.8]
        assert len(history.updates) == 2

    def test_add_invalidation_condition(self):
        v = self.engine.create_thesis(symbol="AAPL", title="Test")
        condition = InvalidationCondition(
            description="Revenue growth below 5%",
            metric="revenue_growth",
            threshold=5.0,
            comparator="lt",
            consecutive_periods=2,
        )
        self.engine.add_invalidation_condition(v.thesis_id, condition)
        assert len(self.engine._invalidation_conditions[v.thesis_id]) == 1

    def test_evaluate_thesis_strengthening(self):
        v = self.engine.create_thesis(symbol="AAPL", title="Test", confidence=0.7)
        evaluation = self.engine.evaluate_thesis(
            v.thesis_id,
            supporting_evidence=["e1", "e2", "e3"],
            contradicting_evidence=["e1"],
        )
        assert evaluation.health == "strengthening"
        assert evaluation.supporting_count == 3
        assert evaluation.contradicting_count == 1

    def test_evaluate_thesis_weakening(self):
        v = self.engine.create_thesis(symbol="AAPL", title="Test", confidence=0.7)
        evaluation = self.engine.evaluate_thesis(
            v.thesis_id,
            supporting_evidence=["e1"],
            contradicting_evidence=["e1", "e2", "e3"],
        )
        assert evaluation.health == "weakening"

    def test_evaluate_thesis_with_metrics(self):
        v = self.engine.create_thesis(symbol="AAPL", title="Test", confidence=0.7)
        condition = InvalidationCondition(
            description="Revenue growth below 5%",
            metric="revenue_growth",
            threshold=5.0,
            comparator="lt",
            consecutive_periods=1,
        )
        self.engine.add_invalidation_condition(v.thesis_id, condition)

        evaluation = self.engine.evaluate_thesis(
            v.thesis_id,
            metric_values={"revenue_growth": 3.0},
        )
        assert "Revenue growth below 5%" in evaluation.invalidation_met

    def test_list_theses(self):
        self.engine.create_thesis(symbol="AAPL", title="Apple")
        self.engine.create_thesis(symbol="MSFT", title="Microsoft")
        all_theses = self.engine.list_theses()
        assert len(all_theses) == 2

        aapl = self.engine.list_theses(symbol="AAPL")
        assert len(aapl) == 1

    def test_confidence_levels(self):
        assert self.engine._confidence_to_level(0.9) == ThesisConfidence.HIGH
        assert self.engine._confidence_to_level(0.7) == ThesisConfidence.MODERATE
        assert self.engine._confidence_to_level(0.5) == ThesisConfidence.LOW
        assert self.engine._confidence_to_level(0.2) == ThesisConfidence.VERY_LOW

    def test_condition_check(self):
        from core.intelligence.thesis.models import InvalidationCondition
        c = InvalidationCondition(description="lt test", metric="x", threshold=10.0, comparator="lt")
        assert self.engine._check_condition(5.0, c) is True
        assert self.engine._check_condition(15.0, c) is False

        c2 = InvalidationCondition(description="gt test", metric="x", threshold=10.0, comparator="gt")
        assert self.engine._check_condition(15.0, c2) is True
        assert self.engine._check_condition(5.0, c2) is False
