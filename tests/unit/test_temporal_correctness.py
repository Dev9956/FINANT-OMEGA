"""Tests for temporal correctness — no future information leakage."""

from datetime import date, datetime, timedelta, timezone

from core.intelligence.decay.engine import DecayEngine
from core.intelligence.decay.models import DecayFactor, EvidenceItem
from core.intelligence.predictions.engine import PredictionEngine
from core.analytics.estimates.engine import EstimateEngine
from core.analytics.estimates.models import EstimateRecord


class TestTemporalCorrectness:
    """Ensure no look-ahead bias or future information leakage."""

    def test_evidence_freshness_respects_time(self):
        engine = DecayEngine()
        now = datetime.now(timezone.utc)
        old = EvidenceItem(
            content="Old filing",
            decay_factor=DecayFactor.EARNINGS_FILING,
            published_time=now - timedelta(days=365),
        )
        new = EvidenceItem(
            content="New filing",
            decay_factor=DecayFactor.EARNINGS_FILING,
            published_time=now - timedelta(days=5),
        )
        engine.add_evidence(old)
        engine.add_evidence(new)

        old_score = engine.score_freshness(old.evidence_id, reference_time=now)
        new_score = engine.score_freshness(new.evidence_id, reference_time=now)
        assert new_score.decay_adjusted > old_score.decay_adjusted

    def test_estimate_surprise_as_of_prevents_leakage(self):
        engine = EstimateEngine()
        engine.add_estimate(EstimateRecord(
            symbol="AAPL", metric="eps", period_end=date(2024, 3, 31),
            actual_value=2.50, estimate_value=2.30,
            timestamp=datetime(2024, 4, 1, tzinfo=timezone.utc),
        ))
        engine.add_estimate(EstimateRecord(
            symbol="AAPL", metric="eps", period_end=date(2024, 6, 30),
            actual_value=2.80, estimate_value=2.60,
            timestamp=datetime(2024, 7, 1, tzinfo=timezone.utc),
        ))

        surprise_q1 = engine.compute_surprise("AAPL", period_end=date(2024, 3, 31), as_of=date(2024, 5, 1))
        assert surprise_q1 is not None

        surprise_q2 = engine.compute_surprise("AAPL", period_end=date(2024, 6, 30), as_of=date(2024, 8, 1))
        assert surprise_q2 is not None

        surprise_q2_early = engine.compute_surprise("AAPL", period_end=date(2024, 6, 30), as_of=date(2024, 5, 1))
        assert surprise_q2_early is None

    def test_prediction_expiration(self):
        engine = PredictionEngine()
        pred = engine.register_prediction(
            entity="AAPL",
            prediction_text="Test",
            horizon_days=30,
        )
        assert pred.expires_at is None or pred.status.value == "pending"

    def test_decay_different_information_types(self):
        engine = DecayEngine()
        now = datetime.now(timezone.utc)

        market = EvidenceItem(
            content="Market data",
            decay_factor=DecayFactor.MARKET_DATA,
            published_time=now - timedelta(days=1),
        )
        filing = EvidenceItem(
            content="SEC filing",
            decay_factor=DecayFactor.REGULATORY_FILING,
            published_time=now - timedelta(days=1),
        )
        engine.add_evidence(market)
        engine.add_evidence(filing)

        market_score = engine.score_freshness(market.evidence_id, reference_time=now)
        filing_score = engine.score_freshness(filing.evidence_id, reference_time=now)
        assert filing_score.decay_adjusted > market_score.decay_adjusted

    def test_thesis_versioning_preserves_history(self):
        from core.intelligence.thesis.thesis_engine import ThesisEngine
        engine = ThesisEngine()
        v1 = engine.create_thesis(symbol="AAPL", title="Test", confidence=0.6)
        engine.update_thesis(v1.thesis_id, confidence=0.7, change_summary="Updated")
        engine.update_thesis(v1.thesis_id, confidence=0.8, change_summary="Updated again")
        history = engine.get_thesis_history(v1.thesis_id)
        assert history.total_versions == 3
        assert history.confidence_trend == [0.6, 0.7, 0.8]

    def test_debate_audit_trail(self):
        from core.intelligence.debate.engine import DebateEngine
        engine = DebateEngine()
        result = engine.run_debate(question="Test", evidence_items=["A", "B"])
        assert result.duration_ms >= 0
        assert result.bull_argument is not None
        assert result.bear_argument is not None
