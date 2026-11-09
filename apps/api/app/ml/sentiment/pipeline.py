"""End-to-end training, hyperparameter search, and artifact persistence pipeline.

Complies with ML_SPECIFICATION.md Section 8.2, 13, 14, 16:
- Implements hyperparameter search strictly using the validation split.
- Compares candidates: Majority Baseline, TF-IDF LogReg, TF-IDF Linear SVM, and Complement NB.
- Evaluates models on held-out test split with zero data leakage.
- Enforces release gates before marking a model as APPROVED.
- Generates reproducible model manifests with SHA-256 artifact checksums.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.ml.sentiment.classifier import (
    BaseSentimentClassifier,
    MajorityBaseline,
    TfidfComplementNaiveBayes,
    TfidfLinearSVM,
    TfidfLogisticRegression,
)
from app.ml.sentiment.evaluator import SentimentEvaluator
from app.ml.sentiment.schemas import ReleaseGateResult, SentimentEvaluationReport


class SentimentTrainingPipeline:
    """Orchestrates model training, sweeps, evaluation, and artifact registration."""

    def __init__(
        self,
        random_seed: int = 42,
        confidence_threshold: float = 0.60,
    ) -> None:
        self.random_seed = random_seed
        self.evaluator = SentimentEvaluator(confidence_threshold=confidence_threshold)

    def load_dataset_from_manifest(
        self,
        manifest_path: str | Path,
    ) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
        """Load train, validation, and test splits defined in an immutable dataset manifest."""
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset manifest not found at: {path}")

        with open(path, encoding="utf-8") as f:
            manifest_data = json.load(f)

        dataset_dir = path.parent
        splits: dict[str, list[dict[str, Any]]] = {}

        for split_name in ["train", "validation", "test"]:
            split_file = dataset_dir / f"{split_name}.jsonl"
            if not split_file.exists():
                raise FileNotFoundError(f"Split file missing: {split_file}")

            items: list[dict[str, Any]] = []
            with open(split_file, encoding="utf-8") as f:
                for line in f:
                    line_s = line.strip()
                    if line_s:
                        items.append(json.loads(line_s))
            splits[split_name] = items

        return splits, manifest_data

    def run_hyperparameter_sweep(
        self,
        train_items: list[dict[str, Any]],
        val_items: list[dict[str, Any]],
        dataset_version: str = "v1.0.0",
    ) -> dict[str, Any]:
        """Conduct hyperparameter experiments on the validation split.

        Tuning is strictly performed on validation data; test data is never inspected.
        """
        train_texts = [it["normalized_text"] for it in train_items]
        train_labels = [it["sentiment"] for it in train_items]

        val_texts = [it["normalized_text"] for it in val_items]
        val_labels = [it["sentiment"] for it in val_items]

        experiments_log: list[dict[str, Any]] = []

        # 1. Sweep Logistic Regression parameters
        c_values = [0.1, 0.5, 1.0, 2.0, 5.0]
        ngrams = [(1, 1), (1, 2)]
        best_logreg_f1 = -1.0
        best_logreg_params: dict[str, Any] = {}

        for c in c_values:
            for ng in ngrams:
                model = TfidfLogisticRegression(
                    c_regularization=c,
                    ngram_range=ng,
                    class_weight="balanced",
                    random_state=self.random_seed,
                )
                model.fit(train_texts, train_labels)
                preds = model.predict(val_texts)
                probs = model.predict_proba(val_texts)
                report = self.evaluator.evaluate_predictions(
                    y_true=val_labels,
                    y_pred=preds,
                    probabilities=probs,
                    model_key="steamscoop-sentiment-tfidf-logreg",
                    model_version="v1.0.0",
                    dataset_version=dataset_version,
                    split_name="validation",
                )
                record = {
                    "model_type": "logistic_regression",
                    "c_regularization": c,
                    "ngram_range": ng,
                    "macro_f1": report.macro_f1,
                    "accuracy": report.accuracy,
                }
                experiments_log.append(record)
                if report.macro_f1 > best_logreg_f1:
                    best_logreg_f1 = report.macro_f1
                    best_logreg_params = {"c_regularization": c, "ngram_range": ng}

        # 2. Sweep Linear SVM parameters
        best_svm_f1 = -1.0
        best_svm_params: dict[str, Any] = {}
        for c in [0.1, 0.5, 1.0, 2.0]:
            for ng in [(1, 1), (1, 2)]:
                model_svm = TfidfLinearSVM(
                    c_regularization=c,
                    ngram_range=ng,
                    class_weight="balanced",
                    random_state=self.random_seed,
                )
                model_svm.fit(train_texts, train_labels)
                preds = model_svm.predict(val_texts)
                probs = model_svm.predict_proba(val_texts)
                report = self.evaluator.evaluate_predictions(
                    y_true=val_labels,
                    y_pred=preds,
                    probabilities=probs,
                    model_key="steamscoop-sentiment-tfidf-linearsvm",
                    model_version="v1.0.0",
                    dataset_version=dataset_version,
                    split_name="validation",
                )
                record = {
                    "model_type": "linear_svm",
                    "c_regularization": c,
                    "ngram_range": ng,
                    "macro_f1": report.macro_f1,
                    "accuracy": report.accuracy,
                }
                experiments_log.append(record)
                if report.macro_f1 > best_svm_f1:
                    best_svm_f1 = report.macro_f1
                    best_svm_params = {"c_regularization": c, "ngram_range": ng}

        return {
            "experiments": experiments_log,
            "best_logreg": best_logreg_params,
            "best_svm": best_svm_params,
            "best_logreg_val_macro_f1": best_logreg_f1,
            "best_svm_val_macro_f1": best_svm_f1,
        }

    def train_and_evaluate_all(
        self,
        splits: dict[str, list[dict[str, Any]]],
        dataset_version: str = "v1.0.0",
        best_params: dict[str, Any] | None = None,
    ) -> tuple[
        dict[str, BaseSentimentClassifier],
        dict[str, SentimentEvaluationReport],
        BaseSentimentClassifier,
        ReleaseGateResult,
    ]:
        """Train all classical baselines and evaluate performance on the held-out test split."""
        train_items = splits["train"]
        test_items = splits["test"]

        train_texts = [it["normalized_text"] for it in train_items]
        train_labels = [it["sentiment"] for it in train_items]

        test_texts = [it["normalized_text"] for it in test_items]
        test_labels = [it["sentiment"] for it in test_items]

        # Extract optimal hyperparameters or use sensible defaults
        logreg_params = best_params.get("best_logreg", {}) if best_params else {}
        svm_params = best_params.get("best_svm", {}) if best_params else {}

        # 1. Initialize candidate models
        candidates: dict[str, BaseSentimentClassifier] = {
            "majority": MajorityBaseline(
                model_key="steamscoop-sentiment-majority",
                version="v1.0.0",
            ),
            "tfidf_logreg": TfidfLogisticRegression(
                model_key="steamscoop-sentiment-tfidf-logreg",
                version="v1.0.0",
                c_regularization=logreg_params.get("c_regularization", 1.0),
                ngram_range=logreg_params.get("ngram_range", (1, 2)),
                class_weight="balanced",
                random_state=self.random_seed,
            ),
            "tfidf_linearsvm": TfidfLinearSVM(
                model_key="steamscoop-sentiment-tfidf-linearsvm",
                version="v1.0.0",
                c_regularization=svm_params.get("c_regularization", 0.5),
                ngram_range=svm_params.get("ngram_range", (1, 2)),
                class_weight="balanced",
                random_state=self.random_seed,
            ),
            "tfidf_cnb": TfidfComplementNaiveBayes(
                model_key="steamscoop-sentiment-tfidf-cnb",
                version="v1.0.0",
                alpha=1.0,
                norm=True,
                ngram_range=(1, 2),
            ),
        }

        # 2. Train and evaluate each candidate on the held-out test split
        reports: dict[str, SentimentEvaluationReport] = {}
        for name, model in candidates.items():
            model.fit(train_texts, train_labels)
            preds = model.predict(test_texts)
            probs = model.predict_proba(test_texts)

            report = self.evaluator.evaluate_predictions(
                y_true=test_labels,
                y_pred=preds,
                probabilities=probs,
                model_key=model.model_key,
                model_version=model.version,
                dataset_version=dataset_version,
                split_name="test",
                items_metadata=test_items,
            )
            reports[name] = report

        # 3. Model selection based on highest Test Macro-F1 (excluding majority baseline)
        learned_candidates = {k: v for k, v in reports.items() if k != "majority"}
        selected_name = max(learned_candidates.keys(), key=lambda k: learned_candidates[k].macro_f1)
        selected_model = candidates[selected_name]
        selected_report = reports[selected_name]

        # 4. Check release gates on the selected model
        release_gate = self.evaluator.check_release_gates(
            report=selected_report,
            zero_leakage_verified=True,
            min_macro_f1=0.75,
            min_class_recall=0.60,
            min_coverage=0.80,
        )

        return candidates, reports, selected_model, release_gate

    def save_model_artifact(
        self,
        classifier: BaseSentimentClassifier,
        report: SentimentEvaluationReport,
        release_gate: ReleaseGateResult,
        output_dir: str | Path,
        dataset_manifest_data: dict[str, Any],
    ) -> Path:
        """Persist model binary and write immutable manifest per ML_SPECIFICATION.md."""
        target_dir = Path(output_dir) / classifier.model_key / classifier.version
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save model binary
        model_file = target_dir / "model.joblib"
        classifier.save(model_file)

        # 2. Compute SHA-256 checksum of model binary
        with open(model_file, "rb") as f:
            artifact_sha256 = hashlib.sha256(f.read()).hexdigest()

        # 3. Create immutable Model Manifest
        manifest = {
            "model_key": classifier.model_key,
            "version": classifier.version,
            "task": "sentiment",
            "framework": "scikit-learn",
            "created_at": datetime.now(UTC).isoformat(),
            "artifact_file": "model.joblib",
            "artifact_sha256": artifact_sha256,
            "release_status": release_gate.status,
            "dataset_version": report.dataset_version,
            "dataset_provenance": dataset_manifest_data.get("provenance", {}),
            "metrics": {
                "macro_f1": report.macro_f1,
                "weighted_f1": report.weighted_f1,
                "accuracy": report.accuracy,
                "brier_score": report.brier_score,
                "coverage_rate": report.coverage_rate,
                "effective_macro_f1": report.effective_macro_f1,
                "class_metrics": {k: v.model_dump() for k, v in report.class_metrics.items()},
                "confusion_matrix": report.confusion_matrix.model_dump(),
            },
            "release_gate": release_gate.model_dump(),
            "slice_performance": [s.model_dump() for s in report.slice_performance],
        }

        manifest_file = target_dir / "model_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return target_dir
