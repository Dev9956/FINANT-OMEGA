"""FININT OMEGA — Company monitoring API routes."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.company_monitoring.engine import MonitoringEngine
from core.intelligence.company_monitoring.models import MonitorMetric

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

_engine = MonitoringEngine()


class RegisterRequest(BaseModel):
    """Request to register a company for monitoring."""

    symbol: str
    metrics: list[MonitorMetric]


class UpdateRequest(BaseModel):
    """Request to update a company's state."""

    symbol: str
    data: dict


class AlertResponse(BaseModel):
    """Response for a monitoring alert."""

    alert_id: str
    symbol: str
    metric: str
    materiality: str
    thesis_impact: str
    change_pct: float
    old_value: object
    new_value: object
    created_at: str


class StateResponse(BaseModel):
    """Response for company state."""

    symbol: str
    metrics: dict
    snapshot_version: int
    timestamp: str


@router.post("/companies")
async def register_company(request: RegisterRequest):
    """Register a company for monitoring."""
    try:
        _engine.register_company(symbol=request.symbol, metrics_to_monitor=request.metrics)
        return {"status": "registered", "symbol": request.symbol}
    except Exception as e:
        logger.error("register_company_failed", symbol=request.symbol, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to register {request.symbol}")


@router.delete("/companies/{symbol}")
async def unregister_company(symbol: str):
    """Unregister a company from monitoring."""
    try:
        _engine.unregister_company(symbol)
        return {"status": "unregistered", "symbol": symbol}
    except Exception as e:
        logger.error("unregister_company_failed", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to unregister {symbol}")


@router.post("/update", response_model=list[AlertResponse])
async def update_state(request: UpdateRequest):
    """Update a company's state and return any material alerts."""
    try:
        alerts = _engine.update_state(symbol=request.symbol, new_data=request.data)
        return [
            AlertResponse(
                alert_id=a.alert_id,
                symbol=a.symbol,
                metric=a.metric,
                materiality=a.materiality.value,
                thesis_impact=a.thesis_impact,
                change_pct=a.diff.change_pct,
                old_value=a.diff.old_value,
                new_value=a.diff.new_value,
                created_at=a.created_at.isoformat(),
            )
            for a in alerts
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("update_state_failed", symbol=request.symbol, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update state")


@router.get("/alerts/{symbol}", response_model=list[AlertResponse])
async def get_alerts(symbol: str, since: str | None = None):
    """Get alerts for a monitored company."""
    try:
        since_dt = datetime.fromisoformat(since) if since else None
        alerts = _engine.get_alerts(symbol, since=since_dt)
        return [
            AlertResponse(
                alert_id=a.alert_id,
                symbol=a.symbol,
                metric=a.metric,
                materiality=a.materiality.value,
                thesis_impact=a.thesis_impact,
                change_pct=a.diff.change_pct,
                old_value=a.diff.old_value,
                new_value=a.diff.new_value,
                created_at=a.created_at.isoformat(),
            )
            for a in alerts
        ]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid 'since' datetime format")
    except Exception as e:
        logger.error("get_alerts_failed", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.get("/state/{symbol}", response_model=StateResponse)
async def get_state(symbol: str):
    """Get the current state of a monitored company."""
    try:
        state = _engine.get_state(symbol)
        if state is None:
            raise HTTPException(status_code=404, detail=f"No state found for {symbol}")
        return StateResponse(
            symbol=state.symbol,
            metrics=state.metrics,
            snapshot_version=state.snapshot_version,
            timestamp=state.timestamp.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_state_failed", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get state")
