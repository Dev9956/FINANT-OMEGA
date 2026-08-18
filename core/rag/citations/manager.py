"""FININT OMEGA — Citation manager for source tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A citation linking generated text to source material."""

    citation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    chunk_id: str = ""
    text_snippet: str = ""
    page: int | None = None
    section: str = ""
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)


class CitationManager:
    """Track and manage citations for generated content."""

    def __init__(self) -> None:
        self._citations: dict[str, Citation] = {}
        self._response_citations: dict[str, list[str]] = {}

    def add_citation(self, source_id: str, chunk_id: str = "", text_snippet: str = "", **kwargs) -> Citation:
        citation = Citation(
            source_id=source_id,
            chunk_id=chunk_id,
            text_snippet=text_snippet,
            **kwargs,
        )
        self._citations[citation.citation_id] = citation
        return citation

    def link_to_response(self, response_id: str, citation_id: str) -> None:
        if response_id not in self._response_citations:
            self._response_citations[response_id] = []
        if citation_id not in self._response_citations[response_id]:
            self._response_citations[response_id].append(citation_id)

    def get_citations_for_response(self, response_id: str) -> list[Citation]:
        ids = self._response_citations.get(response_id, [])
        return [self._citations[cid] for cid in ids if cid in self._citations]

    def get_citation(self, citation_id: str) -> Citation | None:
        return self._citations.get(citation_id)

    def get_all_citations(self) -> list[Citation]:
        return list(self._citations.values())

    def format_footnotes(self, response_id: str) -> str:
        citations = self.get_citations_for_response(response_id)
        if not citations:
            return ""
        lines = []
        for i, c in enumerate(citations, 1):
            lines.append(f"[{i}] Source: {c.source_id} | {c.text_snippet[:80]}...")
        return "\n".join(lines)

    def clear(self) -> None:
        self._citations.clear()
        self._response_citations.clear()
