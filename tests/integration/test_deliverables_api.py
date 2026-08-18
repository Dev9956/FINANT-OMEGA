"""Integration tests for the Deliverables API."""

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


class TestDeliverablesAPI:
    """Tests for deliverables API endpoints."""

    def test_generate_research_memo(self) -> None:
        response = client.post(
            "/api/v1/deliverables/generate",
            json={
                "deliverable_type": "research_memo",
                "title": "Test Memo",
                "data": {"thesis": "Buy AAPL", "metrics": {"roe": 18.5}},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deliverable_type"] == "research_memo"
        assert data["title"] == "Test Memo"

    def test_generate_company_report(self) -> None:
        response = client.post(
            "/api/v1/deliverables/generate",
            json={
                "deliverable_type": "company_report",
                "data": {"symbol": "AAPL", "overview": "Apple Inc."},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deliverable_type"] == "company_report"

    def test_get_deliverable(self) -> None:
        gen_response = client.post(
            "/api/v1/deliverables/generate",
            json={
                "deliverable_type": "executive_summary",
                "data": {"summary": "Key findings"},
            },
        )
        deliverable_id = gen_response.json()["deliverable_id"]
        response = client.get(f"/api/v1/deliverables/{deliverable_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["deliverable_id"] == deliverable_id

    def test_get_deliverable_not_found(self) -> None:
        response = client.get("/api/v1/deliverables/nonexistent")
        assert response.status_code == 404

    def test_render_markdown(self) -> None:
        gen_response = client.post(
            "/api/v1/deliverables/generate",
            json={
                "deliverable_type": "research_memo",
                "data": {"title": "Memo", "thesis": "Buy"},
            },
        )
        deliverable_id = gen_response.json()["deliverable_id"]
        response = client.get(
            f"/api/v1/deliverables/{deliverable_id}/render",
            params={"format": "markdown"},
        )
        assert response.status_code == 200
        content = response.json()["content"]
        assert "# Memo" in content

    def test_render_json(self) -> None:
        gen_response = client.post(
            "/api/v1/deliverables/generate",
            json={
                "deliverable_type": "research_memo",
                "data": {"title": "Memo"},
            },
        )
        deliverable_id = gen_response.json()["deliverable_id"]
        response = client.get(
            f"/api/v1/deliverables/{deliverable_id}/render",
            params={"format": "json"},
        )
        assert response.status_code == 200

    def test_render_csv(self) -> None:
        gen_response = client.post(
            "/api/v1/deliverables/generate",
            json={
                "deliverable_type": "research_memo",
                "data": {"title": "Memo"},
            },
        )
        deliverable_id = gen_response.json()["deliverable_id"]
        response = client.get(
            f"/api/v1/deliverables/{deliverable_id}/render",
            params={"format": "csv"},
        )
        assert response.status_code == 200
        content = response.json()["content"]
        assert "section_id" in content

    def test_render_invalid_format(self) -> None:
        gen_response = client.post(
            "/api/v1/deliverables/generate",
            json={
                "deliverable_type": "research_memo",
                "data": {"title": "Memo"},
            },
        )
        deliverable_id = gen_response.json()["deliverable_id"]
        response = client.get(
            f"/api/v1/deliverables/{deliverable_id}/render",
            params={"format": "invalid"},
        )
        assert response.status_code == 400
