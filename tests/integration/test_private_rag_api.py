"""FININT OMEGA — Integration tests for Private RAG API."""

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


class TestDocumentCRUDAPI:
    """Test document CRUD operations via API."""

    def test_upload_document(self, client):
        response = client.post(
            "/api/v1/private/documents",
            json={"title": "Test Doc", "content": "Hello world"},
            headers={"X-User-Id": "test_user"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Doc"
        assert data["owner_id"] == "test_user"
        assert data["content_hash"]

    def test_list_documents(self, client):
        client.post(
            "/api/v1/private/documents",
            json={"title": "Doc1", "content": "Content1"},
            headers={"X-User-Id": "list_user"},
        )
        client.post(
            "/api/v1/private/documents",
            json={"title": "Doc2", "content": "Content2"},
            headers={"X-User-Id": "list_user"},
        )
        response = client.get(
            "/api/v1/private/documents",
            headers={"X-User-Id": "list_user"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_document(self, client):
        resp = client.post(
            "/api/v1/private/documents",
            json={"title": "Get Me", "content": "content"},
            headers={"X-User-Id": "get_user"},
        )
        doc_id = resp.json()["doc_id"]
        response = client.get(
            f"/api/v1/private/documents/{doc_id}",
            headers={"X-User-Id": "get_user"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Get Me"

    def test_get_document_not_found(self, client):
        response = client.get(
            "/api/v1/private/documents/nonexistent",
            headers={"X-User-Id": "user"},
        )
        assert response.status_code == 404

    def test_delete_document(self, client):
        resp = client.post(
            "/api/v1/private/documents",
            json={"title": "Delete Me", "content": "x"},
            headers={"X-User-Id": "del_user"},
        )
        doc_id = resp.json()["doc_id"]
        response = client.delete(
            f"/api/v1/private/documents/{doc_id}",
            headers={"X-User-Id": "del_user"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_wrong_owner(self, client):
        resp = client.post(
            "/api/v1/private/documents",
            json={"title": "Owner1", "content": "x"},
            headers={"X-User-Id": "owner1"},
        )
        doc_id = resp.json()["doc_id"]
        response = client.delete(
            f"/api/v1/private/documents/{doc_id}",
            headers={"X-User-Id": "owner2"},
        )
        assert response.status_code == 404


class TestSearchAPI:
    """Test search API."""

    def test_search(self, client):
        client.post(
            "/api/v1/private/documents",
            json={"title": "Finance", "content": "revenue growth report"},
            headers={"X-User-Id": "search_user"},
        )
        response = client.post(
            "/api/v1/private/search",
            json={"query": "finance"},
            headers={"X-User-Id": "search_user"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestTenantIsolationAPI:
    """Test tenant isolation via API."""

    def test_users_cannot_see_each_others_documents(self, client):
        client.post(
            "/api/v1/private/documents",
            json={"title": "User1 Doc", "content": "secret1"},
            headers={"X-User-Id": "iso_user1"},
        )
        client.post(
            "/api/v1/private/documents",
            json={"title": "User2 Doc", "content": "secret2"},
            headers={"X-User-Id": "iso_user2"},
        )
        resp1 = client.get(
            "/api/v1/private/documents",
            headers={"X-User-Id": "iso_user1"},
        )
        resp2 = client.get(
            "/api/v1/private/documents",
            headers={"X-User-Id": "iso_user2"},
        )
        assert len(resp1.json()) == 1
        assert len(resp2.json()) == 1
        assert resp1.json()[0]["title"] == "User1 Doc"
        assert resp2.json()[0]["title"] == "User2 Doc"

    def test_search_isolation(self, client):
        client.post(
            "/api/v1/private/documents",
            json={"title": "Confidential A", "content": "data A"},
            headers={"X-User-Id": "s_user1"},
        )
        client.post(
            "/api/v1/private/documents",
            json={"title": "Confidential B", "content": "data B"},
            headers={"X-User-Id": "s_user2"},
        )
        resp = client.post(
            "/api/v1/private/search",
            json={"query": "confidential"},
            headers={"X-User-Id": "s_user1"},
        )
        assert len(resp.json()) == 1
