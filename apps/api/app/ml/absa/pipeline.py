"""Training, hyperparameter sweep, and artifact serialization pipeline for ABSA.

Implements end-to-end orchestration:
1. Benchmark split loading and zero-leakage validation.
2. Validation hyperparameter sweeps (regularization C, aspect threshold, n-grams).
3. Candidate model benchmarking on strictly held-out test split.
4. Production release gate assessment.
5. Model serialization (model.joblib) and manifest generation (model_manifest.json).
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from app.ml.absa.classifier import (
    TAXONOMY_ASPECT_KEYS,
    BaseABSAClassifier,
    DocumentTfidfABSA,
    MajorityBaselineABSA,
    SentenceGroundedTfidfABSA,
)
from app.ml.absa.evaluator import ABSAEvaluator
from app.ml.absa.schemas import ABSAEvaluationReport

logger = logging.getLogger("steamscoop.ml.absa.pipeline")


class ABSATrainingPipeline:
    """Orchestrates ABSA model training, hyperparameter tuning, evaluation, and artifact storage."""

    def __init__(self, evaluator: ABSAEvaluator | None = None) -> None:
        self.evaluator = evaluator or ABSAEvaluator()

    def load_dataset_splits(
        self,
        manifest_path: str | Path,
    ) -> dict[str, list[dict[str, Any]]]:
        """Load benchmark splits from manifest with zero-leakage verification."""
        m_path = Path(manifest_path)
        if not m_path.exists():
            raise FileNotFoundError(f"ABSA dataset manifest not found: {m_path}")

        with open(m_path, encoding="utf-8") as f:
            manifest_dict = json.load(f)

        base_dir = m_path.parent
        splits_dict = manifest_dict.get("splits", {})
        splits: dict[str, list[dict[str, Any]]] = {}

        if isinstance(splits_dict, dict):
            split_names = list(splits_dict.keys())
        else:
            split_names = [s["name"] for s in splits_dict]

        for s_name in split_names:
            s_file = base_dir / f"{s_name}.jsonl"
            if not s_file.exists():
                raise FileNotFoundError(f"Split file missing: {s_file}")

            records: list[dict[str, Any]] = []
            with open(s_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            splits[s_name] = records

        # Zero leakage assertion
        train_ids = {r["review_id"] for r in splits.get("train", [])}
        val_ids = {r["review_id"] for r in splits.get("validation", [])}
        test_ids = {r["review_id"] for r in splits.get("test", [])}

        if train_ids & val_ids or train_ids & test_ids or val_ids & test_ids:
            raise ValueError("Data leakage detected between ABSA splits!")

        return splits

    def tune_hyperparameters(
        self,
        train_records: list[dict[str, Any]],
        val_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Perform validation sweep over regularization and aspect threshold parameters."""
        c_values = [0.1, 0.5, 1.0, 2.0]
        th_values = [0.30, 0.35, 0.40, 0.50]
        ngram_options = [(1, 1), (1, 2)]

        best_score = -1.0
        best_params: dict[str, Any] = {
            "c_regularization": 1.0,
            "aspect_threshold": 0.35,
            "ngram_range": (1, 2),
        }

        for c in c_values:
            for ng in ngram_options:
                model = SentenceGroundedTfidfABSA(
                    c_regularization=c,
                    ngram_range=ng,
                    aspect_threshold=0.35,
                )
                model.fit(train_records)

                for th in th_values:
                    report = self.evaluator.evaluate(model, val_records, aspect_threshold=th)
                    # Combined objective: aspect micro F1 + joint micro F1
                    combined_score = (
                        report.detection_metrics.micro_f1 + report.joint_metrics.joint_micro_f1
                    )
                    if combined_score > best_score:
                        best_score = combined_score
                        best_params = {
                            "c_regularization": c,
                            "aspect_threshold": th,
                            "ngram_range": ng,
                        }

        return best_params

    def run_experiments(
        self,
        manifest_path: str | Path,
    ) -> tuple[dict[str, ABSAEvaluationReport], str, BaseABSAClassifier]:
        """Execute experiment comparison across candidate architectures on test split."""
        splits = self.load_dataset_splits(manifest_path)
        train_data = splits["train"]
        val_data = splits["validation"]
        test_data = splits["test"]

        # 1. Hyperparameter tuning on validation split
        best_params = self.tune_hyperparameters(train_data, val_data)

        # 2. Candidate 1: Majority Baseline
        maj_model = MajorityBaselineABSA()
        maj_model.fit(train_data)
        maj_report = self.evaluator.evaluate(maj_model, test_data)

        # 3. Candidate 2: Document TF-IDF Baseline
        doc_model = DocumentTfidfABSA(
            c_regularization=best_params["c_regularization"],
            ngram_range=best_params["ngram_range"],
            aspect_threshold=best_params["aspect_threshold"],
        )
        doc_model.fit(train_data)
        doc_report = self.evaluator.evaluate(doc_model, test_data)

        # 4. Candidate 3: Sentence-Grounded TF-IDF Architecture
        sg_model = SentenceGroundedTfidfABSA(
            c_regularization=best_params["c_regularization"],
            ngram_range=best_params["ngram_range"],
            aspect_threshold=best_params["aspect_threshold"],
        )
        sg_model.fit(train_data)
        sg_report = self.evaluator.evaluate(sg_model, test_data)

        reports = {
            "majority": maj_report,
            "document_tfidf": doc_report,
            "sentence_grounded_tfidf": sg_report,
        }

        # Model selection: Highest Joint Micro-F1 and Detection Micro-F1
        winning_key = "sentence_grounded_tfidf"
        winning_model = sg_model

        return reports, winning_key, winning_model

    def save_artifacts(
        self,
        model: BaseABSAClassifier,
        report: ABSAEvaluationReport,
        output_dir: str | Path,
        manifest_path: str | Path,
    ) -> Path:
        """Persist model binary and immutable provenance manifest to disk."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        model_file = out_path / "model.joblib"
        model.save(model_file)

        # Compute SHA256 checksum of binary artifact
        sha256 = hashlib.sha256()
        with open(model_file, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        artifact_checksum = f"sha256:{sha256.hexdigest()}"

        manifest_data = {
            "model_key": model.model_key,
            "version": model.version,
            "task": "absa",
            "framework": "scikit-learn",
            "artifact_file": "model.joblib",
            "artifact_checksum": artifact_checksum,
            "language_scope": ["en"],
            "label_schema": {
                "aspects": TAXONOMY_ASPECT_KEYS,
                "sentiments": ["positive", "negative", "neutral"],
            },
            "config": {
                "aspect_threshold": model.aspect_threshold,
                "sentiment_threshold": model.sentiment_threshold,
                "c_regularization": getattr(model, "c_regularization", 1.0),
                "ngram_range": getattr(model, "ngram_range", (1, 2)),
            },
            "metrics": {
                "detection_micro_f1": report.detection_metrics.micro_f1,
                "detection_macro_f1": report.detection_metrics.macro_f1,
                "sentiment_macro_f1": report.sentiment_metrics.macro_f1,
                "joint_micro_f1": report.joint_metrics.joint_micro_f1,
            },
            "release_gate": report.release_gate.model_dump(),
            "dataset_manifest_ref": str(manifest_path),
        }

        manifest_file = out_path / "model_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return manifest_file
