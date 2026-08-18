# Cross-Entity Intelligence

## Overview
Analyzes and ranks multiple entities across configurable criteria (earnings momentum, cashflow quality, valuation, growth, risk, thesis health, composite). Supports pattern-based screening across portfolios.

## Architecture
- **CrossEntityEngine** — registers entities, runs multi-criteria ranking
- 7 ranking criteria with scoring logic per criterion
- Composite score: 0.3*earnings + 0.3*fcf + 0.2*valuation + 0.2*risk
- Pattern finders: weakening thesis, strong cashflow + low valuation, high anomaly

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/cross-entity/entities` | Register an entity |
| POST | `/api/v1/intelligence/cross-entity/analyze` | Run cross-entity analysis |
| GET | `/api/v1/intelligence/cross-entity/results/{result_id}` | Get analysis result |
| GET | `/api/v1/intelligence/cross-entity/weakening-thesis` | Find entities with weakening theses |
| GET | `/api/v1/intelligence/cross-entity/strong-cashflow-low-valuation` | Find value + quality |
| GET | `/api/v1/intelligence/cross-entity/high-anomaly` | Find high-anomaly entities |

## Data Models
- **RankingCriterion**: `earnings_momentum`, `cashflow_quality`, `valuation`, `growth`, `thesis_health`, `risk`, `composite`
- **EntityMetrics**: symbol, name, metrics dict, thesis_health, anomaly_score, warning_count
- **RankingResult**: criterion, ranked entities, total count
- **CrossEntityResult**: request, rankings[], summary, entities_analyzed

## Design Decisions
- Multiple criteria allow portfolio-level screening
- Composite criterion provides balanced ranking
- Pattern finders address common investment screening use cases
- Entity registration enables incremental updates

## Known Limitations
- No database persistence
- No sector/industry classification
- No time-series ranking history
- No relative strength or momentum calculations

## Test Coverage
- Tested via `tests/unit/test_cross_entity.py`
- Covers: entity registration, multi-criteria ranking, pattern finders
