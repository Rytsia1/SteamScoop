from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TFIDFHyperparameters(BaseModel):
    """Hyperparameter configuration for TF-IDF feature extraction."""

    model_config = ConfigDict(frozen=True)

    max_features: int = Field(default=10000, ge=100, le=100000)
    ngram_range: tuple[int, int] = Field(default=(1, 2))
    min_df: int = Field(default=2, ge=1)
    max_df: float = Field(default=0.95, gt=0.0, le=1.0)
    sublinear_tf: bool = Field(default=True)


class LinearClassifierHyperparameters(BaseModel):
    """Hyperparameter configuration for linear classifiers (Logistic Regression, Linear SVC)."""

    model_config = ConfigDict(frozen=True)

    classifier_type: str = Field(
        default="logistic_regression", description="'logistic_regression' or 'linear_svc'"
    )
    c_regularization: float = Field(default=1.0, gt=0.0)
    class_weight: str | None = Field(default="balanced", description="'balanced' or None")
    max_iter: int = Field(default=1000, ge=100)
    random_state: int = Field(default=42)


class TransformerHyperparameters(BaseModel):
    """Hyperparameters for pretrained transformer fine-tuning candidates."""

    model_config = ConfigDict(frozen=True)

    base_model_name: str = Field(default="distilbert-base-uncased")
    max_sequence_length: int = Field(default=256, ge=32, le=512)
    batch_size: int = Field(default=32, ge=1, le=256)
    learning_rate: float = Field(default=2e-5, gt=0.0)
    num_epochs: int = Field(default=3, ge=1, le=20)
    weight_decay: float = Field(default=0.01, ge=0.0)
    warmup_ratio: float = Field(default=0.1, ge=0.0, le=0.5)
    random_state: int = Field(default=42)


class TopicModelHyperparameters(BaseModel):
    """Hyperparameters for baseline topic modeling (NMF, LDA)."""

    model_config = ConfigDict(frozen=True)

    method: str = Field(default="nmf", description="'nmf' or 'lda'")
    num_topics: int = Field(default=10, ge=2, le=100)
    max_features: int = Field(default=5000, ge=100)
    random_state: int = Field(default=42)


class ExperimentConfig(BaseModel):
    """Reproducible experiment definition complying with ML_SPECIFICATION.md Section 13.2."""

    model_config = ConfigDict(frozen=True)

    experiment_name: str = Field(
        description="Logical experiment name (e.g. sentiment-baseline-tfidf)"
    )
    experiment_id: str = Field(description="Unique run identifier")
    task: str = Field(description="'sentiment', 'absa', or 'topic'")
    dataset_version: str = Field(description="Immutable dataset manifest version")
    dataset_manifest_path: str = Field(description="Relative path to dataset manifest JSON")
    preprocessing_version: str = Field(default="v1.0.0")
    random_seed: int = Field(default=42)
    hyperparameters: dict[str, Any] = Field(description="Serialized task-specific hyperparameters")
    metrics_tracked: list[str] = Field(
        default_factory=lambda: [
            "macro_f1",
            "weighted_f1",
            "accuracy",
            "per_class_f1",
            "confusion_matrix",
        ],
    )
    acceptance_criteria: dict[str, float] = Field(
        default_factory=lambda: {"min_macro_f1": 0.80},
        description="Gate criteria for release consideration",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
