"""FININT OMEGA — Private search engine with hybrid search."""

from __future__ import annotations

import structlog

from core.data.private_rag.models import PrivateDocument, SearchResult
from core.data.private_rag.store import PrivateDocumentStore

logger = structlog.get_logger()


class PrivateSearchEngine:
    """Hybrid search engine over private documents with tenant isolation."""

    def __init__(self, store: PrivateDocumentStore) -> None:
        self._store = store

    def hybrid_search(self, query: str, owner_id: str, top_k: int = 5) -> list[SearchResult]:
        """Combine vector and keyword search results."""
        try:
            vector_results = self.vector_search(query, owner_id, top_k)
            keyword_results = self.keyword_search(query, owner_id, top_k)
            return self.merge_results(vector_results, keyword_results, top_k)
        except Exception as e:
            logger.error("hybrid_search_failed", error=str(e))
            return []

    def vector_search(self, query: str, owner_id: str, top_k: int = 5) -> list[SearchResult]:
        """Search by vector similarity (placeholder — uses keyword fallback)."""
        try:
            query_lower = query.lower()
            results: list[SearchResult] = []
            for doc in self._list_owner_docs(owner_id):
                if query_lower in doc.content.lower() or query_lower in doc.title.lower():
                    score = 1.0 if query_lower in doc.title.lower() else 0.5
                    results.append(
                        SearchResult(
                            doc_id=doc.doc_id,
                            title=doc.title,
                            content=doc.content[:500],
                            score=score,
                            metadata={"search_type": "vector"},
                        )
                    )
            results.sort(key=lambda r: r.score, reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []

    def keyword_search(self, query: str, owner_id: str, top_k: int = 5) -> list[SearchResult]:
        """Search by keyword match."""
        try:
            return self._store.search(query, owner_id, top_k)
        except Exception as e:
            logger.error("keyword_search_failed", error=str(e))
            return []

    def merge_results(
        self,
        vector_results: list[SearchResult],
        keyword_results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Merge two result sets, deduplicating by doc_id."""
        try:
            seen: dict[str, SearchResult] = {}
            for r in vector_results + keyword_results:
                if r.doc_id not in seen or r.score > seen[r.doc_id].score:
                    seen[r.doc_id] = r
            merged = sorted(seen.values(), key=lambda r: r.score, reverse=True)
            return merged[:top_k]
        except Exception as e:
            logger.error("merge_results_failed", error=str(e))
            return []

    def _list_owner_docs(self, owner_id: str) -> list[PrivateDocument]:
        """Internal helper to list owner's documents."""
        return self._store.list_documents(owner_id)
