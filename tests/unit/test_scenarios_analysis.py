"""Tests for Counterfactual / Scenario Analysis Engine."""

import pytest
from core.intelligence.scenarios.models import ImpactDirection
from core.intelligence.scenarios.engine import ScenarioAnalysisEngine


class TestScenarioAnalysisEngine:
    def setup_method(self):
        self.engine = ScenarioAnalysisEngine()

    def test_create_scenario(self):
        result = self.engine.create_scenario(
            title="Rate Cut Scenario",
            variables=[
                {"name": "interest_rate", "current_value": 6.5, "scenario_value": 5.5},
            ],
        )
        assert result.title == "Rate Cut Scenario"
        assert len(result.variables) == 1
        assert result.variables[0].change_pct < 0

    def test_scenario_with_multiple_variables(self):
        result = self.engine.create_scenario(
            title="Oil Shock",
            variables=[
                {"name": "oil_price", "current_value": 80, "scenario_value": 120},
                {"name": "interest_rate", "current_value": 6.5, "scenario_value": 7.5},
            ],
        )
        assert len(result.variables) == 2
        assert len(result.variable_changes) == 2

    def test_dependencies_computed(self):
        result = self.engine.create_scenario(
            title="Rate Cut",
            variables=[
                {"name": "interest_rate", "current_value": 6.5, "scenario_value": 5.5},
            ],
        )
        assert len(result.affected_metrics) > 0

    def test_bull_base_bear_generated(self):
        result = self.engine.create_scenario(
            title="Test",
            variables=[
                {"name": "revenue_growth", "current_value": 10, "scenario_value": 15},
            ],
        )
        assert "bull" in result.bull_base_bear
        assert "base" in result.bull_base_bear
        assert "bear" in result.bull_base_bear

    def test_risk_assessment(self):
        result = self.engine.create_scenario(
            title="Big Move",
            variables=[
                {"name": "oil_price", "current_value": 80, "scenario_value": 150},
            ],
        )
        assert result.risk_assessment != ""

    def test_assumptions(self):
        result = self.engine.create_scenario(
            title="Test",
            variables=[
                {"name": "gdp_growth", "current_value": 2.5, "scenario_value": 1.0},
            ],
        )
        assert len(result.assumptions) > 0

    def test_get_scenario(self):
        result = self.engine.create_scenario(
            title="Test",
            variables=[{"name": "x", "current_value": 1, "scenario_value": 2}],
        )
        retrieved = self.engine.get_scenario(result.scenario_id)
        assert retrieved is not None

    def test_get_scenario_not_found(self):
        assert self.engine.get_scenario("nonexistent") is None

    def test_list_scenarios(self):
        self.engine.create_scenario(title="S1", variables=[{"name": "x", "current_value": 1, "scenario_value": 2}])
        self.engine.create_scenario(title="S2", variables=[{"name": "y", "current_value": 5, "scenario_value": 3}])
        assert len(self.engine.list_scenarios()) == 2

    def test_change_pct_computed(self):
        result = self.engine.create_scenario(
            title="Test",
            variables=[{"name": "x", "current_value": 100, "scenario_value": 120}],
        )
        assert abs(result.variables[0].change_pct - 20.0) < 0.01
