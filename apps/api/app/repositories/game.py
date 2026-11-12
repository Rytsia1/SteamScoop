import uuid
from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.core.cursor import decode_cursor, encode_cursor
from app.core.exceptions import InvalidCursorError
from app.models.game import Game
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.repositories.base import BaseRepository

# sort key -> (column, descending). Ties always break on Game.id in the same direction.
_SORTS: dict[str, tuple[InstrumentedAttribute[Any], bool]] = {
    "name_asc": (Game.name, False),
    "name_desc": (Game.name, True),
    "recently_updated": (Game.updated_at, True),
    "release_desc": (Game.release_date, True),
    "release_asc": (Game.release_date, False),
}


def _parse_cursor_value(column: InstrumentedAttribute[Any], raw: Any) -> Any:
    """Turn the JSON cursor value back into the sort column's Python type."""
    if column is Game.updated_at:
        return datetime.fromisoformat(raw)
    if column is Game.release_date:
        return date.fromisoformat(raw)
    if not isinstance(raw, str):
        raise TypeError("Expected string cursor value")
    return raw


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
        catalog_statuses: Sequence[str] | None = ("indexed",),
        sort: str = "name_asc",
        cursor: str | None = None,
        limit: int = 20,
        is_free: bool | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        upcoming: bool = False,
    ) -> tuple[Sequence[Game], bool, str | None]:
        """Perform keyset-paginated search and listing across public catalog games."""
        stmt = select(Game).where(Game.is_active.is_(True))

        if catalog_statuses:
            stmt = stmt.where(Game.catalog_status.in_(catalog_statuses))

        if q is not None and q.strip():
            term = q.strip()
            name_match = Game.name.ilike(f"%{term}%")
            # Numeric queries also match the Steam App ID exactly
            stmt = stmt.where(
                or_(name_match, Game.steam_app_id == int(term)) if term.isdigit() else name_match
            )

        if genre is not None and genre.strip():
            # Check JSONB array of genres contains the given genre string
            stmt = stmt.where(Game.genres.contains([genre.strip()]))

        if is_free is not None:
            stmt = stmt.where(Game.is_free.is_(is_free))
        if year_from is not None:
            stmt = stmt.where(Game.release_date >= date(year_from, 1, 1))
        if year_to is not None:
            stmt = stmt.where(Game.release_date < date(year_to + 1, 1, 1))
        if upcoming:
            stmt = stmt.where(Game.release_date > func.current_date())

        column, descending = _SORTS.get(sort, _SORTS["name_asc"])
        if column is Game.release_date:
            # ponytail: undated games are left out of date-sorted lists;
            # add a NULLS LAST keyset branch if they need to appear.
            stmt = stmt.where(Game.release_date.is_not(None))

        if cursor:
            raw_value, cursor_id = decode_cursor(cursor)
            try:
                cursor_value = _parse_cursor_value(column, raw_value)
            except (TypeError, ValueError) as exc:
                raise InvalidCursorError(
                    message="The provided pagination cursor is invalid or malformed."
                ) from exc
            if descending:
                stmt = stmt.where(
                    or_(column < cursor_value, and_(column == cursor_value, Game.id < cursor_id))
                )
            else:
                stmt = stmt.where(
                    or_(column > cursor_value, and_(column == cursor_value, Game.id > cursor_id))
                )

        if descending:
            stmt = stmt.order_by(column.desc(), Game.id.desc())
        else:
            stmt = stmt.order_by(column.asc(), Game.id.asc())

        # Fetch limit + 1 to check for has_more
        results = list(self.session.scalars(stmt.limit(limit + 1)).all())
        has_more = len(results) > limit
        items = results[:limit]

        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            value = getattr(last_item, column.key)
            next_cursor = encode_cursor(
                value.isoformat() if isinstance(value, date) else value, last_item.id
            )

        return items, has_more, next_cursor

    def get_list_metrics(
        self, game_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, int, int, int, int]]:
        """Per-game (reviews, recommended, not_recommended, positive_sentiment, classified).

        Two grouped queries for a whole page of games, so listing stays free of N+1 lookups.
        """
        if not game_ids:
            return {}

        review_stmt = (
            select(
                Review.game_id,
                func.count(Review.id),
                func.count(Review.id).filter(Review.voted_up.is_(True)),
                func.count(Review.id).filter(Review.voted_up.is_(False)),
            )
            .where(Review.game_id.in_(game_ids))
            .group_by(Review.game_id)
        )
        sentiment_stmt = (
            select(
                Review.game_id,
                func.count(SentimentPrediction.id).filter(SentimentPrediction.label == "positive"),
                func.count(SentimentPrediction.id),
            )
            .join(SentimentPrediction, SentimentPrediction.review_id == Review.id)
            .where(Review.game_id.in_(game_ids), SentimentPrediction.is_current.is_(True))
            .group_by(Review.game_id)
        )

        sentiment = {
            row[0]: (row[1], row[2]) for row in self.session.execute(sentiment_stmt).all()
        }
        metrics: dict[uuid.UUID, tuple[int, int, int, int, int]] = {}
        for game_id, total, rec, not_rec in self.session.execute(review_stmt).all():
            pos, classified = sentiment.get(game_id, (0, 0))
            metrics[game_id] = (total, rec, not_rec, pos, classified)
        return metrics

    def list_genres(self) -> list[str]:
        """Distinct genre labels across publicly listed games, alphabetically."""
        genre = func.jsonb_array_elements_text(Game.genres).label("genre")
        stmt = (
            select(genre)
            .where(Game.is_active.is_(True), Game.catalog_status == "indexed")
            .distinct()
            .order_by(genre)
        )
        return list(self.session.scalars(stmt).all())

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
