# Counterfactual / Scenario Engine

## Overview
Runs counterfactual scenario analysis on financial variables. Models dependency chains between macro/financial variables and computes affected metrics, bull/base/bear outcomes, and risk assessments.

## Architecture
- **ScenarioAnalysisEngine** — creates and evaluates scenarios
- Built-in dependency map: interest_rate → bond_yields, mortgage_rates, equity_valuation, currency
- Variable impact propagation with configurable sensitivity (default 0.5)
- Auto-generated bull/base/bear scenarios (±10% from scenario values)

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/intelligence/scenarios` | Create a scenario |
| GET | `/api/v1/intelligence/scenarios/{scenario_id}` | Get scenario result |
| GET | `/api/v1/intelligence/scenarios` | List all scenarios |

## Data Models
- **ScenarioVariable**: name, current_value, scenario_value, unit, change_pct
- **VariableChange**: original/new values, impacted_metrics, impact_direction (positive/negative/neutral/mixed)
- **ScenarioConfig**: include_dependencies, max_depth, show_assumptions
- **ScenarioResult**: variables, variable_changes, affected_metrics, bull_base_bear, risk_assessment, assumptions

## Design Decisions
- Pre-built dependency graph covers common macro-financial relationships
- Linear sensitivity model (0.5x) for impact propagation — simple but interpretable
- Risk assessment based on maximum variable change magnitude
- Assumptions explicitly listed for transparency

## Known Limitations
- Linear relationships only — no non-linear or threshold effects
- Fixed dependency map — not customizable
- No Monte Carlo simulation
- No portfolio-level scenario aggregation

## Test Coverage
- Tested via `tests/unit/test_scenarios_analysis.py`
- Covers: scenario creation, variable changes, dependency propagation, bull/base/bear generation
