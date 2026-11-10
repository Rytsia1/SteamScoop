"""Unit tests for production ML batch inference service and item-level tracking."""

from typing import Any
from unittest.mock import MagicMock

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.sentiment.schemas import SentimentPredictionOutput
from app.models.aspect import AspectPrediction
from app.models.ml import PipelineRunItem
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.services.inference_pipeline_service import InferencePipelineService


def test_sentiment_batch_inference_lifecycle(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Validate sentiment batch inference, prediction persistence, and item outcome tracking."""
    game = sample_catalog["game1"]
    service = InferencePipelineService(session=db_session)

    run = service.run_sentiment_batch_inference(game_id=game.id, batch_size=5)

    assert run.id is not None
    assert run.pipeline_type == "sentiment"
    assert run.status == "succeeded"
    assert run.input_count >= 1
    assert run.success_count >= 1
    assert run.failure_count == 0

    # Verify predictions in DB
    stmt = select(SentimentPrediction).where(
        SentimentPrediction.pipeline_run_id == run.id,
        SentimentPrediction.is_current.is_(True),
    )
    predictions = list(db_session.scalars(stmt).all())
    assert len(predictions) == run.success_count

    for p in predictions:
        assert p.label in ["positive", "negative", "neutral"]
        assert p.confidence is not None
        assert float(p.confidence) >= 0.0

    # Verify item-level outcomes
    item_stmt = select(PipelineRunItem).where(PipelineRunItem.pipeline_run_id == run.id)
    items = list(db_session.scalars(item_stmt).all())
    assert len(items) == run.success_count
    assert all(it.status == "succeeded" for it in items)


def test_sentiment_batch_inference_fault_isolation(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Validate item-level fault isolation when model output is missing for an item."""
    game = sample_catalog["game1"]
    rev1 = sample_catalog["review1"]

    rev2 = Review(
        game_id=game.id,
        steam_review_id=99990001,
        language="en",
        review_text="This is an edge-case review to test fault isolation.",
        voted_up=True,
        votes_up=0,
        votes_funny=0,
        comment_count=0,
    )
    db_session.add(rev2)
    db_session.flush()

    # Mock classifier that only returns prediction for rev1, omitting rev2
    mock_classifier = MagicMock()
    mock_classifier.is_fitted = True
    mock_classifier.predict_records.return_value = [
        SentimentPredictionOutput(
            task="sentiment",
            review_id=str(rev1.id),
            label="positive",
            confidence=0.92,
            probabilities={"positive": 0.92, "negative": 0.05, "neutral": 0.03},
            is_abstained=False,
            model_key="mock-model",
            model_version="v1.0.0",
        )
    ]

    service = InferencePipelineService(session=db_session, sentiment_model=mock_classifier)
    run = service.run_sentiment_batch_inference(
        game_id=game.id,
        review_ids=[rev1.id, rev2.id],
    )

    assert run.status == "succeeded"
    assert run.input_count == 2
    assert run.success_count == 1
    assert run.failure_count == 1

    # Inspect item outcomes
    failed_item = db_session.scalars(
        select(PipelineRunItem).where(
            PipelineRunItem.pipeline_run_id == run.id,
            PipelineRunItem.status == "failed",
        )
    ).first()

    assert failed_item is not None
    assert failed_item.review_id == rev2.id
    assert failed_item.error_code == "PREDICTION_MISSING"


def test_absa_batch_inference_lifecycle(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Validate ABSA batch inference, taxonomy resolution, and offset persistence."""
    game = sample_catalog["game1"]
    service = InferencePipelineService(session=db_session)

    run = service.run_absa_batch_inference(game_id=game.id)

    assert run.id is not None
    assert run.pipeline_type == "absa"
    assert run.status == "succeeded"

    # Verify aspect predictions
    stmt = select(AspectPrediction).where(AspectPrediction.pipeline_run_id == run.id)
    preds = list(db_session.scalars(stmt).all())
    assert len(preds) >= 1

    for p in preds:
        assert p.sentiment_label in ["positive", "negative", "neutral"]
        assert p.aspect_id is not None
        assert p.confidence is not None


def test_topic_batch_inference_insufficient_corpus(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Validate strict enforcement of minimum corpus size for topic modeling."""
    game = sample_catalog["game1"]
    service = InferencePipelineService(session=db_session)

    # Game has fewer than 25 reviews
    run = service.run_topic_batch_inference(game_id=game.id, min_corpus_size=25)

    assert run.pipeline_type == "topic"
    assert run.status == "failed"
    assert "below minimum required 25" in (run.error_summary or "")


def test_reprocess_failed_items(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """Validate reprocessing workflow for previously failed items."""
    game = sample_catalog["game1"]
    rev = sample_catalog["review1"]

    # 1. Run inference with a failing mock classifier
    failing_classifier = MagicMock()
    failing_classifier.is_fitted = True
    failing_classifier.predict_records.side_effect = RuntimeError("Temporary model error")

    service_failing = InferencePipelineService(
        session=db_session, sentiment_model=failing_classifier
    )
    failed_run = service_failing.run_sentiment_batch_inference(
        game_id=game.id,
        review_ids=[rev.id],
    )
    assert failed_run.failure_count == 1

    # 2. Reprocess failed items with working classifier
    service_working = InferencePipelineService(session=db_session)
    reprocessed_run = service_working.reprocess_failed_items(failed_run.id)

    assert reprocessed_run.status == "succeeded"
    assert reprocessed_run.success_count == 1
    assert reprocessed_run.failure_count == 0
