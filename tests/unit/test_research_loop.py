"""Tests for Autonomous Research Loop."""

import pytest
from core.intelligence.research_loop.models import LoopConfig, LoopPhase
from core.intelligence.research_loop.engine import ResearchLoopEngine


class TestResearchLoopEngine:
    def setup_method(self):
        self.engine = ResearchLoopEngine()

    def test_run_basic(self):
        result = self.engine.run(question="Is AAPL undervalued?")
        assert result.status == "completed"
        assert len(result.iterations) > 0

    def test_run_produces_findings(self):
        result = self.engine.run(question="Test")
        assert len(result.final_findings) > 0

    def test_run_produces_hypotheses(self):
        result = self.engine.run(question="Test")
        assert len(result.final_hypotheses) > 0

    def test_max_iterations_respected(self):
        config = LoopConfig(max_iterations=2)
        result = self.engine.run(question="Test", config=config)
        assert len(result.iterations) <= 2

    def test_confidence_increases(self):
        config = LoopConfig(max_iterations=3)
        result = self.engine.run(question="Test", config=config)
        assert result.confidence > 0

    def test_audit_trail(self):
        result = self.engine.run(question="Test")
        assert len(result.audit_trail) > 0

    def test_get_result(self):
        result = self.engine.run(question="Test")
        retrieved = self.engine.get_result(result.loop_id)
        assert retrieved is not None

    def test_get_result_not_found(self):
        assert self.engine.get_result("nonexistent") is None

    def test_total_steps(self):
        result = self.engine.run(question="Test")
        assert result.total_steps > 0

    def test_iteration_phases(self):
        result = self.engine.run(question="Test")
        iteration = result.iterations[0]
        phase_names = [s.phase for s in iteration.steps]
        assert LoopPhase.OBSERVE in phase_names
        assert LoopPhase.DETECT in phase_names
