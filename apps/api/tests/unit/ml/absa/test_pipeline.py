"""Unit tests for ABSATrainingPipeline, manifest loading, sweeps, and artifact serialization."""

import json
import tempfile
from pathlib import Path

from app.ml.absa.classifier import SentenceGroundedTfidfABSA
from app.ml.absa.evaluator import ABSAEvaluator
from app.ml.absa.pipeline import ABSATrainingPipeline
from app.ml.taxonomy import AspectKey, SentimentLabel


def test_pipeline_hyperparameter_sweep_and_save() -> None:
    train_records = [
        {
            "review_id": f"tr_{i}",
            "normalized_text": "Combat mechanics feel crisp and fluid.",
            "aspects": [
                {
                    "aspect": AspectKey.GAMEPLAY.value,
                    "sentiment": SentimentLabel.POSITIVE.value,
                    "snippet": "Combat mechanics feel crisp and fluid",
                }
            ],
        }
        for i in range(8)
    ] + [
        {
            "review_id": f"tr_neg_{i}",
            "normalized_text": "Severe microstutter and constant crashes.",
            "aspects": [
                {
                    "aspect": AspectKey.PERFORMANCE.value,
                    "sentiment": SentimentLabel.NEGATIVE.value,
                    "snippet": "Severe microstutter and constant crashes",
                }
            ],
        }
        for i in range(8)
    ]

    val_records = [
        {
            "review_id": "val_1",
            "normalized_text": "Great gunplay combat mechanics.",
            "aspects": [
                {
                    "aspect": AspectKey.GAMEPLAY.value,
                    "sentiment": SentimentLabel.POSITIVE.value,
                    "snippet": "Great gunplay",
                }
            ],
        },
        {
            "review_id": "val_2",
            "normalized_text": "Horrible stuttering and crashes.",
            "aspects": [
                {
                    "aspect": AspectKey.PERFORMANCE.value,
                    "sentiment": SentimentLabel.NEGATIVE.value,
                    "snippet": "Horrible stuttering",
                }
            ],
        },
    ]

    evaluator = ABSAEvaluator()
    pipeline = ABSATrainingPipeline(evaluator)

    best_params = pipeline.tune_hyperparameters(train_records, val_records)
    assert "c_regularization" in best_params
    assert "aspect_threshold" in best_params
    assert "ngram_range" in best_params

    model = SentenceGroundedTfidfABSA(
        c_regularization=best_params["c_regularization"],
        aspect_threshold=best_params["aspect_threshold"],
        ngram_range=best_params["ngram_range"],
    )
    model.fit(train_records)

    report = evaluator.evaluate(model, val_records)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "test_model"
        dummy_manifest = Path(tmp_dir) / "dataset_manifest.json"
        dummy_manifest.write_text("{}", encoding="utf-8")

        manifest_file = pipeline.save_artifacts(model, report, out_path, dummy_manifest)
        assert manifest_file.exists()
        assert (out_path / "model.joblib").exists()

        with open(manifest_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["task"] == "absa"
        assert data["artifact_checksum"].startswith("sha256:")
        assert "release_gate" in data
