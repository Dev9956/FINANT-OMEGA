# Research Audit Trail — Architecture

## Overview

The Research Audit Trail provides append-only, immutable logging of all research activities including tool calls, model calls, evidence collection, and errors. Enables full reproducibility and compliance tracking for financial research.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                API Layer                          │
│  GET /audit/{id}   GET /audit/{id}/events        │
│  GET /audit/{id}/tool-calls   GET /audit/{id}/export│
├──────────────────────────────────────────────────┤
│           AuditTrailStore                         │
│  record_event · get_trail · get_events            │
│  get_tool_calls · get_model_calls · export_trail  │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  AuditEvent · AuditTrail                          │
│  ToolCallRecord · ModelCallRecord                 │
│  ExecutionMetadata                                │
└──────────────────────────────────────────────────┘
```

## Key Components

### AuditTrailStore (`core/evidence/audit/store.py`)

- **`record_event(event)`** — Appends event to trail; auto-creates trail if new; indexes tool/model calls separately
- **`get_trail(research_id)`** — Returns full `AuditTrail` with all events
- **`get_events(research_id, event_type)`** — Filtered event retrieval
- **`get_tool_calls(research_id)`** — Returns all `ToolCallRecord` for a session
- **`get_model_calls(research_id)`** — Returns all `ModelCallRecord` for a session
- **`export_trail(research_id, fmt)`** — Export as JSON or plain text

### Event Types

| Event Type | Description |
|------------|-------------|
| `research_started` | Research run initiated |
| `task_completed` | Individual task finished |
| `evidence_collected` | New evidence gathered |
| `evidence_verified` | Evidence validated |
| `tool_called` | Tool invocation (recorded as `ToolCallRecord`) |
| `model_called` | LLM invocation (recorded as `ModelCallRecord`) |
| `error_occurred` | Error during execution |
| `research_completed` | Research run finished |

### ToolCallRecord

```python
class ToolCallRecord(BaseModel):
    tool_name: str
    arguments_hash: str      # SHA-256 of arguments
    result_hash: str         # SHA-256 of result
    duration_ms: float
    success: bool
    error_message: str | None
```

### ModelCallRecord

```python
class ModelCallRecord(BaseModel):
    model_id: str
    prompt_hash: str         # SHA-256 of prompt
    response_hash: str       # SHA-256 of response
    tokens_used: int
    duration_ms: float
    cost: float
```

### ExecutionMetadata

```python
class ExecutionMetadata(BaseModel):
    planner_version: str
    agent_versions: dict[str, str]
    llm_config: dict[str, Any]
    tools_used: list[str]
    data_versions: dict[str, str]
    document_versions: dict[str, str]
```

## Data Flow

```
Research Activity
  │
  ▼
AuditEvent(research_id, event_type, data)
  │
  ▼
AuditTrailStore.record_event(event)
  ├─ append to trail.events
  ├─ index in _events[research_id]
  ├─ if tool_called → index in _tool_calls
  └─ if model_called → index in _model_calls
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/audit/{research_id}` | Full audit trail |
| GET | `/api/v1/audit/{research_id}/events` | Events (filterable by type) |
| GET | `/api/v1/audit/{research_id}/tool-calls` | Tool call records |
| GET | `/api/v1/audit/{research_id}/export?format=json\|text` | Export trail |

## Export Formats

### JSON Export
```json
{
  "research_id": "...",
  "events": [...],
  "created_at": "..."
}
```

### Text Export
```
Audit Trail: {research_id}
Created: {timestamp}
Events: {count}
------------------------------------------------------------
[2026-08-16T10:00:00Z] tool_called: {"tool_name": "market_data", ...}
[2026-08-16T10:00:01Z] evidence_collected: {"evidence_id": "..."}
```

## Design Decisions

1. **Append-only** — Events are never modified or deleted after recording
2. **Hash-based deduplication** — Arguments/results stored as SHA-256 hashes to reduce storage while preserving auditability
3. **Separate indexing** — Tool calls and model calls indexed separately for fast retrieval
4. **Per-research isolation** — Each research run has its own audit trail
5. **Dual export** — JSON for programmatic access, text for human review

## Known Limitations

- In-memory only — trails lost on restart
- No encryption of event data
- No retention policy or cleanup
- Hash collisions theoretically possible (SHA-256 practically collision-free)
- No streaming/real-time audit feed
