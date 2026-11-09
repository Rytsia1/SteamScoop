"""Pydantic schemas and data contracts for Aspect-Based Sentiment Analysis (ABSA).

Adheres to:
- Docs/ML_SPECIFICATION.md Section 6.7 (ABSA output contract)
- Docs/ML_SPECIFICATION.md Section 9.3 (ABSA evaluation metrics)
- Docs/ML_SPECIFICATION.md Section 9.7 (Provisional release gates)
- Docs/CODING_STANDARDS.md Section 5.1 (Pydantic v2 validation)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ml.taxonomy import AspectKey, SentimentLabel


class ABSAInput(BaseModel):
    """Input payload for single or batch ABSA inference."""

    model_config = ConfigDict(frozen=True)

    review_id: str = Field(description="Unique review identifier")
    text: str = Field(description="Normalized review text to be analyzed")
    language: str = Field(default="en", description="ISO 639-1 language code")


class AspectPredictionItem(BaseModel):
    """Single predicted aspect with polarity, confidence, evidence snippet, and offsets."""

    model_config = ConfigDict(frozen=True)

    aspect: AspectKey = Field(description="Machine key of detected aspect in controlled taxonomy")
    sentiment: SentimentLabel = Field(
        description="Predicted polarity for this specific aspect (positive, negative, neutral)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for aspect presence",
    )
    sentiment_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Calibrated probability of assigned sentiment class",
    )
    evidence_text: str | None = Field(
        default=None,
        description="Exact substring or sentence supporting the aspect judgment",
    )
    start_offset: int | None = Field(
        default=None,
        ge=0,
        description="Start character offset in normalized text",
    )
    end_offset: int | None = Field(
        default=None,
        ge=0,
        description="End character offset in normalized text",
    )
    probabilities: dict[str, float] = Field(
        default_factory=dict,
        description="Calibrated probability distribution across sentiment classes",
    )


class ABSAPredictionOutput(BaseModel):
    """Output contract for ABSA prediction on a review."""

    model_config = ConfigDict(frozen=True)

    review_id: str = Field(description="Unique review identifier")
    aspects: list[AspectPredictionItem] = Field(
        default_factory=list,
        description="List of detected aspect mentions with aspect-level polarity",
    )
    has_aspects: bool = Field(
        description="Flag indicating whether at least one aspect was identified with confidence"
    )
    model_key: str = Field(description="Unique identifier of model used for inference")
    model_version: str = Field(description="SemVer version of the deployed model")
    latency_ms: float = Field(ge=0.0, description="Inference execution latency in milliseconds")


class AspectDetectionMetrics(BaseModel):
    """Per-aspect detection precision, recall, F1, and support count."""

    model_config = ConfigDict(frozen=True)

    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    support: int = Field(ge=0)


class MultiLabelMetrics(BaseModel):
    """Aggregate multi-label aspect detection metrics."""

    model_config = ConfigDict(frozen=True)

    micro_f1: float = Field(ge=0.0, le=1.0)
    macro_f1: float = Field(ge=0.0, le=1.0)
    weighted_f1: float = Field(ge=0.0, le=1.0)
    subset_accuracy: float = Field(ge=0.0, le=1.0, description="Exact match ratio")
    hamming_loss: float = Field(ge=0.0, le=1.0)
    per_aspect: dict[str, AspectDetectionMetrics] = Field(default_factory=dict)


class AspectSentimentMetrics(BaseModel):
    """Polarity classification metrics evaluated across detected aspects."""

    model_config = ConfigDict(frozen=True)

    macro_f1: float = Field(ge=0.0, le=1.0)
    weighted_f1: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    per_class_f1: dict[str, float] = Field(default_factory=dict)
    confusion_matrix: list[list[int]] = Field(
        default_factory=list,
        description="3x3 confusion matrix [positive, negative, neutral]",
    )


class JointABSAMetrics(BaseModel):
    """End-to-end joint ABSA metrics requiring BOTH correct aspect and correct polarity."""

    model_config = ConfigDict(frozen=True)

    joint_micro_f1: float = Field(ge=0.0, le=1.0)
    joint_macro_f1: float = Field(ge=0.0, le=1.0)
    joint_precision: float = Field(ge=0.0, le=1.0)
    joint_recall: float = Field(ge=0.0, le=1.0)


class ThresholdTuningPoint(BaseModel):
    """Evaluation point for confidence threshold sweep."""

    model_config = ConfigDict(frozen=True)

    threshold: float = Field(ge=0.0, le=1.0)
    micro_f1: float = Field(ge=0.0, le=1.0)
    macro_f1: float = Field(ge=0.0, le=1.0)
    coverage_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of reviews receiving at least one predicted aspect",
    )


class ABSAReleaseGateResult(BaseModel):
    """Assessment against ML_SPECIFICATION.md Section 9.7 ABSA release gates."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(
        description="APPROVED (ready for production), CANDIDATE (experimental), REJECTED"
    )
    detection_micro_f1: float = Field(ge=0.0, le=1.0)
    detection_macro_f1: float = Field(ge=0.0, le=1.0)
    sentiment_macro_f1: float = Field(ge=0.0, le=1.0)
    joint_macro_f1: float = Field(ge=0.0, le=1.0)
    passed_gates: bool
    failures: list[str] = Field(default_factory=list)


class ABSAEvaluationReport(BaseModel):
    """Full comprehensive ABSA evaluation report."""

    model_config = ConfigDict(frozen=True)

    model_key: str
    model_version: str
    dataset_version: str
    detection_metrics: MultiLabelMetrics
    sentiment_metrics: AspectSentimentMetrics
    joint_metrics: JointABSAMetrics
    threshold_analysis: list[ThresholdTuningPoint]
    slice_performance: dict[str, Any] = Field(default_factory=dict)
    release_gate: ABSAReleaseGateResult
    justification_summary: str = Field(
        description="Technical justification evaluating multi-label vs span extraction"
    )
