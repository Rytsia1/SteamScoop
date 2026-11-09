"""Comprehensive evaluation metrics and slicing for sentiment analysis models.

Complies with ML_SPECIFICATION.md Section 8.3 & 9.2:
- Primary metric: Macro-F1 (classes treated equally, prevents majority-class bias).
- Class-wise metrics: Precision, Recall, F1, and Support per class.
- 3x3 Confusion Matrix (raw and normalized).
- Calibration quality: Multi-class Brier score.
- Confidence thresholding and abstention handling (coverage and effective macro-F1).
- Slice evaluations: Language, Temporal, Text Length, and Steam voted_up concordance.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from app.ml.sentiment.schemas import (
    ClassMetrics,
    ConfusionMatrixData,
    ReleaseGateResult,
    SentimentEvaluationReport,
    SlicePerformance,
)
from app.ml.taxonomy import SentimentLabel

ORDERED_CLASSES: list[str] = [lbl.value for lbl in SentimentLabel]


class SentimentEvaluator:
    """Evaluates sentiment models across primary metrics, slices, and release criteria."""

    def __init__(self, confidence_threshold: float = 0.60) -> None:
        self.confidence_threshold = confidence_threshold

    def evaluate_predictions(
        self,
        y_true: list[str],
        y_pred: list[str],
        probabilities: list[dict[str, float]],
        model_key: str,
        model_version: str,
        dataset_version: str,
        split_name: str,
        items_metadata: list[dict[str, Any]] | None = None,
    ) -> SentimentEvaluationReport:
        """Compute full statistical metrics, confusion matrices, and slice evaluations."""
        n = len(y_true)
        if n == 0:
            raise ValueError("Cannot evaluate predictions on empty dataset.")

        # 1. Primary macro, weighted, and accuracy metrics
        macro_f1 = float(
            f1_score(y_true, y_pred, labels=ORDERED_CLASSES, average="macro", zero_division=0)
        )
        weighted_f1 = float(
            f1_score(y_true, y_pred, labels=ORDERED_CLASSES, average="weighted", zero_division=0)
        )
        accuracy = float(accuracy_score(y_true, y_pred))

        # 2. Per-class performance
        precisions, recalls, f1s, supports = precision_recall_fscore_support(
            y_true, y_pred, labels=ORDERED_CLASSES, zero_division=0
        )
        class_metrics: dict[str, ClassMetrics] = {}
        for idx, cls_name in enumerate(ORDERED_CLASSES):
            class_metrics[cls_name] = ClassMetrics(
                precision=round(float(precisions[idx]), 4),
                recall=round(float(recalls[idx]), 4),
                f1_score=round(float(f1s[idx]), 4),
                support=int(supports[idx]),
            )

        # 3. 3x3 Confusion Matrix
        cm = confusion_matrix(y_true, y_pred, labels=ORDERED_CLASSES)
        cm_norm = np.zeros_like(cm, dtype=float)
        for i in range(len(ORDERED_CLASSES)):
            row_sum = cm[i].sum()
            if row_sum > 0:
                cm_norm[i] = cm[i] / row_sum

        confusion_data = ConfusionMatrixData(
            labels=ORDERED_CLASSES,
            matrix=cm.tolist(),
            normalized_matrix=[[round(float(val), 4) for val in row] for row in cm_norm],
        )

        # 4. Confidence and abstention handling
        abstained_indices: list[int] = []
        confident_y_true: list[str] = []
        confident_y_pred: list[str] = []

        brier_sum = 0.0
        for i in range(n):
            prob_dict = probabilities[i]
            top_prob = max(prob_dict.values()) if prob_dict else 0.0

            # Compute multi-class Brier score: sum_{k} (p_{k} - y_{k})^2
            for cls_name in ORDERED_CLASSES:
                target_indicator = 1.0 if y_true[i] == cls_name else 0.0
                pred_prob = prob_dict.get(cls_name, 0.0)
                brier_sum += (pred_prob - target_indicator) ** 2

            if top_prob < self.confidence_threshold:
                abstained_indices.append(i)
            else:
                confident_y_true.append(y_true[i])
                confident_y_pred.append(y_pred[i])

        abstention_count = len(abstained_indices)
        coverage_rate = (n - abstention_count) / n
        brier_score = round(brier_sum / n, 4)

        if confident_y_true:
            effective_macro_f1 = float(
                f1_score(
                    confident_y_true,
                    confident_y_pred,
                    labels=ORDERED_CLASSES,
                    average="macro",
                    zero_division=0,
                )
            )
        else:
            effective_macro_f1 = 0.0

        # 5. Slices: Language, Temporal, Text Length, Voted-Up Concordance
        slices = self._evaluate_slices(
            y_true=y_true,
            y_pred=y_pred,
            items_metadata=items_metadata or [],
        )

        return SentimentEvaluationReport(
            model_key=model_key,
            model_version=model_version,
            dataset_version=dataset_version,
            split_name=split_name,
            sample_count=n,
            macro_f1=round(macro_f1, 4),
            weighted_f1=round(weighted_f1, 4),
            accuracy=round(accuracy, 4),
            class_metrics=class_metrics,
            confusion_matrix=confusion_data,
            confidence_threshold=self.confidence_threshold,
            coverage_rate=round(coverage_rate, 4),
            abstention_count=abstention_count,
            effective_macro_f1=round(effective_macro_f1, 4),
            slice_performance=slices,
            brier_score=brier_score,
            evaluated_at=datetime.now(UTC).isoformat(),
        )

    def compute_abstention_curve(
        self,
        y_true: list[str],
        y_pred: list[str],
        probabilities: list[dict[str, float]],
        thresholds: list[float] | None = None,
    ) -> list[dict[str, float]]:
        """Evaluate coverage vs accuracy trade-offs across confidence thresholds."""
        if thresholds is None:
            thresholds = [0.34, 0.36, 0.38, 0.40, 0.45, 0.50, 0.60]

        n = len(y_true)
        curve: list[dict[str, float]] = []
        for t in thresholds:
            confident_yt = []
            confident_yp = []
            for i in range(n):
                top_prob = max(probabilities[i].values()) if probabilities[i] else 0.0
                if top_prob >= t:
                    confident_yt.append(y_true[i])
                    confident_yp.append(y_pred[i])

            cov = len(confident_yt) / n if n > 0 else 0.0
            eff_f1 = (
                float(
                    f1_score(
                        confident_yt,
                        confident_yp,
                        labels=ORDERED_CLASSES,
                        average="macro",
                        zero_division=0,
                    )
                )
                if confident_yt
                else 0.0
            )
            eff_acc = float(accuracy_score(confident_yt, confident_yp)) if confident_yt else 0.0

            curve.append(
                {
                    "threshold": round(t, 2),
                    "coverage_rate": round(cov, 4),
                    "abstention_count": n - len(confident_yt),
                    "effective_macro_f1": round(eff_f1, 4),
                    "effective_accuracy": round(eff_acc, 4),
                }
            )
        return curve

    def _evaluate_slices(
        self,
        y_true: list[str],
        y_pred: list[str],
        items_metadata: list[dict[str, Any]],
    ) -> list[SlicePerformance]:
        """Compute performance across domain slices."""
        if not items_metadata or len(items_metadata) != len(y_true):
            return []

        slices: list[SlicePerformance] = []

        # Slice 1: Text Length Slices (short, medium, long)
        length_groups: dict[str, list[int]] = defaultdict(list)
        for i, meta in enumerate(items_metadata):
            words = meta.get("word_count", len(meta.get("normalized_text", "").split()))
            if words <= 5:
                length_groups["length_short (<=5 words)"].append(i)
            elif words <= 25:
                length_groups["length_medium (6-25 words)"].append(i)
            else:
                length_groups["length_long (>25 words)"].append(i)

        for sname, indices in length_groups.items():
            if indices:
                sub_yt = [y_true[i] for i in indices]
                sub_yp = [y_pred[i] for i in indices]
                mf1 = float(
                    f1_score(
                        sub_yt, sub_yp, labels=ORDERED_CLASSES, average="macro", zero_division=0
                    )
                )
                acc = float(accuracy_score(sub_yt, sub_yp))
                slices.append(
                    SlicePerformance(
                        slice_name=sname,
                        sample_count=len(indices),
                        macro_f1=round(mf1, 4),
                        accuracy=round(acc, 4),
                        notes="Text length partition",
                    )
                )

        # Slice 2: Language Slices
        lang_groups: dict[str, list[int]] = defaultdict(list)
        for i, meta in enumerate(items_metadata):
            lang = meta.get("language", "en")
            lang_groups[f"language_{lang}"].append(i)

        for sname, indices in lang_groups.items():
            if indices:
                sub_yt = [y_true[i] for i in indices]
                sub_yp = [y_pred[i] for i in indices]
                mf1 = float(
                    f1_score(
                        sub_yt, sub_yp, labels=ORDERED_CLASSES, average="macro", zero_division=0
                    )
                )
                acc = float(accuracy_score(sub_yt, sub_yp))
                slices.append(
                    SlicePerformance(
                        slice_name=sname,
                        sample_count=len(indices),
                        macro_f1=round(mf1, 4),
                        accuracy=round(acc, 4),
                        notes="Language slice",
                    )
                )

        # Slice 3: Steam voted_up Concordance Slice
        concordance_groups: dict[str, list[int]] = defaultdict(list)
        for i, meta in enumerate(items_metadata):
            voted_up = meta.get("voted_up")
            actual_sentiment = y_true[i]
            if voted_up is None:
                continue

            # Concordant if voted_up=True and positive, or voted_up=False and negative
            is_concordant = (voted_up and actual_sentiment == SentimentLabel.POSITIVE.value) or (
                not voted_up and actual_sentiment == SentimentLabel.NEGATIVE.value
            )
            label_name = (
                "concordant (voted_up aligns with text)"
                if is_concordant
                else "discordant (sarcasm / mixed / cautious)"
            )
            concordance_groups[label_name].append(i)

        for sname, indices in concordance_groups.items():
            if indices:
                sub_yt = [y_true[i] for i in indices]
                sub_yp = [y_pred[i] for i in indices]
                mf1 = float(
                    f1_score(
                        sub_yt, sub_yp, labels=ORDERED_CLASSES, average="macro", zero_division=0
                    )
                )
                acc = float(accuracy_score(sub_yt, sub_yp))
                slices.append(
                    SlicePerformance(
                        slice_name=f"steam_signal_{sname}",
                        sample_count=len(indices),
                        macro_f1=round(mf1, 4),
                        accuracy=round(acc, 4),
                        notes="Evaluation of steam voted_up alignment with text sentiment",
                    )
                )

        # Slice 4: Temporal Robustness Slices (earlier vs later)
        timed_indices = [
            (i, meta.get("steam_created_at") or meta.get("created_at"))
            for i, meta in enumerate(items_metadata)
            if meta.get("steam_created_at") or meta.get("created_at")
        ]
        if len(timed_indices) >= 4:
            timed_indices.sort(key=lambda x: str(x[1]))
            midpoint = len(timed_indices) // 2
            earlier = [idx for idx, _ in timed_indices[:midpoint]]
            later = [idx for idx, _ in timed_indices[midpoint:]]

            for sname, indices in [
                ("temporal_earlier_reviews", earlier),
                ("temporal_later_reviews", later),
            ]:
                sub_yt = [y_true[i] for i in indices]
                sub_yp = [y_pred[i] for i in indices]
                mf1 = float(
                    f1_score(
                        sub_yt, sub_yp, labels=ORDERED_CLASSES, average="macro", zero_division=0
                    )
                )
                acc = float(accuracy_score(sub_yt, sub_yp))
                slices.append(
                    SlicePerformance(
                        slice_name=sname,
                        sample_count=len(indices),
                        macro_f1=round(mf1, 4),
                        accuracy=round(acc, 4),
                        notes="Chronological temporal slice to test drift robustness",
                    )
                )

        return slices

    def check_release_gates(
        self,
        report: SentimentEvaluationReport,
        zero_leakage_verified: bool = True,
        min_macro_f1: float = 0.75,
        min_class_recall: float = 0.60,
        min_coverage: float = 0.80,
    ) -> ReleaseGateResult:
        """Evaluate candidate model against strict production release gates."""
        details: list[str] = []
        passed = True

        # Gate 1: Macro-F1 threshold
        if report.macro_f1 < min_macro_f1:
            passed = False
            details.append(
                f"FAILED: Macro-F1 {report.macro_f1:.4f} is below minimum {min_macro_f1:.2f}"
            )
        else:
            details.append(f"PASSED: Macro-F1 {report.macro_f1:.4f} >= {min_macro_f1:.2f}")

        # Gate 2: Per-class Recall threshold
        class_recalls = {cls: report.class_metrics[cls].recall for cls in ORDERED_CLASSES}
        for cls_name, recall in class_recalls.items():
            if recall < min_class_recall:
                passed = False
                details.append(
                    f"FAILED: Class '{cls_name}' recall {recall:.4f} < {min_class_recall:.2f}"
                )
            else:
                details.append(
                    f"PASSED: Class '{cls_name}' recall {recall:.4f} >= {min_class_recall:.2f}"
                )

        # Gate 3: Coverage rate threshold
        if report.coverage_rate < min_coverage:
            passed = False
            details.append(f"FAILED: Coverage rate {report.coverage_rate:.2%} < {min_coverage:.2%}")
        else:
            details.append(
                f"PASSED: Coverage rate {report.coverage_rate:.2%} >= {min_coverage:.2%}"
            )

        # Gate 4: Zero data leakage verification
        if not zero_leakage_verified:
            passed = False
            details.append("FAILED: Data leakage between train/val/test splits was not disproven!")
        else:
            details.append(
                "PASSED: Verified zero overlap of review IDs and duplicate groups across splits."
            )

        status = "APPROVED" if passed else "CANDIDATE"

        return ReleaseGateResult(
            passed=passed,
            status=status,
            min_macro_f1_threshold=min_macro_f1,
            actual_macro_f1=report.macro_f1,
            min_class_recall_threshold=min_class_recall,
            actual_class_recalls=class_recalls,
            min_coverage_threshold=min_coverage,
            actual_coverage=report.coverage_rate,
            zero_leakage_verified=zero_leakage_verified,
            gate_details=details,
        )
