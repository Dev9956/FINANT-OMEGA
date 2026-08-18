//! FININT OMEGA — Attribution analysis.

/// Asset-level attribution.
pub fn asset_attribution(
    portfolio_weights: &[f64],
    portfolio_returns: &[f64],
    benchmark_weights: &[f64],
    benchmark_returns: &[f64],
) -> Result<Vec<f64>, AttributionError> {
    let n = portfolio_weights.len();
    if n != portfolio_returns.len() || n != benchmark_weights.len() || n != benchmark_returns.len() {
        return Err(AttributionError::DimensionMismatch);
    }
    let mut contributions = Vec::with_capacity(n);
    for i in 0..n {
        let contribution = portfolio_weights[i] * portfolio_returns[i]
            - benchmark_weights[i] * benchmark_returns[i];
        contributions.push(contribution);
    }
    Ok(contributions)
}

/// Sector-level attribution.
pub fn sector_attribution(
    sector_weights: &[f64],
    sector_returns: &[f64],
    benchmark_sector_weights: &[f64],
    benchmark_sector_returns: &[f64],
) -> Result<Vec<(String, f64, f64)>, AttributionError> {
    let n = sector_weights.len();
    if n != sector_returns.len()
        || n != benchmark_sector_weights.len()
        || n != benchmark_sector_returns.len()
    {
        return Err(AttributionError::DimensionMismatch);
    }
    let mut results = Vec::with_capacity(n);
    for i in 0..n {
        let allocation = (sector_weights[i] - benchmark_sector_weights[i]) * benchmark_sector_returns[i];
        let selection = benchmark_sector_weights[i] * (sector_returns[i] - benchmark_sector_returns[i]);
        let _total = allocation + selection;
        results.push((format!("Sector_{}", i), allocation, selection));
    }
    Ok(results)
}

/// Brinson-Fachler attribution.
pub fn brinson_attribution(
    portfolio_weights: &[f64],
    portfolio_returns: &[f64],
    benchmark_weights: &[f64],
    benchmark_returns: &[f64],
) -> Result<BrinsonResult, AttributionError> {
    let n = portfolio_weights.len();
    if n != portfolio_returns.len() || n != benchmark_weights.len() || n != benchmark_returns.len() {
        return Err(AttributionError::DimensionMismatch);
    }
    let total_bench_return: f64 = benchmark_weights.iter().zip(benchmark_returns.iter()).map(|(w, r)| w * r).sum();
    let mut allocation = 0.0;
    let mut selection = 0.0;
    let mut interaction = 0.0;
    for i in 0..n {
        let aw = portfolio_weights[i] - benchmark_weights[i];
        let ar = benchmark_returns[i] - total_bench_return;
        allocation += aw * ar;
        selection += benchmark_weights[i] * (portfolio_returns[i] - benchmark_returns[i]);
        interaction += aw * (portfolio_returns[i] - benchmark_returns[i]);
    }
    Ok(BrinsonResult {
        allocation_effect: allocation,
        selection_effect: selection,
        interaction_effect: interaction,
        total_active_return: allocation + selection + interaction,
    })
}

#[derive(Debug, Clone)]
pub struct BrinsonResult {
    pub allocation_effect: f64,
    pub selection_effect: f64,
    pub interaction_effect: f64,
    pub total_active_return: f64,
}

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum AttributionError {
    #[error("Dimension mismatch")]
    DimensionMismatch,
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_asset_attribution() {
        let pw = vec![0.6, 0.4];
        let pr = vec![0.10, 0.05];
        let bw = vec![0.5, 0.5];
        let br = vec![0.08, 0.06];
        let result = asset_attribution(&pw, &pr, &bw, &br).unwrap();
        assert_eq!(result.len(), 2);
        assert_relative_eq!(result[0], 0.6 * 0.10 - 0.5 * 0.08);
    }

    #[test]
    fn test_brinson_attribution() {
        let pw = vec![0.6, 0.4];
        let pr = vec![0.10, 0.05];
        let bw = vec![0.5, 0.5];
        let br = vec![0.08, 0.06];
        let result = brinson_attribution(&pw, &pr, &bw, &br).unwrap();
        assert!(result.total_active_return.is_finite());
    }

    #[test]
    fn test_attribution_dimension_error() {
        let result = asset_attribution(&[0.5], &[0.1, 0.2], &[0.5], &[0.1]);
        assert_eq!(result, Err(AttributionError::DimensionMismatch));
    }
}
