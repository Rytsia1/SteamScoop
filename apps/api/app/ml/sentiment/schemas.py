"""Pydantic schemas and output contracts for SteamScoop sentiment analysis.

Complies with ML_SPECIFICATION.md Section 5.4, 8.3, and 9.2:
- Three-class sentiment target space: positive, negative, neutral.
- Output contract with task, label, confidence, probability distribution, and model version.
- Structured evaluation metrics including macro-F1, per-class metrics, confusion matrices,
  coverage, abstention rates, and domain slice performance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ml.taxonomy import SentimentLabel


class SentimentInput(BaseModel):
    """Input record for sentiment classification."""

    model_config = ConfigDict(frozen=True)

    review_id: str
    text: str
    language: str = "en"
    steam_app_id: int | None = None
    voted_up: bool | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SentimentPredictionOutput(BaseModel):
    """Immutable prediction contract matching ML_SPECIFICATION.md Section 5.4."""

    model_config = ConfigDict(frozen=True)

    task: str = "sentiment"
    review_id: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float] = Field(
        description="Probability distribution across positive, negative, neutral"
    )
    is_abstained: bool = Field(
        default=False,
        description="True if confidence falls below the model decision threshold",
    )
    model_key: str
    model_version: str


class ClassMetrics(BaseModel):
    """Per-class classification performance metrics."""

    model_config = ConfigDict(frozen=True)

    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1_score: float = Field(ge=0.0, le=1.0)
    support: int = Field(ge=0)


class ConfusionMatrixData(BaseModel):
    """Structured 3x3 confusion matrix."""

    model_config = ConfigDict(frozen=True)

    labels: list[str] = Field(default_factory=lambda: [lbl.value for lbl in SentimentLabel])
    matrix: list[list[int]] = Field(description="Raw counts: matrix[true_idx][pred_idx]")
    normalized_matrix: list[list[float]] = Field(
        description="Row-normalized proportions (recall per cell)"
    )


class SlicePerformance(BaseModel):
    """Metrics for specific data slices (language, temporal, length, sarcasm)."""

    model_config = ConfigDict(frozen=True)

    slice_name: str
    sample_count: int = Field(ge=0)
    macro_f1: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    notes: str = ""


class SentimentEvaluationReport(BaseModel):
    """Comprehensive evaluation metrics complying with ML_SPECIFICATION.md Section 9.2."""

    model_config = ConfigDict(frozen=True)

    model_key: str
    model_version: str
    dataset_version: str
    split_name: str
    sample_count: int
    macro_f1: float = Field(ge=0.0, le=1.0)
    weighted_f1: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    class_metrics: dict[str, ClassMetrics]
    confusion_matrix: ConfusionMatrixData
    confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    coverage_rate: float = Field(ge=0.0, le=1.0)
    abstention_count: int = Field(ge=0)
    effective_macro_f1: float = Field(
        ge=0.0, le=1.0, description="Macro F1 on confident (non-abstained) predictions"
    )
    slice_performance: list[SlicePerformance] = Field(default_factory=list)
    brier_score: float = Field(ge=0.0, description="Multi-class Brier score calibration metric")
    evaluated_at: str


class ReleaseGateResult(BaseModel):
    """Assessment against ML_SPECIFICATION.md Section 14 & 16 Release Gates."""

    model_config = ConfigDict(frozen=True)

    passed: bool
    status: str = Field(description="'APPROVED', 'CANDIDATE', or 'REJECTED_FOR_PRODUCTION'")
    min_macro_f1_threshold: float = 0.75
    actual_macro_f1: float
    min_class_recall_threshold: float = 0.60
    actual_class_recalls: dict[str, float]
    min_coverage_threshold: float = 0.80
    actual_coverage: float
    zero_leakage_verified: bool
    gate_details: list[str] = Field(default_factory=list)
