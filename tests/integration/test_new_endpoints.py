"""FININT OMEGA — Integration tests for new API endpoints."""

from __future__ import annotations

import os
os.environ["APP_SECRET_KEY"] = "test-secret-key-for-auth-integration"
from core.auth.security import create_access_token

from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routes.audit import get_store as get_audit_store
from apps.api.routes.corporate_actions import get_engine as get_ca_engine
from apps.api.routes.estimates import get_engine as get_est_engine
from apps.api.routes.ma import get_engine as get_ma_engine

_test_token = create_access_token("test-user", "admin", org_id="test-org")
_AUTH_HEADERS = {"Authorization": f"Bearer {_test_token}"}


@pytest.fixture(autouse=True)
def reset_stores() -> None:
    """Reset all stores before each test."""
    from core.evidence.audit.store import AuditTrailStore
    from core.analytics.estimates.engine import EstimateEngine
    from core.analytics.corporate_actions.engine import CorporateActionsEngine
    from core.analytics.ma_intelligence.engine import MAIntelligenceEngine

    import apps.api.routes.audit as audit_module
    import apps.api.routes.estimates as estimates_module
    import apps.api.routes.corporate_actions as ca_module
    import apps.api.routes.ma as ma_module

    audit_module._store = AuditTrailStore()
    estimates_module._engine = EstimateEngine()
    ca_module._engine = CorporateActionsEngine()
    ma_module._engine = MAIntelligenceEngine()
    yield


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    from apps.api.main import create_app
    app = create_app()
    return TestClient(app, headers=_AUTH_HEADERS)


class TestAuditAPI:
    """Integration tests for audit trail API endpoints."""

    def test_get_audit_trail_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/audit/nonexistent")
        assert response.status_code == 404

    def test_get_events(self, client: TestClient) -> None:
        response = client.get("/api/v1/audit/r1/events")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_tool_calls(self, client: TestClient) -> None:
        response = client.get("/api/v1/audit/r1/tool-calls")
        assert response.status_code == 200
        assert response.json() == []

    def test_export_trail_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/audit/nonexistent/export")
        assert response.status_code == 404


class TestEstimatesAPI:
    """Integration tests for estimates API endpoints."""

    def test_add_estimate(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/estimates",
            json={
                "symbol": "AAPL",
                "metric": "eps",
                "period_end": "2025-03-31",
                "estimate_value": 1.40,
                "actual_value": 1.50,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "estimate_id" in data
        assert data["status"] == "created"

    def test_get_estimates(self, client: TestClient) -> None:
        client.post(
            "/api/v1/estimates",
            json={
                "symbol": "AAPL",
                "metric": "eps",
                "period_end": "2025-03-31",
                "estimate_value": 1.40,
            },
        )
        response = client.get("/api/v1/estimates/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"

    def test_compute_surprise(self, client: TestClient) -> None:
        client.post(
            "/api/v1/estimates",
            json={
                "symbol": "AAPL",
                "metric": "eps",
                "period_end": "2025-03-31",
                "estimate_value": 1.40,
                "actual_value": 1.50,
            },
        )
        response = client.get(
            "/api/v1/estimates/AAPL/surprise",
            params={"period_end": "2025-03-31"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["surprise_type"] == "beat"

    def test_compute_surprise_not_found(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/estimates/AAPL/surprise",
            params={"period_end": "2025-03-31"},
        )
        assert response.status_code == 404

    def test_get_revisions(self, client: TestClient) -> None:
        response = client.get("/api/v1/estimates/AAPL/revisions")
        assert response.status_code == 200
        data = response.json()
        assert data["upward_revisions"] == 0


class TestCorporateActionsAPI:
    """Integration tests for corporate actions API endpoints."""

    def test_add_corporate_action(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/corporate-actions",
            json={
                "symbol": "AAPL",
                "action_type": "split",
                "ex_date": "2025-06-01",
                "ratio": 4.0,
                "description": "4-for-1 split",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "action_id" in data

    def test_get_actions(self, client: TestClient) -> None:
        client.post(
            "/api/v1/corporate-actions",
            json={
                "symbol": "AAPL",
                "action_type": "split",
                "ex_date": "2025-06-01",
                "ratio": 4.0,
            },
        )
        response = client.get("/api/v1/corporate-actions/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_adjust_prices(self, client: TestClient) -> None:
        client.post(
            "/api/v1/corporate-actions",
            json={
                "symbol": "AAPL",
                "action_type": "split",
                "ex_date": "2025-06-01",
                "ratio": 4.0,
            },
        )
        response = client.post(
            "/api/v1/corporate-actions/adjust",
            json={
                "symbol": "AAPL",
                "prices": [
                    {"date": "2025-05-30", "close": 200.0, "symbol": "AAPL"},
                    {"date": "2025-06-02", "close": 50.0, "symbol": "AAPL"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["adjusted_prices"]) == 2

    def test_adjust_prices_no_actions(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/corporate-actions/adjust",
            json={
                "symbol": "AAPL",
                "prices": [{"date": "2025-06-02", "close": 50.0, "symbol": "AAPL"}],
            },
        )
        assert response.status_code == 404


class TestMAAPI:
    """Integration tests for M&A intelligence API endpoints."""

    def test_add_transaction(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/ma/transactions",
            json={
                "transaction_type": "acquisition",
                "acquirer_symbol": "MSFT",
                "target_symbol": "ATVI",
                "deal_value": 69000000000,
                "deal_date": "2023-10-13",
                "status": "completed",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "transaction_id" in data

    def test_get_transactions(self, client: TestClient) -> None:
        client.post(
            "/api/v1/ma/transactions",
            json={
                "transaction_type": "acquisition",
                "acquirer_symbol": "MSFT",
                "target_symbol": "ATVI",
                "deal_value": 69000000000,
                "deal_date": "2023-10-13",
            },
        )
        response = client.get("/api/v1/ma/transactions/ATVI")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_active_deals(self, client: TestClient) -> None:
        client.post(
            "/api/v1/ma/transactions",
            json={
                "transaction_type": "acquisition",
                "acquirer_symbol": "A",
                "target_symbol": "B",
                "deal_date": "2025-01-01",
                "status": "announced",
            },
        )
        response = client.get("/api/v1/ma/active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_sector_transactions(self, client: TestClient) -> None:
        client.post(
            "/api/v1/ma/transactions",
            json={
                "transaction_type": "acquisition",
                "acquirer_symbol": "MSFT",
                "target_symbol": "ATVI",
                "deal_date": "2023-10-13",
                "metadata": {"sector": "technology"},
            },
        )
        response = client.get("/api/v1/ma/sector/technology")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["acquirer_symbol"] == "MSFT"

    def test_get_sector_transactions_empty(self, client: TestClient) -> None:
        response = client.get("/api/v1/ma/sector/healthcare")
        assert response.status_code == 200
        assert response.json() == []
