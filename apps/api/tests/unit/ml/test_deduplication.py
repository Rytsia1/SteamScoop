"""Unit tests for ReviewDeduplicator according to ML_SPECIFICATION.md Section 4.5."""

from app.ml.deduplication import DEDUPLICATION_VERSION, ReviewDeduplicator


def test_deduplicator_version() -> None:
    dedup = ReviewDeduplicator()
    assert dedup.version == DEDUPLICATION_VERSION


def test_exact_duplicate_detection() -> None:
    dedup = ReviewDeduplicator()
    reviews = [
        {"review_id": "r1", "normalized_text": "Fix the servers already! Game is broken."},
        {"review_id": "r2", "normalized_text": "Fix the servers already! Game is broken."},
    ]
    clusters = dedup.cluster_reviews(reviews)
    assert len(clusters) == 2
    assert clusters["r1"].group_id == clusters["r2"].group_id
    assert clusters["r1"].is_exact_duplicate is True
    assert clusters["r2"].is_exact_duplicate is True
    assert clusters["r1"].group_size == 2


def test_near_duplicate_clustering_via_jaccard() -> None:
    dedup = ReviewDeduplicator(near_duplicate_threshold=0.85)
    reviews = [
        {
            "review_id": "r1",
            "normalized_text": "Fix the servers already! Game is completely unplayable.",
        },
        # Slight variation: "The game" instead of "Game"
        {
            "review_id": "r2",
            "normalized_text": "Fix the servers already! The game is completely unplayable.",
        },
    ]
    clusters = dedup.cluster_reviews(reviews)
    assert clusters["r1"].group_id == clusters["r2"].group_id
    assert clusters["r1"].group_size == 2


def test_distinct_non_duplicate_reviews() -> None:
    dedup = ReviewDeduplicator()
    reviews = [
        {"review_id": "r1", "normalized_text": "Cyberpunk 2077 has amazing visuals and music."},
        {
            "review_id": "r2",
            "normalized_text": "Hades combat mechanics are crisp and voice acting is great.",
        },
    ]
    clusters = dedup.cluster_reviews(reviews)
    assert clusters["r1"].group_id != clusters["r2"].group_id
    assert clusters["r1"].group_size == 1
    assert clusters["r2"].group_size == 1
    assert clusters["r1"].is_exact_duplicate is False


def test_empty_input_handling() -> None:
    dedup = ReviewDeduplicator()
    assert dedup.cluster_reviews([]) == {}
