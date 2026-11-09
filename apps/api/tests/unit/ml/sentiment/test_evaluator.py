"""Unit tests for SentimentEvaluator, metrics calculations, confusion matrices, and release gates."""

from app.ml.sentiment.evaluator import SentimentEvaluator


def test_evaluator_metrics_and_confusion_matrix() -> None:
    evaluator = SentimentEvaluator(confidence_threshold=0.50)

    y_true = ["positive", "positive", "negative", "negative", "neutral", "neutral"]
    y_pred = ["positive", "neutral", "negative", "negative", "neutral", "positive"]
    probas = [
        {"positive": 0.80, "negative": 0.10, "neutral": 0.10},
        {"positive": 0.35, "negative": 0.25, "neutral": 0.40},
        {"positive": 0.05, "negative": 0.90, "neutral": 0.05},
        {"positive": 0.10, "negative": 0.85, "neutral": 0.05},
        {"positive": 0.20, "negative": 0.20, "neutral": 0.60},
        {"positive": 0.55, "negative": 0.15, "neutral": 0.30},
    ]

    report = evaluator.evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        probabilities=probas,
        model_key="test-model",
        model_version="v1.0.0",
        dataset_version="v1.0.0",
        split_name="test",
    )

    assert 0.0 <= report.macro_f1 <= 1.0
    assert 0.0 <= report.accuracy <= 1.0
    assert report.sample_count == 6
    assert len(report.class_metrics) == 3

    # Check confusion matrix dimensions and values
    assert len(report.confusion_matrix.matrix) == 3
    assert len(report.confusion_matrix.matrix[0]) == 3
    assert report.confusion_matrix.labels == ["positive", "negative", "neutral"]

    # Verify Brier score calculation
    assert report.brier_score >= 0.0


def test_abstention_curve_calculation() -> None:
    evaluator = SentimentEvaluator()
    y_true = ["positive", "negative"]
    y_pred = ["positive", "negative"]
    probas = [
        {"positive": 0.70, "negative": 0.20, "neutral": 0.10},  # max 0.70
        {"positive": 0.20, "negative": 0.45, "neutral": 0.35},  # max 0.45
    ]

    curve = evaluator.compute_abstention_curve(
        y_true=y_true,
        y_pred=y_pred,
        probabilities=probas,
        thresholds=[0.40, 0.50, 0.80],
    )

    assert len(curve) == 3
    # At T=0.40, both max probas (0.70, 0.45) >= 0.40 -> coverage = 1.0
    assert curve[0]["threshold"] == 0.40
    assert curve[0]["coverage_rate"] == 1.0

    # At T=0.50, only first (0.70) >= 0.50 -> coverage = 0.50
    assert curve[1]["threshold"] == 0.50
    assert curve[1]["coverage_rate"] == 0.50

    # At T=0.80, neither >= 0.80 -> coverage = 0.0
    assert curve[2]["threshold"] == 0.80
    assert curve[2]["coverage_rate"] == 0.0


def test_slice_evaluations() -> None:
    evaluator = SentimentEvaluator()
    y_true = ["positive", "negative", "neutral", "positive"]
    y_pred = ["positive", "negative", "neutral", "positive"]
    probas = [
        {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
        {"positive": 0.1, "negative": 0.8, "neutral": 0.1},
        {"positive": 0.1, "negative": 0.1, "neutral": 0.8},
        {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
    ]
    metadata = [
        {"word_count": 4, "language": "en", "voted_up": True, "created_at": "2024-01-01"},
        {"word_count": 12, "language": "en", "voted_up": False, "created_at": "2024-01-02"},
        {"word_count": 15, "language": "en", "voted_up": True, "created_at": "2024-06-01"},
        {"word_count": 35, "language": "en", "voted_up": True, "created_at": "2024-06-02"},
    ]

    report = evaluator.evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        probabilities=probas,
        model_key="test-model",
        model_version="v1.0.0",
        dataset_version="v1.0.0",
        split_name="test",
        items_metadata=metadata,
    )

    slice_names = {s.slice_name for s in report.slice_performance}
    assert any("length" in name for name in slice_names)
    assert any("language" in name for name in slice_names)
    assert any("steam" in name for name in slice_names)
    assert any("temporal" in name for name in slice_names)


def test_check_release_gates_pass_and_fail() -> None:
    evaluator = SentimentEvaluator()

    # Create dummy high-performing report
    y_true = ["positive", "negative", "neutral"] * 10
    y_pred = list(y_true)  # 100% accuracy
    probas = [
        {"positive": 0.9, "negative": 0.05, "neutral": 0.05}
        if y == "positive"
        else (
            {"positive": 0.05, "negative": 0.9, "neutral": 0.05}
            if y == "negative"
            else {"positive": 0.05, "negative": 0.05, "neutral": 0.9}
        )
        for y in y_true
    ]
    high_report = evaluator.evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        probabilities=probas,
        model_key="high-model",
        model_version="v1.0.0",
        dataset_version="v1.0.0",
        split_name="test",
    )

    pass_result = evaluator.check_release_gates(high_report, zero_leakage_verified=True)
    assert pass_result.passed is True
    assert pass_result.status == "APPROVED"

    # Leakage failure
    leak_result = evaluator.check_release_gates(high_report, zero_leakage_verified=False)
    assert leak_result.passed is False
    assert leak_result.status == "CANDIDATE"

    # Threshold failure
    strict_result = evaluator.check_release_gates(high_report, min_macro_f1=1.01)
    assert strict_result.passed is False
    assert strict_result.status == "CANDIDATE"
