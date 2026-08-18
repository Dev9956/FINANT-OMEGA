"""FININT OMEGA — Grid API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.research.grid.generator import GridGenerator
from core.research.grid.models import GridSpec, GeneratedGrid
from core.research.grid.planner import GridPlanner

router = APIRouter(prefix="/api/v1/grid", tags=["grid"])

_planner = GridPlanner()
_generator = GridGenerator()
_grid_store: dict[str, GeneratedGrid] = {}


class GridGenerateRequest(BaseModel):
    """Request body for grid generation."""

    query: str = Field(description="Natural language request for the grid")
    data: dict | None = Field(default=None, description="Optional data source")


class GridGenerateResponse(BaseModel):
    """Response for grid generation."""

    grid_id: str
    title: str
    row_count: int
    column_count: int
    cell_count: int


@router.post("/generate", response_model=GridGenerateResponse)
async def generate_grid(request: GridGenerateRequest) -> GridGenerateResponse:
    """Generate a research grid from a natural language request."""
    spec = _planner.plan_grid(request.query)
    grid = _generator.generate(spec, request.data)
    _grid_store[grid.grid_id] = grid
    return GridGenerateResponse(
        grid_id=grid.grid_id,
        title=spec.title,
        row_count=len(spec.rows),
        column_count=len(spec.columns),
        cell_count=len(grid.cells),
    )


@router.get("/{grid_id}")
async def get_grid(grid_id: str) -> dict:
    """Get a generated grid."""
    if grid_id not in _grid_store:
        raise HTTPException(status_code=404, detail=f"Grid not found: {grid_id}")
    return _grid_store[grid_id].model_dump(mode="json")
