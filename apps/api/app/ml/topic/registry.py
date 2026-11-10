"""Model registry service for Topic Modeling.

Manages synchronization between topic model manifests and the PostgreSQL
ml_model and topic tables, enforcing release gate approval before allowing production activation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml import MLModel
from app.models.topic import Topic


class TopicModelRegistryService:
    """Synchronizes topic model artifacts and discovered topics with PostgreSQL."""

    def load_manifest(self, manifest_path: str | Path) -> dict[str, Any]:
        """Read and validate topic model manifest JSON."""
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Topic model manifest not found: {path}")

        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        required_keys = {"model_key", "version", "task", "framework", "config", "metrics"}
        missing = required_keys - set(data.keys())
        if missing:
            raise ValueError(f"Invalid model manifest format; missing keys: {missing}")

        if data.get("task") != "topic":
            raise ValueError(f"Expected task 'topic', got '{data.get('task')}'")

        return data

    def sync_model_to_db(
        self,
        db: Session,
        manifest_data: dict[str, Any],
        is_active: bool = False,
    ) -> MLModel:
        """Register or update a topic model record in PostgreSQL.

        Enforces production release gate: if is_active=True is requested but
        the model's release gate status is not APPROVED, the operation is strictly rejected.
        """
        model_key = manifest_data["model_key"]
        version = manifest_data["version"]
        task = manifest_data.get("task", "topic")

        # Validate production activation safety
        gate_info = manifest_data.get("release_gate", {})
        status = gate_info.get("status") or manifest_data.get("release_status", "CANDIDATE")

        if is_active and status != "APPROVED":
            raise ValueError(
                f"Cannot activate topic model '{model_key}@{version}' with status '{status}'. "
                "Per ML_SPECIFICATION.md and operational policy, only models that have passed "
                "all predeclared release gates (APPROVED) may be activated in production."
            )

        stmt = select(MLModel).where(
            MLModel.model_key == model_key,
            MLModel.version == version,
            MLModel.task == task,
        )
        model = db.scalars(stmt).first()

        language_scope = manifest_data.get("language_scope", ["en"])
        label_schema = {
            "topics_count": manifest_data.get("topics_count", 0),
            "curated": manifest_data.get("curated", False),
        }

        if not model:
            model = MLModel(
                model_key=model_key,
                version=version,
                task=task,
                framework=manifest_data.get("framework", "scikit-learn"),
                artifact_uri=manifest_data.get("artifact_file"),
                language_scope=language_scope,
                label_schema=label_schema,
                config=manifest_data.get("config", {}),
                metrics=manifest_data.get("metrics", {}),
                is_active=is_active,
            )
            db.add(model)
        else:
            model.framework = manifest_data.get("framework", model.framework)
            model.artifact_uri = manifest_data.get("artifact_file", model.artifact_uri)
            model.language_scope = language_scope
            model.label_schema = label_schema
            model.config = manifest_data.get("config", model.config)
            model.metrics = manifest_data.get("metrics", model.metrics)
            if is_active:
                model.is_active = True

        db.flush()

        # Seed or sync topic definitions if present in manifest
        if "topics" in manifest_data and isinstance(manifest_data["topics"], list):
            self.seed_topics_from_manifest(db, model, manifest_data["topics"])

        db.commit()
        db.refresh(model)
        return model

    def seed_topics_from_manifest(
        self,
        db: Session,
        model: MLModel,
        topics_data: list[dict[str, Any]],
    ) -> list[Topic]:
        """Upsert topic taxonomy definitions linked to the specific MLModel."""
        persisted_topics: list[Topic] = []

        for t_info in topics_data:
            t_key = t_info.get("topic_key", f"topic_{t_info.get('topic_id', 0)}")
            label = t_info.get("label", t_key)
            description = t_info.get("description")
            keywords = t_info.get("keywords", [])
            rep_terms = t_info.get("representative_terms", [])
            is_outlier = bool(t_info.get("is_outlier", False))

            stmt = select(Topic).where(
                Topic.ml_model_id == model.id,
                Topic.topic_key == t_key,
            )
            existing_topic = db.scalars(stmt).first()

            if existing_topic:
                existing_topic.label = label
                existing_topic.description = description
                existing_topic.keywords = keywords
                existing_topic.representative_terms = rep_terms
                existing_topic.is_outlier = is_outlier
                persisted_topics.append(existing_topic)
            else:
                new_topic = Topic(
                    ml_model_id=model.id,
                    topic_key=t_key,
                    label=label,
                    description=description,
                    keywords=keywords,
                    representative_terms=rep_terms,
                    is_outlier=is_outlier,
                )
                db.add(new_topic)
                persisted_topics.append(new_topic)

        db.flush()
        return persisted_topics

    def activate_model(self, db: Session, model_key: str, version: str) -> MLModel:
        """Promote an approved topic model version to active production state."""
        stmt = select(MLModel).where(
            MLModel.model_key == model_key,
            MLModel.version == version,
            MLModel.task == "topic",
        )
        model = db.scalars(stmt).first()
        if not model:
            raise ValueError(f"Topic model '{model_key}@{version}' not found in registry.")

        # Deactivate any other active topic models for this specific model key
        active_models = db.scalars(
            select(MLModel).where(
                MLModel.model_key == model_key,
                MLModel.task == "topic",
                MLModel.is_active.is_(True),
            )
        ).all()
        for m in active_models:
            m.is_active = False

        model.is_active = True
        db.commit()
        db.refresh(model)
        return model
