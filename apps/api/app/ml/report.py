from collections import Counter

from pydantic import BaseModel, ConfigDict

from app.ml.dataset_builder import DatasetItem
from app.ml.quality import QualityStatus


class QualityReportSummary(BaseModel):
    """Structured data quality and dataset statistics summary."""

    model_config = ConfigDict(frozen=True)

    total_evaluated: int
    trainable_count: int
    trainable_percentage: float
    status_counts: dict[str, int]
    language_counts: dict[str, int]
    uncertain_language_count: int
    exact_duplicate_count: int
    unique_clusters_count: int
    duplicate_rate: float
    sentiment_counts: dict[str, int]
    voted_up_concordance: dict[str, int]
    length_metrics: dict[str, float]
    aspect_counts: dict[str, int]
    negation_percentage: float


class DataQualityReporter:
    """Generates structured analytics and formatted Markdown data quality reports."""

    def generate_report(self, items: list[DatasetItem]) -> QualityReportSummary:
        """Compute statistical data quality distributions across processed items."""
        total = len(items)
        if total == 0:
            return QualityReportSummary(
                total_evaluated=0,
                trainable_count=0,
                trainable_percentage=0.0,
                status_counts={},
                language_counts={},
                uncertain_language_count=0,
                exact_duplicate_count=0,
                unique_clusters_count=0,
                duplicate_rate=0.0,
                sentiment_counts={},
                voted_up_concordance={},
                length_metrics={},
                aspect_counts={},
                negation_percentage=0.0,
            )

        status_counts = Counter(it.get("quality_status", QualityStatus.VALID.value) for it in items)
        trainable = sum(1 for it in items if it.get("is_trainable", False))
        lang_counts = Counter(it.get("language", "unknown") for it in items)
        uncertain_langs = sum(1 for it in items if it.get("is_language_uncertain", False))

        exact_dups = sum(1 for it in items if it.get("is_exact_duplicate", False))
        unique_groups = len({it.get("duplicate_group_id") for it in items})
        dup_rate = (total - unique_groups) / total if total > 0 else 0.0

        sentiment_counts = Counter(it.get("sentiment", "unknown") for it in items)

        # Concordance between Steam voted_up and text sentiment
        concordance = Counter(
            f"voted_up={it.get('voted_up')}__sentiment={it.get('sentiment')}" for it in items
        )

        char_lengths = sorted([it.get("char_count", 0) for it in items])
        word_lengths = sorted([it.get("word_count", 0) for it in items])

        n = len(char_lengths)
        length_metrics = {
            "mean_char_length": round(sum(char_lengths) / n, 1),
            "p10_char_length": float(char_lengths[int(n * 0.10)]),
            "p50_char_length": float(char_lengths[int(n * 0.50)]),
            "p90_char_length": float(char_lengths[int(n * 0.90)]),
            "max_char_length": float(char_lengths[-1]),
            "mean_word_length": round(sum(word_lengths) / n, 1),
            "p50_word_length": float(word_lengths[int(n * 0.50)]),
            "max_word_length": float(word_lengths[-1]),
        }

        aspect_counts: Counter[str] = Counter()
        for it in items:
            for a in it.get("aspects", []):
                k = a.get("aspect") if isinstance(a, dict) else getattr(a, "aspect", None)
                if k:
                    aspect_counts[str(k)] += 1

        negation_count = sum(
            1 for it in items if "not" in it.get("normalized_text", "").lower().split()
        )
        negation_pct = round(negation_count / total * 100.0, 2)

        return QualityReportSummary(
            total_evaluated=total,
            trainable_count=trainable,
            trainable_percentage=round(trainable / total * 100.0, 2),
            status_counts=dict(status_counts),
            language_counts=dict(lang_counts),
            uncertain_language_count=uncertain_langs,
            exact_duplicate_count=exact_dups,
            unique_clusters_count=unique_groups,
            duplicate_rate=round(dup_rate, 4),
            sentiment_counts=dict(sentiment_counts),
            voted_up_concordance=dict(concordance),
            length_metrics=length_metrics,
            aspect_counts=dict(aspect_counts),
            negation_percentage=negation_pct,
        )

    def render_markdown(
        self, summary: QualityReportSummary, title: str = "SteamScoop Dataset Quality Report"
    ) -> str:
        """Render markdown summary of dataset quality statistics."""
        md = [
            f"# {title}",
            "",
            "## 1. Executive Summary",
            f"- **Total Reviews Evaluated:** {summary.total_evaluated:,}",
            f"- **Trainable / Quality Passed:** {summary.trainable_count:,} "
            f"({summary.trainable_percentage}%)",
            f"- **Unique Duplicate Clusters:** {summary.unique_clusters_count:,}",
            f"- **Duplicate / Redundancy Rate:** {summary.duplicate_rate * 100:.2f}%",
            f"- **Uncertain Language Flagged:** {summary.uncertain_language_count:,}",
            "",
            "## 2. Quality Status Breakdown",
            "| Quality Status | Count | Percentage |",
            "| :--- | :--- | :--- |",
        ]
        for st, cnt in sorted(summary.status_counts.items(), key=lambda x: x[1], reverse=True):
            pct = cnt / summary.total_evaluated * 100 if summary.total_evaluated else 0
            md.append(f"| `{st}` | {cnt:,} | {pct:.2f}% |")

        md.extend(
            [
                "",
                "## 3. Language Distribution",
                "| Language Code | Count | Percentage |",
                "| :--- | :--- | :--- |",
            ]
        )
        for lang, cnt in sorted(summary.language_counts.items(), key=lambda x: x[1], reverse=True):
            pct = cnt / summary.total_evaluated * 100 if summary.total_evaluated else 0
            md.append(f"| `{lang}` | {cnt:,} | {pct:.2f}% |")

        word_mean = summary.length_metrics.get("mean_word_length", 0)
        word_p50 = summary.length_metrics.get("p50_word_length", 0)
        char_p90 = summary.length_metrics.get("p90_char_length", 0)
        char_max = summary.length_metrics.get("max_char_length", 0)
        md.extend(
            [
                "",
                "## 4. Length Statistics",
                f"- **Mean Word Count:** {word_mean:.1f} words",
                f"- **Median (P50) Word Count:** {word_p50:.0f} words",
                f"- **P90 Character Length:** {char_p90:.0f} chars",
                f"- **Max Character Length:** {char_max:.0f} chars",
                (
                    f"- **Negation Frequency:** {summary.negation_percentage}% of reviews "
                    "contain explicit negation markers"
                ),
                "",
                "## 5. Sentiment Label Distribution",
                "| Sentiment Label | Count | Percentage |",
                "| :--- | :--- | :--- |",
            ]
        )
        for snt, cnt in sorted(summary.sentiment_counts.items(), key=lambda x: x[1], reverse=True):
            pct = cnt / summary.total_evaluated * 100 if summary.total_evaluated else 0
            md.append(f"| `{snt}` | {cnt:,} | {pct:.2f}% |")

        if summary.aspect_counts:
            md.extend(
                [
                    "",
                    "## 6. Aspect Mention Prevalence",
                    "| Aspect Key | Mentions |",
                    "| :--- | :--- |",
                ]
            )
            for asp, cnt in sorted(summary.aspect_counts.items(), key=lambda x: x[1], reverse=True):
                md.append(f"| `{asp}` | {cnt:,} |")

        return "\n".join(md)
