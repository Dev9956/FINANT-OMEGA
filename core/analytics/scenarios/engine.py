"""FININT OMEGA — Scenario engine: market shocks, rate shocks, FX shocks."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ShockType(str, Enum):
    MARKET = "market"
    RATE = "rate"
    FX = "fx"
    SECTOR = "sector"
    CUSTOM = "custom"


class Shock(BaseModel):
    """Definition of a single shock to apply."""

    shock_type: ShockType
    target: str = ""
    magnitude: float = 0.0
    description: str = ""


class ScenarioResult(BaseModel):
    """Result of running a scenario."""

    scenario_name: str
    shocks_applied: list[Shock] = Field(default_factory=list)
    portfolio_impact: float = 0.0
    position_impacts: dict[str, float] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class ScenarioEngine:
    """Run market, rate, FX, and custom scenarios against portfolio positions."""

    def __init__(self) -> None:
        self._scenarios: dict[str, list[Shock]] = {}

    def define_scenario(self, name: str, shocks: list[Shock]) -> None:
        self._scenarios[name] = list(shocks)

    def list_scenarios(self) -> list[str]:
        return list(self._scenarios.keys())

    def _apply_market_shock(self, positions: list[dict], shock: Shock) -> dict[str, float]:
        impacts: dict[str, float] = {}
        for pos in positions:
            symbol = pos.get("symbol", "")
            market_value = pos.get("market_value", 0.0)
            beta = pos.get("beta", 1.0)
            impacts[symbol] = -market_value * shock.magnitude * beta
        return impacts

    def _apply_rate_shock(self, positions: list[dict], shock: Shock) -> dict[str, float]:
        impacts: dict[str, float] = {}
        for pos in positions:
            symbol = pos.get("symbol", "")
            market_value = pos.get("market_value", 0.0)
            duration = pos.get("duration", 0.0)
            impacts[symbol] = -market_value * duration * shock.magnitude
        return impacts

    def _apply_fx_shock(self, positions: list[dict], shock: Shock) -> dict[str, float]:
        impacts: dict[str, float] = {}
        for pos in positions:
            symbol = pos.get("symbol", "")
            market_value = pos.get("market_value", 0.0)
            fx_exposure = pos.get("fx_exposure", 0.0)
            impacts[symbol] = -market_value * fx_exposure * shock.magnitude
        return impacts

    def run_scenario(self, name: str, positions: list[dict]) -> ScenarioResult:
        shocks = self._scenarios.get(name, [])
        all_impacts: dict[str, float] = {}
        for shock in shocks:
            if shock.shock_type == ShockType.MARKET:
                imp = self._apply_market_shock(positions, shock)
            elif shock.shock_type == ShockType.RATE:
                imp = self._apply_rate_shock(positions, shock)
            elif shock.shock_type == ShockType.FX:
                imp = self._apply_fx_shock(positions, shock)
            else:
                imp = {}
            for sym, val in imp.items():
                all_impacts[sym] = all_impacts.get(sym, 0.0) + val

        return ScenarioResult(
            scenario_name=name,
            shocks_applied=shocks,
            portfolio_impact=sum(all_impacts.values()),
            position_impacts=all_impacts,
        )

    def run_custom(self, shocks: list[Shock], positions: list[dict]) -> ScenarioResult:
        tmp_name = "_custom_run"
        self._scenarios[tmp_name] = shocks
        result = self.run_scenario(tmp_name, positions)
        del self._scenarios[tmp_name]
        return result
