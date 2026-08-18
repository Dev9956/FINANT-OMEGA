"""FININT OMEGA — Shared fixtures for integration tests."""

import os

import pytest
from fastapi.testclient import TestClient

# Set test secret key so JWT tokens are valid
os.environ["APP_SECRET_KEY"] = "test-secret-key-for-auth-integration"

from apps.api.main import app
from core.auth.security import create_access_token

TEST_TOKEN = create_access_token("test-user", "admin", org_id="test-org")
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


@pytest.fixture
def client():
    """Create a test client with valid auth headers."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """Provide valid auth headers."""
    return AUTH_HEADERS
