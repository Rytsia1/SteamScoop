"""Candidate topic model implementations: NMF, LDA, and Semantic Clustering (c-TF-IDF).

Adheres to:
- Docs/ML_SPECIFICATION.md Section 7.2 (Candidate architectures: NMF, LDA, BERTopic)
- Docs/ML_SPECIFICATION.md Section 7.4 (Handling short texts & outlier identification)
- Docs/ML_SPECIFICATION.md Section 7.5 (Topic model output contract)
"""

from __future__ import annotations

import abc
import math
from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import NMF, LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from app.ml.topic.preprocessor import TopicPreprocessor
from app.ml.topic.schemas import (
    RawDocument,
    ReviewTopicAssignment,
    TopicRepresentation,
    TopicTerm,
)


class BaseTopicModel(abc.ABC):
    """Abstract base class for SteamScoop topic modeling candidates."""

    def __init__(
        self,
        model_key: str,
        num_topics: int = 5,
        random_seed: int = 42,
        outlier_threshold: float = 0.10,
    ) -> None:
        self.model_key = model_key
        self.num_topics = num_topics
        self.random_seed = random_seed
        self.outlier_threshold = outlier_threshold
        self.is_fitted = False
        self.preprocessor = TopicPreprocessor()

    @abc.abstractmethod
    def fit(self, documents: list[RawDocument]) -> BaseTopicModel:
        """Fit the topic model on a corpus of raw documents."""

    @abc.abstractmethod
    def transform(
        self,
        documents: list[RawDocument],
    ) -> tuple[list[TopicRepresentation], list[ReviewTopicAssignment]]:
        """Compute topic definitions and document-topic assignments."""

    @abc.abstractmethod
    def get_topic_terms(self, top_k: int = 10) -> list[list[str]]:
        """Return list of top-K keyword strings for each topic (for evaluation metrics)."""

    def transform_documents(
        self,
        documents: list[RawDocument],
    ) -> list[ReviewTopicAssignment]:
        """Compute document-topic assignments for inference on new documents."""
        _, assignments = self.transform(documents)
        return assignments

    def save(self, path: str | Path) -> None:
        """Serialize model artifact to disk."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, target_path)

    @classmethod
    def load(cls, path: str | Path) -> BaseTopicModel:
        """Deserialize model artifact from disk."""
        model = joblib.load(path)
        if not isinstance(model, BaseTopicModel):
            raise TypeError(f"Loaded artifact {type(model)} is not a BaseTopicModel.")
        return model


class NMFTopicModel(BaseTopicModel):
    """Non-Negative Matrix Factorization (NMF) on sublinear TF-IDF term matrix."""

    def __init__(
        self,
        model_key: str = "steamscoop-topic-nmf",
        num_topics: int = 5,
        random_seed: int = 42,
        outlier_threshold: float = 0.08,
        ngram_range: tuple[int, int] = (1, 2),
        max_features: int = 5000,
    ) -> None:
        super().__init__(model_key, num_topics, random_seed, outlier_threshold)
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            sublinear_tf=True,
            max_features=max_features,
            token_pattern=r"(?u)\b[a-zA-Z]{3,}\b",
            stop_words=list(self.preprocessor.stop_words),
            min_df=1,
            max_df=0.90,
        )
        self.nmf = NMF(
            n_components=num_topics,
            init="nndsvda",
            random_state=random_seed,
            max_iter=1000,
        )
        self.feature_names_: list[str] = []

    def fit(self, documents: list[RawDocument]) -> NMFTopicModel:
        texts = [doc.text for doc in documents]
        X = self.vectorizer.fit_transform(texts)
        self.nmf.fit(X)
        self.feature_names_ = self.vectorizer.get_feature_names_out().tolist()
        self.is_fitted = True
        return self

    def transform(
        self,
        documents: list[RawDocument],
    ) -> tuple[list[TopicRepresentation], list[ReviewTopicAssignment]]:
        if not self.is_fitted:
            raise ValueError("Model is not fitted.")

        texts = [doc.text for doc in documents]
        X = self.vectorizer.transform(texts)
        W = self.nmf.transform(X)  # shape: (n_docs, n_topics)
        H = self.nmf.components_  # shape: (n_topics, n_features)

        # Build TopicRepresentations
        topics: list[TopicRepresentation] = []
        topic_doc_counts: list[int] = [0] * self.num_topics
        topic_rep_reviews: list[list[str]] = [[] for _ in range(self.num_topics)]

        # Precompute top terms for each topic
        topic_top_terms: list[list[TopicTerm]] = []
        for t_idx in range(self.num_topics):
            comp = H[t_idx]
            top_indices = np.argsort(comp)[::-1][:10]
            terms = [
                TopicTerm(term=self.feature_names_[i], weight=round(float(comp[i]), 4))
                for i in top_indices
                if comp[i] > 0
            ]
            topic_top_terms.append(terms)

        # Assign documents
        assignments: list[ReviewTopicAssignment] = []
        for d_idx, doc in enumerate(documents):
            weights = W[d_idx]
            max_weight = float(np.max(weights)) if len(weights) > 0 else 0.0
            sum_weights = float(np.sum(weights)) if len(weights) > 0 else 1.0

            if max_weight < self.outlier_threshold or sum_weights == 0.0:
                # Document classified as outlier / unassigned
                assignments.append(
                    ReviewTopicAssignment(
                        review_id=doc.review_id,
                        topic_id=-1,
                        topic_key=f"{self.model_key}_outlier",
                        score=0.0,
                        is_primary=True,
                        is_outlier=True,
                    )
                )
            else:
                top_t = int(np.argmax(weights))
                norm_score = min(1.0, max(0.0, max_weight / sum_weights))
                topic_doc_counts[top_t] += 1
                if len(topic_rep_reviews[top_t]) < 3:
                    topic_rep_reviews[top_t].append(doc.text[:120])

                assignments.append(
                    ReviewTopicAssignment(
                        review_id=doc.review_id,
                        topic_id=top_t,
                        topic_key=f"{self.model_key}_topic_{top_t}",
                        score=round(norm_score, 4),
                        is_primary=True,
                        is_outlier=False,
                    )
                )

        for t_idx in range(self.num_topics):
            terms = topic_top_terms[t_idx]
            keywords = [t.term for t in terms]
            auto_label = ", ".join(keywords[:3]).title() if keywords else f"Topic {t_idx}"

            topics.append(
                TopicRepresentation(
                    topic_id=t_idx,
                    topic_key=f"{self.model_key}_topic_{t_idx}",
                    label=auto_label,
                    description=f"Automated theme characterized by: {', '.join(keywords[:5])}",
                    keywords=keywords,
                    representative_terms=terms,
                    representative_reviews=topic_rep_reviews[t_idx],
                    doc_count=topic_doc_counts[t_idx],
                    is_outlier=False,
                )
            )

        return topics, assignments

    def get_topic_terms(self, top_k: int = 10) -> list[list[str]]:
        if not self.is_fitted:
            return []
        H = self.nmf.components_
        res: list[list[str]] = []
        for t_idx in range(self.num_topics):
            top_i = np.argsort(H[t_idx])[::-1][:top_k]
            res.append([self.feature_names_[i] for i in top_i])
        return res


class LDATopicModel(BaseTopicModel):
    """Latent Dirichlet Allocation (LDA) probabilistic topic model."""

    def __init__(
        self,
        model_key: str = "steamscoop-topic-lda",
        num_topics: int = 5,
        random_seed: int = 42,
        outlier_threshold: float = 0.25,
        max_features: int = 5000,
    ) -> None:
        super().__init__(model_key, num_topics, random_seed, outlier_threshold)
        self.max_features = max_features
        self.vectorizer = CountVectorizer(
            max_features=max_features,
            token_pattern=r"(?u)\b[a-zA-Z]{3,}\b",
            stop_words=list(self.preprocessor.stop_words),
            min_df=1,
            max_df=0.90,
        )
        self.lda = LatentDirichletAllocation(
            n_components=num_topics,
            random_state=random_seed,
            max_iter=100,
            learning_method="batch",
        )
        self.feature_names_: list[str] = []

    def fit(self, documents: list[RawDocument]) -> LDATopicModel:
        texts = [doc.text for doc in documents]
        X = self.vectorizer.fit_transform(texts)
        self.lda.fit(X)
        self.feature_names_ = self.vectorizer.get_feature_names_out().tolist()
        self.is_fitted = True
        return self

    def transform(
        self,
        documents: list[RawDocument],
    ) -> tuple[list[TopicRepresentation], list[ReviewTopicAssignment]]:
        if not self.is_fitted:
            raise ValueError("Model is not fitted.")

        texts = [doc.text for doc in documents]
        X = self.vectorizer.transform(texts)
        doc_topics = self.lda.transform(X)  # shape: (n_docs, n_topics) (normalized probabilities)
        components = self.lda.components_

        topics: list[TopicRepresentation] = []
        topic_doc_counts: list[int] = [0] * self.num_topics
        topic_rep_reviews: list[list[str]] = [[] for _ in range(self.num_topics)]

        topic_top_terms: list[list[TopicTerm]] = []
        for t_idx in range(self.num_topics):
            comp = components[t_idx]
            top_indices = np.argsort(comp)[::-1][:10]
            terms = [
                TopicTerm(term=self.feature_names_[i], weight=round(float(comp[i]), 4))
                for i in top_indices
            ]
            topic_top_terms.append(terms)

        assignments: list[ReviewTopicAssignment] = []
        uniform_baseline = 1.0 / self.num_topics

        for d_idx, doc in enumerate(documents):
            probs = doc_topics[d_idx]
            max_p = float(np.max(probs))
            top_t = int(np.argmax(probs))

            # If posterior is near uniform distribution, mark as outlier
            if max_p <= uniform_baseline + 0.05:
                assignments.append(
                    ReviewTopicAssignment(
                        review_id=doc.review_id,
                        topic_id=-1,
                        topic_key=f"{self.model_key}_outlier",
                        score=round(max_p, 4),
                        is_primary=True,
                        is_outlier=True,
                    )
                )
            else:
                topic_doc_counts[top_t] += 1
                if len(topic_rep_reviews[top_t]) < 3:
                    topic_rep_reviews[top_t].append(doc.text[:120])

                assignments.append(
                    ReviewTopicAssignment(
                        review_id=doc.review_id,
                        topic_id=top_t,
                        topic_key=f"{self.model_key}_topic_{top_t}",
                        score=round(max_p, 4),
                        is_primary=True,
                        is_outlier=False,
                    )
                )

        for t_idx in range(self.num_topics):
            terms = topic_top_terms[t_idx]
            keywords = [t.term for t in terms]
            auto_label = ", ".join(keywords[:3]).title() if keywords else f"Topic {t_idx}"

            topics.append(
                TopicRepresentation(
                    topic_id=t_idx,
                    topic_key=f"{self.model_key}_topic_{t_idx}",
                    label=auto_label,
                    description=f"Probabilistic theme: {', '.join(keywords[:5])}",
                    keywords=keywords,
                    representative_terms=terms,
                    representative_reviews=topic_rep_reviews[t_idx],
                    doc_count=topic_doc_counts[t_idx],
                    is_outlier=False,
                )
            )

        return topics, assignments

    def get_topic_terms(self, top_k: int = 10) -> list[list[str]]:
        if not self.is_fitted:
            return []
        res: list[list[str]] = []
        for t_idx in range(self.num_topics):
            top_i = np.argsort(self.lda.components_[t_idx])[::-1][:top_k]
            res.append([self.feature_names_[i] for i in top_i])
        return res


class SemanticClusterTopicModel(BaseTopicModel):
    """Semantic clustering topic model implementing the BERTopic c-TF-IDF architecture.

    Steps:
    1. Sublinear TF-IDF + TruncatedSVD semantic embedding space.
    2. Dense cluster assignment via KMeans clustering.
    3. Class-based TF-IDF (c-TF-IDF) representation extracting topic keywords per cluster:
       W_{t, c} = tf_{t, c} * log(1 + A / f_t)
    4. Outlier classification for distant/noise points.
    """

    def __init__(
        self,
        model_key: str = "steamscoop-topic-bertopic-adapter",
        num_topics: int = 5,
        random_seed: int = 42,
        embedding_dim: int = 16,
        outlier_threshold: float = 0.85,
    ) -> None:
        super().__init__(model_key, num_topics, random_seed, outlier_threshold)
        self.embedding_dim = embedding_dim
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000,
            token_pattern=r"(?u)\b[a-zA-Z]{3,}\b",
            stop_words=list(self.preprocessor.stop_words),
            min_df=1,
            max_df=0.90,
        )
        self.svd = TruncatedSVD(n_components=embedding_dim, random_state=random_seed)
        self.clusterer = KMeans(n_clusters=num_topics, random_state=random_seed, n_init=10)
        self.feature_names_: list[str] = []
        self.c_tfidf_matrix_: np.ndarray | None = None

    def fit(self, documents: list[RawDocument]) -> SemanticClusterTopicModel:
        texts = [doc.text for doc in documents]
        X = self.vectorizer.fit_transform(texts)
        self.feature_names_ = self.vectorizer.get_feature_names_out().tolist()

        # Semantic embedding space via TruncatedSVD
        max_possible = max(1, min(X.shape[0] - 1, X.shape[1] - 1))
        actual_dim = max(1, min(self.embedding_dim, max_possible))
        self.svd.n_components = actual_dim
        embeddings = self.svd.fit_transform(X)

        # Cluster embeddings
        labels = self.clusterer.fit_predict(embeddings)

        # Compute Class-based TF-IDF (c-TF-IDF)
        self._fit_c_tfidf(texts, labels)
        self.is_fitted = True
        return self

    def _fit_c_tfidf(self, texts: list[str], labels: np.ndarray) -> None:
        """Compute c-TF-IDF term representations across clusters."""
        num_clusters = self.num_topics
        vocab_size = len(self.feature_names_)

        # Count frequencies per cluster
        c_counts = np.zeros((num_clusters, vocab_size), dtype=float)
        word_to_idx = {w: i for i, w in enumerate(self.feature_names_)}

        for txt, cluster_id in zip(texts, labels, strict=False):
            if cluster_id < 0 or cluster_id >= num_clusters:
                continue
            tokens = self.preprocessor.tokenize(txt)
            for tok in tokens:
                if tok in word_to_idx:
                    c_counts[cluster_id, word_to_idx[tok]] += 1.0

        # Global term frequency across all clusters
        f_t = np.sum(c_counts, axis=0)  # shape: (vocab_size,)
        # Average words per cluster
        cluster_lengths = np.sum(c_counts, axis=1)  # shape: (num_clusters,)
        A = float(np.mean(cluster_lengths)) if len(cluster_lengths) > 0 else 1.0

        c_tfidf = np.zeros_like(c_counts)
        for c in range(num_clusters):
            for t in range(vocab_size):
                tf = c_counts[c, t]
                if tf > 0:
                    idf = math.log(1.0 + (A / (f_t[t] + 1e-9)))
                    c_tfidf[c, t] = tf * idf

        self.c_tfidf_matrix_ = c_tfidf

    def transform(
        self,
        documents: list[RawDocument],
    ) -> tuple[list[TopicRepresentation], list[ReviewTopicAssignment]]:
        if not self.is_fitted or self.c_tfidf_matrix_ is None:
            raise ValueError("Model is not fitted.")

        texts = [doc.text for doc in documents]
        X = self.vectorizer.transform(texts)
        embeddings = self.svd.transform(X)

        # Distances to cluster centers
        centers = self.clusterer.cluster_centers_
        labels = self.clusterer.predict(embeddings)

        # Extract top terms from c-TF-IDF
        topic_top_terms: list[list[TopicTerm]] = []
        for t_idx in range(self.num_topics):
            weights = self.c_tfidf_matrix_[t_idx]
            top_idx = np.argsort(weights)[::-1][:10]
            terms = [
                TopicTerm(term=self.feature_names_[i], weight=round(float(weights[i]), 4))
                for i in top_idx
                if weights[i] > 0
            ]
            topic_top_terms.append(terms)

        topic_doc_counts = [0] * self.num_topics
        topic_rep_reviews: list[list[str]] = [[] for _ in range(self.num_topics)]
        assignments: list[ReviewTopicAssignment] = []

        # Outlier calculation: distance to nearest center
        for d_idx, doc in enumerate(documents):
            emb = embeddings[d_idx]
            top_c = int(labels[d_idx])
            dist = float(np.linalg.norm(emb - centers[top_c]))

            # Normalized similarity score
            score = 1.0 / (1.0 + dist)

            if score < (1.0 - self.outlier_threshold):
                assignments.append(
                    ReviewTopicAssignment(
                        review_id=doc.review_id,
                        topic_id=-1,
                        topic_key=f"{self.model_key}_outlier",
                        score=round(score, 4),
                        is_primary=True,
                        is_outlier=True,
                    )
                )
            else:
                topic_doc_counts[top_c] += 1
                if len(topic_rep_reviews[top_c]) < 3:
                    topic_rep_reviews[top_c].append(doc.text[:120])

                assignments.append(
                    ReviewTopicAssignment(
                        review_id=doc.review_id,
                        topic_id=top_c,
                        topic_key=f"{self.model_key}_topic_{top_c}",
                        score=round(score, 4),
                        is_primary=True,
                        is_outlier=False,
                    )
                )

        topics: list[TopicRepresentation] = []
        for t_idx in range(self.num_topics):
            terms = topic_top_terms[t_idx]
            keywords = [t.term for t in terms]
            auto_label = ", ".join(keywords[:3]).title() if keywords else f"Topic {t_idx}"

            topics.append(
                TopicRepresentation(
                    topic_id=t_idx,
                    topic_key=f"{self.model_key}_topic_{t_idx}",
                    label=auto_label,
                    description=f"Semantic cluster: {', '.join(keywords[:5])}",
                    keywords=keywords,
                    representative_terms=terms,
                    representative_reviews=topic_rep_reviews[t_idx],
                    doc_count=topic_doc_counts[t_idx],
                    is_outlier=False,
                )
            )

        return topics, assignments

    def get_topic_terms(self, top_k: int = 10) -> list[list[str]]:
        if not self.is_fitted or self.c_tfidf_matrix_ is None:
            return []
        res: list[list[str]] = []
        for t_idx in range(self.num_topics):
            weights = self.c_tfidf_matrix_[t_idx]
            top_i = np.argsort(weights)[::-1][:top_k]
            res.append([self.feature_names_[i] for i in top_i])
        return res
