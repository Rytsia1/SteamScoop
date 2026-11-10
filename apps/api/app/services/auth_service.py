"""Authentication and session management service for SteamScoop."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import SessionStore, hash_password, verify_password
from app.models.workspace import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, UserProfileResponse


class AuthService:
    """Service managing user registration, credential verification, and sessions."""

    def __init__(self, session: Session, user_repo: UserRepository | None = None) -> None:
        self.session = session
        self.user_repo = user_repo or UserRepository(session)
        self.session_store = SessionStore.get_store()

    def register(self, req: RegisterRequest) -> UserProfileResponse:
        """Register a new user account with hashed credentials."""
        existing = self.user_repo.get_by_email(req.email)
        if existing:
            raise ConflictError(
                message="An account with this email address already exists.",
                code="RESOURCE_ALREADY_EXISTS",
            )

        pw_hash = hash_password(req.password)
        user = self.user_repo.create_user(
            email=req.email,
            password_hash=pw_hash,
            display_name=req.display_name,
            status="active",
            roles=["member"],
        )
        roles = self.user_repo.get_user_roles(user.id)
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            roles=roles,
        )

    def login(self, req: LoginRequest) -> tuple[UserProfileResponse, str]:
        """Authenticate user credentials and generate active session token."""
        user = self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.password_hash):
            raise UnauthorizedError(
                message="Invalid email or password.",
                code="INVALID_CREDENTIALS",
            )

        if user.status != "active":
            raise UnauthorizedError(
                message="Account is suspended or pending verification.",
                code="ACCOUNT_INACTIVE",
            )

        roles = self.user_repo.get_user_roles(user.id)
        session_data = self.session_store.create_session(
            user_id=user.id,
            email=user.email,
            roles=roles,
        )

        profile = UserProfileResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            roles=roles,
        )
        return profile, session_data.session_token

    def logout(self, session_token: str | None) -> None:
        """Invalidate active session token."""
        if session_token:
            self.session_store.delete_session(session_token)

    def get_user_from_token(self, token: str) -> User | None:
        """Resolve active user from session token."""
        data = self.session_store.get_session(token)
        if not data:
            return None
        return self.user_repo.get(data.user_id)
