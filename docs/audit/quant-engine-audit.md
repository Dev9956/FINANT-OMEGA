# Quant Engine Audit

## Overview

- **Language**: Rust 2021 edition
- **Lines of Code**: ~1,665 across 12 source files
- **Dependencies**: `thiserror` (error handling), `approx` (dev, float comparisons)
- **Tests**: 64 (all passing)
- **Unsafe Blocks**: None

---

## Module-by-Module Findings

### 1. Returns (140 lines, 8 tests)

**Implementation**: `simple_returns`, `log_returns`, `cagr`

| Issue | Severity | Detail |
|---|---|---|
| Negative price not rejected in simple_returns | MEDIUM | Only checks p==0.0, not p<0.0 |
| cagr with negative end price | LOW | Produces NaN via powf |

**Verdict**: REAL, functionally correct for normal inputs.

### 2. Statistics (171 lines, 10 tests)

**Implementation**: `mean`, `variance`, `std_dev`, `annualized_volatility`, `sharpe_ratio`, `max_drawdown`

| Issue | Severity | Detail |
|---|---|---|
| Catastrophic cancellation in variance | HIGH | Naive sum-of-squares formula loses precision for large-mean, small-variance data |
| sharpe_ratio unwrap_or(0.0) | MEDIUM | Silently uses 0.0 for failed std_dev |
| max_drawdown division by zero | MEDIUM | When peak is 0.0 |

**Verdict**: REAL, correct for normal inputs. Numerical stability issue for edge cases.

### 3. Indicators (235 lines, 7 tests)

**Implementation**: `sma`, `ema`, `rsi`, `bollinger_bands`, `macd`, `atr`

| Issue | Severity | Detail |
|---|---|---|
| EMA unwrap_or(0.0) | MEDIUM | Misleading but safe in practice |
| RSI: Wilder's smoothing correct | OK | First value uses simple avg, subsequent use Wilder's |

**Verdict**: REAL, functionally correct. Standard implementations.

### 4. Factors (157 lines, 10 tests)

**Implementation**: `momentum_factor`, `volatility_factor`, `value_factor`, `quality_factor`, `size_factor`, `liquidity_factor`, `FactorExposure`

| Issue | Severity | Detail |
|---|---|---|
| quality_factor clamps ROE to [0,1] | LOW | ROE can legitimately exceed 100% |
| value_factor with negative PE | MEDIUM | Returns 0.0 for negative PE (reasonable heuristic) |

**Verdict**: REAL, standard factor implementations.

### 5. Portfolio (187 lines, 8 tests)

**Implementation**: `Portfolio` struct with `expected_return`, `variance`, `std_dev`, `hhi`, `risk_contribution`, `sector_exposure`

| Issue | Severity | Detail |
|---|---|---|
| Naive O(n^2) variance | LOW | Correct but slow for large portfolios |
| Weights sum tolerance 1e-6 | LOW | May reject valid 1/3 weights |

**Verdict**: REAL, standard portfolio analytics.

### 6. Risk (195 lines, 9 tests)

**Implementation**: `var`, `cvar`, `sortino_ratio`, `calmar_ratio`, `beta`, `information_ratio`

| Issue | Severity | Detail |
|---|---|---|
| VaR panic on NaN input | HIGH | `partial_cmp().unwrap()` panics if returns contain NaN |
| CVaR when cutoff==0 | OK | Returns None correctly |
| Sortino uses population variance | LOW | Standard practice for downside deviation |

**Verdict**: REAL, but NaN-unsafe. Must add input validation.

### 7. Scenarios (146 lines, 5 tests)

**Implementation**: `apply_scenario`, `monte_carlo`, `historical_stress`

| Issue | Severity | Detail |
|---|---|---|
| Box-Muller NaN/Inf bug | HIGH | u1=0.0 produces ln(0)=-inf -> NaN |
| LCG-to-float precision loss | MEDIUM | u64->f64 loses 11 bits of precision |
| apply_scenario ignores factor mapping | MEDIUM | Sums all shocks regardless of factor |

**Verdict**: REAL but has critical numerical bug.

### 8. Attribution (122 lines, 3 tests)

**Implementation**: `asset_attribution`, `sector_attribution`, `brinson_attribution`

| Issue | Severity | Detail |
|---|---|---|
| Dead code _total | LOW | Computed but unused |
| Weak test coverage | MEDIUM | Only 3 tests |

**Verdict**: REAL, correct Brinson implementation.

### 9. Backtest (259 lines, 5 tests)

**Implementation**: `backtest` function with `BacktestConfig`, `Trade`, `BacktestResult`

| Issue | Severity | Detail |
|---|---|---|
| Hardcoded risk-free rate 5% | MEDIUM | Should be configurable |
| profit_factor returns Infinity | MEDIUM | When no losses |
| Position sizing hardcoded 95% | LOW | Should be configurable |

**Verdict**: REAL, functional backtesting engine.

### 10. Simulation (15 lines, 1 test)

**Implementation**: Re-exports `monte_carlo` from scenarios

**Verdict**: STUB/RE-EXPORT.

### 11. Bindings (5 lines, 0 tests)

**Implementation**: Version constant only

**Verdict**: STUB. No PyO3 code. Cargo.toml doesn't even list pyo3 dependency.

---

## Numerical Correctness Summary

| Function | Correctness | Edge Cases | Confidence |
|---|---|---|---|
| simple_returns | Correct | Negative prices not rejected | HIGH |
| log_returns | Correct | Negative prices rejected | HIGH |
| mean | Correct | Empty input handled | HIGH |
| variance | Correct (precision issue) | Large-mean small-var | MEDIUM |
| std_dev | Correct | <2 elements handled | HIGH |
| sharpe_ratio | Correct | Zero std handled | HIGH |
| max_drawdown | Correct | Zero peak not handled | MEDIUM |
| sma | Correct | Empty/period=0 handled | HIGH |
| ema | Correct | Warmup period correct | HIGH |
| rsi | Correct | Wilder's smoothing correct | HIGH |
| var | Correct | NaN panics | LOW |
| cvar | Correct | Empty/cutoff=0 handled | HIGH |
| monte_carlo | Bug (NaN) | u1=0 not guarded | LOW |
| brinson_attribution | Correct | Dimension check present | HIGH |
| backtest | Correct | Hardcoded params | MEDIUM |

---

## Performance Concerns

1. **No parallelism**: All code is single-threaded. No `rayon`.
2. **No `ndarray`**: Manual loops for matrix operations.
3. **Portfolio variance O(n^2)**: Could use Cholesky decomposition.
4. **Monte Carlo allocates Vec<Vec<f64>>**: Could use flat buffer.

---

## Recommendations

### Immediate Fixes (P0)
1. Add NaN validation to VaR/CVaR before partial_cmp
2. Fix Box-Muller NaN bug (guard u1=0)
3. Implement Welford's algorithm for variance

### Short-term (P1)
4. Add `pyo3` dependency and implement real bindings
5. Make risk-free rate configurable in backtest
6. Cap profit_factor at large value instead of Infinity
7. Add NaN input validation across all modules

### Medium-term (P2)
8. Add `rayon` for parallel computation
9. Add `ndarray` for matrix operations
10. Improve test coverage for attribution module
11. Add benchmark tests with known-answer financial calculations
