"""FININT OMEGA — Integration tests for monitoring API."""

import os
os.environ["APP_SECRET_KEY"] = "test-secret-key-for-auth-integration"
from core.auth.security import create_access_token

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

_test_token = create_access_token("test-user", "admin", org_id="test-org")
_AUTH_HEADERS = {"Authorization": f"Bearer {_test_token}"}


@pytest.fixture
def client():
    return TestClient(app, headers=_AUTH_HEADERS)


class TestMonitoringRegistration:
    """Test company registration for monitoring."""

    def test_register_company(self, client):
        response = client.post(
            "/api/v1/monitoring/companies",
            json={"symbol": "TCS", "metrics": ["price", "earnings"]},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "registered"

    def test_unregister_company(self, client):
        client.post(
            "/api/v1/monitoring/companies",
            json={"symbol": "TCS", "metrics": ["price"]},
        )
        response = client.delete("/api/v1/monitoring/companies/TCS")
        assert response.status_code == 200
        assert response.json()["status"] == "unregistered"


class TestStateUpdates:
    """Test state update and alert generation."""

    def test_update_state_first_time(self, client):
        client.post(
            "/api/v1/monitoring/companies",
            json={"symbol": "TCS", "metrics": ["price"]},
        )
        response = client.post(
            "/api/v1/monitoring/update",
            json={"symbol": "TCS", "data": {"price": 100}},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_update_state_generates_alert(self, client):
        client.post(
            "/api/v1/monitoring/companies",
            json={"symbol": "TCS", "metrics": ["price"]},
        )
        client.post(
            "/api/v1/monitoring/update",
            json={"symbol": "TCS", "data": {"price": 100}},
        )
        response = client.post(
            "/api/v1/monitoring/update",
            json={"symbol": "TCS", "data": {"price": 125}},
        )
        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) >= 1
        assert alerts[0]["materiality"] == "critical"

    def test_update_unregistered_company(self, client):
        response = client.post(
            "/api/v1/monitoring/update",
            json={"symbol": "UNKNOWN", "data": {"price": 100}},
        )
        assert response.status_code == 400


class TestAlertRetrieval:
    """Test alert retrieval."""

    def test_get_alerts(self, client):
        client.post(
            "/api/v1/monitoring/companies",
            json={"symbol": "TCS", "metrics": ["price"]},
        )
        client.post(
            "/api/v1/monitoring/update",
            json={"symbol": "TCS", "data": {"price": 100}},
        )
        client.post(
            "/api/v1/monitoring/update",
            json={"symbol": "TCS", "data": {"price": 120}},
        )
        response = client.get("/api/v1/monitoring/alerts/TCS")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_state(self, client):
        client.post(
            "/api/v1/monitoring/companies",
            json={"symbol": "TCS", "metrics": ["price"]},
        )
        client.post(
            "/api/v1/monitoring/update",
            json={"symbol": "TCS", "data": {"price": 100}},
        )
        response = client.get("/api/v1/monitoring/state/TCS")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TCS"
        assert data["metrics"]["price"] == 100

    def test_get_state_not_found(self, client):
        response = client.get("/api/v1/monitoring/state/NONEXISTENT")
        assert response.status_code == 404
