import React from "react";
import { GameTopicsData } from "../../intelligence/types/intelligence";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { MessageSquareText, Hash, AlertCircle } from "lucide-react";
import { COMPARISON_PALETTE } from "../../../lib/tokens";

export interface GameTopicComparisonItem {
  gameId: string;
  gameTitle: string;
  topicsData?: GameTopicsData | null;
  isLoading?: boolean;
}

export interface ComparisonTopicSectionProps {
  games: GameTopicComparisonItem[];
}

export const ComparisonTopicSection: React.FC<ComparisonTopicSectionProps> = ({ games }) => {
  if (games.length === 0) return null;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquareText className="w-5 h-5 text-sky-400" aria-hidden="true" />
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Community Discussion Clusters Comparison
            </h3>
            <p className="text-xs text-slate-400">
              Side-by-side topic modeling comparing player discussion clusters across selected games.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {games.map((g, idx) => {
          const color = COMPARISON_PALETTE[idx % COMPARISON_PALETTE.length];
          const topics = g.topicsData?.topics?.filter((t) => !t.is_outlier) || [];
          const hasTopics = topics.length > 0;

          return (
            <Card
              key={g.gameId}
              className="border-t-4 bg-slate-900/60"
              style={{ borderTopColor: color }}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-bold text-white line-clamp-1">
                    {g.gameTitle}
                  </CardTitle>
                  {g.topicsData?.model_version && (
                    <Badge variant="outline" size="sm" className="font-mono text-[10px] text-slate-400">
                      {g.topicsData.model_version}
                    </Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-3 pt-0">
                {g.isLoading ? (
                  <div className="space-y-2 py-4">
                    <div className="h-4 w-3/4 bg-slate-800 rounded animate-pulse" />
                    <div className="h-10 bg-slate-800/60 rounded animate-pulse" />
                  </div>
                ) : !hasTopics ? (
                  <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 text-xs text-slate-400 flex items-start gap-2.5">
                    <AlertCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" aria-hidden="true" />
                    <div className="space-y-1">
                      <span className="font-semibold text-slate-300 block">Insufficient Corpus for Topics</span>
                      <p className="text-[11px] text-slate-500 leading-relaxed">
                        Topic clustering requires an aggregated corpus of representative reviews. Review volume is either below threshold ($N &lt; 30$) or reviews are unclustered outliers.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {topics.slice(0, 3).map((t) => (
                      <div
                        key={t.topic_key}
                        className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-1.5"
                      >
                        <div className="flex items-start justify-between gap-1.5">
                          <span className="text-xs font-semibold text-slate-200 line-clamp-1">
                            {t.label}
                          </span>
                          <span className="text-[10px] font-mono font-bold text-sky-400 shrink-0">
                            {(t.prevalence * 100).toFixed(0)}% prev.
                          </span>
                        </div>

                        {t.keywords && t.keywords.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-0.5">
                            {t.keywords.slice(0, 3).map((kw) => (
                              <span
                                key={kw}
                                className="inline-flex items-center text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono"
                              >
                                <Hash className="w-2 h-2 mr-0.5" aria-hidden="true" />
                                {kw}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}

                    {g.topicsData && g.topicsData.outlier_count > 0 && (
                      <div className="text-[10px] text-slate-500 pt-1 flex items-center justify-between border-t border-slate-800/60">
                        <span>Outliers: {g.topicsData.outlier_count.toLocaleString()}</span>
                        <span>Rate: {(g.topicsData.outlier_rate * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
};

