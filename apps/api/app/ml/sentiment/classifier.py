"""Machine learning classifiers and baseline implementations for Steam review sentiment.

Implements ML_SPECIFICATION.md Section 5.2 & 8.2:
- MajorityBaseline: Minimum baseline predicting most frequent class.
- TfidfLogisticRegression: Interpretable linear classifier with sublinear TF-IDF features.
- TfidfLinearSVM: Margin-based classifier with Platt scaling probability calibration.
- TfidfComplementNaiveBayes: Imbalance-resilient probabilistic text classifier.
"""

from __future__ import annotations

import abc
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from app.ml.preprocessor import ReviewPreprocessor
from app.ml.sentiment.schemas import SentimentInput, SentimentPredictionOutput
from app.ml.taxonomy import SentimentLabel

ORDERED_CLASSES: list[str] = [lbl.value for lbl in SentimentLabel]


class BaseSentimentClassifier(abc.ABC):
    """Abstract base class for all SteamScoop review sentiment models."""

    def __init__(
        self,
        model_key: str,
        version: str = "v1.0.0",
        preprocessor: ReviewPreprocessor | None = None,
    ) -> None:
        self.model_key = model_key
        self.version = version
        self.preprocessor = preprocessor or ReviewPreprocessor()
        self.classes_: list[str] = list(ORDERED_CLASSES)
        self.is_fitted: bool = False

    @abc.abstractmethod
    def fit(self, texts: list[str], labels: list[str]) -> BaseSentimentClassifier:
        """Train the classifier on normalized texts and target sentiment labels."""
        raise NotImplementedError

    @abc.abstractmethod
    def predict(self, texts: list[str]) -> list[str]:
        """Predict sentiment label for a list of raw or normalized texts."""
        raise NotImplementedError

    @abc.abstractmethod
    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        """Predict class probability distribution for each input text."""
        raise NotImplementedError

    def predict_records(
        self,
        inputs: list[SentimentInput],
        confidence_threshold: float = 0.60,
    ) -> list[SentimentPredictionOutput]:
        """Execute full prediction pipeline returning standard output contracts."""
        if not inputs:
            return []

        texts = [self.preprocessor.process(inp.text).normalized_text for inp in inputs]
        preds = self.predict(texts)
        probas = self.predict_proba(texts)

        results: list[SentimentPredictionOutput] = []
        for inp, label, prob_dict in zip(inputs, preds, probas, strict=True):
            top_prob = prob_dict.get(label, 0.0)
            is_abstained = top_prob < confidence_threshold

            results.append(
                SentimentPredictionOutput(
                    task="sentiment",
                    review_id=inp.review_id,
                    label=label,
                    confidence=round(top_prob, 4),
                    probabilities={k: round(v, 4) for k, v in prob_dict.items()},
                    is_abstained=is_abstained,
                    model_key=self.model_key,
                    model_version=self.version,
                )
            )

        return results

    def save(self, output_path: str | Path) -> None:
        """Persist classifier artifact using joblib."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, artifact_path: str | Path) -> BaseSentimentClassifier:
        """Load persisted classifier artifact."""
        model = joblib.load(artifact_path)
        if not isinstance(model, BaseSentimentClassifier):
            raise TypeError(f"Loaded object is not a BaseSentimentClassifier: {type(model)}")
        return model


class MajorityBaseline(BaseSentimentClassifier):
    """Minimum baseline classifier always predicting the training majority class.

    ML_SPECIFICATION.md Section 5.2 & 8.2:
    Provides the benchmark floor against which any learned model must be compared.
    """

    def __init__(
        self,
        model_key: str = "steamscoop-sentiment-majority",
        version: str = "v1.0.0",
    ) -> None:
        super().__init__(model_key=model_key, version=version)
        self.majority_class: str = SentimentLabel.POSITIVE.value
        self.class_proportions: dict[str, float] = {}

    def fit(self, texts: list[str], labels: list[str]) -> MajorityBaseline:
        if not labels:
            raise ValueError("Cannot fit MajorityBaseline on empty labels.")

        counts = Counter(labels)
        total = len(labels)
        self.majority_class = counts.most_common(1)[0][0]
        self.class_proportions = {c: round(counts.get(c, 0) / total, 4) for c in self.classes_}
        self.is_fitted = True
        return self

    def predict(self, texts: list[str]) -> list[str]:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        return [self.majority_class] * len(texts)

    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        return [dict(self.class_proportions) for _ in texts]


class TfidfLogisticRegression(BaseSentimentClassifier):
    """Sparse n-gram TF-IDF vectorizer paired with a multinomial Logistic Regression classifier."""

    def __init__(
        self,
        model_key: str = "steamscoop-sentiment-tfidf-logreg",
        version: str = "v1.0.0",
        c_regularization: float = 1.0,
        class_weight: str | None = "balanced",
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int = 10000,
        min_df: int = 1,
        sublinear_tf: bool = True,
        max_iter: int = 1000,
        random_state: int = 42,
    ) -> None:
        super().__init__(model_key=model_key, version=version)
        self.c_regularization = c_regularization
        self.class_weight = class_weight
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.min_df = min_df
        self.sublinear_tf = sublinear_tf
        self.max_iter = max_iter
        self.random_state = random_state

        self.pipeline: Pipeline | None = None

    def fit(self, texts: list[str], labels: list[str]) -> TfidfLogisticRegression:
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]

        vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            min_df=self.min_df,
            sublinear_tf=self.sublinear_tf,
            lowercase=True,
            strip_accents="unicode",
        )
        classifier = LogisticRegression(
            C=self.c_regularization,
            class_weight=self.class_weight,
            max_iter=self.max_iter,
            random_state=self.random_state,
            solver="lbfgs",
        )

        self.pipeline = Pipeline([("tfidf", vectorizer), ("clf", classifier)])
        self.pipeline.fit(clean_texts, labels)
        self.classes_ = list(classifier.classes_)
        self.is_fitted = True
        return self

    def predict(self, texts: list[str]) -> list[str]:
        if self.pipeline is None or not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]
        preds = self.pipeline.predict(clean_texts)
        return [str(p) for p in preds]

    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        if self.pipeline is None or not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]
        probs = self.pipeline.predict_proba(clean_texts)

        results: list[dict[str, float]] = []
        for row in probs:
            p_dict = {str(c): float(round(row[idx], 4)) for idx, c in enumerate(self.classes_)}
            # Ensure full ordered class distribution is always populated
            for cls_name in ORDERED_CLASSES:
                p_dict.setdefault(cls_name, 0.0)
            results.append(p_dict)
        return results


class TfidfLinearSVM(BaseSentimentClassifier):
    """TF-IDF vectorizer paired with LinearSVC, calibrated via Platt scaling."""

    def __init__(
        self,
        model_key: str = "steamscoop-sentiment-tfidf-linearsvm",
        version: str = "v1.0.0",
        c_regularization: float = 0.5,
        class_weight: str | None = "balanced",
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int = 10000,
        min_df: int = 1,
        sublinear_tf: bool = True,
        random_state: int = 42,
    ) -> None:
        super().__init__(model_key=model_key, version=version)
        self.c_regularization = c_regularization
        self.class_weight = class_weight
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.min_df = min_df
        self.sublinear_tf = sublinear_tf
        self.random_state = random_state

        self.pipeline: Pipeline | None = None

    def fit(self, texts: list[str], labels: list[str]) -> TfidfLinearSVM:
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]

        vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            min_df=self.min_df,
            sublinear_tf=self.sublinear_tf,
            lowercase=True,
            strip_accents="unicode",
        )
        base_svm = LinearSVC(
            C=self.c_regularization,
            class_weight=self.class_weight,
            random_state=self.random_state,
            max_iter=2000,
        )

        # Use CalibratedClassifierCV when minimum class count allows (>= 2 folds)
        min_class_count = min(Counter(labels).values()) if labels else 0
        if min_class_count >= 2:
            cv_splits = min(3, min_class_count)
            clf = CalibratedClassifierCV(estimator=base_svm, method="sigmoid", cv=cv_splits)
            self._uses_calibrated = True
        else:
            clf = base_svm
            self._uses_calibrated = False

        self.pipeline = Pipeline([("tfidf", vectorizer), ("clf", clf)])
        self.pipeline.fit(clean_texts, labels)
        self.classes_ = list(clf.classes_)
        self.is_fitted = True
        return self

    def predict(self, texts: list[str]) -> list[str]:
        if self.pipeline is None or not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]
        preds = self.pipeline.predict(clean_texts)
        return [str(p) for p in preds]

    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        if self.pipeline is None or not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]

        if getattr(self, "_uses_calibrated", True):
            probs = self.pipeline.predict_proba(clean_texts)
        else:
            decision = self.pipeline.decision_function(clean_texts)
            if decision.ndim == 1:
                decision = np.vstack([-decision, decision]).T
            exp_d = np.exp(decision - np.max(decision, axis=1, keepdims=True))
            probs = exp_d / np.sum(exp_d, axis=1, keepdims=True)

        results: list[dict[str, float]] = []
        for row in probs:
            p_dict = {str(c): float(round(row[idx], 4)) for idx, c in enumerate(self.classes_)}
            for cls_name in ORDERED_CLASSES:
                p_dict.setdefault(cls_name, 0.0)
            results.append(p_dict)
        return results


class TfidfComplementNaiveBayes(BaseSentimentClassifier):
    """Complement Naive Bayes classifier designed for imbalanced text corpora."""

    def __init__(
        self,
        model_key: str = "steamscoop-sentiment-tfidf-cnb",
        version: str = "v1.0.0",
        alpha: float = 1.0,
        norm: bool = True,
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int = 10000,
        min_df: int = 1,
        sublinear_tf: bool = True,
    ) -> None:
        super().__init__(model_key=model_key, version=version)
        self.alpha = alpha
        self.norm = norm
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.min_df = min_df
        self.sublinear_tf = sublinear_tf

        self.pipeline: Pipeline | None = None

    def fit(self, texts: list[str], labels: list[str]) -> TfidfComplementNaiveBayes:
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]

        vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            min_df=self.min_df,
            sublinear_tf=self.sublinear_tf,
            lowercase=True,
            strip_accents="unicode",
        )
        classifier = ComplementNB(alpha=self.alpha, norm=self.norm)

        self.pipeline = Pipeline([("tfidf", vectorizer), ("clf", classifier)])
        self.pipeline.fit(clean_texts, labels)
        self.classes_ = list(classifier.classes_)
        self.is_fitted = True
        return self

    def predict(self, texts: list[str]) -> list[str]:
        if self.pipeline is None or not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]
        preds = self.pipeline.predict(clean_texts)
        return [str(p) for p in preds]

    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        if self.pipeline is None or not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        clean_texts = [self.preprocessor.process(t).normalized_text for t in texts]
        probs = self.pipeline.predict_proba(clean_texts)

        results: list[dict[str, float]] = []
        for row in probs:
            p_dict = {str(c): float(round(row[idx], 4)) for idx, c in enumerate(self.classes_)}
            for cls_name in ORDERED_CLASSES:
                p_dict.setdefault(cls_name, 0.0)
            results.append(p_dict)
        return results
