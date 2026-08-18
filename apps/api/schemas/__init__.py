"""FININT OMEGA — API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Status of a single service."""

    name: str
    status: str = Field(description="ok, degraded, or error")
    latency_ms: float | None = Field(default=None, description="Response time in milliseconds")
    message: str | None = None


class HealthResponse(BaseModel):
    """Response schema for health endpoint."""

    status: str = Field(description="Overall status: ok, degraded, or error")
    version: str
    timestamp: datetime
    uptime_seconds: float
    services: list[HealthStatus]


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    request_id: str | None = None


class RootResponse(BaseModel):
    """Root endpoint response."""

    service: str
    version: str
    docs_url: str
