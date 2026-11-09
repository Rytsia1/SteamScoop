"""Aspect-Based Sentiment Analysis (ABSA) module."""

from app.ml.absa.classifier import (
    BaseABSAClassifier,
    DocumentTfidfABSA,
    MajorityBaselineABSA,
    SentenceGroundedTfidfABSA,
)
from app.ml.absa.evaluator import ABSAEvaluator
from app.ml.absa.pipeline import ABSATrainingPipeline
from app.ml.absa.registry import ABSAModelRegistryService
from app.ml.absa.schemas import (
    ABSAEvaluationReport,
    ABSAInput,
    ABSAPredictionOutput,
    ABSAReleaseGateResult,
    AspectDetectionMetrics,
    AspectPredictionItem,
    AspectSentimentMetrics,
    JointABSAMetrics,
    MultiLabelMetrics,
    ThresholdTuningPoint,
)

__all__ = [
    "BaseABSAClassifier",
    "MajorityBaselineABSA",
    "DocumentTfidfABSA",
    "SentenceGroundedTfidfABSA",
    "ABSAEvaluator",
    "ABSATrainingPipeline",
    "ABSAModelRegistryService",
    "ABSAInput",
    "AspectPredictionItem",
    "ABSAPredictionOutput",
    "AspectDetectionMetrics",
    "MultiLabelMetrics",
    "AspectSentimentMetrics",
    "JointABSAMetrics",
    "ThresholdTuningPoint",
    "ABSAReleaseGateResult",
    "ABSAEvaluationReport",
]
