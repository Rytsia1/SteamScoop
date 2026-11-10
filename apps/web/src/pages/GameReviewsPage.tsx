import React, { useState } from "react";
import { Link } from "../app/router/Router";
import { useParams, useSearchParams } from "../app/router/RouterContext";
import { gameOverviewPath } from "../app/router/routes";
import { useGame } from "../features/games/api/gamesApi";
import { useGameReviews } from "../features/reviews/api/reviewsApi";
import { ReviewFilters } from "../features/reviews/components/ReviewFilters";
import { ReviewList } from "../features/reviews/components/ReviewList";
import { ReviewSortOption } from "../features/reviews/types/review";
import { ArrowLeft, MessagesSquare, ShieldAlert } from "lucide-react";

export const GameReviewsPage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  // Read initial filter values from URL search parameters to preserve filter state
  const sentiment = searchParams.get("sentiment") || "";
  const votedUp = searchParams.get("steam_recommended") || searchParams.get("voted_up") || "";
  const aspect = searchParams.get("aspect") || "";
  const language = searchParams.get("language") || "";
  const sort = (searchParams.get("sort") as ReviewSortOption) || "created_at_desc";

  // Cursor pagination state
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [cursorHistory, setCursorHistory] = useState<string[]>([]);

  const { data: game } = useGame(gameId);

  const {
    data: reviewsData,
    isLoading,
    error,
    refetch,
  } = useGameReviews(gameId, {
    sentiment: sentiment || undefined,
    steam_recommended: votedUp || undefined,
    aspect: aspect || undefined,
    language: language || undefined,
    sort,
    limit: 15,
    cursor,
  });

  const updateFilters = (newFilters: {
    sentiment?: string;
    votedUp?: string;
    aspect?: string;
    language?: string;
    sort?: string;
  }) => {
    setCursor(undefined);
    setCursorHistory([]);

    const nextSentiment = newFilters.sentiment !== undefined ? newFilters.sentiment : sentiment;
    const nextVotedUp = newFilters.votedUp !== undefined ? newFilters.votedUp : votedUp;
    const nextAspect = newFilters.aspect !== undefined ? newFilters.aspect : aspect;
    const nextLanguage = newFilters.language !== undefined ? newFilters.language : language;
    const nextSort = newFilters.sort !== undefined ? newFilters.sort : sort;

    setSearchParams({
      sentiment: nextSentiment || undefined,
      steam_recommended: nextVotedUp || undefined,
      aspect: nextAspect || undefined,
      language: nextLanguage || undefined,
      sort: nextSort !== "created_at_desc" ? nextSort : undefined,
    });
  };

  const handleNextPage = () => {
    if (reviewsData?.pagination?.next_cursor) {
      setCursorHistory((prev) => [...prev, cursor || ""]);
      setCursor(reviewsData.pagination.next_cursor);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handlePrevPage = () => {
    if (cursorHistory.length > 0) {
      const prev = cursorHistory[cursorHistory.length - 1];
      setCursorHistory((prevList) => prevList.slice(0, -1));
      setCursor(prev || undefined);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleResetFilters = () => {
    setCursor(undefined);
    setCursorHistory([]);
    setSearchParams({
      sentiment: undefined,
      steam_recommended: undefined,
      voted_up: undefined,
      aspect: undefined,
      language: undefined,
      sort: undefined,
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Breadcrumb Back Link */}
      <div>
        <Link
          to={gameOverviewPath(gameId)}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors focus-visible:outline-none"
        >
          <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Back to {game?.title || game?.name || "Game"} Overview</span>
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <MessagesSquare className="w-5 h-5 text-sky-400" aria-hidden="true" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Player Review Explorer
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-400">
            Explore public Steam reviews annotated with multi-task NLP sentiment inferences, aspect tags, and topic clusters for{" "}
            <span className="text-slate-200 font-semibold">{game?.title || game?.name || "Game"}</span>.
          </p>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-900/60 border border-slate-800 px-3 py-2 rounded-xl self-start sm:self-auto">
          <ShieldAlert className="w-4 h-4 text-emerald-500 shrink-0" aria-hidden="true" />
          <span>PII Protected: Author profiles and personal SteamIDs are strictly omitted.</span>
        </div>
      </div>

      {/* Review Filters & Sorting */}
      <ReviewFilters
        sentiment={sentiment}
        onSentimentChange={(val) => updateFilters({ sentiment: val })}
        votedUp={votedUp}
        onVotedUpChange={(val) => updateFilters({ votedUp: val })}
        aspect={aspect}
        onAspectChange={(val) => updateFilters({ aspect: val })}
        language={language}
        onLanguageChange={(val) => updateFilters({ language: val })}
        sort={sort}
        onSortChange={(val) => updateFilters({ sort: val })}
        onReset={handleResetFilters}
      />

      {/* Reviews List & Pagination */}
      <ReviewList
        reviews={reviewsData?.items}
        isLoading={isLoading}
        error={error}
        onRetry={() => refetch()}
        pagination={reviewsData?.pagination}
        onNextPage={handleNextPage}
        onPrevPage={handlePrevPage}
        hasPrevPage={cursorHistory.length > 0}
      />
    </div>
  );
};
