"""Pydantic schemas and data contracts for SteamScoop Topic Modeling.

Adheres to:
- Docs/ML_SPECIFICATION.md Section 7 (Topic modeling specification)
- Docs/ML_SPECIFICATION.md Section 9.4 (Topic modeling metrics)
- Docs/DATABASE_DESIGN.md Section 5.3 (Topic & ReviewTopic models)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CorpusFilterConfig(BaseModel):
    """Configuration for building a per-game and per-language topic corpus."""

    model_config = ConfigDict(frozen=True)

    steam_app_id: int = Field(description="Steam Application ID for per-game corpus")
    language: str = Field(default="en", description="Target ISO 639-1 language code")
    min_corpus_size: int = Field(
        default=25,
        ge=1,
        description="Minimum review count required to fit and publish topics",
    )
    min_char_length: int = Field(
        default=20,
        ge=5,
        description="Minimum review character length for inclusion",
    )
    min_word_length: int = Field(
        default=4,
        ge=1,
        description="Minimum review word count for inclusion",
    )
    deduplicate: bool = Field(
        default=True,
        description="Whether to exclude exact duplicate reviews from the corpus",
    )


class RawDocument(BaseModel):
    """Single input document for topic modeling corpus."""

    model_config = ConfigDict(frozen=True)

    review_id: str
    text: str
    language: str = "en"
    voted_up: bool = True
    metadata_: dict[str, Any] = Field(default_factory=dict)


class TopicTerm(BaseModel):
    """Single salient term with its model weight."""

    model_config = ConfigDict(frozen=True)

    term: str
    weight: float = Field(ge=0.0)


class TopicRepresentation(BaseModel):
    """Complete structured definition of a discovered topic."""

    model_config = ConfigDict(frozen=True)

    topic_id: int = Field(description="Internal model cluster index (-1 for outlier)")
    topic_key: str = Field(description="Stable machine key for database persistence")
    label: str = Field(description="Human-readable title (auto-generated or curated)")
    description: str | None = Field(default=None, description="Detailed explanatory scope")
    keywords: list[str] = Field(description="Ordered list of top keyword strings")
    representative_terms: list[TopicTerm] = Field(
        default_factory=list, description="Terms with feature weights"
    )
    representative_reviews: list[str] = Field(
        default_factory=list, description="Review IDs or quotes strongly assigned to topic"
    )
    doc_count: int = Field(ge=0, description="Total documents assigned to this topic")
    is_outlier: bool = Field(
        default=False, description="Flag indicating whether this represents noise/unassigned"
    )


class ReviewTopicAssignment(BaseModel):
    """Association between a review and a topic output."""

    model_config = ConfigDict(frozen=True)

    review_id: str
    topic_id: int
    topic_key: str
    score: float = Field(ge=0.0, le=1.0, description="Assignment score / loading / similarity")
    is_primary: bool = Field(
        default=True, description="Flag indicating the single primary topic for this review"
    )
    is_outlier: bool = Field(default=False)


class TopicMetrics(BaseModel):
    """Quantitative evaluation metrics for topic model quality."""

    model_config = ConfigDict(frozen=True)

    num_topics: int = Field(ge=0, description="Total non-outlier topics discovered")
    topic_diversity: float = Field(
        ge=0.0,
        le=1.0,
        description="Ratio of unique words among top-K terms across all topics (higher is better)",
    )
    mean_pairwise_jaccard: float = Field(
        ge=0.0,
        le=1.0,
        description="Average Jaccard overlap between topic vocabularies (lower is better)",
    )
    npmi_coherence: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Average Normalized Pointwise Mutual Information coherence",
    )
    outlier_count: int = Field(ge=0, description="Count of documents assigned to outlier cluster")
    outlier_rate: float = Field(ge=0.0, le=1.0, description="Fraction of documents as outliers")
    topic_size_entropy: float = Field(
        ge=0.0, description="Shannon entropy of topic size distribution"
    )
    stability_score: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Vocabulary stability across resampled partitions or seeds",
    )


class HumanTopicEvaluationRubric(BaseModel):
    """Qualitative rubric for human inspection and curation of candidate topics."""

    model_config = ConfigDict(frozen=True)

    topic_key: str = Field(default="", description="Topic machine key")
    topic_id: str | None = Field(default=None, description="Topic cluster identifier")
    interpretability: int = Field(ge=1, le=5, description="1 (noise) to 5 (coherent theme)")
    redundancy: int = Field(ge=1, le=5, description="1 (redundant duplicate) to 5 (distinct)")
    domain_relevance: int = Field(ge=1, le=5, description="1 (trivial chatter) to 5 (critical)")
    assignment_plausibility: int = Field(ge=1, le=5, description="1 (poor fit) to 5 (great fit)")
    suggested_label: str | None = Field(default=None, description="Curator-proposed human title")
    evaluator_notes: str | None = Field(default=None)


class TopicEvaluationReport(BaseModel):
    """Full evaluation and provenance report for a topic model run."""

    model_config = ConfigDict(frozen=True)

    model_key: str
    model_version: str
    steam_app_id: int
    corpus_size: int
    metrics: TopicMetrics
    topics: list[TopicRepresentation]
    human_evaluation: list[HumanTopicEvaluationRubric] = Field(default_factory=list)
    curated: bool = Field(default=False, description="Whether human curation has been applied")
