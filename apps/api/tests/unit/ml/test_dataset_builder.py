"""Unit tests for DatasetBuilder and leakage-free dataset splitting."""

import pytest

from app.ml.dataset_builder import DatasetBuilder
from app.ml.taxonomy import AspectKey, SentimentLabel


def test_dataset_builder_full_pipeline_and_leakage_guarantees() -> None:
    raw_samples = [
        # Cluster 1: Exact duplicates
        {
            "review_id": "r1",
            "steam_app_id": 100,
            "review_text": "Cyberpunk 2077 runs great and story is wonderful.",
            "voted_up": True,
            "sentiment": SentimentLabel.POSITIVE.value,
            "aspects": [
                {"aspect": AspectKey.STORY.value, "sentiment": SentimentLabel.POSITIVE.value}
            ],
        },
        {
            "review_id": "r2",
            "steam_app_id": 100,
            "review_text": "Cyberpunk 2077 runs great and story is wonderful.",
            "voted_up": True,
            "sentiment": SentimentLabel.POSITIVE.value,
            "aspects": [
                {"aspect": AspectKey.STORY.value, "sentiment": SentimentLabel.POSITIVE.value}
            ],
        },
        # Cluster 2: Distinct positive
        {
            "review_id": "r3",
            "steam_app_id": 100,
            "review_text": "Combat mechanics and sword deflection feel amazing in this game.",
            "voted_up": True,
            "sentiment": SentimentLabel.POSITIVE.value,
            "aspects": [
                {"aspect": AspectKey.GAMEPLAY.value, "sentiment": SentimentLabel.POSITIVE.value}
            ],
        },
        # Cluster 3: Negative review
        {
            "review_id": "r4",
            "steam_app_id": 100,
            "review_text": "Terrible stuttering and crash to desktop every ten minutes.",
            "voted_up": False,
            "sentiment": SentimentLabel.NEGATIVE.value,
            "aspects": [
                {"aspect": AspectKey.PERFORMANCE.value, "sentiment": SentimentLabel.NEGATIVE.value}
            ],
        },
        # Cluster 4: Negative review
        {
            "review_id": "r5",
            "steam_app_id": 100,
            "review_text": "Horrible microtransactions and greedy 70 dollar pricing.",
            "voted_up": False,
            "sentiment": SentimentLabel.NEGATIVE.value,
            "aspects": [
                {"aspect": AspectKey.MONETIZATION.value, "sentiment": SentimentLabel.NEGATIVE.value}
            ],
        },
        # Cluster 5: Neutral review
        {
            "review_id": "r6",
            "steam_app_id": 100,
            "review_text": "Visuals are great but performance is poor. Mixed recommendation.",
            "voted_up": True,
            "sentiment": SentimentLabel.NEUTRAL.value,
            "aspects": [
                {"aspect": AspectKey.GRAPHICS.value, "sentiment": SentimentLabel.POSITIVE.value}
            ],
        },
        # Non-trainable foreign sample
        {
            "review_id": "r7",
            "steam_app_id": 100,
            "review_text": "Отличная игра, очень понравилась графика и сюжет.",
            "voted_up": True,
            "sentiment": SentimentLabel.POSITIVE.value,
        },
        # Non-trainable empty sample
        {
            "review_id": "r8",
            "steam_app_id": 100,
            "review_text": "   ",
            "voted_up": False,
            "sentiment": SentimentLabel.NEGATIVE.value,
        },
    ]

    builder = DatasetBuilder(random_seed=42)
    processed = builder.process_raw_reviews(raw_samples, target_language="en")

    assert len(processed) == 8
    # r7 is Russian -> not trainable en
    r7_item = next(it for it in processed if it["review_id"] == "r7")
    assert r7_item["language"] == "ru"
    assert r7_item["is_trainable"] is False

    # r8 is empty -> not trainable
    r8_item = next(it for it in processed if it["review_id"] == "r8")
    assert r8_item["quality_status"] == "empty_text"
    assert r8_item["is_trainable"] is False

    # r1 and r2 must share the same duplicate_group_id
    r1_item = next(it for it in processed if it["review_id"] == "r1")
    r2_item = next(it for it in processed if it["review_id"] == "r2")
    assert r1_item["duplicate_group_id"] == r2_item["duplicate_group_id"]
    assert r1_item["is_exact_duplicate"] is True

    # Perform group-stratified splits
    splits, manifest = builder.create_group_stratified_splits(
        items=processed,
        dataset_id="test-dataset",
        version="v1.0.0",
        train_ratio=0.6,
        val_ratio=0.2,
        test_ratio=0.2,
        filter_trainable_only=True,
    )

    train_ids = {it["review_id"] for it in splits["train"]}
    val_ids = {it["review_id"] for it in splits["validation"]}
    test_ids = {it["review_id"] for it in splits["test"]}

    # Zero leakage check
    assert len(train_ids & val_ids) == 0
    assert len(train_ids & test_ids) == 0
    assert len(val_ids & test_ids) == 0

    # Ensure r1 and r2 are in the EXACT SAME split
    all_splits_for_cluster = [
        "train" if "r1" in train_ids else ("val" if "r1" in val_ids else "test"),
        "train" if "r2" in train_ids else ("val" if "r2" in val_ids else "test"),
    ]
    assert all_splits_for_cluster[0] == all_splits_for_cluster[1]

    # Verify manifest integrity
    assert manifest.dataset_id == "test-dataset"
    assert manifest.splits["train"].sample_count == len(splits["train"])
    assert len(manifest.splits["train"].sha256_hash) == 64


def test_builder_empty_eligible_items_raises_value_error() -> None:
    builder = DatasetBuilder()
    with pytest.raises(ValueError, match="No eligible items"):
        builder.create_group_stratified_splits([], dataset_id="empty-dataset")
