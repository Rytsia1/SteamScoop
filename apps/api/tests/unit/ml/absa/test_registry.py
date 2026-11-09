"""Unit tests for ABSAModelRegistryService and production release gate enforcement."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.ml.absa.registry import ABSAModelRegistryService


def test_registry_manifest_validation() -> None:
    service = ABSAModelRegistryService()

    with tempfile.TemporaryDirectory() as tmp_dir:
        bad_manifest = Path(tmp_dir) / "bad.json"
        bad_manifest.write_text(json.dumps({"invalid": True}), encoding="utf-8")

        with pytest.raises(ValueError, match="missing keys"):
            service.load_manifest(bad_manifest)


def test_registry_blocks_candidate_activation() -> None:
    service = ABSAModelRegistryService()

    manifest_data = {
        "model_key": "steamscoop-absa-sentence-tfidf",
        "version": "v1.0.0",
        "task": "absa",
        "framework": "scikit-learn",
        "config": {"aspect_threshold": 0.35},
        "metrics": {"detection_micro_f1": 0.85},
        "release_gate": {
            "status": "CANDIDATE",
            "passed_gates": False,
            "failures": ["Sentiment macro F1 below threshold"],
        },
    }

    mock_db = MagicMock()

    # Attempting to activate a CANDIDATE model in production must be rejected
    with pytest.raises(ValueError, match="Cannot activate ABSA model .* with status 'CANDIDATE'"):
        service.sync_model_to_db(mock_db, manifest_data, is_active=True)


def test_registry_allows_approved_activation() -> None:
    service = ABSAModelRegistryService()

    manifest_data = {
        "model_key": "steamscoop-absa-sentence-tfidf",
        "version": "v1.0.0",
        "task": "absa",
        "framework": "scikit-learn",
        "config": {"aspect_threshold": 0.35},
        "metrics": {"detection_micro_f1": 0.88, "sentiment_macro_f1": 0.82},
        "release_gate": {
            "status": "APPROVED",
            "passed_gates": True,
            "failures": [],
        },
    }

    mock_db = MagicMock()
    mock_db.scalars.return_value.first.return_value = None

    model = service.sync_model_to_db(mock_db, manifest_data, is_active=True)
    assert model.is_active is True
    assert model.task == "absa"
    assert mock_db.commit.called
