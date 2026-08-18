"""FININT OMEGA — Digital Twin API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.digital_twin.engine import DigitalTwinEngine
from core.intelligence.digital_twin.models import TwinScenario, TwinSnapshot

router = APIRouter(prefix="/api/v1/intelligence/digital-twin", tags=["digital-twin"])

_engine: DigitalTwinEngine | None = None


def _get_engine() -> DigitalTwinEngine:
    global _engine
    if _engine is None:
        _engine = DigitalTwinEngine()
    return _engine


class CreateTwinRequest(BaseModel):
    entity: str
    name: str = ""


class UpdateSnapshotRequest(BaseModel):
    financials: dict[str, float] = Field(default_factory=dict)
    market: dict[str, float] = Field(default_factory=dict)
    valuation: dict[str, float] = Field(default_factory=dict)
    risk: dict[str, float] = Field(default_factory=dict)


class ApplyScenarioRequest(BaseModel):
    name: str
    changes: dict[str, float]
    assumptions: list[str] = Field(default_factory=list)


@router.post("")
def create_twin(req: CreateTwinRequest):
    engine = _get_engine()
    twin = engine.create_twin(entity=req.entity, name=req.name)
    return {"twin_id": twin.twin_id, "entity": twin.entity}


@router.get("/{twin_id}")
def get_twin(twin_id: str):
    engine = _get_engine()
    twin = engine.get_twin(twin_id)
    if twin is None:
        raise HTTPException(status_code=404, detail="Twin not found")
    return twin


@router.post("/{twin_id}/snapshot")
def update_snapshot(twin_id: str, req: UpdateSnapshotRequest):
    engine = _get_engine()
    snapshot = TwinSnapshot(
        financials=req.financials,
        market=req.market,
        valuation=req.valuation,
        risk=req.risk,
    )
    if not engine.update_snapshot(twin_id, snapshot):
        raise HTTPException(status_code=404, detail="Twin not found")
    return {"snapshot_id": snapshot.snapshot_id, "status": "added"}


@router.post("/{twin_id}/scenario")
def apply_scenario(twin_id: str, req: ApplyScenarioRequest):
    engine = _get_engine()
    scenario = TwinScenario(name=req.name, changes=req.changes, assumptions=req.assumptions)
    affected = engine.apply_scenario(twin_id, scenario)
    if affected is None:
        raise HTTPException(status_code=404, detail="Twin not found")
    return {"scenario_id": scenario.scenario_id, "affected_metrics": affected}


@router.get("")
def list_twins():
    engine = _get_engine()
    return {"twins": engine.list_twins(), "count": len(engine.list_twins())}
