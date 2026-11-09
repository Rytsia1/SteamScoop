"""Unit tests for TopicEvaluator and human topic rubric according to ML_SPECIFICATION.md Section 11."""

from app.ml.topics import (
    HumanTopicEvaluationRubric,
    TopicEvaluator,
    compute_mean_pairwise_jaccard,
    compute_topic_coherence_npmi,
    compute_topic_diversity,
)


def test_topic_diversity_unique_words() -> None:
    topics = [
        ["combat", "gameplay", "sword", "parry", "boss"],
        ["story", "lore", "dialogue", "characters", "narrative"],
    ]
    diversity = compute_topic_diversity(topics, top_k=5)
    # All 10 words are distinct -> diversity should be 1.0
    assert diversity == 1.0


def test_topic_diversity_repetitive_words() -> None:
    topics = [
        ["game", "play", "good", "fun", "bad"],
        ["game", "play", "good", "fun", "worst"],
    ]
    diversity = compute_topic_diversity(topics, top_k=5)
    # 6 unique words out of 10 slots -> 0.6
    assert round(diversity, 2) == 0.60


def test_mean_pairwise_jaccard() -> None:
    topics = [
        ["graphics", "visuals", "art", "lighting"],
        ["graphics", "visuals", "textures", "rendering"],
    ]
    # Intersect = 2 ('graphics', 'visuals'), Union = 6 -> 2/6 = 0.3333
    jaccard = compute_mean_pairwise_jaccard(topics, top_k=4)
    assert round(jaccard, 3) == 0.333


def test_npmi_coherence_calculation() -> None:
    corpus = [
        ["the", "graphics", "and", "art", "style", "are", "stunning"],
        ["stunning", "graphics", "with", "ray", "tracing", "and", "art"],
        ["great", "graphics", "and", "beautiful", "art", "direction"],
        ["combat", "is", "fun", "and", "responsive"],
    ]
    topic_terms = [["graphics", "art", "stunning"]]
    npmi = compute_topic_coherence_npmi(topic_terms, corpus, top_k=3)
    # Frequently co-occurring words in the small corpus should have positive NPMI
    assert npmi > 0.0


def test_topic_evaluator_metrics() -> None:
    evaluator = TopicEvaluator()
    topic_terms = [
        ["combat", "gameplay", "sword"],
        ["story", "lore", "dialogue"],
    ]
    assignments = [0, 0, 1, 1, 1, -1]  # 1 outlier out of 6
    metrics = evaluator.evaluate_model(topic_terms, assignments, top_k=3)

    assert metrics.num_topics == 2
    assert metrics.outlier_count == 1
    assert round(metrics.outlier_rate, 2) == 0.17
    assert metrics.topic_diversity == 1.0
    assert metrics.topic_size_entropy > 0.0


def test_human_topic_rubric_validation() -> None:
    rubric = HumanTopicEvaluationRubric(
        topic_id="topic_001",
        interpretability=5,
        redundancy=1,
        domain_relevance=5,
        assignment_plausibility=4,
        suggested_label="Performance & Technical Issues",
        evaluator_notes="Clearly represents performance and technical stability issues.",
    )
    assert rubric.topic_id == "topic_001"
    assert rubric.interpretability == 5
    assert rubric.suggested_label == "Performance & Technical Issues"
