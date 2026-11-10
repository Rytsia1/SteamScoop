import React from "react";
import { SentimentDistributionData } from "../types/intelligence";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { SentimentPieChart } from "../../../components/charts/SentimentPieChart";
import { SentimentTrendChart, SentimentTrendPoint } from "../../../components/charts/SentimentTrendChart";
import { EmptyState } from "../../../components/feedback/EmptyState";
import { ThumbsUp, ThumbsDown, Minus, Cpu, AlertCircle } from "lucide-react";

export interface SentimentOverviewCardProps {
  sentiment: SentimentDistributionData | undefined;
  isLoading: boolean;
}

export const SentimentOverviewCard: React.FC<SentimentOverviewCardProps> = ({
  sentiment,
  isLoading,
}) => {
  if (isLoading || !sentiment) {
    return (
      <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/40 animate-pulse" />
    );
  }

  const hasClassified = sentiment.classified_count > 0;

  const pieData = {
    positiveCount: sentiment.positive_count,
    negativeCount: sentiment.negative_count,
    neutralCount: sentiment.neutral_count,
    positiveRate: sentiment.positive_rate,
    negativeRate: sentiment.negative_rate,
    neutralRate: sentiment.neutral_rate,
    totalClassified: sentiment.classified_count,
  };

  const trendPoints: SentimentTrendPoint[] = (sentiment.timeline || []).map((pt) => {
    const total = pt.positive_count + pt.negative_count + pt.neutral_count;
    return {
      date: pt.period_start,
      positiveRate: total > 0 ? pt.positive_count / total : 0,
      negativeRate: total > 0 ? pt.negative_count / total : 0,
      reviewCount: pt.review_count,
    };
  });

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Sentiment Intelligence Overview</CardTitle>
          <p className="text-xs text-slate-400 mt-0.5">
            Classified across {sentiment.classified_count.toLocaleString()} eligible reviews (
            {sentiment.unclassified_count.toLocaleString()} unclassified/abstained).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" size="sm" className="font-mono text-slate-400">
            <Cpu className="w-3 h-3 mr-1 text-sky-400" aria-hidden="true" />
            Model: {sentiment.model_version}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {!hasClassified ? (
          <EmptyState
            icon={<AlertCircle className="w-8 h-8 text-slate-500" />}
            title="No Classified Sentiment Data"
            description="The machine learning sentiment model has not classified any reviews for this game yet, or confidence thresholds caused the model to abstain."
          />
        ) : (
          <>
            {/* Metric KPI Tiles */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Positive */}
              <div className="p-4 rounded-xl border border-emerald-900/50 bg-emerald-950/20 flex items-center justify-between">
                <div>
                  <span className="text-xs text-emerald-400/80 font-medium block">
                    Positive Sentiment
                  </span>
                  <span className="text-2xl font-bold text-emerald-300">
                    {(sentiment.positive_rate * 100).toFixed(1)}%
                  </span>
                  <span className="text-[11px] text-emerald-500/80 block mt-0.5">
                    {sentiment.positive_count.toLocaleString()} / {sentiment.classified_count.toLocaleString()} classified
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-emerald-900/40 text-emerald-300">
                  <ThumbsUp className="w-5 h-5" aria-hidden="true" />
                </div>
              </div>

              {/* Negative */}
              <div className="p-4 rounded-xl border border-rose-900/50 bg-rose-950/20 flex items-center justify-between">
                <div>
                  <span className="text-xs text-rose-400/80 font-medium block">
                    Negative Sentiment
                  </span>
                  <span className="text-2xl font-bold text-rose-300">
                    {(sentiment.negative_rate * 100).toFixed(1)}%
                  </span>
                  <span className="text-[11px] text-rose-500/80 block mt-0.5">
                    {sentiment.negative_count.toLocaleString()} / {sentiment.classified_count.toLocaleString()} classified
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-rose-900/40 text-rose-300">
                  <ThumbsDown className="w-5 h-5" aria-hidden="true" />
                </div>
              </div>

              {/* Neutral / Unclassified */}
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-medium block">
                    Neutral / Abstained
                  </span>
                  <span className="text-2xl font-bold text-slate-200">
                    {((sentiment.neutral_rate + sentiment.unclassified_rate) * 100).toFixed(1)}%
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    {(sentiment.neutral_count + sentiment.unclassified_count).toLocaleString()} / {sentiment.total_reviews.toLocaleString()} total
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-800 text-slate-400">
                  <Minus className="w-5 h-5" aria-hidden="true" />
                </div>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-5">
                <SentimentPieChart data={pieData} height={260} />
              </div>
              <div className="lg:col-span-7">
                <SentimentTrendChart
                  data={trendPoints}
                  height={260}
                  title="Temporal Sentiment Trajectory"
                  description="Longitudinal satisfaction trends across collection windows."
                />
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};
