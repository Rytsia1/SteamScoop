import hashlib
import json
import random
from collections import defaultdict
from typing import Any

from app.ml.deduplication import ReviewDeduplicator
from app.ml.language_detector import ReviewLanguageDetector
from app.ml.manifest import DatasetManifest, SplitSummary
from app.ml.preprocessor import ReviewPreprocessor
from app.ml.quality import ReviewQualityAssessor
from app.ml.taxonomy import SentimentLabel


class DatasetItem(dict[str, Any]):
    """Standardized dictionary representation of a processed dataset example."""


class DatasetBuilder:
    """Assembles, cleans, deduplicates, and splits Steam review datasets with zero data leakage.

    Enforces ML_SPECIFICATION.md Section 4.5, 4.6, 13.1:
    - Preserves verbatim raw review text alongside normalized text.
    - Runs Unicode NFC normalization, language detection, and quality assessment.
    - Groups exact and near-duplicates to ensure entire duplicate clusters reside
      in the same partition.
    - Produces group-stratified train/val/test partitions.
    - Computes reproducible SHA-256 split checksums and an immutable DatasetManifest.
    """

    def __init__(
        self,
        preprocessor: ReviewPreprocessor | None = None,
        language_detector: ReviewLanguageDetector | None = None,
        quality_assessor: ReviewQualityAssessor | None = None,
        deduplicator: ReviewDeduplicator | None = None,
        random_seed: int = 42,
    ) -> None:
        self.preprocessor = preprocessor or ReviewPreprocessor()
        self.language_detector = language_detector or ReviewLanguageDetector()
        self.quality_assessor = quality_assessor or ReviewQualityAssessor()
        self.deduplicator = deduplicator or ReviewDeduplicator()
        self.random_seed = random_seed

    def process_raw_reviews(
        self,
        raw_items: list[dict[str, Any]],
        target_language: str = "en",
    ) -> list[DatasetItem]:
        """Preprocess, detect language, assess quality, and assign duplicate groups."""
        if not raw_items:
            return []

        # 1. Individual text processing, language detection, quality evaluation
        processed_candidates: list[dict[str, Any]] = []
        for item in raw_items:
            rid = str(item["review_id"])
            raw_text = item.get("review_text") or ""
            proc = self.preprocessor.process(raw_text)
            lang_res = self.language_detector.detect(proc.normalized_text)
            quality = self.quality_assessor.assess(
                proc.normalized_text,
                is_language_uncertain=lang_res.is_uncertain,
            )

            # Extract label if provided
            sentiment = item.get("sentiment")
            if sentiment is None:
                # Fallback to voted_up proxy if unlabeled
                sentiment = (
                    SentimentLabel.POSITIVE.value
                    if item.get("voted_up", True)
                    else SentimentLabel.NEGATIVE.value
                )

            processed_candidates.append(
                {
                    "review_id": rid,
                    "steam_app_id": item.get("steam_app_id", 0),
                    "raw_text": raw_text,
                    "normalized_text": proc.normalized_text,
                    "language": lang_res.language,
                    "language_confidence": lang_res.confidence,
                    "is_language_uncertain": lang_res.is_uncertain,
                    "quality_status": quality.status.value,
                    "quality_reason": quality.reason_code,
                    "is_trainable": quality.is_trainable and lang_res.language == target_language,
                    "voted_up": bool(item.get("voted_up", True)),
                    "sentiment": str(sentiment),
                    "aspects": item.get("aspects", []),
                    "char_count": proc.char_count,
                    "word_count": proc.word_count,
                    "is_truncated": proc.is_truncated,
                    "steam_created_at": item.get("steam_created_at"),
                    "metadata": item.get("metadata", {}),
                }
            )

        # 2. Cluster exact and near-duplicates
        dedup_inputs = [
            {"review_id": p["review_id"], "normalized_text": p["normalized_text"]}
            for p in processed_candidates
        ]
        review_to_group = self.deduplicator.cluster_reviews(dedup_inputs)

        # 3. Attach duplicate group metadata
        final_items: list[DatasetItem] = []
        for p in processed_candidates:
            rid = p["review_id"]
            group = review_to_group.get(rid)
            p["duplicate_group_id"] = group.group_id if group else f"grp_{rid}"
            p["is_exact_duplicate"] = group.is_exact_duplicate if group else False
            p["group_size"] = group.group_size if group else 1
            final_items.append(DatasetItem(p))

        return final_items

    def create_group_stratified_splits(
        self,
        items: list[DatasetItem],
        dataset_id: str,
        version: str = "v1.0.0",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        filter_trainable_only: bool = True,
    ) -> tuple[dict[str, list[DatasetItem]], DatasetManifest]:
        """Partition dataset into Train / Val / Test by duplicate group, preventing data leakage.

        Guarantees:
        - Reviews in the same duplicate group are strictly placed in the same split.
        - Stratified roughly by sentiment label distribution.
        - Bit-exact reproducibility using configured random seed.
        """
        eligible = [i for i in items if i["is_trainable"]] if filter_trainable_only else items
        if not eligible:
            raise ValueError("No eligible items available for dataset splitting.")

        # 1. Group items by duplicate_group_id
        groups: dict[str, list[DatasetItem]] = defaultdict(list)
        for it in eligible:
            groups[it["duplicate_group_id"]].append(it)

        # 2. Stratify groups by dominant sentiment label
        stratified_groups: dict[str, list[str]] = defaultdict(list)
        for gid, g_items in groups.items():
            dominant_label = g_items[0]["sentiment"]
            stratified_groups[dominant_label].append(gid)

        rng = random.Random(self.random_seed)

        train_groups: set[str] = set()
        val_groups: set[str] = set()
        test_groups: set[str] = set()

        for _label, gids in stratified_groups.items():
            shuffled = list(gids)
            rng.shuffle(shuffled)
            n = len(shuffled)
            n_train = int(round(n * train_ratio))
            n_val = int(round(n * val_ratio))

            train_groups.update(shuffled[:n_train])
            val_groups.update(shuffled[n_train : n_train + n_val])
            test_groups.update(shuffled[n_train + n_val :])

        # Assemble partitions
        train_items = [it for it in eligible if it["duplicate_group_id"] in train_groups]
        val_items = [it for it in eligible if it["duplicate_group_id"] in val_groups]
        test_items = [it for it in eligible if it["duplicate_group_id"] in test_groups]

        # Critical zero-leakage assertions
        train_ids = {it["review_id"] for it in train_items}
        val_ids = {it["review_id"] for it in val_items}
        test_ids = {it["review_id"] for it in test_items}

        assert len(train_ids & val_ids) == 0, (
            "Data leakage detected: train and val share review IDs!"
        )
        assert len(train_ids & test_ids) == 0, (
            "Data leakage detected: train and test share review IDs!"
        )
        assert len(val_ids & test_ids) == 0, "Data leakage detected: val and test share review IDs!"

        assert len(train_groups & val_groups) == 0, "Duplicate group leakage between train and val!"
        assert len(train_groups & test_groups) == 0, (
            "Duplicate group leakage between train and test!"
        )
        assert len(val_groups & test_groups) == 0, "Duplicate group leakage between val and test!"

        splits = {
            "train": train_items,
            "validation": val_items,
            "test": test_items,
        }

        # Compute SplitSummaries
        split_summaries: dict[str, SplitSummary] = {}
        for sname, sitems in splits.items():
            split_summaries[sname] = self._build_split_summary(sname, sitems)

        total_unique_groups = len(groups)
        duplicate_rate = (len(eligible) - total_unique_groups) / len(eligible) if eligible else 0.0

        manifest = DatasetManifest(
            dataset_id=dataset_id,
            version=version,
            description="SteamScoop benchmark dataset with group-stratified leakage prevention.",
            splits=split_summaries,
            total_reviews=len(eligible),
            total_unique_groups=total_unique_groups,
            duplicate_rate=round(duplicate_rate, 4),
            preprocessing_version=self.preprocessor.version,
            quality_engine_version=self.quality_assessor.version,
            deduplication_version=self.deduplicator.version,
            random_seed=self.random_seed,
            provenance={
                "games_count": len({it["steam_app_id"] for it in eligible}),
                "target_language": "en",
                "filter_trainable_only": filter_trainable_only,
            },
        )

        return splits, manifest

    def _build_split_summary(self, split_name: str, items: list[DatasetItem]) -> SplitSummary:
        """Calculate statistical distribution for a single split partition."""
        sample_count = len(items)
        unique_groups = len({it["duplicate_group_id"] for it in items})

        # Serialized JSONL string for stable SHA-256 checksum
        serialized = "\n".join(json.dumps(dict(it), sort_keys=True, default=str) for it in items)
        sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        label_counts: dict[str, int] = defaultdict(int)
        aspect_counts: dict[str, int] = defaultdict(int)
        lang_counts: dict[str, int] = defaultdict(int)
        char_lengths: list[int] = []
        word_lengths: list[int] = []

        for it in items:
            label_counts[str(it["sentiment"])] += 1
            lang_counts[str(it["language"])] += 1
            char_lengths.append(it["char_count"])
            word_lengths.append(it["word_count"])

            for asp in it.get("aspects", []):
                akey = asp.get("aspect") if isinstance(asp, dict) else getattr(asp, "aspect", None)
                if akey:
                    aspect_counts[str(akey)] += 1

        length_stats: dict[str, float] = {}
        if char_lengths:
            char_lengths.sort()
            word_lengths.sort()
            n = len(char_lengths)
            length_stats = {
                "mean_char_length": round(sum(char_lengths) / n, 1),
                "p10_char_length": float(char_lengths[int(n * 0.10)]),
                "p50_char_length": float(char_lengths[int(n * 0.50)]),
                "p90_char_length": float(char_lengths[int(n * 0.90)]),
                "max_char_length": float(char_lengths[-1]),
                "mean_word_length": round(sum(word_lengths) / n, 1),
                "p50_word_length": float(word_lengths[int(n * 0.50)]),
            }

        return SplitSummary(
            split_name=split_name,
            sample_count=sample_count,
            group_count=unique_groups,
            sha256_hash=sha256,
            label_distribution=dict(label_counts),
            aspect_distribution=dict(aspect_counts),
            language_distribution=dict(lang_counts),
            length_statistics=length_stats,
        )
