import React, { useMemo } from "react";
import { GameOverviewData } from "../../games/types/game";
import {
  GameAspectsData,
  GameTopicsData,
  SentimentDistributionData,
} from "../types/intelligence";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Layers,
  MessageSquare,
  Sparkles,
} from "lucide-react";

export interface AnalyticalSummaryCardProps {
  overview?: GameOverviewData;
  sentiment?: SentimentDistributionData;
  aspects?: GameAspectsData;
  topics?: GameTopicsData;
  isLoading?: boolean;
}

export const AnalyticalSummaryCard: React.FC<AnalyticalSummaryCardProps> = ({
  overview,
  sentiment,
  aspects,
  topics,
  isLoading = false,
}) => {
  const insights = useMemo(() => {
    if (!overview && !sentiment) return null;

    // 1. Steam vs Model Sentiment Divergence
    let steamPercent: number | null = null;
    let modelPercent: number | null = null;
    let divergenceDiff: number | null = null;

    if (overview?.steam_recommendations) {
      const rawSteam = overview.steam_recommendations.positive_percentage;
      steamPercent = rawSteam <= 1.0 ? rawSteam * 100 : rawSteam;
    }

    if (sentiment) {
      modelPercent = sentiment.positive_rate * 100;
    } else if (overview?.model_sentiment) {
      const rawModel = overview.model_sentiment.positive_rate;
      modelPercent = rawModel <= 1.0 ? rawModel * 100 : rawModel;
    }

    if (steamPercent !== null && modelPercent !== null) {
      divergenceDiff = steamPercent - modelPercent;
    }

    // 2. Aspect Strengths & Weaknesses
    let topPraisedAspect: { name: string; positiveRate: number; mentions: number } | null = null;
    let topCriticizedAspect: { name: string; negativeRate: number; mentions: number } | null = null;

    if (aspects?.aspects && aspects.aspects.length > 0) {
      const sortedByPositive = [...aspects.aspects].sort(
        (a, b) => b.positive_rate - a.positive_rate
      );
      const topPos = sortedByPositive[0];
      if (topPos) {
        topPraisedAspect = {
          name: topPos.display_name,
          positiveRate: topPos.positive_rate * 100,
          mentions: topPos.mention_count,
        };
      }

      const sortedByNegative = [...aspects.aspects].sort(
        (a, b) => b.negative_rate - a.negative_rate
      );
      const topNeg = sortedByNegative[0];
      if (topNeg) {
        topCriticizedAspect = {
          name: topNeg.display_name,
          negativeRate: topNeg.negative_rate * 100,
          mentions: topNeg.mention_count,
        };
      }
    }

    // 3. Dominant Topic Cluster
    let topTopic: { label: string; prevalence: number; count: number; keywords: string[] } | null =
      null;
    if (topics?.topics && topics.topics.length > 0) {
      const nonOutliers = topics.topics.filter((t) => !t.is_outlier);
      if (nonOutliers.length > 0) {
        const sorted = [...nonOutliers].sort((a, b) => b.prevalence - a.prevalence);
        const top = sorted[0];
        topTopic = {
          label: top.label,
          prevalence: top.prevalence * 100,
          count: top.review_count,
          keywords: top.keywords.slice(0, 4),
        };
      }
    }

    // 4. Sample Volume & Low Data Warning
    const totalCollected =
      overview?.coverage.total_reviews_collected ??
      sentiment?.total_reviews ??
      0;
    const isLowSample = totalCollected > 0 && totalCollected < 30;

    return {
      steamPercent,
      modelPercent,
      divergenceDiff,
      topPraisedAspect,
      topCriticizedAspect,
      topTopic,
      totalCollected,
      isLowSample,
    };
  }, [overview, sentiment, aspects, topics]);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 animate-pulse space-y-4">
        <div className="h-5 w-48 bg-slate-800 rounded" />
        <div className="h-16 bg-slate-800/60 rounded" />
      </div>
    );
  }

  if (!insights) {
    return null;
  }

  return (
    <Card className="w-full border-sky-900/30 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-sky-950/20">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
            <Sparkles className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <CardTitle className="text-base text-white">Synthesized Intelligence Summary</CardTitle>
            <p className="text-xs text-slate-400">
              Automated analytical findings comparing binary Steam reviews against NLP sentiment models.
            </p>
          </div>
        </div>
        <Badge variant="outline" size="sm" className="font-mono text-sky-400 border-sky-800/60">
          NLP Synthesis
        </Badge>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Low Sample Warning Banner */}
        {insights.isLowSample && (
          <div
            className="flex items-start gap-3 p-3 rounded-lg border border-amber-900/50 bg-amber-950/20 text-amber-300 text-xs"
            role="alert"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <span className="font-semibold">Low Sample Size Alert:</span> Only{" "}
              <b>{insights.totalCollected}</b> reviews have been collected. In accordance with
              methodology standards, ABSA and topic models require a minimum of 30 reviews for statistical significance. Results should be treated as provisional.
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Finding 1: Divergence or Alignment */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              {insights.divergenceDiff !== null && Math.abs(insights.divergenceDiff) >= 5 ? (
                <TrendingUp className="w-4 h-4 text-amber-400" aria-hidden="true" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" aria-hidden="true" />
              )}
              <span>Recommendation vs Sentiment</span>
            </div>

            {insights.divergenceDiff !== null && insights.steamPercent !== null && insights.modelPercent !== null ? (
              <p className="text-xs text-slate-300 leading-relaxed">
                {Math.abs(insights.divergenceDiff) >= 5 ? (
                  insights.divergenceDiff > 0 ? (
                    <>
                      Steam recommendations sit at{" "}
                      <b className="text-emerald-400">{insights.steamPercent.toFixed(1)}%</b>,
                      whereas NLP text analysis measures{" "}
                      <b className="text-sky-400">{insights.modelPercent.toFixed(1)}%</b> positive sentiment (
                      <b className="text-amber-400">-{insights.divergenceDiff.toFixed(1)}% pts</b>).
                      Players frequently submit positive thumbs-up reviews while expressing reservations or technical caveats in text.
                    </>
                  ) : (
                    <>
                      Steam thumbs-up sits at{" "}
                      <b className="text-emerald-400">{insights.steamPercent.toFixed(1)}%</b>, while
                      NLP text sentiment reaches{" "}
                      <b className="text-sky-400">{insights.modelPercent.toFixed(1)}%</b> (
                      <b className="text-emerald-400">+{Math.abs(insights.divergenceDiff).toFixed(1)}% pts</b>).
                      Reviews classified as &apos;Not Recommended&apos; contain praise for specific aspects.
                    </>
                  )
                ) : (
                  <>
                    Strong consensus: Steam thumbs-up votes (
                    <b className="text-emerald-400">{insights.steamPercent.toFixed(1)}%</b>) and NLP
                    sentiment analysis (<b className="text-sky-400">{insights.modelPercent.toFixed(1)}%</b>)
                    converge closely within {Math.abs(insights.divergenceDiff).toFixed(1)}% pts.
                  </>
                )}
              </p>
            ) : (
              <p className="text-xs text-slate-500">
                Comparative sentiment rates currently computing.
              </p>
            )}
          </div>

          {/* Finding 2: Aspect Strengths & Weaknesses */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Layers className="w-4 h-4 text-purple-400" aria-hidden="true" />
              <span>Leading Aspect Dimensions</span>
            </div>

            {insights.topPraisedAspect || insights.topCriticizedAspect ? (
              <div className="text-xs text-slate-300 space-y-1.5">
                {insights.topPraisedAspect && (
                  <div className="leading-snug">
                    <span className="text-slate-400">Top Praised: </span>
                    <b className="text-white">{insights.topPraisedAspect.name}</b> (
                    <span className="text-emerald-400 font-semibold">
                      {insights.topPraisedAspect.positiveRate.toFixed(0)}% positive
                    </span>
                    , {insights.topPraisedAspect.mentions} mentions)
                  </div>
                )}
                {insights.topCriticizedAspect && (
                  <div className="leading-snug">
                    <span className="text-slate-400">Top Friction: </span>
                    <b className="text-white">{insights.topCriticizedAspect.name}</b> (
                    <span className="text-rose-400 font-semibold">
                      {insights.topCriticizedAspect.negativeRate.toFixed(0)}% negative
                    </span>
                    , {insights.topCriticizedAspect.mentions} mentions)
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500">
                Aspect polarity requires additional review volume.
              </p>
            )}
          </div>

          {/* Finding 3: Dominant Topic Cluster */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <MessageSquare className="w-4 h-4 text-sky-400" aria-hidden="true" />
              <span>Core Discussion Cluster</span>
            </div>

            {insights.topTopic ? (
              <div className="text-xs text-slate-300 space-y-1.5">
                <div className="font-semibold text-white leading-snug">
                  {insights.topTopic.label}
                </div>
                <div className="text-slate-400 text-[11px]">
                  Represents <b>{insights.topTopic.prevalence.toFixed(1)}%</b> of categorized reviews (
                  {insights.topTopic.count.toLocaleString()} assigned).
                </div>
                {insights.topTopic.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-0.5">
                    {insights.topTopic.keywords.map((kw) => (
                      <span
                        key={kw}
                        className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-mono"
                      >
                        #{kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500">
                Topic clustering will populate after corpus aggregation.
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

