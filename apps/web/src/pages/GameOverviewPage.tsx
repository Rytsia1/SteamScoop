import React, { useEffect, useState } from "react";
import { Link } from "../app/router/Router";
import { useParams } from "../app/router/RouterContext";
import { gameReviewsPath, ROUTES } from "../app/router/routes";
import { useGame, useGameOverview } from "../features/games/api/gamesApi";
import { getGameName } from "../features/games/types/game";
import { useRecentlyViewed } from "../features/games/hooks/useGameList";
import { FavoriteButton } from "../features/games/components/FavoriteButton";
import {
  useGameAnalytics,
  useGameAspects,
  useGameSentiment,
  useGameTopics,
} from "../features/intelligence/api/intelligenceApi";
import { SentimentOverviewCard } from "../features/intelligence/components/SentimentOverviewCard";
import { AspectBreakdownCard } from "../features/intelligence/components/AspectBreakdownCard";
import { TopicClusteringCard } from "../features/intelligence/components/TopicClusteringCard";
import {
  AnalyticsFilterBar,
  AnalyticsFilterState,
} from "../features/intelligence/components/AnalyticsFilterBar";
import { AnalyticalSummaryCard } from "../features/intelligence/components/AnalyticalSummaryCard";
import { DashboardMethodologyFooter } from "../features/intelligence/components/DashboardMethodologyFooter";
import { ReviewActivityChart } from "../components/charts/ReviewActivityChart";
import { PartialDataNotice } from "../components/feedback/PartialDataNotice";
import { ErrorAlert } from "../components/feedback/ErrorAlert";
import { CardSkeleton } from "../components/feedback/LoadingSkeleton";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Tabs } from "../components/ui/Tabs";
import {
  ArrowLeft,
  MessagesSquare,
  ExternalLink,
  Brain,
  Layers,
  MessageSquareText,
  ThumbsUp,
  Database,
  BarChart3,
  Calendar,
} from "lucide-react";

export const GameOverviewPage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const [activeTab, setActiveTab] = useState<string>("sentiment");
  const [filterState, setFilterState] = useState<AnalyticsFilterState>({
    preset: "all",
    period: "week",
  });

  const {
    data: overview,
    isLoading: isLoadingOverview,
    error: overviewError,
    refetch: refetchOverview,
  } = useGameOverview(gameId);

  // Game identity for favorites / recently viewed comes from GET /games/{id}
  const { data: gameDetail } = useGame(gameId);
  const savedGame = gameDetail
    ? {
        id: gameDetail.id,
        name: getGameName(gameDetail),
        header_image_url: gameDetail.header_image_url,
      }
    : null;

  const { pushRecent } = useRecentlyViewed();
  const savedId = savedGame?.id;
  const savedName = savedGame?.name;
  const savedImage = savedGame?.header_image_url;
  useEffect(() => {
    if (savedId && savedName) {
      pushRecent({ id: savedId, name: savedName, header_image_url: savedImage });
    }
  }, [savedId, savedName, savedImage, pushRecent]);

  const {
    data: analyticsData,
    isLoading: isLoadingAnalytics,
  } = useGameAnalytics(gameId, {
    period: filterState.period,
    from: filterState.from,
    to: filterState.to,
  });

  const {
    data: sentimentData,
    isLoading: isLoadingSentiment,
  } = useGameSentiment(gameId);

  const {
    data: aspectsData,
    isLoading: isLoadingAspects,
  } = useGameAspects(gameId);

  const {
    data: topicsData,
    isLoading: isLoadingTopics,
  } = useGameTopics(gameId);

  if (isLoadingOverview) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        <div className="h-8 w-48 bg-slate-800 rounded animate-pulse" />
        <CardSkeleton count={1} />
        <div className="h-64 bg-slate-800/60 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (overviewError || !overview) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        <Link
          to={ROUTES.HOME}
          className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:text-sky-300 font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Back to Games Catalog</span>
        </Link>
        <ErrorAlert
          title="Could not find game analytics"
          message={overviewError?.message || `Game ${gameId} was not found.`}
          onRetry={() => refetchOverview()}
        />
      </div>
    );
  }

  const { game, steam_recommendations, model_sentiment, coverage } = overview;

  const rawSteamPct = steam_recommendations?.positive_percentage ?? 0;
  const steamPositivePct = rawSteamPct <= 1.0 ? rawSteamPct * 100 : rawSteamPct;

  const rawModelPct = model_sentiment?.positive_rate ?? 0;
  const modelPositivePct = rawModelPct <= 1.0 ? rawModelPct * 100 : rawModelPct;

  const tabs = [
    {
      id: "sentiment",
      label: "Sentiment Intelligence",
      icon: <Brain className="w-4 h-4 text-emerald-400" aria-hidden="true" />,
    },
    {
      id: "aspects",
      label: "Aspect Dimensions (ABSA)",
      icon: <Layers className="w-4 h-4 text-purple-400" aria-hidden="true" />,
      count: aspectsData?.aspects?.length,
    },
    {
      id: "topics",
      label: "Recurring Topics",
      icon: <MessageSquareText className="w-4 h-4 text-sky-400" aria-hidden="true" />,
      count: topicsData?.topics?.length,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb Back Link */}
      <div>
        <Link
          to={ROUTES.HOME}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors focus-visible:outline-none"
        >
          <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Back to Catalog</span>
        </Link>
      </div>

      {/* Game Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 backdrop-blur-sm">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="positive" size="sm">
              {game.catalog_status.toUpperCase()}
            </Badge>
            <span className="text-xs font-mono text-slate-400">
              Steam App ID: <b>{game.steam_app_id}</b>
            </span>
            {game.release_date && (
              <span className="inline-flex items-center gap-1 text-xs text-slate-400">
                <Calendar className="w-3 h-3 text-slate-500" aria-hidden="true" />
                Released: {game.release_date}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {game.name || game.title}
            </h1>
            {savedGame && <FavoriteButton game={savedGame} className="p-1.5 [&>svg]:w-5 [&>svg]:h-5" />}
          </div>

          <p className="text-xs sm:text-sm text-slate-400">
            Developer: <span className="text-slate-200">{game.developer || (game.developers && game.developers[0]) || "Unknown"}</span>
            {(game.publisher || (game.publishers && game.publishers[0])) && (
              <span> &bull; Publisher: <span className="text-slate-200">{game.publisher || game.publishers?.[0]}</span></span>
            )}
          </p>

          <div className="flex flex-wrap gap-1.5 pt-1">
            {(game.genres || []).map((genre) => (
              <span
                key={genre}
                className="px-2.5 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700/60"
              >
                {genre}
              </span>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap md:flex-col gap-3 shrink-0">
          <Link to={gameReviewsPath(game.id)}>
            <Button
              variant="primary"
              size="md"
              leftIcon={<MessagesSquare className="w-4 h-4" aria-hidden="true" />}
              className="w-full sm:w-auto"
            >
              Explore Sample Reviews ({coverage.total_reviews_collected.toLocaleString()})
            </Button>
          </Link>

          <a
            href={`https://store.steampowered.com/app/${game.steam_app_id}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button
              variant="outline"
              size="md"
              leftIcon={<ExternalLink className="w-4 h-4" aria-hidden="true" />}
              className="w-full sm:w-auto"
            >
              Steam Store Page
            </Button>
          </a>
        </div>
      </div>

      {/* KPI Stats Overview Bar */}
      <section aria-label="Game Key Performance Indicators" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stored Reviews & Coverage */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-medium block">Dataset Ingestion</span>
            <span className="text-xl font-bold text-white">
              {coverage.total_reviews_collected.toLocaleString()}
            </span>
            <span className="text-[11px] text-slate-400 block">
              {(coverage.coverage_percentage).toFixed(1)}% of Steam total
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800 text-sky-400">
            <Database className="w-5 h-5" aria-hidden="true" />
          </div>
        </div>

        {/* Steam Recommendation Rate */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-medium block">Steam Recommended</span>
            <span className="text-xl font-bold text-emerald-400">
              {steamPositivePct.toFixed(1)}%
            </span>
            <span className="text-[11px] text-slate-400 block">
              {steam_recommendations?.positive_reviews?.toLocaleString() ?? 0} positive votes
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
            <ThumbsUp className="w-5 h-5" aria-hidden="true" />
          </div>
        </div>

        {/* Model Sentiment Rate */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-medium block">Model Positive Rate</span>
            <span className="text-xl font-bold text-sky-400">
              {modelPositivePct.toFixed(1)}%
            </span>
            <span className="text-[11px] text-slate-400 block font-mono">
              Model: {model_sentiment?.model_version || "1.0.0"}
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-sky-950/40 text-sky-400">
            <Brain className="w-5 h-5" aria-hidden="true" />
          </div>
        </div>

        {/* Temporal Activity Influx */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-medium block">Active Time Window</span>
            <span className="text-xl font-bold text-slate-200">
              {analyticsData?.points?.length ?? 0}
            </span>
            <span className="text-[11px] text-slate-400 block capitalize">
              {filterState.period} aggregation buckets
            </span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800 text-purple-400">
            <BarChart3 className="w-5 h-5" aria-hidden="true" />
          </div>
        </div>
      </section>

      {/* Coverage Disclosure Banner */}
      <PartialDataNotice
        coveragePercent={coverage.coverage_percentage}
        sampleCount={coverage.total_reviews_collected}
        totalAvailable={coverage.steam_total_reviews}
      />

      {/* Automated Analytical Synthesized Insights */}
      <AnalyticalSummaryCard
        overview={overview}
        sentiment={sentimentData}
        aspects={aspectsData}
        topics={topicsData}
      />

      {/* Analytics Timeline & Filtering Section */}
      <section aria-label="Review activity timeline" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              Temporal Activity & Volume Dynamics
            </h2>
            <p className="text-xs text-slate-400">
              Explore longitudinal review volume alongside calibrated NLP sentiment scores.
            </p>
          </div>
        </div>

        {/* Date Filter Bar */}
        <AnalyticsFilterBar
          initialState={filterState}
          onFilterChange={setFilterState}
          isLoading={isLoadingAnalytics}
        />

        {/* Time-Series Activity Chart */}
        <ReviewActivityChart
          points={analyticsData?.points}
          period={filterState.period}
          height={320}
        />
      </section>

      {/* Deep-Dive Interactive Tabs */}
      <section aria-label="Granular intelligence breakdown" className="space-y-6 pt-2">
        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onChange={setActiveTab}
          ariaLabel="Game intelligence sections"
        />

        <div className="pt-2">
          {activeTab === "sentiment" && (
            <SentimentOverviewCard
              sentiment={sentimentData}
              isLoading={isLoadingSentiment}
            />
          )}

          {activeTab === "aspects" && (
            <AspectBreakdownCard
              aspectsData={aspectsData}
              isLoading={isLoadingAspects}
            />
          )}

          {activeTab === "topics" && (
            <TopicClusteringCard
              topicsData={topicsData}
              isLoading={isLoadingTopics}
            />
          )}
        </div>
      </section>

      {/* Methodology, Denominators & Model Provenance */}
      <DashboardMethodologyFooter
        sentimentModelVersion={model_sentiment?.model_version || sentimentData?.model_version}
        taxonomyVersion={aspectsData?.taxonomy_version}
        topicModelVersion={topicsData?.model_version}
        totalCollected={coverage.total_reviews_collected}
      />
    </div>
  );
};
