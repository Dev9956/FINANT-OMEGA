# Company Monitoring Engine — Architecture

## Overview

The Company Monitoring Engine tracks registered companies, captures state snapshots, detects material changes via diff analysis, scores materiality, evaluates thesis impact, and generates alerts for notable/significant/critical changes.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                API Layer                          │
│  POST /monitoring/register   GET /monitoring/...  │
├──────────────────────────────────────────────────┤
│              MonitoringEngine                     │
│  register · update_state · get_alerts             │
├──────────────────────────────────────────────────┤
│              CompanyMonitor                       │
│  snapshot · diff · score_materiality              │
│  evaluate_thesis_impact · should_alert            │
├──────────────────────────────────────────────────┤
│              ThesisTracker                        │
│  create · evaluate_health · add_event             │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  CompanyState · StateDiff · MonitoringAlert       │
│  MonitorMetric · MaterialityLevel                 │
└──────────────────────────────────────────────────┘
```

## Key Components

### MonitoringEngine (`core/intelligence/company_monitoring/engine.py`)

- **`register_company(symbol, metrics_to_monitor)`** — Registers a company for monitoring with specific `MonitorMetric` types
- **`unregister_company(symbol)`** — Removes registration, state, and alerts
- **`update_state(symbol, new_data)`** — Creates snapshot, diffs against previous state, generates alerts for material changes
- **`get_alerts(symbol, since)`** — Retrieves alerts, optionally filtered by timestamp
- **`get_state(symbol)`** — Returns current `CompanyState`

### CompanyMonitor (`core/intelligence/company_monitoring/monitor.py`)

- **`snapshot(symbol, data)`** — Creates `CompanyState` from raw data dict
- **`diff(previous, current)`** — Compares all metric keys, computes percentage changes for numerics, detects additions/removals
- **`score_materiality(diff)`** — Returns 0.0–1.0 based on absolute change percentage
- **`score_materiality_level(diff)`** — Classifies as NORMAL/NOTABLE/SIGNIFICANT/CRITICAL
- **`evaluate_thesis_impact(diffs, thesis)`** — Returns "supports", "weakens", or "neutral"
- **`should_alert(diff, materiality)`** — True for NOTABLE, SIGNIFICANT, or CRITICAL

### Materiality Thresholds

| Level | Change % | Score |
|-------|----------|-------|
| NORMAL | <5% | 0.0 |
| NOTABLE | ≥5% | 0.5 |
| SIGNIFICANT | ≥10% | 0.75 |
| CRITICAL | ≥20% | 1.0 |

### Monitored Metrics

`MonitorMetric` enum: PRICE, VALUATION, FINANCIALS, EARNINGS, GUIDANCE, ESTIMATES, NEWS, FILINGS, MANAGEMENT, RISK, THESIS

## Data Models

```
CompanyState
  ├── symbol: str
  ├── timestamp: datetime
  ├── metrics: dict         # metric_name → value
  └── snapshot_version: int

StateDiff
  ├── symbol: str
  ├── metric: str
  ├── old_value / new_value: object
  ├── change_pct: float
  ├── is_material: bool
  └── materiality_score: float

MonitoringAlert
  ├── alert_id: str
  ├── symbol: str
  ├── metric: str
  ├── diff: StateDiff
  ├── materiality: MaterialityLevel
  └── thesis_impact: str
```

## Data Flow

```
External Data Update
  │
  ▼
MonitoringEngine.update_state(symbol, new_data)
  │
  ├─ CompanyMonitor.snapshot(symbol, new_data)
  │   → new_state: CompanyState
  │
  ├─ CompanyMonitor.diff(previous_state, new_state)
  │   → list[StateDiff]
  │
  ├─ For each diff:
  │   ├─ score_materiality_level(diff)
  │   ├─ should_alert(diff, materiality)
  │   └─ if alertable → MonitoringAlert
  │
  ├─ Store new_state
  └─ Return alerts
```

## Design Decisions

1. **Per-metric monitoring** — Companies register specific metrics, not all-or-nothing
2. **Threshold-based materiality** — Simple percentage thresholds, easily configurable
3. **Thesis impact evaluation** — Positive/negative material diffs drive thesis health
4. **Alert on change** — Only NOTABLE+ changes generate alerts, reducing noise
5. **State snapshotting** — Previous state retained for diff comparison

## Known Limitations

- In-memory state only — lost on restart
- No time-series storage of historical states
- Materiality thresholds are static (not adaptive to volatility)
- Thesis impact is simple positive/negative counting, not contextual
- No alert delivery mechanism (webhook, email, etc.)
