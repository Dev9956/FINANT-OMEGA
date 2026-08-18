# Generative Research Grid — Architecture

## Overview

The Generative Research Grid transforms natural language requests into structured comparison grids. Users describe what they want to compare (e.g., "Compare AAPL, MSFT, GOOGL on revenue growth, ROE, P/E ratio"), and the system plans the grid specification, resolves metrics, and generates evidence-grounded cells.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                API Layer                          │
│  POST /grid/generate   GET /grid/{grid_id}       │
├──────────────────────────────────────────────────┤
│              GridPlanner                          │
│  plan_grid → resolve_entities → resolve_metrics   │
├──────────────────────────────────────────────────┤
│              MetricResolver                       │
│  resolve_metric · resolve_entity                  │
│  resolve_calculation · extract_value              │
├──────────────────────────────────────────────────┤
│              GridGenerator                        │
│  generate → _compute_cell → _compute_confidence   │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  GridSpec · ColumnSpec · RowSpec                  │
│  GridCell · GeneratedGrid                         │
└──────────────────────────────────────────────────┘
```

## Key Components

### GridPlanner (`core/research/grid/planner.py`)

Parses natural language into `GridSpec`:

- **Entity resolution** — Detects sector keywords (tech, finance, healthcare, energy, consumer) → pre-defined symbol lists; extracts ticker symbols via regex
- **Metric resolution** — Matches NL keywords to metric keys (e.g., "revenue growth" → `revenue_growth`, "return on equity" → `roe`)
- **Default fallback** — If no metrics detected, uses `revenue_growth, roe, pe_ratio`

### MetricResolver (`core/research/grid/resolver.py`)

Maps metric names to `ColumnSpec` with:

| Metric | Source | Unit |
|--------|--------|------|
| revenue_growth | financial_statements | % |
| eps_growth | financial_statories | % |
| roe | financial_ratios | % |
| roce | financial_ratios | % |
| debt_equity | financial_ratios | x |
| pe_ratio | financial_ratios | x |
| ev_ebitda | financial_ratios | x |
| fcf_yield | financial_ratios | % |
| gross_margin | financial_ratios | % |
| operating_margin | financial_ratios | % |
| net_margin | financial_ratios | % |
| earnings_surprise | earnings | $ |
| market_cap | market | USD |
| dividend_yield | financial_ratios | % |
| current_ratio | financial_ratios | x |
| revenue | financial_statements | USD |
| ebitda | financial_statements | USD |
| net_income | financial_statements | USD |
| total_debt | financial_statements | USD |
| free_cash_flow | financial_statements | USD |

Also supports computed metrics: `revenue_growth_yoy`, `eps_growth_yoy`, `debt_equity_ratio`, `fcf_yield`, `ev_ebitda`.

### GridGenerator (`core/research/grid/generator.py`)

- Iterates rows × columns, extracts values via `MetricResolver.extract_value()`
- Computes confidence (0.95 if data source version present, 0.7 otherwise)
- Generates evidence IDs for cells with values when `evidence_required=True`

## Data Models

```
GridSpec
  ├── grid_id: str
  ├── title: str
  ├── rows: list[RowSpec]
  ├── columns: list[ColumnSpec]
  ├── filters: dict
  └── sorting: dict

ColumnSpec
  ├── column_id: str
  ├── name: str
  ├── metric_type: MetricType (NUMERIC/CATEGORICAL/TEXT)
  ├── source: str
  ├── calculation: str
  └── evidence_required: bool

RowSpec
  ├── row_id: str
  ├── entity_type: str ("company")
  ├── entity_id: str (e.g. "AAPL")
  └── entity_name: str

GridCell
  ├── row_id / column_id: str
  ├── value: str | float | int | None
  ├── evidence_id: str | None
  └── confidence: float | None

GeneratedGrid
  ├── grid_id: str
  ├── spec: GridSpec
  ├── cells: list[GridCell]
  ├── generated_at: datetime
  └── evidence_summary: dict
```

## Data Flow

```
Natural Language Request
  "Compare tech stocks on revenue growth and P/E ratio"
  │
  ▼
GridPlanner.plan_grid()
  ├─ resolve_entities("tech") → [AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA]
  └─ resolve_metrics("revenue growth, P/E ratio") → [revenue_growth, pe_ratio]
  │
  ▼
GridSpec { rows: 7, columns: 2 }
  │
  ▼
GridGenerator.generate(spec, data_source)
  ├─ for each (row, column):
  │   ├─ MetricResolver.extract_value(row_data, calculation)
  │   ├─ _compute_confidence(value, row_data)
  │   └─ GridCell(row_id, column_id, value, confidence)
  │
  ▼
GeneratedGrid { cells: 14 }
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/grid/generate` | Generate grid from NL request |
| GET | `/api/v1/grid/{grid_id}` | Get generated grid |

## Design Decisions

1. **NL-first interface** — Users describe grids in natural language, not code
2. **Sector presets** — Pre-defined symbol lists for common sector comparisons
3. **Evidence-grounded cells** — Each cell can link to its evidence source
4. **Confidence scoring** — Cells include confidence based on data source availability
5. **Pluggable data sources** — GridGenerator accepts arbitrary data dicts

## Known Limitations

- Sector symbol lists are hardcoded
- No sorting/filtering in generated grids (spec supports it, generator doesn't)
- No chart generation from grid data
- Metric resolver has fixed metric catalog
- No cross-grid comparison or aggregation
