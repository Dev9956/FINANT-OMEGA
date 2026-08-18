"""FININT OMEGA — M2 integration tests for market/fundamentals API."""

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


class TestMarketPricesAPI:
    def test_get_prices(self, client):
        response = client.get("/api/v1/market/TCS/prices?days=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        assert data[0]["symbol"] == "TCS"


class TestMarketAnalyticsAPI:
    def test_compute_analytics(self, client):
        response = client.post(
            "/api/v1/market/TCS/analytics",
            json={"symbol": "TCS"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TCS"
        assert data["data_points"] > 0
        assert data["cagr"] is not None
        assert data["volatility"] is not None


class TestMarketIndicatorsAPI:
    def test_get_indicators(self, client):
        response = client.get("/api/v1/market/TCS/indicators")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TCS"
        assert "sma" in data
        assert "ema" in data
        assert "rsi" in data


class TestFundamentalsAPI:
    def test_get_fundamentals(self, client):
        response = client.get("/api/v1/fundamentals/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_ratios(self, client):
        response = client.get("/api/v1/fundamentals/RELIANCE/ratios")
        assert response.status_code == 200
        data = response.json()
        assert "pe_ratio" in data


class TestScreeningAPI:
    def test_screen_stocks(self, client):
        response = client.post(
            "/api/v1/screening/query",
            json={
                "filters": [{"field": "pe_ratio", "operator": "<", "value": 20}],
                "candidates": [
                    {"symbol": "A", "pe_ratio": 15},
                    {"symbol": "B", "pe_ratio": 25},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "A"


class TestEarningsAPI:
    def test_earnings_analysis(self, client):
        response = client.get("/api/v1/earnings/TCS/analysis")
        assert response.status_code == 200
        data = response.json()
        assert "surprise" in data
        assert "momentum" in data
