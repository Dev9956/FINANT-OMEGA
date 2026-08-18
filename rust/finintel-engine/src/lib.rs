//! FININT OMEGA — Quantitative Engine
//!
//! High-performance numerical computation for financial analytics.

pub mod returns;
pub mod statistics;
pub mod indicators;
pub mod factors;
pub mod portfolio;
pub mod risk;
pub mod attribution;
pub mod scenarios;
pub mod backtest;
pub mod simulation;
pub mod bindings;

/// Engine version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
