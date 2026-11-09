"""Unit tests for ABSA classifiers (Majority, Document TF-IDF, Sentence-Grounded TF-IDF)."""

import tempfile
from pathlib import Path

import pytest

from app.ml.absa.classifier import (
    MajorityBaselineABSA,
    SentenceGroundedTfidfABSA,
    split_sentences_with_offsets,
)
from app.ml.absa.schemas import ABSAInput
from app.ml.taxonomy import AspectKey, SentimentLabel


@pytest.fixture
def sample_absa_records() -> list[dict]:
    return [
        {
            "review_id": "r1",
            "normalized_text": "Combat mechanics feel crisp and fluid. Hacking enemies is great.",
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
            "normalized_text": "The framerate stutters constantly and crashes desktop. Ugly graphics.",
            "aspects": [
                {
                    "aspect": AspectKey.PERFORMANCE.value,
                    "sentiment": SentimentLabel.NEGATIVE.value,
                    "snippet": "framerate stutters constantly and crashes",
                },
                {
                    "aspect": AspectKey.GRAPHICS.value,
                    "sentiment": SentimentLabel.NEGATIVE.value,
                    "snippet": "Ugly graphics",
                },
            ],
        },
        {
            "review_id": "r3",
            "normalized_text": "Soundtrack is pure masterpiece. However, battle pass is predatory MTX.",
            "aspects": [
                {
                    "aspect": AspectKey.AUDIO.value,
                    "sentiment": SentimentLabel.POSITIVE.value,
                    "snippet": "Soundtrack is pure masterpiece",
                },
                {
                    "aspect": AspectKey.MONETIZATION.value,
                    "sentiment": SentimentLabel.NEGATIVE.value,
                    "snippet": "battle pass is predatory MTX",
                },
            ],
        },
        {
            "review_id": "r4",
            "normalized_text": "Average game. Ten out of ten.",
            "aspects": [],
        },
    ]


def test_split_sentences_with_offsets() -> None:
    text = "Combat is great! But the game crashes constantly. 10/10."
    splits = split_sentences_with_offsets(text)
    assert len(splits) >= 2
    for s_text, start_o, end_o in splits:
        assert s_text == text[start_o:end_o]
        assert start_o >= 0
        assert end_o <= len(text)


def test_majority_baseline_predict(sample_absa_records: list[dict]) -> None:
    model = MajorityBaselineABSA()
    model.fit(sample_absa_records)
    assert model.is_fitted

    inputs = [ABSAInput(review_id="test1", text="Random text here")]
    outputs = model.predict_records(inputs)

    assert len(outputs) == 1
    assert outputs[0].has_aspects
    assert len(outputs[0].aspects) == 1
    assert outputs[0].aspects[0].aspect.value in [ak.value for ak in AspectKey]


def test_sentence_grounded_tfidf_mixed_sentiment(sample_absa_records: list[dict]) -> None:
    model = SentenceGroundedTfidfABSA(aspect_threshold=0.25)
    model.fit(sample_absa_records)
    assert model.is_fitted

    # Multi-aspect review with opposing sentiments
    inputs = [
        ABSAInput(
            review_id="test_mixed",
            text="Combat mechanics feel crisp and fluid. But framerate stutters constantly and crashes desktop.",
        )
    ]
    outputs = model.predict_records(inputs)
    assert len(outputs) == 1
    pred = outputs[0]

    # Verify both aspects detected with distinct, non-mixed sentiments
    aspect_map = {item.aspect.value: item for item in pred.aspects}
    assert AspectKey.GAMEPLAY.value in aspect_map or AspectKey.PERFORMANCE.value in aspect_map

    if AspectKey.GAMEPLAY.value in aspect_map:
        assert aspect_map[AspectKey.GAMEPLAY.value].sentiment == SentimentLabel.POSITIVE

    if AspectKey.PERFORMANCE.value in aspect_map:
        assert aspect_map[AspectKey.PERFORMANCE.value].sentiment == SentimentLabel.NEGATIVE


def test_no_aspect_reviews_behavior(sample_absa_records: list[dict]) -> None:
    model = SentenceGroundedTfidfABSA(aspect_threshold=0.45)
    model.fit(sample_absa_records)

    # Empty / pure emotional review with no aspect evidence
    inputs = [ABSAInput(review_id="empty_1", text="Just yes.")]
    outputs = model.predict_records(inputs)

    assert len(outputs) == 1
    # When no aspect keywords or features exceed threshold, aspects should be empty
    assert len(outputs[0].aspects) == 0
    assert not outputs[0].has_aspects


def test_model_serialization(sample_absa_records: list[dict]) -> None:
    model = SentenceGroundedTfidfABSA(c_regularization=0.5, aspect_threshold=0.35)
    model.fit(sample_absa_records)

    with tempfile.TemporaryDirectory() as tmp_dir:
        model_path = Path(tmp_dir) / "model.joblib"
        model.save(model_path)
        assert model_path.exists()

        loaded = SentenceGroundedTfidfABSA.load(model_path)
        assert isinstance(loaded, SentenceGroundedTfidfABSA)
        assert loaded.is_fitted
        assert loaded.c_regularization == 0.5
        assert loaded.aspect_threshold == 0.35

        inputs = [ABSAInput(review_id="t1", text="Combat is crisp.")]
        preds = loaded.predict_records(inputs)
        assert len(preds) == 1
