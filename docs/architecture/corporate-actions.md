# Corporate Actions — Architecture

## Overview

The Corporate Actions engine manages stock splits, bonus issues, dividends, and other corporate events. It computes cumulative adjustment factors, adjusts historical prices for splits/dividends, and calculates total returns including all corporate action effects.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                API Layer                          │
│  POST /corporate-actions   GET /...              │
├──────────────────────────────────────────────────┤
│           CorporateActionsEngine                  │
│  add_action · get_actions                        │
│  compute_adjustment_factor · adjust_prices        │
│  compute_total_return · is_split · is_dividend    │
├──────────────────────────────────────────────────┤
│              Data Models                          │
│  CorporateActionRecord · AdjustmentFactor         │
│  ActionAdjustedPrice · ActionType                 │
└──────────────────────────────────────────────────┘
```

## Key Components

### CorporateActionsEngine (`core/analytics/corporate_actions/engine.py`)

- **`add_action(record)`** — Stores and sorts actions by ex_date
- **`get_actions(symbol, since_date)`** — Filtered retrieval
- **`compute_adjustment_factor(symbol, date_range)`** — Computes cumulative adjustment factors for splits, bonus issues, and dividends within a date range
- **`adjust_prices(prices, actions)`** — Adjusts historical prices forward for all corporate actions
- **`compute_total_return(prices, actions)`** — Total return including price appreciation and dividends
- **`is_split(actions, target_date)`** / **`is_dividend(actions, target_date)`** — Date-based checks

### Action Types

| Type | Adjustment Formula |
|------|-------------------|
| `split` | factor × ratio |
| `bonus` | factor × (1 + ratio) |
| `dividend` | factor × ref_close / (ref_close - dps) |
| `rights` | (not implemented) |
| `buyback` | (not implemented) |
| `merger` | (not implemented) |
| `acquisition` | (not implemented) |
| `spinoff` | (not implemented) |
| `demerger` | (not implemented) |
| `delisting` | (not implemented) |

### Price Adjustment Algorithm

```
cumulative_factor = 1.0
for each price in sorted(prices):
    while action_idx < len(actions) and actions[idx].ex_date <= price_date:
        if split:     factor *= ratio
        if bonus:     factor *= (1 + ratio)
        if dividend:  factor *= ref_close / (ref_close - dps)
        idx++
    adjusted_close = original_close × cumulative_factor
```

### Total Return Computation

```
price_return = (last_close × cumulative_factor - first_close) / first_close
dividend_return = sum(all_dividends) / first_close
total_return = price_return + dividend_return
```

## Data Models

```
CorporateActionRecord
  ├── action_id: str
  ├── symbol: str
  ├── action_type: ActionType
  ├── ex_date: date
  ├── effective_date: date | None
  ├── ratio: float | None        # for split/bonus
  ├── dividend_per_share: float | None
  ├── description: str
  └── metadata: dict

AdjustmentFactor
  ├── symbol: str
  ├── date: date
  ├── factor: float              # cumulative
  └── reason: str

ActionAdjustedPrice
  ├── symbol: str
  ├── date: date
  ├── adjusted_close: float
  ├── original_close: float
  └── adjustment_factor: float
```

## Data Flow

```
Historical Prices + Corporate Actions
  │
  ▼
CorporateActionsEngine.adjust_prices(prices, actions)
  ├─ sort prices by date
  ├─ sort actions by ex_date
  ├─ for each price:
  │   ├─ apply all actions with ex_date ≤ price_date
  │   └─ adjusted = original × cumulative_factor
  │
  ▼
list[ActionAdjustedPrice]

Total Return:
  │
  ▼
CorporateActionsEngine.compute_total_return(prices, actions)
  ├─ price_return = adjusted_final - first / first
  ├─ dividend_return = total_dividends / first
  └─ total = price_return + dividend_return
```

## Design Decisions

1. **Forward adjustment** — Prices on/after ex_date are scaled up to pre-action equivalents
2. **Cumulative factors** — Multiple actions compose multiplicatively
3. **Dividend adjustment** — Uses previous close as reference price
4. **Sorted processing** — Actions and prices sorted by date for correct ordering
5. **Total return** — Combines price appreciation with dividend income

## Known Limitations

- In-memory only — no persistent storage
- Only split, bonus, and dividend adjustments implemented
- No rights issue, buyback, merger, spinoff handling
- No currency adjustment
- No fractional share handling
- Dividend adjustment uses simplified formula (not exact tax-adjusted)
