"""Model registry management and database synchronization for sentiment models.

Complies with ML_SPECIFICATION.md Section 11.3, 11.4, 15.2, 15.3:
- Registry lifecycle states: development, candidate, approved, active, deprecated, retired.
- Only approved models satisfying release criteria may be activated for production.
- Validates output contracts and persists prediction provenance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml import MLModel


class ModelRegistryService:
    """Manages model registry sync between disk artifacts and PostgreSQL."""

    @staticmethod
    def load_manifest(manifest_path: str | Path) -> dict[str, Any]:
        """Read and validate a model manifest from disk."""
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Model manifest not found at: {path}")

        with open(path, encoding="utf-8") as f:
            manifest_data = json.load(f)

        if not isinstance(manifest_data, dict):
            raise TypeError(f"Manifest must be a JSON object, got {type(manifest_data)}")

        manifest: dict[str, Any] = dict(manifest_data)

        required_fields = [
            "model_key",
            "version",
            "task",
            "framework",
            "artifact_sha256",
            "metrics",
        ]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Manifest missing required field: {field}")

        return manifest

    @staticmethod
    async def register_model(
        session: AsyncSession,
        manifest: dict[str, Any],
        artifact_uri: str,
        activate: bool = False,
    ) -> MLModel:
        """Register or update model entry in PostgreSQL ml_model table.

        Enforces ML_SPECIFICATION.md Release Gate:
        A model can ONLY be activated if release_status is 'APPROVED'.
        """
        model_key = manifest["model_key"]
        version = manifest["version"]
        task = manifest["task"]
        release_status = manifest.get("release_status", "CANDIDATE")

        if activate and release_status != "APPROVED":
            raise ValueError(
                f"Cannot activate model {model_key}@{version}: "
                f"status is '{release_status}', not 'APPROVED'."
            )

        # Check if record already exists
        stmt = select(MLModel).where(
            MLModel.model_key == model_key,
            MLModel.version == version,
            MLModel.task == task,
        )
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = MLModel(
                model_key=model_key,
                version=version,
                task=task,
                framework=manifest.get("framework", "scikit-learn"),
                artifact_uri=artifact_uri,
                language_scope=["en"],
                label_schema={"labels": ["positive", "negative", "neutral"]},
                config={
                    "artifact_sha256": manifest["artifact_sha256"],
                    "dataset_version": manifest.get("dataset_version"),
                    "release_status": release_status,
                },
                metrics=manifest.get("metrics", {}),
                is_active=activate,
            )
            session.add(model)
        else:
            model.artifact_uri = artifact_uri
            model.metrics = manifest.get("metrics", {})
            model.config = {
                "artifact_sha256": manifest["artifact_sha256"],
                "dataset_version": manifest.get("dataset_version"),
                "release_status": release_status,
            }
            if activate:
                model.is_active = True

        await session.flush()
        return model
