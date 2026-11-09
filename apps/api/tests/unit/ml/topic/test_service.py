"""Unit tests for TopicService domain workflows and persistence."""

import uuid
from unittest.mock import MagicMock

import pytest

from app.ml.topic.models import NMFTopicModel
from app.ml.topic.pipeline import InsufficientCorpusError
from app.models.game import Game
from app.models.review import Review
from app.models.topic import Topic
from app.repositories.topic import TopicRepository
from app.services.topic_service import TopicService


def test_build_corpus_insufficient_reviews_raises() -> None:
    mock_session = MagicMock()
    mock_repo = MagicMock(spec=TopicRepository)

    # Return only 2 reviews when min_corpus_size is 25
    r1 = Review(
        id=uuid.uuid4(), review_text="Great game with deep lore and characters.", language="en"
    )
    r2 = Review(
        id=uuid.uuid4(), review_text="Terrible performance and constant stuttering.", language="en"
    )
    mock_session.scalars.return_value.all.return_value = [r1, r2]
    mock_session.get.return_value = Game(
        id=uuid.uuid4(), steam_app_id=1091500, name="Cyberpunk 2077"
    )

    service = TopicService(mock_session, topic_repo=mock_repo)

    with pytest.raises(InsufficientCorpusError) as exc:
        service.build_corpus_for_game(
            game_id=uuid.uuid4(),
            language="en",
            min_corpus_size=25,
        )
    assert "minimum threshold of 25" in str(exc.value)


def test_fit_and_persist_topics() -> None:
    mock_session = MagicMock()
    mock_repo = MagicMock(spec=TopicRepository)

    # Create 30 mock reviews
    mock_reviews = [
        Review(
            id=uuid.uuid4(),
            review_text=f"Combat and gunplay mechanics review number {i} with good depth.",
            language="en",
            voted_up=True,
        )
        for i in range(15)
    ] + [
        Review(
            id=uuid.uuid4(),
            review_text=f"Performance fps drops and stuttering review number {i} to fix.",
            language="en",
            voted_up=False,
        )
        for i in range(15)
    ]
    mock_session.scalars.return_value.all.return_value = mock_reviews

    ml_model_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()
    game_id = uuid.uuid4()

    # Mock persisted Topic entities returned by bulk_create_topics
    t0_id = uuid.uuid4()
    t1_id = uuid.uuid4()
    mock_repo.bulk_create_topics.return_value = [
        Topic(id=t0_id, topic_key="test-topic_topic_0", label="Combat Mechanics"),
        Topic(id=t1_id, topic_key="test-topic_topic_1", label="Performance & FPS"),
    ]
    mock_repo.bulk_assign_review_topics.return_value = []

    service = TopicService(mock_session, topic_repo=mock_repo)
    model = NMFTopicModel(model_key="test-topic", num_topics=2, random_seed=42)

    topics, assignments = service.fit_and_persist_topics(
        game_id=game_id,
        ml_model_id=ml_model_id,
        pipeline_run_id=pipeline_run_id,
        model=model,
        language="en",
        min_corpus_size=20,
    )

    assert mock_repo.bulk_create_topics.called
    assert mock_repo.bulk_assign_review_topics.called
    assert len(topics) == 2
