"""FININT OMEGA — Risk analytics: volatility, beta, correlation, VaR, CVaR, drawdown."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pydantic import BaseModel


class RiskMetrics(BaseModel):
    """Aggregated risk metrics."""

    volatility: float = 0.0
    annualized_volatility: float = 0.0
    beta: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown: float = 0.0
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0


class RiskAnalyzer:
    """Compute portfolio risk metrics from return series."""

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        self._risk_free_rate = risk_free_rate

    def _returns_stats(self, returns: list[float]) -> tuple[float, float]:
        n = len(returns)
        if n < 2:
            return 0.0, 0.0
        mean = sum(returns) / n
        variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
        return mean, math.sqrt(variance)

    def volatility(self, returns: list[float]) -> float:
        _, vol = self._returns_stats(returns)
        return vol

    def annualized_volatility(self, returns: list[float]) -> float:
        return self.volatility(returns) * math.sqrt(252)

    def beta(self, asset_returns: list[float], market_returns: list[float]) -> float | None:
        if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
            return None
        n = len(asset_returns)
        mean_a = sum(asset_returns) / n
        mean_m = sum(market_returns) / n
        cov = sum((a - mean_a) * (m - mean_m) for a, m in zip(asset_returns, market_returns)) / (n - 1)
        var_m = sum((m - mean_m) ** 2 for m in market_returns) / (n - 1)
        if var_m == 0:
            return None
        return cov / var_m

    def correlation(self, x: list[float], y: list[float]) -> float | None:
        if len(x) != len(y) or len(x) < 2:
            return None
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / (n - 1)
        _, std_x = self._returns_stats(x)
        _, std_y = self._returns_stats(y)
        if std_x == 0 or std_y == 0:
            return None
        return cov / (std_x * std_y)

    def var(self, returns: list[float], confidence: float = 0.95) -> float:
        sorted_r = sorted(returns)
        idx = int((1 - confidence) * len(sorted_r))
        idx = max(0, min(idx, len(sorted_r) - 1))
        return -sorted_r[idx]

    def cvar(self, returns: list[float], confidence: float = 0.95) -> float:
        sorted_r = sorted(returns)
        cutoff = int((1 - confidence) * len(sorted_r))
        cutoff = max(1, cutoff)
        tail = sorted_r[:cutoff]
        return -sum(tail) / len(tail)

    def max_drawdown(self, returns: list[float]) -> float:
        cumulative = 1.0
        peak = 1.0
        max_dd = 0.0
        for r in returns:
            cumulative *= 1 + r
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def sharpe_ratio(self, returns: list[float]) -> float:
        mean_r, vol = self._returns_stats(returns)
        if vol == 0:
            return 0.0
        return (mean_r - self._risk_free_rate) / vol * math.sqrt(252)

    def sortino_ratio(self, returns: list[float]) -> float:
        mean_r, _ = self._returns_stats(returns)
        downside = [r for r in returns if r < self._risk_free_rate]
        if not downside:
            return 0.0
        downside_dev = math.sqrt(sum((r - self._risk_free_rate) ** 2 for r in downside) / len(downside))
        if downside_dev == 0:
            return 0.0
        return (mean_r - self._risk_free_rate) / downside_dev * math.sqrt(252)

    def compute_all(self, returns: list[float], market_returns: list[float] | None = None) -> RiskMetrics:
        beta_val = self.beta(returns, market_returns) if market_returns else None
        return RiskMetrics(
            volatility=self.volatility(returns),
            annualized_volatility=self.annualized_volatility(returns),
            beta=beta_val,
            sharpe_ratio=self.sharpe_ratio(returns),
            sortino_ratio=self.sortino_ratio(returns),
            max_drawdown=self.max_drawdown(returns),
            var_95=self.var(returns, 0.95),
            var_99=self.var(returns, 0.99),
            cvar_95=self.cvar(returns, 0.95),
            cvar_99=self.cvar(returns, 0.99),
        )
