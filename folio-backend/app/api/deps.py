"""
app/api/deps.py
────────────────
FastAPI dependency helpers:
  - get_current_user  →  requires valid Bearer JWT
  - get_current_active_user  →  also checks is_active
  - require_plan  →  factory for plan-gating endpoints
"""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_access_token
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the JWT from Authorization: Bearer <token>."""
    token = credentials.credentials
    user_id = verify_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user


def require_plan(*plans: str) -> Callable:
    """
    Factory dependency — gate an endpoint by subscription plan.

    Usage:
        @router.get("/export", dependencies=[Depends(require_plan("pro", "team"))])
    """
    def _check(user: User = Depends(get_current_active_user)) -> User:
        if user.plan not in plans:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires a {' or '.join(plans)} plan.",
            )
        return user
    return _check