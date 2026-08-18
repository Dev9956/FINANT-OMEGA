# Narrative vs Numbers

## Overview
Compares qualitative narrative statements against quantitative financial data to measure alignment. Extracts sentiment components from text and directional signals from metrics, then scores how well they agree.

## Architecture
- **NarrativeAnalyzer** — two-stage pipeline: narrative component extraction + quantitative signal extraction
- Keyword dictionaries for bullish/bearish/neutral sentiment
- Metric change classification: >5% threshold for significant, >10% for moderate, >20% for major
- Alignment scoring: ratio of aligned signals to total signals

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/narrative/analyze` | Analyze narrative vs numbers alignment |

## Data Models
- **AlignmentLevel**: `high_alignment` (≥0.75), `moderate_alignment` (≥0.5), `low_alignment`, `insufficient_data`
- **NarrativeComponent**: text, component_type (growth/risk/neutral), sentiment score, keywords
- **QuantitativeSignal**: metric, current/previous values, change_pct, direction (up/down/flat), significance
- **NarrativeAnalysis**: alignment_level, alignment_score, supporting/conflicting signals, confidence

## Design Decisions
- Sentiment scoring: min(bullish_hits / 3.0, 1.0) — saturates at 3 keywords
- Direction classification uses ±5% threshold to filter noise
- Alignment score = aligned_signals / total_signals
- Confidence scales with alignment: high (0.85), moderate (0.65), low (0.45)

## Known Limitations
- No deep NLP — limited to keyword matching
- No context awareness (e.g., sarcasm, conditional statements)
- Metric direction thresholds are fixed
- No handling of time-lagged effects

## Test Coverage
- 8 tests in `tests/unit/test_narrative.py`
- Covers: high/low alignment, bearish alignment, insufficient data, component extraction, signal extraction, metric mappings
