# FININT OMEGA — Auth router (login / register)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.auth.security import create_access_token, get_current_user, SecurityContext

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


# In-memory user store for dev mode
_users: dict[str, dict] = {}


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if req.email in _users:
        raise HTTPException(status_code=409, detail="User already exists")
    _users[req.email] = {
        "email": req.email,
        "password": req.password,
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
        _users[req.email] = {
            "email": req.email,
            "password": req.password,
            "role": "admin",
        }
        user = _users[req.email]
    token = create_access_token(
        subject=req.email,
        role=user.get("role", "admin"),
        org_id="dev-org",
    )
    return TokenResponse(
        access_token=token,
        user_id=req.email,
        email=req.email,
        role=user.get("role", "admin"),
    )


@router.get("/me")
def me(ctx: SecurityContext = Depends(get_current_user)):
    return {
        "user_id": ctx.user_id,
        "role": ctx.role,
        "org_id": ctx.org_id,
    }
