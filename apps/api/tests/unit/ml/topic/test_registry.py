"""Unit tests for TopicModelRegistryService and model synchronization."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.ml.topic.registry import TopicModelRegistryService


def test_load_manifest_validation(tmp_path: Path) -> None:
    service = TopicModelRegistryService()

    # Valid manifest
    valid_data = {
        "model_key": "steamscoop-topic-nmf-1091500",
        "version": "v1.0.0",
        "task": "topic",
        "framework": "scikit-learn",
        "config": {"num_topics": 4},
        "metrics": {"topic_diversity": 1.0},
    }
    manifest_path = tmp_path / "model_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)

    loaded = service.load_manifest(manifest_path)
    assert loaded["model_key"] == "steamscoop-topic-nmf-1091500"

    # Invalid task
    invalid_data = dict(valid_data, task="sentiment")
    invalid_path = tmp_path / "invalid_manifest.json"
    with open(invalid_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)

    with pytest.raises(ValueError) as exc:
        service.load_manifest(invalid_path)
    assert "Expected task 'topic'" in str(exc.value)


def test_sync_model_release_gate_rejection() -> None:
    service = TopicModelRegistryService()
    mock_db = MagicMock()

    manifest_unapproved = {
        "model_key": "topic-nmf",
        "version": "v1.0.0",
        "task": "topic",
        "framework": "scikit-learn",
        "config": {},
        "metrics": {},
        "release_gate": {"status": "CANDIDATE"},
    }

    # Attempting to activate an unapproved candidate model must raise ValueError
    with pytest.raises(ValueError) as exc:
        service.sync_model_to_db(mock_db, manifest_unapproved, is_active=True)
    assert "only models that have passed all predeclared release gates (APPROVED)" in str(exc.value)


def test_sync_model_to_db_success() -> None:
    service = TopicModelRegistryService()
    mock_db = MagicMock()
    mock_db.scalars.return_value.first.return_value = None

    manifest = {
        "model_key": "steamscoop-topic-nmf-1091500",
        "version": "v1.0.0",
        "task": "topic",
        "framework": "scikit-learn",
        "config": {"num_topics": 2},
        "metrics": {"topic_diversity": 1.0},
        "release_gate": {"status": "APPROVED"},
        "topics": [
            {
                "topic_key": "top_0",
                "label": "Combat Mechanics",
                "keywords": ["combat", "gunplay"],
                "representative_terms": [{"term": "combat", "weight": 0.5}],
                "is_outlier": False,
            }
        ],
    }

    model = service.sync_model_to_db(mock_db, manifest, is_active=True)
    assert mock_db.add.called
    assert mock_db.commit.called
    assert model.task == "topic"
    assert model.is_active is True
