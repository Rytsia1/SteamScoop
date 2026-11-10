import React, { useState, useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { useGames } from "../features/games/api/gamesApi";
import { useCompareGames } from "../features/comparison/api/comparisonApi";
import { fetchGameAnalytics, fetchGameTopics } from "../features/intelligence/api/intelligenceApi";
import { GameSelector } from "../features/comparison/components/GameSelector";
import { ComparisonMetricsGrid } from "../features/comparison/components/ComparisonMetricsGrid";
import { ComparisonVolumeBarChart } from "../components/charts/ComparisonVolumeBarChart";
import { ComparisonRadarChart } from "../components/charts/ComparisonRadarChart";
import { ComparisonTrendChart, GameTrendSeries } from "../components/charts/ComparisonTrendChart";
import {
  ComparisonTopicSection,
  GameTopicComparisonItem,
} from "../features/comparison/components/ComparisonTopicSection";
import { ComparisonMethodologyNotice } from "../features/comparison/components/ComparisonMethodologyNotice";
import {
  AnalyticsFilterBar,
  AnalyticsFilterState,
} from "../features/intelligence/components/AnalyticsFilterBar";
import { ErrorAlert } from "../components/feedback/ErrorAlert";
import { ChartSkeleton, CardSkeleton } from "../components/feedback/LoadingSkeleton";
import { GitCompare, Layers, TrendingUp, Compass } from "lucide-react";

export const GameComparisonPage: React.FC = () => {
  const { data: gamesData, isLoading: isLoadingGames } = useGames({ limit: 50 });

  // Selected game IDs (bounded 2 to 5)
  const [selectedGameIds, setSelectedGameIds] = useState<string[]>([]);

  // Date range and temporal aggregation filter
  const [filterState, setFilterState] = useState<AnalyticsFilterState>({
    preset: "all",
    period: "week",
  });

  // Auto-select first two games once games catalog loads if user hasn't selected yet
  React.useEffect(() => {
    if (selectedGameIds.length === 0 && gamesData?.items && gamesData.items.length >= 2) {
      setSelectedGameIds([gamesData.items[0].id, gamesData.items[1].id]);
    }
  }, [gamesData, selectedGameIds.length]);

  const periodPayload = useMemo(() => {
    if (filterState.from || filterState.to) {
      return {
        from: filterState.from,
        to: filterState.to,
      };
    }
    return null;
  }, [filterState.from, filterState.to]);

  const {
    data: comparisonData,
    isLoading: isComparing,
    error: comparisonError,
    refetch,
  } = useCompareGames(
    {
      game_ids: selectedGameIds,
      period: periodPayload,
      metrics: [
        "review_volume",
        "steam_recommendation",
        "model_sentiment",
        "aspect_sentiment",
      ],
    },
    { enabled: selectedGameIds.length >= 2 }
  );

  const handleSelectGame = (gameId: string) => {
    if (selectedGameIds.length < 5 && !selectedGameIds.includes(gameId)) {
      setSelectedGameIds((prev) => [...prev, gameId]);
    }
  };

  const handleRemoveGame = (gameId: string) => {
    setSelectedGameIds((prev) => prev.filter((id) => id !== gameId));
  };

  // Build radar chart data from comparison response (strictly no synthetic fallbacks)
  const radarChartData = useMemo(() => {
    if (!comparisonData?.games) return [];
    return comparisonData.games.map((g) => {
      const title = g.title || g.name || "Game";
      const rec = g.steam_recommendation_rate;
      const nlp = g.model_positive_rate ?? g.model_sentiment_rate;
      const aspects = g.aspect_sentiment;

      return {
        gameTitle: title,
        steamRecommendationRate: rec,
        modelSentimentRate: nlp,
        gameplaySatisfaction: aspects?.gameplay ?? null,
        performanceSatisfaction: aspects?.performance ?? null,
        contentSatisfaction: aspects?.story ?? aspects?.content ?? null,
      };
    });
  }, [comparisonData]);

  // Map selected games for parallel queries
  const selectedGamesMeta = useMemo(() => {
    return selectedGameIds.map((id) => {
      const fromComparison = comparisonData?.games.find((g) => g.game_id === id);
      const fromCatalog = gamesData?.items.find((g) => g.id === id);
      return {
        id,
        title: fromComparison?.title || fromComparison?.name || fromCatalog?.title || `Game ${id.slice(0, 6)}`,
      };
    });
  }, [selectedGameIds, comparisonData, gamesData]);

  // Fetch longitudinal trends for selected games in parallel
  const analyticsQueries = useQueries({
    queries: selectedGamesMeta.map((g) => ({
      queryKey: [
        "gameAnalytics",
        g.id,
        { period: filterState.period, from: filterState.from, to: filterState.to },
      ],
      queryFn: () =>
        fetchGameAnalytics(g.id, {
          period: filterState.period,
          from: filterState.from,
          to: filterState.to,
        }),
      enabled: selectedGameIds.length >= 2 && Boolean(g.id),
      staleTime: 60_000,
    })),
  });

  // Fetch topics for selected games in parallel
  const topicsQueries = useQueries({
    queries: selectedGamesMeta.map((g) => ({
      queryKey: ["gameTopics", g.id],
      queryFn: () => fetchGameTopics(g.id),
      enabled: selectedGameIds.length >= 2 && Boolean(g.id),
      staleTime: 60_000,
    })),
  });

  // Prepare longitudinal trend series
  const trendSeries = useMemo<GameTrendSeries[]>(() => {
    return selectedGamesMeta.map((meta, idx) => {
      const query = analyticsQueries[idx];
      const points =
        query?.data?.points?.map((p) => ({
          date: p.period_start,
          score: p.sentiment_score ?? 0,
        })) || [];
      return {
        gameTitle: meta.title,
        points,
      };
    });
  }, [selectedGamesMeta, analyticsQueries]);

  // Prepare topic comparison items
  const topicComparisonItems = useMemo<GameTopicComparisonItem[]>(() => {
    return selectedGamesMeta.map((meta, idx) => {
      const query = topicsQueries[idx];
      return {
        gameId: meta.id,
        gameTitle: meta.title,
        topicsData: query?.data,
        isLoading: query?.isLoading,
      };
    });
  }, [selectedGamesMeta, topicsQueries]);

  // Assess sample size safeguard ($N < 30$) across compared games
  const hasInsufficientDataGames = useMemo(() => {
    if (!comparisonData?.games) return false;
    return comparisonData.games.some((g) => (g.review_volume ?? 0) < 30);
  }, [comparisonData]);

  // Gather model versions to detect calibration disparities
  const modelVersions = useMemo(() => {
    if (!comparisonData?.games) return [];
    const versions = comparisonData.games
      .map((g) => g.model_version || comparisonData.model_version || "baseline")
      .filter(Boolean);
    return Array.from(new Set(versions));
  }, [comparisonData]);

  const hasAtLeastTwo = selectedGameIds.length >= 2;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Title & Context */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-800/60 text-xs font-medium text-sky-300">
          <GitCompare className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Multi-Game Comparative Analytics</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Benchmark Game Perception Across Titles
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
          Compare player feedback volume, Steam recommendation ratios, and NLP-derived sentiment
          across 2 to 5 games simultaneously. Ensure consistent metric definitions and model provenance.
        </p>
      </div>

      {/* Game Selector Controls */}
      <GameSelector
        availableGames={gamesData?.items}
        selectedGameIds={selectedGameIds}
        onSelectGame={handleSelectGame}
        onRemoveGame={handleRemoveGame}
        isLoadingAvailable={isLoadingGames}
      />

      {/* Date Range & Aggregation Filter Bar */}
      <AnalyticsFilterBar
        initialState={filterState}
        onFilterChange={setFilterState}
        isLoading={isComparing}
      />

      {/* Insufficient Selection Notice */}
      {!hasAtLeastTwo && (
        <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/40 text-center space-y-2">
          <GitCompare className="w-8 h-8 text-slate-500 mx-auto" aria-hidden="true" />
          <h3 className="text-sm font-semibold text-white">Select at Least Two Games</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Comparative analysis requires selecting between 2 and 5 games from the catalog above to
            benchmark sentiment and topic clusters.
          </p>
        </div>
      )}

      {/* Error State */}
      {comparisonError && hasAtLeastTwo && (
        <ErrorAlert
          title="Comparison Failed"
          message={comparisonError.message}
          onRetry={() => refetch()}
        />
      )}

      {/* Loading Skeletons */}
      {isComparing && hasAtLeastTwo && (
        <div className="space-y-6">
          <CardSkeleton count={3} />
          <ChartSkeleton height={360} />
          <ChartSkeleton height={340} />
        </div>
      )}

      {/* Comparison Results */}
      {!isComparing && comparisonData && comparisonData.games.length >= 2 && (
        <div className="space-y-8">
          {/* Section 1: Comparative Overview Grid */}
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" aria-hidden="true" />
              <h2 className="text-base font-bold text-white tracking-tight">
                Comparative Overview & Core Metrics
              </h2>
            </div>
            <ComparisonMetricsGrid games={comparisonData.games} />
          </section>

          {/* Section 2: Volume & Sentiment Ratio Benchmark Chart */}
          <section className="space-y-3">
            <ComparisonVolumeBarChart games={comparisonData.games} height={380} />
          </section>

          {/* Section 3: Longitudinal Sentiment Trends */}
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-purple-400" aria-hidden="true" />
              <h2 className="text-base font-bold text-white tracking-tight">
                Longitudinal Sentiment Trajectory Comparison
              </h2>
            </div>
            <ComparisonTrendChart series={trendSeries} height={340} />
          </section>

          {/* Section 4: Multi-Dimensional Aspect Perception Benchmark */}
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-emerald-400" aria-hidden="true" />
              <h2 className="text-base font-bold text-white tracking-tight">
                Aspect Dimension Multi-Game Benchmark
              </h2>
            </div>
            <ComparisonRadarChart data={radarChartData} height={380} />
          </section>

          {/* Section 5: Topic Modeling Comparison */}
          <section className="space-y-3">
            <ComparisonTopicSection games={topicComparisonItems} />
          </section>

          {/* Section 6: Methodology, Definitions & Model Compatibility Notice */}
          <section className="space-y-3 pt-2">
            <ComparisonMethodologyNotice
              modelVersions={modelVersions}
              hasInsufficientDataGames={hasInsufficientDataGames}
            />
          </section>
        </div>
      )}
    </div>
  );
};
