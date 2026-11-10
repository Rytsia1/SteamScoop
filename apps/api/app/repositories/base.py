import uuid
from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base repository implementing common CRUD operations."""

    def __init__(self, model: type[ModelType], session: Session) -> None:
        self.model = model
        self.session = session

    def get(self, entity_id: uuid.UUID) -> ModelType | None:
        """Fetch a single record by its primary key UUID."""
        return self.session.get(self.model, entity_id)

    def get_by_id(self, entity_id: uuid.UUID) -> ModelType | None:
        """Fetch a single record by its primary key UUID (alias for get)."""
        return self.get(entity_id)

    def get_multi(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Fetch multiple records with standard pagination offsets."""
        stmt = select(self.model).offset(skip).limit(limit)
        return self.session.scalars(stmt).all()

    def create(self, entity: ModelType) -> ModelType:
        """Add and commit a new entity to the database."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: ModelType) -> ModelType:
        """Commit updates to an existing entity."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity_id: uuid.UUID) -> bool:
        """Remove an entity by ID if present. Returns True if removed."""
        entity = self.get(entity_id)
        if entity is None:
            return False
        self.session.delete(entity)
        self.session.commit()
        return True
