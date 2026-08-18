//! FININT OMEGA — Backtesting engine.

/// Backtest configuration.
#[derive(Debug, Clone)]
pub struct BacktestConfig {
    pub initial_capital: f64,
    pub transaction_cost_bps: f64,
    pub slippage_bps: f64,
    pub commission_per_share: f64,
}

impl Default for BacktestConfig {
    fn default() -> Self {
        Self {
            initial_capital: 100_000.0,
            transaction_cost_bps: 10.0,
            slippage_bps: 5.0,
            commission_per_share: 0.005,
        }
    }
}

/// Trade record.
#[derive(Debug, Clone, PartialEq)]
pub struct Trade {
    pub date_index: usize,
    pub symbol: String,
    pub side: TradeSide,
    pub shares: f64,
    pub price: f64,
    pub cost: f64,
}

#[derive(Debug, Clone, PartialEq)]
pub enum TradeSide {
    Buy,
    Sell,
}

/// Backtest result.
#[derive(Debug, Clone, PartialEq)]
pub struct BacktestResult {
    pub total_return: f64,
    pub annualized_return: f64,
    pub volatility: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub win_rate: f64,
    pub profit_factor: f64,
    pub total_trades: usize,
    pub total_costs: f64,
    pub equity_curve: Vec<f64>,
    pub trades: Vec<Trade>,
}

/// Simple backtester for a single-asset strategy.
pub fn backtest(
    prices: &[f64],
    signals: &[i8], // 1 = buy, -1 = sell, 0 = hold
    config: &BacktestConfig,
) -> Result<BacktestResult, BacktestError> {
    if prices.len() != signals.len() {
        return Err(BacktestError::DimensionMismatch);
    }
    if prices.is_empty() {
        return Err(BacktestError::EmptyData);
    }

    let mut capital = config.initial_capital;
    let mut position = 0.0_f64;
    let mut equity_curve = Vec::with_capacity(prices.len());
    let mut trades = Vec::new();
    let mut total_costs = 0.0_f64;
    let mut wins = 0;
    let mut losses = 0;
    let mut gross_profit = 0.0_f64;
    let mut gross_loss = 0.0_f64;

    for (i, (&price, &signal)) in prices.iter().zip(signals.iter()).enumerate() {
        let effective_price = if signal == 1 {
            price * (1.0 + config.slippage_bps / 10_000.0)
        } else if signal == -1 {
            price * (1.0 - config.slippage_bps / 10_000.0)
        } else {
            price
        };

        if signal == 1 && position == 0.0 {
            // Buy
            let shares = (capital * 0.95) / effective_price; // 95% of capital
            let cost = shares * effective_price * config.transaction_cost_bps / 10_000.0
                + shares * config.commission_per_share;
            capital -= shares * effective_price + cost;
            position = shares;
            total_costs += cost;
            trades.push(Trade {
                date_index: i,
                symbol: "ASSET".to_string(),
                side: TradeSide::Buy,
                shares,
                price: effective_price,
                cost,
            });
        } else if signal == -1 && position > 0.0 {
            // Sell
            let proceeds = position * effective_price;
            let cost = proceeds * config.transaction_cost_bps / 10_000.0
                + position * config.commission_per_share;
            capital += proceeds - cost;
            total_costs += cost;
            let pnl = position * (effective_price - trades.last().map(|t| t.price).unwrap_or(price));
            if pnl > 0.0 {
                wins += 1;
                gross_profit += pnl;
            } else {
                losses += 1;
                gross_loss += pnl.abs();
            }
            trades.push(Trade {
                date_index: i,
                symbol: "ASSET".to_string(),
                side: TradeSide::Sell,
                shares: position,
                price: effective_price,
                cost,
            });
            position = 0.0;
        }

        let equity = capital + position * price;
        equity_curve.push(equity);
    }

    // Final metrics
    let total_return = (equity_curve.last().unwrap_or(&config.initial_capital) - config.initial_capital) / config.initial_capital;
    let n_years = prices.len() as f64 / 252.0;
    let annualized_return = if n_years > 0.0 {
        (1.0 + total_return).powf(1.0 / n_years) - 1.0
    } else {
        0.0
    };

    // Volatility
    let returns: Vec<f64> = equity_curve
        .windows(2)
        .map(|w| (w[1] - w[0]) / w[0])
        .collect();
    let vol = if returns.len() > 1 {
        let mean = returns.iter().sum::<f64>() / returns.len() as f64;
        let var = returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / (returns.len() - 1) as f64;
        var.sqrt() * 252.0_f64.sqrt()
    } else {
        0.0
    };

    // Sharpe
    let daily_rf = 0.05 / 252.0;
    let sharpe = if vol > 0.0 {
        let mean_ret = returns.iter().sum::<f64>() / returns.len() as f64;
        (mean_ret - daily_rf) / (vol / 252.0_f64.sqrt()) * 252.0_f64.sqrt()
    } else {
        0.0
    };

    // Max drawdown
    let mut peak = equity_curve[0];
    let mut max_dd = 0.0_f64;
    for &eq in &equity_curve {
        if eq > peak {
            peak = eq;
        }
        let dd = (peak - eq) / peak;
        if dd > max_dd {
            max_dd = dd;
        }
    }

    let win_rate = if wins + losses > 0 {
        wins as f64 / (wins + losses) as f64
    } else {
        0.0
    };

    let profit_factor = if gross_loss > 0.0 {
        gross_profit / gross_loss
    } else {
        f64::INFINITY
    };

    Ok(BacktestResult {
        total_return,
        annualized_return,
        volatility: vol,
        sharpe_ratio: sharpe,
        max_drawdown: max_dd,
        win_rate,
        profit_factor,
        total_trades: trades.len(),
        total_costs,
        equity_curve,
        trades,
    })
}

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum BacktestError {
    #[error("Dimension mismatch between prices and signals")]
    DimensionMismatch,
    #[error("Data is empty")]
    EmptyData,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_backtest() {
        let prices = vec![100.0, 105.0, 110.0, 108.0, 115.0, 120.0];
        let signals = vec![1, 0, 0, 0, 0, -1]; // Buy at start, sell at end
        let config = BacktestConfig::default();
        let result = backtest(&prices, &signals, &config).unwrap();
        assert!(result.total_return > 0.0);
        assert_eq!(result.total_trades, 2);
        assert!(result.max_drawdown >= 0.0);
    }

    #[test]
    fn test_backtest_dimension_error() {
        let result = backtest(&[100.0], &[1, 0], &BacktestConfig::default());
        assert_eq!(result, Err(BacktestError::DimensionMismatch));
    }

    #[test]
    fn test_backtest_empty() {
        let result = backtest(&[], &[], &BacktestConfig::default());
        assert_eq!(result, Err(BacktestError::EmptyData));
    }

    #[test]
    fn test_backtest_no_trades() {
        let prices = vec![100.0, 105.0, 110.0];
        let signals = vec![0, 0, 0];
        let result = backtest(&prices, &signals, &BacktestConfig::default()).unwrap();
        assert_eq!(result.total_trades, 0);
    }

    #[test]
    fn test_backtest_costs() {
        let prices = vec![100.0, 105.0, 110.0, 108.0, 115.0, 120.0];
        let signals = vec![1, 0, 0, 0, 0, -1];
        let config = BacktestConfig {
            transaction_cost_bps: 50.0,
            ..Default::default()
        };
        let result = backtest(&prices, &signals, &config).unwrap();
        assert!(result.total_costs > 0.0);
    }
}
