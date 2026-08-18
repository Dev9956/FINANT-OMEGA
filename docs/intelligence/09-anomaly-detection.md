# Financial Anomaly Detection

## Overview
Detects unusual financial patterns across four dimensions: cashflow divergence, margin anomalies, working capital buildup, and peer-relative anomalies. Each anomaly is scored and prioritized for investigation.

## Architecture
- **AnomalyDetector** — runs four specialized detection methods
- Cashflow divergence: positive earnings + negative operating cashflow
- Margin anomaly: revenue growth but margin compression
- Working capital: receivables or inventory growing >30%
- Peer relative: P/E ratio >2x peer average

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/anomaly/detect` | Detect anomalies in metrics |
| GET | `/api/v1/intelligence/anomaly/anomalies` | Get all anomalies (optional symbol filter) |

## Data Models
- **AnomalyType**: `ratio_divergence`, `working_capital`, `cashflow_divergence`, `margin_anomaly`, `debt_movement`, `valuation_anomaly`, `trading_anomaly`, `peer_relative`
- **AnomalyScore**: statistical_score, peer_score, historical_score, overall_score (0-1 each)
- **AnomalyItem**: symbol, anomaly_type, score, affected_metrics, description, investigation_priority, peer_context

## Design Decisions
- Multi-dimensional scoring (statistical, peer, historical) for nuanced prioritization
- Fixed thresholds tuned for common financial red flags
- Peer comparison adds relative context
- Investigation priority derived from anomaly severity

## Known Limitations
- No time-series anomaly detection (only point-in-time)
- Limited to 4 anomaly types
- No machine learning models
- Peer comparison requires external peer data

## Test Coverage
- Tested via `tests/unit/test_anomaly.py`
- Covers: cashflow divergence, margin anomalies, working capital, peer relative detection
