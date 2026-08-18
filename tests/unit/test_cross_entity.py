"""Tests for Cross-Entity Intelligence."""

import pytest
from core.intelligence.cross_entity.models import (
    CrossEntityRequest,
    EntityMetrics,
    RankingCriterion,
)
from core.intelligence.cross_entity.engine import CrossEntityEngine


class TestCrossEntityEngine:
    def setup_method(self):
        self.engine = CrossEntityEngine()

    def test_register_entity(self):
        entity = EntityMetrics(
            entity_id="1", symbol="AAPL", metrics={"pe_ratio": 25, "fcf_yield": 5},
        )
        eid = self.engine.register_entity(entity)
        assert eid == "1"

    def test_analyze_composite(self):
        self.engine.register_entity(EntityMetrics(
            entity_id="1", symbol="AAPL",
            metrics={"earnings_growth": 15, "fcf_yield": 5, "pe_ratio": 25},
        ))
        self.engine.register_entity(EntityMetrics(
            entity_id="2", symbol="MSFT",
            metrics={"earnings_growth": 10, "fcf_yield": 4, "pe_ratio": 30},
        ))
        request = CrossEntityRequest(symbols=["AAPL", "MSFT"])
        result = self.engine.analyze(request)
        assert result.entities_analyzed == 2
        assert len(result.rankings) > 0

    def test_ranking_by_earnings_momentum(self):
        self.engine.register_entity(EntityMetrics(
            entity_id="1", symbol="AAPL", metrics={"earnings_growth": 20},
        ))
        self.engine.register_entity(EntityMetrics(
            entity_id="2", symbol="MSFT", metrics={"earnings_growth": 10},
        ))
        request = CrossEntityRequest(
            symbols=["AAPL", "MSFT"],
            criteria=[RankingCriterion.EARNINGS_MOMENTUM],
        )
        result = self.engine.analyze(request)
        rankings = result.rankings[0].rankings
        assert rankings[0].symbol == "AAPL"

    def test_find_weakening_thesis(self):
        self.engine.register_entity(EntityMetrics(
            entity_id="1", symbol="AAPL", thesis_health="weakening",
        ))
        self.engine.register_entity(EntityMetrics(
            entity_id="2", symbol="MSFT", thesis_health="strengthening",
        ))
        weakening = self.engine.find_weakening_thesis()
        assert len(weakening) == 1
        assert weakening[0].symbol == "AAPL"

    def test_find_strong_cashflow_low_valuation(self):
        self.engine.register_entity(EntityMetrics(
            entity_id="1", symbol="AAPL", metrics={"fcf_yield": 8, "pe_ratio": 12},
        ))
        self.engine.register_entity(EntityMetrics(
            entity_id="2", symbol="MSFT", metrics={"fcf_yield": 3, "pe_ratio": 30},
        ))
        results = self.engine.find_strong_cashflow_low_valuation()
        assert len(results) == 1

    def test_get_result(self):
        self.engine.register_entity(EntityMetrics(entity_id="1", symbol="AAPL"))
        request = CrossEntityRequest(symbols=["AAPL"])
        result = self.engine.analyze(request)
        retrieved = self.engine.get_result(result.result_id)
        assert retrieved is not None

    def test_summary(self):
        self.engine.register_entity(EntityMetrics(
            entity_id="1", symbol="AAPL", metrics={"earnings_growth": 15, "fcf_yield": 5, "pe_ratio": 25},
        ))
        request = CrossEntityRequest(symbols=["AAPL"])
        result = self.engine.analyze(request)
        assert result.summary != ""
