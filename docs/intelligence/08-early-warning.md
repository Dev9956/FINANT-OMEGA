# Early Warning System

## Overview
Scans financial metrics for deterioration patterns and generates prioritized warnings with recommended investigation steps. Monitors revenue, margins, cashflow, leverage, working capital, and valuation metrics.

## Architecture
- **EarlyWarningEngine** — threshold-based scanner with per-metric configurations
- 11 monitored metrics with severity levels (Critical/High/Medium/Low)
- Category mapping: metric → warning category (revenue_deterioration, margin_compression, etc.)
- Investigation recommendations per category

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/early-warning/scan` | Scan metrics for warnings |
| GET | `/api/v1/intelligence/early-warning/warnings` | Get all warnings (optional symbol filter) |

## Data Models
- **WarningCategory**: `revenue_deterioration`, `margin_compression`, `cashflow_divergence`, `leverage_increase`, `inventory_buildup`, `receivables_growth`, `guidance_cut`, `earnings_revision`, `valuation_extreme`, `unusual_volume`, `sentiment_shift`, `governance_signal`
- **WarningSeverity**: `critical`, `high`, `medium`, `low`
- **EarlyWarning**: symbol, category, severity, indicator, current_value, threshold, deviation_pct, recommended_investigation

## Design Decisions
- Threshold-based for fast, deterministic detection
- Severity pre-assigned per metric (e.g., operating_cashflow decline → CRITICAL)
- Investigation recommendations provide actionable next steps
- Deviation percentage calculated automatically for alerting

## Known Limitations
- No trend analysis — only period-over-period comparison
- No anomaly-based thresholds (fixed absolute/relative thresholds)
- No alert suppression or deduplication
- No integration with external data feeds

## Test Coverage
- Tested via `tests/unit/test_early_warning.py`
- Covers: scan with various metric changes, warning generation, severity classification
