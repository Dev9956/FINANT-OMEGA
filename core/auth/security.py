"""FININT OMEGA — Security primitives: password hashing and JWT tokens."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class TokenPayload:
    """Decoded JWT payload."""

    def __init__(
        self,
        sub: str,
        role: str,
        org_id: str | None = None,
        exp: int | None = None,
        **extra: Any,
    ) -> None:
        self.sub = sub
        self.role = role
        self.org_id = org_id
        self.exp = exp
        self.extra = extra

    @classmethod
    def from_dict(cls, data: dict) -> "TokenPayload":
        return cls(
            sub=data.get("sub", ""),
            role=data.get("role", "analyst"),
            org_id=data.get("org_id"),
            exp=data.get("exp"),
        )

    def to_dict(self) -> dict:
        return {
            "sub": self.sub,
            "role": self.role,
            "org_id": self.org_id,
            "exp": self.exp,
            **self.extra,
        }


class SecurityContext:
    """Authenticated request context with tenant isolation."""

    def __init__(
        self,
        user_id: str,
        role: str,
        org_id: str | None = None,
        email: str = "",
    ) -> None:
        self.user_id = user_id
        self.role = role
        self.org_id = org_id
        self.email = email

    @property
    def tenant_id(self) -> str:
        """Tenant identifier for isolation — user scoped unless org exists."""
        return self.org_id or self.user_id


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def _get_secret_key() -> str:
    key = os.environ.get("APP_SECRET_KEY", "")
    if key:
        return key
    logger.warning("auth_using_ephemeral_secret", msg="APP_SECRET_KEY not set; tokens invalid on restart")
    return "dev-ephemeral-key-do-not-use-in-prod"


def create_access_token(
    subject: str,
    role: str,
    org_id: str | None = None,
    expires_delta: timedelta | None = None,
    secret_key: str | None = None,
) -> str:
    """Create a signed JWT access token."""
    expires = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = TokenPayload(
        sub=subject,
        role=role,
        org_id=org_id,
        exp=int(expires.timestamp()),
        iat=int(datetime.now(timezone.utc).timestamp()),
    )
    return jwt.encode(payload.to_dict(), secret_key or _get_secret_key(), algorithm=JWT_ALGORITHM)


def decode_token(token: str, secret_key: str | None = None) -> TokenPayload:
    """Decode and validate a JWT token."""
    try:
        data = jwt.decode(token, secret_key or _get_secret_key(), algorithms=[JWT_ALGORITHM])
        payload = TokenPayload.from_dict(data)
        if not payload.sub:
            raise ValueError("Token missing subject")
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def get_current_user(token: str, secret_key: str | None = None) -> SecurityContext:
    """Create a SecurityContext from a bearer token."""
    payload = decode_token(token, secret_key=secret_key)
    return SecurityContext(
        user_id=payload.sub,
        role=payload.role,
        org_id=payload.org_id,
    )