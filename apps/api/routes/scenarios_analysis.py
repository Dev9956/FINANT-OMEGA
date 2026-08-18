"""FININT OMEGA — Scenario Analysis API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.scenarios.engine import ScenarioAnalysisEngine

router = APIRouter(prefix="/api/v1/intelligence/scenarios", tags=["scenarios"])

_engine: ScenarioAnalysisEngine | None = None


def _get_engine() -> ScenarioAnalysisEngine:
    global _engine
    if _engine is None:
        _engine = ScenarioAnalysisEngine()
    return _engine


class ScenarioVariableRequest(BaseModel):
    name: str
    current_value: float
    scenario_value: float
    unit: str = ""


class CreateScenarioRequest(BaseModel):
    title: str
    description: str = ""
    variables: list[ScenarioVariableRequest]


@router.post("")
def create_scenario(req: CreateScenarioRequest):
    engine = _get_engine()
    variables = [v.model_dump() for v in req.variables]
    result = engine.create_scenario(
        title=req.title,
        variables=variables,
        description=req.description,
    )
    return result


@router.get("/{scenario_id}")
def get_scenario(scenario_id: str):
    engine = _get_engine()
    scenario = engine.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.get("")
def list_scenarios():
    engine = _get_engine()
    return {"scenarios": engine.list_scenarios()}
