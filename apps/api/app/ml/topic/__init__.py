"""SteamScoop Topic Modeling package.

Provides per-game topic modeling, candidate benchmarking (NMF, LDA, Semantic Clustering),
coherence/diversity evaluation, human curation, and PostgreSQL persistence.
"""

from app.ml.topic.curation import TopicCurationService
from app.ml.topic.evaluator import (
    TopicModelEvaluator,
    compute_mean_pairwise_jaccard,
    compute_topic_coherence_npmi,
    compute_topic_diversity,
    evaluate_topic_stability,
)
from app.ml.topic.models import (
    BaseTopicModel,
    LDATopicModel,
    NMFTopicModel,
    SemanticClusterTopicModel,
)
from app.ml.topic.pipeline import InsufficientCorpusError, TopicTrainingPipeline
from app.ml.topic.preprocessor import (
    STEAM_DOMAIN_STOP_WORDS,
    TopicPreprocessor,
    TopicTextPreprocessor,
)
from app.ml.topic.registry import TopicModelRegistryService
from app.ml.topic.schemas import (
    CorpusFilterConfig,
    HumanTopicEvaluationRubric,
    RawDocument,
    ReviewTopicAssignment,
    TopicEvaluationReport,
    TopicMetrics,
    TopicRepresentation,
    TopicTerm,
)

__all__ = [
    "BaseTopicModel",
    "CorpusFilterConfig",
    "HumanTopicEvaluationRubric",
    "InsufficientCorpusError",
    "LDATopicModel",
    "NMFTopicModel",
    "RawDocument",
    "ReviewTopicAssignment",
    "STEAM_DOMAIN_STOP_WORDS",
    "SemanticClusterTopicModel",
    "TopicCurationService",
    "TopicEvaluationReport",
    "TopicModelEvaluator",
    "TopicModelRegistryService",
    "TopicMetrics",
    "TopicPreprocessor",
    "TopicRepresentation",
    "TopicTerm",
    "TopicTextPreprocessor",
    "TopicTrainingPipeline",
    "compute_mean_pairwise_jaccard",
    "compute_topic_coherence_npmi",
    "compute_topic_diversity",
    "evaluate_topic_stability",
]
