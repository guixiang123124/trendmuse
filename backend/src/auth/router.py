"""
Auth API routes for TrendMuse.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional

from src.auth.models import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_google_id,
    create_user,
)
from src.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    verify_google_token,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()


# --- Schemas ---

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    credits_remaining: int
    is_active: bool
    is_admin: bool
    created_at: str


# --- Dependencies ---

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Decode JWT and return user dict. Use as a FastAPI dependency."""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# --- Routes ---

@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest):
    if get_user_by_email(data.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(data.password)
    user = create_user(
        email=data.email,
        username=data.username,
        hashed_password=hashed,
        full_name=data.full_name,
    )
    token = create_access_token(user["id"])
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user or not user.get("hashed_password"):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"])
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest):
    """Verify Google ID token, create or find user, return JWT."""
    info = verify_google_token(data.id_token)
    if not info or not info.get("email"):
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # Try find by google_id first, then email
    user = get_user_by_google_id(info["google_id"])
    if not user:
        user = get_user_by_email(info["email"])
    if not user:
        # Auto-register
        username = info["email"].split("@")[0]
        user = create_user(
            email=info["email"],
            username=username,
            full_name=info.get("full_name"),
            google_id=info["google_id"],
        )

    token = create_access_token(user["id"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        full_name=user["full_name"],
        credits_remaining=user["credits_remaining"],
        is_active=bool(user["is_active"]),
        is_admin=bool(user["is_admin"]),
        created_at=user["created_at"],
    )
