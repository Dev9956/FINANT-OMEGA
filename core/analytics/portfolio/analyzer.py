"""FININT OMEGA — Portfolio analytics: holdings, weights, P&L, benchmark, sector exposure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pydantic import BaseModel, Field


class Position(BaseModel):
    """A single portfolio position."""

    symbol: str
    name: str = ""
    quantity: float = 0.0
    avg_cost: float = 0.0
    current_price: float = 0.0
    sector: str = "Unknown"
    asset_class: str = "Equity"
    currency: str = "USD"

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float | None:
        if self.cost_basis == 0:
            return None
        return self.unrealized_pnl / abs(self.cost_basis)


class BenchmarkReturn(BaseModel):
    """Benchmark return data point."""

    date: date
    return_pct: float


class PortfolioAnalyzer:
    """Analyze portfolio holdings, weights, P&L, benchmark, and sector exposure."""

    def __init__(self, positions: list[Position] | None = None, benchmark: list[BenchmarkReturn] | None = None) -> None:
        self._positions: list[Position] = positions or []
        self._benchmark: list[BenchmarkReturn] = benchmark or []

    @property
    def positions(self) -> list[Position]:
        return list(self._positions)

    def set_positions(self, positions: list[Position]) -> None:
        self._positions = list(positions)

    def set_benchmark(self, benchmark: list[BenchmarkReturn]) -> None:
        self._benchmark = list(benchmark)

    def total_market_value(self) -> float:
        return sum(p.market_value for p in self._positions)

    def total_cost_basis(self) -> float:
        return sum(p.cost_basis for p in self._positions)

    def total_pnl(self) -> float:
        return self.total_market_value() - self.total_cost_basis()

    def total_pnl_pct(self) -> float | None:
        basis = self.total_cost_basis()
        if basis == 0:
            return None
        return self.total_pnl() / abs(basis)

    def weights(self) -> dict[str, float]:
        total = self.total_market_value()
        if total == 0:
            return {}
        return {p.symbol: p.market_value / total for p in self._positions}

    def sector_exposure(self) -> dict[str, float]:
        total = self.total_market_value()
        if total == 0:
            return {}
        sectors: dict[str, float] = {}
        for p in self._positions:
            sectors[p.sector] = sectors.get(p.sector, 0.0) + p.market_value
        return {k: v / total for k, v in sectors.items()}

    def holdings_summary(self) -> list[dict]:
        return [
            {
                "symbol": p.symbol,
                "name": p.name,
                "quantity": p.quantity,
                "market_value": p.market_value,
                "weight": p.market_value / self.total_market_value() if self.total_market_value() else 0,
                "pnl": p.unrealized_pnl,
                "pnl_pct": p.unrealized_pnl_pct,
                "sector": p.sector,
            }
            for p in self._positions
        ]

    def benchmark_comparison(self) -> dict | None:
        if not self._benchmark:
            return None
        cum_return = 1.0
        for r in self._benchmark:
            cum_return *= 1 + r.return_pct
        return {
            "periods": len(self._benchmark),
            "cumulative_return": cum_return - 1,
            "annualized_return": (cum_return ** (252 / max(len(self._benchmark), 1))) - 1,
        }
