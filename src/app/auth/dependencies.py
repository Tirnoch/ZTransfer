"""Authentication dependencies for FastAPI routes."""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status

from ..config import settings
from ..models import User
from . import service


def get_current_user(session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name)) -> User:
    """Dependency that resolves the currently authenticated user."""

    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = service.resolve_user_from_session(session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


RequireAuth = Depends(get_current_user)
