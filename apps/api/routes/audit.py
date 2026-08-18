"""FININT OMEGA — Audit trail API routes."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Query

from core.evidence.audit.models import AuditEvent, AuditEventType
from core.evidence.audit.store import AuditTrailStore

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

_store = AuditTrailStore()


def get_store() -> AuditTrailStore:
    """Get the audit trail store instance."""
    return _store


@router.get("/{research_id}")
async def get_audit_trail(research_id: str) -> dict:
    """Get the full audit trail for a research session."""
    store = get_store()
    trail = store.get_trail(research_id)
    if trail is None:
        raise HTTPException(status_code=404, detail=f"Audit trail not found for {research_id}")
    return trail.model_dump()


@router.get("/{research_id}/events")
async def get_events(
    research_id: str,
    event_type: AuditEventType | None = Query(default=None, description="Filter by event type"),
) -> list[dict]:
    """Get events for a research session."""
    store = get_store()
    events = store.get_events(research_id, event_type)
    return [e.model_dump() for e in events]


@router.get("/{research_id}/tool-calls")
async def get_tool_calls(research_id: str) -> list[dict]:
    """Get tool call records for a research session."""
    store = get_store()
    calls = store.get_tool_calls(research_id)
    return [c.model_dump() for c in calls]


@router.get("/{research_id}/export")
async def export_trail(
    research_id: str,
    format: str = Query(default="json", description="Export format: json or text"),
) -> dict:
    """Export the audit trail."""
    store = get_store()
    try:
        content = store.export_trail(research_id, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not content:
        raise HTTPException(status_code=404, detail=f"Audit trail not found for {research_id}")
    return {"research_id": research_id, "format": format, "content": content}
