"""Domain service for bounded multi-game comparative analysis."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import GameNotFoundError
from app.models.aspect import Aspect, AspectPrediction
from app.models.game import Game
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.schemas.comparison import (
    ComparisonPeriod,
    ComparisonRequest,
    ComparisonResponseData,
    GameComparisonResult,
)


class ComparisonService:
    """Service evaluating comparative analytics across 2 to 5 indexed games."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def compare_games(self, request: ComparisonRequest) -> ComparisonResponseData:
        """Compare games across requested allowlisted metrics in a bounded read-only query."""
        results: list[GameComparisonResult] = []

        from_date = request.period.from_date if request.period else None
        to_date = request.period.to_date if request.period else None

        for game_id in request.game_ids:
            game = self.session.get(Game, game_id)
            if not game or not game.is_active:
                raise GameNotFoundError(str(game_id))

            # Fetch reviews in period
            timestamp_col = func.coalesce(Review.steam_created_at, Review.created_at)
            stmt = select(Review).where(Review.game_id == game_id)
            if from_date:
                stmt = stmt.where(timestamp_col >= from_date)
            if to_date:
                stmt = stmt.where(timestamp_col < to_date)

            reviews = list(self.session.scalars(stmt).all())
            review_count = len(reviews)
            review_ids = [r.id for r in reviews]

            # Steam recommendation rate
            steam_rec = sum(1 for r in reviews if r.voted_up is True)
            steam_not_rec = sum(1 for r in reviews if r.voted_up is False)
            rec_total = steam_rec + steam_not_rec
            steam_rate = round(steam_rec / rec_total, 4) if rec_total > 0 else None

            # Sentiment predictions
            model_pos_rate = None
            sentiment_score = None
            if review_ids and ("model_sentiment" in request.metrics):
                sent_stmt = select(SentimentPrediction).where(
                    SentimentPrediction.review_id.in_(review_ids),
                    SentimentPrediction.is_current.is_(True),
                )
                preds = list(self.session.scalars(sent_stmt).all())
                pos = sum(1 for p in preds if p.label == "positive")
                neg = sum(1 for p in preds if p.label == "negative")
                neu = sum(1 for p in preds if p.label == "neutral")
                classified = pos + neg + neu

                if classified > 0:
                    model_pos_rate = round(pos / classified, 4)
                    sentiment_score = round((pos - neg) / classified, 4)

            # Aspect sentiment
            aspect_scores: dict[str, float] | None = None
            if review_ids and ("aspect_sentiment" in request.metrics):
                asp_stmt = (
                    select(AspectPrediction, Aspect)
                    .join(Aspect, AspectPrediction.aspect_id == Aspect.id)
                    .where(AspectPrediction.review_id.in_(review_ids))
                )
                asp_rows = self.session.execute(asp_stmt).all()
                asp_counts: dict[str, dict[str, int]] = {}
                for ap, asp in asp_rows:
                    if asp.aspect_key not in asp_counts:
                        asp_counts[asp.aspect_key] = {"pos": 0, "neg": 0, "total": 0}
                    asp_counts[asp.aspect_key]["total"] += 1
                    if ap.sentiment_label == "positive":
                        asp_counts[asp.aspect_key]["pos"] += 1
                    elif ap.sentiment_label == "negative":
                        asp_counts[asp.aspect_key]["neg"] += 1

                aspect_scores = {
                    k: round((v["pos"] - v["neg"]) / v["total"], 4)
                    for k, v in asp_counts.items()
                    if v["total"] > 0
                }

            results.append(
                GameComparisonResult(
                    game_id=game.id,
                    name=game.name,
                    review_volume=review_count if "review_volume" in request.metrics else None,
                    steam_recommendation_rate=steam_rate
                    if "steam_recommendation" in request.metrics
                    else None,
                    model_positive_rate=model_pos_rate
                    if "model_sentiment" in request.metrics
                    else None,
                    sentiment_score=sentiment_score
                    if "model_sentiment" in request.metrics
                    else None,
                    aspect_sentiment=aspect_scores
                    if "aspect_sentiment" in request.metrics
                    else None,
                )
            )

        return ComparisonResponseData(
            games=results,
            period=ComparisonPeriod(from_date=from_date, to_date=to_date)
            if (from_date or to_date)
            else None,
            model_version=request.model_version,
        )

