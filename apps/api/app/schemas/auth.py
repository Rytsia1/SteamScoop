"""Schemas for authentication, session lifecycle, and user profiles."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    email: str = Field(
        min_length=5,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Valid email address",
    )
    password: str = Field(min_length=8, max_length=128, description="Strong user password")
    display_name: str = Field(
        min_length=2, max_length=120, description="Public profile display name"
    )


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: str = Field(min_length=5, max_length=320, description="User email address")
    password: str = Field(description="User password")


class UserProfileResponse(BaseModel):
    """User profile data approved for public/member inspection."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    status: str
    roles: list[str] = Field(default_factory=lambda: ["member"])


class LoginResponseData(BaseModel):
    """Response payload for POST /auth/login."""

    user: UserProfileResponse
    token: str
