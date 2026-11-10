"""Authentication and user profile endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import (
    _extract_token,
    get_auth_service,
    get_current_active_user,
    get_request_id,
    get_user_repository,
)
from app.models.workspace import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, LoginResponseData, RegisterRequest, UserProfileResponse
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/auth/register",
    response_model=ResponseEnvelope[UserProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Create a new platform user account with email and password.",
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[UserProfileResponse]:
    profile = auth_service.register(request)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[UserProfileResponse](
        data=profile,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/auth/login",
    response_model=ResponseEnvelope[LoginResponseData],
    summary="Authenticate User and Create Session",
    description="Validate credentials, issue session token, and set HttpOnly session cookie.",
)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[LoginResponseData]:
    profile, token = auth_service.login(request)
    now_utc = datetime.now(UTC).isoformat()

    # Set session cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,
    )

    return ResponseEnvelope[LoginResponseData](
        data=LoginResponseData(user=profile, token=token),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate Current Session",
    description="Invalidate session token in session store and clear session cookie.",
)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    token = _extract_token(request)
    if token:
        auth_service.logout(token)
    response.delete_cookie(key="session_token")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/auth/me",
    response_model=ResponseEnvelope[UserProfileResponse],
    summary="Get Current User Profile",
    description="Retrieve the profile and assigned roles for the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[UserProfileResponse]:
    roles = user_repo.get_user_roles(current_user.id)
    profile = UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        status=current_user.status,
        roles=roles,
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[UserProfileResponse](
        data=profile,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )

