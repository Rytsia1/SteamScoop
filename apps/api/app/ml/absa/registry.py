"""Model registry service for Aspect-Based Sentiment Analysis (ABSA).

Manages synchronization between model provenance manifests and the PostgreSQL
ml_model table, strictly enforcing release gate approval before allowing production activation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml import MLModel


class ABSAModelRegistryService:
    """Synchronizes ABSA model artifacts with the database model registry."""

    def load_manifest(self, manifest_path: str | Path) -> dict[str, Any]:
        """Read and validate model manifest JSON."""
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Model manifest not found: {path}")

        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        required_keys = {"model_key", "version", "task", "framework", "config", "metrics"}
        missing = required_keys - set(data.keys())
        if missing:
            raise ValueError(f"Invalid model manifest format; missing keys: {missing}")

        return data

    def sync_model_to_db(
        self,
        db: Session,
        manifest_data: dict[str, Any],
        is_active: bool = False,
    ) -> MLModel:
        """Register or update an ABSA model record in PostgreSQL.

        Enforces production release gate: if is_active=True is requested but
        the model's release gate status is not APPROVED, the operation is strictly rejected.
        """
        model_key = manifest_data["model_key"]
        version = manifest_data["version"]
        task = manifest_data.get("task", "absa")

        # Validate production activation safety
        gate_info = manifest_data.get("release_gate", {})
        status = gate_info.get("status", "CANDIDATE")

        if is_active and status != "APPROVED":
            raise ValueError(
                f"Cannot activate ABSA model '{model_key}@{version}' with status '{status}'. "
                "Per ML_SPECIFICATION.md and operational policy, only models that have passed "
                "all predeclared release gates (APPROVED) may be activated in production."
            )

        stmt = select(MLModel).where(
            MLModel.model_key == model_key,
            MLModel.version == version,
            MLModel.task == task,
        )
        model = db.scalars(stmt).first()

        if not model:
            model = MLModel(
                model_key=model_key,
                version=version,
                task=task,
                framework=manifest_data.get("framework", "scikit-learn"),
                artifact_uri=manifest_data.get("artifact_file"),
                language_scope=manifest_data.get("language_scope", ["en"]),
                label_schema=manifest_data.get("label_schema", {}),
                config=manifest_data.get("config", {}),
                metrics=manifest_data.get("metrics", {}),
                is_active=is_active,
            )
            db.add(model)
        else:
            model.framework = manifest_data.get("framework", model.framework)
            model.artifact_uri = manifest_data.get("artifact_file", model.artifact_uri)
            model.label_schema = manifest_data.get("label_schema", model.label_schema)
            model.config = manifest_data.get("config", model.config)
            model.metrics = manifest_data.get("metrics", model.metrics)
            if is_active:
                model.is_active = True

        db.commit()
        db.refresh(model)
        return model

    def activate_model(self, db: Session, model_key: str, version: str) -> MLModel:
        """Promote an approved ABSA model version to active production state."""
        stmt = select(MLModel).where(
            MLModel.model_key == model_key,
            MLModel.version == version,
            MLModel.task == "absa",
        )
        model = db.scalars(stmt).first()
        if not model:
            raise ValueError(f"ABSA model '{model_key}@{version}' not found in registry.")

        # Deactivate any other active ABSA models
        all_absa = db.scalars(
            select(MLModel).where(MLModel.task == "absa", MLModel.is_active.is_(True))
        ).all()
        for m in all_absa:
            m.is_active = False

        model.is_active = True
        db.commit()
        db.refresh(model)
        return model
