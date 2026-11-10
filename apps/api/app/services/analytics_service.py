"""Analytics coordination service for SteamScoop.

Orchestrates time-series bucket generation, version-aware prediction aggregation,
metric computation with explicit denominators, and idempotency guarantees.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.aggregator import (
    AnalyticsAggregator,
    AspectPredictionInput,
    BucketMetricsResult,
    RawReviewInput,
    SentimentPredictionInput,
    TopicAssignmentInput,
)
from app.core.exceptions import GameNotFoundError
from app.models.aspect import Aspect, AspectPrediction
from app.models.game import Game
from app.models.ml import MLModel
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.models.topic import ReviewTopic, Topic
from app.repositories.analytics import AnalyticsRepository
from app.repositories.aspect import AspectRepository
from app.repositories.review import ReviewRepository
from app.repositories.sentiment import SentimentRepository
from app.repositories.topic import TopicRepository
from app.schemas.analytics import (
    AnalyticsPoint,
    AspectSummaryPoint,
    GameAnalyticsData,
    GameAspectsData,
    GameTopicsData,
    SentimentDistributionData,
    TopicSummaryPoint,
)

logger = logging.getLogger("steamscoop.services.analytics")


class AnalyticsService:
    """Service orchestrating batch analytics generation and query operations."""

    def __init__(
        self,
        session: Session,
        analytics_repo: AnalyticsRepository | None = None,
        review_repo: ReviewRepository | None = None,
        sentiment_repo: SentimentRepository | None = None,
        aspect_repo: AspectRepository | None = None,
        topic_repo: TopicRepository | None = None,
    ) -> None:
        self.session = session
        self.analytics_repo = analytics_repo or AnalyticsRepository(session)
        self.review_repo = review_repo or ReviewRepository(session)
        self.sentiment_repo = sentiment_repo or SentimentRepository(session)
        self.aspect_repo = aspect_repo or AspectRepository(session)
        self.topic_repo = topic_repo or TopicRepository(session)

    def aggregate_game(
        self,
        game_id: uuid.UUID,
        period_types: list[str] | None = None,
        model_version_key: str = "baseline",
    ) -> dict[str, Any]:
        """Aggregate all review and model prediction metrics for a game across time periods.

        Enforces version-awareness: predictions are filtered strictly to the active or
        specified model version key, preventing silent cross-contamination of models.
        """
        game = self.session.get(Game, game_id)
        if not game:
            raise GameNotFoundError(str(game_id))

        target_periods = period_types or ["day", "week", "month"]

        # 1. Determine temporal boundaries for game reviews
        timestamp_col = func.coalesce(Review.steam_created_at, Review.created_at)
        boundary_stmt = select(
            func.min(timestamp_col),
            func.max(timestamp_col),
        ).where(Review.game_id == game_id)

        min_dt, max_dt = self.session.execute(boundary_stmt).one()
        if not min_dt or not max_dt:
            logger.info("No reviews available for game %s; skipping aggregation.", game_id)
            return {
                "game_id": str(game_id),
                "model_version_key": model_version_key,
                "buckets_computed": 0,
                "message": "No reviews found for game.",
            }

        min_date: date = min_dt.date() if isinstance(min_dt, datetime) else min_dt
        max_date: date = max_dt.date() if isinstance(max_dt, datetime) else max_dt

        # Resolve active model IDs if needed to ensure model isolation
        active_sentiment_model = self.session.scalars(
            select(MLModel)
            .where(MLModel.task == "sentiment", MLModel.is_active.is_(True))
            .order_by(MLModel.created_at.desc())
        ).first()
        active_absa_model = self.session.scalars(
            select(MLModel)
            .where(MLModel.task == "absa", MLModel.is_active.is_(True))
            .order_by(MLModel.created_at.desc())
        ).first()
        active_topic_model = self.session.scalars(
            select(MLModel)
            .where(MLModel.task == "topic", MLModel.is_active.is_(True))
            .order_by(MLModel.created_at.desc())
        ).first()

        total_buckets_created = 0

        for period_type in target_periods:
            buckets = AnalyticsAggregator.generate_period_buckets(min_date, max_date, period_type)

            for p_start, p_end in buckets:
                p_start_dt = datetime.combine(p_start, time.min, tzinfo=UTC)
                p_end_dt = datetime.combine(p_end, time.min, tzinfo=UTC)

                # Fetch reviews in bucket
                review_stmt = (
                    select(Review)
                    .where(
                        Review.game_id == game_id,
                        timestamp_col >= p_start_dt,
                        timestamp_col < p_end_dt,
                    )
                    .order_by(timestamp_col.asc())
                )
                reviews = list(self.session.scalars(review_stmt).all())
                review_inputs = [
                    RawReviewInput(
                        id=str(r.id),
                        voted_up=r.voted_up,
                        created_date=(r.steam_created_at or r.created_at).date(),
                    )
                    for r in reviews
                ]

                review_ids = [r.id for r in reviews]

                # Fetch version-isolated Sentiment predictions
                sentiment_map: dict[str, SentimentPredictionInput] = {}
                if review_ids:
                    sent_stmt = select(SentimentPrediction).where(
                        SentimentPrediction.review_id.in_(review_ids),
                        SentimentPrediction.is_current.is_(True),
                    )
                    if active_sentiment_model and model_version_key != "all":
                        sent_stmt = sent_stmt.where(
                            SentimentPrediction.ml_model_id == active_sentiment_model.id
                        )

                    for sp in self.session.scalars(sent_stmt).all():
                        sentiment_map[str(sp.review_id)] = SentimentPredictionInput(
                            review_id=str(sp.review_id),
                            label=sp.label,
                            confidence=float(sp.confidence) if sp.confidence is not None else None,
                        )

                # Fetch version-isolated ABSA predictions
                aspect_inputs: list[AspectPredictionInput] = []
                if review_ids:
                    asp_stmt = (
                        select(AspectPrediction, Aspect)
                        .join(Aspect, AspectPrediction.aspect_id == Aspect.id)
                        .where(AspectPrediction.review_id.in_(review_ids))
                    )
                    if active_absa_model and model_version_key != "all":
                        asp_stmt = asp_stmt.where(
                            AspectPrediction.ml_model_id == active_absa_model.id
                        )

                    for ap, asp in self.session.execute(asp_stmt).all():
                        aspect_inputs.append(
                            AspectPredictionInput(
                                review_id=str(ap.review_id),
                                aspect_key=asp.aspect_key,
                                display_name=asp.display_name,
                                sentiment_label=ap.sentiment_label,
                                confidence=float(ap.confidence)
                                if ap.confidence is not None
                                else None,
                            )
                        )

                # Fetch version-isolated Topic assignments
                topic_inputs: list[TopicAssignmentInput] = []
                if review_ids:
                    top_stmt = (
                        select(ReviewTopic, Topic)
                        .join(Topic, ReviewTopic.topic_id == Topic.id)
                        .where(ReviewTopic.review_id.in_(review_ids))
                    )
                    if active_topic_model and model_version_key != "all":
                        top_stmt = top_stmt.where(Topic.ml_model_id == active_topic_model.id)

                    for rt, top in self.session.execute(top_stmt).all():
                        topic_inputs.append(
                            TopicAssignmentInput(
                                review_id=str(rt.review_id),
                                topic_key=top.topic_key,
                                label=top.label,
                                score=float(rt.score) if rt.score is not None else None,
                                is_primary=rt.is_primary,
                                is_outlier=top.is_outlier,
                                keywords=top.keywords if isinstance(top.keywords, list) else [],
                            )
                        )

                # Compute pure mathematical aggregates
                metrics: BucketMetricsResult = AnalyticsAggregator.compute_bucket_metrics(
                    period_type=period_type,
                    period_start=p_start,
                    period_end=p_end,
                    model_version_key=model_version_key,
                    reviews=review_inputs,
                    sentiment_predictions=sentiment_map,
                    aspect_predictions=aspect_inputs,
                    topic_assignments=topic_inputs,
                )

                # Persist aggregate idempotently
                self.analytics_repo.upsert_analytic(
                    game_id=game_id,
                    period_type=metrics.period_type,
                    period_start=metrics.period_start,
                    period_end=metrics.period_end,
                    model_version_key=metrics.model_version_key,
                    review_count=metrics.review_count,
                    positive_count=metrics.positive_count,
                    negative_count=metrics.negative_count,
                    neutral_count=metrics.neutral_count,
                    steam_recommended_count=metrics.steam_recommended_count,
                    steam_not_recommended_count=metrics.steam_not_recommended_count,
                    sentiment_score=metrics.sentiment_score,
                    aspect_summary=metrics.aspect_summary,
                    topic_summary=metrics.topic_summary,
                )
                total_buckets_created += 1

        return {
            "game_id": str(game_id),
            "model_version_key": model_version_key,
            "period_types": target_periods,
            "buckets_computed": total_buckets_created,
            "time_range": {"min_date": min_date.isoformat(), "max_date": max_date.isoformat()},
        }

    def get_game_analytics(
        self,
        game_id: uuid.UUID,
        period_type: str = "week",
        from_date: date | None = None,
        to_date: date | None = None,
        model_version_key: str = "baseline",
    ) -> GameAnalyticsData:
        """Fetch timeline of aggregated analytics matching query constraints."""
        game = self.session.get(Game, game_id)
        if not game:
            raise GameNotFoundError(str(game_id))

        records = self.analytics_repo.get_timeline(
            game_id=game_id,
            period_type=period_type,
            start_date=from_date,
            end_date=to_date,
            model_version_key=model_version_key,
        )

        points = [
            AnalyticsPoint(
                period_start=r.period_start,
                period_end=r.period_end,
                review_count=r.review_count,
                positive_count=r.positive_count,
                negative_count=r.negative_count,
                neutral_count=r.neutral_count,
                steam_recommended_count=r.steam_recommended_count,
                steam_not_recommended_count=r.steam_not_recommended_count,
                sentiment_score=float(r.sentiment_score) if r.sentiment_score is not None else None,
            )
            for r in records
        ]

        return GameAnalyticsData(
            game_id=game_id,
            period=period_type,  # type: ignore[arg-type]
            model_version=model_version_key,
            points=points,
        )

    def get_game_sentiment_distribution(
        self,
        game_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        model_version_key: str = "baseline",
        include_trend: bool = False,
    ) -> SentimentDistributionData:
        """Calculate total sentiment distribution and coverage rates over the date window."""
        game = self.session.get(Game, game_id)
        if not game:
            raise GameNotFoundError(str(game_id))

        records = self.analytics_repo.get_timeline(
            game_id=game_id,
            period_type="week",
            start_date=from_date,
            end_date=to_date,
            model_version_key=model_version_key,
        )

        total_reviews = sum(r.review_count for r in records)
        pos = sum(r.positive_count for r in records)
        neg = sum(r.negative_count for r in records)
        neu = sum(r.neutral_count for r in records)

        classified = pos + neg + neu
        unclassified = max(0, total_reviews - classified)

        pos_rate = round(pos / classified, 4) if classified > 0 else 0.0
        neg_rate = round(neg / classified, 4) if classified > 0 else 0.0
        neu_rate = round(neu / classified, 4) if classified > 0 else 0.0
        cov_rate = round(classified / total_reviews, 4) if total_reviews > 0 else 0.0
        unclass_rate = round(unclassified / total_reviews, 4) if total_reviews > 0 else 0.0

        sentiment_score = round((pos - neg) / classified, 4) if classified > 0 else None

        points: list[AnalyticsPoint] | None = None
        if include_trend:
            points = [
                AnalyticsPoint(
                    period_start=r.period_start,
                    period_end=r.period_end,
                    review_count=r.review_count,
                    positive_count=r.positive_count,
                    negative_count=r.negative_count,
                    neutral_count=r.neutral_count,
                    steam_recommended_count=r.steam_recommended_count,
                    steam_not_recommended_count=r.steam_not_recommended_count,
                    sentiment_score=float(r.sentiment_score)
                    if r.sentiment_score is not None
                    else None,
                )
                for r in records
            ]

        return SentimentDistributionData(
            game_id=game_id,
            model_version=model_version_key,
            total_reviews=total_reviews,
            classified_count=classified,
            unclassified_count=unclassified,
            positive_count=pos,
            negative_count=neg,
            neutral_count=neu,
            positive_rate=pos_rate,
            negative_rate=neg_rate,
            neutral_rate=neu_rate,
            coverage_rate=cov_rate,
            unclassified_rate=unclass_rate,
            sentiment_score=sentiment_score,
            timeline=points,
        )

    def get_game_aspects(
        self,
        game_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        model_version_key: str = "baseline",
        limit: int = 20,
        sort: str = "mentions_desc",
    ) -> GameAspectsData:
        """Aggregate aspect-level mentions and polarities across time buckets."""
        game = self.session.get(Game, game_id)
        if not game:
            raise GameNotFoundError(str(game_id))

        records = self.analytics_repo.get_timeline(
            game_id=game_id,
            period_type="week",
            start_date=from_date,
            end_date=to_date,
            model_version_key=model_version_key,
        )

        total_reviews = sum(r.review_count for r in records)
        total_mentions = 0
        merged_aspects: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "aspect_key": "",
                "display_name": "",
                "mention_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            }
        )

        for r in records:
            asp_sum = r.aspect_summary or {}
            for item in asp_sum.get("aspects", []):
                key = item["aspect_key"]
                merged = merged_aspects[key]
                merged["aspect_key"] = key
                merged["display_name"] = item.get("display_name", key)
                merged["mention_count"] += item.get("mention_count", 0)
                merged["positive_count"] += item.get("positive_count", 0)
                merged["negative_count"] += item.get("negative_count", 0)
                merged["neutral_count"] += item.get("neutral_count", 0)
                total_mentions += item.get("mention_count", 0)

        aspect_points: list[AspectSummaryPoint] = []
        for key, item in merged_aspects.items():
            m_c = item["mention_count"]
            p_c = item["positive_count"]
            n_c = item["negative_count"]
            u_c = item["neutral_count"]

            asp_score = round((p_c - n_c) / m_c, 4) if m_c > 0 else 0.0
            p_rate = round(p_c / m_c, 4) if m_c > 0 else 0.0
            n_rate = round(n_c / m_c, 4) if m_c > 0 else 0.0
            u_rate = round(u_c / m_c, 4) if m_c > 0 else 0.0
            prev = round(m_c / total_reviews, 4) if total_reviews > 0 else 0.0

            aspect_points.append(
                AspectSummaryPoint(
                    aspect_key=key,
                    display_name=item["display_name"],
                    mention_count=m_c,
                    positive_count=p_c,
                    negative_count=n_c,
                    neutral_count=u_c,
                    positive_rate=p_rate,
                    negative_rate=n_rate,
                    neutral_rate=u_rate,
                    sentiment_score=asp_score,
                    prevalence=prev,
                )
            )

        if sort == "negative_rate_desc":
            aspect_points.sort(key=lambda x: x.negative_rate, reverse=True)
        elif sort == "positive_rate_desc":
            aspect_points.sort(key=lambda x: x.positive_rate, reverse=True)
        else:  # mentions_desc
            aspect_points.sort(key=lambda x: x.mention_count, reverse=True)

        return GameAspectsData(
            game_id=game_id,
            taxonomy_version="aspects-1.0",
            model_version=model_version_key,
            aspects=aspect_points[:limit],
            total_aspect_mentions=total_mentions,
            unique_reviews_with_aspects=sum(
                (r.aspect_summary or {}).get("unique_reviews_with_aspects", 0) for r in records
            ),
        )

    def get_game_topics(
        self,
        game_id: uuid.UUID,
        model_version_key: str = "baseline",
        limit: int = 20,
        include_outliers: bool = False,
    ) -> GameTopicsData:
        """Fetch discovered topics and prevalence statistics for a game."""
        game = self.session.get(Game, game_id)
        if not game:
            raise GameNotFoundError(str(game_id))

        # Query latest aggregate record containing topic summary
        records = self.analytics_repo.get_timeline(
            game_id=game_id,
            period_type="month",
            model_version_key=model_version_key,
        )
        if not records:
            # Fall back to week if month is not computed
            records = self.analytics_repo.get_timeline(
                game_id=game_id,
                period_type="week",
                model_version_key=model_version_key,
            )

        merged_topics: dict[str, dict[str, Any]] = {}
        total_assigned = 0
        total_outliers = 0

        for r in records:
            top_sum = r.topic_summary or {}
            for item in top_sum.get("topics", []):
                key = item["topic_key"]
                if key not in merged_topics:
                    merged_topics[key] = {
                        "topic_key": key,
                        "label": item.get("label", key),
                        "review_count": 0,
                        "scores": [],
                        "is_outlier": item.get("is_outlier", False),
                        "keywords": item.get("keywords", []),
                    }
                merged_topics[key]["review_count"] += item.get("review_count", 0)
                if "avg_score" in item:
                    merged_topics[key]["scores"].append(item["avg_score"])

            total_assigned += top_sum.get("total_assigned_reviews", 0)
            total_outliers += top_sum.get("outlier_count", 0)

        topic_points: list[TopicSummaryPoint] = []
        for key, item in merged_topics.items():
            if not include_outliers and item["is_outlier"]:
                continue

            r_c = item["review_count"]
            scores = item["scores"]
            avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0
            prev = round(r_c / total_assigned, 4) if total_assigned > 0 else 0.0

            topic_points.append(
                TopicSummaryPoint(
                    topic_key=key,
                    label=item["label"],
                    review_count=r_c,
                    prevalence=prev,
                    avg_score=avg_score,
                    is_outlier=item["is_outlier"],
                    keywords=item["keywords"],
                )
            )

        topic_points.sort(key=lambda x: x.review_count, reverse=True)
        outlier_rate = round(total_outliers / total_assigned, 4) if total_assigned > 0 else 0.0

        return GameTopicsData(
            game_id=game_id,
            model_version=model_version_key,
            topics=topic_points[:limit],
            total_assigned_reviews=total_assigned,
            outlier_count=total_outliers,
            outlier_rate=outlier_rate,
        )
