import React from "react";
import { GameTopicsData } from "../types/intelligence";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { EmptyState } from "../../../components/feedback/EmptyState";
import { MessageSquareText, Hash, AlertCircle } from "lucide-react";

export interface TopicClusteringCardProps {
  topicsData: GameTopicsData | undefined;
  isLoading: boolean;
}

export const TopicClusteringCard: React.FC<TopicClusteringCardProps> = ({
  topicsData,
  isLoading,
}) => {
  if (isLoading || !topicsData) {
    return (
      <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/40 animate-pulse" />
    );
  }

  const validTopics = topicsData.topics?.filter((t) => !t.is_outlier) || [];
  const hasTopics = validTopics.length > 0;

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Topic Clustering & Recurring Themes</CardTitle>
          <p className="text-xs text-slate-400 mt-0.5">
            Unsupervised topic modeling identifying community talking points and discussion clusters.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" size="sm" className="font-mono text-slate-400">
            <MessageSquareText className="w-3 h-3 mr-1 text-sky-400" aria-hidden="true" />
            Model: {topicsData.model_version}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {!hasTopics ? (
          <EmptyState
            icon={<AlertCircle className="w-8 h-8 text-slate-500" />}
            title="No Topic Clusters Identified"
            description="Topic clustering requires an aggregated corpus of representative reviews to detect statistically significant semantic themes. Either the review corpus is below threshold or all reviews were categorized as unclustered outliers."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {validTopics.map((topic) => (
              <div
                key={topic.topic_key}
                className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 flex flex-col justify-between gap-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-semibold text-white tracking-tight">
                      {topic.label}
                    </h4>
                    <span className="text-[11px] text-slate-400">
                      {topic.review_count.toLocaleString()} assigned reviews &bull;{" "}
                      {(topic.prevalence * 100).toFixed(1)}% prevalence
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-sky-950 text-sky-300 border border-sky-800/60">
                    score: {topic.avg_score.toFixed(2)}
                  </span>
                </div>

                {/* Keywords badges */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {topic.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="inline-flex items-center text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/50"
                    >
                      <Hash className="w-2.5 h-2.5 mr-0.5 text-slate-400" aria-hidden="true" />
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {topicsData.outlier_count > 0 && (
          <div className="pt-3 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <span>
              Outlier / unclustered reviews: <b>{topicsData.outlier_count.toLocaleString()}</b> (
              {(topicsData.outlier_rate * 100).toFixed(1)}%)
            </span>
            <span className="text-[11px] text-slate-500 font-mono">
              Total assigned: {topicsData.total_assigned_reviews.toLocaleString()}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
