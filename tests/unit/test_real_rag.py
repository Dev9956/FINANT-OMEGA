"""Tests for real RAG components — M15.5 Phase 3."""

from __future__ import annotations

import os

import pytest

from core.rag.embeddings.embedder import (
    BaseEmbedder,
    MockEmbedder,
    get_embedder,
)
from core.rag.retrieval.vector_index import (
    IndexedChunk,
    SearchResult,
    VectorIndex,
)


class TestMockEmbedder:
    def test_embed_returns_vector(self):
        embedder = MockEmbedder(dim=128)
        vec = embedder.embed("Hello world")
        assert len(vec) == 128
        assert all(isinstance(v, float) for v in vec)

    def test_embed_deterministic(self):
        embedder = MockEmbedder(dim=128)
        vec1 = embedder.embed("Hello world")
        vec2 = embedder.embed("Hello world")
        assert vec1 == vec2

    def test_embed_different_texts(self):
        embedder = MockEmbedder(dim=128)
        vec1 = embedder.embed("Hello world")
        vec2 = embedder.embed("Goodbye world")
        assert vec1 != vec2

    def test_embed_batch(self):
        embedder = MockEmbedder(dim=64)
        vecs = embedder.embed_batch(["a", "b", "c"])
        assert len(vecs) == 3
        assert all(len(v) == 64 for v in vecs)

    def test_cosine_similarity(self):
        embedder = MockEmbedder()
        vec1 = embedder.embed("AAPL stock price")
        vec2 = embedder.embed("Apple stock price")
        vec3 = embedder.embed("Tesla stock price")
        sim_12 = embedder.cosine_similarity(vec1, vec2)
        sim_13 = embedder.cosine_similarity(vec1, vec3)
        # Mock embedder doesn't guarantee semantic similarity
        # but should produce valid scores
        assert -1.0 <= sim_12 <= 1.0
        assert -1.0 <= sim_13 <= 1.0

    def test_dimension_property(self):
        embedder = MockEmbedder(dim=256)
        assert embedder.dimension == 256


class TestGetEmbedder:
    def test_mock_embedder(self):
        embedder = get_embedder(use_real=False)
        assert isinstance(embedder, MockEmbedder)

    def test_mock_fallback(self):
        # Without OPENAI_API_KEY, should fallback to mock
        embedder = get_embedder(use_real=True)
        assert isinstance(embedder, MockEmbedder)


class TestVectorIndex:
    def test_add_and_get(self):
        index = VectorIndex()
        chunk = IndexedChunk(
            chunk_id="c1",
            text="AAPL stock price is $150",
            embedding=[0.1, 0.2, 0.3, 0.4],
            company="AAPL",
        )
        index.add(chunk)
        assert index.size() == 1
        retrieved = index.get("c1")
        assert retrieved is not None
        assert retrieved.text == "AAPL stock price is $150"

    def test_add_batch(self):
        index = VectorIndex()
        chunks = [
            IndexedChunk(chunk_id=f"c{i}", text=f"text {i}", embedding=[0.1 * i, 0.2, 0.3])
            for i in range(5)
        ]
        index.add_batch(chunks)
        assert index.size() == 5

    def test_remove(self):
        index = VectorIndex()
        chunk = IndexedChunk(chunk_id="c1", text="text", embedding=[0.1, 0.2, 0.3])
        index.add(chunk)
        assert index.remove("c1") is True
        assert index.size() == 0
        assert index.remove("c1") is False

    def test_dimension_mismatch(self):
        index = VectorIndex()
        chunk1 = IndexedChunk(chunk_id="c1", text="text", embedding=[0.1, 0.2, 0.3])
        chunk2 = IndexedChunk(chunk_id="c2", text="text", embedding=[0.1, 0.2])
        index.add(chunk1)
        with pytest.raises(ValueError):
            index.add(chunk2)

    def test_search_basic(self):
        index = VectorIndex()
        chunks = [
            IndexedChunk(chunk_id="c1", text="AAPL stock", embedding=[1.0, 0.0, 0.0]),
            IndexedChunk(chunk_id="c2", text="GOOGL stock", embedding=[0.0, 1.0, 0.0]),
            IndexedChunk(chunk_id="c3", text="MSFT stock", embedding=[0.0, 0.0, 1.0]),
        ]
        index.add_batch(chunks)

        # Query similar to c1
        results = index.search([0.9, 0.1, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0].chunk.chunk_id == "c1"
        assert results[0].score > results[1].score

    def test_search_with_filters(self):
        index = VectorIndex()
        chunks = [
            IndexedChunk(chunk_id="c1", text="AAPL Q1", embedding=[1.0, 0.0], company="AAPL"),
            IndexedChunk(chunk_id="c2", text="GOOGL Q1", embedding=[0.9, 0.1], company="GOOGL"),
        ]
        index.add_batch(chunks)

        results = index.search([1.0, 0.0], top_k=10, filters={"company": "AAPL"})
        assert len(results) == 1
        assert results[0].chunk.company == "AAPL"

    def test_search_empty_index(self):
        index = VectorIndex()
        results = index.search([0.1, 0.2, 0.3], top_k=5)
        assert len(results) == 0

    def test_search_min_score(self):
        index = VectorIndex()
        chunk = IndexedChunk(chunk_id="c1", text="text", embedding=[1.0, 0.0])
        index.add(chunk)

        results = index.search([0.0, 1.0], top_k=5, min_score=0.5)
        assert len(results) == 0

    def test_stats(self):
        index = VectorIndex()
        chunks = [
            IndexedChunk(chunk_id="c1", text="text", embedding=[0.1, 0.2], company="AAPL", source_id="sec"),
            IndexedChunk(chunk_id="c2", text="text", embedding=[0.3, 0.4], company="GOOGL", source_id="news"),
        ]
        index.add_batch(chunks)
        stats = index.get_stats()
        assert stats["total_chunks"] == 2
        assert "AAPL" in stats["companies"]
        assert "sec" in stats["sources"]


class TestSearchResult:
    def test_result_fields(self):
        chunk = IndexedChunk(chunk_id="c1", text="text", embedding=[0.1])
        result = SearchResult(chunk=chunk, score=0.95, rank=1)
        assert result.chunk.chunk_id == "c1"
        assert result.score == 0.95
        assert result.rank == 1
