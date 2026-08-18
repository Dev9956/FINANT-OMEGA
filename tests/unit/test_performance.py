"""Performance benchmark tests — M15.5 Phase 10.

Measures latency of core operations against reasonable thresholds.
These are functional performance gates, not micro-benchmarks.
"""

from __future__ import annotations

import time

import pytest

from core.research.evidence_pipeline.pipeline import EvidencePipeline
from core.storage.base import MockObjectStorage
from core.ai.llm.base import ModelTier, ModelRouter


def make_tool(name, output):
    def handler(**kwargs):
        return output
    return handler


class TestPipelineLatency:
    def test_pipeline_completes_under_2s(self):
        p = EvidencePipeline()
        p.register_tool("market_data", make_tool("market_data", {"price": 150.0}))
        p.register_tool("earnings_data", make_tool("earnings_data", "Revenue $10B"))
        start = time.perf_counter()
        result = p.execute("Analyze AAPL", symbol="AAPL")
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0
        assert result.synthesis is not None

    def test_multiple_runs_stable(self):
        p = EvidencePipeline()
        p.register_tool("market_data", make_tool("market_data", {"price": 150.0}))
        times = []
        for _ in range(5):
            start = time.perf_counter()
            p.execute("price of AAPL", symbol="AAPL")
            times.append(time.perf_counter() - start)
        avg = sum(times) / len(times)
        assert avg < 1.0  # avg sub-second for mock pipeline


class TestStoragePerformance:
    def test_mock_storage_1000_ops(self):
        storage = MockObjectStorage()
        start = time.perf_counter()
        for i in range(1000):
            storage.put(f"k{i}", b"x" * 100)
        for i in range(1000):
            storage.get(f"k{i}")
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0
        assert len(storage.list(limit=5000)) == 1000


class TestVectorSearchPerformance:
    def test_search_1000_vectors(self):
        from core.rag.retrieval.vector_index import IndexedChunk, VectorIndex
        import random
        idx = VectorIndex()
        for i in range(1000):
            vec = [random.random() for _ in range(8)]
            idx.add(IndexedChunk(chunk_id=str(i), text=f"doc {i}", embedding=vec))
        query = [random.random() for _ in range(8)]
        start = time.perf_counter()
        results = idx.search(query, top_k=10)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0
        assert len(results) == 10


class TestModelRouterLatency:
    def test_routing_fast(self):
        from core.ai.llm.base import LLMConfig, LLMMessage, LLMProvider, LLMResponse
        from core.ai.llm.base import ModelRouter

        class Dummy(LLMProvider):
            def __init__(self):
                super().__init__("dummy", LLMConfig())

            def _complete(self, messages, **kwargs):
                return LLMResponse(content="x", model="m", usage={}, finish_reason="stop", latency_ms=0)

            def health_check(self):
                return True

        router = ModelRouter()
        dummy = Dummy()
        router.register_provider(ModelTier.FAST, dummy)
        router.register_provider(ModelTier.BALANCED, dummy)
        router.register_provider(ModelTier.REASONING, dummy)
        start = time.perf_counter()
        for i in range(1000):
            router.route_query("what is the price")
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0


class TestAuthPerformance:
    def test_jwt_roundtrip(self):
        from core.auth.security import create_access_token, decode_token
        start = time.perf_counter()
        for _ in range(100):
            token = create_access_token("user", "analyst", secret_key="test-key")
            decode_token(token, secret_key="test-key")
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0