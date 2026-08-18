"""FININT OMEGA — Deliverables API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.research.deliverables.generator import DeliverableGenerator
from core.research.deliverables.models import DeliverableType, ResearchDeliverable

router = APIRouter(prefix="/api/v1/deliverables", tags=["deliverables"])

_generator = DeliverableGenerator()
_deliverable_store: dict[str, ResearchDeliverable] = {}


class DeliverableGenerateRequest(BaseModel):
    """Request body for deliverable generation."""

    deliverable_type: DeliverableType
    title: str = ""
    data: dict = Field(default_factory=dict, description="Research data for the deliverable")


class DeliverableGenerateResponse(BaseModel):
    """Response for deliverable generation."""

    deliverable_id: str
    deliverable_type: str
    title: str
    section_count: int


@router.post("/generate", response_model=DeliverableGenerateResponse)
async def generate_deliverable(request: DeliverableGenerateRequest) -> DeliverableGenerateResponse:
    """Generate a research deliverable."""
    if request.title:
        request.data["title"] = request.title
    deliverable = _generator.generate(request.deliverable_type, request.data)
    _deliverable_store[deliverable.deliverable_id] = deliverable
    return DeliverableGenerateResponse(
        deliverable_id=deliverable.deliverable_id,
        deliverable_type=deliverable.deliverable_type.value,
        title=deliverable.title,
        section_count=len(deliverable.sections),
    )


@router.get("/{deliverable_id}")
async def get_deliverable(deliverable_id: str) -> dict:
    """Get a deliverable."""
    if deliverable_id not in _deliverable_store:
        raise HTTPException(status_code=404, detail=f"Deliverable not found: {deliverable_id}")
    return _deliverable_store[deliverable_id].model_dump(mode="json")


@router.get("/{deliverable_id}/render")
async def render_deliverable(
    deliverable_id: str,
    format: str = Query(default="markdown", description="Render format: markdown, text, json, csv"),
) -> dict | str:
    """Render a deliverable in the specified format."""
    if deliverable_id not in _deliverable_store:
        raise HTTPException(status_code=404, detail=f"Deliverable not found: {deliverable_id}")
    deliverable = _deliverable_store[deliverable_id]
    if format == "markdown":
        return {"content": _generator.render_markdown(deliverable)}
    elif format == "text":
        return {"content": _generator.render_text(deliverable)}
    elif format == "json":
        return _generator.render_json(deliverable)
    elif format == "csv":
        return {"content": _generator.render_csv(deliverable)}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format}")
