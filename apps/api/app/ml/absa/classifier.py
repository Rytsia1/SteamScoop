"""Aspect-Based Sentiment Analysis (ABSA) model implementations.

Implements:
1. BaseABSAClassifier: Abstract interface for ABSA classifiers.
2. MajorityBaselineABSA: Benchmark floor predicting majority aspect and polarity.
3. DocumentTfidfABSA: Classical multi-label TF-IDF + LogisticRegression baseline.
4. SentenceGroundedTfidfABSA: Sentence-grounded multi-label ABSA architecture with
   localized aspect detection, non-mixed sentiment classification, and evidence offsets.
"""

from __future__ import annotations

import abc
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

from app.ml.absa.schemas import (
    ABSAInput,
    ABSAPredictionOutput,
    AspectPredictionItem,
)
from app.ml.taxonomy import ASPECT_TAXONOMY, AspectKey, SentimentLabel

# Ordered canonical aspect list
TAXONOMY_ASPECT_KEYS: list[str] = [ak.value for ak in AspectKey]
SENTIMENT_CLASSES: list[str] = [
    SentimentLabel.POSITIVE.value,
    SentimentLabel.NEGATIVE.value,
    SentimentLabel.NEUTRAL.value,
]


def split_sentences_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Segment review text into sentences or clauses while tracking exact character offsets."""
    results: list[tuple[str, int, int]] = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?\n]+|$)", text):
        raw_span = match.group()
        span_text = raw_span.strip()
        if span_text:
            rel_start = raw_span.find(span_text)
            start_offset = match.start() + rel_start
            end_offset = start_offset + len(span_text)
            results.append((span_text, start_offset, end_offset))
    if not results and text.strip():
        results.append((text.strip(), 0, len(text.strip())))
    return results


class BaseABSAClassifier(abc.ABC):
    """Abstract base class for all ABSA models in SteamScoop."""

    def __init__(
        self,
        model_key: str,
        version: str = "v1.0.0",
        aspect_threshold: float = 0.40,
        sentiment_threshold: float = 0.35,
    ) -> None:
        self.model_key = model_key
        self.version = version
        self.aspect_threshold = aspect_threshold
        self.sentiment_threshold = sentiment_threshold
        self.is_fitted = False

    @abc.abstractmethod
    def fit(self, records: list[dict[str, Any]]) -> BaseABSAClassifier:
        """Train the classifier on benchmark records."""

    @abc.abstractmethod
    def predict_records(
        self,
        inputs: list[ABSAInput],
        aspect_threshold: float | None = None,
    ) -> list[ABSAPredictionOutput]:
        """Execute ABSA prediction on batch of inputs."""

    def save(self, path: str | Path) -> None:
        """Serialize model artifact to disk using joblib."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, target_path)

    @classmethod
    def load(cls, path: str | Path) -> BaseABSAClassifier:
        """Deserialize model artifact from disk."""
        model = joblib.load(path)
        if not isinstance(model, BaseABSAClassifier):
            raise TypeError(f"Loaded artifact {type(model)} is not a BaseABSAClassifier.")
        return model


class MajorityBaselineABSA(BaseABSAClassifier):
    """Empirical floor baseline: predicts the majority aspect with its empirical polarity."""

    def __init__(
        self,
        model_key: str = "steamscoop-absa-majority",
        version: str = "v1.0.0",
        aspect_threshold: float = 0.50,
    ) -> None:
        super().__init__(model_key, version, aspect_threshold)
        self.majority_aspect: str = AspectKey.GAMEPLAY.value
        self.majority_sentiment: str = SentimentLabel.POSITIVE.value

    def fit(self, records: list[dict[str, Any]]) -> MajorityBaselineABSA:
        aspect_counts: Counter[str] = Counter()
        sentiment_counts: Counter[str] = Counter()

        for r in records:
            for asp in r.get("aspects", []):
                aspect_counts[asp["aspect"]] += 1
                sentiment_counts[asp["sentiment"]] += 1

        if aspect_counts:
            self.majority_aspect = aspect_counts.most_common(1)[0][0]
        if sentiment_counts:
            self.majority_sentiment = sentiment_counts.most_common(1)[0][0]

        self.is_fitted = True
        return self

    def predict_records(
        self,
        inputs: list[ABSAInput],
        aspect_threshold: float | None = None,
    ) -> list[ABSAPredictionOutput]:
        outputs: list[ABSAPredictionOutput] = []
        for inp in inputs:
            t0 = time.perf_counter()
            item = AspectPredictionItem(
                aspect=AspectKey(self.majority_aspect),
                sentiment=SentimentLabel(self.majority_sentiment),
                confidence=0.50,
                sentiment_confidence=0.50,
                evidence_text=inp.text[:100],
                start_offset=0,
                end_offset=min(100, len(inp.text)),
                probabilities={self.majority_sentiment: 1.0},
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            outputs.append(
                ABSAPredictionOutput(
                    review_id=inp.review_id,
                    aspects=[item],
                    has_aspects=True,
                    model_key=self.model_key,
                    model_version=self.version,
                    latency_ms=elapsed_ms,
                )
            )
        return outputs


class DocumentTfidfABSA(BaseABSAClassifier):
    """Document-level multi-label TF-IDF + Logistic Regression baseline."""

    def __init__(
        self,
        model_key: str = "steamscoop-absa-doc-tfidf",
        version: str = "v1.0.0",
        aspect_threshold: float = 0.40,
        c_regularization: float = 1.0,
        ngram_range: tuple[int, int] = (1, 2),
    ) -> None:
        super().__init__(model_key, version, aspect_threshold)
        self.c_regularization = c_regularization
        self.ngram_range = ngram_range
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            sublinear_tf=True,
            max_features=8000,
            token_pattern=r"(?u)\b\w+\b",
        )
        self.aspect_classifier = OneVsRestClassifier(
            LogisticRegression(
                C=c_regularization,
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
            )
        )
        self.sentiment_classifier = LogisticRegression(
            C=c_regularization,
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )
        self.classes_: list[str] = TAXONOMY_ASPECT_KEYS

    def fit(self, records: list[dict[str, Any]]) -> DocumentTfidfABSA:
        texts: list[str] = []
        y_aspects: list[list[int]] = []
        sentiment_texts: list[str] = []
        sentiment_labels: list[str] = []

        for r in records:
            txt = r.get("normalized_text") or r.get("raw_text") or ""
            texts.append(txt)
            asp_set = {asp["aspect"] for asp in r.get("aspects", [])}
            y_aspects.append([1 if ak in asp_set else 0 for ak in self.classes_])

            for asp in r.get("aspects", []):
                snippet = asp.get("snippet") or txt
                sentiment_texts.append(snippet)
                sentiment_labels.append(asp.get("sentiment", SentimentLabel.POSITIVE.value))

        X_tfidf = self.vectorizer.fit_transform(texts)
        y_mat = np.array(y_aspects)
        self.aspect_classifier.fit(X_tfidf, y_mat)

        if sentiment_texts:
            X_sent = self.vectorizer.transform(sentiment_texts)
            self.sentiment_classifier.fit(X_sent, sentiment_labels)
        else:
            self.sentiment_classifier.fit(X_tfidf, [SentimentLabel.POSITIVE.value] * len(texts))

        self.is_fitted = True
        return self

    def predict_records(
        self,
        inputs: list[ABSAInput],
        aspect_threshold: float | None = None,
    ) -> list[ABSAPredictionOutput]:
        th = aspect_threshold if aspect_threshold is not None else self.aspect_threshold
        outputs: list[ABSAPredictionOutput] = []
        if not inputs:
            return outputs

        texts = [inp.text for inp in inputs]
        X_tfidf = self.vectorizer.transform(texts)

        # Aspect probability matrix (N, num_aspects)
        aspect_probs = self.aspect_classifier.predict_proba(X_tfidf)
        # Document sentiment probability matrix (N, num_sentiments)
        sent_probs = self.sentiment_classifier.predict_proba(X_tfidf)
        sent_classes = list(self.sentiment_classifier.classes_)

        for i, inp in enumerate(inputs):
            t0 = time.perf_counter()
            items: list[AspectPredictionItem] = []
            doc_sent_dist = {
                sent_classes[j]: float(sent_probs[i][j]) for j in range(len(sent_classes))
            }
            top_sent_label = max(doc_sent_dist, key=doc_sent_dist.get)  # type: ignore[arg-type]
            top_sent_conf = doc_sent_dist[top_sent_label]

            for a_idx, a_key in enumerate(self.classes_):
                prob = float(aspect_probs[i][a_idx])
                if prob >= th:
                    items.append(
                        AspectPredictionItem(
                            aspect=AspectKey(a_key),
                            sentiment=SentimentLabel(top_sent_label),
                            confidence=round(prob, 4),
                            sentiment_confidence=round(top_sent_conf, 4),
                            evidence_text=inp.text,
                            start_offset=0,
                            end_offset=len(inp.text),
                            probabilities={k: round(v, 4) for k, v in doc_sent_dist.items()},
                        )
                    )

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            outputs.append(
                ABSAPredictionOutput(
                    review_id=inp.review_id,
                    aspects=items,
                    has_aspects=len(items) > 0,
                    model_key=self.model_key,
                    model_version=self.version,
                    latency_ms=elapsed_ms,
                )
            )

        return outputs


class SentenceGroundedTfidfABSA(BaseABSAClassifier):
    """Sentence-grounded multi-label ABSA architecture.

    Features:
    1. Sentence segmentation preserving character boundary offsets.
    2. Localized aspect detection combining sublinear TF-IDF classification
       with domain-specific taxonomy keyword affinity.
    3. Independent, non-mixed aspect-level sentiment classification evaluated
       strictly on the grounded aspect evidence sentence/clause.
    4. Abstention handling when confidence falls below the calibrated threshold.
    """

    def __init__(
        self,
        model_key: str = "steamscoop-absa-sentence-tfidf",
        version: str = "v1.0.0",
        aspect_threshold: float = 0.35,
        sentiment_threshold: float = 0.35,
        c_regularization: float = 1.0,
        ngram_range: tuple[int, int] = (1, 2),
    ) -> None:
        super().__init__(model_key, version, aspect_threshold, sentiment_threshold)
        self.c_regularization = c_regularization
        self.ngram_range = ngram_range
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            sublinear_tf=True,
            max_features=10000,
            token_pattern=r"(?u)\b\w+\b",
        )
        self.aspect_classifier = OneVsRestClassifier(
            LogisticRegression(
                C=c_regularization,
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
            )
        )
        self.sentiment_classifier = LogisticRegression(
            C=c_regularization,
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )
        self.classes_: list[str] = TAXONOMY_ASPECT_KEYS
        # Compile keyword matching patterns from taxonomy for high-precision grounding
        self.keyword_patterns: dict[str, list[str]] = {
            ak.value: [kw.lower() for kw in defn.seed_keywords]
            for ak, defn in ASPECT_TAXONOMY.items()
        }

    def fit(self, records: list[dict[str, Any]]) -> SentenceGroundedTfidfABSA:
        training_units: list[str] = []
        y_aspects: list[list[int]] = []
        sentiment_texts: list[str] = []
        sentiment_labels: list[str] = []

        for r in records:
            txt = r.get("normalized_text") or r.get("raw_text") or ""
            r_aspects = r.get("aspects", [])
            asp_set = {asp["aspect"] for asp in r_aspects}

            # 1. Whole document level unit
            training_units.append(txt)
            y_aspects.append([1 if ak in asp_set else 0 for ak in self.classes_])

            # 2. Localized snippet level units (if available)
            for asp in r_aspects:
                snippet = asp.get("snippet") or txt
                training_units.append(snippet)
                y_aspects.append([1 if ak == asp["aspect"] else 0 for ak in self.classes_])

                sentiment_texts.append(snippet)
                sentiment_labels.append(asp.get("sentiment", SentimentLabel.POSITIVE.value))

        X_tfidf = self.vectorizer.fit_transform(training_units)
        y_mat = np.array(y_aspects)
        self.aspect_classifier.fit(X_tfidf, y_mat)

        if sentiment_texts:
            X_sent = self.vectorizer.transform(sentiment_texts)
            self.sentiment_classifier.fit(X_sent, sentiment_labels)
        else:
            self.sentiment_classifier.fit(
                X_tfidf, [SentimentLabel.POSITIVE.value] * len(training_units)
            )

        self.is_fitted = True
        return self

    def _score_sentence_aspects(self, sentence_text: str) -> np.ndarray:
        """Compute aspect probability vector combining TF-IDF and taxonomy keyword priors."""
        vec = self.vectorizer.transform([sentence_text])
        raw_probs = self.aspect_classifier.predict_proba(vec)[0]  # shape: (num_aspects,)

        lower_sent = sentence_text.lower()
        adjusted = np.copy(raw_probs)

        # Keyword affinity boost
        for idx, ak in enumerate(self.classes_):
            keywords = self.keyword_patterns.get(ak, [])
            match_count = sum(1 for kw in keywords if kw in lower_sent)
            if match_count > 0:
                # Add calibrated prior boost for explicit keyword occurrence
                boost = min(0.35, 0.15 * match_count)
                adjusted[idx] = min(0.99, adjusted[idx] + boost)

        return adjusted

    def predict_records(
        self,
        inputs: list[ABSAInput],
        aspect_threshold: float | None = None,
    ) -> list[ABSAPredictionOutput]:
        th = aspect_threshold if aspect_threshold is not None else self.aspect_threshold
        outputs: list[ABSAPredictionOutput] = []
        sent_classes = list(self.sentiment_classifier.classes_)

        for inp in inputs:
            t0 = time.perf_counter()
            text = inp.text
            sentences = split_sentences_with_offsets(text)

            # Map aspect_key -> best AspectPredictionItem (deduplicating per review constraint)
            best_aspect_items: dict[str, AspectPredictionItem] = {}

            for s_text, start_o, end_o in sentences:
                probs = self._score_sentence_aspects(s_text)
                for a_idx, a_key in enumerate(self.classes_):
                    prob = float(probs[a_idx])
                    if prob >= th:
                        # Aspect detected in this sentence: evaluate sentiment ON THIS SENTENCE
                        s_vec = self.vectorizer.transform([s_text])
                        s_sent_probs = self.sentiment_classifier.predict_proba(s_vec)[0]
                        sent_dist = {
                            sent_classes[k]: float(s_sent_probs[k])
                            for k in range(len(sent_classes))
                        }
                        top_sent = max(sent_dist, key=sent_dist.get)  # type: ignore[arg-type]
                        top_sent_conf = sent_dist[top_sent]

                        item = AspectPredictionItem(
                            aspect=AspectKey(a_key),
                            sentiment=SentimentLabel(top_sent),
                            confidence=round(prob, 4),
                            sentiment_confidence=round(top_sent_conf, 4),
                            evidence_text=s_text,
                            start_offset=start_o,
                            end_offset=end_o,
                            probabilities={k: round(v, 4) for k, v in sent_dist.items()},
                        )

                        # Retain mention with highest aspect confidence
                        if (
                            a_key not in best_aspect_items
                            or prob > best_aspect_items[a_key].confidence
                        ):
                            best_aspect_items[a_key] = item

            # Document-level fallback if no sentence exceeded threshold
            if not best_aspect_items:
                doc_probs = self._score_sentence_aspects(text)
                for a_idx, a_key in enumerate(self.classes_):
                    prob = float(doc_probs[a_idx])
                    if prob >= th:
                        d_vec = self.vectorizer.transform([text])
                        d_sent_probs = self.sentiment_classifier.predict_proba(d_vec)[0]
                        sent_dist = {
                            sent_classes[k]: float(d_sent_probs[k])
                            for k in range(len(sent_classes))
                        }
                        top_sent = max(sent_dist, key=sent_dist.get)  # type: ignore[arg-type]
                        top_sent_conf = sent_dist[top_sent]

                        best_aspect_items[a_key] = AspectPredictionItem(
                            aspect=AspectKey(a_key),
                            sentiment=SentimentLabel(top_sent),
                            confidence=round(prob, 4),
                            sentiment_confidence=round(top_sent_conf, 4),
                            evidence_text=text[:120],
                            start_offset=0,
                            end_offset=min(120, len(text)),
                            probabilities={k: round(v, 4) for k, v in sent_dist.items()},
                        )

            detected_items = list(best_aspect_items.values())
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            outputs.append(
                ABSAPredictionOutput(
                    review_id=inp.review_id,
                    aspects=detected_items,
                    has_aspects=len(detected_items) > 0,
                    model_key=self.model_key,
                    model_version=self.version,
                    latency_ms=elapsed_ms,
                )
            )

        return outputs
