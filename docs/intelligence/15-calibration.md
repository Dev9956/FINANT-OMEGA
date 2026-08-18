# Prediction Calibration

## Overview
Measures how well-calibrated prediction confidence scores are against actual outcomes. Groups predictions into confidence buckets and computes accuracy, average confidence, and calibration error per bucket.

## Architecture
- Part of the Prediction Engine
- 5 confidence buckets: 0-20%, 20-40%, 40-60%, 60-80%, 80-100%
- Calibration error = |accuracy - mid_bucket_confidence|
- Brier score = mean((confidence - actual)^2) across all resolved predictions

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/intelligence/predictions/calibration/report` | Get calibration report with Brier score |

## Data Models
- **CalibrationResult**: confidence_bucket, total_predictions, correct_predictions, accuracy, avg_confidence, calibration_error

## Design Decisions
- Bucket-based analysis is standard for calibration assessment
- Brier score provides single-number accuracy metric
- Calibration error measures over/under-confidence per bucket
- Mid-bucket reference (e.g., 10% for 0-20% bucket) for comparison

## Known Limitations
- Requires resolved predictions to compute
- No temporal calibration analysis
- No per-entity calibration breakdown
- No confidence adjustment recommendations

## Test Coverage
- Tested via prediction engine tests in `tests/unit/test_predictions.py`
