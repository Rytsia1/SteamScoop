"""Unit tests for TopicTrainingPipeline and corpus filtering rules."""

from pathlib import Path

import pytest

from app.ml.topic.pipeline import InsufficientCorpusError, TopicTrainingPipeline
from app.ml.topic.schemas import CorpusFilterConfig, RawDocument


def test_build_game_corpus_filters_and_deduplication() -> None:
    pipeline = TopicTrainingPipeline()
    raw = [
        {
            "steam_app_id": 1091500,
            "language": "en",
            "review_text": "Valid review with sufficient length.",
            "review_id": "r1",
        },
        {
            "steam_app_id": 1091500,
            "language": "en",
            "review_text": "Valid review with sufficient length.",
            "review_id": "r2",
        },  # duplicate
        {
            "steam_app_id": 1091500,
            "language": "en",
            "review_text": "Too short",
            "review_id": "r3",
        },  # too short
        {
            "steam_app_id": 555555,
            "language": "en",
            "review_text": "Different app id entirely.",
            "review_id": "r4",
        },  # wrong app
        {
            "steam_app_id": 1091500,
            "language": "ru",
            "review_text": "Russian review text here.",
            "review_id": "r5",
        },  # wrong lang
    ]

    # With min_corpus_size=1, should return exactly 1 document
    config = CorpusFilterConfig(
        steam_app_id=1091500, language="en", min_corpus_size=1, deduplicate=True
    )
    corpus = pipeline.build_game_corpus(raw, config)
    assert len(corpus) == 1
    assert corpus[0].review_id == "r1"


def test_insufficient_corpus_error() -> None:
    pipeline = TopicTrainingPipeline()
    raw = [
        {
            "steam_app_id": 1091500,
            "language": "en",
            "review_text": "Just one valid review here.",
            "review_id": "r1",
        }
    ]
    config = CorpusFilterConfig(steam_app_id=1091500, language="en", min_corpus_size=25)

    with pytest.raises(InsufficientCorpusError) as exc_info:
        pipeline.build_game_corpus(raw, config)
    assert "below the minimum threshold of 25" in str(exc_info.value)


def test_compare_candidate_models_and_save_artifacts(tmp_path: Path) -> None:
    pipeline = TopicTrainingPipeline()
    docs = [
        RawDocument(review_id=str(i), text=f"Combat gunplay and weapons review number {i}")
        for i in range(15)
    ] + [
        RawDocument(review_id=str(i + 15), text=f"Performance fps stuttering crashes number {i}")
        for i in range(15)
    ]

    reports, winning_key, winning_model = pipeline.compare_candidate_models(
        documents=docs,
        steam_app_id=1091500,
        num_topics=2,
        random_seed=42,
    )

    assert winning_key in ["nmf", "lda", "semantic_clustering"]
    assert len(reports) == 3
    assert winning_model.is_fitted

    # Test saving artifacts
    out_dir = tmp_path / "artifacts"
    manifest_file = pipeline.save_artifacts(winning_model, reports[winning_key], out_dir)
    assert manifest_file.exists()
    assert (out_dir / "model.joblib").exists()
