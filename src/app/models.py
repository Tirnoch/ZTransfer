"""Database models and Pydantic schemas for ZTransfer."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Persistence model for authenticated users."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    password_hash: str
    role: str = Field(default="member", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    last_login_at: Optional[datetime] = None
    is_active: bool = Field(default=True)


class Upload(SQLModel, table=True):
    """Persistence model for uploaded files."""

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", nullable=False)
    download_token: str = Field(index=True, unique=True, nullable=False)
    delete_token_hash: str = Field(nullable=False)
    path: str = Field(nullable=False)
    original_name: str = Field(nullable=False)
    content_type: str = Field(nullable=False)
    size_bytes: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    expires_at: datetime = Field(nullable=False)
    sha256: str = Field(nullable=False)


class UploadResponse(BaseModel):
    """Response payload returned after a successful upload."""

    download_url: str
    delete_url: str


class Invite(SQLModel, table=True):
    """Invite tokens used to onboard new users."""

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True, nullable=False)
    email: EmailStr = Field(nullable=False)
    role: str = Field(default="member", nullable=False)
    expires_at: datetime = Field(nullable=False)
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")


class Session(SQLModel, table=True):
    """Active authenticated session tokens."""

    id: Optional[int] = Field(default=None, primary_key=True)
    token_hash: str = Field(index=True, unique=True, nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    expires_at: datetime = Field(nullable=False)
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
