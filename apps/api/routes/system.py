"""FININT OMEGA — System routes (health, root)."""

import time
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, Request

from apps.api.config import get_settings
from apps.api.schemas import HealthResponse, HealthStatus, RootResponse
from core.auth.dependencies import PUBLIC

router = APIRouter(tags=["system"])
logger = structlog.get_logger()

_start_time = time.monotonic()


@router.get("/", response_model=RootResponse, dependencies=[Depends(PUBLIC)])
async def root() -> RootResponse:
    """Root endpoint with service info."""
    settings = get_settings()
    return RootResponse(
        service="finintel-omega",
        version="0.1.0",
        docs_url="/docs",
    )


@router.get("/api/v1/system/health", response_model=HealthResponse, dependencies=[Depends(PUBLIC)])
async def health(request: Request) -> HealthResponse:
    """Health endpoint verifying all services."""
    request_id = getattr(request.state, "request_id", None)
    services: list[HealthStatus] = []

    # Check PostgreSQL
    pg_status = await _check_postgresql()
    services.append(pg_status)

    # Check ClickHouse
    ch_status = await _check_clickhouse()
    services.append(ch_status)

    # Check Redis
    redis_status = await _check_redis()
    services.append(redis_status)

    # Determine overall status
    statuses = [s.status for s in services]
    if all(s == "ok" for s in statuses):
        overall = "ok"
    elif any(s == "error" for s in statuses):
        overall = "error"
    else:
        overall = "degraded"

    uptime = time.monotonic() - _start_time

    logger.info(
        "health_check",
        overall_status=overall,
        request_id=request_id,
        postgresql=pg_status.status,
        clickhouse=ch_status.status,
        redis=redis_status.status,
    )

    return HealthResponse(
        status=overall,
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=uptime,
        services=services,
    )


async def _check_postgresql() -> HealthStatus:
    """Check PostgreSQL connectivity."""
    settings = get_settings()
    start = time.monotonic()
    try:
        import asyncpg

        conn = await asyncpg.connect(settings.postgres_dsn)
        await conn.fetchval("SELECT 1")
        await conn.close()
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(name="postgresql", status="ok", latency_ms=round(latency, 2))
    except ImportError:
        return HealthStatus(name="postgresql", status="error", message="asyncpg not installed")
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            name="postgresql", status="error", latency_ms=round(latency, 2), message=str(e)
        )


async def _check_clickhouse() -> HealthStatus:
    """Check ClickHouse connectivity."""
    settings = get_settings()
    start = time.monotonic()
    try:
        import clickhouse_connect

        client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
        client.query("SELECT 1")
        client.close()
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(name="clickhouse", status="ok", latency_ms=round(latency, 2))
    except ImportError:
        return HealthStatus(name="clickhouse", status="error", message="clickhouse-connect not installed")
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            name="clickhouse", status="error", latency_ms=round(latency, 2), message=str(e)
        )


async def _check_redis() -> HealthStatus:
    """Check Redis connectivity."""
    settings = get_settings()
    start = time.monotonic()
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(name="redis", status="ok", latency_ms=round(latency, 2))
    except ImportError:
        return HealthStatus(name="redis", status="error", message="redis not installed")
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            name="redis", status="error", latency_ms=round(latency, 2), message=str(e)
        )
