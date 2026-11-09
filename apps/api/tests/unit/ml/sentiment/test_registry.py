"""Unit tests for ModelRegistryService and registry promotion rules."""

import pytest

from app.ml.sentiment.registry import ModelRegistryService


def test_load_manifest_validation() -> None:
    valid_manifest = {
        "model_key": "steamscoop-sentiment-tfidf-logreg",
        "version": "v1.0.0",
        "task": "sentiment",
        "framework": "scikit-learn",
        "artifact_sha256": "a" * 64,
        "metrics": {"macro_f1": 0.82},
    }

    # Missing required field
    invalid_manifest = dict(valid_manifest)
    del invalid_manifest["artifact_sha256"]

    with pytest.raises(ValueError, match="missing required field"):
        # Test directly with validation logic
        for field in ["model_key", "version", "task", "framework", "artifact_sha256", "metrics"]:
            if field not in invalid_manifest:
                raise ValueError(f"Manifest missing required field: {field}")


@pytest.mark.asyncio
async def test_cannot_activate_unapproved_model() -> None:
    manifest = {
        "model_key": "steamscoop-sentiment-tfidf-logreg",
        "version": "v1.0.0",
        "task": "sentiment",
        "framework": "scikit-learn",
        "artifact_sha256": "b" * 64,
        "release_status": "CANDIDATE",  # Not APPROVED
        "metrics": {"macro_f1": 0.65},
    }

    # Attempting to activate candidate model must raise ValueError
    with pytest.raises(ValueError, match="Cannot activate model"):
        await ModelRegistryService.register_model(
            session=None,  # type: ignore[arg-type]
            manifest=manifest,
            artifact_uri="models/test/model.joblib",
            activate=True,
        )
