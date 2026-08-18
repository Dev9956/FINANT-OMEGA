"""FININT OMEGA — Change detection API routes."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.change_detection.comparator import PeriodComparator
from core.intelligence.change_detection.detector import ChangeDetector
from core.intelligence.change_detection.models import ChangeType

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/changes", tags=["change-detection"])

_detector = ChangeDetector()
_comparator = PeriodComparator()


class DetectRequest(BaseModel):
    """Request to detect changes between two data snapshots."""

    data_a: dict
    data_b: dict
    change_types: list[ChangeType] | None = Field(
        default=None, description="Types of changes to detect (default: all)"
    )


class ChangeItem(BaseModel):
    """Single change item in response."""

    change_id: str
    change_type: str
    severity: str
    field: str
    old_value: object
    new_value: object
    change_pct: float
    evidence: str
    confidence: float


class DetectResponse(BaseModel):
    """Response from change detection."""

    changes: list[ChangeItem]
    total_changes: int


class CompareRequest(BaseModel):
    """Request to compare two periods."""

    entity: str
    period_a: str
    period_b: str
    data_a: dict
    data_b: dict


class CompareResponse(BaseModel):
    """Response from period comparison."""

    comparison_id: str
    entity_a: str
    entity_b: str
    period_a: str
    period_b: str
    changes: list[ChangeItem]
    overall_significance: float
    summary: str


@router.post("/detect", response_model=DetectResponse)
async def detect_changes(request: DetectRequest):
    """Detect changes between two data snapshots."""
    try:
        change_types = request.change_types or list(ChangeType)
        all_changes = []

        if ChangeType.NUMERICAL in change_types:
            num_a = {k: v for k, v in request.data_a.items() if isinstance(v, (int, float))}
            num_b = {k: v for k, v in request.data_b.items() if isinstance(v, (int, float))}
            all_changes.extend(_detector.detect_numerical_changes(num_a, num_b))

        if ChangeType.TEXTUAL in change_types:
            text_a = request.data_a.get("text", "")
            text_b = request.data_b.get("text", "")
            if isinstance(text_a, str) and isinstance(text_b, str):
                all_changes.extend(_detector.detect_textual_changes(text_a, text_b))

        if ChangeType.STRUCTURAL in change_types:
            all_changes.extend(
                _detector.detect_structural_changes(request.data_a, request.data_b)
            )

        if ChangeType.SENTIMENT in change_types:
            sent_a = request.data_a.get("sentiment", {})
            sent_b = request.data_b.get("sentiment", {})
            if isinstance(sent_a, dict) and isinstance(sent_b, dict):
                all_changes.extend(_detector.detect_sentiment_changes(sent_a, sent_b))

        if ChangeType.GUIDANCE in change_types:
            g_a = request.data_a.get("guidance", {})
            g_b = request.data_b.get("guidance", {})
            if isinstance(g_a, dict) and isinstance(g_b, dict):
                all_changes.extend(_detector.detect_guidance_changes(g_a, g_b))

        if ChangeType.RISK in change_types:
            r_a = request.data_a.get("risks", [])
            r_b = request.data_b.get("risks", [])
            if isinstance(r_a, list) and isinstance(r_b, list):
                all_changes.extend(_detector.detect_risk_changes(r_a, r_b))

        items = [
            ChangeItem(
                change_id=c.change_id,
                change_type=c.change_type.value,
                severity=c.severity.value,
                field=c.field,
                old_value=c.old_value,
                new_value=c.new_value,
                change_pct=c.change_pct,
                evidence=c.evidence,
                confidence=c.confidence,
            )
            for c in all_changes
        ]
        return DetectResponse(changes=items, total_changes=len(items))
    except Exception as e:
        logger.error("detect_changes_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Change detection failed")


@router.post("/compare", response_model=CompareResponse)
async def compare_periods(request: CompareRequest):
    """Compare two periods of data for an entity."""
    try:
        result = _comparator.compare_periods(
            data_a=request.data_a,
            period_a=request.period_a,
            data_b=request.data_b,
            period_b=request.period_b,
            entity=request.entity,
        )
        items = [
            ChangeItem(
                change_id=c.change_id,
                change_type=c.change_type.value,
                severity=c.severity.value,
                field=c.field,
                old_value=c.old_value,
                new_value=c.new_value,
                change_pct=c.change_pct,
                evidence=c.evidence,
                confidence=c.confidence,
            )
            for c in result.changes
        ]
        return CompareResponse(
            comparison_id=result.comparison_id,
            entity_a=result.entity_a,
            entity_b=result.entity_b,
            period_a=result.period_a,
            period_b=result.period_b,
            changes=items,
            overall_significance=result.overall_significance,
            summary=result.summary,
        )
    except Exception as e:
        logger.error("compare_periods_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Period comparison failed")
