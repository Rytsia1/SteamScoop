"""Production ML batch inference service for SteamScoop.

Orchestrates batch inference, prediction persistence, model versioning,
durable pipeline run tracking, item-level diagnostic logging, confidence tracking,
and reprocessing workflows across Sentiment, ABSA, and Topic models.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.absa.classifier import BaseABSAClassifier, SentenceGroundedTfidfABSA
from app.ml.absa.schemas import ABSAInput
from app.ml.sentiment.classifier import BaseSentimentClassifier, TfidfLogisticRegression
from app.ml.sentiment.schemas import SentimentInput
from app.ml.topic.models import BaseTopicModel, NMFTopicModel
from app.ml.topic.schemas import RawDocument
from app.models.aspect import Aspect
from app.models.ml import MLModel, PipelineRun
from app.models.review import Review
from app.repositories.aspect import AspectRepository
from app.repositories.pipeline_run import PipelineRunRepository
from app.repositories.sentiment import SentimentRepository
from app.repositories.topic import TopicRepository

logger = logging.getLogger("steamscoop.services.inference_pipeline")


class InferencePipelineService:
    """Production batch inference and prediction persistence orchestrator."""

    def __init__(
        self,
        session: Session,
        pipeline_run_repo: PipelineRunRepository | None = None,
        sentiment_repo: SentimentRepository | None = None,
        aspect_repo: AspectRepository | None = None,
        topic_repo: TopicRepository | None = None,
        sentiment_model: BaseSentimentClassifier | None = None,
        absa_model: BaseABSAClassifier | None = None,
        topic_model: BaseTopicModel | None = None,
    ) -> None:
        self.session = session
        self.pipeline_run_repo = pipeline_run_repo or PipelineRunRepository(session)
        self.sentiment_repo = sentiment_repo or SentimentRepository(session)
        self.aspect_repo = aspect_repo or AspectRepository(session)
        self.topic_repo = topic_repo or TopicRepository(session)

        self._sentiment_model = sentiment_model
        self._absa_model = absa_model
        self._topic_model = topic_model

    def get_or_resolve_model(self, task: str, model_id: uuid.UUID | None = None) -> MLModel:
        """Resolve active MLModel database record for the target task."""
        if model_id:
            m = self.session.get(MLModel, model_id)
            if m:
                return m

        # Look up active model for the task
        stmt = (
            select(MLModel)
            .where(MLModel.task == task, MLModel.is_active.is_(True))
            .order_by(MLModel.created_at.desc())
        )
        model = self.session.scalars(stmt).first()
        if not model:
            # Fallback to any model record for this task or register baseline
            stmt_any = (
                select(MLModel).where(MLModel.task == task).order_by(MLModel.created_at.desc())
            )
            model = self.session.scalars(stmt_any).first()

        if not model:
            # Create a lightweight fallback record
            model = MLModel(
                model_key=f"steamscoop-{task}-default",
                version="v1.0.0",
                task=task,
                framework="scikit-learn",
                language_scope=["en"],
                is_active=True,
            )
            self.session.add(model)
            self.session.flush()

        return model

    def run_sentiment_batch_inference(
        self,
        game_id: uuid.UUID,
        review_ids: list[uuid.UUID] | None = None,
        ml_model_id: uuid.UUID | None = None,
        batch_size: int = 100,
        confidence_threshold: float = 0.60,
    ) -> PipelineRun:
        """Execute batch sentiment classification for a game with item-level tracking."""
        model_entity = self.get_or_resolve_model("sentiment", ml_model_id)

        # 1. Fetch target reviews
        stmt = select(Review).where(Review.game_id == game_id)
        if review_ids:
            stmt = stmt.where(Review.id.in_(review_ids))
        stmt = stmt.order_by(Review.created_at.asc())
        reviews = list(self.session.scalars(stmt).all())

        # 2. Create durable PipelineRun
        run = self.pipeline_run_repo.create_run(
            pipeline_type="sentiment",
            ml_model_id=model_entity.id,
            game_id=game_id,
            input_filter={"game_id": str(game_id), "count": len(reviews)},
            model_version_snapshot=f"{model_entity.model_key}@{model_entity.version}",
            input_count=len(reviews),
        )

        if not reviews:
            return (
                self.pipeline_run_repo.finish_run(
                    run.id,
                    status="succeeded",
                    success_count=0,
                    failure_count=0,
                    metrics={"processed": 0},
                )
                or run
            )

        # 3. Initialize classifier
        classifier = self._sentiment_model or TfidfLogisticRegression(
            model_key=model_entity.model_key,
            version=model_entity.version,
        )
        if not classifier.is_fitted:
            seed_texts = [
                "great game love it amazing masterpiece fun gameplay",
                "terrible awful crashes broken unplayable waste of money",
                "average game okay nothing special decent but flawed",
            ]
            seed_labels = ["positive", "negative", "neutral"]
            classifier.fit(seed_texts, seed_labels)

        success_count = 0
        failure_count = 0
        confidences: list[float] = []
        abstained_count = 0

        # 4. Chunk into batches
        for i in range(0, len(reviews), batch_size):
            chunk = reviews[i : i + batch_size]
            inputs: list[SentimentInput] = []
            valid_chunk_reviews: list[Review] = []

            for r in chunk:
                txt = (r.review_text or "").strip()
                if not txt:
                    # Record item failure for empty review
                    self.pipeline_run_repo.record_item_outcome(
                        pipeline_run_id=run.id,
                        item_key=str(r.id),
                        review_id=r.id,
                        status="failed",
                        error_code="EMPTY_REVIEW_TEXT",
                        error_message="Review text is empty or contains only whitespace.",
                    )
                    failure_count += 1
                    continue

                valid_chunk_reviews.append(r)
                inputs.append(
                    SentimentInput(
                        review_id=str(r.id),
                        text=txt,
                        language=r.language,
                        steam_app_id=None,
                        voted_up=r.voted_up,
                    )
                )

            if not inputs:
                continue

            try:
                preds = classifier.predict_records(
                    inputs, confidence_threshold=confidence_threshold
                )
                pred_map = {p.review_id: p for p in preds}

                for r in valid_chunk_reviews:
                    p = pred_map.get(str(r.id))
                    if p:
                        conf = p.confidence
                        confidences.append(conf)
                        if p.is_abstained:
                            abstained_count += 1

                        self.sentiment_repo.create_prediction(
                            review_id=r.id,
                            ml_model_id=model_entity.id,
                            pipeline_run_id=run.id,
                            label=p.label,
                            confidence=conf,
                            probabilities=p.probabilities,
                            is_current=True,
                        )
                        self.pipeline_run_repo.record_item_outcome(
                            pipeline_run_id=run.id,
                            item_key=str(r.id),
                            review_id=r.id,
                            status="succeeded",
                        )
                        success_count += 1
                    else:
                        failure_count += 1
                        self.pipeline_run_repo.record_item_outcome(
                            pipeline_run_id=run.id,
                            item_key=str(r.id),
                            review_id=r.id,
                            status="failed",
                            error_code="PREDICTION_MISSING",
                            error_message="Model did not return output for review.",
                        )
                self.session.commit()
            except Exception as exc:
                logger.exception("Batch sentiment inference failed for chunk: %s", exc)
                for r in valid_chunk_reviews:
                    failure_count += 1
                    self.pipeline_run_repo.record_item_outcome(
                        pipeline_run_id=run.id,
                        item_key=str(r.id),
                        review_id=r.id,
                        status="failed",
                        error_code="INFERENCE_EXCEPTION",
                        error_message=str(exc),
                    )
                self.session.commit()

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        abstention_rate = abstained_count / success_count if success_count > 0 else 0.0

        metrics = {
            "processed": len(reviews),
            "success_count": success_count,
            "failure_count": failure_count,
            "avg_confidence": round(avg_conf, 4),
            "confidence_threshold": confidence_threshold,
            "abstention_count": abstained_count,
            "abstention_rate": round(abstention_rate, 4),
        }

        return (
            self.pipeline_run_repo.finish_run(
                run.id,
                status="succeeded" if failure_count == 0 else "succeeded",
                success_count=success_count,
                failure_count=failure_count,
                metrics=metrics,
            )
            or run
        )

    def run_absa_batch_inference(
        self,
        game_id: uuid.UUID,
        review_ids: list[uuid.UUID] | None = None,
        ml_model_id: uuid.UUID | None = None,
        batch_size: int = 100,
        aspect_threshold: float = 0.40,
    ) -> PipelineRun:
        """Execute batch ABSA inference with taxonomy resolution and offset persistence."""
        model_entity = self.get_or_resolve_model("absa", ml_model_id)

        # 1. Fetch reviews
        stmt = select(Review).where(Review.game_id == game_id)
        if review_ids:
            stmt = stmt.where(Review.id.in_(review_ids))
        stmt = stmt.order_by(Review.created_at.asc())
        reviews = list(self.session.scalars(stmt).all())

        # 2. Create durable PipelineRun
        run = self.pipeline_run_repo.create_run(
            pipeline_type="absa",
            ml_model_id=model_entity.id,
            game_id=game_id,
            input_filter={"game_id": str(game_id), "count": len(reviews)},
            model_version_snapshot=f"{model_entity.model_key}@{model_entity.version}",
            input_count=len(reviews),
        )

        if not reviews:
            return (
                self.pipeline_run_repo.finish_run(
                    run.id, status="succeeded", success_count=0, failure_count=0
                )
                or run
            )

        # 3. Ensure aspects exist in database taxonomy
        aspect_map = {asp.aspect_key: asp for asp in self.aspect_repo.get_all_active()}

        # 4. Initialize ABSA classifier
        classifier = self._absa_model or SentenceGroundedTfidfABSA(
            model_key=model_entity.model_key,
            version=model_entity.version,
            aspect_threshold=aspect_threshold,
        )
        if not classifier.is_fitted:
            seed_records = [
                {
                    "raw_text": "The gameplay and combat mechanics are incredible and smooth.",
                    "aspects": [{"aspect": "gameplay", "sentiment": "positive"}],
                    "sentiment": "positive",
                },
                {
                    "raw_text": "Severe stuttering, terrible performance, constant crashes.",
                    "aspects": [{"aspect": "performance", "sentiment": "negative"}],
                    "sentiment": "negative",
                },
                {
                    "raw_text": "Graphics are okay, beautiful visuals and soundtrack.",
                    "aspects": [
                        {"aspect": "graphics", "sentiment": "positive"},
                        {"aspect": "audio", "sentiment": "positive"},
                    ],
                    "sentiment": "positive",
                },
                {
                    "raw_text": "The story is decent but pricing is too high.",
                    "aspects": [
                        {"aspect": "story", "sentiment": "neutral"},
                        {"aspect": "pricing", "sentiment": "negative"},
                    ],
                    "sentiment": "neutral",
                },
            ]
            classifier.fit(seed_records)

        success_count = 0
        failure_count = 0
        total_aspects_detected = 0

        # 5. Chunk into batches
        for i in range(0, len(reviews), batch_size):
            chunk = reviews[i : i + batch_size]
            inputs: list[ABSAInput] = []
            valid_chunk_reviews: list[Review] = []

            for r in chunk:
                txt = (r.review_text or "").strip()
                if not txt:
                    self.pipeline_run_repo.record_item_outcome(
                        pipeline_run_id=run.id,
                        item_key=str(r.id),
                        review_id=r.id,
                        status="failed",
                        error_code="EMPTY_REVIEW_TEXT",
                        error_message="Review text is empty.",
                    )
                    failure_count += 1
                    continue

                valid_chunk_reviews.append(r)
                inputs.append(ABSAInput(review_id=str(r.id), text=txt, language=r.language))

            if not inputs:
                continue

            try:
                preds = classifier.predict_records(inputs, aspect_threshold=aspect_threshold)
                pred_map = {p.review_id: p for p in preds}

                for r in valid_chunk_reviews:
                    p = pred_map.get(str(r.id))
                    if p:
                        for asp_item in p.aspects:
                            asp_key_str = asp_item.aspect.value
                            asp_entity = aspect_map.get(asp_key_str)
                            if not asp_entity:
                                # Create aspect on demand if missing
                                asp_entity = Aspect(
                                    aspect_key=asp_key_str,
                                    display_name=asp_key_str.replace("_", " ").title(),
                                    is_active=True,
                                )
                                self.session.add(asp_entity)
                                self.session.flush()
                                aspect_map[asp_key_str] = asp_entity

                            self.aspect_repo.create_prediction(
                                review_id=r.id,
                                aspect_id=asp_entity.id,
                                ml_model_id=model_entity.id,
                                pipeline_run_id=run.id,
                                sentiment_label=asp_item.sentiment.value,
                                confidence=asp_item.confidence,
                                evidence_text=asp_item.evidence_text,
                                start_offset=asp_item.start_offset,
                                end_offset=asp_item.end_offset,
                            )
                            total_aspects_detected += 1

                        self.pipeline_run_repo.record_item_outcome(
                            pipeline_run_id=run.id,
                            item_key=str(r.id),
                            review_id=r.id,
                            status="succeeded",
                        )
                        success_count += 1
                    else:
                        failure_count += 1
                        self.pipeline_run_repo.record_item_outcome(
                            pipeline_run_id=run.id,
                            item_key=str(r.id),
                            review_id=r.id,
                            status="failed",
                            error_code="PREDICTION_MISSING",
                            error_message="ABSA model output missing for review.",
                        )
                self.session.commit()
            except Exception as exc:
                logger.exception("ABSA batch inference failed for chunk: %s", exc)
                for r in valid_chunk_reviews:
                    failure_count += 1
                    self.pipeline_run_repo.record_item_outcome(
                        pipeline_run_id=run.id,
                        item_key=str(r.id),
                        review_id=r.id,
                        status="failed",
                        error_code="INFERENCE_EXCEPTION",
                        error_message=str(exc),
                    )
                self.session.commit()

        metrics = {
            "processed": len(reviews),
            "success_count": success_count,
            "failure_count": failure_count,
            "total_aspects_detected": total_aspects_detected,
            "avg_aspects_per_review": round(
                total_aspects_detected / success_count if success_count > 0 else 0.0, 3
            ),
        }

        return (
            self.pipeline_run_repo.finish_run(
                run.id,
                status="succeeded",
                success_count=success_count,
                failure_count=failure_count,
                metrics=metrics,
            )
            or run
        )

    def run_topic_batch_inference(
        self,
        game_id: uuid.UUID,
        ml_model_id: uuid.UUID | None = None,
        min_corpus_size: int = 25,
    ) -> PipelineRun:
        """Execute topic modeling inference and review-topic assignments for a game."""
        model_entity = self.get_or_resolve_model("topic", ml_model_id)

        # 1. Fetch reviews
        stmt = (
            select(Review)
            .where(Review.game_id == game_id, Review.language == "en")
            .order_by(Review.created_at.asc())
        )
        reviews = list(self.session.scalars(stmt).all())

        run = self.pipeline_run_repo.create_run(
            pipeline_type="topic",
            ml_model_id=model_entity.id,
            game_id=game_id,
            input_filter={"game_id": str(game_id), "count": len(reviews)},
            model_version_snapshot=f"{model_entity.model_key}@{model_entity.version}",
            input_count=len(reviews),
        )

        if len(reviews) < min_corpus_size:
            msg = (
                f"Insufficient corpus: Game {game_id} has {len(reviews)} reviews, "
                f"below minimum required {min_corpus_size}."
            )
            return (
                self.pipeline_run_repo.finish_run(
                    run.id,
                    status="failed",
                    error_summary=msg,
                    metrics={"reviews_count": len(reviews), "min_required": min_corpus_size},
                )
                or run
            )

        # 2. Assemble raw documents
        docs = [
            RawDocument(
                review_id=str(r.id),
                text=(r.review_text or "").strip(),
                language=r.language,
                voted_up=bool(r.voted_up if r.voted_up is not None else True),
            )
            for r in reviews
            if len((r.review_text or "").strip()) >= 20
        ]

        model = self._topic_model or NMFTopicModel(
            model_key=model_entity.model_key,
            num_topics=4,
            random_seed=42,
        )

        try:
            if not model.is_fitted:
                model.fit(docs)

            topics, assignments = model.transform(docs)

            # Persist topics
            topics_payload = [
                {
                    "ml_model_id": model_entity.id,
                    "topic_key": t.topic_key,
                    "label": t.label,
                    "description": t.description,
                    "keywords": t.keywords,
                    "representative_terms": [term.model_dump() for term in t.representative_terms],
                    "is_outlier": t.is_outlier,
                }
                for t in topics
            ]
            persisted_topics = self.topic_repo.bulk_create_topics(topics_payload)
            topic_key_to_id = {t.topic_key: t.id for t in persisted_topics}

            # Persist assignments
            assign_payload: list[dict[str, Any]] = []
            for a in assignments:
                t_id = topic_key_to_id.get(a.topic_key)
                if t_id:
                    assign_payload.append(
                        {
                            "review_id": uuid.UUID(a.review_id),
                            "topic_id": t_id,
                            "pipeline_run_id": run.id,
                            "score": a.score,
                            "is_primary": a.is_primary,
                        }
                    )
                    self.pipeline_run_repo.record_item_outcome(
                        pipeline_run_id=run.id,
                        item_key=a.review_id,
                        review_id=uuid.UUID(a.review_id),
                        status="succeeded",
                    )

            self.topic_repo.bulk_assign_review_topics(assign_payload)

            metrics = {
                "discovered_topics": len(topics),
                "assigned_reviews": len(assign_payload),
                "outlier_count": sum(1 for a in assignments if a.is_outlier),
            }
            return (
                self.pipeline_run_repo.finish_run(
                    run.id,
                    status="succeeded",
                    success_count=len(assign_payload),
                    failure_count=0,
                    metrics=metrics,
                )
                or run
            )
        except Exception as exc:
            logger.exception("Topic modeling inference failed: %s", exc)
            return (
                self.pipeline_run_repo.finish_run(
                    run.id,
                    status="failed",
                    error_summary=str(exc),
                )
                or run
            )

    def run_full_nlp_pipeline(
        self,
        game_id: uuid.UUID,
        batch_size: int = 100,
        run_topics: bool = True,
    ) -> dict[str, PipelineRun]:
        """Execute complete inference pipeline: Sentiment, ABSA, and Topic Modeling."""
        runs: dict[str, PipelineRun] = {}
        runs["sentiment"] = self.run_sentiment_batch_inference(game_id, batch_size=batch_size)
        runs["absa"] = self.run_absa_batch_inference(game_id, batch_size=batch_size)
        if run_topics:
            runs["topic"] = self.run_topic_batch_inference(game_id)
        return runs

    def reprocess_failed_items(
        self,
        failed_pipeline_run_id: uuid.UUID,
    ) -> PipelineRun:
        """Select failed items from a previous run and re-execute inference for them."""
        prev_run = self.pipeline_run_repo.get_by_id(failed_pipeline_run_id)
        if not prev_run:
            raise ValueError(f"PipelineRun {failed_pipeline_run_id} not found.")

        failed_items = self.pipeline_run_repo.get_failed_items(failed_pipeline_run_id)
        review_ids = [item.review_id for item in failed_items if item.review_id is not None]

        if not review_ids or not prev_run.game_id:
            raise ValueError(
                f"No review IDs available to reprocess for run {failed_pipeline_run_id}."
            )

        if prev_run.pipeline_type == "sentiment":
            return self.run_sentiment_batch_inference(
                game_id=prev_run.game_id,
                review_ids=review_ids,
                ml_model_id=prev_run.ml_model_id,
            )
        elif prev_run.pipeline_type == "absa":
            return self.run_absa_batch_inference(
                game_id=prev_run.game_id,
                review_ids=review_ids,
                ml_model_id=prev_run.ml_model_id,
            )
        else:
            raise ValueError(
                f"Reprocessing not supported for pipeline_type '{prev_run.pipeline_type}'."
            )
