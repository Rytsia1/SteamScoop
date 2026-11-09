"""Unit tests for ABSAService domain execution and AspectPrediction persistence."""

import uuid
from unittest.mock import MagicMock

from app.ml.absa.classifier import SentenceGroundedTfidfABSA
from app.ml.absa.schemas import (
    ABSAPredictionOutput,
    AspectPredictionItem,
)
from app.ml.taxonomy import AspectKey, SentimentLabel
from app.models.aspect import Aspect
from app.models.review import Review
from app.repositories.aspect import AspectRepository
from app.services.absa_service import ABSAService


def test_ensure_taxonomy_seeded() -> None:
    mock_session = MagicMock()
    mock_repo = MagicMock(spec=AspectRepository)
    mock_repo.get_all_active.return_value = []

    service = ABSAService(mock_session, aspect_repo=mock_repo)
    aspect_map = service.ensure_taxonomy_seeded()

    assert len(aspect_map) == 12
    for ak in AspectKey:
        assert ak.value in aspect_map
    assert mock_session.commit.called


def test_predict_and_persist_for_reviews() -> None:
    mock_session = MagicMock()
    mock_repo = MagicMock(spec=AspectRepository)

    # Mock taxonomy aspect entities
    gameplay_id = uuid.uuid4()
    perf_id = uuid.uuid4()
    gameplay_aspect = Aspect(
        id=gameplay_id, aspect_key=AspectKey.GAMEPLAY.value, display_name="Gameplay"
    )
    perf_aspect = Aspect(
        id=perf_id, aspect_key=AspectKey.PERFORMANCE.value, display_name="Performance"
    )
    mock_repo.get_all_active.return_value = [gameplay_aspect, perf_aspect]

    # Mock reviews
    r1_id = uuid.uuid4()
    r2_id = uuid.uuid4()
    r1 = Review(id=r1_id, review_text="Combat mechanics feel crisp and fluid.", language="en")
    r2 = Review(id=r2_id, review_text="Yes masterpiece.", language="en")
    mock_session.scalars.return_value.all.return_value = [r1, r2]

    # Mock model
    mock_model = MagicMock(spec=SentenceGroundedTfidfABSA)
    mock_model.predict_records.return_value = [
        ABSAPredictionOutput(
            review_id=str(r1_id),
            aspects=[
                AspectPredictionItem(
                    aspect=AspectKey.GAMEPLAY,
                    sentiment=SentimentLabel.POSITIVE,
                    confidence=0.88,
                    sentiment_confidence=0.92,
                    evidence_text="Combat mechanics feel crisp and fluid.",
                    start_offset=0,
                    end_offset=38,
                    probabilities={"positive": 0.92},
                )
            ],
            has_aspects=True,
            model_key="test-model",
            model_version="v1.0.0",
            latency_ms=1.2,
        ),
        ABSAPredictionOutput(
            review_id=str(r2_id),
            aspects=[],
            has_aspects=False,
            model_key="test-model",
            model_version="v1.0.0",
            latency_ms=0.5,
        ),
    ]

    service = ABSAService(mock_session, model=mock_model, aspect_repo=mock_repo)

    ml_model_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()

    preds = service.predict_and_persist_for_reviews(
        review_ids=[r1_id, r2_id],
        ml_model_id=ml_model_id,
        pipeline_run_id=pipeline_run_id,
    )

    assert len(preds) == 2
    # Verify create_prediction called for r1 gameplay aspect
    assert mock_repo.create_prediction.call_count == 1
    call_kwargs = mock_repo.create_prediction.call_args.kwargs
    assert call_kwargs["review_id"] == r1_id
    assert call_kwargs["aspect_id"] == gameplay_id
    assert call_kwargs["sentiment_label"] == SentimentLabel.POSITIVE.value
    assert call_kwargs["confidence"] == 0.88
    assert mock_session.commit.called
