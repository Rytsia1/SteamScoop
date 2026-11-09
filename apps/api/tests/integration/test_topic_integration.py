"""Integration tests for Topic Modeling persistence, registry, and repository interactions."""

import pytest
from sqlalchemy.orm import Session

from app.ml.topic.models import NMFTopicModel
from app.ml.topic.pipeline import InsufficientCorpusError
from app.ml.topic.registry import TopicModelRegistryService
from app.models.game import Game
from app.models.ml import PipelineRun
from app.models.review import Review
from app.repositories.topic import TopicRepository
from app.services.topic_service import TopicService


def test_topic_database_integration_and_persistence(db_session: Session) -> None:
    # 1. Create a game and 30 reviews (15 combat, 15 performance)
    game = Game(
        steam_app_id=999200, name="Topic Test Game", catalog_status="indexed", is_active=True
    )
    db_session.add(game)
    db_session.flush()

    reviews: list[Review] = []
    for i in range(15):
        rev = Review(
            game_id=game.id,
            steam_review_id=998000 + i,
            review_text=f"Combat and gunplay mechanics review number {i}. Responsive dodging and crisp shooting.",
            language="en",
            voted_up=True,
        )
        reviews.append(rev)

    for i in range(15):
        rev = Review(
            game_id=game.id,
            steam_review_id=998100 + i,
            review_text=f"Severe performance stutter and fps drops number {i}. Low frame rate and frequent crashes.",
            language="en",
            voted_up=False,
        )
        reviews.append(rev)

    db_session.add_all(reviews)
    db_session.flush()

    # 2. Register Topic MLModel via TopicModelRegistryService
    registry = TopicModelRegistryService()
    manifest_data = {
        "model_key": "steamscoop-topic-nmf-test",
        "version": "v1.0.0",
        "task": "topic",
        "framework": "scikit-learn",
        "config": {"num_topics": 2, "random_seed": 42},
        "metrics": {"topic_diversity": 1.0, "npmi_coherence": 0.45},
        "release_gate": {"status": "APPROVED"},
        "topics": [],
    }
    ml_model = registry.sync_model_to_db(db_session, manifest_data, is_active=True)
    assert ml_model.is_active is True

    # 3. Create PipelineRun for topic execution
    pipeline_run = PipelineRun(
        pipeline_type="topic",
        status="running",
        game_id=game.id,
        ml_model_id=ml_model.id,
        input_count=len(reviews),
        success_count=0,
        failure_count=0,
    )
    db_session.add(pipeline_run)
    db_session.flush()

    # 4. Initialize TopicService and fit topic model
    topic_repo = TopicRepository(db_session)
    service = TopicService(db_session, topic_repo=topic_repo)
    model = NMFTopicModel(model_key="test-nmf-int", num_topics=2, random_seed=42)

    curation_map = {
        "test-nmf-int_topic_0": {
            "label": "Combat Mechanics & Gunplay",
            "description": "Analysis of weapon handling and gunplay feel.",
        },
        "test-nmf-int_topic_1": {
            "label": "Technical Stability & Performance",
            "description": "Discussion of PC frame rates and stability.",
        },
    }

    topics, assignments = service.fit_and_persist_topics(
        game_id=game.id,
        ml_model_id=ml_model.id,
        pipeline_run_id=pipeline_run.id,
        model=model,
        language="en",
        min_corpus_size=25,
        curation_map=curation_map,
    )

    assert len(topics) == 2
    assert len(assignments) == len(reviews)

    # 5. Verify database records via TopicRepository
    db_topics = topic_repo.get_topics_by_model(ml_model_id=ml_model.id)
    assert len(db_topics) == 2
    for t in db_topics:
        assert len(t.keywords) > 0
        assert len(t.representative_terms) > 0

    rev1_topics = topic_repo.get_review_topics_by_review(reviews[0].id)
    assert len(rev1_topics) >= 1
    assignment = rev1_topics[0]
    assert assignment.pipeline_run_id == pipeline_run.id
    assert assignment.score is not None
    assert 0.0 <= float(assignment.score) <= 1.0

    # 6. Test Idempotency (re-running topic assignment updates without duplicate key violation)
    re_assignments = service.assign_topics_to_reviews(
        review_ids=[reviews[0].id, reviews[1].id],
        ml_model_id=ml_model.id,
        pipeline_run_id=pipeline_run.id,
        model=model,
    )
    assert len(re_assignments) == 2
    rev1_topics_after = topic_repo.get_review_topics_by_review(reviews[0].id)
    assert len(rev1_topics_after) == len(rev1_topics)

    # 7. Test InsufficientCorpusError enforcement
    with pytest.raises(InsufficientCorpusError):
        service.build_corpus_for_game(
            game_id=game.id,
            language="en",
            min_corpus_size=100,  # Only 30 reviews exist
        )
