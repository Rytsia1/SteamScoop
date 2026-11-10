"""Unit tests for human-in-the-loop topic curation and qualitative rubric ratings."""

from app.ml.topic.curation import TopicCurationService
from app.ml.topic.schemas import (
    TopicEvaluationReport,
    TopicMetrics,
    TopicRepresentation,
)


def test_apply_curated_labels() -> None:
    curation_service = TopicCurationService()

    raw_report = TopicEvaluationReport(
        model_key="test-model",
        model_version="v1.0.0",
        steam_app_id=1091500,
        corpus_size=40,
        metrics=TopicMetrics(
            num_topics=2,
            topic_diversity=1.0,
            mean_pairwise_jaccard=0.0,
            npmi_coherence=0.4,
            outlier_count=2,
            outlier_rate=0.05,
            topic_size_entropy=1.0,
            stability_score=1.0,
        ),
        topics=[
            TopicRepresentation(
                topic_id=0,
                topic_key="topic_0",
                label="Topic 0: combat, gunplay",
                description=None,
                keywords=["combat", "gunplay"],
                representative_terms=[],
                doc_count=20,
                is_outlier=False,
            ),
            TopicRepresentation(
                topic_id=1,
                topic_key="topic_1",
                label="Topic 1: fps, stuttering",
                description=None,
                keywords=["fps", "stuttering"],
                representative_terms=[],
                doc_count=18,
                is_outlier=False,
            ),
        ],
        curated=False,
    )

    curation_map = {
        "topic_0": {
            "label": "Combat Mechanics & Gunplay",
            "description": "Analysis of weapon handling and gunplay feel.",
            "rubric": {
                "interpretability": 5,
                "redundancy": 5,
                "domain_relevance": 5,
                "assignment_plausibility": 5,
            },
        },
        "topic_1": {
            "label": "Technical Performance & FPS",
            "description": "Discussion of PC frame rates and stability.",
            "rubric": {
                "interpretability": 4,
                "redundancy": 4,
                "domain_relevance": 5,
                "assignment_plausibility": 4,
            },
        },
    }

    curated = curation_service.apply_curated_labels(
        report=raw_report,
        curation_map=curation_map,
        curator_id="curator_alex",
    )

    assert curated.curated is True
    assert len(curated.human_evaluation) == 2
    assert curated.topics[0].label == "Combat Mechanics & Gunplay"
    assert curated.topics[0].description == "Analysis of weapon handling and gunplay feel."
    assert curated.topics[1].label == "Technical Performance & FPS"

    rubric_0 = next(r for r in curated.human_evaluation if r.topic_key == "topic_0")
    assert rubric_0.interpretability == 5
    assert rubric_0.suggested_label == "Combat Mechanics & Gunplay"
    assert "curator_alex" in (rubric_0.evaluator_notes or "")
