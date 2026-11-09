"""Integration tests for ABSA persistence, model registry, and aspect repositories."""

from sqlalchemy.orm import Session

from app.ml.absa.classifier import SentenceGroundedTfidfABSA
from app.ml.absa.registry import ABSAModelRegistryService
from app.ml.taxonomy import AspectKey, SentimentLabel
from app.models.game import Game
from app.models.ml import PipelineRun
from app.models.review import Review
from app.repositories.aspect import AspectRepository
from app.services.absa_service import ABSAService


def test_absa_database_integration_and_persistence(db_session: Session) -> None:
    # 1. Create a game and reviews
    game = Game(
        steam_app_id=999100, name="ABSA Test Game", catalog_status="indexed", is_active=True
    )
    db_session.add(game)
    db_session.flush()

    rev1 = Review(
        game_id=game.id,
        steam_review_id=999001,
        review_text="Combat mechanics feel crisp and fluid. Hacking enemies is great.",
        language="en",
        voted_up=True,
    )
    rev2 = Review(
        game_id=game.id,
        steam_review_id=999002,
        review_text="Severe framerate microstutter and constant crashes. But story lore was decent.",
        language="en",
        voted_up=False,
    )
    rev3 = Review(
        game_id=game.id,
        steam_review_id=999003,
        review_text="10/10 masterpiece.",
        language="en",
        voted_up=True,
    )
    db_session.add_all([rev1, rev2, rev3])
    db_session.flush()

    # 2. Register ABSA model
    registry = ABSAModelRegistryService()
    manifest_data = {
        "model_key": "steamscoop-absa-test",
        "version": "v1.0.0",
        "task": "absa",
        "framework": "scikit-learn",
        "config": {"aspect_threshold": 0.35},
        "metrics": {"detection_micro_f1": 0.85},
        "release_gate": {"status": "CANDIDATE", "passed_gates": False},
    }
    ml_model = registry.sync_model_to_db(db_session, manifest_data, is_active=False)

    # 3. Create PipelineRun
    pipeline_run = PipelineRun(
        pipeline_type="absa",
        status="running",
        game_id=game.id,
        ml_model_id=ml_model.id,
        input_count=3,
        success_count=0,
        failure_count=0,
    )
    db_session.add(pipeline_run)
    db_session.flush()

    # 4. Initialize ABSA classifier and train on sample records including a zero-aspect review
    classifier = SentenceGroundedTfidfABSA(aspect_threshold=0.45)
    classifier.fit(
        [
            {
                "normalized_text": rev1.review_text,
                "aspects": [
                    {
                        "aspect": AspectKey.GAMEPLAY.value,
                        "sentiment": SentimentLabel.POSITIVE.value,
                        "snippet": "Combat mechanics feel crisp and fluid",
                    }
                ],
            },
            {
                "normalized_text": rev2.review_text,
                "aspects": [
                    {
                        "aspect": AspectKey.PERFORMANCE.value,
                        "sentiment": SentimentLabel.NEGATIVE.value,
                        "snippet": "Severe framerate microstutter and constant crashes",
                    },
                    {
                        "aspect": AspectKey.STORY.value,
                        "sentiment": SentimentLabel.POSITIVE.value,
                        "snippet": "story lore was decent",
                    },
                ],
            },
            {
                "normalized_text": "Just yes. 10/10 masterpiece.",
                "aspects": [],
            },
        ]
    )

    # 5. Execute ABSAService
    aspect_repo = AspectRepository(db_session)
    service = ABSAService(db_session, model=classifier, aspect_repo=aspect_repo)

    preds = service.predict_and_persist_for_reviews(
        review_ids=[rev1.id, rev2.id, rev3.id],
        ml_model_id=ml_model.id,
        pipeline_run_id=pipeline_run.id,
    )

    assert len(preds) == 3

    # 6. Verify AspectPrediction database records
    db_preds_rev1 = aspect_repo.get_predictions_for_review(rev1.id)
    assert len(db_preds_rev1) >= 1
    p1 = db_preds_rev1[0]
    assert p1.ml_model_id == ml_model.id
    assert p1.pipeline_run_id == pipeline_run.id
    assert p1.sentiment_label in [
        SentimentLabel.POSITIVE.value,
        SentimentLabel.NEGATIVE.value,
        SentimentLabel.NEUTRAL.value,
    ]
    assert p1.confidence is not None
    assert p1.evidence_text is not None

    # Verify zero-aspect review (rev3) produced no hallucinated database rows
    db_preds_rev3 = aspect_repo.get_predictions_for_review(rev3.id)
    assert len(db_preds_rev3) == 0

    # 7. Test Idempotency (re-running prediction updates existing rows without duplicate key violations)
    re_preds = service.predict_and_persist_for_reviews(
        review_ids=[rev1.id],
        ml_model_id=ml_model.id,
        pipeline_run_id=pipeline_run.id,
    )
    assert len(re_preds) == 1
    db_preds_rev1_after = aspect_repo.get_predictions_for_review(rev1.id)
    assert len(db_preds_rev1_after) == len(db_preds_rev1)
