//! FININT OMEGA — Risk analytics.

use super::statistics;

/// Value at Risk (historical method).
/// Returns the loss at the given confidence level.
pub fn var(returns: &[f64], confidence: f64) -> Option<f64> {
    if returns.is_empty() || confidence <= 0.0 || confidence >= 1.0 {
        return None;
    }
    let mut sorted: Vec<f64> = returns.iter().copied().filter(|r| r.is_finite()).collect();
    if sorted.is_empty() {
        return None;
    }
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let index = ((1.0 - confidence) * sorted.len() as f64) as usize;
    let idx = index.min(sorted.len() - 1);
    Some(-sorted[idx])
}

/// Conditional Value at Risk (Expected Shortfall).
pub fn cvar(returns: &[f64], confidence: f64) -> Option<f64> {
    if returns.is_empty() || confidence <= 0.0 || confidence >= 1.0 {
        return None;
    }
    let mut sorted: Vec<f64> = returns.iter().copied().filter(|r| r.is_finite()).collect();
    if sorted.is_empty() {
        return None;
    }
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let cutoff = ((1.0 - confidence) * sorted.len() as f64) as usize;
    let cutoff = cutoff.min(sorted.len());
    if cutoff == 0 {
        return None;
    }
    let tail_sum: f64 = sorted[..cutoff].iter().sum();
    Some(-tail_sum / cutoff as f64)
}

/// Sortino ratio.
pub fn sortino_ratio(
    returns: &[f64],
    risk_free_rate: f64,
    target_return: f64,
) -> Option<f64> {
    if returns.is_empty() {
        return None;
    }
    let mean = statistics::mean(returns).ok()?;
    let downside: Vec<f64> = returns
        .iter()
        .map(|r| {
            let diff = r - target_return;
            if diff < 0.0 {
                diff * diff
            } else {
                0.0
            }
        })
        .collect();
    let downside_var = downside.iter().sum::<f64>() / downside.len() as f64;
    let downside_dev = downside_var.sqrt();
    if downside_dev == 0.0 {
        return None;
    }
    let daily_rf = risk_free_rate / 252.0;
    Some((mean - daily_rf) / downside_dev * 252.0_f64.sqrt())
}

/// Calmar ratio.
pub fn calmar_ratio(returns: &[f64], risk_free_rate: f64) -> Option<f64> {
    if returns.len() < 2 {
        return None;
    }
    let mean = statistics::mean(returns).ok()?;
    let annualized_return = mean * 252.0;
    // Compute max drawdown from cumulative returns
    let mut cumulative = 1.0;
    let mut peak = 1.0;
    let mut max_dd = 0.0_f64;
    for r in returns {
        cumulative *= 1.0 + r;
        if cumulative > peak {
            peak = cumulative;
        }
        let dd = (peak - cumulative) / peak;
        if dd > max_dd {
            max_dd = dd;
        }
    }
    if max_dd == 0.0 {
        return None;
    }
    Some((annualized_return - risk_free_rate) / max_dd)
}

/// Beta of an asset relative to a benchmark.
pub fn beta(asset_returns: &[f64], benchmark_returns: &[f64]) -> Option<f64> {
    if asset_returns.len() != benchmark_returns.len() || asset_returns.len() < 2 {
        return None;
    }
    let asset_mean = statistics::mean(asset_returns).ok()?;
    let bench_mean = statistics::mean(benchmark_returns).ok()?;
    let mut cov = 0.0;
    let mut bench_var = 0.0;
    for (a, b) in asset_returns.iter().zip(benchmark_returns.iter()) {
        cov += (a - asset_mean) * (b - bench_mean);
        bench_var += (b - bench_mean).powi(2);
    }
    if bench_var == 0.0 {
        return None;
    }
    Some(cov / bench_var)
}

/// Information ratio.
pub fn information_ratio(
    asset_returns: &[f64],
    benchmark_returns: &[f64],
) -> Option<f64> {
    if asset_returns.len() != benchmark_returns.len() || asset_returns.is_empty() {
        return None;
    }
    let tracking: Vec<f64> = asset_returns
        .iter()
        .zip(benchmark_returns.iter())
        .map(|(a, b)| a - b)
        .collect();
    let mean_tracking = statistics::mean(&tracking).ok()?;
    let tracking_sd = statistics::std_dev(&tracking).ok()?;
    if tracking_sd == 0.0 {
        return None;
    }
    Some(mean_tracking / tracking_sd * 252.0_f64.sqrt())
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_var() {
        let returns = vec![-0.05, -0.02, 0.01, 0.03, -0.01, 0.02, -0.03];
        let v = var(&returns, 0.95).unwrap();
        assert!(v > 0.0);
    }

    #[test]
    fn test_var_confidence() {
        let returns = vec![-0.10, -0.05, -0.02, 0.01, 0.03, 0.05];
        let v = var(&returns, 0.90).unwrap();
        assert!(v > 0.0);
    }

    #[test]
    fn test_cvar() {
        // 20 returns to ensure cutoff > 0
        let mut returns: Vec<f64> = (0..20).map(|i| -0.05 + i as f64 * 0.01).collect();
        let cv = cvar(&returns, 0.90);
        assert!(cv.is_some());
        assert!(cv.unwrap() > 0.0);
    }

    #[test]
    fn test_sortino_ratio() {
        // Returns with some negative values to create downside deviation
        let returns = vec![0.01, -0.005, 0.015, -0.008, 0.012, 0.01, -0.003, 0.011];
        let sr = sortino_ratio(&returns, 0.05, 0.0).unwrap();
        assert!(sr.is_finite());
    }

    #[test]
    fn test_sortino_ratio_empty() {
        assert!(sortino_ratio(&[], 0.05, 0.0).is_none());
    }

    #[test]
    fn test_calmar_ratio() {
        // Returns with a drawdown so max_dd > 0
        let returns = vec![0.02, 0.03, -0.05, 0.01, 0.02, -0.03, 0.04, 0.01, 0.03, 0.02];
        let cr = calmar_ratio(&returns, 0.05);
        assert!(cr.is_some());
    }

    #[test]
    fn test_beta() {
        let asset = vec![0.01, 0.02, -0.01, 0.015, 0.01];
        let bench = vec![0.01, 0.01, 0.005, 0.01, 0.008];
        let b = beta(&asset, &bench).unwrap();
        assert!(b.is_finite());
    }

    #[test]
    fn test_information_ratio() {
        let asset = vec![0.01, 0.02, -0.01, 0.015, 0.01];
        let bench = vec![0.01, 0.01, 0.005, 0.01, 0.008];
        let ir = information_ratio(&asset, &bench).unwrap();
        assert!(ir.is_finite());
    }
}
