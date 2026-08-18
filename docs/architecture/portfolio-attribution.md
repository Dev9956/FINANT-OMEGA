# Enhanced Portfolio Attribution — Architecture

## Overview

The Portfolio Attribution system decomposes portfolio returns by asset, sector, and factor contributions. Provides granular insight into which holdings, sectors, and risk factors drove portfolio performance.

## Architecture

```
┌──────────────────────────────────────────────────┐
│              AttributionAnalyzer                   │
│  asset_attribution · sector_attribution           │
│  factor_attribution · full_attribution            │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  AttributionResult                                │
│  holdings[] · factor_exposures{}                  │
└──────────────────────────────────────────────────┘
```

## Key Components

### AttributionAnalyzer (`core/analytics/attribution/analyzer.py`)

#### Asset Attribution

```python
contribution[symbol] = weight × return_pct
```

Decomposes total return into per-asset contributions. Each holding provides `symbol`, `weight`, and `return_pct`.

#### Sector Attribution

```python
sector_contribution[sector] = sum(weight × return_pct for holdings in sector)
```

Groups holdings by sector and sums weighted returns within each sector.

#### Factor Attribution

```python
factor_contribution[factor] = sum(weight × exposure for each holding)
```

Multiplies portfolio weights by factor exposures to compute factor-driven returns. Factor exposures map `factor_name → {symbol → exposure}`.

#### Full Attribution

```python
total_return = sum(asset_contributions)
explained = sum(sector_contributions)
residual = total_return - explained
```

Runs all three attribution methods and computes residual (unexplained return).

## Data Models

```
AttributionResult
  ├── total_return: float
  ├── asset_contribution: dict[str, float]     # symbol → contribution
  ├── sector_contribution: dict[str, float]    # sector → contribution
  ├── factor_contribution: dict[str, float]    # factor → contribution
  └── residual: float
```

### Input Format

```python
holdings = [
    {"symbol": "AAPL", "weight": 0.3, "return_pct": 0.12, "sector": "Technology"},
    {"symbol": "JPM", "weight": 0.2, "return_pct": 0.08, "sector": "Finance"},
    ...
]

factor_exposures = {
    "value": {"AAPL": 0.1, "JPM": 0.8, ...},
    "momentum": {"AAPL": 0.9, "JPM": 0.3, ...},
    "size": {"AAPL": 0.7, "JPM": 0.5, ...},
}
```

## Data Flow

```
Portfolio Holdings + Factor Exposures
  │
  ▼
AttributionAnalyzer.full_attribution(holdings, factor_exposures)
  │
  ├─ asset_attribution(holdings)
  │   → {symbol: weight × return}
  │
  ├─ sector_attribution(holdings)
  │   → {sector: sum(weight × return)}
  │
  ├─ factor_attribution(holdings, factor_exposures)
  │   → {factor: sum(weight × exposure)}
  │
  └─ residual = total - explained
  │
  ▼
AttributionResult
```

## Design Decisions

1. **Weight × return decomposition** — Standard Brinson-style asset attribution
2. **Sector grouping** — Automatic aggregation by sector field
3. **Factor exposure model** — Pluggable factor definitions (value, momentum, size, etc.)
4. **Residual tracking** — Quantifies unexplained return for model validation
5. **Simple interface** — Dict-based inputs for easy integration with any data source

## Known Limitations

- No Brinson-Fachler interaction/selection/allocation decomposition
- Factor attribution uses simple weight × exposure, not regression-based
- No multi-period attribution
- No risk attribution (tracking error, information ratio contribution)
- No benchmark-relative attribution
- In-memory only — no persistence
