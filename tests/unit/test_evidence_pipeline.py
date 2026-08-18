"""Tests for Evidence Execution Pipeline — M15.5 Phase 7."""

from __future__ import annotations

import pytest

from core.ai.llm.base import LLMConfig, LLMMessage, LLMProvider, LLMResponse
from core.research.evidence_pipeline.pipeline import EvidencePipeline, PipelineStage
from core.research.deep_research.models import ResearchDepth, ResearchConfig


class MockLLM(LLMProvider):
    """Deterministic mock LLM."""

    def __init__(self) -> None:
        super().__init__("mock", LLMConfig(model="mock-model"))

    def _complete(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        content = "Evidence-grounded answer: revenue grew 5% YoY. Conclusion supported."
        return LLMResponse(
            content=content,
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
            latency_ms=1.0,
            cost_usd=0.001,
        )

    def health_check(self) -> bool:
        return True


def make_tool(name: str, output):
    def handler(**kwargs):
        return output
    handler.__name__ = name
    return handler


@pytest.fixture
def pipeline():
    p = EvidencePipeline()
    p.register_tool("market_data", make_tool("market_data", {"price": 150.0, "currency": "USD"}))
    p.register_tool("earnings_data", make_tool("earnings_data", "Revenue $10B, EPS $2.50"))
    p.register_tool("risk_analyzer", make_tool("risk_analyzer", {"var_95": 0.02, "volatility": 0.35}))
    return p


class TestPipelineBasics:
    def test_initialization(self):
        p = EvidencePipeline()
        assert p._planner is not None
        assert p._synthesizer is not None

    def test_register_tool(self, pipeline):
        assert "market_data" in pipeline._tools

    def test_set_llm(self):
        p = EvidencePipeline()
        p.set_llm(MockLLM())
        assert p._llm is not None

    def test_execute_empty_question(self, pipeline):
        result = pipeline.execute("")
        assert result.stages  # pipeline still executes stages

    def test_execute_pipeline_stages(self, pipeline):
        result = pipeline.execute("What is the price and earnings of AAPL?")
        assert PipelineStage.PLAN in result.stages
        assert PipelineStage.RETRIEVE in result.stages
        assert PipelineStage.TOOLS in result.stages
        assert PipelineStage.EVIDENCE in result.stages
        assert PipelineStage.CONTRADICTION in result.stages
        assert PipelineStage.LLM in result.stages
        assert PipelineStage.SYNTHESIS in result.stages
        assert PipelineStage.GRAPH in result.stages
        assert PipelineStage.AUDIT in result.stages

    def test_evidence_collected(self, pipeline):
        result = pipeline.execute("Price and earnings of AAPL?", symbol="AAPL")
        assert len(result.evidence) > 0
        source_types = {e.source_type for e in result.evidence}
        assert "market_data" in source_types or "earnings_data" in source_types

    def test_synthesis_created(self, pipeline):
        result = pipeline.execute("What is the valuation of AAPL?")
        assert result.synthesis is not None
        assert result.synthesis.confidence >= 0.0

    def test_graph_built(self, pipeline):
        result = pipeline.execute("What is the risk of AAPL?", symbol="AAPL")
        assert result.graph is not None
        assert result.graph.node_count() > 0


class TestPipelineLLM:
    def test_llm_answer_used(self):
        p = EvidencePipeline()
        p.set_llm(MockLLM())
        result = p.execute("Analyze AAPL earnings")
        assert "Evidence-grounded" in result.llm_answer

    def test_llm_answer_fallback_without_provider(self):
        p = EvidencePipeline()
        p.register_tool("market_data", make_tool("market_data", {"price": 150.0}))
        result = p.execute("price of AAPL", symbol="AAPL")
        assert "Evidence-based analysis" in result.llm_answer

    def test_audit_trail_recorded(self):
        p = EvidencePipeline()
        p.set_llm(MockLLM())
        result = p.execute("Analyze AAPL")
        trail = p._audit.get_trail(result.research_id)
        assert trail is not None
        assert len(trail.events) >= 3
        event_types = {e.event_type.value for e in trail.events}
        assert "model_called" in event_types

    def test_audit_tool_calls_recorded(self, pipeline):
        result = pipeline.execute("price of AAPL", symbol="AAPL")
        tool_calls = pipeline._audit.get_tool_calls(result.research_id)
        assert len(tool_calls) >= 1
        assert tool_calls[0].tool_name == "market_data"


class TestPipelineContradictions:
    def test_no_contradictions_no_conflicts(self):
        p = EvidencePipeline()
        result = p.execute("price of AAPL")
        # No evidence with supports/contradicts claims set -> no conflicts
        assert result.conflicts == []

    def test_conflicts_detected_with_claims(self):
        p = EvidencePipeline()
        from core.research.deep_research.models import EvidenceItem
        # Simulate evidence with conflicting claims
        ev1 = EvidenceItem(
            source_type="tool",
            source_id="a",
            content="Bullish thesis",
            supports_claim="AAPL will outperform",
            confidence=0.8,
        )
        ev2 = EvidenceItem(
            source_type="tool",
            source_id="b",
            content="Bearish data",
            contradicts_claim="AAPL will outperform",
            confidence=0.6,
        )
        result = p.execute("AAPL outlook")
        # pipeline's own evidence appended after; test detection directly
        conflicts = p._detect_contradictions([ev1, ev2])
        assert len(conflicts) == 1
        assert conflicts[0].severity == 0.8


class TestPipelineConfig:
    def test_custom_config(self, pipeline):
        config = ResearchConfig.for_depth(ResearchDepth.SHALLOW)
        result = pipeline.execute("What is the valuation of AAPL?", config=config)
        assert result.synthesis is not None

    def test_quant_executed_for_risk(self, pipeline):
        result = pipeline.execute("What is the risk profile of MSFT?", symbol="MSFT")
        assert any(e.source_type == "quant_risk" for e in result.evidence)


class TestPipelineResult:
    def test_to_dict(self, pipeline):
        result = pipeline.execute("price of AAPL")
        d = result.to_dict()
        assert d["research_id"] == result.research_id
        assert d["question"] == "price of AAPL"
        assert "evidence_count" in d
        assert "stages_executed" in d