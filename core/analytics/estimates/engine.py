"""FININT OMEGA — Estimate revision engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from core.analytics.estimates.models import (
    EPSRecord,
    EstimateRecord,
    EstimateRevision,
    RevisionMomentum,
    RevenueRecord,
    SurpriseMagnitude,
    SurpriseResult,
    SurpriseType,
)


class EstimateEngine:
    """Engine for tracking and analyzing estimate revisions."""

    def __init__(self) -> None:
        self._records: dict[str, list[EstimateRecord]] = defaultdict(list)

    def add_estimate(self, record: EstimateRecord) -> str:
        """Add an estimate record. Returns the estimate_id."""
        self._records[record.symbol].append(record)
        return record.estimate_id

    def get_estimates(
        self, symbol: str, metric: str | None = None, period: date | None = None
    ) -> list[EstimateRecord]:
        """Get estimates for a symbol, optionally filtered by metric and period."""
        records = self._records.get(symbol, [])
        if metric is not None:
            records = [r for r in records if r.metric == metric]
        if period is not None:
            records = [r for r in records if r.period_end == period]
        return list(records)

    def compute_surprise(
        self, symbol: str, period_end: date, as_of: date | None = None
    ) -> SurpriseResult | None:
        """Compute earnings surprise for a given period.

        If as_of is provided, only estimates available before that date are used
        to prevent future-information leakage.
        """
        records = self._records.get(symbol, [])
        period_records = [r for r in records if r.period_end == period_end]
        if not period_records:
            return None

        if as_of is not None:
            period_records = [r for r in period_records if r.timestamp.date() <= as_of]
            if not period_records:
                return None

        latest = max(period_records, key=lambda r: r.timestamp)

        eps_surprise_pct: float | None = None
        if latest.actual_value is not None and latest.estimate_value is not None:
            if latest.estimate_value != 0:
                eps_surprise_pct = (
                    (latest.actual_value - latest.estimate_value)
                    / abs(latest.estimate_value)
                )

        revenue_surprise_pct: float | None = None
        if latest.consensus_value is not None and latest.actual_value is not None:
            if latest.consensus_value != 0:
                revenue_surprise_pct = (
                    (latest.actual_value - latest.consensus_value)
                    / abs(latest.consensus_value)
                )

        surprise_type = SurpriseType.inline
        magnitude = SurpriseMagnitude.slight

        if eps_surprise_pct is not None:
            if eps_surprise_pct > 0.02:
                surprise_type = SurpriseType.beat
            elif eps_surprise_pct < -0.02:
                surprise_type = SurpriseType.miss
            else:
                surprise_type = SurpriseType.inline

            abs_surprise = abs(eps_surprise_pct)
            if abs_surprise > 0.10:
                magnitude = SurpriseMagnitude.significant
            elif abs_surprise > 0.05:
                magnitude = SurpriseMagnitude.moderate
            else:
                magnitude = SurpriseMagnitude.slight

        return SurpriseResult(
            symbol=symbol,
            period_end=period_end,
            eps_surprise_pct=eps_surprise_pct,
            revenue_surprise_pct=revenue_surprise_pct,
            surprise_type=surprise_type,
            magnitude=magnitude,
        )

    def compute_revision_momentum(
        self, symbol: str, lookback_periods: int = 4
    ) -> RevisionMomentum:
        """Compute revision momentum over recent periods."""
        records = self._records.get(symbol, [])
        if not records:
            return RevisionMomentum(symbol=symbol)

        sorted_records = sorted(records, key=lambda r: r.period_end, reverse=True)
        recent = sorted_records[:lookback_periods]

        upward = 0
        downward = 0
        for r in recent:
            if r.previous_estimate is not None and r.estimate_value is not None:
                if r.estimate_value > r.previous_estimate:
                    upward += 1
                elif r.estimate_value < r.previous_estimate:
                    downward += 1

        net = upward - downward
        total = upward + downward
        momentum = net / total if total > 0 else 0.0

        return RevisionMomentum(
            symbol=symbol,
            upward_revisions=upward,
            downward_revisions=downward,
            net_revisions=net,
            momentum_score=momentum,
        )

    def get_consensus(
        self, symbol: str, metric: str, period: date
    ) -> float | None:
        """Get consensus value for a metric and period."""
        records = self.get_estimates(symbol, metric, period)
        if not records:
            return None
        latest = max(records, key=lambda r: r.timestamp)
        return latest.consensus_value

    def detect_estimate_revisions(
        self, symbol: str, metric: str, since_date: date
    ) -> list[EstimateRevision]:
        """Detect estimate revisions since a given date.

        Only considers estimates available on or before the current date
        (i.e., no future-information leakage).
        """
        records = self._records.get(symbol, [])
        metric_records = [
            r
            for r in records
            if r.metric == metric and r.timestamp.date() >= since_date
        ]
        if len(metric_records) < 2:
            return []

        metric_records.sort(key=lambda r: r.timestamp)
        revisions: list[EstimateRevision] = []

        for i in range(1, len(metric_records)):
            prev = metric_records[i - 1]
            curr = metric_records[i]
            if prev.estimate_value is None or curr.estimate_value is None:
                continue
            if prev.estimate_value == 0:
                continue

            revision_pct = (
                (curr.estimate_value - prev.estimate_value) / abs(prev.estimate_value)
            ) * 100

            revisions.append(
                EstimateRevision(
                    symbol=symbol,
                    metric=metric,
                    old_estimate=prev.estimate_value,
                    new_estimate=curr.estimate_value,
                    revision_pct=revision_pct,
                    revision_date=curr.timestamp.date(),
                    analyst_count=curr.revision_count,
                )
            )

        return revisions
