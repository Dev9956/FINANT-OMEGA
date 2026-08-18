//! Return calculations for financial time series.

/// Calculate simple returns from a slice of prices.
///
/// Returns a vector of length `prices.len() - 1`.
/// `returns[i] = (prices[i+1] - prices[i]) / prices[i]`
///
/// # Errors
/// Returns `ReturnError::EmptyInput` if prices is empty.
/// Returns `ReturnError::ZeroPrice` if any price is zero.
pub fn simple_returns(prices: &[f64]) -> Result<Vec<f64>, ReturnError> {
    if prices.is_empty() {
        return Err(ReturnError::EmptyInput);
    }
    if prices.len() < 2 {
        return Ok(Vec::new());
    }
    for &p in prices {
        if p == 0.0 {
            return Err(ReturnError::ZeroPrice);
        }
    }
    Ok(prices
        .windows(2)
        .map(|w| (w[1] - w[0]) / w[0])
        .collect())
}

/// Calculate log returns from a slice of prices.
///
/// `log_return[i] = ln(prices[i+1] / prices[i])`
///
/// # Errors
/// Returns `ReturnError::EmptyInput` if prices is empty.
/// Returns `ReturnError::ZeroPrice` if any price is zero or negative.
pub fn log_returns(prices: &[f64]) -> Result<Vec<f64>, ReturnError> {
    if prices.is_empty() {
        return Err(ReturnError::EmptyInput);
    }
    if prices.len() < 2 {
        return Ok(Vec::new());
    }
    for &p in prices {
        if p <= 0.0 {
            return Err(ReturnError::ZeroPrice);
        }
    }
    Ok(prices
        .windows(2)
        .map(|w| (w[1] / w[0]).ln())
        .collect())
}

/// Calculate Compound Annual Growth Rate.
///
/// `CAGR = (end / start)^(1/years) - 1`
///
/// # Errors
/// Returns `ReturnError::EmptyInput` if prices has fewer than 2 elements.
/// Returns `ReturnError::ZeroPrice` if start price is zero or negative.
pub fn cagr(prices: &[f64]) -> Result<f64, ReturnError> {
    if prices.len() < 2 {
        return Err(ReturnError::EmptyInput);
    }
    let start = prices[0];
    let end = prices[prices.len() - 1];
    if start <= 0.0 {
        return Err(ReturnError::ZeroPrice);
    }
    let years = (prices.len() - 1) as f64;
    Ok((end / start).powf(1.0 / years) - 1.0)
}

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum ReturnError {
    #[error("Input prices slice is empty")]
    EmptyInput,
    #[error("Price is zero or negative")]
    ZeroPrice,
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_simple_returns() {
        let prices = vec![100.0, 110.0, 105.0, 120.0];
        let returns = simple_returns(&prices).unwrap();
        assert_eq!(returns.len(), 3);
        assert_relative_eq!(returns[0], 0.10);
        assert_relative_eq!(returns[1], -0.045454, epsilon = 1e-5);
        assert_relative_eq!(returns[2], 0.142857, epsilon = 1e-5);
    }

    #[test]
    fn test_simple_returns_empty() {
        assert_eq!(simple_returns(&[]), Err(ReturnError::EmptyInput));
    }

    #[test]
    fn test_simple_returns_single() {
        let returns = simple_returns(&[100.0]).unwrap();
        assert!(returns.is_empty());
    }

    #[test]
    fn test_simple_returns_zero_price() {
        assert_eq!(simple_returns(&[100.0, 0.0]), Err(ReturnError::ZeroPrice));
    }

    #[test]
    fn test_log_returns() {
        let prices = vec![100.0, 110.0, 105.0];
        let returns = log_returns(&prices).unwrap();
        assert_eq!(returns.len(), 2);
        assert_relative_eq!(returns[0], 0.09531, epsilon = 1e-4);
        // ln(105/110) = -0.04652
        assert_relative_eq!(returns[1], -0.04652, epsilon = 1e-4);
    }

    #[test]
    fn test_log_returns_negative_price() {
        assert_eq!(log_returns(&[100.0, -10.0]), Err(ReturnError::ZeroPrice));
    }

    #[test]
    fn test_cagr() {
        // (121/100)^(1/1) - 1 = 0.21
        let prices = vec![100.0, 121.0];
        let result = cagr(&prices).unwrap();
        assert_relative_eq!(result, 0.21);
    }

    #[test]
    fn test_cagr_insufficient_data() {
        assert_eq!(cagr(&[100.0]), Err(ReturnError::EmptyInput));
    }
}
