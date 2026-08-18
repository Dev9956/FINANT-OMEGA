"""FININT OMEGA — M0 unit tests for API schemas."""

from datetime import datetime, timezone

from apps.api.schemas import ErrorResponse, HealthResponse, HealthStatus, RootResponse


class TestHealthStatus:
    def test_ok_status(self):
        status = HealthStatus(name="postgresql", status="ok", latency_ms=1.5)
        assert status.name == "postgresql"
        assert status.status == "ok"
        assert status.latency_ms == 1.5
        assert status.message is None

    def test_error_status_with_message(self):
        status = HealthStatus(name="redis", status="error", message="connection refused")
        assert status.status == "error"
        assert status.message == "connection refused"


class TestHealthResponse:
    def test_health_response(self):
        services = [HealthStatus(name="pg", status="ok")]
        resp = HealthResponse(
            status="ok",
            version="0.1.0",
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=100.0,
            services=services,
        )
        assert resp.status == "ok"
        assert len(resp.services) == 1


class TestRootResponse:
    def test_root_response(self):
        resp = RootResponse(service="finintel-omega", version="0.1.0", docs_url="/docs")
        assert resp.service == "finintel-omega"


class TestErrorResponse:
    def test_error_response(self):
        resp = ErrorResponse(error="not_found", detail="Resource not found")
        assert resp.error == "not_found"
