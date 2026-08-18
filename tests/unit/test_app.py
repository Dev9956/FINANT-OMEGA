"""FININT OMEGA — M0 unit tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "finintel-omega"
        assert data["version"] == "0.1.0"

    def test_root_has_docs_url(self, client):
        response = client.get("/")
        data = response.json()
        assert "docs_url" in data


class TestHealthEndpoint:
    def test_health_returns_200_or_503(self, client):
        """Health endpoint should return 200 or 503 depending on service availability."""
        response = client.get("/api/v1/system/health")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data
        assert isinstance(data["services"], list)

    def test_health_has_request_id(self, client):
        """Response should include X-Request-ID header."""
        response = client.get("/api/v1/system/health")
        assert "X-Request-ID" in response.headers

    def test_health_has_response_time(self, client):
        """Response should include X-Response-Time header."""
        response = client.get("/api/v1/system/health")
        assert "X-Response-Time" in response.headers

    def test_health_services_structure(self, client):
        """Each service in health response should have required fields."""
        response = client.get("/api/v1/system/health")
        data = response.json()
        for service in data["services"]:
            assert "name" in service
            assert "status" in service
            assert service["status"] in ("ok", "degraded", "error")


class TestOpenAPI:
    def test_openapi_schema_available(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "/api/v1/system/health" in schema["paths"]
