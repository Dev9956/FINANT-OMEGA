# Investment Thesis Engine

## Overview
Manages the full lifecycle of investment theses: creation, versioning, evaluation, and evolution tracking. Supports invalidation conditions, confidence scoring, and evidence-based health assessment.

## Architecture
- **ThesisEngine** — core class managing thesis state via in-memory dicts (`_theses`, `_versions`, `_updates`, `_invalidation_conditions`)
- **ThesisVersion** — immutable snapshot of a thesis at a point in time
- **ThesisUpdate** — record of what changed between versions
- **ThesisEvaluation** — result of evaluating thesis health against evidence and metrics
- **ThesisEvolution** — full timeline with confidence trend and status history

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/thesis` | Create a new thesis |
| GET | `/api/v1/intelligence/thesis/{thesis_id}` | Get current thesis version |
| GET | `/api/v1/intelligence/thesis/{thesis_id}/history` | Get full evolution history |
| PUT | `/api/v1/intelligence/thesis/{thesis_id}` | Update thesis (creates new version) |
| POST | `/api/v1/intelligence/thesis/{thesis_id}/evaluate` | Evaluate thesis health with evidence |
| POST | `/api/v1/intelligence/thesis/{thesis_id}/invalidation` | Add invalidation condition |
| GET | `/api/v1/intelligence/thesis` | List all theses (optional symbol filter) |

## Data Models
- **ThesisStatus**: `active`, `strengthened`, `weakened`, `invalidated`, `closed`
- **ThesisConfidence**: `high` (≥0.8), `moderate` (≥0.6), `low` (≥0.4), `very_low`
- **InvalidationCondition**: metric + threshold + comparator + consecutive periods
- **ThesisVersion**: version_number, bull/base/bear case, key drivers/risks/assumptions, confidence

## Design Decisions
- Versioned snapshots instead of mutable state — every change is traceable
- Invalidation conditions use consecutive-period requirement to avoid noise
- Confidence auto-adjusts based on supporting vs contradicting evidence ratio
- In-memory storage for simplicity; database persistence via future integration

## Known Limitations
- No persistent storage — data lost on restart
- No LLM integration for automatic evidence classification
- Keyword-based evidence analysis (no semantic understanding)
- Single-user in-memory model (no concurrency)

## Test Coverage
- 13 tests in `tests/unit/test_thesis_engine.py`
- Covers: create, get, update, history, invalidation, evaluation, listing, confidence levels, condition checking
