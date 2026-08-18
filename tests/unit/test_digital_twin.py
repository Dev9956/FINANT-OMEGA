"""Tests for Financial Digital Twin."""

import pytest
from core.intelligence.digital_twin.models import TwinScenario, TwinSnapshot
from core.intelligence.digital_twin.engine import DigitalTwinEngine


class TestDigitalTwinEngine:
    def setup_method(self):
        self.engine = DigitalTwinEngine()

    def test_create_twin(self):
        twin = self.engine.create_twin(entity="AAPL", name="Apple")
        assert twin.entity == "AAPL"
        assert twin.name == "Apple"

    def test_get_twin(self):
        twin = self.engine.create_twin(entity="AAPL")
        retrieved = self.engine.get_twin(twin.twin_id)
        assert retrieved is not None

    def test_get_twin_by_entity(self):
        self.engine.create_twin(entity="AAPL")
        self.engine.create_twin(entity="MSFT")
        aapl = self.engine.get_twin_by_entity("AAPL")
        assert aapl is not None
        assert aapl.entity == "AAPL"

    def test_update_snapshot(self):
        twin = self.engine.create_twin(entity="AAPL")
        snapshot = TwinSnapshot(
            financials={"revenue": 100, "net_income": 20},
            market={"price": 150, "pe_ratio": 25},
        )
        assert self.engine.update_snapshot(twin.twin_id, snapshot) is True
        latest = self.engine.get_latest_snapshot(twin.twin_id)
        assert latest.financials["revenue"] == 100

    def test_apply_scenario(self):
        twin = self.engine.create_twin(entity="AAPL")
        self.engine.update_snapshot(twin.twin_id, TwinSnapshot(
            market={"price": 150},
        ))
        scenario = TwinScenario(name="Rate Cut", changes={"price": 10})
        affected = self.engine.apply_scenario(twin.twin_id, scenario)
        assert affected is not None
        assert "price" in affected

    def test_list_twins(self):
        self.engine.create_twin(entity="AAPL")
        self.engine.create_twin(entity="MSFT")
        assert len(self.engine.list_twins()) == 2

    def test_update_nonexistent(self):
        assert self.engine.update_snapshot("nonexistent", TwinSnapshot()) is False

    def test_apply_scenario_nonexistent(self):
        assert self.engine.apply_scenario("nonexistent", TwinScenario(name="Test")) is None
