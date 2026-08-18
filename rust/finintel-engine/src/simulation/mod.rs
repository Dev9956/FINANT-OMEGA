//! FININT OMEGA — Monte Carlo simulation helpers.

pub use super::scenarios::monte_carlo;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_monte_carlo_basic() {
        let paths = monte_carlo(0.10, 0.20, 252, 1000, 42);
        assert_eq!(paths.len(), 1000);
        assert_eq!(paths[0].len(), 252);
    }
}
