"""Unit tests for topic model evaluation metrics and TopicModelEvaluator."""

from app.ml.topic.evaluator import (
    TopicModelEvaluator,
    compute_mean_pairwise_jaccard,
    compute_topic_coherence_npmi,
    compute_topic_diversity,
    evaluate_topic_stability,
)
from app.ml.topic.models import NMFTopicModel
from app.ml.topic.schemas import RawDocument


def test_diversity_metrics() -> None:
    # Completely disjoint topic vocabularies -> 1.0 diversity
    topics_disjoint = [
        ["combat", "gunplay", "weapons"],
        ["story", "characters", "writing"],
    ]
    assert compute_topic_diversity(topics_disjoint, top_k=3) == 1.0

    # Overlapping vocabularies
    topics_overlap = [
        ["game", "combat", "weapons"],
        ["game", "combat", "story"],
    ]
    div = compute_topic_diversity(topics_overlap, top_k=3)
    # 4 distinct words ("game", "combat", "weapons", "story") out of 6 slots -> 4/6 = 0.6667
    assert round(div, 2) == 0.67


def test_pairwise_jaccard_metrics() -> None:
    topics = [
        ["combat", "weapons", "gunplay"],
        ["combat", "weapons", "story"],
    ]
    # Intersect = 2, Union = 4 -> 0.50
    jaccard = compute_mean_pairwise_jaccard(topics, top_k=3)
    assert jaccard == 0.50


def test_npmi_coherence() -> None:
    corpus = [
        ["combat", "weapons", "gunplay", "smooth"],
        ["combat", "weapons", "great", "gunplay"],
        ["story", "writing", "characters"],
        ["narrative", "story", "lore"],
    ]
    topic_terms = [["combat", "weapons", "gunplay"]]
    npmi = compute_topic_coherence_npmi(topic_terms, corpus, top_k=3)
    # High co-occurrence -> positive NPMI
    assert npmi > 0.0


def test_stability_evaluation() -> None:
    docs = [
        RawDocument(review_id="1", text="Combat mechanics are fast and responsive."),
        RawDocument(review_id="2", text="Gunplay is punchy, combat is enjoyable."),
        RawDocument(review_id="3", text="Stuttering and low FPS ruin performance."),
        RawDocument(review_id="4", text="Terrible lag and frame rate drops constantly."),
    ]
    stability = evaluate_topic_stability(
        model_factory=lambda s: NMFTopicModel(
            model_key="stability-test", num_topics=2, random_seed=s
        ),
        documents=docs,
        seeds=[42, 100],
        top_k=3,
    )
    assert 0.0 <= stability <= 1.0


def test_evaluator_complete_report() -> None:
    docs = [
        RawDocument(review_id="1", text="Combat and gunplay are top tier."),
        RawDocument(review_id="2", text="Weapons feel great with fun combat."),
        RawDocument(review_id="3", text="Terrible stutter and crashes."),
        RawDocument(review_id="4", text="Low FPS and constant lag."),
        RawDocument(review_id="5", text="Great character writing and deep story."),
        RawDocument(review_id="6", text="Compelling narrative and emotional story."),
    ]
    model = NMFTopicModel(model_key="test-eval", num_topics=3, random_seed=42)
    model.fit(docs)

    evaluator = TopicModelEvaluator()
    report = evaluator.evaluate(
        model=model,
        documents=docs,
        steam_app_id=1091500,
        model_version="v1.0.0",
        top_k=3,
    )

    assert report.model_key == "test-eval"
    assert report.steam_app_id == 1091500
    assert report.metrics.num_topics == 3
    assert report.metrics.topic_diversity > 0.0
    assert report.metrics.topic_size_entropy > 0.0
    assert len(report.topics) == 3
