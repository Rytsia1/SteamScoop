"""Schemas for public methodology, model cards, and dataset documentation."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CollectionPolicy(BaseModel):
    """Collection policy metadata."""

    method: str = Field(
        description="Ingestion approach: historical windowed sampling + weekly refresh"
    )
    historical_sample_target: int = Field(description="Target review quota for historical seed")
    weekly_refresh_policy: str = Field(description="Incremental collection cadence and lookback")
    language_scope: list[str] = Field(description="List of supported review languages")
    supported_review_types: list[str] = Field(description="Steam purchase/review types collected")
    known_limitations: list[str] = Field(
        description="Known coverage constraints and sampling boundaries"
    )


class MetricDefinitions(BaseModel):
    """Formal definitions of exposed metrics."""

    steam_recommendation: str = Field(
        description="Binary player recommendation flag (voted_up) on Steam"
    )
    model_sentiment: str = Field(
        description="NLP model classification on [-1.0, 1.0] scale excluding neutral/unclassified"
    )
    aspect_sentiment: str = Field(
        description="Sentence-grounded polarity per controlled aspect category"
    )
    topic_prevalence: str = Field(
        description="Share of reviews assigned to a discovered thematic cluster"
    )


class MethodologyResponse(BaseModel):
    """Response payload for GET /methodology."""

    version: str = Field(description="Methodology document version")
    updated_at: str = Field(description="ISO timestamp of last methodology update")
    collection_policy: CollectionPolicy
    definitions: MetricDefinitions
    data_retention: str = Field(description="Steam privacy policy compliance and retention terms")


class ModelCardItem(BaseModel):
    """Public model card documenting ML model provenance and performance."""

    model_id: uuid.UUID
    model_key: str
    version: str
    task: str = Field(description="sentiment, absa, or topic")
    framework: str = Field(description="scikit-learn, transformers, etc.")
    supported_languages: list[str]
    label_schema: list[str]
    evaluation_dataset_version: str | None = None
    headline_metrics: dict[str, float] = Field(default_factory=dict)
    known_limitations: list[str] = Field(default_factory=list)
    status: str = Field(description="active or deprecated")
    training_date: str | None = None


class DatasetDocumentationItem(BaseModel):
    """Dataset specification and provenance."""

    dataset_version: str
    description: str
    source: str
    collection_window: dict[str, str]
    sampling_policy: str
    language_scope: list[str]
    annotation_process: str
    inclusion_rules: list[str]
    exclusion_rules: list[str]
    limitations: list[str]
    access_policy: str
