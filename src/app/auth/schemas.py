"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class BootstrapInviteRequest(BaseModel):
    """Payload for seeding the first admin invite."""

    admin_token: str = Field(..., description="Shared secret from ADMIN_BOOTSTRAP_TOKEN")
    email: EmailStr
    role: str = Field(default="admin", description="Role assigned to the invited user")


class InviteResponse(BaseModel):
    """Response containing invite details returned to the caller."""

    invite_token: str
    expires_at: datetime
    email: EmailStr
    role: str


class InviteAcceptRequest(BaseModel):
    """Payload for accepting an invite and creating a user."""

    token: str
    email: EmailStr
    password: str


class MessageResponse(BaseModel):
    """Generic response used for success/error messaging."""

    detail: str
