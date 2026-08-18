"""FININT OMEGA — Counterfactual / Scenario Analysis Engine."""

from __future__ import annotations

from core.intelligence.scenarios.models import (
    ImpactDirection,
    ScenarioConfig,
    ScenarioResult,
    ScenarioVariable,
    VariableChange,
)


class ScenarioAnalysisEngine:
    """Run counterfactual scenario analysis on financial variables."""

    def __init__(self) -> None:
        self._scenarios: dict[str, ScenarioResult] = {}
        self._dependencies: dict[str, list[str]] = {
            "interest_rate": ["bond_yields", "mortgage_rates", "equity_valuation", "currency"],
            "oil_price": ["inflation", "transportation_costs", "energy_sector", "consumer_spending"],
            "gdp_growth": ["earnings_growth", "unemployment", "consumer_spending", "tax_revenue"],
            "inflation": ["interest_rates", "purchasing_power", "wage_growth", "bond_yields"],
            "exchange_rate": ["import_costs", "export_competitiveness", "foreign_revenue", "inflation"],
            "revenue_growth": ["earnings", "cash_flow", "valuation", "hiring"],
        }

    def create_scenario(
        self,
        title: str,
        variables: list[dict],
        description: str = "",
        config: ScenarioConfig | None = None,
    ) -> ScenarioResult:
        cfg = config or ScenarioConfig()
        scenario_vars = []
        changes = []

        for var in variables:
            current = var.get("current_value", 0)
            scenario_val = var.get("scenario_value", 0)
            if current != 0:
                change_pct = ((scenario_val - current) / abs(current)) * 100
            else:
                change_pct = 0.0

            sv = ScenarioVariable(
                name=var.get("name", "unknown"),
                current_value=current,
                scenario_value=scenario_val,
                unit=var.get("unit", ""),
                change_pct=change_pct,
            )
            scenario_vars.append(sv)

            impacted = self._find_impacted_metrics(sv.name) if cfg.include_dependencies else []
            direction = ImpactDirection.POSITIVE if change_pct > 0 else ImpactDirection.NEGATIVE if change_pct < 0 else ImpactDirection.NEUTRAL

            changes.append(VariableChange(
                variable_name=sv.name,
                original_value=current,
                new_value=scenario_val,
                change_pct=change_pct,
                impacted_metrics=impacted,
                impact_direction=direction,
            ))

        affected = self._compute_affected_metrics(scenario_vars)
        bull_base_bear = self._generate_bull_base_bear(scenario_vars, affected)
        assumptions = [f"Linear relationship assumed for {v.name}" for v in scenario_vars]
        risk = self._assess_risk(scenario_vars)

        result = ScenarioResult(
            title=title,
            description=description,
            variables=scenario_vars,
            variable_changes=changes,
            affected_metrics=affected,
            bull_base_bear=bull_base_bear,
            risk_assessment=risk,
            assumptions=assumptions,
            confidence=0.6,
            summary=f"Scenario '{title}' with {len(scenario_vars)} variable changes analyzed.",
        )

        self._scenarios[result.scenario_id] = result
        return result

    def get_scenario(self, scenario_id: str) -> ScenarioResult | None:
        return self._scenarios.get(scenario_id)

    def list_scenarios(self) -> list[ScenarioResult]:
        return list(self._scenarios.values())

    def _find_impacted_metrics(self, variable_name: str) -> list[str]:
        return self._dependencies.get(variable_name, [])

    def _compute_affected_metrics(self, variables: list[ScenarioVariable]) -> dict[str, float]:
        affected = {}
        for var in variables:
            impacted = self._dependencies.get(var.name, [])
            for metric in impacted:
                sensitivity = 0.5
                affected[metric] = var.change_pct * sensitivity
        return affected

    def _generate_bull_base_bear(
        self,
        variables: list[ScenarioVariable],
        affected: dict[str, float],
    ) -> dict[str, dict]:
        base = {v.name: v.current_value for v in variables}
        bull = {v.name: v.scenario_value * 1.1 for v in variables}
        bear = {v.name: v.scenario_value * 0.9 for v in variables}

        return {"bull": bull, "base": base, "bear": bear}

    def _assess_risk(self, variables: list[ScenarioVariable]) -> str:
        max_change = max((abs(v.change_pct) for v in variables), default=0)
        if max_change > 30:
            return "High risk — large variable changes"
        elif max_change > 15:
            return "Moderate risk — significant variable changes"
        return "Low risk — moderate variable changes"
