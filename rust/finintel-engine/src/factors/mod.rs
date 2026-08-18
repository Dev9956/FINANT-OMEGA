//! FININT OMEGA — Factor models.

/// Fama-French style factor exposure.
#[derive(Debug, Clone)]
pub struct FactorExposure {
    pub value: f64,
    pub growth: f64,
    pub quality: f64,
    pub momentum: f64,
    pub size: f64,
    pub volatility: f64,
    pub liquidity: f64,
}

impl FactorExposure {
    pub fn zero() -> Self {
        Self {
            value: 0.0,
            growth: 0.0,
            quality: 0.0,
            momentum: 0.0,
            size: 0.0,
            volatility: 0.0,
            liquidity: 0.0,
        }
    }
}

/// Compute momentum factor from price series.
/// momentum = (price[t] / price[t-n]) - 1
pub fn momentum_factor(prices: &[f64], lookback: usize) -> Option<f64> {
    if prices.len() <= lookback || lookback == 0 {
        return None;
    }
    let n = prices.len();
    if prices[n - 1 - lookback] == 0.0 {
        return None;
    }
    Some(prices[n - 1] / prices[n - 1 - lookback] - 1.0)
}

/// Compute volatility factor (inverse volatility weighting).
pub fn volatility_factor(returns: &[f64]) -> Option<f64> {
    if returns.len() < 2 {
        return None;
    }
    let mean = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / (returns.len() - 1) as f64;
    let vol = variance.sqrt();
    if vol == 0.0 {
        return None;
    }
    Some(1.0 / vol)
}

/// Compute value factor from valuation metrics.
pub fn value_factor(pe_ratio: f64, pb_ratio: f64) -> f64 {
    // Lower PE and PB → higher value score
    let pe_score = if pe_ratio > 0.0 { 1.0 / pe_ratio } else { 0.0 };
    let pb_score = if pb_ratio > 0.0 { 1.0 / pb_ratio } else { 0.0 };
    (pe_score + pb_score) / 2.0
}

/// Compute quality factor from financial metrics.
pub fn quality_factor(roe: f64, roa: f64, debt_equity: f64) -> f64 {
    let roe_score = roe.clamp(0.0, 1.0);
    let roa_score = roa.clamp(0.0, 1.0);
    let leverage_penalty = if debt_equity > 0.0 {
        (1.0 / (1.0 + debt_equity)).clamp(0.0, 1.0)
    } else {
        1.0
    };
    (roe_score + roa_score + leverage_penalty) / 3.0
}

/// Compute size factor (log market cap).
pub fn size_factor(market_cap: f64) -> Option<f64> {
    if market_cap <= 0.0 {
        return None;
    }
    Some(market_cap.ln())
}

/// Compute liquidity factor from average daily volume.
pub fn liquidity_factor(avg_daily_volume: f64, avg_daily_turnover: f64) -> f64 {
    if avg_daily_turnover == 0.0 {
        return 0.0;
    }
    avg_daily_volume / avg_daily_turnover
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_momentum_factor() {
        let prices = vec![100.0, 110.0, 105.0, 120.0, 115.0];
        let m = momentum_factor(&prices, 2).unwrap();
        assert_relative_eq!(m, (115.0 / 105.0) - 1.0);
    }

    #[test]
    fn test_momentum_factor_insufficient_data() {
        let prices = vec![100.0, 110.0];
        assert!(momentum_factor(&prices, 5).is_none());
    }

    #[test]
    fn test_volatility_factor() {
        let returns = vec![0.01, -0.01, 0.02, -0.02, 0.015];
        let vf = volatility_factor(&returns).unwrap();
        assert!(vf > 0.0);
    }

    #[test]
    fn test_volatility_factor_single() {
        assert!(volatility_factor(&[0.01]).is_none());
    }

    #[test]
    fn test_value_factor() {
        let vf = value_factor(15.0, 2.0);
        assert!(vf > 0.0);
    }

    #[test]
    fn test_quality_factor() {
        let qf = quality_factor(0.20, 0.10, 0.5);
        assert!(qf > 0.0 && qf <= 1.0);
    }

    #[test]
    fn test_size_factor() {
        let sf = size_factor(1_000_000_000.0).unwrap();
        assert!(sf > 0.0);
    }

    #[test]
    fn test_size_factor_zero() {
        assert!(size_factor(0.0).is_none());
    }

    #[test]
    fn test_liquidity_factor() {
        let lf = liquidity_factor(1_000_000.0, 50_000_000.0);
        assert_relative_eq!(lf, 0.02);
    }

    #[test]
    fn test_factor_exposure_zero() {
        let fe = FactorExposure::zero();
        assert_eq!(fe.value, 0.0);
        assert_eq!(fe.momentum, 0.0);
    }
}
