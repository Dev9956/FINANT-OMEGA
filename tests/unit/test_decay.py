"""Tests for Information Decay Engine."""

import pytest
from datetime import datetime, timedelta, timezone

from core.intelligence.decay.models import DecayFactor, EvidenceItem
from core.intelligence.decay.engine import DecayEngine


class TestDecayEngine:
    def setup_method(self):
        self.engine = DecayEngine()

    def test_add_evidence(self):
        e = EvidenceItem(content="Test", decay_factor=DecayFactor.NEWS_ARTICLE)
        eid = self.engine.add_evidence(e)
        assert eid == e.evidence_id

    def test_score_freshness_recent(self):
        e = EvidenceItem(
            content="Recent",
            decay_factor=DecayFactor.NEWS_ARTICLE,
            published_time=datetime.now(timezone.utc),
            source_quality=1.0,
        )
        self.engine.add_evidence(e)
        score = self.engine.score_freshness(e.evidence_id)
        assert score.decay_adjusted > 0.9

    def test_score_freshness_old(self):
        e = EvidenceItem(
            content="Old",
            decay_factor=DecayFactor.NEWS_ARTICLE,
            published_time=datetime.now(timezone.utc) - timedelta(days=60),
            source_quality=1.0,
        )
        self.engine.add_evidence(e)
        score = self.engine.score_freshness(e.evidence_id)
        assert score.decay_adjusted < 0.1

    def test_confirmation_boost(self):
        e = EvidenceItem(
            content="Confirmed",
            decay_factor=DecayFactor.NEWS_ARTICLE,
            published_time=datetime.now(timezone.utc) - timedelta(days=30),
            confirmed=True,
            source_quality=1.0,
        )
        self.engine.add_evidence(e)
        score = self.engine.score_freshness(e.evidence_id)
        assert score.confirmation_boost > 0

    def test_different_decay_factors(self):
        news = EvidenceItem(content="News", decay_factor=DecayFactor.NEWS_ARTICLE,
                           published_time=datetime.now(timezone.utc) - timedelta(days=7))
        filing = EvidenceItem(content="Filing", decay_factor=DecayFactor.EARNINGS_FILING,
                             published_time=datetime.now(timezone.utc) - timedelta(days=7))
        self.engine.add_evidence(news)
        self.engine.add_evidence(filing)

        news_score = self.engine.score_freshness(news.evidence_id)
        filing_score = self.engine.score_freshness(filing.evidence_id)
        assert filing_score.decay_adjusted > news_score.decay_adjusted

    def test_get_weighted_evidence(self):
        e1 = EvidenceItem(content="Fresh", decay_factor=DecayFactor.MARKET_DATA,
                         published_time=datetime.now(timezone.utc), confidence=0.9)
        e2 = EvidenceItem(content="Old", decay_factor=DecayFactor.NEWS_ARTICLE,
                         published_time=datetime.now(timezone.utc) - timedelta(days=60), confidence=0.9)
        self.engine.add_evidence(e1)
        self.engine.add_evidence(e2)

        weighted = self.engine.get_weighted_evidence()
        assert weighted[0]["content"] == "Fresh"

    def test_confirm_evidence(self):
        e = EvidenceItem(content="Test", decay_factor=DecayFactor.NEWS_ARTICLE)
        self.engine.add_evidence(e)
        assert self.engine.confirm_evidence(e.evidence_id) is True
        assert self.engine.get_evidence(e.evidence_id).confirmed is True

    def test_confirm_nonexistent(self):
        assert self.engine.confirm_evidence("nonexistent") is False
