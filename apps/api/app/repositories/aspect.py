"""Repository for controlled aspect taxonomy and review-level aspect predictions."""

import uuid
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aspect import Aspect, AspectPrediction
from app.repositories.base import BaseRepository


class AspectRepository(BaseRepository[Aspect]):
    """Data access repository for Aspect taxonomy and AspectPrediction records."""

    def __init__(self, session: Session) -> None:
        super().__init__(Aspect, session)

    def get_by_key(self, aspect_key: str) -> Aspect | None:
        """Fetch aspect definition by its stable machine key."""
        stmt = select(Aspect).where(Aspect.aspect_key == aspect_key)
        return self.session.scalars(stmt).first()

    def get_all_active(self) -> Sequence[Aspect]:
        """Fetch all active taxonomy aspects."""
        stmt = select(Aspect).where(Aspect.is_active.is_(True)).order_by(Aspect.aspect_key)
        return self.session.scalars(stmt).all()

    def get_predictions_for_review(
        self,
        review_id: uuid.UUID,
        ml_model_id: uuid.UUID | None = None,
    ) -> Sequence[AspectPrediction]:
        """Fetch aspect predictions associated with a specific review."""
        stmt = select(AspectPrediction).where(AspectPrediction.review_id == review_id)
        if ml_model_id:
            stmt = stmt.where(AspectPrediction.ml_model_id == ml_model_id)
        return self.session.scalars(stmt).all()

    def create_prediction(
        self,
        review_id: uuid.UUID,
        aspect_id: uuid.UUID,
        ml_model_id: uuid.UUID,
        pipeline_run_id: uuid.UUID,
        sentiment_label: str,
        confidence: float | None = None,
        evidence_text: str | None = None,
        start_offset: int | None = None,
        end_offset: int | None = None,
    ) -> AspectPrediction:
        """Create or update an aspect prediction enforcing idempotency."""
        stmt = select(AspectPrediction).where(
            AspectPrediction.review_id == review_id,
            AspectPrediction.aspect_id == aspect_id,
            AspectPrediction.ml_model_id == ml_model_id,
            AspectPrediction.pipeline_run_id == pipeline_run_id,
        )
        existing = self.session.scalars(stmt).first()

        conf_decimal = Decimal(f"{confidence:.5f}") if confidence is not None else None

        if existing:
            existing.sentiment_label = sentiment_label
            existing.confidence = conf_decimal
            existing.evidence_text = evidence_text
            existing.start_offset = start_offset
            existing.end_offset = end_offset
            self.session.flush()
            return existing

        prediction = AspectPrediction(
            review_id=review_id,
            aspect_id=aspect_id,
            ml_model_id=ml_model_id,
            pipeline_run_id=pipeline_run_id,
            sentiment_label=sentiment_label,
            confidence=conf_decimal,
            evidence_text=evidence_text,
            start_offset=start_offset,
            end_offset=end_offset,
        )
        self.session.add(prediction)
        self.session.flush()
        return prediction

    def bulk_create_predictions(
        self,
        predictions_data: list[dict[str, Any]],
    ) -> list[AspectPrediction]:
        """Persist a batch of aspect predictions with transactional safety."""
        created: list[AspectPrediction] = []
        for d in predictions_data:
            pred = self.create_prediction(
                review_id=d["review_id"],
                aspect_id=d["aspect_id"],
                ml_model_id=d["ml_model_id"],
                pipeline_run_id=d["pipeline_run_id"],
                sentiment_label=d["sentiment_label"],
                confidence=d.get("confidence"),
                evidence_text=d.get("evidence_text"),
                start_offset=d.get("start_offset"),
                end_offset=d.get("end_offset"),
            )
            created.append(pred)
        self.session.commit()
        return created
