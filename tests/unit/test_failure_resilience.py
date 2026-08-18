"""Tests for failure resilience — M15.5 Phase 9.

Verifies graceful degradation when real services fail:
data providers down, LLM unavailable, retrieval failures, DB connection issues.
"""

from __future__ import annotations

import pytest

from core.ai.llm.base import LLMConfig, LLMMessage, LLMProvider, LLMResponse
from core.research.evidence_pipeline.pipeline import EvidencePipeline, PipelineStage
from core.storage.base import MockObjectStorage, StorageConfig, get_storage


class FailingLLM(LLMProvider):
    """LLM provider that always fails."""

    def __init__(self) -> None:
        super().__init__("failing", LLMConfig(model="failing", max_retries=2))

    def _complete(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        raise ConnectionError("LLM service unreachable")

    def health_check(self) -> bool:
        return False


class FailingEmbedder:
    """Embedder that fails on embed."""

    def embed(self, text: str):
        raise RuntimeError("Embedding service down")

    def embed_batch(self, texts: list[str]):
        raise RuntimeError("Embedding service down")


class TestDataProviderFailure:
    def test_missing_connector_falls_back(self):
        from core.research.e2e.orchestrator import E2EResearchOrchestrator
        orch = E2EResearchOrchestrator()
        results = orch._fetch_with_fallback("market_data", "NONEXISTENT_XYZ", "")
        assert results  # non-empty fallback

    def test_pipeline_survives_tool_failure(self):
        def failing_tool(**kwargs):
            raise ConnectionError("data provider down")
        p = EvidencePipeline()
        p.register_tool("market_data", failing_tool)
        result = p.execute("What is the price of AAPL?", symbol="AAPL")
        assert result.stages
        assert PipelineStage.TOOLS in result.stages

    def test_all_tools_failing_still_completes(self):
        def fail(**kwargs):
            raise RuntimeError("boom")
        p = EvidencePipeline()
        p.register_tool("market_data", fail)
        p.register_tool("earnings_data", fail)
        p.register_tool("fundamentals", fail)
        result = p.execute("Analyze AAPL", symbol="AAPL")
        assert result.synthesis is not None


class TestLLMFailure:
    def test_pipeline_falls_back_on_llm_failure(self):
        p = EvidencePipeline()
        p.set_llm(FailingLLM())
        p.register_tool("market_data", lambda **kw: {"price": 100})
        result = p.execute("Analyze AAPL", symbol="AAPL")
        # Should fall back to deterministic synthesis, not crash
        assert result.synthesis is not None
        assert result.llm_answer  # fallback text present

    def test_failing_llm_survives_multiple_retries(self):
        llm = FailingLLM()
        with pytest.raises(Exception):
            llm.complete([LLMMessage(role="user", content="hi")])


class TestRetrievalFailure:
    def test_retrieval_failure_graceful(self):
        p = EvidencePipeline()
        p.set_retrieval(FailingEmbedder())
        result = p.execute("Analyze AAPL", symbol="AAPL")
        assert result.stages
        assert PipelineStage.RETRIEVE in result.stages

    def test_retrieval_none(self):
        p = EvidencePipeline()
        p.register_tool("market_data", lambda **kw: {"price": 100})
        result = p.execute("Analyze AAPL", symbol="AAPL")
        assert result.evidence  # tools still produce evidence


class TestStorageFailure:
    def test_mock_storage_always_works(self):
        storage = MockObjectStorage()
        obj = storage.put("test.txt", b"content")
        assert obj.key == "test.txt"

    def test_storage_fallback_on_unknown(self):
        storage = get_storage(StorageConfig(backend="s3"))
        assert isinstance(storage, MockObjectStorage)


class TestDatabaseFailure:
    @pytest.mark.asyncio
    async def test_repo_fallback_on_bad_dsn(self):
        from core.persistence.base import RepositoryConfig
        from core.persistence.thesis_repository import ThesisRepository
        repo = ThesisRepository(RepositoryConfig(
            postgres_dsn="postgresql://bad:bad@localhost:1/nonexistent",
            use_mock=False,
        ))
        # initialize should not crash - falls back to mock
        await repo.initialize()
        assert repo._pool is None  # fallback to mock


class TestExtremeInputs:
    def test_empty_question(self):
        p = EvidencePipeline()
        result = p.execute("")
        assert result.stages

    def test_very_long_question(self):
        p = EvidencePipeline()
        q = "What is " + "data " * 200 + "?"
        result = p.execute(q, symbol="AAPL")
        assert result.synthesis is not None

    def test_special_chars_question(self):
        p = EvidencePipeline()
        result = p.execute("What is A?A?L's !@#$%^&*() valuation?")
        assert result.synthesis is not None

    def test_unicode_question(self):
        p = EvidencePipeline()
        result = p.execute("Analyser la valorisation de éèçà")
        assert result.stages