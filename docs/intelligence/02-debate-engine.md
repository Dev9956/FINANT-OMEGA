# AI Investment Debate Engine

## Overview
Multi-agent adversarial analysis system with Bull, Bear, and Neutral analysts followed by a Synthesis Judge. Forces structured debate on investment questions to surface blind spots and produce balanced conclusions.

## Architecture
- **DebateEngine** — orchestrates the four-phase debate pipeline
- **Bull Analyst** — finds positive evidence, builds bullish thesis
- **Bear Analyst** — finds negative evidence, builds bearish thesis
- **Neutral Verifier** — cross-checks evidence quality and corroboration
- **Synthesis Judge** — weighs both sides, produces consensus/disputes and recommended action

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/debate` | Run a new debate |
| GET | `/api/v1/intelligence/debate/{debate_id}` | Retrieve debate result |

## Data Models
- **AnalystRole**: `bull`, `bear`, `neutral`, `evidence_verifier`, `synthesis_judge`
- **AnalystArgument**: thesis, key_points, evidence, confidence, risks/catalysts identified
- **EvidenceVerification**: per-item verification with source quality and corroboration counts
- **SynthesisResult**: conclusion, evidence quality score, consensus/disputes, final confidence, recommended action
- **DebateConfig**: max_evidence_per_analyst, min_evidence_threshold, confidence_threshold

## Design Decisions
- Keyword-based evidence classification (positive/negative sentiment) for fast execution
- Evidence verification step ensures both sides actually use the same evidence pool
- Weighted synthesis: bull/bear confidence weighted by evidence quality
- Action recommendation based on confidence differential (±0.2 threshold)

## Known Limitations
- No LLM agents — uses keyword matching instead of actual AI reasoning
- No iterative debate rounds (single pass)
- No external knowledge retrieval during debate
- Confidence calculations are heuristic-based

## Test Coverage
- 10 tests in `tests/unit/test_debate.py`
- Covers: basic debate, bull/bear evidence finding, neutral verification, synthesis, config, timing, empty evidence
