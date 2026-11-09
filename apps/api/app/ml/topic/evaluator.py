"""Comprehensive evaluation metrics and quality benchmarking for topic models.

Implements:
1. Topic Diversity: Ratio of unique words across topic top-K vocabularies.
2. Mean Pairwise Jaccard: Vocabulary overlap between topic clusters (redundancy).
3. Coherence (NPMI): Normalized Pointwise Mutual Information across co-occurrence matrices.
4. Stability: Vocabulary persistence across random initializations and seeds.
5. Outlier Rate: Identification and accounting of noise documents.
6. Entropy: Shannon entropy of document distribution across topics.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable

from app.ml.topic.models import BaseTopicModel
from app.ml.topic.preprocessor import TopicPreprocessor
from app.ml.topic.schemas import (
    RawDocument,
    TopicEvaluationReport,
    TopicMetrics,
)


def compute_topic_diversity(topic_terms: list[list[str]], top_k: int = 10) -> float:
    """Calculate Topic Diversity: ratio of unique words across top-K terms of all topics."""
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
    """Calculate mean pairwise Jaccard similarity across topic top-K vocabularies."""
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
    """Compute average Normalized Pointwise Mutual Information (NPMI) coherence for top-K terms."""
    if not topic_terms or not tokenized_corpus:
        return 0.0

    total_docs = len(tokenized_corpus)
    if total_docs == 0:
        return 0.0

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

                joint_docs = sum(1 for s in doc_sets if w1 in s and w2 in s)
                if joint_docs == 0:
                    pairs_npmi.append(-1.0)
                    continue

                p_w1 = f1 / total_docs
                p_w2 = f2 / total_docs
                p_joint = joint_docs / total_docs

                pmi = math.log((p_joint + eps) / (p_w1 * p_w2))
                npmi = pmi / (-math.log(p_joint + eps))
                npmi = max(-1.0, min(1.0, npmi))
                pairs_npmi.append(npmi)

        if pairs_npmi:
            topic_npmi_scores.append(sum(pairs_npmi) / len(pairs_npmi))

    if not topic_npmi_scores:
        return 0.0

    return round(sum(topic_npmi_scores) / len(topic_npmi_scores), 4)


def evaluate_topic_stability(
    model_factory: Callable[[int], BaseTopicModel],
    documents: list[RawDocument],
    seeds: list[int] | None = None,
    top_k: int = 10,
) -> float:
    """Evaluate topic vocabulary stability across multiple random seed initializations."""
    test_seeds = seeds or [42, 100, 2024]
    if len(test_seeds) < 2:
        return 1.0

    topic_sets_by_seed: list[list[set[str]]] = []
    for s in test_seeds:
        m = model_factory(s)
        m.fit(documents)
        terms = m.get_topic_terms(top_k=top_k)
        topic_sets_by_seed.append([set(t) for t in terms])

    # Compute average pairwise Jaccard across corresponding topics
    pairwise_stabilities: list[float] = []
    for i in range(len(test_seeds)):
        for j in range(i + 1, len(test_seeds)):
            sets1 = topic_sets_by_seed[i]
            sets2 = topic_sets_by_seed[j]
            # Match each topic in sets1 with most similar topic in sets2
            for s1 in sets1:
                best_jaccard = max(
                    (len(s1 & s2) / len(s1 | s2) if len(s1 | s2) > 0 else 0.0) for s2 in sets2
                )
                pairwise_stabilities.append(best_jaccard)

    if not pairwise_stabilities:
        return 1.0
    return round(sum(pairwise_stabilities) / len(pairwise_stabilities), 4)


class TopicModelEvaluator:
    """Evaluates candidate topic models and produces quantitative reports."""

    def __init__(self, preprocessor: TopicPreprocessor | None = None) -> None:
        self.preprocessor = preprocessor or TopicPreprocessor()

    def evaluate_model(
        self,
        topic_terms: list[list[str]],
        assignments: list[int],
        top_k: int = 10,
    ) -> TopicMetrics:
        """Evaluate raw topic term lists and integer assignments."""
        total_docs = len(assignments)
        outlier_count = sum(1 for a in assignments if a == -1)
        outlier_rate = outlier_count / total_docs if total_docs > 0 else 0.0

        non_outliers = [a for a in assignments if a != -1]
        topic_counts = Counter(non_outliers)

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
            npmi_coherence=0.0,
            outlier_count=outlier_count,
            outlier_rate=round(outlier_rate, 4),
            topic_size_entropy=round(entropy, 4),
            stability_score=1.0,
        )

    def evaluate(
        self,
        model: BaseTopicModel,
        documents: list[RawDocument],
        steam_app_id: int,
        model_version: str = "v1.0.0",
        top_k: int = 10,
        model_factory: Callable[[int], BaseTopicModel] | None = None,
    ) -> TopicEvaluationReport:
        """Run complete quantitative evaluation suite on a fitted topic model."""
        topics, assignments = model.transform(documents)
        topic_terms = model.get_topic_terms(top_k=top_k)

        # 1. Outlier rate and counts
        total_docs = len(assignments)
        outlier_count = sum(1 for a in assignments if a.is_outlier)
        outlier_rate = outlier_count / total_docs if total_docs > 0 else 0.0

        # 2. Topic size entropy
        non_outliers = [a.topic_id for a in assignments if not a.is_outlier]
        topic_counts = Counter(non_outliers)
        entropy = 0.0
        if non_outliers:
            total_valid = len(non_outliers)
            for cnt in topic_counts.values():
                p = cnt / total_valid
                entropy -= p * math.log2(p)

        # 3. Topic diversity and pairwise Jaccard
        diversity = compute_topic_diversity(topic_terms, top_k=top_k)
        mean_jaccard = compute_mean_pairwise_jaccard(topic_terms, top_k=top_k)

        # 4. NPMI Coherence
        tokenized_corpus = [self.preprocessor.tokenize(doc.text) for doc in documents]
        npmi = compute_topic_coherence_npmi(topic_terms, tokenized_corpus, top_k=top_k)

        # 5. Stability across seeds
        stability = 1.0
        if model_factory is not None:
            stability = evaluate_topic_stability(model_factory, documents, top_k=top_k)

        metrics = TopicMetrics(
            num_topics=len(topics),
            topic_diversity=diversity,
            mean_pairwise_jaccard=mean_jaccard,
            npmi_coherence=npmi,
            outlier_count=outlier_count,
            outlier_rate=round(outlier_rate, 4),
            topic_size_entropy=round(entropy, 4),
            stability_score=stability,
        )

        return TopicEvaluationReport(
            model_key=model.model_key,
            model_version=model_version,
            steam_app_id=steam_app_id,
            corpus_size=total_docs,
            metrics=metrics,
            topics=topics,
            curated=False,
        )
