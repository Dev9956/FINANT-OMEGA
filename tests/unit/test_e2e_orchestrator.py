"""Tests for E2E research orchestrator — M15.5 Phase 8."""

from __future__ import annotations

import pytest

from core.research.e2e.orchestrator import E2EResearchOrchestrator, build_e2e_orchestrator
from core.research.evidence_pipeline.pipeline import PipelineStage


@pytest.fixture
def orchestrator():
    return E2EResearchOrchestrator()


class TestE2EOrchestrator:
    def test_build(self):
        orch = build_e2e_orchestrator()
        assert isinstance(orch, E2EResearchOrchestrator)

    def test_default_mode_is_dev(self, orchestrator):
        assert orchestrator._use_real is False

    def test_run_market_research(self, orchestrator):
        result = orchestrator.run("What is the price of AAPL?", symbol="AAPL")
        assert PipelineStage.TOOLS in result.stages
        assert len(result.evidence) > 0

    def test_run_earnings(self, orchestrator):
        result = orchestrator.run("What are the latest earnings for MSFT?", symbol="MSFT")
        assert result.synthesis is not None

    def test_run_valuation(self, orchestrator):
        result = orchestrator.run("Is GOOGL fairly valued?", symbol="GOOGL")
        assert result.stages  # pipeline ran

    def test_run_macro(self, orchestrator):
        result = orchestrator.run("What is the current inflation rate?")
        assert result.synthesis is not None

    def test_all_stages_executed(self, orchestrator):
        result = orchestrator.run("What is the risk profile of AAPL?", symbol="AAPL")
        expected = {
            PipelineStage.PLAN,
            PipelineStage.TOOLS,
            PipelineStage.QUANT,
            PipelineStage.EVIDENCE,
            PipelineStage.CONTRADICTION,
            PipelineStage.SYNTHESIS,
            PipelineStage.GRAPH,
            PipelineStage.AUDIT,
        }
        assert expected.issubset(set(result.stages))

    def test_result_serializable(self, orchestrator):
        result = orchestrator.run("Analyze AAPL", symbol="AAPL")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["research_id"]


class TestE2EFetchFallback:
    def test_market_fallback_to_mock(self, orchestrator):
        results = orchestrator._fetch_with_fallback("market_data", "AAPL", "")
        assert results  # non-empty even in dev mode

    def test_fetch_records_have_data(self, orchestrator):
        results = orchestrator._fetch_with_fallback("market_data", "AAPL", "")
        assert all("_quality" in r for r in results)