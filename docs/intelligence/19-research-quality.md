# Research Quality Score

## Overview
Scores research quality across 8 weighted dimensions: evidence coverage, source quality, numerical accuracy, freshness, contradiction handling, completeness, uncertainty disclosure, and reproducibility.

## Architecture
- **QualityEngine** — computes weighted quality score from 8 dimensions
- Weights: evidence_coverage (0.20), numerical_accuracy (0.20), source_quality (0.15), contradiction_handling (0.15), freshness (0.10), completeness (0.10), uncertainty (0.05), reproducibility (0.05)
- Grading: A (≥0.85), B (≥0.70), C (≥0.50), D (<0.50)
- Improvement recommendations generated from low-scoring dimensions

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/quality/evaluate` | Evaluate research quality |

## Data Models
- **QualityDimension**: 8 dimensions (evidence_coverage, source_quality, numerical_accuracy, freshness, contradiction_handling, completeness, uncertainty, reproducibility)
- **QualityResult**: overall_score, dimension_scores dict, grade, recommendations

## Design Decisions
- Weighted scoring emphasizes evidence and accuracy
- Binary scoring for uncertainty (0.3 if not disclosed, 1.0 if disclosed)
- Binary scoring for reproducibility (same logic)
- Recommendations target specific low-scoring dimensions

## Known Limitations
- Weights are fixed — not customizable per research type
- No temporal quality tracking
- No benchmarking against quality standards
- No integration with research output pipeline

## Test Coverage
- Tested via `tests/unit/test_quality.py`
- Covers: evaluation with various inputs, grading, recommendations
