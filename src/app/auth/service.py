"""Service-layer helpers for authentication and invite workflows."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

from sqlmodel import select

from ..config import settings
from ..db import session_scope
from ..models import Invite, Session as SessionModel, User
from .passwords import hash_password, verify_password


class AuthError(Exception):
    """Base class for authentication-related errors."""


class InvalidInvite(AuthError):
    """Raised when an invite token is invalid or expired."""


class InviteAlreadyUsed(AuthError):
    """Raised when an invite token has already been consumed."""


class InvalidCredentials(AuthError):
    """Raised when login credentials are incorrect."""


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _hash_token(raw_token: str) -> str:
    digest = hashlib.sha256()
    digest.update(raw_token.encode("utf-8"))
    return digest.hexdigest()


def _generate_token() -> tuple[str, str]:
    raw = token_urlsafe(32)
    return raw, _hash_token(raw)


def create_invite(email: str, role: str = "member", created_by: Optional[int] = None) -> tuple[Invite, str]:
    """Create a new invite token for the provided email."""

    normalized_email = _normalize_email(email)
    expires_at = _now() + timedelta(hours=settings.invite_ttl_hours)
    raw_token, token_hash = _generate_token()

    with session_scope() as session:
        invite = Invite(
            token=token_hash,
            email=normalized_email,
            role=role,
            expires_at=expires_at,
            created_by=created_by,
        )
        session.add(invite)
        session.flush()
        session.refresh(invite)
    invite.token = token_hash
    return invite, raw_token


def consume_invite(token: str, email: str, password: str) -> User:
    """Create a user from an invite and invalidate the invite."""

    token_hash = _hash_token(token)
    now = _now()
    normalized_email = _normalize_email(email)
    with session_scope() as session:
        invite = session.exec(select(Invite).where(Invite.token == token_hash)).one_or_none()
        if invite is None:
            raise InvalidInvite("Invite not found")
        if invite.used_at is not None:
            raise InviteAlreadyUsed("Invite already used")
        if _ensure_aware(invite.expires_at) < now:
            raise InvalidInvite("Invite expired")
        if _normalize_email(invite.email) != normalized_email:
            raise InvalidInvite("Invite email mismatch")

        existing_user = session.exec(select(User).where(User.email == normalized_email)).one_or_none()
        if existing_user is not None:
            raise InviteAlreadyUsed("User already exists for invite email")

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            role=invite.role,
            created_at=now,
            last_login_at=None,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.refresh(user)

        invite.used_at = now
        session.add(invite)

    return user


def authenticate_user(email: str, password: str) -> User:
    """Validate credentials and return the user record."""

    normalized_email = _normalize_email(email)
    with session_scope() as session:
        user = session.exec(select(User).where(User.email == normalized_email)).one_or_none()
        if user is None or not user.is_active:
            raise InvalidCredentials("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise InvalidCredentials("Invalid credentials")
        user.last_login_at = _now()
        session.add(user)
        session.refresh(user)
    return user


def create_session(user_id: int, ip_address: Optional[str], user_agent: Optional[str]) -> str:
    """Create a session row and return the raw token for the cookie."""

    raw_token, token_hash = _generate_token()
    now = _now()
    expires_at = now + timedelta(seconds=settings.session_cookie_max_age)

    with session_scope() as session:
        session_model = SessionModel(
            token_hash=token_hash,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            last_seen_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(session_model)

    return raw_token


def revoke_session(raw_token: str) -> None:
    """Mark the session as revoked and remove future access."""

    token_hash = _hash_token(raw_token)
    now = _now()
    with session_scope() as session:
        session_model = (
            session.exec(select(SessionModel).where(SessionModel.token_hash == token_hash)).one_or_none()
        )
        if session_model is None:
            return
        session_model.revoked_at = now
        session.add(session_model)


def resolve_user_from_session(raw_token: str) -> Optional[User]:
    """Return the associated user for a session token, if valid."""

    token_hash = _hash_token(raw_token)
    now = _now()
    with session_scope() as session:
        row = session.exec(
            select(SessionModel, User)
            .where(SessionModel.token_hash == token_hash)
            .where(SessionModel.revoked_at.is_(None))  # type: ignore[union-attr]
            .where(SessionModel.expires_at > now)
            .where(SessionModel.user_id == User.id)
        ).one_or_none()
        if row is None:
            return None
        session_model, user = row
        session_model.last_seen_at = now
        session.add(session_model)
        session.refresh(user)
    return user


def users_exist() -> bool:
    """Return True if any user records currently exist."""

    with session_scope() as session:
        return session.exec(select(User.id)).first() is not None
