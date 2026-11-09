"""Corpus building, candidate model comparison, and serialization pipeline for topic modeling.

Enforces:
- Per-game and per-language corpus isolation (ML_SPECIFICATION.md Section 7.3).
- Minimum corpus-size requirement before model fitting or topic publication.
- Comparative benchmarking across NMF, LDA, and Semantic Clustering (c-TF-IDF).
- Artifact serialization with SHA256 provenance checksums.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from app.ml.topic.evaluator import TopicModelEvaluator
from app.ml.topic.models import (
    BaseTopicModel,
    LDATopicModel,
    NMFTopicModel,
    SemanticClusterTopicModel,
)
from app.ml.topic.schemas import (
    CorpusFilterConfig,
    RawDocument,
    TopicEvaluationReport,
)

logger = logging.getLogger("steamscoop.ml.topic.pipeline")


class InsufficientCorpusError(ValueError):
    """Raised when a review corpus is smaller than the predeclared minimum publication threshold."""


class TopicTrainingPipeline:
    """Orchestrates corpus assembly, candidate model benchmarking, and artifact packaging."""

    def __init__(self, evaluator: TopicModelEvaluator | None = None) -> None:
        self.evaluator = evaluator or TopicModelEvaluator()

    def build_game_corpus(
        self,
        raw_reviews: list[dict[str, Any]],
        config: CorpusFilterConfig,
    ) -> list[RawDocument]:
        """Filter and assemble a clean per-game corpus adhering to minimum size rules."""
        seen_texts: set[str] = set()
        corpus: list[RawDocument] = []

        for r in raw_reviews:
            appid = r.get("steam_app_id")
            if appid != config.steam_app_id:
                continue

            lang = r.get("language", "en")
            if lang != config.language:
                continue

            txt = r.get("normalized_text") or r.get("review_text") or ""
            txt_clean = txt.strip()

            if len(txt_clean) < config.min_char_length:
                continue

            words = txt_clean.split()
            if len(words) < config.min_word_length:
                continue

            if config.deduplicate:
                normalized_key = " ".join(words).lower()
                if normalized_key in seen_texts:
                    continue
                seen_texts.add(normalized_key)

            corpus.append(
                RawDocument(
                    review_id=str(r.get("review_id", f"rev_{len(corpus)}")),
                    text=txt_clean,
                    language=lang,
                    voted_up=bool(r.get("voted_up", True)),
                )
            )

        # Enforce minimum corpus size gate
        if len(corpus) < config.min_corpus_size:
            raise InsufficientCorpusError(
                f"Game {config.steam_app_id} has {len(corpus)} eligible reviews, which is below "
                f"the minimum threshold of {config.min_corpus_size}. Topic modeling cannot be "
                "reliably published without sufficient player sample size."
            )

        return corpus

    def compare_candidate_models(
        self,
        documents: list[RawDocument],
        steam_app_id: int,
        num_topics: int = 4,
        random_seed: int = 42,
    ) -> tuple[dict[str, TopicEvaluationReport], str, BaseTopicModel]:
        """Fit and quantitatively benchmark NMF, LDA, and Semantic Clustering candidates."""
        reports: dict[str, TopicEvaluationReport] = {}

        # 1. Candidate 1: NMF Topic Model
        nmf_model = NMFTopicModel(
            model_key=f"steamscoop-topic-nmf-{steam_app_id}",
            num_topics=num_topics,
            random_seed=random_seed,
        )
        nmf_model.fit(documents)
        nmf_report = self.evaluator.evaluate(
            nmf_model,
            documents,
            steam_app_id=steam_app_id,
            model_factory=lambda s: NMFTopicModel(
                model_key=f"steamscoop-topic-nmf-{steam_app_id}",
                num_topics=num_topics,
                random_seed=s,
            ),
        )
        reports["nmf"] = nmf_report

        # 2. Candidate 2: LDA Topic Model
        lda_model = LDATopicModel(
            model_key=f"steamscoop-topic-lda-{steam_app_id}",
            num_topics=num_topics,
            random_seed=random_seed,
        )
        lda_model.fit(documents)
        lda_report = self.evaluator.evaluate(
            lda_model,
            documents,
            steam_app_id=steam_app_id,
            model_factory=lambda s: LDATopicModel(
                model_key=f"steamscoop-topic-lda-{steam_app_id}",
                num_topics=num_topics,
                random_seed=s,
            ),
        )
        reports["lda"] = lda_report

        # 3. Candidate 3: Semantic Clustering Topic Model (c-TF-IDF)
        cluster_model = SemanticClusterTopicModel(
            model_key=f"steamscoop-topic-bertopic-adapter-{steam_app_id}",
            num_topics=num_topics,
            random_seed=random_seed,
        )
        cluster_model.fit(documents)
        cluster_report = self.evaluator.evaluate(
            cluster_model,
            documents,
            steam_app_id=steam_app_id,
            model_factory=lambda s: SemanticClusterTopicModel(
                model_key=f"steamscoop-topic-bertopic-adapter-{steam_app_id}",
                num_topics=num_topics,
                random_seed=s,
            ),
        )
        reports["semantic_clustering"] = cluster_report

        # Select model with best combined composite metric:
        # Score = NPMI_Coherence + Topic_Diversity - Mean_Pairwise_Jaccard
        def score_model(rep: TopicEvaluationReport) -> float:
            m = rep.metrics
            return m.npmi_coherence + m.topic_diversity - m.mean_pairwise_jaccard

        winning_key = max(reports, key=lambda k: score_model(reports[k]))
        model_map = {
            "nmf": nmf_model,
            "lda": lda_model,
            "semantic_clustering": cluster_model,
        }
        winning_model = model_map[winning_key]

        return reports, winning_key, winning_model

    def save_artifacts(
        self,
        model: BaseTopicModel,
        report: TopicEvaluationReport,
        output_dir: str | Path,
    ) -> Path:
        """Serialize topic model binary and immutable provenance manifest."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        model_file = out_path / "model.joblib"
        model.save(model_file)

        # Compute SHA256 checksum
        sha256 = hashlib.sha256()
        with open(model_file, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        artifact_checksum = f"sha256:{sha256.hexdigest()}"

        manifest_data = {
            "model_key": model.model_key,
            "version": report.model_version,
            "task": "topic",
            "framework": "scikit-learn",
            "artifact_file": "model.joblib",
            "artifact_checksum": artifact_checksum,
            "steam_app_id": report.steam_app_id,
            "corpus_size": report.corpus_size,
            "config": {
                "num_topics": model.num_topics,
                "outlier_threshold": model.outlier_threshold,
                "random_seed": model.random_seed,
            },
            "metrics": report.metrics.model_dump(),
            "topics": [t.model_dump() for t in report.topics],
            "topics_count": len(report.topics),
            "curated": report.curated,
        }

        manifest_file = out_path / "model_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return manifest_file
