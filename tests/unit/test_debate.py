"""Tests for AI Investment Debate Engine."""

import pytest
from core.intelligence.debate.models import (
    AnalystRole,
    DebateConfig,
)
from core.intelligence.debate.engine import DebateEngine


class TestDebateEngine:
    def setup_method(self):
        self.engine = DebateEngine()

    def test_run_debate_basic(self):
        result = self.engine.run_debate(
            question="Is AAPL attractive at current valuation?",
            evidence_items=["Revenue growth 15%", "P/E ratio elevated", "Strong cash flow"],
        )
        assert result.status == "completed"
        assert result.bull_argument is not None
        assert result.bear_argument is not None
        assert result.synthesis is not None

    def test_bull_analyst_finds_positive_evidence(self):
        result = self.engine.run_debate(
            question="Test",
            evidence_items=["Strong growth momentum", "Risk of decline", "Catalyst ahead"],
        )
        bull = result.bull_argument
        assert len(bull.key_points) > 0
        assert bull.confidence > 0

    def test_bear_analyst_finds_negative_evidence(self):
        result = self.engine.run_debate(
            question="Test",
            evidence_items=["Risk of decline", "Weak demand", "Strong growth"],
        )
        bear = result.bear_argument
        assert len(bear.key_points) > 0

    def test_neutral_verifier(self):
        result = self.engine.run_debate(
            question="Test",
            evidence_items=["Evidence A", "Evidence B", "Evidence C"],
        )
        assert len(result.neutral_verification) == 3

    def test_synthesis_produces_action(self):
        result = self.engine.run_debate(
            question="Test",
            evidence_items=["Growth catalyst", "Valuation risk", "Strong balance sheet"],
        )
        assert result.synthesis.recommended_action != ""
        assert result.synthesis.final_confidence >= 0

    def test_get_debate(self):
        result = self.engine.run_debate(question="Test")
        retrieved = self.engine.get_debate(result.debate_id)
        assert retrieved is not None
        assert retrieved.debate_id == result.debate_id

    def test_get_debate_not_found(self):
        assert self.engine.get_debate("nonexistent") is None

    def test_empty_evidence(self):
        result = self.engine.run_debate(question="Test", evidence_items=[])
        assert result.status == "completed"
        assert result.synthesis is not None

    def test_custom_config(self):
        config = DebateConfig(max_evidence_per_analyst=3, confidence_threshold=0.7)
        engine = DebateEngine(config=config)
        result = engine.run_debate(question="Test", evidence_items=["A", "B", "C", "D", "E"])
        assert len(result.bull_argument.key_points) <= 3

    def test_debate_timing(self):
        result = self.engine.run_debate(question="Test", evidence_items=["A", "B"])
        assert result.duration_ms >= 0
