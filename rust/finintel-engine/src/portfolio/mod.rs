//! FININT OMEGA — Portfolio analytics.

/// Portfolio weights.
#[derive(Debug, Clone, PartialEq)]
pub struct Portfolio {
    pub symbols: Vec<String>,
    pub weights: Vec<f64>,
}

impl Portfolio {
    pub fn new(symbols: Vec<String>, weights: Vec<f64>) -> Result<Self, PortfolioError> {
        if symbols.len() != weights.len() {
            return Err(PortfolioError::DimensionMismatch);
        }
        if symbols.is_empty() {
            return Err(PortfolioError::EmptyPortfolio);
        }
        let sum: f64 = weights.iter().sum();
        if (sum - 1.0).abs() > 1e-6 {
            return Err(PortfolioError::WeightsNotSumToOne);
        }
        Ok(Self { symbols, weights })
    }

    /// Portfolio expected return given asset expected returns.
    pub fn expected_return(&self, asset_returns: &[f64]) -> Result<f64, PortfolioError> {
        if asset_returns.len() != self.weights.len() {
            return Err(PortfolioError::DimensionMismatch);
        }
        Ok(self
            .weights
            .iter()
            .zip(asset_returns.iter())
            .map(|(w, r)| w * r)
            .sum())
    }

    /// Portfolio variance given covariance matrix.
    pub fn variance(&self, cov_matrix: &[Vec<f64>]) -> Result<f64, PortfolioError> {
        let n = self.weights.len();
        if cov_matrix.len() != n {
            return Err(PortfolioError::DimensionMismatch);
        }
        for row in cov_matrix {
            if row.len() != n {
                return Err(PortfolioError::DimensionMismatch);
            }
        }
        let mut var = 0.0;
        for i in 0..n {
            for j in 0..n {
                var += self.weights[i] * self.weights[j] * cov_matrix[i][j];
            }
        }
        Ok(var)
    }

    /// Portfolio standard deviation.
    pub fn std_dev(&self, cov_matrix: &[Vec<f64>]) -> Result<f64, PortfolioError> {
        Ok(self.variance(cov_matrix)?.sqrt())
    }

    /// Concentration: Herfindahl–Hirschman Index.
    pub fn hhi(&self) -> f64 {
        self.weights.iter().map(|w| w * w).sum()
    }

    /// Asset contribution to risk.
    pub fn risk_contribution(&self, cov_matrix: &[Vec<f64>]) -> Result<Vec<f64>, PortfolioError> {
        let n = self.weights.len();
        let port_var = self.variance(cov_matrix)?;
        if port_var == 0.0 {
            return Ok(vec![0.0; n]);
        }
        let mut contributions = Vec::with_capacity(n);
        for i in 0..n {
            let mut marginal = 0.0;
            for j in 0..n {
                marginal += self.weights[j] * cov_matrix[i][j];
            }
            contributions.push(self.weights[i] * marginal / port_var.sqrt());
        }
        Ok(contributions)
    }

    /// Sector exposure (given asset-to-sector mapping).
    pub fn sector_exposure(
        &self,
        asset_sectors: &[&str],
    ) -> Result<Vec<(String, f64)>, PortfolioError> {
        if asset_sectors.len() != self.weights.len() {
            return Err(PortfolioError::DimensionMismatch);
        }
        let mut exposure: std::collections::HashMap<String, f64> = std::collections::HashMap::new();
        for (sector, weight) in asset_sectors.iter().zip(self.weights.iter()) {
            *exposure.entry(sector.to_string()).or_insert(0.0) += weight;
        }
        let mut result: Vec<(String, f64)> = exposure.into_iter().collect();
        result.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        Ok(result)
    }
}

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum PortfolioError {
    #[error("Dimension mismatch between symbols and weights")]
    DimensionMismatch,
    #[error("Portfolio is empty")]
    EmptyPortfolio,
    #[error("Weights do not sum to 1.0")]
    WeightsNotSumToOne,
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    fn test_portfolio() -> Portfolio {
        Portfolio::new(
            vec!["A".into(), "B".into(), "C".into()],
            vec![0.5, 0.3, 0.2],
        )
        .unwrap()
    }

    #[test]
    fn test_portfolio_creation() {
        let p = test_portfolio();
        assert_eq!(p.symbols.len(), 3);
    }

    #[test]
    fn test_portfolio_bad_weights() {
        let result = Portfolio::new(vec!["A".into()], vec![0.5]);
        assert_eq!(result, Err(PortfolioError::WeightsNotSumToOne));
    }

    #[test]
    fn test_expected_return() {
        let p = test_portfolio();
        let returns = vec![0.10, 0.05, 0.08];
        let er = p.expected_return(&returns).unwrap();
        assert_relative_eq!(er, 0.5 * 0.10 + 0.3 * 0.05 + 0.2 * 0.08);
    }

    #[test]
    fn test_variance() {
        let p = test_portfolio();
        let cov = vec![
            vec![0.04, 0.01, 0.005],
            vec![0.01, 0.09, 0.01],
            vec![0.005, 0.01, 0.0625],
        ];
        let var = p.variance(&cov).unwrap();
        assert!(var > 0.0);
    }

    #[test]
    fn test_hhi() {
        let p = test_portfolio();
        let hhi = p.hhi();
        assert_relative_eq!(hhi, 0.25 + 0.09 + 0.04);
    }

    #[test]
    fn test_risk_contribution() {
        let p = test_portfolio();
        let cov = vec![
            vec![0.04, 0.01, 0.005],
            vec![0.01, 0.09, 0.01],
            vec![0.005, 0.01, 0.0625],
        ];
        let rc = p.risk_contribution(&cov).unwrap();
        assert_eq!(rc.len(), 3);
        assert!(rc.iter().all(|&x| x >= 0.0));
    }

    #[test]
    fn test_sector_exposure() {
        let p = test_portfolio();
        let sectors = vec!["Tech", "Finance", "Tech"];
        let exp = p.sector_exposure(&sectors).unwrap();
        assert_eq!(exp.len(), 2);
        assert!(exp[0].1 > exp[1].1); // Tech > Finance
    }
}
