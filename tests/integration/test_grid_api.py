"""Integration tests for the Grid API."""

from __future__ import annotations

import os
os.environ["APP_SECRET_KEY"] = "test-secret-key-for-auth-integration"
from core.auth.security import create_access_token

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

_test_token = create_access_token("test-user", "admin", org_id="test-org")
_AUTH_HEADERS = {"Authorization": f"Bearer {_test_token}"}

client = TestClient(app, headers=_AUTH_HEADERS)


class TestGridAPI:
    """Tests for grid API endpoints."""

    def test_generate_grid(self) -> None:
        response = client.post(
            "/api/v1/grid/generate",
            json={"query": "Compare AAPL MSFT on ROE and PE ratio"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "grid_id" in data
        assert data["row_count"] == 2
        assert data["column_count"] >= 2

    def test_generate_grid_sector(self) -> None:
        response = client.post(
            "/api/v1/grid/generate",
            json={"query": "Show me finance sector metrics"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 7

    def test_get_grid(self) -> None:
        gen_response = client.post(
            "/api/v1/grid/generate",
            json={"query": "AAPL MSFT ROE"},
        )
        grid_id = gen_response.json()["grid_id"]
        response = client.get(f"/api/v1/grid/{grid_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["grid_id"] == grid_id
        assert "cells" in data

    def test_get_grid_not_found(self) -> None:
        response = client.get("/api/v1/grid/nonexistent")
        assert response.status_code == 404

    def test_generate_grid_with_data(self) -> None:
        response = client.post(
            "/api/v1/grid/generate",
            json={
                "query": "AAPL ROE",
                "data": {"AAPL": {"roe": 18.5}},
            },
        )
        assert response.status_code == 200
