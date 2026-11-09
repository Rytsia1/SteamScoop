import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.cursor import decode_cursor, encode_cursor
from app.models.game import Game
from app.models.review import Review
from app.repositories.base import BaseRepository


class GameRepository(BaseRepository[Game]):
    """Repository handling persistence and queries for the Steam game catalog."""

    def __init__(self, session: Session) -> None:
        super().__init__(Game, session)

    def get_by_steam_app_id(self, steam_app_id: int) -> Game | None:
        """Fetch a game by its official Steam Application ID."""
        stmt = select(Game).where(Game.steam_app_id == steam_app_id)
        return self.session.scalars(stmt).first()

    def get_active_game_by_id(self, game_id: uuid.UUID) -> Game | None:
        """Fetch an active game by primary key UUID."""
        stmt = select(Game).where(Game.id == game_id, Game.is_active.is_(True))
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

    def search_catalog(
        self,
        q: str | None = None,
        genre: str | None = None,
        catalog_status: str | None = "indexed",
        sort: str = "name_asc",
        cursor: str | None = None,
        limit: int = 20,
    ) -> tuple[Sequence[Game], bool, str | None]:
        """Perform keyset-paginated search and listing across public catalog games."""
        stmt = select(Game).where(Game.is_active.is_(True))

        if catalog_status is not None:
            stmt = stmt.where(Game.catalog_status == catalog_status)

        if q is not None and q.strip():
            stmt = stmt.where(Game.name.ilike(f"%{q.strip()}%"))

        if genre is not None and genre.strip():
            # Check JSONB array of genres contains the given genre string
            genre_val = genre.strip()
            stmt = stmt.where(Game.genres.contains([genre_val]))

        # Apply sort ordering and cursor filters
        if sort == "name_desc":
            if cursor:
                cursor_name, cursor_id = decode_cursor(cursor)
                stmt = stmt.where(
                    or_(
                        Game.name < cursor_name,
                        and_(Game.name == cursor_name, Game.id < cursor_id),
                    )
                )
            stmt = stmt.order_by(Game.name.desc(), Game.id.desc())
        elif sort == "recently_updated":
            if cursor:
                cursor_ts_str, cursor_id = decode_cursor(cursor)
                cursor_dt = datetime.fromisoformat(cursor_ts_str)
                stmt = stmt.where(
                    or_(
                        Game.updated_at < cursor_dt,
                        and_(Game.updated_at == cursor_dt, Game.id < cursor_id),
                    )
                )
            stmt = stmt.order_by(Game.updated_at.desc(), Game.id.desc())
        else:  # name_asc (default)
            if cursor:
                cursor_name, cursor_id = decode_cursor(cursor)
                stmt = stmt.where(
                    or_(
                        Game.name > cursor_name,
                        and_(Game.name == cursor_name, Game.id > cursor_id),
                    )
                )
            stmt = stmt.order_by(Game.name.asc(), Game.id.asc())

        # Fetch limit + 1 to check for has_more
        results = list(self.session.scalars(stmt.limit(limit + 1)).all())
        has_more = len(results) > limit
        items = results[:limit]

        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            if sort == "name_desc":
                next_cursor = encode_cursor(last_item.name, last_item.id)
            elif sort == "recently_updated":
                next_cursor = encode_cursor(last_item.updated_at.isoformat(), last_item.id)
            else:
                next_cursor = encode_cursor(last_item.name, last_item.id)

        return items, has_more, next_cursor

    def get_game_data_coverage(self, game_id: uuid.UUID) -> tuple[datetime | None, int, list[str]]:
        """Compute live coverage metadata: (latest_collection_at, total_reviews, languages)."""
        review_count_stmt = select(func.count(Review.id)).where(Review.game_id == game_id)
        review_count = self.session.scalar(review_count_stmt) or 0

        latest_time_stmt = select(func.max(Review.last_seen_at)).where(Review.game_id == game_id)
        latest_time = self.session.scalar(latest_time_stmt)

        languages_stmt = select(Review.language).where(Review.game_id == game_id).distinct()
        languages = list(self.session.scalars(languages_stmt).all())
        if not languages:
            languages = ["all"]

        return latest_time, review_count, languages

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
