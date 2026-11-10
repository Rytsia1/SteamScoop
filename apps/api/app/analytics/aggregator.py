"""Pure mathematical aggregation engine for SteamScoop.

Computes deterministic, version-aware analytics across review volume,
sentiment distribution, aspect-based sentiment, and topic prevalence.
No database I/O is performed in this module to guarantee testability and reproducibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class RawReviewInput:
    """Raw review data input for aggregation."""

    id: str
    voted_up: bool | None
    created_date: date


@dataclass(frozen=True)
class SentimentPredictionInput:
    """Sentiment prediction input for aggregation."""

    review_id: str
    label: str  # 'positive', 'negative', 'neutral'
    confidence: float | None = None
    is_abstained: bool = False


@dataclass(frozen=True)
class AspectPredictionInput:
    """Aspect prediction input for aggregation."""

    review_id: str
    aspect_key: str
    display_name: str
    sentiment_label: str  # 'positive', 'negative', 'neutral'
    confidence: float | None = None


@dataclass(frozen=True)
class TopicAssignmentInput:
    """Topic assignment input for aggregation."""

    review_id: str
    topic_key: str
    label: str
    score: float | None = None
    is_primary: bool = True
    is_outlier: bool = False
    keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BucketMetricsResult:
    """Calculated metric aggregates for a discrete time bucket."""

    period_type: str
    period_start: date
    period_end: date
    model_version_key: str

    review_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    unclassified_count: int

    steam_recommended_count: int
    steam_not_recommended_count: int

    sentiment_score: Decimal | None
    aspect_summary: dict[str, Any]
    topic_summary: dict[str, Any]

    # Explicit rates and denominators
    classified_count: int
    positive_rate: float
    negative_rate: float
    neutral_rate: float
    coverage_rate: float
    unclassified_rate: float
    steam_recommendation_rate: float | None


class AnalyticsAggregator:
    """Pure aggregation engine computing game analytics with explicit denominators."""

    @staticmethod
    def generate_period_buckets(
        min_date: date,
        max_date: date,
        period_type: str,
    ) -> list[tuple[date, date]]:
        """Generate contiguous, non-overlapping [period_start, period_end) bucket dates."""
        if min_date > max_date:
            return []

        buckets: list[tuple[date, date]] = []

        if period_type == "day":
            curr = min_date
            while curr <= max_date:
                nxt = curr + timedelta(days=1)
                buckets.append((curr, nxt))
                curr = nxt

        elif period_type == "week":
            # Align to Monday of the starting week
            start_monday = min_date - timedelta(days=min_date.weekday())
            curr = start_monday
            while curr <= max_date:
                nxt = curr + timedelta(days=7)
                buckets.append((curr, nxt))
                curr = nxt

        elif period_type == "month":
            # Align to 1st of starting month
            curr_year = min_date.year
            curr_month = min_date.month
            curr = date(curr_year, curr_month, 1)

            while curr <= max_date:
                # Next month
                if curr_month == 12:
                    nxt = date(curr_year + 1, 1, 1)
                    curr_year += 1
                    curr_month = 1
                else:
                    nxt = date(curr_year, curr_month + 1, 1)
                    curr_month += 1
                buckets.append((curr, nxt))
                curr = nxt

        else:
            raise ValueError(
                f"Unsupported period_type '{period_type}'. Must be 'day', 'week', or 'month'."
            )

        return buckets

    @classmethod
    def compute_bucket_metrics(
        cls,
        period_type: str,
        period_start: date,
        period_end: date,
        model_version_key: str,
        reviews: list[RawReviewInput],
        sentiment_predictions: dict[str, SentimentPredictionInput],
        aspect_predictions: list[AspectPredictionInput],
        topic_assignments: list[TopicAssignmentInput],
    ) -> BucketMetricsResult:
        """Compute all aggregate metrics for a single time bucket with explicit denominators.

        Mathematical Definitions:
        - total_reviews (N): count of reviews in [period_start, period_end)
        - steam_recommended_count: reviews where voted_up is True
        - steam_not_recommended_count: reviews where voted_up is False
        - classified_count (C): positive_count + negative_count + neutral_count
        - unclassified_count (U): total_reviews - classified_count
        - sentiment_score: (pos - neg) / classified_count in [-1.0, 1.0] (None if C == 0)
        - positive_rate: positive_count / classified_count (0.0 if C == 0)
        - negative_rate: negative_count / classified_count (0.0 if C == 0)
        - neutral_rate: neutral_count / classified_count (0.0 if C == 0)
        - coverage_rate: classified_count / total_reviews (0.0 if N == 0)
        - unclassified_rate: unclassified_count / total_reviews (0.0 if N == 0)
        - aspect_sentiment_score: (pos_mentions - neg_mentions) / total_mentions in [-1.0, 1.0]
        - topic_prevalence: topic_reviews / total_assigned_reviews
        """
        review_count = len(reviews)

        # 1. Steam Recommendation Counts
        steam_rec = 0
        steam_not_rec = 0
        for r in reviews:
            if r.voted_up is True:
                steam_rec += 1
            elif r.voted_up is False:
                steam_not_rec += 1

        rec_sum = steam_rec + steam_not_rec
        steam_rec_rate = (steam_rec / rec_sum) if rec_sum > 0 else None

        # 2. Sentiment Counts & Distribution
        pos_count = 0
        neg_count = 0
        neu_count = 0

        for r in reviews:
            pred = sentiment_predictions.get(r.id)
            if pred and not pred.is_abstained:
                lbl = pred.label.lower()
                if lbl == "positive":
                    pos_count += 1
                elif lbl == "negative":
                    neg_count += 1
                elif lbl == "neutral":
                    neu_count += 1

        classified_count = pos_count + neg_count + neu_count
        unclassified_count = max(0, review_count - classified_count)

        if classified_count > 0:
            raw_score = (pos_count - neg_count) / classified_count
            sentiment_score = Decimal(f"{raw_score:.5f}")
            pos_rate = round(pos_count / classified_count, 4)
            neg_rate = round(neg_count / classified_count, 4)
            neu_rate = round(neu_count / classified_count, 4)
        else:
            sentiment_score = None
            pos_rate = 0.0
            neg_rate = 0.0
            neu_rate = 0.0

        coverage_rate = round(classified_count / review_count, 4) if review_count > 0 else 0.0
        unclassified_rate = round(unclassified_count / review_count, 4) if review_count > 0 else 0.0

        # 3. Aspect Aggregations
        aspect_buckets: dict[str, dict[str, Any]] = {}
        unique_reviews_with_aspects: set[str] = set()

        for asp in aspect_predictions:
            unique_reviews_with_aspects.add(asp.review_id)
            if asp.aspect_key not in aspect_buckets:
                aspect_buckets[asp.aspect_key] = {
                    "aspect_key": asp.aspect_key,
                    "display_name": asp.display_name,
                    "mention_count": 0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                }
            item = aspect_buckets[asp.aspect_key]
            item["mention_count"] += 1
            s_lbl = asp.sentiment_label.lower()
            if s_lbl == "positive":
                item["positive_count"] += 1
            elif s_lbl == "negative":
                item["negative_count"] += 1
            elif s_lbl == "neutral":
                item["neutral_count"] += 1

        aspect_items: list[dict[str, Any]] = []
        for key, item in aspect_buckets.items():
            m_count = item["mention_count"]
            p_c = item["positive_count"]
            n_c = item["negative_count"]
            u_c = item["neutral_count"]

            asp_score = round((p_c - n_c) / m_count, 4) if m_count > 0 else 0.0
            asp_p_rate = round(p_c / m_count, 4) if m_count > 0 else 0.0
            asp_n_rate = round(n_c / m_count, 4) if m_count > 0 else 0.0
            asp_u_rate = round(u_c / m_count, 4) if m_count > 0 else 0.0
            prevalence = round(m_count / review_count, 4) if review_count > 0 else 0.0

            aspect_items.append(
                {
                    "aspect_key": key,
                    "display_name": item["display_name"],
                    "mention_count": m_count,
                    "positive_count": p_c,
                    "negative_count": n_c,
                    "neutral_count": u_c,
                    "sentiment_score": asp_score,
                    "positive_rate": asp_p_rate,
                    "negative_rate": asp_n_rate,
                    "neutral_rate": asp_u_rate,
                    "prevalence": prevalence,
                }
            )

        # Sort aspects by mention_count descending
        aspect_items.sort(key=lambda x: int(x["mention_count"]), reverse=True)

        aspect_summary = {
            "aspects": aspect_items,
            "total_aspect_mentions": len(aspect_predictions),
            "unique_reviews_with_aspects": len(unique_reviews_with_aspects),
            "methodology": {
                "sentiment_formula": "(positive - negative) / mention_count",
                "denominator": "mention_count",
                "scale": "[-1.0, 1.0]",
            },
        }

        # 4. Topic Aggregations
        topic_buckets: dict[str, dict[str, Any]] = {}
        total_assigned_reviews = 0
        outlier_count = 0

        # Filter to primary assignments for canonical prevalence distribution
        primary_assignments = [ta for ta in topic_assignments if ta.is_primary]
        for ta in primary_assignments:
            total_assigned_reviews += 1
            if ta.is_outlier:
                outlier_count += 1

            if ta.topic_key not in topic_buckets:
                topic_buckets[ta.topic_key] = {
                    "topic_key": ta.topic_key,
                    "label": ta.label,
                    "review_count": 0,
                    "scores": [],
                    "is_outlier": ta.is_outlier,
                    "keywords": ta.keywords,
                }
            t_item = topic_buckets[ta.topic_key]
            t_item["review_count"] += 1
            if ta.score is not None:
                t_item["scores"].append(ta.score)

        topic_items: list[dict[str, Any]] = []
        for key, item in topic_buckets.items():
            r_c = item["review_count"]
            scores = item["scores"]
            avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0
            prev = round(r_c / total_assigned_reviews, 4) if total_assigned_reviews > 0 else 0.0

            topic_items.append(
                {
                    "topic_key": key,
                    "label": item["label"],
                    "review_count": r_c,
                    "prevalence": prev,
                    "avg_score": avg_score,
                    "is_outlier": item["is_outlier"],
                    "keywords": item["keywords"],
                }
            )

        # Sort topics by review_count descending
        topic_items.sort(key=lambda x: int(x["review_count"]), reverse=True)
        outlier_rate = (
            round(outlier_count / total_assigned_reviews, 4) if total_assigned_reviews > 0 else 0.0
        )

        topic_summary = {
            "topics": topic_items,
            "total_assigned_reviews": total_assigned_reviews,
            "outlier_count": outlier_count,
            "outlier_rate": outlier_rate,
            "methodology": {
                "assignment_rule": "primary_assignments_only",
                "prevalence_denominator": "total_assigned_reviews",
            },
        }

        return BucketMetricsResult(
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            model_version_key=model_version_key,
            review_count=review_count,
            positive_count=pos_count,
            negative_count=neg_count,
            neutral_count=neu_count,
            unclassified_count=unclassified_count,
            steam_recommended_count=steam_rec,
            steam_not_recommended_count=steam_not_rec,
            sentiment_score=sentiment_score,
            aspect_summary=aspect_summary,
            topic_summary=topic_summary,
            classified_count=classified_count,
            positive_rate=pos_rate,
            negative_rate=neg_rate,
            neutral_rate=neu_rate,
            coverage_rate=coverage_rate,
            unclassified_rate=unclassified_rate,
            steam_recommendation_rate=steam_rec_rate,
        )
