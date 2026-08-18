# Contradiction Hunter

## Overview
Detects contradictions between qualitative statements (management commentary, narratives) and quantitative data (financials, guidance vs actuals, earnings vs cashflow). Scores contradiction severity for prioritized investigation.

## Architecture
- **ContradictionDetector** — runs four detection methods with configurable thresholds
- Management vs Financials — compares positive statements against declining metrics
- Guidance vs Actual — detects deviations >10% from guided values
- Narrative vs Numbers — compares narrative sentiment against metric direction
- Earnings vs Cashflow — flags quality issues (positive earnings + negative cashflow)

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/contradictions/management-vs-financials` | Detect management vs financials contradictions |
| POST | `/api/v1/intelligence/contradictions/guidance-vs-actual` | Detect guidance misses |
| POST | `/api/v1/intelligence/contradictions/narrative-vs-numbers` | Detect narrative/data divergence |
| POST | `/api/v1/intelligence/contradictions/earnings-vs-cashflow` | Detect earnings quality issues |

## Data Models
- **ContradictionCategory**: `management_vs_financials`, `guidance_vs_actual`, `narrative_vs_market`, `thesis_vs_evidence`, `valuation_vs_growth`, `earnings_vs_cashflow`, `peer_comparison`, `temporal_divergence`
- **ContradictionSeverity**: `critical`, `high`, `moderate`, `low`, `info`
- **ContradictionItem**: category, severity, statement, conflicting_evidence, confidence, requires_investigation
- **ContradictionResult**: entity-level summary with overall severity

## Design Dectives
- Configurable divergence thresholds per metric (e.g., revenue_growth: 5%, margin_change: 3%)
- Severity escalation: >20% deviation → CRITICAL, >10% → HIGH
- Composite scoring: weighted sum of severities normalized to 0-100
- `requires_investigation` flag for automated alerting

## Known Limitations
- No NLP — uses simple keyword matching for sentiment detection
- No temporal analysis (doesn't track contradiction trends over time)
- No cross-entity contradiction detection
- No automatic evidence gathering

## Test Coverage
- 10 tests in `tests/unit/test_contradiction.py`
- Covers: all four detection methods, scoring, aligned cases, edge cases
