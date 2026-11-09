import math
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field


class TopicMetrics(BaseModel):
    """Quantitative evaluation metrics for topic modeling outputs."""

    model_config = ConfigDict(frozen=True)

    num_topics: int = Field(ge=0, description="Total number of non-outlier topics discovered")
    topic_diversity: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of unique words among top-K terms across all topics",
    )
    mean_pairwise_jaccard: float = Field(
        ge=0.0,
        le=1.0,
        description="Average Jaccard overlap between topic top-K vocabularies (lower is better)",
    )
    outlier_count: int = Field(
        ge=0, description="Number of documents assigned to outlier (-1) cluster"
    )
    outlier_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction of documents classified as outliers"
    )
    topic_size_entropy: float = Field(
        ge=0.0,
        description="Shannon entropy of topic size distribution (measures balance)",
    )


class HumanTopicEvaluationRubric(BaseModel):
    """Qualitative rubric criteria for human review of candidate topic models."""

    model_config = ConfigDict(frozen=True)

    topic_id: str
    interpretability: int = Field(
        ge=1,
        le=5,
        description="1 (incoherent noise) to 5 (crystal-clear coherent theme)",
    )
    redundancy: int = Field(
        ge=1,
        le=5,
        description="1 (completely redundant duplicate) to 5 (fully distinct unique theme)",
    )
    domain_relevance: int = Field(
        ge=1,
        le=5,
        description="1 (irrelevant chatter/stopwords) to 5 (critical actionable gamer feedback)",
    )
    assignment_plausibility: int = Field(
        ge=1,
        le=5,
        description="1 (sample reviews don't fit) to 5 (sample reviews fit theme perfectly)",
    )
    suggested_label: str | None = Field(
        default=None, description="Curator-proposed human display label"
    )
    evaluator_notes: str | None = Field(default=None)


def compute_topic_diversity(topic_terms: list[list[str]], top_k: int = 10) -> float:
    """Calculate Topic Diversity: ratio of unique words across top-K terms of all topics.

    A value of 1.0 means no words are shared across topics (maximum diversity).
    A lower value indicates repetitive or redundant keywords across clusters.
    """
    if not topic_terms:
        return 0.0

    all_terms: list[str] = []
    for terms in topic_terms:
        all_terms.extend(terms[:top_k])

    if not all_terms:
        return 0.0

    unique_count = len(set(all_terms))
    return round(unique_count / len(all_terms), 4)


def compute_mean_pairwise_jaccard(topic_terms: list[list[str]], top_k: int = 10) -> float:
    """Calculate mean pairwise Jaccard similarity across topic top-K vocabularies.

    Lower values indicate greater separation and lower redundancy between topics.
    """
    num_topics = len(topic_terms)
    if num_topics < 2:
        return 0.0

    term_sets = [set(terms[:top_k]) for terms in topic_terms]
    pairwise_similarities: list[float] = []

    for i in range(num_topics):
        for j in range(i + 1, num_topics):
            union = len(term_sets[i] | term_sets[j])
            if union == 0:
                continue
            intersection = len(term_sets[i] & term_sets[j])
            pairwise_similarities.append(intersection / union)

    if not pairwise_similarities:
        return 0.0

    return round(sum(pairwise_similarities) / len(pairwise_similarities), 4)


def compute_topic_coherence_npmi(
    topic_terms: list[list[str]],
    tokenized_corpus: list[list[str]],
    top_k: int = 10,
    eps: float = 1e-12,
) -> float:
    """Compute average Normalized Pointwise Mutual Information (NPMI) coherence for top-K terms.

    NPMI ranges from -1 (words never co-occur) to +1 (words always co-occur together).
    """
    if not topic_terms or not tokenized_corpus:
        return 0.0

    total_docs = len(tokenized_corpus)
    if total_docs == 0:
        return 0.0

    # Build document-frequency and co-occurrence counts
    doc_sets = [set(doc) for doc in tokenized_corpus]
    word_doc_freq: Counter[str] = Counter()
    for s in doc_sets:
        word_doc_freq.update(s)

    topic_npmi_scores: list[float] = []

    for terms in topic_terms:
        k_terms = terms[:top_k]
        pairs_npmi: list[float] = []

        for i in range(len(k_terms)):
            for j in range(i + 1, len(k_terms)):
                w1, w2 = k_terms[i], k_terms[j]
                f1 = word_doc_freq[w1]
                f2 = word_doc_freq[w2]

                if f1 == 0 or f2 == 0:
                    continue

                # Count joint occurrences
                joint_docs = sum(1 for s in doc_sets if w1 in s and w2 in s)
                if joint_docs == 0:
                    pairs_npmi.append(-1.0)
                    continue

                p_w1 = f1 / total_docs
                p_w2 = f2 / total_docs
                p_joint = joint_docs / total_docs

                # PMI = log( P(w1, w2) / (P(w1)*P(w2)) )
                pmi = math.log((p_joint + eps) / (p_w1 * p_w2))
                # Normalized PMI = PMI / -log(P(w1, w2))
                npmi = pmi / (-math.log(p_joint + eps))
                # Bound between -1.0 and 1.0
                npmi = max(-1.0, min(1.0, npmi))
                pairs_npmi.append(npmi)

        if pairs_npmi:
            topic_npmi_scores.append(sum(pairs_npmi) / len(pairs_npmi))

    if not topic_npmi_scores:
        return 0.0

    return round(sum(topic_npmi_scores) / len(topic_npmi_scores), 4)


class TopicEvaluator:
    """Evaluates quality, stability, and human interpretability of topic modeling results."""

    def evaluate_model(
        self,
        topic_terms: list[list[str]],
        assignments: list[int],
        top_k: int = 10,
    ) -> TopicMetrics:
        """Evaluate topic model output arrays and return structured TopicMetrics."""
        total_docs = len(assignments)
        outlier_count = sum(1 for a in assignments if a == -1)
        outlier_rate = outlier_count / total_docs if total_docs > 0 else 0.0

        non_outliers = [a for a in assignments if a != -1]
        topic_counts = Counter(non_outliers)

        # Shannon entropy of cluster distribution
        entropy = 0.0
        if non_outliers:
            total_valid = len(non_outliers)
            for count in topic_counts.values():
                p = count / total_valid
                entropy -= p * math.log2(p)

        diversity = compute_topic_diversity(topic_terms, top_k=top_k)
        mean_jaccard = compute_mean_pairwise_jaccard(topic_terms, top_k=top_k)

        return TopicMetrics(
            num_topics=len(topic_terms),
            topic_diversity=diversity,
            mean_pairwise_jaccard=mean_jaccard,
            outlier_count=outlier_count,
            outlier_rate=round(outlier_rate, 4),
            topic_size_entropy=round(entropy, 4),
        )
