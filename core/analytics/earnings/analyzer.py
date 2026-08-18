"""FININT OMEGA — Earnings analytics module."""

from __future__ import annotations

from datetime import date


class EarningsRecord:
    """Earnings event record."""

    def __init__(
        self,
        symbol: str,
        report_date: date,
        period_end: date,
        eps_actual: float | None = None,
        eps_estimate: float | None = None,
        revenue_actual: float | None = None,
        revenue_estimate: float | None = None,
    ):
        self.symbol = symbol
        self.report_date = report_date
        self.period_end = period_end
        self.eps_actual = eps_actual
        self.eps_estimate = eps_estimate
        self.revenue_actual = revenue_actual
        self.revenue_estimate = revenue_estimate

    @property
    def eps_surprise(self) -> float | None:
        """EPS surprise (actual - estimate)."""
        if self.eps_actual is not None and self.eps_estimate is not None:
            return self.eps_actual - self.eps_estimate
        return None

    @property
    def eps_surprise_pct(self) -> float | None:
        """EPS surprise percentage."""
        if self.eps_actual is not None and self.eps_estimate and self.eps_estimate != 0:
            return (self.eps_actual - self.eps_estimate) / abs(self.eps_estimate)
        return None

    @property
    def revenue_surprise(self) -> float | None:
        """Revenue surprise."""
        if self.revenue_actual is not None and self.revenue_estimate is not None:
            return self.revenue_actual - self.revenue_estimate
        return None

    @property
    def revenue_surprise_pct(self) -> float | None:
        """Revenue surprise percentage."""
        if self.revenue_actual is not None and self.revenue_estimate and self.revenue_estimate != 0:
            return (self.revenue_actual - self.revenue_estimate) / abs(self.revenue_estimate)
        return None


class EarningsAnalyzer:
    """Analyzes earnings events."""

    def analyze_surprise(self, record: EarningsRecord) -> dict:
        """Analyze an earnings surprise."""
        eps_surp = record.eps_surprise_pct
        rev_surp = record.revenue_surprise_pct

        if eps_surp is not None and eps_surp > 0.05:
            rating = "strong_beat"
        elif eps_surp is not None and eps_surp > 0:
            rating = "beat"
        elif eps_surp is not None and eps_surp < -0.05:
            rating = "strong_miss"
        elif eps_surp is not None and eps_surp < 0:
            rating = "miss"
        else:
            rating = "inline"

        return {
            "symbol": record.symbol,
            "report_date": record.report_date.isoformat(),
            "eps_actual": record.eps_actual,
            "eps_estimate": record.eps_estimate,
            "eps_surprise_pct": eps_surp,
            "revenue_actual": record.revenue_actual,
            "revenue_estimate": record.revenue_estimate,
            "revenue_surprise_pct": rev_surp,
            "rating": rating,
        }

    def compute_earnings_momentum(
        self, records: list[EarningsRecord]
    ) -> dict:
        """Compute earnings momentum over a series of earnings."""
        if not records:
            return {"trend": "unknown", "consecutive_beats": 0, "consecutive_misses": 0}

        consecutive_beats = 0
        consecutive_misses = 0
        for r in reversed(records):
            if r.eps_surprise_pct is not None:
                if r.eps_surprise_pct > 0:
                    consecutive_beats += 1
                    break
                elif r.eps_surprise_pct < 0:
                    consecutive_misses += 1
                    break

        # Full consecutive count
        beat_count = 0
        miss_count = 0
        for r in reversed(records):
            if r.eps_surprise_pct is not None:
                if r.eps_surprise_pct > 0:
                    beat_count += 1
                    miss_count = 0
                elif r.eps_surprise_pct < 0:
                    miss_count += 1
                    beat_count = 0
                else:
                    break

        if beat_count > 0:
            trend = "improving"
        elif miss_count > 0:
            trend = "deteriorating"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "consecutive_beats": beat_count,
            "consecutive_misses": miss_count,
            "total_records": len(records),
        }
