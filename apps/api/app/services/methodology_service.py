"""Domain service for public methodology, model card catalogs, and dataset specifications."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml import MLModel
from app.schemas.methodology import (
    CollectionPolicy,
    DatasetDocumentationItem,
    MethodologyResponse,
    MetricDefinitions,
    ModelCardItem,
)


class MethodologyService:
    """Service providing authoritative methodology and model card disclosures."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_methodology(self) -> MethodologyResponse:
        """Fetch current collection, sampling, and analytics methodology."""
        return MethodologyResponse(
            version="1.0.0",
            updated_at=datetime.now(UTC).isoformat(),
            collection_policy=CollectionPolicy(
                method="hybrid_historical_and_incremental",
                historical_sample_target=5000,
                weekly_refresh_policy="weekly_lookback_incremental_sync",
                language_scope=["en", "schinese", "russian", "all"],
                supported_review_types=["steam_purchased", "key_activation"],
                known_limitations=[
                    "Steam review cursor pagination can be subject to upstream rate limits.",
                    "Historical review volume is sampled according to representativeness policies.",
                    "Predictions reflect the declared model version and are strictly isolated.",
                ],
            ),
            definitions=MetricDefinitions(
                steam_recommendation=(
                    "Player recommendation flag (voted_up) submitted directly by Steam users."
                ),
                model_sentiment=(
                    "Machine learning inferred polarity on [-1.0, 1.0] scale: "
                    "(positive - negative) / classified_count."
                ),
                aspect_sentiment=(
                    "Sentence-grounded polarity classified strictly on evidence clauses "
                    "matching aspect taxonomy."
                ),
                topic_prevalence=(
                    "Primary assigned topic share over all primary assignments in corpus: "
                    "topic_count / total_assigned."
                ),
            ),
            data_retention=(
                "Adheres strictly to Steam Developer API terms. Author account identifiers "
                "and private profiles are scrubbed."
            ),
        )

    def get_model_cards(self) -> list[ModelCardItem]:
        """Fetch public model cards for registered/active ML models."""
        stmt = select(MLModel).order_by(MLModel.task.asc(), MLModel.created_at.desc())
        models = list(self.session.scalars(stmt).all())

        cards: list[ModelCardItem] = []
        for m in models:
            headline = {}
            if isinstance(m.metrics, dict):
                for k, v in m.metrics.items():
                    if isinstance(v, (int, float)):
                        headline[k] = round(float(v), 4)

            label_schema = []
            if isinstance(m.label_schema, dict):
                label_schema = list(m.label_schema.keys())
            elif isinstance(m.label_schema, list):
                label_schema = [str(x) for x in m.label_schema]
            elif m.task == "sentiment":
                label_schema = ["positive", "negative", "neutral"]

            cards.append(
                ModelCardItem(
                    model_id=m.id,
                    model_key=m.model_key,
                    version=m.version,
                    task=m.task,
                    framework=m.framework,
                    supported_languages=m.language_scope
                    if isinstance(m.language_scope, list)
                    else ["en"],
                    label_schema=label_schema,
                    evaluation_dataset_version=getattr(m, "dataset_version", None)
                    or "steam-reviews-eval-v1.0",
                    headline_metrics=headline,
                    known_limitations=[
                        "Model performs best on standard English game discourse.",
                        "Extreme slang or ASCII art may trigger lower confidence scores.",
                    ],
                    status="active" if m.is_active else "deprecated",
                    training_date=m.created_at.isoformat() if m.created_at else None,
                )
            )

        return cards

    def get_datasets(self) -> list[DatasetDocumentationItem]:
        """Fetch documentation on training and evaluation datasets."""
        return [
            DatasetDocumentationItem(
                dataset_version="steam-reviews-eval-v1.0",
                description=(
                    "Evaluation benchmark corpus for Steam game sentiment "
                    "and aspect classification."
                ),
                source="Steam Store Customer Reviews API",
                collection_window={"start": "2024-01-01", "end": "2026-10-01"},
                sampling_policy=(
                    "Stratified temporal sampling balanced across positive and "
                    "negative recommendations."
                ),
                language_scope=["en"],
                annotation_process=(
                    "Annotated under standard NLP annotation guidelines with "
                    "inter-annotator agreement verification."
                ),
                inclusion_rules=[
                    "Review text length must exceed 20 characters.",
                    "Must be written in supported language.",
                ],
                exclusion_rules=[
                    "Spam, ASCII art, or automated bot copypastas.",
                    "Empty review text.",
                ],
                limitations=[
                    "Biased toward popular indexed titles in catalog.",
                ],
                access_policy=(
                    "Public benchmark metadata; full text accessible under "
                    "research usage guidelines."
                ),
            )
        ]
