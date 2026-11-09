"""Domain service for Topic Modeling execution, curation, and database persistence."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.topic.curation import TopicCurationService
from app.ml.topic.models import BaseTopicModel
from app.ml.topic.pipeline import InsufficientCorpusError
from app.ml.topic.schemas import (
    RawDocument,
    TopicEvaluationReport,
    TopicMetrics,
)
from app.models.game import Game
from app.models.review import Review
from app.models.topic import ReviewTopic, Topic
from app.repositories.topic import TopicRepository

logger = logging.getLogger("steamscoop.services.topic")


class TopicService:
    """Domain service managing topic model execution, human curation, and persistence."""

    def __init__(
        self,
        session: Session,
        topic_repo: TopicRepository | None = None,
        curation_service: TopicCurationService | None = None,
    ) -> None:
        self.session = session
        self.topic_repo = topic_repo or TopicRepository(session)
        self.curation_service = curation_service or TopicCurationService()

    def build_corpus_for_game(
        self,
        game_id: uuid.UUID,
        language: str = "en",
        min_corpus_size: int = 25,
        min_char_length: int = 20,
        min_word_length: int = 4,
        deduplicate: bool = True,
    ) -> list[RawDocument]:
        """Fetch and assemble a clean per-game, per-language review corpus from PostgreSQL."""
        stmt = (
            select(Review)
            .where(Review.game_id == game_id, Review.language == language)
            .order_by(Review.created_at.desc())
        )
        reviews = list(self.session.scalars(stmt).all())

        seen_texts: set[str] = set()
        corpus: list[RawDocument] = []

        for r in reviews:
            txt = (getattr(r, "normalized_text", None) or r.review_text or "").strip()
            if len(txt) < min_char_length:
                continue

            words = txt.split()
            if len(words) < min_word_length:
                continue

            if deduplicate:
                norm_key = " ".join(words).lower()
                if norm_key in seen_texts:
                    continue
                seen_texts.add(norm_key)

            corpus.append(
                RawDocument(
                    review_id=str(r.id),
                    text=txt,
                    language=r.language,
                    voted_up=bool(r.voted_up if r.voted_up is not None else True),
                )
            )

        if len(corpus) < min_corpus_size:
            # Look up game app id for descriptive error
            game = self.session.get(Game, game_id)
            app_id = game.steam_app_id if game else "unknown"
            raise InsufficientCorpusError(
                f"Game {game_id} (App ID {app_id}) has {len(corpus)} eligible reviews, "
                f"below minimum threshold of {min_corpus_size}. Topic modeling cannot be "
                "reliably published without sufficient player sample size."
            )

        return corpus

    def fit_and_persist_topics(
        self,
        game_id: uuid.UUID,
        ml_model_id: uuid.UUID,
        pipeline_run_id: uuid.UUID,
        model: BaseTopicModel,
        language: str = "en",
        min_corpus_size: int = 25,
        curation_map: dict[str, dict[str, Any]] | None = None,
        curator_id: str = "curator_01",
    ) -> tuple[list[Topic], list[ReviewTopic]]:
        """Fit a topic model on the game corpus, apply curation if provided, and persist to DB."""
        # 1. Build and validate corpus
        corpus = self.build_corpus_for_game(
            game_id=game_id,
            language=language,
            min_corpus_size=min_corpus_size,
        )

        # 2. Fit topic model
        model.fit(corpus)
        topics, assignments = model.transform(corpus)

        # 3. Apply human curation if provided
        if curation_map:
            # Build mock evaluation report to apply curation
            report = TopicEvaluationReport(
                model_key=model.model_key,
                model_version="v1.0.0",
                steam_app_id=0,
                corpus_size=len(corpus),
                metrics=report_metrics_placeholder(len(topics)),
                topics=topics,
                curated=False,
            )
            curated_report = self.curation_service.apply_curated_labels(
                report=report,
                curation_map=curation_map,
                curator_id=curator_id,
            )
            topics = curated_report.topics

        # 4. Persist Topic taxonomy records
        topics_payload: list[dict[str, Any]] = [
            {
                "ml_model_id": ml_model_id,
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

        # 5. Persist ReviewTopic assignments
        assignments_payload: list[dict[str, Any]] = []
        for a in assignments:
            r_id = uuid.UUID(a.review_id)
            t_id = topic_key_to_id.get(a.topic_key)
            if not t_id:
                continue

            assignments_payload.append(
                {
                    "review_id": r_id,
                    "topic_id": t_id,
                    "pipeline_run_id": pipeline_run_id,
                    "score": a.score,
                    "is_primary": a.is_primary,
                }
            )

        persisted_assignments = self.topic_repo.bulk_assign_review_topics(assignments_payload)
        return persisted_topics, persisted_assignments

    def assign_topics_to_reviews(
        self,
        review_ids: list[uuid.UUID],
        ml_model_id: uuid.UUID,
        pipeline_run_id: uuid.UUID,
        model: BaseTopicModel,
    ) -> list[ReviewTopic]:
        """Perform topic inference for a specific set of reviews using an existing topic model."""
        if not review_ids:
            return []

        # 1. Fetch reviews
        stmt = select(Review).where(Review.id.in_(review_ids))
        reviews = list(self.session.scalars(stmt).all())
        if not reviews:
            return []

        # 2. Build RawDocuments
        docs = [
            RawDocument(
                review_id=str(r.id),
                text=getattr(r, "normalized_text", None) or r.review_text or "",
                language=r.language,
                voted_up=bool(r.voted_up if r.voted_up is not None else True),
            )
            for r in reviews
        ]

        # 3. Infer assignments
        assignments = model.transform_documents(docs)

        # 4. Map topic_key to persisted Topic ID
        topics = self.topic_repo.get_topics_by_model(ml_model_id, include_outliers=True)
        topic_key_to_id = {t.topic_key: t.id for t in topics}

        # 5. Persist assignments
        payload: list[dict[str, Any]] = []
        for a in assignments:
            r_id = uuid.UUID(a.review_id)
            t_id = topic_key_to_id.get(a.topic_key)
            if not t_id:
                continue

            payload.append(
                {
                    "review_id": r_id,
                    "topic_id": t_id,
                    "pipeline_run_id": pipeline_run_id,
                    "score": a.score,
                    "is_primary": a.is_primary,
                }
            )

        return self.topic_repo.bulk_assign_review_topics(payload)

    def get_game_topics(
        self,
        ml_model_id: uuid.UUID,
        include_outliers: bool = False,
    ) -> Sequence[Topic]:
        """Fetch all discovered topics for a given ML model version."""
        return self.topic_repo.get_topics_by_model(
            ml_model_id=ml_model_id,
            include_outliers=include_outliers,
        )


def report_metrics_placeholder(num_topics: int) -> TopicMetrics:
    """Helper to construct dummy metrics for curation report wrapper."""
    return TopicMetrics(
        num_topics=num_topics,
        topic_diversity=1.0,
        mean_pairwise_jaccard=0.0,
        npmi_coherence=0.0,
        outlier_count=0,
        outlier_rate=0.0,
        topic_size_entropy=1.0,
        stability_score=1.0,
    )
