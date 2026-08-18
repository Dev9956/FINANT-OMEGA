# Autonomous Research Loop

## Overview
Controlled autonomous research loop that iterates through Observe → Detect → Investigate → Hypothesize → Test → Verify phases with budget limits and stopping conditions. Produces findings, hypotheses, and audit trails.

## Architecture
- **ResearchLoopEngine** — orchestrates multi-iteration research with config-driven limits
- 12 loop phases defined (observe, detect, investigate, hypothesize, test, verify, conclude, predict, monitor, measure, calibrate, update)
- Each iteration runs all phases sequentially with step-level tracking
- Stopping conditions: max iterations, max hypotheses (10), confidence threshold (0.9), timeout

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/research-loop/run` | Run a research loop |
| GET | `/api/v1/intelligence/research-loop/{loop_id}` | Get loop result |

## Data Models
- **LoopPhase**: 12 phases from observe to calibrate
- **LoopStep**: phase, description, input/output data, status, duration_ms
- **ResearchIteration**: steps, findings, hypotheses, confidence
- **LoopConfig**: max_steps (50), max_iterations (5), timeout_seconds (300), max_cost
- **LoopResult**: iterations, final_findings, final_hypotheses, confidence, audit_trail

## Design Decisions
- Budget-limited to prevent runaway research
- Audit trail built from all steps for reproducibility
- Confidence increases with iterations (0.5 + iteration * 0.1)
- Phase-based structure mirrors scientific method

## Known Limitations
- No actual tool execution (steps are simulated)
- No LLM integration for reasoning
- No external data fetching
- Fixed phase sequence — no adaptive ordering

## Test Coverage
- Tested via `tests/unit/test_research_loop.py`
- Covers: loop execution, iteration tracking, stopping conditions, audit trail
