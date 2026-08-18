"""FININT OMEGA — FastAPI application."""

import time
import uuid

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.config import get_settings
from apps.api.logging_config import configure_logging
from apps.api.routes.audit import router as audit_router
from apps.api.routes.auth import router as auth_router
from apps.api.routes.integrations import router as integrations_router
from apps.api.routes.portfolio import router as portfolio_router
from apps.api.routes.change_detection import router as change_detection_router
from apps.api.routes.research import router as research_router
from apps.api.routes.corporate_actions import router as corporate_actions_router
from apps.api.routes.data import router as data_router
from apps.api.routes.deliverables import router as deliverables_router
from apps.api.routes.estimates import router as estimates_router
from apps.api.routes.grid import router as grid_router
from apps.api.routes.ma import router as ma_router
from apps.api.routes.market_fundamentals import router as market_router
from apps.api.routes.monitoring import router as monitoring_router
from apps.api.routes.private_rag import router as private_rag_router
from apps.api.routes.scheduled import router as scheduled_router
from apps.api.routes.system import router as system_router
from apps.api.routes.watchlist import router as watchlist_router
from apps.api.routes.thesis import router as thesis_router
from apps.api.routes.contradiction import router as contradiction_router
from apps.api.routes.narrative import router as narrative_router
from apps.api.routes.evidence_graph import router as evidence_graph_router
from apps.api.routes.debate import router as debate_router
from apps.api.routes.causal import router as causal_router
from apps.api.routes.regime import router as regime_router
from apps.api.routes.scenarios_analysis import router as scenarios_analysis_router
from apps.api.routes.early_warning import router as early_warning_router
from apps.api.routes.anomaly import router as anomaly_router
from apps.api.routes.decay import router as decay_router
from apps.api.routes.research_loop import router as research_loop_router
from apps.api.routes.cross_entity import router as cross_entity_router
from apps.api.routes.predictions import router as predictions_router
from apps.api.routes.digital_twin import router as digital_twin_router
from apps.api.routes.quality import router as quality_router
from apps.api.routes.memo import router as memo_router
from core.auth.dependencies import get_current_user
from core.persistence.db import init_db, close_db

logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.app_log_level)

    app = FastAPI(
        title="FININT OMEGA",
        description="Financial Intelligence & Quantitative Research Engine",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Store settings on app
    app.state.settings = settings

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware: request ID + timing
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.monotonic()
        response = await call_next(request)
        elapsed = time.monotonic() - start

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed:.4f}s"

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_s=round(elapsed, 4),
        )
        return response

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": str(exc),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # Register routes
    # system_router + auth_router: PUBLIC (no auth dependency)
    app.include_router(system_router)
    app.include_router(auth_router)
    # All other routers: AUTHENTICATED (require valid JWT)
    _auth = [Depends(get_current_user)]
    app.include_router(data_router, dependencies=_auth)
    app.include_router(market_router, dependencies=_auth)
    app.include_router(audit_router, dependencies=_auth)
    app.include_router(estimates_router, dependencies=_auth)
    app.include_router(corporate_actions_router, dependencies=_auth)
    app.include_router(ma_router, dependencies=_auth)
    app.include_router(private_rag_router, dependencies=_auth)
    app.include_router(monitoring_router, dependencies=_auth)
    app.include_router(change_detection_router, dependencies=_auth)
    app.include_router(research_router, dependencies=_auth)
    app.include_router(grid_router, dependencies=_auth)
    app.include_router(deliverables_router, dependencies=_auth)
    app.include_router(scheduled_router, dependencies=_auth)
    app.include_router(watchlist_router, dependencies=_auth)
    app.include_router(thesis_router, dependencies=_auth)
    app.include_router(contradiction_router, dependencies=_auth)
    app.include_router(narrative_router, dependencies=_auth)
    app.include_router(evidence_graph_router, dependencies=_auth)
    app.include_router(debate_router, dependencies=_auth)
    app.include_router(causal_router, dependencies=_auth)
    app.include_router(regime_router, dependencies=_auth)
    app.include_router(scenarios_analysis_router, dependencies=_auth)
    app.include_router(early_warning_router, dependencies=_auth)
    app.include_router(anomaly_router, dependencies=_auth)
    app.include_router(decay_router, dependencies=_auth)
    app.include_router(research_loop_router, dependencies=_auth)
    app.include_router(cross_entity_router, dependencies=_auth)
    app.include_router(predictions_router, dependencies=_auth)
    app.include_router(digital_twin_router, dependencies=_auth)
    app.include_router(quality_router, dependencies=_auth)
    app.include_router(memo_router, dependencies=_auth)
    app.include_router(integrations_router, dependencies=_auth)
    app.include_router(portfolio_router, dependencies=_auth)

    @app.on_event("startup")
    async def startup():
        await init_db()
        logger.info("app_started", port=settings.api_port)

    @app.on_event("shutdown")
    async def shutdown():
        await close_db()
        logger.info("app_shutdown")

    return app


app = create_app()
