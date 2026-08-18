# Prediction Tracking

## Overview
Registers, tracks, and resolves investment predictions with outcome measurement. Supports both value predictions and directional forecasts with configurable time horizons.

## Architecture
- **PredictionEngine** — manages prediction lifecycle: register → pending → resolve
- Resolution computes error (actual - predicted) and direction correctness
- Direction logic: up/down/stable with 5% tolerance for stable
- Status transitions: pending → resolved/expired/cancelled

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/predictions` | Register a prediction |
| GET | `/api/v1/intelligence/predictions/{prediction_id}` | Get prediction |
| POST | `/api/v1/intelligence/predictions/{prediction_id}/resolve` | Resolve with actual value |
| GET | `/api/v1/intelligence/predictions` | List predictions (optional entity filter) |
| GET | `/api/v1/intelligence/predictions/calibration/report` | Get calibration analysis |

## Data Models
- **PredictionStatus**: `pending`, `resolved`, `expired`, `cancelled`
- **PredictionRecord**: entity, prediction_text, metric, predicted_value, direction, confidence, horizon_days, assumptions, evidence
- **PredictionOutcome**: actual_value, error, direction_correct
- **CalibrationResult**: confidence_bucket, total/correct predictions, accuracy, calibration_error

## Design Decisions
- Direction correctness uses 5% tolerance for "stable" predictions
- Confidence bucketing (0-20%, 20-40%, etc.) for calibration analysis
- Brier score computed as mean squared error between confidence and outcome
- Assumptions and evidence tracked per prediction for accountability

## Known Limitations
- No automatic expiration based on horizon_days
- No batch resolution
- No probabilistic calibration (only directional)
- No prediction market or ensemble mechanisms

## Test Coverage
- Tested via `tests/unit/test_predictions.py`
- Covers: registration, resolution, direction correctness, calibration, listing
