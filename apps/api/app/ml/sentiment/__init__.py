"""SteamScoop Sentiment Analysis module.

Exposes core classifiers, evaluators, training pipelines, and schemas.
"""

from app.ml.sentiment.classifier import (
    BaseSentimentClassifier,
    MajorityBaseline,
    TfidfComplementNaiveBayes,
    TfidfLinearSVM,
    TfidfLogisticRegression,
)
from app.ml.sentiment.evaluator import SentimentEvaluator
from app.ml.sentiment.pipeline import SentimentTrainingPipeline
from app.ml.sentiment.registry import ModelRegistryService
from app.ml.sentiment.schemas import (
    ClassMetrics,
    ConfusionMatrixData,
    ReleaseGateResult,
    SentimentEvaluationReport,
    SentimentInput,
    SentimentPredictionOutput,
    SlicePerformance,
)

__all__ = [
    "BaseSentimentClassifier",
    "ClassMetrics",
    "ConfusionMatrixData",
    "MajorityBaseline",
    "ModelRegistryService",
    "ReleaseGateResult",
    "SentimentEvaluationReport",
    "SentimentEvaluator",
    "SentimentInput",
    "SentimentPredictionOutput",
    "SentimentTrainingPipeline",
    "SlicePerformance",
    "TfidfComplementNaiveBayes",
    "TfidfLinearSVM",
    "TfidfLogisticRegression",
]
