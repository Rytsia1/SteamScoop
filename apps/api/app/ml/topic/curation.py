"""Human-in-the-loop topic curation and labeling workflow.

Implements ML_SPECIFICATION.md Section 7.6:
- Provides human review and refinement for machine-generated candidate topics.
- Replaces raw cluster numbers with concise, interpretable semantic labels and descriptions.
- Records curator audit trails and qualitative rubric evaluations.
"""

from __future__ import annotations

from typing import Any

from app.ml.topic.schemas import (
    HumanTopicEvaluationRubric,
    TopicEvaluationReport,
    TopicRepresentation,
)


class TopicCurationService:
    """Manages qualitative review, label assignment, and approval of topic models."""

    def apply_curated_labels(
        self,
        report: TopicEvaluationReport,
        curation_map: dict[str, dict[str, Any]],
        curator_id: str = "curator_01",
    ) -> TopicEvaluationReport:
        """Apply human-reviewed titles and rubric scores to candidate topics.

        Args:
            report: Raw machine-generated topic evaluation report.
            curation_map: Mapping from topic_key to dictionary containing:
                - "label": Curated human-readable title
                - "description": Curated explanatory scope
                - "rubric": Qualitative ratings (interpretability, redundancy, relevance)
            curator_id: Pseudonymous identifier of the human reviewer.
        """
        updated_topics: list[TopicRepresentation] = []
        rubric_entries: list[HumanTopicEvaluationRubric] = []

        for top in report.topics:
            t_key = top.topic_key
            if t_key in curation_map:
                curated_info = curation_map[t_key]
                new_label = curated_info.get("label", top.label)
                new_desc = curated_info.get("description", top.description)

                updated_top = TopicRepresentation(
                    topic_id=top.topic_id,
                    topic_key=top.topic_key,
                    label=new_label,
                    description=new_desc,
                    keywords=top.keywords,
                    representative_terms=top.representative_terms,
                    representative_reviews=top.representative_reviews,
                    doc_count=top.doc_count,
                    is_outlier=top.is_outlier,
                )
                updated_topics.append(updated_top)

                rubric_data = curated_info.get("rubric", {})
                rubric_entries.append(
                    HumanTopicEvaluationRubric(
                        topic_key=top.topic_key,
                        interpretability=rubric_data.get("interpretability", 4),
                        redundancy=rubric_data.get("redundancy", 4),
                        domain_relevance=rubric_data.get("domain_relevance", 4),
                        assignment_plausibility=rubric_data.get("assignment_plausibility", 4),
                        suggested_label=new_label,
                        evaluator_notes=f"Reviewed and curated by {curator_id}.",
                    )
                )
            else:
                updated_topics.append(top)

        return TopicEvaluationReport(
            model_key=report.model_key,
            model_version=report.model_version,
            steam_app_id=report.steam_app_id,
            corpus_size=report.corpus_size,
            metrics=report.metrics,
            topics=updated_topics,
            human_evaluation=rubric_entries,
            curated=len(rubric_entries) > 0,
        )
