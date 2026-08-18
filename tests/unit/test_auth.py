"""Tests for authentication & RBAC — M15.5 Phase 6."""

from __future__ import annotations

import pytest

from core.auth.rbac import (
    AuthorizationError,
    Permission,
    Role,
    authorize,
    get_role_permissions,
    has_permission,
)
from core.auth.security import (
    create_access_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from core.auth.service import AuthService

TEST_SECRET = "test-secret-key-for-unit-tests"


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("s3cure-password")
        assert hashed != "s3cure-password"
        assert verify_password("s3cure-password", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_unique(self):
        h1 = hash_password("password")
        h2 = hash_password("password")
        assert h1 != h2  # bcrypt salts


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token("user-1", Role.ANALYST.value, secret_key=TEST_SECRET)
        payload = decode_token(token, secret_key=TEST_SECRET)
        assert payload.sub == "user-1"
        assert payload.role == Role.ANALYST.value

    def test_invalid_token(self):
        with pytest.raises(ValueError):
            decode_token("not-a-valid-token", secret_key=TEST_SECRET)

    def test_tampered_token(self):
        token = create_access_token("user-1", Role.ANALYST.value, secret_key=TEST_SECRET)
        with pytest.raises(ValueError):
            decode_token(token + "x", secret_key=TEST_SECRET)

    def test_wrong_secret(self):
        token = create_access_token("user-1", Role.ANALYST.value, secret_key="secret-a")
        with pytest.raises(ValueError):
            decode_token(token, secret_key="secret-b")

    def test_org_id_in_token(self):
        token = create_access_token("user-1", Role.ADMIN.value, org_id="org-1", secret_key=TEST_SECRET)
        payload = decode_token(token, secret_key=TEST_SECRET)
        assert payload.org_id == "org-1"

    def test_get_current_user(self):
        token = create_access_token("user-1", Role.MANAGER.value, org_id="org-1", secret_key=TEST_SECRET)
        ctx = get_current_user(token, secret_key=TEST_SECRET)
        assert ctx.user_id == "user-1"
        assert ctx.role == Role.MANAGER.value
        assert ctx.org_id == "org-1"
        assert ctx.tenant_id == "org-1"

    def test_tenant_fallback_to_user(self):
        token = create_access_token("user-1", Role.ANALYST.value, secret_key=TEST_SECRET)
        ctx = get_current_user(token, secret_key=TEST_SECRET)
        assert ctx.tenant_id == "user-1"


class TestRBAC:
    def test_admin_has_all(self):
        assert has_permission(Role.ADMIN.value, Permission.MANAGE_USERS)
        assert has_permission(Role.ADMIN.value, Permission.VIEW_AUDIT)
        assert has_permission(Role.ADMIN.value, Permission.READ_DATA)

    def test_viewer_limited(self):
        assert has_permission(Role.VIEWER.value, Permission.READ_DATA)
        assert has_permission(Role.VIEWER.value, Permission.READ_RESEARCH)
        assert not has_permission(Role.VIEWER.value, Permission.CREATE_THESIS)
        assert not has_permission(Role.VIEWER.value, Permission.WRITE_DATA)

    def test_unknown_role(self):
        assert not has_permission("hacker", Permission.READ_DATA)

    def test_authorize_pass(self):
        authorize(Role.ANALYST.value, Permission.CREATE_THESIS)

    def test_authorize_fail(self):
        with pytest.raises(AuthorizationError):
            authorize(Role.VIEWER.value, Permission.DELETE_THESIS)

    def test_permissions_list(self):
        perms = get_role_permissions(Role.ADMIN.value)
        assert Permission.MANAGE_USERS.value in perms

    def test_unknown_role_permissions_empty(self):
        assert get_role_permissions("hacker") == []


class TestAuthService:
    def test_register_and_authenticate(self):
        svc = AuthService()
        svc.set_token_secret(TEST_SECRET)
        user = svc.register("test@example.com", "password123", "Test User")
        assert user.user_id
        assert user.email == "test@example.com"

        authenticated = svc.authenticate("test@example.com", "password123")
        assert authenticated.user_id == user.user_id

    def test_register_duplicate_email(self):
        svc = AuthService()
        svc.register("dup@example.com", "password123", "A")
        with pytest.raises(ValueError):
            svc.register("dup@example.com", "otherpass123", "B")

    def test_register_short_password(self):
        svc = AuthService()
        with pytest.raises(ValueError):
            svc.register("short@example.com", "short", "A")

    def test_authenticate_wrong_password(self):
        svc = AuthService()
        svc.register("auth@example.com", "password123", "A")
        with pytest.raises(ValueError):
            svc.authenticate("auth@example.com", "wrong-password")

    def test_login_returns_token(self):
        svc = AuthService()
        svc.set_token_secret(TEST_SECRET)
        svc.register("login@example.com", "password123", "A", role=Role.MANAGER.value)
        token = svc.login("login@example.com", "password123")
        payload = decode_token(token, secret_key=TEST_SECRET)
        assert payload.role == Role.MANAGER.value

    def test_inactive_user(self):
        svc = AuthService()
        user = svc.register("inactive@example.com", "password123", "A")
        user.is_active = False
        with pytest.raises(ValueError):
            svc.authenticate("inactive@example.com", "password123")

    def test_get_context(self):
        svc = AuthService()
        svc.set_token_secret(TEST_SECRET)
        user = svc.register("ctx@example.com", "password123", "A", org_id="org-1")
        ctx = svc.get_context(user.user_id)
        assert ctx.org_id == "org-1"
        assert ctx.tenant_id == "org-1"

    def test_get_context_unknown_user(self):
        svc = AuthService()
        with pytest.raises(ValueError):
            svc.get_context("missing-user")

    def test_user_dict_includes_permissions(self):
        svc = AuthService()
        user = svc.register("perms@example.com", "password123", "A", role=Role.VIEWER.value)
        d = user.to_dict()
        assert Permission.READ_DATA.value in d["permissions"]
        assert Permission.CREATE_THESIS.value not in d["permissions"]