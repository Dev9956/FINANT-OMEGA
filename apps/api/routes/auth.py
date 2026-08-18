# FININT OMEGA — Auth router (login / register / me)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.auth.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    SecurityContext,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "analyst"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str


# In-memory user store for dev mode (replaced with DB-backed store in production)
_users: dict[str, dict] = {}


# Seed default test user
def _seed_default_user():
    email = "test@finint.dev"
    if email not in _users:
        _users[email] = {
            "email": email,
            "password_hash": hash_password("test123"),
            "role": "admin",
        }


_seed_default_user()


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if req.email in _users:
        raise HTTPException(status_code=409, detail="User already exists")
    _users[req.email] = {
        "email": req.email,
        "password_hash": hash_password(req.password),
        "role": req.role,
    }
    token = create_access_token(
        subject=req.email,
        role=req.role,
        org_id="dev-org",
    )
    return TokenResponse(
        access_token=token,
        user_id=req.email,
        email=req.email,
        role=req.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    user = _users.get(req.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    token = create_access_token(
        subject=req.email,
        role=user["role"],
        org_id="dev-org",
    )
    return TokenResponse(
        access_token=token,
        user_id=req.email,
        email=req.email,
        role=user["role"],
    )


@router.get("/me")
def me(ctx: SecurityContext = Depends(get_current_user)):
    return {
        "user_id": ctx.user_id,
        "role": ctx.role,
        "org_id": ctx.org_id,
    }
