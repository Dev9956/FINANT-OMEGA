"""FININT OMEGA — Authentication service for user management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from core.auth.rbac import Role, get_role_permissions
from core.auth.security import SecurityContext, hash_password, verify_password

logger = structlog.get_logger()


class User:
    """Domain model for a user."""

    def __init__(
        self,
        email: str,
        full_name: str,
        role: str,
        user_id: str | None = None,
        org_id: str | None = None,
        hashed_password: str = "",
        is_active: bool = True,
    ) -> None:
        self.user_id = user_id or str(uuid.uuid4())
        self.email = email
        self.full_name = full_name
        self.role = role
        self.org_id = org_id
        self.hashed_password = hashed_password
        self.is_active = is_active

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "org_id": self.org_id,
            "is_active": self.is_active,
            "permissions": get_role_permissions(self.role),
        }


class UserStore:
    """In-memory user store (PostgreSQL-backed in production)."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._by_email: dict[str, str] = {}

    def add(self, user: User) -> None:
        self._users[user.user_id] = user
        self._by_email[user.email.lower()] = user.user_id

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        uid = self._by_email.get(email.lower())
        return self._users.get(uid) if uid else None

    def list(self) -> list[User]:
        return list(self._users.values())

    def update(self, user: User) -> None:
        self._users[user.user_id] = user

    def delete(self, user_id: str) -> bool:
        user = self._users.pop(user_id, None)
        if user:
            self._by_email.pop(user.email.lower(), None)
            return True
        return False


class AuthService:
    """Handles registration, login, and token issuance."""

    def __init__(self, store: UserStore | None = None) -> None:
        self._store = store or UserStore()
        self._token_secret: str | None = None

    @property
    def store(self) -> UserStore:
        return self._store

    def set_token_secret(self, secret: str) -> None:
        self._token_secret = secret

    def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = Role.ANALYST.value,
        org_id: str | None = None,
    ) -> User:
        """Register a new user."""
        if not email or not password:
            raise ValueError("Email and password are required")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if self._store.get_by_email(email):
            raise ValueError(f"User already exists: {email}")

        user = User(
            email=email,
            full_name=full_name,
            role=role,
            org_id=org_id,
            hashed_password=hash_password(password),
        )
        self._store.add(user)
        logger.info("user_registered", user_id=user.user_id, email=email, role=role)
        return user

    def authenticate(self, email: str, password: str) -> User:
        """Authenticate a user and return the user if valid."""
        user = self._store.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("User account is inactive")
        return user

    def login(self, email: str, password: str) -> str:
        """Authenticate and return a JWT token."""
        user = self.authenticate(email, password)
        from core.auth.security import create_access_token
        return create_access_token(
            subject=user.user_id,
            role=user.role,
            org_id=user.org_id,
            secret_key=self._token_secret,
        )

    def get_context(self, user_id: str) -> SecurityContext:
        """Get a security context for a user."""
        user = self._store.get(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        return SecurityContext(
            user_id=user.user_id,
            role=user.role,
            org_id=user.org_id,
            email=user.email,
        )