"""Unit tests validating mathematical correctness and explicit denominators of AnalyticsAggregator."""

from datetime import date
from decimal import Decimal

import pytest

from app.analytics.aggregator import (
    AnalyticsAggregator,
    AspectPredictionInput,
    RawReviewInput,
    SentimentPredictionInput,
    TopicAssignmentInput,
)


def test_generate_period_buckets_day() -> None:
    """Validate daily contiguous bucket generation."""
    min_d = date(2026, 10, 1)
    max_d = date(2026, 10, 3)

    buckets = AnalyticsAggregator.generate_period_buckets(min_d, max_d, "day")

    assert len(buckets) == 3
    assert buckets[0] == (date(2026, 10, 1), date(2026, 10, 2))
    assert buckets[1] == (date(2026, 10, 2), date(2026, 10, 3))
    assert buckets[2] == (date(2026, 10, 3), date(2026, 10, 4))


def test_generate_period_buckets_week() -> None:
    """Validate weekly bucket generation aligning on Mondays."""
    # 2026-10-07 is Wednesday; start Monday is 2026-10-05
    min_d = date(2026, 10, 7)
    max_d = date(2026, 10, 14)

    buckets = AnalyticsAggregator.generate_period_buckets(min_d, max_d, "week")

    assert len(buckets) == 2
    assert buckets[0] == (date(2026, 10, 5), date(2026, 10, 12))
    assert buckets[1] == (date(2026, 10, 12), date(2026, 10, 19))


def test_generate_period_buckets_month() -> None:
    """Validate monthly bucket generation aligning on 1st of each month."""
    min_d = date(2026, 10, 15)
    max_d = date(2026, 12, 5)

    buckets = AnalyticsAggregator.generate_period_buckets(min_d, max_d, "month")

    assert len(buckets) == 3
    assert buckets[0] == (date(2026, 10, 1), date(2026, 11, 1))
    assert buckets[1] == (date(2026, 11, 1), date(2026, 12, 1))
    assert buckets[2] == (date(2026, 12, 1), date(2027, 1, 1))


def test_generate_period_buckets_invalid_dates() -> None:
    """Validate empty result when min_date > max_date."""
    buckets = AnalyticsAggregator.generate_period_buckets(
        date(2026, 10, 10), date(2026, 10, 5), "day"
    )
    assert buckets == []


def test_compute_bucket_metrics_against_manual_calculation() -> None:
    """Validate all metrics against hand-calculated, deterministic ground truth values."""
    # Scenario: 10 raw reviews in bucket [2026-10-05, 2026-10-12)
    # Steam: 6 voted_up=True, 3 voted_up=False, 1 voted_up=None
    # Sentiment:
    #   r1..r5: positive (5)
    #   r6..r7: negative (2)
    #   r8:     neutral  (1)
    #   r9:     abstained (is_abstained=True)
    #   r10:    unpredicted (missing)
    # Total classified = 5 + 2 + 1 = 8.
    # Total unclassified = 10 - 8 = 2.
    # Expected sentiment_score = (5 - 2) / 8 = 3/8 = +0.37500.

    reviews = [
        RawReviewInput(id=f"r{i}", voted_up=True, created_date=date(2026, 10, 6))
        for i in range(1, 7)
    ]
    reviews.extend(
        [
            RawReviewInput(id=f"r{i}", voted_up=False, created_date=date(2026, 10, 7))
            for i in range(7, 10)
        ]
    )
    reviews.append(RawReviewInput(id="r10", voted_up=None, created_date=date(2026, 10, 8)))

    assert len(reviews) == 10

    sentiments = {
        "r1": SentimentPredictionInput("r1", "positive", 0.95),
        "r2": SentimentPredictionInput("r2", "positive", 0.90),
        "r3": SentimentPredictionInput("r3", "positive", 0.85),
        "r4": SentimentPredictionInput("r4", "positive", 0.80),
        "r5": SentimentPredictionInput("r5", "positive", 0.75),
        "r6": SentimentPredictionInput("r6", "negative", 0.92),
        "r7": SentimentPredictionInput("r7", "negative", 0.88),
        "r8": SentimentPredictionInput("r8", "neutral", 0.70),
        "r9": SentimentPredictionInput("r9", "positive", 0.40, is_abstained=True),
        # r10 not in dictionary
    }

    # Aspects:
    # "gameplay": 4 mentions (3 pos, 1 neg). Score = (3 - 1) / 4 = +0.5000.
    # "performance": 3 mentions (1 pos, 2 neg). Score = (1 - 2) / 3 = -0.3333.
    aspects = [
        AspectPredictionInput("r1", "gameplay", "Gameplay", "positive", 0.85),
        AspectPredictionInput("r2", "gameplay", "Gameplay", "positive", 0.80),
        AspectPredictionInput("r3", "gameplay", "Gameplay", "positive", 0.75),
        AspectPredictionInput("r6", "gameplay", "Gameplay", "negative", 0.90),
        AspectPredictionInput("r6", "performance", "Performance", "negative", 0.95),
        AspectPredictionInput("r7", "performance", "Performance", "negative", 0.85),
        AspectPredictionInput("r4", "performance", "Performance", "positive", 0.70),
    ]

    # Topics:
    # 8 reviews assigned primary topics:
    # "combat": 5 reviews (r1..r5), avg_score = 0.80
    # "story": 2 reviews (r6..r7), avg_score = 0.65
    # "outlier": 1 review (r8), is_outlier=True, score=0.30
    topics = [
        TopicAssignmentInput("r1", "combat", "Combat", 0.85, is_primary=True),
        TopicAssignmentInput("r2", "combat", "Combat", 0.80, is_primary=True),
        TopicAssignmentInput("r3", "combat", "Combat", 0.80, is_primary=True),
        TopicAssignmentInput("r4", "combat", "Combat", 0.75, is_primary=True),
        TopicAssignmentInput("r5", "combat", "Combat", 0.80, is_primary=True),
        TopicAssignmentInput("r6", "story", "Story", 0.70, is_primary=True),
        TopicAssignmentInput("r7", "story", "Story", 0.60, is_primary=True),
        TopicAssignmentInput("r8", "cluster_-1", "Outlier", 0.30, is_primary=True, is_outlier=True),
        # Secondary topic assignment for r1 (should not distort primary topic counts)
        TopicAssignmentInput("r1", "story", "Story", 0.40, is_primary=False),
    ]

    res = AnalyticsAggregator.compute_bucket_metrics(
        period_type="week",
        period_start=date(2026, 10, 5),
        period_end=date(2026, 10, 12),
        model_version_key="sentiment:v1.0.0",
        reviews=reviews,
        sentiment_predictions=sentiments,
        aspect_predictions=aspects,
        topic_assignments=topics,
    )

    # 1. Review Volume verification
    assert res.review_count == 10
    assert res.steam_recommended_count == 6
    assert res.steam_not_recommended_count == 3
    # Denominator for steam recommendation rate = 6 + 3 = 9
    assert res.steam_recommendation_rate == pytest.approx(6 / 9, abs=1e-4)

    # 2. Sentiment Counts & Formula verification
    assert res.positive_count == 5
    assert res.negative_count == 2
    assert res.neutral_count == 1
    assert res.classified_count == 8
    assert res.unclassified_count == 2
    assert res.sentiment_score == Decimal("0.37500")

    # Rates over classified reviews (denominator = 8)
    assert res.positive_rate == pytest.approx(5 / 8, abs=1e-4)  # 0.625
    assert res.negative_rate == pytest.approx(2 / 8, abs=1e-4)  # 0.250
    assert res.neutral_rate == pytest.approx(1 / 8, abs=1e-4)  # 0.125

    # Coverage over total reviews (denominator = 10)
    assert res.coverage_rate == pytest.approx(8 / 10, abs=1e-4)  # 0.800
    assert res.unclassified_rate == pytest.approx(2 / 10, abs=1e-4)  # 0.200

    # 3. Aspect Aggregations verification
    asp_summary = res.aspect_summary
    assert asp_summary["total_aspect_mentions"] == 7
    # Unique reviews with aspect mentions: r1, r2, r3, r4, r6, r7 -> 6 reviews
    assert asp_summary["unique_reviews_with_aspects"] == 6

    aspect_map = {a["aspect_key"]: a for a in asp_summary["aspects"]}
    assert "gameplay" in aspect_map
    gameplay = aspect_map["gameplay"]
    assert gameplay["mention_count"] == 4
    assert gameplay["positive_count"] == 3
    assert gameplay["negative_count"] == 1
    assert gameplay["neutral_count"] == 0
    assert gameplay["sentiment_score"] == pytest.approx(0.5000, abs=1e-4)
    assert gameplay["positive_rate"] == pytest.approx(0.7500, abs=1e-4)
    assert gameplay["negative_rate"] == pytest.approx(0.2500, abs=1e-4)
    assert gameplay["prevalence"] == pytest.approx(4 / 10, abs=1e-4)

    assert "performance" in aspect_map
    perf = aspect_map["performance"]
    assert perf["mention_count"] == 3
    assert perf["positive_count"] == 1
    assert perf["negative_count"] == 2
    assert perf["sentiment_score"] == pytest.approx(-0.3333, abs=1e-4)
    assert perf["positive_rate"] == pytest.approx(1 / 3, abs=1e-4)
    assert perf["negative_rate"] == pytest.approx(2 / 3, abs=1e-4)
    assert perf["prevalence"] == pytest.approx(3 / 10, abs=1e-4)

    # 4. Topic Aggregations verification
    top_summary = res.topic_summary
    assert top_summary["total_assigned_reviews"] == 8
    assert top_summary["outlier_count"] == 1
    assert top_summary["outlier_rate"] == pytest.approx(1 / 8, abs=1e-4)

    topic_map = {t["topic_key"]: t for t in top_summary["topics"]}
    assert "combat" in topic_map
    combat = topic_map["combat"]
    assert combat["review_count"] == 5
    assert combat["prevalence"] == pytest.approx(5 / 8, abs=1e-4)
    assert combat["avg_score"] == pytest.approx(0.8000, abs=1e-4)
    assert combat["is_outlier"] is False

    assert "story" in topic_map
    story = topic_map["story"]
    assert story["review_count"] == 2
    assert story["prevalence"] == pytest.approx(2 / 8, abs=1e-4)
    assert story["avg_score"] == pytest.approx(0.6500, abs=1e-4)


def test_compute_bucket_metrics_zero_reviews() -> None:
    """Validate graceful handling of empty review period."""
    res = AnalyticsAggregator.compute_bucket_metrics(
        period_type="day",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 2),
        model_version_key="baseline",
        reviews=[],
        sentiment_predictions={},
        aspect_predictions=[],
        topic_assignments=[],
    )

    assert res.review_count == 0
    assert res.positive_count == 0
    assert res.negative_count == 0
    assert res.neutral_count == 0
    assert res.classified_count == 0
    assert res.unclassified_count == 0
    assert res.sentiment_score is None
    assert res.positive_rate == 0.0
    assert res.coverage_rate == 0.0
    assert res.steam_recommendation_rate is None
    assert res.aspect_summary["total_aspect_mentions"] == 0
    assert res.topic_summary["total_assigned_reviews"] == 0


def test_compute_bucket_metrics_all_unclassified() -> None:
    """Validate behavior when reviews have no predictions or all are abstained."""
    reviews = [
        RawReviewInput(id="r1", voted_up=True, created_date=date(2026, 10, 1)),
        RawReviewInput(id="r2", voted_up=False, created_date=date(2026, 10, 1)),
    ]
    # Abstained prediction for r1
    sentiments = {
        "r1": SentimentPredictionInput("r1", "positive", 0.45, is_abstained=True),
    }

    res = AnalyticsAggregator.compute_bucket_metrics(
        period_type="day",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 2),
        model_version_key="baseline",
        reviews=reviews,
        sentiment_predictions=sentiments,
        aspect_predictions=[],
        topic_assignments=[],
    )

    assert res.review_count == 2
    assert res.classified_count == 0
    assert res.unclassified_count == 2
    assert res.sentiment_score is None
    assert res.coverage_rate == 0.0
    assert res.unclassified_rate == 1.0


def test_database_check_constraints_satisfied() -> None:
    """Validate that computed aggregates satisfy PostgreSQL table check constraints."""
    reviews = [
        RawReviewInput(id="r1", voted_up=True, created_date=date(2026, 10, 1)),
        RawReviewInput(id="r2", voted_up=False, created_date=date(2026, 10, 1)),
        RawReviewInput(id="r3", voted_up=None, created_date=date(2026, 10, 1)),
    ]
    sentiments = {
        "r1": SentimentPredictionInput("r1", "positive", 0.9),
        "r2": SentimentPredictionInput("r2", "negative", 0.9),
    }

    res = AnalyticsAggregator.compute_bucket_metrics(
        period_type="day",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 2),
        model_version_key="baseline",
        reviews=reviews,
        sentiment_predictions=sentiments,
        aspect_predictions=[],
        topic_assignments=[],
    )

    # ck_game_analytic_counts_non_negative
    assert res.review_count >= 0
    assert res.positive_count >= 0
    assert res.negative_count >= 0
    assert res.neutral_count >= 0
    assert res.steam_recommended_count >= 0
    assert res.steam_not_recommended_count >= 0

    # ck_game_analytic_sentiment_counts_sum
    assert res.positive_count + res.negative_count + res.neutral_count <= res.review_count

    # ck_game_analytic_steam_rec_sum
    assert res.steam_recommended_count + res.steam_not_recommended_count <= res.review_count

    # ck_game_analytic_sentiment_score_range
    if res.sentiment_score is not None:
        assert -1.0 <= float(res.sentiment_score) <= 1.0
