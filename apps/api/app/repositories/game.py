from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.game import Game
from app.repositories.base import BaseRepository


class GameRepository(BaseRepository[Game]):
    """Repository handling persistence and queries for the Steam game catalog."""

    def __init__(self, session: Session) -> None:
        super().__init__(Game, session)

    def get_by_steam_app_id(self, steam_app_id: int) -> Game | None:
        """Fetch a game by its official Steam Application ID."""
        stmt = select(Game).where(Game.steam_app_id == steam_app_id)
        return self.session.scalars(stmt).first()

    def get_active_games(self, skip: int = 0, limit: int = 100) -> Sequence[Game]:
        """Fetch indexed, publicly available games with pagination."""
        stmt = (
            select(Game)
            .where(Game.is_active.is_(True), Game.catalog_status == "indexed")
            .order_by(Game.name.asc())
            .offset(skip)
            .limit(limit)
        )
        return self.session.scalars(stmt).all()

    def search_by_name(self, query: str, limit: int = 20) -> Sequence[Game]:
        """Case-insensitive prefix/substring search for games by display name."""
        pattern = f"%{query}%"
        stmt = (
            select(Game)
            .where(Game.name.ilike(pattern), Game.is_active.is_(True))
            .order_by(Game.name.asc())
            .limit(limit)
        )
        return self.session.scalars(stmt).all()

    def upsert_game(
        self,
        steam_app_id: int,
        name: str,
        **kwargs: Any,
    ) -> tuple[Game, bool]:
        """Idempotently insert or update a Game record by steam_app_id.

        Returns (game, is_created).
        """
        existing = self.get_by_steam_app_id(steam_app_id)
        if existing is not None:
            existing.name = name
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing, False

        game = Game(steam_app_id=steam_app_id, name=name, **kwargs)
        created = self.create(game)
        return created, True

