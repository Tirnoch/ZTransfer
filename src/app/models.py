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


class UploadResponse(BaseModel):
    """Response payload returned after a successful upload."""

    download_url: str
    delete_url: str
