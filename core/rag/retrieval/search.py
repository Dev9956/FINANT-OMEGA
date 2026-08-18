"""FININT OMEGA — Hybrid retriever: vector + keyword search."""

from __future__ import annotations

import math
from collections import Counter

from pydantic import BaseModel, Field

from core.rag.embeddings.embedder import MockEmbedder


class RetrievalResult(BaseModel):
    """A single retrieval result."""

    chunk_id: str
    text: str
    source_id: str = ""
    vector_score: float = 0.0
    keyword_score: float = 0.0
    combined_score: float = 0.0
    metadata: dict = Field(default_factory=dict)


class HybridRetriever:
    """Combine vector similarity and keyword matching for retrieval."""

    def __init__(self, embedder: MockEmbedder | None = None, vector_weight: float = 0.6, keyword_weight: float = 0.4) -> None:
        self._embedder = embedder or MockEmbedder()
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight
        self._chunks: list[dict] = []
        self._embeddings: list[list[float]] = []

    def index(self, chunks: list[dict]) -> None:
        self._chunks = list(chunks)
        texts = [c.get("text", "") for c in self._chunks]
        self._embeddings = self._embedder.embed_batch(texts)

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower().strip(".,!?;:\"'") for w in text.split() if len(w) > 1]

    def _keyword_score(self, query_tokens: list[str], doc_text: str) -> float:
        doc_tokens = self._tokenize(doc_text)
        if not doc_tokens:
            return 0.0
        doc_freq = Counter(doc_tokens)
        total = len(doc_tokens)
        score = 0.0
        for qt in query_tokens:
            count = doc_freq.get(qt, 0)
            score += count / total
        return min(score, 1.0)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not self._chunks:
            return []
        query_emb = self._embedder.embed(query)
        query_tokens = self._tokenize(query)
        results: list[RetrievalResult] = []
        for i, chunk in enumerate(self._chunks):
            v_score = self._embedder.cosine_similarity(query_emb, self._embeddings[i])
            k_score = self._keyword_score(query_tokens, chunk.get("text", ""))
            combined = self._vector_weight * v_score + self._keyword_weight * k_score
            results.append(RetrievalResult(
                chunk_id=chunk.get("chunk_id", f"chunk_{i}"),
                text=chunk.get("text", ""),
                source_id=chunk.get("source_id", ""),
                vector_score=v_score,
                keyword_score=k_score,
                combined_score=combined,
                metadata=chunk.get("metadata", {}),
            ))
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[:top_k]

    def clear(self) -> None:
        self._chunks.clear()
        self._embeddings.clear()
