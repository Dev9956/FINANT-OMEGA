"""FININT OMEGA — Unit tests for estimate revisions module."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from core.analytics.estimates.engine import EstimateEngine
from core.analytics.estimates.models import (
    EstimateRecord,
    EstimateRevision,
    RevisionMomentum,
    SurpriseResult,
)


class TestEstimateRecordModels:
    """Tests for estimate Pydantic models."""

    def test_estimate_record_creation(self) -> None:
        record = EstimateRecord(
            symbol="AAPL",
            metric="eps",
            period_end=date(2025, 3, 31),
            actual_value=1.50,
            estimate_value=1.40,
            consensus_value=1.42,
            source="analyst1",
        )
        assert record.symbol == "AAPL"
        assert record.estimate_id  # auto-generated

    def test_surprise_result_defaults(self) -> None:
        result = SurpriseResult(
            symbol="AAPL",
            period_end=date(2025, 3, 31),
        )
        assert result.surprise_type.value == "inline"
        assert result.magnitude.value == "slight"


class TestEstimateEngine:
    """Tests for EstimateEngine."""

    def test_add_and_get_estimate(self) -> None:
        engine = EstimateEngine()
        record = EstimateRecord(
            symbol="AAPL",
            metric="eps",
            period_end=date(2025, 3, 31),
            estimate_value=1.40,
            actual_value=1.50,
        )
        engine.add_estimate(record)
        results = engine.get_estimates("AAPL", "eps", date(2025, 3, 31))
        assert len(results) == 1
        assert results[0].actual_value == 1.50

    def test_get_estimates_by_metric_only(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.40,
            )
        )
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="revenue",
                period_end=date(2025, 3, 31),
                estimate_value=100000,
            )
        )
        eps_only = engine.get_estimates("AAPL", metric="eps")
        assert len(eps_only) == 1
        assert eps_only[0].metric == "eps"

    def test_compute_surprise_beat(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.40,
                actual_value=1.50,
            )
        )
        result = engine.compute_surprise("AAPL", date(2025, 3, 31))
        assert result is not None
        assert result.surprise_type.value == "beat"
        assert result.eps_surprise_pct is not None
        assert result.eps_surprise_pct > 0

    def test_compute_surprise_miss(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.40,
                actual_value=1.20,
            )
        )
        result = engine.compute_surprise("AAPL", date(2025, 3, 31))
        assert result is not None
        assert result.surprise_type.value == "miss"

    def test_compute_surprise_inline(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.40,
                actual_value=1.41,
            )
        )
        result = engine.compute_surprise("AAPL", date(2025, 3, 31))
        assert result is not None
        assert result.surprise_type.value == "inline"

    def test_compute_surprise_magnitude(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.00,
                actual_value=1.20,
            )
        )
        result = engine.compute_surprise("AAPL", date(2025, 3, 31))
        assert result is not None
        assert result.magnitude.value == "significant"

    def test_compute_surprise_no_data(self) -> None:
        engine = EstimateEngine()
        assert engine.compute_surprise("AAPL", date(2025, 3, 31)) is None

    def test_revision_momentum_upward(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.50,
                previous_estimate=1.40,
            )
        )
        momentum = engine.compute_revision_momentum("AAPL")
        assert momentum.upward_revisions == 1
        assert momentum.downward_revisions == 0
        assert momentum.momentum_score > 0

    def test_revision_momentum_downward(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.30,
                previous_estimate=1.40,
            )
        )
        momentum = engine.compute_revision_momentum("AAPL")
        assert momentum.upward_revisions == 0
        assert momentum.downward_revisions == 1
        assert momentum.momentum_score < 0

    def test_revision_momentum_empty(self) -> None:
        engine = EstimateEngine()
        momentum = engine.compute_revision_momentum("AAPL")
        assert momentum.upward_revisions == 0
        assert momentum.downward_revisions == 0
        assert momentum.momentum_score == 0.0

    def test_get_consensus(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                consensus_value=1.45,
            )
        )
        consensus = engine.get_consensus("AAPL", "eps", date(2025, 3, 31))
        assert consensus == 1.45

    def test_get_consensus_missing(self) -> None:
        engine = EstimateEngine()
        assert engine.get_consensus("AAPL", "eps", date(2025, 3, 31)) is None

    def test_detect_revisions(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.30,
                timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )
        )
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.50,
                timestamp=datetime(2025, 2, 1, tzinfo=timezone.utc),
            )
        )
        revisions = engine.detect_estimate_revisions(
            "AAPL", "eps", date(2025, 1, 1)
        )
        assert len(revisions) == 1
        assert revisions[0].old_estimate == 1.30
        assert revisions[0].new_estimate == 1.50
        assert revisions[0].revision_pct > 0


class TestTemporalLeakagePrevention:
    """Tests that estimates prevent future-information leakage."""

    def test_surprise_as_of_filter(self) -> None:
        engine = EstimateEngine()
        # Estimate created AFTER the period ended
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.40,
                actual_value=1.50,
                timestamp=datetime(2025, 4, 15, tzinfo=timezone.utc),
            )
        )
        # Query as-of March 15 (before the estimate was available)
        result = engine.compute_surprise(
            "AAPL", date(2025, 3, 31), as_of=date(2025, 3, 15)
        )
        assert result is None

    def test_surprise_as_of_includes_available(self) -> None:
        engine = EstimateEngine()
        engine.add_estimate(
            EstimateRecord(
                symbol="AAPL",
                metric="eps",
                period_end=date(2025, 3, 31),
                estimate_value=1.40,
                actual_value=1.50,
                timestamp=datetime(2025, 3, 10, tzinfo=timezone.utc),
            )
        )
        result = engine.compute_surprise(
            "AAPL", date(2025, 3, 31), as_of=date(2025, 3, 15)
        )
        assert result is not None
        assert result.eps_surprise_pct is not None


from datetime import datetime, timezone
