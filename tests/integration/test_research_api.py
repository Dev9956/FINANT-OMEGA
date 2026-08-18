"""FININT OMEGA — Integration tests for Deep Research and Agent API endpoints."""

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
    """Create a test client for the FastAPI app."""
    return TestClient(app, headers=_AUTH_HEADERS)


class TestDeepResearchAPI:
    def test_start_deep_research(self, client):
        response = client.post(
            "/api/v1/research/deep",
            json={
                "question": "Analyze TCS earnings and valuation",
                "depth": "shallow",
                "max_tasks": 2,
                "timeout_seconds": 60,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "research_id" in data
        assert data["question"] == "Analyze TCS earnings and valuation"
        assert data["status"] == "completed"
        assert data["task_count"] > 0

    def test_get_research_status(self, client):
        # First start a research run
        start_resp = client.post(
            "/api/v1/research/deep",
            json={"question": "Analyze RELIANCE", "depth": "shallow", "max_tasks": 1},
        )
        research_id = start_resp.json()["research_id"]

        response = client.get(f"/api/v1/research/{research_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["research_id"] == research_id
        assert data["status"] in ("completed", "failed")

    def test_get_research_status_not_found(self, client):
        response = client.get("/api/v1/research/nonexistent-id")
        assert response.status_code == 404

    def test_get_research_tasks(self, client):
        start_resp = client.post(
            "/api/v1/research/deep",
            json={"question": "Analyze INFY", "depth": "shallow", "max_tasks": 2},
        )
        research_id = start_resp.json()["research_id"]

        response = client.get(f"/api/v1/research/{research_id}/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["research_id"] == research_id
        assert isinstance(data["tasks"], list)
        assert len(data["tasks"]) > 0

    def test_get_research_evidence(self, client):
        start_resp = client.post(
            "/api/v1/research/deep",
            json={"question": "Analyze HDFC", "depth": "shallow", "max_tasks": 1},
        )
        research_id = start_resp.json()["research_id"]

        response = client.get(f"/api/v1/research/{research_id}/evidence")
        assert response.status_code == 200
        data = response.json()
        assert data["research_id"] == research_id
        assert isinstance(data["evidence"], list)
        assert "total_count" in data


class TestAgentsAPI:
    def test_list_agents(self, client):
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert data["total_count"] > 0
        roles = [a["role"] for a in data["agents"]]
        assert "company_analyst" in roles
        assert "earnings_analyst" in roles

    def test_execute_company_analyst(self, client):
        response = client.post(
            "/api/v1/agents/company_analyst/execute",
            json={
                "question": "Analyze TCS fundamentals",
                "context": {"symbol": "TCS", "period": "annual"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "company_analyst"
        assert "TCS" in data["answer"]
        assert data["confidence"] > 0

    def test_execute_earnings_analyst(self, client):
        response = client.post(
            "/api/v1/agents/earnings_analyst/execute",
            json={
                "question": "Analyze RELIANCE earnings",
                "context": {"symbol": "RELIANCE"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "earnings_analyst"
        assert "RELIANCE" in data["answer"]

    def test_execute_nonexistent_agent(self, client):
        response = client.post(
            "/api/v1/agents/nonexistent_agent/execute",
            json={"question": "test"},
        )
        assert response.status_code == 404

    def test_execute_agent_empty_question(self, client):
        response = client.post(
            "/api/v1/agents/company_analyst/execute",
            json={"question": ""},
        )
        assert response.status_code == 500
