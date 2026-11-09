"""Topic modeling evaluation metrics and legacy compatibility module.

This module re-exports components from `app.ml.topic` for backward compatibility
with existing tests and services.
"""

from app.ml.topic.evaluator import (
    TopicModelEvaluator as TopicEvaluator,
)
from app.ml.topic.evaluator import (
    compute_mean_pairwise_jaccard,
    compute_topic_coherence_npmi,
    compute_topic_diversity,
)
from app.ml.topic.schemas import (
    HumanTopicEvaluationRubric,
    TopicMetrics,
)

__all__ = [
    "HumanTopicEvaluationRubric",
    "TopicEvaluator",
    "TopicMetrics",
    "compute_mean_pairwise_jaccard",
    "compute_topic_coherence_npmi",
    "compute_topic_diversity",
]
