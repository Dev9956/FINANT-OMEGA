"""FININT OMEGA — Simple reranker for retrieval results."""

from __future__ import annotations

from pydantic import BaseModel

from core.rag.retrieval.search import RetrievalResult


class RerankedResult(BaseModel):
    """A reranked retrieval result."""

    chunk_id: str
    text: str
    source_id: str = ""
    original_score: float = 0.0
    reranked_score: float = 0.0
    metadata: dict = {}


class SimpleReranker:
    """Rerank retrieval results using a simple scoring heuristic."""

    def __init__(self, query_boost: float = 1.5, length_penalty: float = 0.1) -> None:
        self._query_boost = query_boost
        self._length_penalty = length_penalty

    def _count_query_terms(self, text: str, query_terms: list[str]) -> int:
        text_lower = text.lower()
        return sum(1 for t in query_terms if t.lower() in text_lower)

    def rerank(self, query: str, results: list[RetrievalResult], top_k: int = 5) -> list[RerankedResult]:
        query_terms = query.split()
        reranked: list[RerankedResult] = []
        for r in results:
            term_hits = self._count_query_terms(r.text, query_terms)
            bonus = term_hits * self._query_boost
            length_factor = max(0, 1 - len(r.text) / 10000 * self._length_penalty)
            new_score = (r.combined_score + bonus) * length_factor
            reranked.append(RerankedResult(
                chunk_id=r.chunk_id,
                text=r.text,
                source_id=r.source_id,
                original_score=r.combined_score,
                reranked_score=new_score,
                metadata=r.metadata,
            ))
        reranked.sort(key=lambda x: x.reranked_score, reverse=True)
        return reranked[:top_k]
