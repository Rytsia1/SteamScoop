"""Unit tests for ABSAEvaluator and release gate verification."""

from typing import Any

from app.ml.absa.classifier import SentenceGroundedTfidfABSA
from app.ml.absa.evaluator import ABSAEvaluator
from app.ml.taxonomy import AspectKey, SentimentLabel


def test_evaluator_metrics_and_report() -> None:
    records: list[dict[str, Any]] = [
        {
            "review_id": "r1",
            "normalized_text": "Combat mechanics feel crisp and fluid. Great gunplay.",
            "aspects": [
                {
                    "aspect": AspectKey.GAMEPLAY.value,
                    "sentiment": SentimentLabel.POSITIVE.value,
                    "snippet": "Combat mechanics feel crisp and fluid",
                }
            ],
        },
        {
            "review_id": "r2",
            "normalized_text": "Framerate stutters constantly and crashes desktop.",
            "aspects": [
                {
                    "aspect": AspectKey.PERFORMANCE.value,
                    "sentiment": SentimentLabel.NEGATIVE.value,
                    "snippet": "Framerate stutters constantly and crashes",
                }
            ],
        },
        {
            "review_id": "r3",
            "normalized_text": "Soundtrack is pure masterpiece. predatory battle pass MTX.",
            "aspects": [
                {
                    "aspect": AspectKey.AUDIO.value,
                    "sentiment": SentimentLabel.POSITIVE.value,
                    "snippet": "Soundtrack is pure masterpiece",
                },
                {
                    "aspect": AspectKey.MONETIZATION.value,
                    "sentiment": SentimentLabel.NEGATIVE.value,
                    "snippet": "predatory battle pass MTX",
                },
            ],
        },
        {
            "review_id": "r4",
            "normalized_text": "Masterpiece 10/10.",
            "aspects": [],
        },
    ]

    model = SentenceGroundedTfidfABSA(aspect_threshold=0.30)
    model.fit(records)

    evaluator = ABSAEvaluator()
    report = evaluator.evaluate(model, records, aspect_threshold=0.30)

    # Validate output schema
    assert 0.0 <= report.detection_metrics.micro_f1 <= 1.0
    assert 0.0 <= report.detection_metrics.macro_f1 <= 1.0
    assert 0.0 <= report.detection_metrics.subset_accuracy <= 1.0
    assert 0.0 <= report.detection_metrics.hamming_loss <= 1.0

    # Validate sentiment metrics
    assert 0.0 <= report.sentiment_metrics.macro_f1 <= 1.0
    assert 0.0 <= report.sentiment_metrics.accuracy <= 1.0

    # Validate joint metrics
    assert 0.0 <= report.joint_metrics.joint_micro_f1 <= 1.0

    # Validate threshold analysis
    assert len(report.threshold_analysis) > 0
    for pt in report.threshold_analysis:
        assert 0.0 <= pt.threshold <= 1.0
        assert 0.0 <= pt.coverage_rate <= 1.0

    # Validate slice performance
    assert "single_aspect_count" in report.slice_performance
    assert "multi_aspect_count" in report.slice_performance
    assert "zero_aspect_count" in report.slice_performance

    # Validate release gate result
    assert report.release_gate.status in ["APPROVED", "CANDIDATE", "REJECTED"]
