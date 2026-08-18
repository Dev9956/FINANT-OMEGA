"""FININT OMEGA — In-memory vector index for RAG retrieval."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class IndexedChunk:
    """A chunk with its embedding and metadata."""
    chunk_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    source_id: str = ""
    document_id: str = ""
    company: str = ""
    date: str = ""
    page: int | None = None
    section: str = ""
    content_hash: str = ""


@dataclass
class SearchResult:
    """A search result with score and metadata."""
    chunk: IndexedChunk
    score: float
    rank: int


class VectorIndex:
    """In-memory vector index with cosine similarity search.

    Supports:
    - Add/remove/update chunks
    - Cosine similarity search
    - Filtered search (by company, date, source, etc.)
    - Metadata filtering
    """

    def __init__(self) -> None:
        self._chunks: dict[str, IndexedChunk] = {}
        self._dimension: int | None = None

    def add(self, chunk: IndexedChunk) -> None:
        """Add a chunk to the index."""
        if self._dimension is None:
            self._dimension = len(chunk.embedding)
        elif len(chunk.embedding) != self._dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self._dimension}, "
                f"got {len(chunk.embedding)}"
            )
        self._chunks[chunk.chunk_id] = chunk

    def add_batch(self, chunks: list[IndexedChunk]) -> None:
        """Add multiple chunks."""
        for chunk in chunks:
            self.add(chunk)

    def remove(self, chunk_id: str) -> bool:
        """Remove a chunk by ID."""
        if chunk_id in self._chunks:
            del self._chunks[chunk_id]
            return True
        return False

    def get(self, chunk_id: str) -> IndexedChunk | None:
        """Get a chunk by ID."""
        return self._chunks.get(chunk_id)

    def size(self) -> int:
        """Return the number of indexed chunks."""
        return len(self._chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        min_score: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar chunks using cosine similarity.

        Args:
            query_embedding: The query vector.
            top_k: Number of results to return.
            min_score: Minimum similarity score.
            filters: Optional filters (company, date, source_id, etc.).
        """
        if not self._chunks:
            return []

        # Filter chunks
        candidates = list(self._chunks.values())
        if filters:
            candidates = self._apply_filters(candidates, filters)

        # Compute similarities
        results: list[SearchResult] = []
        for chunk in candidates:
            score = self._cosine_similarity(query_embedding, chunk.embedding)
            if score >= min_score:
                results.append(SearchResult(chunk=chunk, score=score, rank=0))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        # Assign ranks and return top_k
        for i, result in enumerate(results[:top_k]):
            result.rank = i + 1

        return results[:top_k]

    def search_by_text(
        self,
        query: str,
        embedder: Any,
        top_k: int = 10,
        min_score: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search by text query (embeds the query first)."""
        query_embedding = embedder.embed(query)
        return self.search(query_embedding, top_k, min_score, filters)

    def _apply_filters(
        self, chunks: list[IndexedChunk], filters: dict[str, Any]
    ) -> list[IndexedChunk]:
        """Apply metadata filters."""
        filtered = []
        for chunk in chunks:
            match = True
            for key, value in filters.items():
                if hasattr(chunk, key):
                    chunk_value = getattr(chunk, key)
                    if isinstance(value, list):
                        if chunk_value not in value:
                            match = False
                            break
                    elif chunk_value != value:
                        match = False
                        break
                elif key in chunk.metadata:
                    chunk_value = chunk.metadata[key]
                    if isinstance(value, list):
                        if chunk_value not in value:
                            match = False
                            break
                    elif chunk_value != value:
                        match = False
                        break
                else:
                    match = False
                    break
            if match:
                filtered.append(chunk)
        return filtered

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "total_chunks": len(self._chunks),
            "dimension": self._dimension,
            "companies": list(set(c.company for c in self._chunks.values() if c.company)),
            "sources": list(set(c.source_id for c in self._chunks.values() if c.source_id)),
        }
