"""FININT OMEGA — Factor analytics: value, growth, quality, momentum, size."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FactorName(str, Enum):
    VALUE = "value"
    GROWTH = "growth"
    QUALITY = "quality"
    MOMENTUM = "momentum"
    SIZE = "size"


class FactorExposure(BaseModel):
    """Factor exposure for a single security."""

    symbol: str
    value: float = 0.0
    growth: float = 0.0
    quality: float = 0.0
    momentum: float = 0.0
    size: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            FactorName.VALUE: self.value,
            FactorName.GROWTH: self.growth,
            FactorName.QUALITY: self.quality,
            FactorName.MOMENTUM: self.momentum,
            FactorName.SIZE: self.size,
        }


class FactorAnalyzer:
    """Compute factor exposures and portfolio factor decomposition."""

    def score_value(self, pe: float | None, pb: float | None, fcf_yield: float | None) -> float:
        score = 0.0
        count = 0
        if pe is not None and pe > 0:
            score += 1.0 / pe
            count += 1
        if pb is not None and pb > 0:
            score += 1.0 / pb
            count += 1
        if fcf_yield is not None:
            score += fcf_yield
            count += 1
        return score / count if count > 0 else 0.0

    def score_growth(self, revenue_growth: float | None, earnings_growth: float | None) -> float:
        score = 0.0
        count = 0
        if revenue_growth is not None:
            score += revenue_growth
            count += 1
        if earnings_growth is not None:
            score += earnings_growth
            count += 1
        return score / count if count > 0 else 0.0

    def score_quality(self, roe: float | None, roce: float | None, debt_equity: float | None) -> float:
        score = 0.0
        count = 0
        if roe is not None:
            score += roe
            count += 1
        if roce is not None:
            score += roce
            count += 1
        if debt_equity is not None:
            score -= debt_equity * 0.1
            count += 1
        return score / count if count > 0 else 0.0

    def score_momentum(self, returns: list[float], lookback: int = 252) -> float:
        if not returns:
            return 0.0
        window = returns[-lookback:] if len(returns) >= lookback else returns
        cumulative = 1.0
        for r in window:
            cumulative *= 1 + r
        return cumulative - 1

    def score_size(self, market_cap: float | None, median_cap: float = 1e9) -> float:
        if market_cap is None or median_cap == 0:
            return 0.0
        return -1.0 if market_cap < median_cap else 1.0

    def compute_exposure(self, fundamentals: dict, price_history: list[float] | None = None, median_cap: float = 1e9) -> FactorExposure:
        symbol = fundamentals.get("symbol", "unknown")
        return FactorExposure(
            symbol=symbol,
            value=self.score_value(
                fundamentals.get("pe_ratio"),
                fundamentals.get("pb_ratio"),
                fundamentals.get("fcf_yield"),
            ),
            growth=self.score_growth(
                fundamentals.get("revenue_growth_yoy"),
                fundamentals.get("earnings_growth_yoy"),
            ),
            quality=self.score_quality(
                fundamentals.get("roe"),
                fundamentals.get("roce"),
                fundamentals.get("debt_equity"),
            ),
            momentum=self.score_momentum(price_history or []),
            size=self.score_size(fundamentals.get("market_cap"), median_cap),
        )

    def portfolio_factor_exposure(self, holdings: list[dict], exposures: dict[str, FactorExposure]) -> dict[str, float]:
        totals: dict[str, float] = {f.value: 0.0 for f in FactorName}
        for h in holdings:
            sym = h.get("symbol", "")
            weight = h.get("weight", 0.0)
            exp = exposures.get(sym)
            if exp:
                totals["value"] += weight * exp.value
                totals["growth"] += weight * exp.growth
                totals["quality"] += weight * exp.quality
                totals["momentum"] += weight * exp.momentum
                totals["size"] += weight * exp.size
        return totals
