//! Statistical functions for financial analytics.

/// Calculate the mean of a slice of f64 values.
///
/// # Errors
/// Returns `StatError::EmptyInput` if the slice is empty.
pub fn mean(data: &[f64]) -> Result<f64, StatError> {
    if data.is_empty() {
        return Err(StatError::EmptyInput);
    }
    Ok(data.iter().sum::<f64>() / data.len() as f64)
}

/// Calculate the variance of a slice of f64 values (sample variance, ddof=1).
///
/// # Errors
/// Returns `StatError::EmptyInput` if the slice has fewer than 2 elements.
pub fn variance(data: &[f64]) -> Result<f64, StatError> {
    if data.len() < 2 {
        return Err(StatError::EmptyInput);
    }
    let m = mean(data)?;
    let sum_sq: f64 = data.iter().map(|x| (x - m).powi(2)).sum();
    Ok(sum_sq / (data.len() - 1) as f64)
}

/// Calculate the standard deviation (sample, ddof=1).
///
/// # Errors
/// Returns `StatError::EmptyInput` if the slice has fewer than 2 elements.
pub fn std_dev(data: &[f64]) -> Result<f64, StatError> {
    Ok(variance(data)?.sqrt())
}

/// Calculate the annualized volatility from returns.
///
/// Assumes daily returns and multiplies by sqrt(252).
///
/// # Errors
/// Returns `StatError::EmptyInput` if fewer than 2 returns.
pub fn annualized_volatility(returns: &[f64]) -> Result<f64, StatError> {
    let sd = std_dev(returns)?;
    Ok(sd * 252.0_f64.sqrt())
}

/// Calculate the Sharpe ratio.
///
/// `Sharpe = (mean_return - risk_free_rate) / std_dev * sqrt(252)`
///
/// # Errors
/// Returns `StatError::EmptyInput` if returns is empty.
/// Returns `StatError::ZeroStdDev` if standard deviation is zero.
pub fn sharpe_ratio(returns: &[f64], risk_free_rate: f64) -> Result<f64, StatError> {
    if returns.is_empty() {
        return Err(StatError::EmptyInput);
    }
    let m = mean(returns)?;
    let sd = std_dev(returns).unwrap_or(0.0);
    if sd == 0.0 {
        return Err(StatError::ZeroStdDev);
    }
    let daily_rf = risk_free_rate / 252.0;
    Ok((m - daily_rf) / sd * 252.0_f64.sqrt())
}

/// Calculate maximum drawdown from a slice of cumulative wealth values.
///
/// Returns the maximum peak-to-trough decline as a positive fraction.
///
/// # Errors
/// Returns `StatError::EmptyInput` if the slice is empty.
pub fn max_drawdown(prices: &[f64]) -> Result<f64, StatError> {
    if prices.is_empty() {
        return Err(StatError::EmptyInput);
    }
    let mut peak = prices[0];
    let mut max_dd = 0.0_f64;
    for &p in prices {
        if p > peak {
            peak = p;
        }
        let dd = (peak - p) / peak;
        if dd > max_dd {
            max_dd = dd;
        }
    }
    Ok(max_dd)
}

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum StatError {
    #[error("Input data is empty or insufficient")]
    EmptyInput,
    #[error("Standard deviation is zero")]
    ZeroStdDev,
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_mean() {
        assert_relative_eq!(mean(&[1.0, 2.0, 3.0, 4.0, 5.0]).unwrap(), 3.0);
    }

    #[test]
    fn test_mean_empty() {
        assert_eq!(mean(&[]), Err(StatError::EmptyInput));
    }

    #[test]
    fn test_variance() {
        // Sample variance of [2,4,4,4,5,5,7,9] = 4.5714...
        let v = variance(&[2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]).unwrap();
        assert_relative_eq!(v, 4.571428571428571, epsilon = 1e-10);
    }

    #[test]
    fn test_variance_single() {
        assert_eq!(variance(&[1.0]), Err(StatError::EmptyInput));
    }

    #[test]
    fn test_std_dev() {
        // Sample std dev of [2,4,4,4,5,5,7,9] = sqrt(4.5714) ≈ 2.1381
        let sd = std_dev(&[2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]).unwrap();
        assert_relative_eq!(sd, 2.138089935299395, epsilon = 1e-10);
    }

    #[test]
    fn test_annualized_volatility() {
        let returns = vec![0.01, -0.01, 0.02, -0.02, 0.015];
        let vol = annualized_volatility(&returns).unwrap();
        assert!(vol > 0.0);
    }

    #[test]
    fn test_sharpe_ratio() {
        // Use returns with variance so std_dev is non-zero
        let returns = vec![0.01, 0.02, -0.005, 0.015, 0.008];
        let sr = sharpe_ratio(&returns, 0.05).unwrap();
        assert!(sr.is_finite());
    }

    #[test]
    fn test_sharpe_ratio_zero_std() {
        let returns = vec![0.01, 0.01, 0.01];
        assert_eq!(sharpe_ratio(&returns, 0.0), Err(StatError::ZeroStdDev));
    }

    #[test]
    fn test_max_drawdown() {
        let prices = vec![100.0, 110.0, 105.0, 90.0, 95.0, 100.0];
        let dd = max_drawdown(&prices).unwrap();
        assert_relative_eq!(dd, (110.0 - 90.0) / 110.0);
    }

    #[test]
    fn test_max_drawdown_no_drawdown() {
        let prices = vec![100.0, 110.0, 120.0, 130.0];
        let dd = max_drawdown(&prices).unwrap();
        assert_relative_eq!(dd, 0.0);
    }

    #[test]
    fn test_max_drawdown_empty() {
        assert_eq!(max_drawdown(&[]), Err(StatError::EmptyInput));
    }
}
