"""Domain service for Aspect-Based Sentiment Analysis (ABSA) execution and persistence."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.absa.classifier import BaseABSAClassifier, SentenceGroundedTfidfABSA
from app.ml.absa.schemas import ABSAInput, ABSAPredictionOutput
from app.ml.taxonomy import ASPECT_TAXONOMY
from app.models.aspect import Aspect, AspectPrediction
from app.models.review import Review
from app.repositories.aspect import AspectRepository

logger = logging.getLogger("steamscoop.services.absa")


class ABSAService:
    """Domain service managing ABSA inference execution and AspectPrediction persistence."""

    def __init__(
        self,
        session: Session,
        model: BaseABSAClassifier | None = None,
        aspect_repo: AspectRepository | None = None,
    ) -> None:
        self.session = session
        self.model = model or SentenceGroundedTfidfABSA()
        self.aspect_repo = aspect_repo or AspectRepository(session)

    def ensure_taxonomy_seeded(self) -> dict[str, Aspect]:
        """Ensure all 12 controlled aspects exist in the database aspect table."""
        existing_aspects = {asp.aspect_key: asp for asp in self.aspect_repo.get_all_active()}
        aspect_map: dict[str, Aspect] = dict(existing_aspects)

        for ak, defn in ASPECT_TAXONOMY.items():
            key_str = ak.value
            if key_str not in aspect_map:
                asp = Aspect(
                    aspect_key=key_str,
                    display_name=defn.display_name,
                    description=defn.description,
                    is_active=True,
                )
                self.session.add(asp)
                self.session.flush()
                aspect_map[key_str] = asp

        self.session.commit()
        return aspect_map

    def predict_and_persist_for_reviews(
        self,
        review_ids: list[uuid.UUID],
        ml_model_id: uuid.UUID,
        pipeline_run_id: uuid.UUID,
        aspect_threshold: float | None = None,
    ) -> list[ABSAPredictionOutput]:
        """Execute ABSA inference on database reviews and persist predictions idempotently."""
        if not review_ids:
            return []

        # 1. Fetch review entities
        stmt = select(Review).where(Review.id.in_(review_ids))
        reviews = list(self.session.scalars(stmt).all())
        review_map = {r.id: r for r in reviews}

        # 2. Ensure controlled taxonomy aspects are cached
        aspect_cache = self.ensure_taxonomy_seeded()

        # 3. Assemble inputs for ABSA model
        inputs = [
            ABSAInput(
                review_id=str(r.id),
                text=r.review_text,
                language=r.language,
            )
            for r in reviews
        ]

        # 4. Execute prediction
        predictions = self.model.predict_records(inputs, aspect_threshold=aspect_threshold)

        # 5. Persist predictions to database
        for pred_out in predictions:
            r_id = uuid.UUID(pred_out.review_id)
            if r_id not in review_map:
                continue

            for asp_item in pred_out.aspects:
                asp_key_str = asp_item.aspect.value
                asp_entity = aspect_cache.get(asp_key_str)
                if not asp_entity:
                    continue

                self.aspect_repo.create_prediction(
                    review_id=r_id,
                    aspect_id=asp_entity.id,
                    ml_model_id=ml_model_id,
                    pipeline_run_id=pipeline_run_id,
                    sentiment_label=asp_item.sentiment.value,
                    confidence=asp_item.confidence,
                    evidence_text=asp_item.evidence_text,
                    start_offset=asp_item.start_offset,
                    end_offset=asp_item.end_offset,
                )

        self.session.commit()
        return predictions

    def get_review_aspects(self, review_id: uuid.UUID) -> Sequence[AspectPrediction]:
        """Fetch all aspect predictions persisted for a review."""
        return self.aspect_repo.get_predictions_for_review(review_id)
