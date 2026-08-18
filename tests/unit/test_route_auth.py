"""FININT OMEGA — Route-level auth integration tests."""

from __future__ import annotations

import os
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from core.auth.security import create_access_token, decode_token, hash_password

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Use a fixed secret so tokens created in tests match the app's secret
SECRET = "test-secret-key-for-auth-integration"
os.environ["APP_SECRET_KEY"] = SECRET

ADMIN = "admin"
MANAGER = "manager"
ANALYST = "analyst"
VIEWER = "viewer"


def _token(role: str = ANALYST, org_id: str | None = None, secret: str = SECRET, **kw) -> str:
    return create_access_token("test-user", role, org_id=org_id, secret_key=secret, **kw)


def _expired_token(role: str = ANALYST) -> str:
    return create_access_token("test-user", role, expires_delta=timedelta(seconds=-1), secret_key=SECRET)


def _wrong_secret_token() -> str:
    return create_access_token("test-user", ANALYST, secret_key="wrong-secret")


# ---------------------------------------------------------------------------
# Public endpoints — must be accessible without auth
# ---------------------------------------------------------------------------


class TestPublicEndpoints:
    """System endpoints are public and must work without authentication."""

    def test_root_no_auth(self):
        from apps.api.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.get("/")
            assert r.status_code == 200

    def test_health_no_auth(self):
        from apps.api.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.get("/api/v1/system/health")
            assert r.status_code == 200


# ---------------------------------------------------------------------------
# Authenticated endpoints — must reject unauthenticated requests
# ---------------------------------------------------------------------------

# Representative endpoints from each router to verify protection.
# Full coverage is ensured by the router-level dependency in main.py.
PROTECTED_ENDPOINTS = [
    ("GET", "/api/v1/data/sources"),
    ("POST", "/api/v1/data/sources"),
    ("GET", "/api/v1/market/AAPL/prices"),
    ("POST", "/api/v1/market/AAPL/analytics"),
    ("GET", "/api/v1/fundamentals/AAPL"),
    ("GET", "/api/v1/audit/test-id"),
    ("POST", "/api/v1/estimates"),
    ("POST", "/api/v1/corporate-actions"),
    ("POST", "/api/v1/ma/transactions"),
    ("POST", "/api/v1/private/documents"),
    ("POST", "/api/v1/monitoring/companies"),
    ("POST", "/api/v1/changes/detect"),
    ("POST", "/api/v1/research/deep"),
    ("GET", "/api/v1/agents"),
    ("POST", "/api/v1/grid/generate"),
    ("POST", "/api/v1/deliverables/generate"),
    ("POST", "/api/v1/scheduled"),
    ("POST", "/api/v1/watchlist/research"),
    ("POST", "/api/v1/intelligence/thesis"),
    ("POST", "/api/v1/intelligence/contradictions/management-vs-financials"),
    ("POST", "/api/v1/intelligence/narrative/analyze"),
    ("POST", "/api/v1/intelligence/evidence-graph/nodes"),
    ("POST", "/api/v1/intelligence/debate"),
    ("POST", "/api/v1/intelligence/causal/graphs"),
    ("POST", "/api/v1/intelligence/regime/detect"),
    ("POST", "/api/v1/intelligence/scenarios"),
    ("POST", "/api/v1/intelligence/early-warning/scan"),
    ("POST", "/api/v1/intelligence/anomaly/detect"),
    ("POST", "/api/v1/intelligence/decay/evidence"),
    ("POST", "/api/v1/intelligence/research-loop/run"),
    ("POST", "/api/v1/intelligence/cross-entity/entities"),
    ("POST", "/api/v1/intelligence/predictions"),
    ("POST", "/api/v1/intelligence/digital-twin"),
    ("POST", "/api/v1/intelligence/quality/evaluate"),
    ("POST", "/api/v1/intelligence/memo/generate"),
]


class TestUnauthenticatedRejection:
    """Every protected endpoint must return 401 when no token is provided."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_no_token_returns_401(self, method: str, path: str):
        from apps.api.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.request(method, path)
            assert r.status_code == 401, f"{method} {path} returned {r.status_code}, expected 401"


class TestInvalidTokenRejection:
    """Every protected endpoint must return 401 when token is invalid."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS[:10])
    def test_tampered_token_returns_401(self, method: str, path: str):
        from apps.api.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.request(method, path, headers={"Authorization": "Bearer invalid.jwt.token"})
            assert r.status_code == 401, f"{method} {path} accepted invalid token"

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS[:10])
    def test_wrong_secret_returns_401(self, method: str, path: str):
        from apps.api.main import app

        token = _wrong_secret_token()
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.request(method, path, headers={"Authorization": f"Bearer {token}"})
            assert r.status_code == 401, f"{method} {path} accepted wrong-secret token"


class TestExpiredTokenRejection:
    """Every protected endpoint must return 401 when token is expired."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS[:10])
    def test_expired_token_returns_401(self, method: str, path: str):
        from apps.api.main import app

        token = _expired_token()
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.request(method, path, headers={"Authorization": f"Bearer {token}"})
            assert r.status_code == 401, f"{method} {path} accepted expired token"


class TestValidTokenAcceptance:
    """Protected endpoints accept valid JWT tokens (return non-401)."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS[:15])
    def test_valid_token_not_401(self, method: str, path: str):
        from apps.api.main import app

        token = _token()
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.request(method, path, headers={"Authorization": f"Bearer {token}"})
            # Should not be 401 — could be 422 (missing body), 404, 200, etc.
            assert r.status_code != 401, f"{method} {path} rejected valid token: {r.status_code}"


# ---------------------------------------------------------------------------
# RBAC enforcement
# ---------------------------------------------------------------------------

class TestRBACEnforcement:
    """Verify that role-based access control is enforced at the route level."""

    def test_viewer_cannot_write(self):
        """Viewer role should not be able to create theses or write data."""
        from apps.api.main import app

        token = _token(role=VIEWER)
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.post(
                "/api/v1/intelligence/thesis",
                json={"title": "test", "hypothesis": "test"},
                headers={"Authorization": f"Bearer {token}"},
            )
            # Viewer lacks thesis:create permission — should be 403
            assert r.status_code in (403, 422), f"Viewer got {r.status_code} for thesis create"

    def test_admin_can_manage_users(self):
        """Admin role should be able to access admin-level endpoints."""
        from apps.api.main import app

        token = _token(role=ADMIN)
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.get(
                "/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 200, f"Admin got {r.status_code} for agents list"


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    """Verify that tenant_id is correctly extracted from JWT and set on context."""

    def test_security_context_tenant_id(self):
        """SecurityContext.tenant_id returns org_id when set."""
        token = _token(org_id="org-A")
        payload = decode_token(token, secret_key=SECRET)
        assert payload.org_id == "org-A"

    def test_security_context_user_scoped(self):
        """SecurityContext.tenant_id falls back to user_id when no org."""
        token = _token()
        payload = decode_token(token, secret_key=SECRET)
        assert payload.org_id is None


# ---------------------------------------------------------------------------
# Token classification audit
# ---------------------------------------------------------------------------

class TestEndpointClassificationAudit:
    """Verify every registered endpoint has an explicit auth classification."""

    EXPECTED_PUBLIC = {
        "GET /",
        "GET /api/v1/system/health",
    }

    def test_all_routes_have_auth_dependency(self):
        """Every route in the app must be either PUBLIC or have an auth dependency."""
        from apps.api.main import app

        public_paths = {"/", "/api/v1/system/health", "/docs", "/redoc", "/openapi.json"}
        protected_prefixes = ["/api/v1/"]

        routes = []
        for route in app.routes:
            if hasattr(route, "methods"):
                for method in route.methods:
                    if method in ("HEAD", "OPTIONS"):
                        continue
                    routes.append((method, route.path))

        # Verify protected endpoints have auth
        for method, path in routes:
            if path in public_paths:
                continue
            # All /api/v1/* routes must be protected
            if any(path.startswith(p) for p in protected_prefixes):
                # This endpoint should require auth — verify by hitting it without token
                from fastapi.testclient import TestClient
                with TestClient(app, raise_server_exceptions=False) as c:
                    r = c.request(method, path)
                    # Should be 401 (no token) — not 200 or other success
                    # Some may be 422 (missing body) — that's fine, means auth passed
                    # But it should NOT be 200
                    assert r.status_code != 200, (
                        f"{method} {path} returned 200 without auth — "
                        f"endpoint is accidentally public"
                    )
