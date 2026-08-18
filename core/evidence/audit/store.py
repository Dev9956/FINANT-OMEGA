"""FININT OMEGA — In-memory append-only audit trail store."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone

from core.evidence.audit.models import (
    AuditEvent,
    AuditEventType,
    AuditTrail,
    ModelCallRecord,
    ToolCallRecord,
)


class AuditTrailStore:
    """Append-only in-memory store for audit trails."""

    def __init__(self) -> None:
        self._trails: dict[str, AuditTrail] = {}
        self._events: dict[str, list[AuditEvent]] = defaultdict(list)
        self._tool_calls: dict[str, list[ToolCallRecord]] = defaultdict(list)
        self._model_calls: dict[str, list[ModelCallRecord]] = defaultdict(list)

    def record_event(self, event: AuditEvent) -> str:
        """Record an audit event. Returns the event_id."""
        if event.research_id not in self._trails:
            self._trails[event.research_id] = AuditTrail(
                research_id=event.research_id,
                created_at=event.timestamp,
            )
        self._trails[event.research_id].events.append(event)
        self._events[event.research_id].append(event)

        if event.event_type == AuditEventType.tool_called:
            tc = ToolCallRecord(**event.data)
            self._tool_calls[event.research_id].append(tc)
        elif event.event_type == AuditEventType.model_called:
            mc = ModelCallRecord(**event.data)
            self._model_calls[event.research_id].append(mc)

        return event.event_id

    def get_trail(self, research_id: str) -> AuditTrail | None:
        """Get the full audit trail for a research session."""
        return self._trails.get(research_id)

    def get_events(
        self, research_id: str, event_type: AuditEventType | None = None
    ) -> list[AuditEvent]:
        """Get events for a research session, optionally filtered by type."""
        events = self._events.get(research_id, [])
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        return list(events)

    def get_tool_calls(self, research_id: str) -> list[ToolCallRecord]:
        """Get all tool call records for a research session."""
        return list(self._tool_calls.get(research_id, []))

    def get_model_calls(self, research_id: str) -> list[ModelCallRecord]:
        """Get all model call records for a research session."""
        return list(self._model_calls.get(research_id, []))

    def export_trail(self, research_id: str, fmt: str = "json") -> str:
        """Export the audit trail as JSON or plain text."""
        trail = self._trails.get(research_id)
        if trail is None:
            return ""

        if fmt == "json":
            return trail.model_dump_json(indent=2)

        if fmt == "text":
            lines: list[str] = [
                f"Audit Trail: {trail.research_id}",
                f"Created: {trail.created_at.isoformat()}",
                f"Events: {len(trail.events)}",
                "-" * 60,
            ]
            for ev in trail.events:
                lines.append(
                    f"[{ev.timestamp.isoformat()}] {ev.event_type.value}: "
                    f"{json.dumps(ev.data, default=str)}"
                )
            return "\n".join(lines)

        raise ValueError(f"Unsupported export format: {fmt}")
