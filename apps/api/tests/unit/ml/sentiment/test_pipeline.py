"""Unit tests for SentimentTrainingPipeline, manifest loading, sweeps, and artifact serialization."""

import json
import tempfile

import pytest

from app.ml.sentiment.classifier import TfidfLogisticRegression
from app.ml.sentiment.evaluator import SentimentEvaluator
from app.ml.sentiment.pipeline import SentimentTrainingPipeline
from app.ml.taxonomy import SentimentLabel


@pytest.fixture
def sample_splits() -> dict[str, list[dict[str, str]]]:
    train = [
        {
            "normalized_text": "Incredible combat and story masterpiece",
            "sentiment": SentimentLabel.POSITIVE.value,
        },
        {
            "normalized_text": "Great graphics and wonderful soundtrack",
            "sentiment": SentimentLabel.POSITIVE.value,
        },
        {
            "normalized_text": "Horrible optimization and constant crashes",
            "sentiment": SentimentLabel.NEGATIVE.value,
        },
        {
            "normalized_text": "Trash garbage, broken gameplay",
            "sentiment": SentimentLabel.NEGATIVE.value,
        },
        {
            "normalized_text": "Average shooter, wait for sale",
            "sentiment": SentimentLabel.NEUTRAL.value,
        },
        {
            "normalized_text": "Decent gameplay, middle of road",
            "sentiment": SentimentLabel.NEUTRAL.value,
        },
    ]
    val = [
        {
            "normalized_text": "Amazing story and soundtrack",
            "sentiment": SentimentLabel.POSITIVE.value,
        },
        {
            "normalized_text": "Terrible crashing and bugs",
            "sentiment": SentimentLabel.NEGATIVE.value,
        },
        {
            "normalized_text": "Fair game, mediocre content",
            "sentiment": SentimentLabel.NEUTRAL.value,
        },
    ]
    test = [
        {
            "normalized_text": "Perfection, best game ever",
            "sentiment": SentimentLabel.POSITIVE.value,
        },
        {
            "normalized_text": "Do not buy, unplayable bugs",
            "sentiment": SentimentLabel.NEGATIVE.value,
        },
        {
            "normalized_text": "It is okay, nothing special",
            "sentiment": SentimentLabel.NEUTRAL.value,
        },
    ]
    return {"train": train, "validation": val, "test": test}


def test_hyperparameter_sweep_and_training(sample_splits: dict[str, list[dict[str, str]]]) -> None:
    pipeline = SentimentTrainingPipeline(random_seed=42)

    sweep = pipeline.run_hyperparameter_sweep(
        train_items=sample_splits["train"],
        val_items=sample_splits["validation"],
    )

    assert "best_logreg" in sweep
    assert "best_svm" in sweep
    assert len(sweep["experiments"]) > 0

    candidates, reports, selected_model, release_gate = pipeline.train_and_evaluate_all(
        splits=sample_splits,
        best_params=sweep,
    )

    assert "majority" in reports
    assert "tfidf_logreg" in reports
    assert "tfidf_linearsvm" in reports
    assert "tfidf_cnb" in reports
    assert selected_model is not None
    assert release_gate is not None


def test_save_model_artifact(sample_splits: dict[str, list[dict[str, str]]]) -> None:
    pipeline = SentimentTrainingPipeline(random_seed=42)
    model = TfidfLogisticRegression(random_state=42)
    train_texts = [it["normalized_text"] for it in sample_splits["train"]]
    train_labels = [it["sentiment"] for it in sample_splits["train"]]
    model.fit(train_texts, train_labels)

    evaluator = SentimentEvaluator()
    test_texts = [it["normalized_text"] for it in sample_splits["test"]]
    test_labels = [it["sentiment"] for it in sample_splits["test"]]
    preds = model.predict(test_texts)
    probs = model.predict_proba(test_texts)

    report = evaluator.evaluate_predictions(
        y_true=test_labels,
        y_pred=preds,
        probabilities=probs,
        model_key=model.model_key,
        model_version=model.version,
        dataset_version="v1.0.0",
        split_name="test",
    )
    gate = evaluator.check_release_gates(report)

    with tempfile.TemporaryDirectory() as tmp_dir:
        saved_dir = pipeline.save_model_artifact(
            classifier=model,
            report=report,
            release_gate=gate,
            output_dir=tmp_dir,
            dataset_manifest_data={"version": "v1.0.0", "provenance": {"source": "test"}},
        )

        assert (saved_dir / "model.joblib").exists()
        assert (saved_dir / "model_manifest.json").exists()

        with open(saved_dir / "model_manifest.json", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["model_key"] == model.model_key
        assert manifest["version"] == model.version
        assert len(manifest["artifact_sha256"]) == 64
