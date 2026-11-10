"""Repository for user accounts, credentials, and role assignments."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.workspace import Role, User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access repository for User entities and role mapping."""

    def __init__(self, session: Session) -> None:
        super().__init__(User, session)

    def get_by_email(self, email: str) -> User | None:
        """Fetch user by case-insensitive email address."""
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        return self.session.scalars(stmt).first()

    def get_user_roles(self, user_id: uuid.UUID) -> list[str]:
        """Fetch active role keys assigned to a user."""
        stmt = (
            select(Role.role_key)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        roles = list(self.session.scalars(stmt).all())
        return roles or ["member"]

    def create_user(
        self,
        email: str,
        password_hash: str,
        display_name: str,
        status: str = "active",
        roles: list[str] | None = None,
    ) -> User:
        """Create new user account and attach default roles."""
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            display_name=display_name.strip(),
            status=status,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(user)
        self.session.flush()

        role_keys = roles or ["member"]
        for r_key in role_keys:
            role_entity = self.session.scalars(select(Role).where(Role.role_key == r_key)).first()
            if not role_entity:
                role_entity = Role(role_key=r_key, description=f"{r_key.title()} role")
                self.session.add(role_entity)
                self.session.flush()

            user_role = UserRole(user_id=user.id, role_id=role_entity.id)
            self.session.add(user_role)

        self.session.commit()
        self.session.refresh(user)
        return user
