"""FININT OMEGA — Thesis tracker: maintain and monitor investment theses."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ThesisStatus(str, Enum):
    ACTIVE = "active"
    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    INVALIDATED = "invalidated"
    CLOSED = "closed"


class Thesis(BaseModel):
    """An investment thesis for a security."""

    thesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    title: str
    bull_case: str = ""
    bear_case: str = ""
    key_catalysts: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    status: ThesisStatus = ThesisStatus.ACTIVE
    confidence: float = 0.7
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    events: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ThesisTracker:
    """Track investment theses and monitor thesis health over time."""

    def __init__(self) -> None:
        self._theses: dict[str, Thesis] = {}

    def create_thesis(self, symbol: str, title: str, **kwargs) -> Thesis:
        thesis = Thesis(symbol=symbol, title=title, **kwargs)
        self._theses[thesis.thesis_id] = thesis
        return thesis

    def get_thesis(self, thesis_id: str) -> Thesis | None:
        return self._theses.get(thesis_id)

    def get_theses_for_symbol(self, symbol: str) -> list[Thesis]:
        return [t for t in self._theses.values() if t.symbol == symbol]

    def list_active(self) -> list[Thesis]:
        return [t for t in self._theses.values() if t.status in (ThesisStatus.ACTIVE, ThesisStatus.STRENGTHENED, ThesisStatus.WEAKENED)]

    def update_thesis(self, thesis_id: str, **kwargs) -> Thesis | None:
        thesis = self._theses.get(thesis_id)
        if thesis is None:
            return None
        updated = thesis.model_copy(update={**kwargs, "updated_at": datetime.now(timezone.utc)})
        self._theses[thesis_id] = updated
        return updated

    def add_event(self, thesis_id: str, event: dict) -> Thesis | None:
        thesis = self._theses.get(thesis_id)
        if thesis is None:
            return None
        events = list(thesis.events)
        events.append({**event, "timestamp": datetime.now(timezone.utc).isoformat()})
        return self.update_thesis(thesis_id, events=events)

    def evaluate_health(self, thesis_id: str) -> dict:
        thesis = self._theses.get(thesis_id)
        if thesis is None:
            return {"error": "Thesis not found"}
        recent_events = thesis.events[-5:] if thesis.events else []
        positive = sum(1 for e in recent_events if e.get("sentiment", 0) > 0)
        negative = sum(1 for e in recent_events if e.get("sentiment", 0) < 0)
        if positive > negative:
            health = "strengthening"
            new_status = ThesisStatus.STRENGTHENED
        elif negative > positive:
            health = "weakening"
            new_status = ThesisStatus.WEAKENED
        else:
            health = "stable"
            new_status = ThesisStatus.ACTIVE
        return {
            "thesis_id": thesis_id,
            "health": health,
            "status": new_status,
            "confidence": thesis.confidence,
            "recent_events": len(recent_events),
        }

    def close_thesis(self, thesis_id: str, reason: str = "") -> Thesis | None:
        return self.update_thesis(thesis_id, status=ThesisStatus.CLOSED, metadata={"close_reason": reason})
