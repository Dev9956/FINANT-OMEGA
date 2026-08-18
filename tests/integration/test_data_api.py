"""FININT OMEGA — M1 integration tests for data API."""

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


class TestDataSourcesAPI:
    def test_list_sources_empty(self, client):
        response = client.get("/api/v1/data/sources")
        assert response.status_code == 200
        assert response.json() == []

    def test_register_source(self, client):
        source = {
            "source_id": "test_source",
            "source_name": "Test Source",
            "source_type": "market_data",
            "provider": "Test Provider",
        }
        response = client.post("/api/v1/data/sources", json=source)
        assert response.status_code == 200
        data = response.json()
        assert data["source_id"] == "test_source"

    def test_get_source(self, client):
        # Register first
        source = {
            "source_id": "test_get",
            "source_name": "Test Get",
            "source_type": "fundamentals",
            "provider": "Test",
        }
        client.post("/api/v1/data/sources", json=source)
        response = client.get("/api/v1/data/sources/test_get")
        assert response.status_code == 200

    def test_get_source_not_found(self, client):
        response = client.get("/api/v1/data/sources/nonexistent")
        assert response.status_code == 404


class TestDatasetsAPI:
    def test_list_datasets_empty(self, client):
        response = client.get("/api/v1/data/datasets")
        assert response.status_code == 200
        assert response.json() == []

    def test_register_dataset(self, client):
        dataset = {
            "source_id": "test",
            "name": "Test Dataset",
            "stage": "raw",
        }
        response = client.post("/api/v1/data/datasets", json=dataset)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Dataset"


class TestMockDataAPI:
    def test_mock_market(self, client):
        response = client.get("/api/v1/data/mock/market?symbol=TCS")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 30
        assert data[0]["symbol"] == "TCS"

    def test_mock_fundamentals(self, client):
        response = client.get("/api/v1/data/mock/fundamentals?symbol=RELIANCE")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_mock_macro(self, client):
        response = client.get("/api/v1/data/mock/macro")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_mock_unknown(self, client):
        response = client.get("/api/v1/data/mock/unknown")
        assert response.status_code == 400


class TestPipelinesAPI:
    def test_list_pipelines(self, client):
        response = client.get("/api/v1/data/pipelines")
        assert response.status_code == 200
        pipelines = response.json()
        assert "market_ohlcv" in pipelines


class TestHealthEndpoint:
    def test_health_still_works(self, client):
        response = client.get("/api/v1/system/health")
        assert response.status_code in (200, 503)
