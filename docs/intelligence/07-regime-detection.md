# Market Regime Detection

## Overview
Classifies the current market environment into one of 10 regimes (Risk-On, Risk-Off, Inflationary, Deflationary, Stagflation, High Growth, Recession, Liquidity Stress, Recovery, Unknown) using multi-dimensional signal analysis.

## Architecture
- **RegimeDetector** — extracts signals from market data, scores each regime, selects highest
- Signal definitions with thresholds: VIX>20 bearish, GDP<0 recessionary, inflation>5 highly inflationary
- Weighted scoring: each signal contributes to multiple regimes with different weights
- Historical reference periods for each regime

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/regime/detect` | Detect current market regime |

## Data Models
- **MarketRegime**: `risk_on`, `risk_off`, `inflationary`, `deflationary`, `stagflation`, `high_growth`, `recession`, `liquidity_stress`, `recovery`, `unknown`
- **RegimeConfidence**: `high` (≥0.6), `moderate` (≥0.4), `low`
- **RegimeSignal**: indicator, value, threshold, direction, weight, description
- **RegimeResult**: regime, confidence, signals, supporting/conflicting signals, historical_similar, summary

## Design Decisions
- Multi-signal scoring prevents single-indicator dominance
- Bullish signals boost Risk-On, High Growth, and Recovery simultaneously
- Inflation-specific logic for Inflationary/Deflationary/Stagflation regimes
- Historical analogs provide context for regime interpretation

## Known Limitations
- No regime transition probability modeling
- Fixed thresholds — not adaptive to market conditions
- No time-series analysis of regime persistence
- Limited to 8 input indicators

## Test Coverage
- Tested via `tests/unit/test_regime.py`
- Covers: regime detection with various market conditions, signal extraction, scoring
