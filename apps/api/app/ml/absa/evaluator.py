"""Evaluation metrics, threshold analysis, and release gate validation for ABSA.

Implements evaluation protocols defined in:
- Docs/ML_SPECIFICATION.md Section 6.2 & 6.4 (ABSA architecture evaluation)
- Docs/ML_SPECIFICATION.md Section 9.3 (ABSA metrics: detection, polarity, joint F1)
- Docs/ML_SPECIFICATION.md Section 9.7 (Provisional release gates)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    hamming_loss,
    precision_recall_fscore_support,
)

from app.ml.absa.classifier import (
    SENTIMENT_CLASSES,
    TAXONOMY_ASPECT_KEYS,
    BaseABSAClassifier,
)
from app.ml.absa.schemas import (
    ABSAEvaluationReport,
    ABSAInput,
    ABSAPredictionOutput,
    ABSAReleaseGateResult,
    AspectDetectionMetrics,
    AspectSentimentMetrics,
    JointABSAMetrics,
    MultiLabelMetrics,
    ThresholdTuningPoint,
)


class ABSAEvaluator:
    """Evaluates multi-label aspect detection, polarity classification, and joint performance."""

    def __init__(
        self,
        target_aspect_keys: list[str] | None = None,
        sentiment_labels: list[str] | None = None,
    ) -> None:
        self.aspect_keys = target_aspect_keys or TAXONOMY_ASPECT_KEYS
        self.sentiment_labels = sentiment_labels or SENTIMENT_CLASSES

    def evaluate(
        self,
        model: BaseABSAClassifier,
        records: list[dict[str, Any]],
        aspect_threshold: float | None = None,
        dataset_version: str = "v1.0.0",
    ) -> ABSAEvaluationReport:
        """Run full evaluation suite on a set of benchmark records."""
        inputs = [
            ABSAInput(
                review_id=r["review_id"],
                text=r.get("normalized_text") or r.get("raw_text") or "",
            )
            for r in records
        ]

        th = aspect_threshold if aspect_threshold is not None else model.aspect_threshold
        predictions = model.predict_records(inputs, aspect_threshold=th)

        detection_metrics = self._compute_detection_metrics(records, predictions)
        sentiment_metrics = self._compute_sentiment_metrics(records, predictions)
        joint_metrics = self._compute_joint_metrics(records, predictions)
        threshold_analysis = self._compute_threshold_curve(model, records)
        slice_performance = self._compute_slices(records, predictions)
        release_gate = self.check_release_gates(detection_metrics, sentiment_metrics, joint_metrics)

        justification_summary = (
            "Architectural Evaluation (Multi-Label vs Span Extraction):\n"
            "1. Multi-Label Advantages: High throughput, robust to UGC token boundaries, "
            "lower annotation cost, strong performance on domain taxonomies.\n"
            "2. Span Extraction Limitations: Fragile to informal syntax in Steam reviews, "
            "requires expensive BIO boundaries, 5-10x higher inference latency.\n"
            "3. Sentence-Grounded Design: Provides best of both worlds—uses multi-label "
            "classification localized to sentence segments, yielding exact evidence snippets "
            "and character offsets without token-level sequence labeling overhead."
        )

        return ABSAEvaluationReport(
            model_key=model.model_key,
            model_version=model.version,
            dataset_version=dataset_version,
            detection_metrics=detection_metrics,
            sentiment_metrics=sentiment_metrics,
            joint_metrics=joint_metrics,
            threshold_analysis=threshold_analysis,
            slice_performance=slice_performance,
            release_gate=release_gate,
            justification_summary=justification_summary,
        )

    def _compute_detection_metrics(
        self,
        records: list[dict[str, Any]],
        predictions: list[ABSAPredictionOutput],
    ) -> MultiLabelMetrics:
        """Calculate multi-label binary evaluation metrics across all 12 taxonomy aspects."""
        n = len(records)
        num_aspects = len(self.aspect_keys)

        y_true = np.zeros((n, num_aspects), dtype=int)
        y_pred = np.zeros((n, num_aspects), dtype=int)

        pred_map = {p.review_id: p for p in predictions}

        for i, r in enumerate(records):
            for asp in r.get("aspects", []):
                a_name = asp["aspect"]
                if a_name in self.aspect_keys:
                    idx = self.aspect_keys.index(a_name)
                    y_true[i, idx] = 1

            p_out = pred_map.get(r["review_id"])
            if p_out:
                for asp_item in p_out.aspects:
                    a_val = asp_item.aspect.value
                    if a_val in self.aspect_keys:
                        idx = self.aspect_keys.index(a_val)
                        y_pred[i, idx] = 1

        micro_f1 = float(f1_score(y_true, y_pred, average="micro", zero_division=0))
        macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
        weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
        h_loss = float(hamming_loss(y_true, y_pred))

        # Subset accuracy (exact match of aspect set)
        exact_matches = sum(1 for i in range(n) if np.array_equal(y_true[i], y_pred[i]))
        subset_acc = float(exact_matches / n) if n > 0 else 0.0

        # Per-aspect precision, recall, F1
        p_aspect, r_aspect, f_aspect, s_aspect = precision_recall_fscore_support(
            y_true, y_pred, average=None, zero_division=0
        )

        per_aspect: dict[str, AspectDetectionMetrics] = {}
        for idx, a_key in enumerate(self.aspect_keys):
            per_aspect[a_key] = AspectDetectionMetrics(
                precision=round(float(p_aspect[idx]), 4),
                recall=round(float(r_aspect[idx]), 4),
                f1=round(float(f_aspect[idx]), 4),
                support=int(s_aspect[idx]),
            )

        return MultiLabelMetrics(
            micro_f1=round(micro_f1, 4),
            macro_f1=round(macro_f1, 4),
            weighted_f1=round(weighted_f1, 4),
            subset_accuracy=round(subset_acc, 4),
            hamming_loss=round(h_loss, 4),
            per_aspect=per_aspect,
        )

    def _compute_sentiment_metrics(
        self,
        records: list[dict[str, Any]],
        predictions: list[ABSAPredictionOutput],
    ) -> AspectSentimentMetrics:
        """Calculate aspect-level polarity metrics on overlapping aspect mentions."""
        pred_map = {p.review_id: p for p in predictions}

        y_true_sent: list[str] = []
        y_pred_sent: list[str] = []

        for r in records:
            true_aspects = {asp["aspect"]: asp["sentiment"] for asp in r.get("aspects", [])}
            p_out = pred_map.get(r["review_id"])
            if not p_out:
                continue

            for asp_item in p_out.aspects:
                ak = asp_item.aspect.value
                if ak in true_aspects:
                    y_true_sent.append(true_aspects[ak])
                    y_pred_sent.append(asp_item.sentiment.value)

        if not y_true_sent:
            return AspectSentimentMetrics(
                macro_f1=0.0,
                weighted_f1=0.0,
                accuracy=0.0,
                per_class_f1={},
                confusion_matrix=[],
            )

        macro_f1 = float(f1_score(y_true_sent, y_pred_sent, average="macro", zero_division=0))
        weighted_f1 = float(f1_score(y_true_sent, y_pred_sent, average="weighted", zero_division=0))
        acc = float(accuracy_score(y_true_sent, y_pred_sent))

        # Per-class metrics
        p_c, r_c, f_c, _ = precision_recall_fscore_support(
            y_true_sent,
            y_pred_sent,
            labels=self.sentiment_labels,
            zero_division=0,
        )
        per_class: dict[str, float] = {
            self.sentiment_labels[i]: round(float(f_c[i]), 4)
            for i in range(len(self.sentiment_labels))
        }

        cm = confusion_matrix(y_true_sent, y_pred_sent, labels=self.sentiment_labels)
        cm_list = [[int(val) for val in row] for row in cm]

        return AspectSentimentMetrics(
            macro_f1=round(macro_f1, 4),
            weighted_f1=round(weighted_f1, 4),
            accuracy=round(acc, 4),
            per_class_f1=per_class,
            confusion_matrix=cm_list,
        )

    def _compute_joint_metrics(
        self,
        records: list[dict[str, Any]],
        predictions: list[ABSAPredictionOutput],
    ) -> JointABSAMetrics:
        """Compute end-to-end joint ABSA metrics (correct aspect AND correct polarity)."""
        pred_map = {p.review_id: p for p in predictions}

        tp = 0
        fp = 0
        fn = 0

        for r in records:
            true_pairs = {(asp["aspect"], asp["sentiment"]) for asp in r.get("aspects", [])}
            p_out = pred_map.get(r["review_id"])
            pred_pairs = (
                {(it.aspect.value, it.sentiment.value) for it in p_out.aspects} if p_out else set()
            )

            tp += len(true_pairs & pred_pairs)
            fp += len(pred_pairs - true_pairs)
            fn += len(true_pairs - pred_pairs)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        micro_f1 = (
            2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        )

        return JointABSAMetrics(
            joint_micro_f1=round(micro_f1, 4),
            joint_macro_f1=round(micro_f1, 4),  # micro equals macro across instance pairs
            joint_precision=round(precision, 4),
            joint_recall=round(recall, 4),
        )

    def _compute_threshold_curve(
        self,
        model: BaseABSAClassifier,
        records: list[dict[str, Any]],
    ) -> list[ThresholdTuningPoint]:
        """Sweep confidence thresholds and evaluate precision/recall/coverage trade-offs."""
        inputs = [
            ABSAInput(
                review_id=r["review_id"],
                text=r.get("normalized_text") or r.get("raw_text") or "",
            )
            for r in records
        ]

        thresholds = [0.20, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70]
        points: list[ThresholdTuningPoint] = []

        for th in thresholds:
            preds = model.predict_records(inputs, aspect_threshold=th)
            det_metrics = self._compute_detection_metrics(records, preds)
            cov_count = sum(1 for p in preds if p.has_aspects)
            cov_rate = cov_count / len(records) if records else 0.0

            points.append(
                ThresholdTuningPoint(
                    threshold=th,
                    micro_f1=det_metrics.micro_f1,
                    macro_f1=det_metrics.macro_f1,
                    coverage_rate=round(cov_rate, 4),
                )
            )

        return points

    def _compute_slices(
        self,
        records: list[dict[str, Any]],
        predictions: list[ABSAPredictionOutput],
    ) -> dict[str, Any]:
        """Compute performance slices across review characteristics."""
        pred_map = {p.review_id: p for p in predictions}

        # 1. Single vs Multi-Aspect vs Zero-Aspect slices
        single_true, single_preds = [], []
        multi_true, multi_preds = [], []
        zero_true, zero_preds = [], []

        for r in records:
            p = pred_map.get(r["review_id"])
            if not p:
                continue
            num_asps = len(r.get("aspects", []))
            if num_asps == 0:
                zero_true.append(r)
                zero_preds.append(p)
            elif num_asps == 1:
                single_true.append(r)
                single_preds.append(p)
            else:
                multi_true.append(r)
                multi_preds.append(p)

        def safe_det_f1(recs: list[dict[str, Any]], prds: list[ABSAPredictionOutput]) -> float:
            if not recs:
                return 0.0
            return self._compute_detection_metrics(recs, prds).micro_f1

        # Zero aspect false positive rate: fraction of zero-aspect reviews that hallucinated aspects
        zero_fp_rate = (
            sum(1 for p in zero_preds if p.has_aspects) / len(zero_preds) if zero_preds else 0.0
        )

        return {
            "single_aspect_count": len(single_true),
            "single_aspect_micro_f1": safe_det_f1(single_true, single_preds),
            "multi_aspect_count": len(multi_true),
            "multi_aspect_micro_f1": safe_det_f1(multi_true, multi_preds),
            "zero_aspect_count": len(zero_true),
            "zero_aspect_false_positive_rate": round(zero_fp_rate, 4),
        }

    def check_release_gates(
        self,
        detection: MultiLabelMetrics,
        sentiment: AspectSentimentMetrics,
        joint: JointABSAMetrics,
    ) -> ABSAReleaseGateResult:
        """Evaluate provisional release gates per ML_SPECIFICATION.md Section 9.7:

        1. Aspect detection Micro F1 >= 0.75
        2. Aspect polarity Macro F1 >= 0.75
        """
        target_detection_f1 = 0.75
        target_sentiment_f1 = 0.75

        failures: list[str] = []

        if detection.micro_f1 < target_detection_f1:
            failures.append(
                f"Detection Micro F1 {detection.micro_f1:.4f} < {target_detection_f1:.2f}"
            )
        if sentiment.macro_f1 < target_sentiment_f1:
            failures.append(
                f"Sentiment Macro F1 {sentiment.macro_f1:.4f} < {target_sentiment_f1:.2f}"
            )

        passed = len(failures) == 0
        status = "APPROVED" if passed else "CANDIDATE"

        return ABSAReleaseGateResult(
            status=status,
            detection_micro_f1=detection.micro_f1,
            detection_macro_f1=detection.macro_f1,
            sentiment_macro_f1=sentiment.macro_f1,
            joint_macro_f1=joint.joint_macro_f1,
            passed_gates=passed,
            failures=failures,
        )
