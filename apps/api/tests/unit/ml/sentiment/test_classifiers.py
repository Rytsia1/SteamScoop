"""Unit tests for SteamScoop sentiment analysis classifiers and baseline models."""

import tempfile
from pathlib import Path

import pytest

from app.ml.sentiment.classifier import (
    BaseSentimentClassifier,
    MajorityBaseline,
    TfidfComplementNaiveBayes,
    TfidfLinearSVM,
    TfidfLogisticRegression,
)
from app.ml.sentiment.schemas import SentimentInput
from app.ml.taxonomy import SentimentLabel

TRAIN_TEXTS = [
    "This game is an absolute masterpiece. Fantastic combat and rich storyline.",
    "Great visuals, responsive controls, and incredible soundtrack.",
    "Unplayable garbage, crashes to desktop every five minutes. Total waste of money.",
    "Horrible performance and predatory microtransactions. Avoid at all costs.",
    "Average shooter. Decent gameplay but repetitive quests. Wait for a sale.",
    "Neither good nor bad, just thoroughly mediocre. Middle of the road.",
]
TRAIN_LABELS = [
    SentimentLabel.POSITIVE.value,
    SentimentLabel.POSITIVE.value,
    SentimentLabel.NEGATIVE.value,
    SentimentLabel.NEGATIVE.value,
    SentimentLabel.NEUTRAL.value,
    SentimentLabel.NEUTRAL.value,
]


def test_majority_baseline_predict_and_probas() -> None:
    # 3 positive, 1 negative -> majority is positive
    texts = ["good 1", "good 2", "good 3", "bad 1"]
    labels = ["positive", "positive", "positive", "negative"]

    model = MajorityBaseline()
    model.fit(texts, labels)

    test_queries = ["great game", "awful game", "something random"]
    preds = model.predict(test_queries)
    assert preds == ["positive", "positive", "positive"]

    probas = model.predict_proba(test_queries)
    assert len(probas) == 3
    for p in probas:
        assert p["positive"] == 0.75
        assert p["negative"] == 0.25
        assert p["neutral"] == 0.0


def test_tfidf_logreg_training_and_serialization() -> None:
    model = TfidfLogisticRegression(c_regularization=1.0, max_iter=200, random_state=42)
    model.fit(TRAIN_TEXTS, TRAIN_LABELS)

    # Test prediction
    preds = model.predict(
        ["Masterpiece with incredible story!", "Crashes constantly, broken trash."]
    )
    assert len(preds) == 2
    assert preds[0] in [lbl.value for lbl in SentimentLabel]

    # Test probability distribution
    probas = model.predict_proba(["Masterpiece story"])
    assert len(probas) == 1
    assert "positive" in probas[0]
    assert "negative" in probas[0]
    assert "neutral" in probas[0]
    assert round(sum(probas[0].values()), 2) == 1.0

    # Test serialization
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = Path(tmp_dir) / "model.joblib"
        model.save(save_path)
        assert save_path.exists()

        loaded = BaseSentimentClassifier.load(save_path)
        assert isinstance(loaded, TfidfLogisticRegression)
        loaded_preds = loaded.predict(["Masterpiece story"])
        assert loaded_preds == model.predict(["Masterpiece story"])


def test_tfidf_linearsvm_training_and_calibrated_proba() -> None:
    model = TfidfLinearSVM(c_regularization=0.5, random_state=42)
    model.fit(TRAIN_TEXTS, TRAIN_LABELS)

    preds = model.predict(["Responsive controls and soundtrack", "Predatory microtransactions"])
    assert len(preds) == 2

    # Verify Platt scaling calibrated probabilities
    probas = model.predict_proba(["Responsive controls"])
    assert len(probas) == 1
    assert 0.0 <= probas[0]["positive"] <= 1.0
    assert 0.0 <= probas[0]["negative"] <= 1.0
    assert 0.0 <= probas[0]["neutral"] <= 1.0
    assert round(sum(probas[0].values()), 2) == 1.0


def test_tfidf_complement_naive_bayes_training() -> None:
    model = TfidfComplementNaiveBayes(alpha=1.0)
    model.fit(TRAIN_TEXTS, TRAIN_LABELS)

    preds = model.predict(["Average shooter, repetitive"])
    assert len(preds) == 1

    probas = model.predict_proba(["Average shooter, repetitive"])
    assert len(probas) == 1
    assert round(sum(probas[0].values()), 2) == 1.0


def test_predict_records_output_contract() -> None:
    model = TfidfLogisticRegression(random_state=42)
    model.fit(TRAIN_TEXTS, TRAIN_LABELS)

    inputs = [
        SentimentInput(review_id="rev_test_1", text="Loved every minute of it, masterpiece!"),
        SentimentInput(review_id="rev_test_2", text="Broke my GPU, terrible optimization."),
    ]
    outputs = model.predict_records(inputs, confidence_threshold=0.40)

    assert len(outputs) == 2
    assert outputs[0].review_id == "rev_test_1"
    assert outputs[0].task == "sentiment"
    assert outputs[0].label in ["positive", "negative", "neutral"]
    assert 0.0 <= outputs[0].confidence <= 1.0
    assert isinstance(outputs[0].is_abstained, bool)
    assert outputs[0].model_key == model.model_key
    assert outputs[0].model_version == model.version


def test_unfitted_model_raises_runtime_error() -> None:
    model = TfidfLogisticRegression()
    with pytest.raises(RuntimeError, match="not fitted"):
        model.predict(["Some text"])

    with pytest.raises(RuntimeError, match="not fitted"):
        model.predict_proba(["Some text"])
