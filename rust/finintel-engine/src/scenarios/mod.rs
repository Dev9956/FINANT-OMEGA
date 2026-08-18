//! FININT OMEGA — Scenario analysis and stress testing.

/// Scenario shock definition.
#[derive(Debug, Clone)]
pub struct ScenarioShock {
    pub name: String,
    pub shocks: Vec<(String, f64)>, // (factor_name, shock_magnitude)
}

impl ScenarioShock {
    pub fn new(name: &str, shocks: Vec<(String, f64)>) -> Self {
        Self {
            name: name.to_string(),
            shocks,
        }
    }
}

/// Apply scenario shocks to portfolio returns.
pub fn apply_scenario(
    base_returns: &[f64],
    factor_loadings: &[f64],
    scenario: &ScenarioShock,
) -> Result<Vec<f64>, ScenarioError> {
    if base_returns.len() != factor_loadings.len() {
        return Err(ScenarioError::DimensionMismatch);
    }
    let total_shock: f64 = scenario
        .shocks
        .iter()
        .map(|(_name, magnitude)| {
            // Simplified: sum all shocks
            magnitude
        })
        .sum();
    let stressed_returns: Vec<f64> = base_returns
        .iter()
        .zip(factor_loadings.iter())
        .map(|(r, loading)| r + loading * total_shock)
        .collect();
    Ok(stressed_returns)
}

/// Monte Carlo simulation of portfolio returns.
pub fn monte_carlo(
    mean_return: f64,
    std_dev: f64,
    n_periods: usize,
    n_simulations: usize,
    seed: u64,
) -> Vec<Vec<f64>> {
    // Simple LCG pseudo-random generator for reproducibility
    let mut results = Vec::with_capacity(n_simulations);
    let mut state = seed;
    for _ in 0..n_simulations {
        let mut path = Vec::with_capacity(n_periods);
        for _ in 0..n_periods {
            // Box-Muller transform approximation
            let mut u1 = lcg_next(&mut state) as f64 / u64::MAX as f64;
            let mut u2 = lcg_next(&mut state) as f64 / u64::MAX as f64;
            // Guard against u1=0 which would produce ln(0)=-inf
            if u1 < 1e-10 { u1 = 1e-10; }
            if u2 < 1e-10 { u2 = 1e-10; }
            let z = (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos();
            let daily_return = mean_return / 252.0 + (std_dev / 252.0_f64.sqrt()) * z;
            path.push(daily_return);
        }
        results.push(path);
    }
    results
}

/// Historical stress test: apply past crisis returns.
pub fn historical_stress(
    current_returns: &[f64],
    crisis_returns: &[f64],
) -> Vec<f64> {
    let n = current_returns.len().min(crisis_returns.len());
    current_returns[..n]
        .iter()
        .zip(crisis_returns[..n].iter())
        .map(|(c, crisis)| c + crisis)
        .collect()
}

fn lcg_next(state: &mut u64) -> u64 {
    *state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
    *state
}

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum ScenarioError {
    #[error("Dimension mismatch between returns and factor loadings")]
    DimensionMismatch,
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_scenario_shock() {
        let scenario = ScenarioShock::new(
            "oil_spike",
            vec![("oil".into(), 0.30), ("usd_inr".into(), 0.10)],
        );
        assert_eq!(scenario.name, "oil_spike");
        assert_eq!(scenario.shocks.len(), 2);
    }

    #[test]
    fn test_apply_scenario() {
        let base_returns = vec![0.01, 0.02, -0.01];
        let factor_loadings = vec![0.5, 0.3, 0.8];
        let scenario = ScenarioShock::new("test", vec![("factor".into(), 0.10)]);
        let result = apply_scenario(&base_returns, &factor_loadings, &scenario).unwrap();
        assert_eq!(result.len(), 3);
        assert!(result[0] > base_returns[0]); // Positive shock
    }

    #[test]
    fn test_monte_carlo() {
        let paths = monte_carlo(0.10, 0.20, 252, 100, 42);
        assert_eq!(paths.len(), 100);
        assert_eq!(paths[0].len(), 252);
        // All returns should be finite
        for path in &paths {
            for r in path {
                assert!(r.is_finite());
            }
        }
    }

    #[test]
    fn test_historical_stress() {
        let current = vec![0.01, 0.02, 0.01];
        let crisis = vec![-0.05, -0.03, -0.02];
        let result = historical_stress(&current, &crisis);
        assert_eq!(result.len(), 3);
        assert_relative_eq!(result[0], -0.04);
    }

    #[test]
    fn test_scenario_dimension_error() {
        let result = apply_scenario(&[0.01], &[0.5, 0.3], &ScenarioShock::new("t", vec![]));
        assert_eq!(result, Err(ScenarioError::DimensionMismatch));
    }
}
