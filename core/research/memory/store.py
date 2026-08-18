"""FININT OMEGA — Research memory store for persisting research context."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """A single memory entry in the research store."""

    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    response: str = ""
    sources: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ResearchMemoryStore:
    """In-memory store for research context and prior queries."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._entries: list[MemoryEntry] = []
        self._max_entries = max_entries

    def add(self, query: str, response: str = "", sources: list[str] | None = None, tags: list[str] | None = None, **metadata) -> MemoryEntry:
        entry = MemoryEntry(
            query=query, response=response,
            sources=sources or [], tags=tags or [], metadata=metadata,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        q = query.lower()
        scored: list[tuple[float, MemoryEntry]] = []
        for entry in self._entries:
            score = 0.0
            if q in entry.query.lower():
                score += 1.0
            if q in entry.response.lower():
                score += 0.5
            for tag in entry.tags:
                if q in tag.lower():
                    score += 0.3
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def get_recent(self, count: int = 10) -> list[MemoryEntry]:
        return self._entries[-count:]

    def get_by_tag(self, tag: str) -> list[MemoryEntry]:
        return [e for e in self._entries if tag in e.tags]

    def delete(self, entry_id: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.entry_id != entry_id]
        return len(self._entries) < before

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
