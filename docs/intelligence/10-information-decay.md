# Information Decay Engine

## Overview
Manages dynamic evidence weighting based on information half-lives. Applies exponential decay to evidence freshness, with confirmation boosts and source quality adjustments.

## Architecture
- **DecayEngine** — stores evidence items and computes freshness scores
- Half-lives by source type: Market Data (1d), News (14d), Macro (30d), Earnings (90d), Regulatory (180d)
- Exponential decay formula: `e^(-0.693 * days / half_life)`
- Confirmation boost: +0.2 when evidence is confirmed
- Weighted evidence = freshness × confidence

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/decay/evidence` | Add evidence item |
| POST | `/api/v1/intelligence/decay/score` | Score evidence freshness |
| POST | `/api/v1/intelligence/decay/confirm/{evidence_id}` | Confirm evidence |
| GET | `/api/v1/intelligence/decay/all` | Get all evidence with scores |

## Data Models
- **DecayFactor**: `earnings_filing` (90d), `news_article` (14d), `analyst_report` (60d), `macro_data` (30d), `regulatory_filing` (180d), `market_data` (1d), `management_statement` (30d), `industry_report` (90d)
- **FreshnessScore**: base_freshness, decay_adjusted, confirmation_boost, final_score
- **EvidenceItem**: content, source, decay_factor, published_time, confirmed, source_quality, confidence

## Design Decisions
- Exponential decay is standard for information relevance modeling
- Half-life approach is intuitive and tunable per source type
- Confirmation mechanism allows manual signal boosting
- Source quality multiplied into final weight for quality-adjusted scoring

## Known Limitations
- No automatic evidence expiration or cleanup
- No content-based decay factor assignment
- Fixed half-life values — not adaptive
- No multi-source corroboration logic

## Test Coverage
- Tested via `tests/unit/test_decay.py`
- Covers: evidence addition, freshness scoring, confirmation, weighted evidence retrieval
