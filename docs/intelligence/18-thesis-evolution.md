# Thesis Evolution Map

## Overview
Tracks the complete lifecycle of investment theses through versioned snapshots, confidence trends, and status changes. Provides full audit trail of how and why theses evolved over time.

## Architecture
- Integrated into the Thesis Engine (see 01-thesis-engine.md)
- **ThesisEvolution** — complete timeline with versions, updates, confidence trend, status history
- **ThesisUpdate** — records what changed, why, and confidence delta between versions
- Version counter ensures monotonic version numbers

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/intelligence/thesis/{thesis_id}/history` | Get full evolution history |

## Data Models
- **ThesisEvolution**: thesis_id, versions[], updates[], total_versions, confidence_trend[], status_history[]
- **ThesisUpdate**: from_version, to_version, changes[], evidence_added/removed, confidence_change, reason, timestamp

## Design Decisions
- Immutable version snapshots prevent history corruption
- Confidence trend array enables visualization
- Status history tracks thesis health progression
- Change summaries provide human-readable audit trail

## Known Limitations
- No visual timeline rendering
- No branching or merge of thesis versions
- No automatic evolution triggers (manual updates only)
- No comparison between different thesis evolutions

## Test Coverage
- Tested via thesis engine tests in `tests/unit/test_thesis_engine.py`
- Covers: version creation, history retrieval, confidence trend tracking
