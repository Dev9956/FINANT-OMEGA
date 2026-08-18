# Estimate Revisions — Architecture

## Overview

The Estimate Revisions engine tracks analyst estimates, computes earnings surprises, detects estimate revisions over time, and computes revision momentum. Includes temporal leakage prevention to ensure estimates are only compared against data available at the time.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                API Layer                          │
│  POST /estimates   GET /estimates/{symbol}        │
│  GET /estimates/{symbol}/surprise                 │
│  GET /estimates/{symbol}/momentum                 │
├──────────────────────────────────────────────────┤
│              EstimateEngine                       │
│  add_estimate · get_estimates                     │
│  compute_surprise · compute_revision_momentum     │
│  detect_estimate_revisions · get_consensus        │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  EstimateRecord · EPSRecord · RevenueRecord       │
│  SurpriseResult · RevisionMomentum                │
│  EstimateRevision · SurpriseType/Magnitude        │
└──────────────────────────────────────────────────┘
```

## Key Components

### EstimateEngine (`core/analytics/estimates/engine.py`)

- **`add_estimate(record)`** — Stores estimate record indexed by symbol
- **`get_estimates(symbol, metric, period)`** — Filtered retrieval
- **`compute_surprise(symbol, period_end, as_of)`** — Computes EPS and revenue surprise with temporal leakage prevention
- **`compute_revision_momentum(symbol, lookback_periods)`** — Counts upward/downward revisions over recent periods
- **`detect_estimate_revisions(symbol, metric, since_date)`** — Detects sequential estimate changes
- **`get_consensus(symbol, metric, period)`** — Returns latest consensus value

### Surprise Computation

```
EPS Surprise % = (actual - estimate) / |estimate|
Revenue Surprise % = (actual - consensus) / |consensus|

Surprise Type:
  > +2%  → beat
  < -2%  → miss
  else   → inline

Magnitude:
  > 10%  → significant
  > 5%   → moderate
  else   → slight
```

### Temporal Leakage Prevention

The `as_of` parameter in `compute_surprise()` ensures only estimates available before a given date are used:

```python
if as_of is not None:
    period_records = [r for r in period_records if r.timestamp.date() <= as_of]
```

Similarly, `detect_estimate_revisions()` only considers estimates with `timestamp.date() >= since_date`.

### Revision Momentum

```
For recent N periods:
  upward_revisions = count(estimate > previous_estimate)
  downward_revisions = count(estimate < previous_estimate)
  net = upward - downward
  momentum_score = net / total (if total > 0 else 0.0)
```

## Data Models

```
EstimateRecord
  ├── estimate_id: str
  ├── symbol: str
  ├── metric: str
  ├── period_end: date
  ├── actual_value: float | None
  ├── estimate_value: float | None
  ├── consensus_value: float | None
  ├── estimate_high / estimate_low: float | None
  ├── previous_estimate: float | None
  ├── revision_count: int
  ├── source: str
  └── timestamp: datetime

SurpriseResult
  ├── symbol / period_end
  ├── eps_surprise_pct: float | None
  ├── revenue_surprise_pct: float | None
  ├── surprise_type: SurpriseType (beat/miss/inline)
  └── magnitude: SurpriseMagnitude (slight/moderate/significant)

RevisionMomentum
  ├── symbol: str
  ├── upward_revisions / downward_revisions / net_revisions: int
  └── momentum_score: float (-1.0 to 1.0)
```

## Data Flow

```
Estimate Data Input
  │
  ▼
EstimateEngine.add_estimate(record)
  → indexed by symbol
  │
  ▼
compute_surprise(symbol, period_end, as_of)
  ├─ filter by period
  ├─ apply temporal filter (as_of)
  ├─ compute EPS surprise %
  ├─ compute revenue surprise %
  └─ classify type + magnitude
  │
  ▼
compute_revision_momentum(symbol)
  ├─ sort by period descending
  ├─ take recent N periods
  ├─ count upward/downward
  └─ compute momentum score
```

## Design Decisions

1. **Temporal leakage prevention** — `as_of` parameter ensures no future information usage in backtesting
2. **Per-symbol indexing** — Estimates stored and queried by symbol for fast access
3. **Surprise classification** — Beat/miss/inline with magnitude for alerting thresholds
4. **Momentum scoring** — Net revision direction over recent periods as a signal
5. **Flexible metrics** — Generic `metric` field supports any estimate type (EPS, revenue, FCF, etc.)

## Known Limitations

- In-memory storage only
- No analyst-level tracking (only aggregated estimates)
- No consensus computation from individual analyst estimates
- Surprise thresholds are fixed (±2% beat/miss, ±5%/10% magnitude)
- No earnings call integration
