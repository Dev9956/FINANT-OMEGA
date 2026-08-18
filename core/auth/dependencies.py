"""FININT OMEGA — FastAPI authentication and authorization dependencies."""

from __future__ import annotations

from functools import wraps
from typing import Annotated, Any, Callable

import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.auth.rbac import AuthorizationError, Permission, Role, has_permission
from core.auth.security import SecurityContext, decode_token

logger = structlog.get_logger()

_bearer_scheme = HTTPBearer(auto_error=False)


async def _extract_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str | None:
    """Extract bearer token from Authorization header or X-API-Key header."""
    if credentials and credentials.credentials:
        return credentials.credentials
    if x_api_key:
        return x_api_key
    return None


async def get_current_user(
    token: Annotated[str | None, Depends(_extract_token)] = None,
) -> SecurityContext:
    """FastAPI dependency: extract and validate JWT, return SecurityContext.

    Raises HTTPException 401 if token missing or invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        ctx = decode_token(token)
        return SecurityContext(
            user_id=ctx.sub,
            role=ctx.role,
            org_id=ctx.org_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_role(*allowed_roles: str) -> Callable:
    """Dependency factory: require the authenticated user to have one of the specified roles."""

    async def _check(
        ctx: Annotated[SecurityContext, Depends(get_current_user)],
    ) -> SecurityContext:
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{ctx.role}' not in {allowed_roles}",
            )
        return ctx

    return _check


def require_permission(permission: Permission) -> Callable:
    """Dependency factory: require the authenticated user to have a specific permission."""

    async def _check(
        ctx: Annotated[SecurityContext, Depends(get_current_user)],
    ) -> SecurityContext:
        if not has_permission(ctx.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}",
            )
        return ctx

    return _check


def require_admin() -> Callable:
    """Shortcut: require admin role."""
    return require_role(Role.ADMIN.value)


def require_manager_or_admin() -> Callable:
    """Shortcut: require manager or admin role."""
    return require_role(Role.ADMIN.value, Role.MANAGER.value)


# ---------------------------------------------------------------------------
# PUBLIC endpoint marker — explicit opt-out from auth
# ---------------------------------------------------------------------------
# Routes that should be fully public (no auth required) use:
#   from core.auth.dependencies import PUBLIC
#   router.get("/health", dependencies=[Depends(PUBLIC)])
# This makes the intent explicit and auditable.


async def PUBLIC() -> None:  # noqa: N802 — intentional uppercase
    """Marker dependency: this endpoint is intentionally public.

    Add as a route dependency to document that the endpoint was reviewed
    and deemed public.  Does nothing at runtime.
    """


# ---------------------------------------------------------------------------
# Endpoint classification registry
# ---------------------------------------------------------------------------
# Every endpoint is classified into one of four tiers:
#   PUBLIC            — no auth, no tenant scoping
#   AUTHENTICATED     — valid JWT required
#   ADMIN             — admin role required
#   TENANT_SCOPED     — valid JWT + tenant isolation enforced
#
# Classification is stored here and checked at test time.
# Individual routes do NOT need to register — the test suite scans
# all routes and checks they have at least one auth dependency.

ENDPOINT_CLASSIFICATION: dict[str, str] = {
    # System
    "GET /": "PUBLIC",
    "GET /api/v1/system/health": "PUBLIC",
    # Auth (public by design — login/register must be accessible)
    "POST /api/v1/auth/register": "PUBLIC",
    "POST /api/v1/auth/login": "PUBLIC",
}
# Everything else defaults to AUTHENTICATED — the test suite
# verifies this by checking that every non-public route has
# an auth dependency injected.


def classify_endpoint(method: str, path: str, classification: str) -> None:
    """Register an endpoint classification (used by tests)."""
    key = f"{method.upper()} {path}"
    ENDPOINT_CLASSIFICATION[key] = classification


def get_endpoint_classification(method: str, path: str) -> str:
    """Get the classification for an endpoint."""
    key = f"{method.upper()} {path}"
    return ENDPOINT_CLASSIFICATION.get(key, "AUTHENTICATED")
