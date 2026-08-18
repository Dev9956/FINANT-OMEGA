"""FININT OMEGA — Unit tests for audit trail module."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from core.evidence.audit.models import (
    AuditEvent,
    AuditEventType,
    AuditTrail,
    ModelCallRecord,
    ToolCallRecord,
)
from core.evidence.audit.store import AuditTrailStore


class TestAuditEventModels:
    """Tests for audit event Pydantic models."""

    def test_event_type_enum_values(self) -> None:
        assert AuditEventType.research_started.value == "research_started"
        assert AuditEventType.tool_called.value == "tool_called"
        assert AuditEventType.error_occurred.value == "error_occurred"
        assert len(AuditEventType) == 8

    def test_audit_event_creation(self) -> None:
        event = AuditEvent(
            research_id="r1",
            event_type=AuditEventType.research_started,
            data={"query": "test"},
            user_id="user1",
        )
        assert event.research_id == "r1"
        assert event.event_type == AuditEventType.research_started
        assert event.event_id  # auto-generated UUID
        assert event.timestamp.tzinfo is not None

    def test_audit_trail_creation(self) -> None:
        trail = AuditTrail(research_id="r1")
        assert trail.research_id == "r1"
        assert trail.events == []
        assert trail.created_at.tzinfo is not None

    def test_tool_call_record_creation(self) -> None:
        tc = ToolCallRecord(
            tool_name="search",
            arguments_hash="abc123",
            result_hash="def456",
            duration_ms=150.5,
            success=True,
        )
        assert tc.tool_name == "search"
        assert tc.success is True

    def test_model_call_record_creation(self) -> None:
        mc = ModelCallRecord(
            model_id="gpt-4",
            prompt_hash="aaa",
            response_hash="bbb",
            tokens_used=500,
            duration_ms=200.0,
            cost=0.01,
        )
        assert mc.model_id == "gpt-4"
        assert mc.tokens_used == 500


class TestAuditTrailStore:
    """Tests for AuditTrailStore."""

    def test_record_event(self) -> None:
        store = AuditTrailStore()
        event = AuditEvent(
            research_id="r1",
            event_type=AuditEventType.research_started,
        )
        event_id = store.record_event(event)
        assert event_id == event.event_id

    def test_get_trail(self) -> None:
        store = AuditTrailStore()
        event = AuditEvent(
            research_id="r1",
            event_type=AuditEventType.research_started,
        )
        store.record_event(event)
        trail = store.get_trail("r1")
        assert trail is not None
        assert trail.research_id == "r1"
        assert len(trail.events) == 1

    def test_get_trail_missing(self) -> None:
        store = AuditTrailStore()
        assert store.get_trail("nonexistent") is None

    def test_get_events_filtered_by_type(self) -> None:
        store = AuditTrailStore()
        store.record_event(
            AuditEvent(research_id="r1", event_type=AuditEventType.research_started)
        )
        store.record_event(
            AuditEvent(research_id="r1", event_type=AuditEventType.tool_called, data={
                "tool_name": "search",
                "arguments_hash": "a",
                "result_hash": "b",
                "duration_ms": 10.0,
                "success": True,
            })
        )
        store.record_event(
            AuditEvent(research_id="r1", event_type=AuditEventType.research_completed)
        )

        tool_events = store.get_events("r1", AuditEventType.tool_called)
        assert len(tool_events) == 1
        assert tool_events[0].event_type == AuditEventType.tool_called

    def test_tool_call_tracking(self) -> None:
        store = AuditTrailStore()
        store.record_event(
            AuditEvent(
                research_id="r1",
                event_type=AuditEventType.tool_called,
                data={
                    "tool_name": "web_search",
                    "arguments_hash": "arg1",
                    "result_hash": "res1",
                    "duration_ms": 250.0,
                    "success": True,
                },
            )
        )
        calls = store.get_tool_calls("r1")
        assert len(calls) == 1
        assert calls[0].tool_name == "web_search"
        assert calls[0].success is True

    def test_model_call_tracking(self) -> None:
        store = AuditTrailStore()
        store.record_event(
            AuditEvent(
                research_id="r1",
                event_type=AuditEventType.model_called,
                data={
                    "model_id": "gpt-4",
                    "prompt_hash": "p1",
                    "response_hash": "r1",
                    "tokens_used": 1000,
                    "duration_ms": 500.0,
                    "cost": 0.03,
                },
            )
        )
        calls = store.get_model_calls("r1")
        assert len(calls) == 1
        assert calls[0].model_id == "gpt-4"
        assert calls[0].tokens_used == 1000

    def test_export_json(self) -> None:
        store = AuditTrailStore()
        store.record_event(
            AuditEvent(research_id="r1", event_type=AuditEventType.research_started)
        )
        exported = store.export_trail("r1", "json")
        assert "r1" in exported
        assert "research_started" in exported

    def test_export_text(self) -> None:
        store = AuditTrailStore()
        store.record_event(
            AuditEvent(research_id="r1", event_type=AuditEventType.research_started)
        )
        exported = store.export_trail("r1", "text")
        assert "Audit Trail: r1" in exported
        assert "research_started" in exported

    def test_export_missing_trail(self) -> None:
        store = AuditTrailStore()
        assert store.export_trail("nonexistent", "json") == ""

    def test_export_unsupported_format(self) -> None:
        store = AuditTrailStore()
        store.record_event(
            AuditEvent(research_id="r1", event_type=AuditEventType.research_started)
        )
        with pytest.raises(ValueError, match="Unsupported export format"):
            store.export_trail("r1", "csv")

    def test_append_only(self) -> None:
        store = AuditTrailStore()
        for i in range(5):
            store.record_event(
                AuditEvent(
                    research_id="r1",
                    event_type=AuditEventType.task_completed,
                    data={"step": i},
                )
            )
        trail = store.get_trail("r1")
        assert trail is not None
        assert len(trail.events) == 5
        for i, ev in enumerate(trail.events):
            assert ev.data["step"] == i

    def test_multiple_research_sessions(self) -> None:
        store = AuditTrailStore()
        store.record_event(
            AuditEvent(research_id="r1", event_type=AuditEventType.research_started)
        )
        store.record_event(
            AuditEvent(research_id="r2", event_type=AuditEventType.research_started)
        )
        assert store.get_trail("r1") is not None
        assert store.get_trail("r2") is not None
        assert len(store.get_events("r1")) == 1
        assert len(store.get_events("r2")) == 1
