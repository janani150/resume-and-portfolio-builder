"""
app/api/v1/endpoints/auth.py
─────────────────────────────
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
PUT  /auth/me
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.models.user import RefreshToken, User
from app.schemas.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── Register ──────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    # Duplicate email check
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.flush()  # get user.id before commit

    access_token = create_access_token(user.id)
    refresh_raw = create_refresh_token(user.id)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_raw),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(rt)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse, summary="Sign in")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise _credentials_error()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(user.id)
    refresh_raw = create_refresh_token(user.id)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_raw),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(rt)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ── Refresh ───────────────────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    from app.core.security import decode_token
    from jose import JWTError

    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    token_hash = _hash_token(body.refresh_token)
    rt = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,  # noqa: E712
    ).first()

    if not rt or rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    # Rotate — revoke old, issue new
    rt.revoked = True
    user_id = payload["sub"]
    new_access = create_access_token(user_id)
    new_refresh_raw = create_refresh_token(user_id)

    new_rt = RefreshToken(
        user_id=user_id,
        token_hash=_hash_token(new_refresh_raw),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_rt)
    db.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh_raw,
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ── Logout ────────────────────────────────────────────────────────────────────
@router.post("/logout", response_model=MessageResponse, summary="Sign out")
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(body.refresh_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt:
        rt.revoked = True
        db.commit()
    return MessageResponse(message="Logged out successfully")


# ── Me ────────────────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserOut, summary="Get current user")
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserOut, summary="Update profile")
def update_me(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    allowed = {"first_name", "last_name", "avatar_url"}
    for field, value in body.items():
        if field in allowed and value is not None:
            setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user