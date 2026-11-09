"""Unit tests for topic model architectures: NMF, LDA, and Semantic Clustering."""

from pathlib import Path

from app.ml.topic.models import (
    LDATopicModel,
    NMFTopicModel,
    SemanticClusterTopicModel,
)
from app.ml.topic.schemas import RawDocument


def sample_documents() -> list[RawDocument]:
    return [
        RawDocument(
            review_id="1", text="Great combat mechanics with crisp gunplay and responsive dodge."
        ),
        RawDocument(
            review_id="2", text="Gunplay is fantastic, weapons feel weighty and combat is fun."
        ),
        RawDocument(review_id="3", text="Combat and gunplay are top tier in this shooter."),
        RawDocument(review_id="4", text="Terrible performance, constant stuttering and FPS drops."),
        RawDocument(
            review_id="5", text="Unplayable stutter and lag, frame rate crashes constantly."
        ),
        RawDocument(review_id="6", text="Severe performance issues, low FPS and frequent crashes."),
        RawDocument(
            review_id="7",
            text="The story and character writing are deeply emotional and compelling.",
        ),
        RawDocument(
            review_id="8",
            text="Brilliant narrative depth, memorable characters and great dialogue.",
        ),
        RawDocument(
            review_id="9", text="Emotional story arc and incredible quest writing throughout."
        ),
        RawDocument(review_id="10", text="Ok."),  # Outlier candidate
    ]


def test_nmf_fit_transform_and_serialization(tmp_path: Path) -> None:
    docs = sample_documents()
    model = NMFTopicModel(model_key="test-nmf", num_topics=3, random_seed=42)
    model.fit(docs)

    assert model.is_fitted
    assert len(model.get_topic_terms()) == 3

    topics, assignments = model.transform(docs)
    assert len(topics) == 3
    assert len(assignments) == len(docs)

    # Check top terms contain domain keywords
    all_terms = model.get_topic_terms(top_k=5)
    flat_terms = [t for sub in all_terms for t in sub]
    assert any(
        w in flat_terms for w in ["combat", "gunplay", "fps", "stuttering", "story", "writing"]
    )

    # Test serialization
    save_path = tmp_path / "nmf_model.joblib"
    model.save(save_path)
    loaded = NMFTopicModel.load(save_path)
    assert loaded.is_fitted
    assert loaded.model_key == "test-nmf"

    _, loaded_assignments = loaded.transform(docs)
    assert len(loaded_assignments) == len(assignments)


def test_lda_fit_transform_and_serialization(tmp_path: Path) -> None:
    docs = sample_documents()
    model = LDATopicModel(model_key="test-lda", num_topics=3, random_seed=42)
    model.fit(docs)

    assert model.is_fitted
    topics, assignments = model.transform(docs)
    assert len(topics) == 3
    assert len(assignments) == len(docs)

    # Test serialization
    save_path = tmp_path / "lda_model.joblib"
    model.save(save_path)
    loaded = LDATopicModel.load(save_path)
    assert loaded.is_fitted
    assert loaded.model_key == "test-lda"


def test_semantic_cluster_fit_transform_and_serialization(tmp_path: Path) -> None:
    docs = sample_documents()
    model = SemanticClusterTopicModel(model_key="test-cluster", num_topics=3, random_seed=42)
    model.fit(docs)

    assert model.is_fitted
    topics, assignments = model.transform(docs)
    assert len(topics) == 3
    assert len(assignments) == len(docs)

    # Test serialization
    save_path = tmp_path / "cluster_model.joblib"
    model.save(save_path)
    loaded = SemanticClusterTopicModel.load(save_path)
    assert loaded.is_fitted
    assert loaded.model_key == "test-cluster"


def test_outlier_detection_logic() -> None:
    docs = sample_documents()
    model = NMFTopicModel(model_key="test-nmf-outliers", num_topics=3, outlier_threshold=0.15)
    model.fit(docs)

    _, assignments = model.transform(docs)
    # The short text "Ok." should be flagged as an outlier
    outlier_assigned = [a for a in assignments if a.review_id == "10"]
    assert len(outlier_assigned) == 1
    assert outlier_assigned[0].is_outlier or outlier_assigned[0].topic_id == -1
