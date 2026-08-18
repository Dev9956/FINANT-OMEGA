"""FININT OMEGA — Role-based access control."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Permission(str, Enum):
    # Data access
    READ_DATA = "data:read"
    WRITE_DATA = "data:write"
    # Research
    CREATE_RESEARCH = "research:create"
    READ_RESEARCH = "research:read"
    DELETE_RESEARCH = "research:delete"
    # Theses
    CREATE_THESIS = "thesis:create"
    EDIT_THESIS = "thesis:edit"
    DELETE_THESIS = "thesis:delete"
    # Predictions
    CREATE_PREDICTION = "prediction:create"
    RESOLVE_PREDICTION = "prediction:resolve"
    # Admin
    MANAGE_USERS = "admin:users"
    MANAGE_ORG = "admin:org"
    VIEW_AUDIT = "admin:audit"
    MANAGE_API_KEYS = "admin:apikeys"
    # Billing
    VIEW_BILLING = "admin:billing"


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


ROLES: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        Permission.READ_DATA,
        Permission.WRITE_DATA,
        Permission.CREATE_RESEARCH,
        Permission.READ_RESEARCH,
        Permission.DELETE_RESEARCH,
        Permission.CREATE_THESIS,
        Permission.EDIT_THESIS,
        Permission.DELETE_THESIS,
        Permission.CREATE_PREDICTION,
        Permission.RESOLVE_PREDICTION,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ORG,
        Permission.VIEW_AUDIT,
        Permission.MANAGE_API_KEYS,
        Permission.VIEW_BILLING,
    },
    Role.MANAGER: {
        Permission.READ_DATA,
        Permission.CREATE_RESEARCH,
        Permission.READ_RESEARCH,
        Permission.DELETE_RESEARCH,
        Permission.CREATE_THESIS,
        Permission.EDIT_THESIS,
        Permission.CREATE_PREDICTION,
        Permission.RESOLVE_PREDICTION,
        Permission.VIEW_AUDIT,
        Permission.MANAGE_API_KEYS,
    },
    Role.ANALYST: {
        Permission.READ_DATA,
        Permission.CREATE_RESEARCH,
        Permission.READ_RESEARCH,
        Permission.CREATE_THESIS,
        Permission.EDIT_THESIS,
        Permission.CREATE_PREDICTION,
    },
    Role.VIEWER: {
        Permission.READ_DATA,
        Permission.READ_RESEARCH,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a permission."""
    role_enum = Role(role) if role in Role._value2member_map_ else None
    if role_enum is None:
        return False
    return permission in ROLES.get(role_enum, set())


def get_role_permissions(role: str) -> list[str]:
    """Get all permission strings for a role."""
    role_enum = Role(role) if role in Role._value2member_map_ else None
    if role_enum is None:
        return []
    return [p.value for p in ROLES.get(role_enum, set())]


class AuthorizationError(Exception):
    """Raised when a user lacks permission."""


def authorize(role: str, permission: Permission) -> None:
    """Raise AuthorizationError if role lacks permission."""
    if not has_permission(role, permission):
        raise AuthorizationError(
            f"Role '{role}' lacks permission '{permission.value}'"
        )