"""FININT OMEGA — Unit tests for company monitoring."""

import pytest

from core.intelligence.company_monitoring.engine import MonitoringEngine
from core.intelligence.company_monitoring.models import (
    CompanyState,
    MaterialityLevel,
    MonitoringAlert,
    MonitorMetric,
    StateDiff,
)
from core.intelligence.company_monitoring.monitor import CompanyMonitor


class TestCompanyMonitor:
    """Test snapshot, diff, materiality scoring, thesis impact."""

    def setup_method(self):
        self.monitor = CompanyMonitor()

    def test_snapshot(self):
        state = self.monitor.snapshot("TCS", {"price": 100, "pe": 25})
        assert state.symbol == "TCS"
        assert state.metrics["price"] == 100

    def test_diff_detection(self):
        s1 = self.monitor.snapshot("TCS", {"price": 100, "pe": 25})
        s2 = self.monitor.snapshot("TCS", {"price": 110, "pe": 25})
        diffs = self.monitor.diff(s1, s2)
        price_diffs = [d for d in diffs if d.metric == "price"]
        assert len(price_diffs) == 1
        assert price_diffs[0].change_pct == pytest.approx(10.0)

    def test_diff_no_change(self):
        s1 = self.monitor.snapshot("TCS", {"price": 100})
        s2 = self.monitor.snapshot("TCS", {"price": 100})
        diffs = self.monitor.diff(s1, s2)
        assert len(diffs) == 0

    def test_diff_new_field(self):
        s1 = self.monitor.snapshot("TCS", {"price": 100})
        s2 = self.monitor.snapshot("TCS", {"price": 100, "pe": 25})
        diffs = self.monitor.diff(s1, s2)
        pe_diffs = [d for d in diffs if d.metric == "pe"]
        assert len(pe_diffs) == 1

    def test_materiality_scoring_normal(self):
        diff = StateDiff(symbol="TCS", metric="price", old_value=100, new_value=102, change_pct=2.0)
        score = self.monitor.score_materiality(diff)
        assert score == 0.0

    def test_materiality_scoring_notable(self):
        diff = StateDiff(symbol="TCS", metric="price", old_value=100, new_value=106, change_pct=6.0)
        score = self.monitor.score_materiality(diff)
        assert score == 0.5

    def test_materiality_scoring_significant(self):
        diff = StateDiff(symbol="TCS", metric="price", old_value=100, new_value=112, change_pct=12.0)
        score = self.monitor.score_materiality(diff)
        assert score == 0.75

    def test_materiality_scoring_critical(self):
        diff = StateDiff(symbol="TCS", metric="price", old_value=100, new_value=125, change_pct=25.0)
        score = self.monitor.score_materiality(diff)
        assert score == 1.0

    def test_thesis_impact_supports(self):
        diffs = [
            StateDiff(symbol="TCS", metric="revenue", old_value=100, new_value=120, change_pct=20.0, is_material=True),
            StateDiff(symbol="TCS", metric="margin", old_value=30, new_value=35, change_pct=16.7, is_material=True),
        ]
        impact = self.monitor.evaluate_thesis_impact(diffs, "bullish")
        assert impact == "supports"

    def test_thesis_impact_weakens(self):
        diffs = [
            StateDiff(symbol="TCS", metric="revenue", old_value=100, new_value=80, change_pct=-20.0, is_material=True),
        ]
        impact = self.monitor.evaluate_thesis_impact(diffs, "bullish")
        assert impact == "weakens"

    def test_thesis_impact_neutral(self):
        impact = self.monitor.evaluate_thesis_impact([], "bullish")
        assert impact == "neutral"

    def test_should_alert(self):
        diff = StateDiff(symbol="TCS", metric="price", old_value=100, new_value=110, change_pct=10.0)
        assert self.monitor.should_alert(diff, MaterialityLevel.SIGNIFICANT) is True
        assert self.monitor.should_alert(diff, MaterialityLevel.NORMAL) is False


class TestMonitoringEngine:
    """Test registration, state updates, alert generation."""

    def setup_method(self):
        self.engine = MonitoringEngine()

    def test_register_company(self):
        self.engine.register_company("TCS", [MonitorMetric.PRICE])
        state = self.engine.get_state("TCS")
        assert state is None

    def test_unregister_company(self):
        self.engine.register_company("TCS", [MonitorMetric.PRICE])
        self.engine.update_state("TCS", {"price": 100})
        self.engine.unregister_company("TCS")
        assert self.engine.get_state("TCS") is None

    def test_update_state_first_time(self):
        self.engine.register_company("TCS", [MonitorMetric.PRICE])
        alerts = self.engine.update_state("TCS", {"price": 100})
        assert alerts == []
        state = self.engine.get_state("TCS")
        assert state is not None
        assert state.metrics["price"] == 100

    def test_update_state_generates_alert(self):
        self.engine.register_company("TCS", [MonitorMetric.PRICE])
        self.engine.update_state("TCS", {"price": 100})
        alerts = self.engine.update_state("TCS", {"price": 125})
        assert len(alerts) >= 1
        assert alerts[0].materiality == MaterialityLevel.CRITICAL

    def test_get_alerts(self):
        self.engine.register_company("TCS", [MonitorMetric.PRICE])
        self.engine.update_state("TCS", {"price": 100})
        self.engine.update_state("TCS", {"price": 120})
        alerts = self.engine.get_alerts("TCS")
        assert len(alerts) >= 1

    def test_unregistered_company_raises(self):
        with pytest.raises(ValueError, match="not registered"):
            self.engine.update_state("UNKNOWN", {"price": 100})

    def test_get_state(self):
        self.engine.register_company("TCS", [MonitorMetric.PRICE])
        self.engine.update_state("TCS", {"price": 100})
        state = self.engine.get_state("TCS")
        assert state is not None
        assert state.symbol == "TCS"
